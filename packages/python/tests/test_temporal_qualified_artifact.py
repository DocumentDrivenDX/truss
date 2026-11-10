# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure receipt/archive controls for exact temporal release-wheel reuse."""
import hashlib
import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import temporal_qualified_artifact as qualified


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def jbytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def fixture():
    commit = "a" * 40
    tree = "b" * 40
    wheel_buffer = io.BytesIO()
    runtime_content = {
        "_catalog_runtime/query-abi.json": b'{"identity":"truss-postgresql-logical-query","version":"1.2"}',
        "_catalog_runtime/query-temporal-abi.json": b'{"identity":"truss-postgresql-temporal-query","version":"1.3"}',
        "_catalog_runtime/query-temporal.sql": b"SELECT synthetic temporal source",
        "_catalog_runtime/query-temporal-sources.sql": b"SELECT synthetic complete source",
        "_catalog_runtime/query-temporal-cursor.sql": b"SELECT synthetic cursor",
        "_catalog_runtime/temporal-storage.sql": b"SELECT synthetic storage",
    }
    native_manifest = b'{"releaseId":"truss-catalog-runtime/0.76-temporal-candidate"}'
    with ZipFile(wheel_buffer, "w") as archive:
        archive.writestr("umf_truss-0.0.56.dist-info/METADATA", b"Metadata-Version: 2.4\nName: umf-truss\nVersion: 0.0.56\n\n")
        for name, raw in runtime_content.items(): archive.writestr("truss/" + name, raw)
        archive.writestr("truss/_catalog_runtime/manifest.json", native_manifest)
    wheel = wheel_buffer.getvalue()
    def owner_wheel(filename, distribution, version, package=None, module=None, content=b"synthetic module"):
        output = io.BytesIO()
        with ZipFile(output, "w") as archive:
            archive.writestr(f"{distribution.replace('-', '_')}-{version}.dist-info/METADATA",
                f"Metadata-Version: 2.4\nName: {distribution}\nVersion: {version}\n\n".encode())
            if package:
                archive.writestr(package + "/" + module, content)
        return output.getvalue()
    core_module = b"synthetic core module"
    weft_module = b"synthetic weft module"
    core_wheel = owner_wheel("core", "umf-core", "0.10.8", "umf", "_rust.so", core_module)
    access_wheel = owner_wheel("access", "umf_access", "0.1.0.dev10")
    weft_wheel = owner_wheel("weft", "umf-weft", "0.4.57", "weft", "_weft.so", weft_module)
    validator = b"synthetic reviewed validator source"
    receipt = jbytes({"scope": "synthetic source test only"})
    files = {
        "inputs/admission.json": b"",
        "inputs/receipts/core.json": receipt,
        "inputs/wheelhouse/umf_truss-0.0.56-py3-none-any.whl": wheel,
        "inputs/wheelhouse/core.whl": core_wheel,
        "inputs/wheelhouse/access.whl": access_wheel,
        "inputs/wheelhouse/weft.whl": weft_wheel,
        "source/scripts/core-validator.py": validator,
        "source/truss-release-cohort.json": b"",
        "inputs/hosted-input.json": b"",
        "source/temporal-native-case-ledger.json": b"",
        "evidence/campaign/admission-result.json": b"",
        "evidence/campaign/census.json": b"",
        "evidence/campaign/campaign-result.json": b"",
    }
    stages = {}
    ledger_stages = {}
    census_stages = {}
    for stage, count in qualified.EXPECTED_COUNTS.items():
        selectors = [f"synthetic.{stage}.case_{i:02}" for i in range(count)]
        ledger_stages[stage] = [{"gate": stage, "test": item} for item in selectors]
        observations = [{"id": item, "status": "passed"} for item in selectors]
        result = {"stage": stage, "expectedIds": selectors, "expectedCases": count,
                  "testsRun": count, "skips": 0, "expectedFailures": 0, "unexpectedSuccesses": 0,
                  "failures": 0, "errors": 0, "wasSuccessful": True, "passed": True,
                  "inventoryVerified": True, "cleanupConfirmed": True, "observations": observations}
        stages[stage] = result
        files[f"evidence/campaign/{stage}/result.json"] = jbytes(result)
        census_stages[stage] = {"count": count, "ids": selectors}
        if stage in ("temporal", "journal"):
            files[f"evidence/native/{stage}/shared-worker-cleanup.json"] = jbytes({
                "confirmed": True, "dataDeleted": True, "pgCtlStatus": 3,
                "originalPostmasterPidAbsent": True, "originalPostmasterPid": 1234})
        else:
            files[f"evidence/campaign/{stage}/isolated-cleanup.json"] = jbytes({
                "clusters": [{"originalPostmasterPid": 1234, "confirmed": True, "dataDeleted": True,
                              "pgCtlStatus": 3, "originalPostmasterPidAbsent": True}],
                "uncertainPaths": [], "cleanupErrors": []})
    ledger = {"schema": "truss-temporal-case-ledger/1", "expectedCounts": qualified.EXPECTED_COUNTS,
              "stages": ledger_stages}
    files["source/temporal-native-case-ledger.json"] = jbytes(ledger)
    cohort = {"schema": "truss-release-cohort/1", "truss": {"distribution": "umf-truss", "version": "0.0.56"},
              "weft": {"distribution": "umf-weft", "version": "0.4.57"},
              "access": {"distribution": "umf_access", "version": "0.1.0.dev10"},
              "core": {"distribution": "umf-core", "version": "0.10.8"}}
    files["source/truss-release-cohort.json"] = jbytes(cohort)
    resource_names = ("coreSchema", "referenceSchema", "packageSchema", "constraints", "domainPolicy",
                      "tablesPackage", "actionsPackage", "bindingPackage", "stableBindingPackage")
    for name in resource_names:
        files[f"inputs/resources/{name}.json"] = ("synthetic " + name).encode()
    owner_identities = {
        "core": {"sourceCommit": "c" * 40, "wheelSha256": digest(files["inputs/wheelhouse/core.whl"]),
                 "wheelPath": "wheelhouse/core.whl", "moduleSha256": digest(core_module), "modulePath": "_rust.so",
                 "resourceSourceCommit": "c" * 40, "resourceManifestSha256": "c" * 64,
                 "resources": {name: {"path": f"resources/{name}.json", "sha256": digest(files[f"inputs/resources/{name}.json"])} for name in resource_names}},
        "weft": {"sourceCommit": "e" * 40, "wheelSha256": digest(files["inputs/wheelhouse/weft.whl"]),
                 "wheelPath": "wheelhouse/weft.whl", "moduleSha256": digest(weft_module), "modulePath": "_weft.so"},
        "truss": {"nativeManifestSha256": digest(native_manifest)},
    }
    hosted_wheels = {"truss": {"path": "wheelhouse/umf_truss-0.0.56-py3-none-any.whl", "sha256": digest(wheel)},
        "core": {"path": "wheelhouse/core.whl", "sha256": digest(files["inputs/wheelhouse/core.whl"])},
        "access": {"path": "wheelhouse/access.whl", "sha256": digest(files["inputs/wheelhouse/access.whl"])},
        "weft": {"path": "wheelhouse/weft.whl", "sha256": digest(files["inputs/wheelhouse/weft.whl"])} }
    hosted_files = {name.removeprefix("inputs/"): digest(raw) for name, raw in files.items()
                    if name.startswith("inputs/") and name != "inputs/hosted-input.json"}
    hosted = {"schema": "truss-temporal-hosted-input/1", "ready": True, "phase": "qualify119",
              "sourceCommit": commit, "sourceTree": tree, "candidateWheel": hosted_wheels["truss"]["path"],
              "ownerIdentities": owner_identities, "wheels": hosted_wheels, "files": hosted_files}
    files["inputs/hosted-input.json"] = jbytes(hosted)
    prereqs = [{"gateId": "core.synthetic", "receiptPath": "inputs/receipts/core.json",
                "receiptSha256": digest(receipt), "validatorId": "synthetic.core.validator/1",
                "validatorSourcePath": "scripts/core-validator.py", "validatorSourceSha256": digest(validator)}]
    runner_wheelhouse = "/runner/inputs/wheelhouse"
    admission_wheels = {owner: {"path": runner_wheelhouse + "/" + row["path"].removeprefix("wheelhouse/"),
                               "sha256": row["sha256"]} for owner, row in hosted_wheels.items()}
    admission = {"sourceCommit": commit, "sourceTree": tree, "wheelhouse": runner_wheelhouse,
                 "wheels": admission_wheels,
                 "componentPrerequisiteReceipts": prereqs}
    files["inputs/admission.json"] = jbytes(admission)
    hosted_files["admission.json"] = digest(files["inputs/admission.json"])
    hosted = {**hosted, "files": hosted_files}
    files["inputs/hosted-input.json"] = jbytes(hosted)
    runtime_assets = {name: {"sha256": digest(raw), "size": len(raw)} for name, raw in runtime_content.items()}
    admission_result = {"nativeManifestSha256": digest(native_manifest), "runtimeAssets": runtime_assets,
        "wheels": {"truss": {"version": "0.0.56", "wheelSha256": digest(wheel)},
                   "core": {"version": "0.10.8", "wheelSha256": hosted_wheels["core"]["sha256"]},
                   "access": {"version": "0.1.0.dev10", "wheelSha256": hosted_wheels["access"]["sha256"]},
                   "weft": {"version": "0.4.57", "wheelSha256": hosted_wheels["weft"]["sha256"]}}}
    files["evidence/campaign/admission-result.json"] = jbytes(admission_result)
    files["evidence/campaign/census.json"] = jbytes({"total": 130, "nativeExecuted": 0,
        "ledgerSha256": digest(files["source/temporal-native-case-ledger.json"]), "stages": census_stages})
    campaign = {"passed": True, "expectedCounts": qualified.EXPECTED_COUNTS, "expectedTotal": 130,
                "stages": [stages[name] for name in qualified.EXPECTED_COUNTS], "error": None,
                "admissionSha256": digest(files["inputs/admission.json"]),
                "ledgerSha256": digest(files["source/temporal-native-case-ledger.json"]),
                "sourceCommit": commit, "workflowRunId": "123456", "workflowRunAttempt": "2"}
    files["evidence/campaign/campaign-result.json"] = jbytes(campaign)

    def ref(path):
        return {"path": path, "sha256": digest(files[path])}
    candidate_path = "inputs/wheelhouse/umf_truss-0.0.56-py3-none-any.whl"
    original_paths = {owner: {"admissionPath": admission_wheels[owner]["path"],
                              "archivePath": hosted_wheels[owner]["path"], "sha256": hosted_wheels[owner]["sha256"]}
                      for owner in hosted_wheels}
    binding = {"schema": qualified.SCHEMA, "sourceCommit": commit, "sourceTree": tree,
        "cohortSha256": digest(files["source/truss-release-cohort.json"]), "ownerIdentities": owner_identities,
        "originalWheelPaths": original_paths,
        "candidateWheel": {"distribution": "umf-truss", "version": "0.0.56",
            "filename": Path(candidate_path).name, "path": candidate_path, "sha256": digest(wheel), "size": len(wheel)},
        "installed": {"candidateWheelSha256": digest(wheel), "nativeManifestSha256": digest(native_manifest),
                      "runtimeAssets": runtime_assets},
        "componentPrerequisiteReceipts": prereqs,
        "receipts": {"admission": ref("inputs/admission.json"),
            "admissionResult": ref("evidence/campaign/admission-result.json"),
            "campaign": ref("evidence/campaign/campaign-result.json"),
            "ledger": ref("source/temporal-native-case-ledger.json"),
            "census": ref("evidence/campaign/census.json"),
            "cohort": ref("source/truss-release-cohort.json"),
            "hostedInput": ref("inputs/hosted-input.json"),
            "stages": {name: ref(f"evidence/campaign/{name}/result.json") for name in qualified.EXPECTED_COUNTS}},
        "members": {name: {"sha256": digest(raw), "size": len(raw)} for name, raw in files.items()},
        "workflow": {"runId": "123456", "runAttempt": "2", "job": qualified.CAMPAIGN_JOB,
                     "path": qualified.WORKFLOW_PATH, "event": "workflow_dispatch"}}
    bundle = io.BytesIO()
    with ZipFile(bundle, "w") as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)
        archive.writestr("temporal-qualification-binding.json", jbytes(binding))
    return bundle.getvalue(), wheel, commit, tree, binding


class TemporalQualifiedArtifactTests(unittest.TestCase):
    def setUp(self):
        self.archive, self.wheel, self.commit, self.tree, self.binding = fixture()

    def test_original_weft_absolute_refs_use_only_closed_authenticated_archive_map(self):
        absolute, (member, digest) = next(iter(qualified.WEFT_ORIGINAL_RECORDS.items()))
        ref={'path':absolute,'sha256':digest}
        self.assertEqual(qualified.WEFT_ORIGINAL_RECORDS[absolute],(member,digest))
        for bad in ({'path':absolute,'sha256':'0'*64},
                    {'path':'/tmp/other/component.json','sha256':digest},
                    {'path':'/private/tmp/../escape/component.json','sha256':digest}):
            with self.subTest(ref=bad),self.assertRaisesRegex(ValueError,'closed correspondence'):
                qualified._original_weft_record(bad,{member:b'not original bytes'})
        with self.assertRaisesRegex(ValueError,'Missing/mismatched authenticated'):
            qualified._original_weft_record(ref,{})
        with self.assertRaisesRegex(ValueError,'Missing/mismatched authenticated'):
            qualified._original_weft_record(ref,{member:b'wrong bytes'})

    def test_weft_handoff_crossjoins_admitted_wheel_and_original_metadata(self):
        digest_value='a'*64; native='b'*64; shim='c'*64
        handoff={'sourceCommit':'1'*40,'sourceTree':'2'*40,'runID':'41686658658',
            'originalAttempt':1,'actualJobID':'126094501575','actualJobConclusion':'success',
            'wheel':{'sha256':digest_value},'nativeModule':{'sha256':native},'shimSha256':shim}
        section={'sourceCommit':'1'*40,'sourceTree':'2'*40}
        metadata={'run':{'id':41686658658,'run_attempt':1},
            'job':{'id':126094501575,'run_id':41686658658,'run_attempt':1,'conclusion':'success'},
            'artifact':{'workflow_run':{'id':41686658658,'run_attempt':1}}}
        owner={'wheelSha256':digest_value,'moduleSha256':native,'shimSha256':shim}
        admitted={'sha256':digest_value}
        qualified._join_original_weft(handoff,section,metadata,owner,admitted)
        mutations=(
            ({**handoff,'sourceTree':'3'*40},section,metadata,owner,admitted),
            (handoff,section,{**metadata,'run':{**metadata['run'],'id':41686658659}},owner,admitted),
            (handoff,section,{**metadata,'job':{**metadata['job'],'id':1}},owner,admitted),
            (handoff,section,metadata,{**owner,'moduleSha256':'d'*64},admitted),
            (handoff,section,metadata,owner,{'sha256':'e'*64}),
            (handoff,section,{**metadata,'job':{**metadata['job'],'conclusion':'failure'}},owner,admitted),
        )
        for args in mutations:
            with self.subTest(args=args),self.assertRaisesRegex(ValueError,'does not join'):
                qualified._join_original_weft(*args)

    def test_lifecycle_source_tuple_normalizes_to_exact_json_ordered_list(self):
        raw=b"LIFECYCLE2_CASES = ('read-case', 'write-case')\n"
        self.assertEqual(qualified._lifecycle_cases(raw),['read-case','write-case'])
        for source in (b"LIFECYCLE2_CASES = ('read-case',)\n",
                       b"LIFECYCLE2_CASES = ('read-case', 'read-case')\n"):
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'exact two-case|malformed'):
                qualified._lifecycle_cases(source)

    def test_synthetic_130_case_hash_joins_are_structural_only(self):
        files = qualified._read_zip(self.archive)
        binding = json.loads(files["temporal-qualification-binding.json"])
        admission, result, campaign, hosted, component = qualified._validate_campaign(files, binding)
        self.assertEqual((campaign["expectedTotal"], result["wheels"]["truss"]["wheelSha256"],
                          hosted["phase"], len(admission["componentPrerequisiteReceipts"])),
                         (130, digest(self.wheel), "qualify119", 1))
        with self.assertRaisesRegex(ValueError, "Missing trusted component source refs: core"):
            qualified.verify_qualified_bundle(self.archive, self.wheel,
                expected_source_commit=self.commit, expected_source_tree=self.tree)

    def test_original_absolute_runner_wheel_paths_join_only_exact_archive_members(self):
        files = qualified._read_zip(self.archive)
        binding = json.loads(files["temporal-qualification-binding.json"])
        admission = json.loads(files[binding["receipts"]["admission"]["path"]])
        hosted = json.loads(files[binding["receipts"]["hostedInput"]["path"]])
        valid = qualified._runner_wheel_correspondence(admission, hosted)
        self.assertEqual(valid, binding["originalWheelPaths"])
        mutations = (
            lambda a,h: a["wheels"]["core"].update(path="/runner/inputs/other/core.whl"),
            lambda a,h: a["wheels"]["core"].update(path="/runner/elsewhere/wheelhouse/core.whl"),
            lambda a,h: h["wheels"]["core"].update(path=h["wheels"]["weft"]["path"]),
            lambda a,h: h["wheels"]["core"].update(path="elsewhere/core.whl"),
            lambda a,h: h["wheels"]["core"].update(sha256="1"*64),
            lambda a,h: a["wheels"]["core"].update(path="wheelhouse/core.whl"),
        )
        for mutate in mutations:
            changed_admission=json.loads(json.dumps(admission));changed_hosted=json.loads(json.dumps(hosted))
            mutate(changed_admission,changed_hosted)
            with self.subTest(admission=changed_admission["wheels"]["core"],hosted=changed_hosted["wheels"]["core"]), self.assertRaises(ValueError):
                qualified._runner_wheel_correspondence(changed_admission,changed_hosted)

    def test_actual_create_binding_transport_preserves_original_absolute_admission_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary);repo=base/'source';repo.mkdir();input_root=base/'runner-inputs';input_root.mkdir()
            evidence_root=base/'runner-evidence';campaign_dir=evidence_root/'campaign';campaign_dir.mkdir(parents=True)
            files=qualified._read_zip(self.archive)
            binding=json.loads(files['temporal-qualification-binding.json'])
            # Commit only the consumed source inputs; runner inputs/evidence stay outside the checkout.
            source_members={'scripts/truss-release-cohort.json':'source/truss-release-cohort.json',
                'scripts/temporal-native-case-ledger.json':'source/temporal-native-case-ledger.json',
                'scripts/core-validator.py':'source/scripts/core-validator.py'}
            for relative,source_member in source_members.items():
                path=repo/relative;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(files[source_member])
            subprocess.run(['git','init','-q'],cwd=repo,check=True)
            subprocess.run(['git','config','user.email','test@example.invalid'],cwd=repo,check=True)
            subprocess.run(['git','config','user.name','Synthetic Test'],cwd=repo,check=True)
            subprocess.run(['git','add','.'],cwd=repo,check=True)
            subprocess.run(['git','commit','-qm','synthetic source fixture'],cwd=repo,check=True)
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
            tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=repo,text=True).strip()
            hosted=json.loads(files[binding['receipts']['hostedInput']['path']])
            admission=json.loads(files[binding['receipts']['admission']['path']])
            admission['sourceCommit']=commit;admission['sourceTree']=tree
            original_wheelhouse=Path(admission['wheelhouse'])
            admission['wheelhouse']=str(input_root/'wheelhouse')
            for owner,row in admission['wheels'].items():
                row['path']=str(Path(admission['wheelhouse'])/Path(row['path']).relative_to(original_wheelhouse))
            campaign=json.loads(files[binding['receipts']['campaign']['path']])
            campaign['sourceCommit']=commit;campaign['admissionSha256']=digest(jbytes(admission))
            hosted['sourceCommit']=commit;hosted['sourceTree']=tree
            hosted['files']={}
            for member,raw in files.items():
                if member.startswith('inputs/') and member not in ('inputs/hosted-input.json','inputs/admission.json'):
                    relative=member.removeprefix('inputs/')
                    target=input_root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
                    hosted['files'][relative]=digest(raw)
            admission_raw=jbytes(admission);(input_root/'admission.json').write_bytes(admission_raw)
            hosted['files']['admission.json']=digest(admission_raw)
            (input_root/'hosted-input.json').write_bytes(jbytes(hosted))
            (input_root/'verified-input.json').write_text(json.dumps({'admission':str(input_root/'admission.json')}))
            for member,raw in files.items():
                if member.startswith('evidence/'):
                    target=evidence_root/member.removeprefix('evidence/');target.parent.mkdir(parents=True,exist_ok=True)
                    if member=='evidence/campaign/campaign-result.json':raw=jbytes(campaign)
                    target.write_bytes(raw)
            candidate=input_root/binding['originalWheelPaths']['truss']['archivePath']
            created=qualified.create_binding(repo,campaign_dir=campaign_dir,input_root=input_root,
                candidate_wheel=candidate,cohort_path=repo/'scripts/truss-release-cohort.json',
                source_commit=commit,source_tree=tree,workflow_run_id='123456',workflow_run_attempt='2',
                workflow_job=qualified.CAMPAIGN_JOB)
            with self.assertRaisesRegex(ValueError,'Missing trusted component source refs: core'):
                qualified.verify_qualified_bundle(created,candidate.read_bytes(),
                    expected_source_commit=commit,expected_source_tree=tree)
            (repo/'scripts/truss-release-cohort.json').write_bytes(b'changed with unchanged HEAD/tree')
            with self.assertRaisesRegex(ValueError,'Dirty tracked qualification inputs|differs from its committed source bytes'):
                qualified.create_binding(repo,campaign_dir=campaign_dir,input_root=input_root,
                    candidate_wheel=candidate,cohort_path=repo/'scripts/truss-release-cohort.json',
                    source_commit=commit,source_tree=tree,workflow_run_id='123456',workflow_run_attempt='2',
                    workflow_job=qualified.CAMPAIGN_JOB)

    def test_consumed_cohort_ledger_and_validator_must_equal_committed_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            original={'scripts/truss-release-cohort.json':b'cohort source',
                      'scripts/temporal-native-case-ledger.json':b'ledger source',
                      'scripts/core-validator.py':b'validator source'}
            for name,raw in original.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            subprocess.run(['git','init','-q'],cwd=root,check=True)
            subprocess.run(['git','config','user.email','test@example.invalid'],cwd=root,check=True)
            subprocess.run(['git','config','user.name','Synthetic Test'],cwd=root,check=True)
            subprocess.run(['git','add','.'],cwd=root,check=True)
            subprocess.run(['git','commit','-qm','source fixture'],cwd=root,check=True)
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
            tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=root,text=True).strip()
            evidence=root/'docs/helix/04-build/evidence/design-audit/tn14-run'
            evidence.mkdir(parents=True);(evidence/'generated-result.json').write_text('{}')
            paths=list(original)
            self.assertEqual(qualified.committed_source_snapshot(root,commit,tree,paths,evidence_roots=(str(evidence),)),original)
            for name in paths:
                selected=root/name;selected.write_bytes(selected.read_bytes()+b' modified')
                with self.subTest(path=name),self.assertRaisesRegex(ValueError,'Dirty tracked qualification inputs|differs from its committed source bytes'):
                    qualified.committed_source_snapshot(root,commit,tree,paths,evidence_roots=(str(evidence),))
                subprocess.run(['git','checkout','--',name],cwd=root,check=True)
            # Scoped generated campaign evidence is allowed, but source inputs stay byte-bound.
            self.assertEqual(qualified.committed_source_snapshot(root,commit,tree,paths,evidence_roots=(str(evidence),)),original)

    def test_generic_fake_and_nonpassing_prerequisite_receipts_refuse_unmapped_validator(self):
        receipts = ({"scope": "synthetic source test only"},
                    {"schema": "fake/1", "passed": True},
                    {"schema": "fake/1", "passed": False, "status": "failed"})
        for validator_id, receipt in (("synthetic.core.validator/1", receipts[0]),
                                      ("invented.validator/99", receipts[1]),
                                      ("synthetic.core.validator/1", receipts[2])):
            with self.subTest(validator_id=validator_id, receipt=receipt):
                files = {"inputs/receipts/core.json": jbytes(receipt)}
                prereq = {"gateId": "core.synthetic", "validatorId": validator_id,
                          "receiptPath": "inputs/receipts/core.json", "receiptSha256": digest(files["inputs/receipts/core.json"])}
                with self.assertRaisesRegex(ValueError, "Missing trusted component source refs"):
                    qualified.require_closed_component_prerequisites([prereq], files,
                        cohort_bytes=jbytes({"schema":"truss-release-cohort/1"}),
                        owner_identities={}, admitted_wheels={})
        with self.assertRaisesRegex(ValueError, "Missing trusted component source refs"):
            qualified.require_closed_component_prerequisites(
                [{"gateId": "core.synthetic", "receipt": {"passed": True}}], {},
                cohort_bytes=jbytes({"schema":"truss-release-cohort/1"}),
                owner_identities={}, admitted_wheels={})

    def test_fixed_registry_dispatch_uses_only_authenticated_original_member_refs(self):
        with self.assertRaisesRegex(ValueError, "Missing trusted component source refs"):
            qualified.require_closed_component_prerequisites([], {},
                cohort_bytes=jbytes({"schema":"truss-release-cohort/1"}),
                owner_identities={}, admitted_wheels={})

    def test_synthetic_closed_component_graph_runs_real_loaders_registry_and_weft_joins(self):
        import io, zipfile
        import release_cohort
        from test_component_prerequisite_validators import fixture as c1_fixture
        _, template_expected = c1_fixture()
        # Explicitly synthetic Weft records retain the original report/handoff
        # formats. The real closed reader and all digest/source joins still run.
        weft_source='3'*40;weft_tree='4'*40;canonical_core='5'*40;weft_lock='6'*64
        synthetic_module=b'synthetic Weft native module';synthetic_shim=b'synthetic Weft shim'
        wheel_io=io.BytesIO()
        with zipfile.ZipFile(wheel_io,'w') as archive:
            archive.writestr('umf_weft-0.4.57.dist-info/METADATA',b'Metadata-Version: 2.4\nName: umf-weft\nVersion: 0.4.57\n')
            archive.writestr('weft/weft.abi3.so',synthetic_module)
            archive.writestr('weft/__init__.py',synthetic_shim)
        original_weft_wheel=wheel_io.getvalue();weft_wheel_sha=digest(original_weft_wheel)
        weft_native_sha=digest(synthetic_module);weft_shim_sha=digest(synthetic_shim)
        weft_run_id='987654321';weft_job_id='987654322'
        pins={'wheelSha256':weft_wheel_sha,'nativeModuleSha256':weft_native_sha,'shimSha256':weft_shim_sha}
        ws={'sourceCommit':weft_source,'version':'0.4.57','controls':42,'pinsBeforeAfter':pins,
            'checks':[{'id':name,'status':status} for name,status in
                (('read-check','compiled'),('page-check','compiled'),
                 ('read-context-drift','blocked'),('page-context-drift','blocked'))]}
        component={'status':'passed','sourceCommit':weft_source,'sourceTree':weft_tree,
            'canonicalUmf':canonical_core,'cargoLockSha256':weft_lock,'target':'x86_64-unknown-linux-gnu',
            'workflowCommit':weft_source,'producerRunId':int(weft_run_id),'producerRunAttempt':'1',
            'temporalCases':14,'routingControls':5,'sdkControls':42,**pins,
            'stageResults':[{'name':name,'exitCode':0} for name in
                ('normal-install','pip-check','packaging','native-origin','temporal14','routing5','sdk42')]}
        packaging={'status':'passed','version':'0.4.57','wheelSha256':weft_wheel_sha,
            'nativeModuleSha256':weft_native_sha}
        component['sdkReportSha256']=digest(jbytes(ws));component['packagingReportSha256']=digest(jbytes(packaging))
        weft_reports={'component.json':jbytes(component),'sdk-smoke.json':jbytes(ws),
            'packaging.json':jbytes(packaging)}
        wc=component;wp=packaging
        rust_groups={}
        for row in template_expected['rustCases']:
            rust_groups.setdefault((row['package'],row['target']),[]).append({'name':row['name']})
        python_groups=template_expected['pythonGroups']
        source='1'*40;controller=source
        names=('coreSchema','referenceSchema','packageSchema','constraints','domainPolicy',
               'tablesPackage','actionsPackage','bindingPackage','stableBindingPackage')
        resource_members={name:('resource '+name).encode() for name in names}
        resources={name:{'path':'spec/'+name+'.json','bytes':len(resource_members[name]),
                         'sha256':digest(resource_members[name])}
                   for name in names}
        fixture={'bindingStatus':'source-bound','candidateArtifactVersion':'0.10.10',
            'generation':{'sourceCommit':source,'sourceTree':'3'*40,'runId':'10','attempt':'1',
                'jobId':'11','artifactId':'12'},'resources':resources,
            'literalData':{'sha256':'a'*64}}
        census={'installedFactory':{'status':'source-frozen','inputProfile':'installed-canonical/1',
            'currentInputs':{'fixturePath':release_cohort.CORE_SOURCE_ROLES['resourceFixture'],
                'fixtureSHA256':'0'*64,'metadataVersion':'0.10.10'},
            'legacyDisposition':{'oldProbeUnchanged':True,'warmed51IsFactoryEvidence':False,
                'separateExplicitHistory':'synthetic isolated history control'},
            'rust':[{'package':package,'target':target,'cases':cases}
                    for (package,target),cases in rust_groups.items()],
            'python':python_groups,
            'publicControls':template_expected['earlyControls']}}
        corpus={'cases':[{'id':'case-'+str(i),'expected':{'n':i}} for i in range(17)]}
        custody="export const SAGA_QUALIFICATION_INPUTS=['fixtures/saga/portable.json'] as const;"
        raw_by_role={'census':jbytes(census),'resourceFixture':jbytes(fixture),
            'inspectionCorpus':jbytes(corpus),'sagaCorpus':b'{"cases":[]}',
            'sagaCustody':custody.encode()}
        section={'core':{'sourceCommit':source,'controllerSourceCommit':controller,
            'sourceRefs':{},'producerSourceRefs':{},'sagaSourceRefs':[],
            'originalMetadataRefs':{}},'weft':{},'validatorSourceRefs':{}}
        members={**{resources[name]['path']:resource_members[name] for name in names}}
        for role,path in release_cohort.CORE_SOURCE_ROLES.items():
            raw=raw_by_role[role];section['core']['sourceRefs'][role]={'path':path,'sha256':digest(raw)};members[path]=raw
        # The source-controlled Saga roster is the exact literal from custody.
        section['core']['sagaSourceRefs']=[{'path':'fixtures/saga/portable.json','sha256':digest(raw_by_role['sagaCorpus'])}]
        for path in release_cohort.CORE_PRODUCERS:
            raw=(b"LIFECYCLE2_CASES = ('tests/qualification/test_lifecycle.py::test_one', "
                 b"'tests/qualification/test_lifecycle.py::test_two')\n" if path.endswith('run_inspector_attribution_lanes.py')
                 else ('synthetic source '+path).encode())
            section['core']['producerSourceRefs'][path]={'path':path,'sha256':digest(raw)};members[path]=raw
        for role,raw in {'run':jbytes({'id':123,'run_attempt':1,'head_sha':controller,
                             'conclusion':'success','repository':{'full_name':'synthetic/repo'}}),
                         'job':jbytes({'run_id':123,'run_attempt':1,'conclusion':'success',
                             'repository':{'full_name':'synthetic/repo'}}),
                         'artifact':jbytes({'workflow_run':{'id':123},'expired':False}),
                         'sourceAndPayload':jbytes({'sourceCommit':source}),
                         'producer':jbytes({'source':source,'currentInputIdentity':{'scope':'private-candidate-component-only-not-release-proof'}})}.items():
            path='original/'+role+'.json';section['core']['originalMetadataRefs'][role]={'path':path,'sha256':digest(raw)};members[path]=raw
        # This pure integration uses the three preserved original Weft reports
        # behind an explicitly synthetic existing-schema handoff.
        weft=section['weft']
        original_refs={
            'component':('/synthetic/weft/component.json',digest(weft_reports['component.json'])),
            'sdk42':('/synthetic/weft/sdk-smoke.json',digest(weft_reports['sdk-smoke.json'])),
            'installedPackaging':('/synthetic/weft/packaging.json',digest(weft_reports['packaging.json']))}
        handoff={'schema':'weft-final-R-linux-x86-component-handoff/1','sourceCommit':wc['sourceCommit'],
            'sourceTree':wc['sourceTree'],'runID':int(weft_run_id),'originalAttempt':1,'actualJobID':weft_job_id,
            'actualJobConclusion':'success','actualControls':{'temporal':14,'ordinaryPaddedRouting':5,'SDK':42},
            'wheel':{'sha256':wc['wheelSha256']},'nativeModule':{'sha256':wc['nativeModuleSha256']},
            'shimSha256':wc['shimSha256'],**{key:{'path':path,'sha256':sha} for key,(path,sha) in original_refs.items()}}
        handoff_raw=jbytes(handoff)
        weft.update(sourceCommit=weft_source,sourceTree=weft_tree,canonicalCoreSourceCommit=canonical_core,
            cargoLockSha256=wc['cargoLockSha256'],handoff={'path':'weft/handoff.json','sha256':digest(handoff_raw)},
            originalMetadataRefs={},sourceRefs={})
        members['weft/handoff.json']=handoff_raw
        for role,raw in {'run':jbytes({'id':weft_run_id,'run_attempt':1,'head_sha':wc['sourceCommit'],
                             'conclusion':'success','repository':{'full_name':'synthetic/weft'}}),
                         'job':jbytes({'id':weft_job_id,'run_id':weft_run_id,'run_attempt':1,'conclusion':'success',
                             'repository':{'full_name':'synthetic/weft'}}),
                         'artifact':jbytes({'workflow_run':{'id':weft_run_id,'run_attempt':1},'expired':False})}.items():
            path='weft/meta-'+role+'.json';weft['originalMetadataRefs'][role]={'path':path,'sha256':digest(raw)};members[path]=raw
        for role,path in release_cohort.WEFT_SOURCE_ROLES.items():
            raw=('synthetic Weft source '+path).encode();weft['sourceRefs'][role]={'path':path,'sha256':digest(raw)};members[path]=raw
        for role,path in (('component','component.json'),('sdk42','sdk-smoke.json'),('installedPackaging','packaging.json')):
            original_path=original_refs[role][0]
            archive_member='inputs/synthetic-weft/'+path
            members[archive_member]=weft_reports[path]
        synthetic_weft_table={path:('inputs/synthetic-weft/'+filename,digest(weft_reports[filename]))
            for role,(path,_) in original_refs.items()
            for filename in ({'component':'component.json','sdk42':'sdk-smoke.json',
                              'installedPackaging':'packaging.json'}[role],)}
        for role,path in (('coreRegistry','scripts/component_prerequisite_validators.py'),
                          ('weftHandoff','scripts/prepare-temporal-binary-enrollment.py')):
            raw=(Path(__file__).resolve().parents[3]/path).read_bytes()
            section['validatorSourceRefs'][role]={'path':path,'sha256':digest(raw)};members[path]=raw;members['source/'+path]=raw
        cohort={'schema':'truss-release-cohort/1','core':{'distribution':'umf-core','version':'0.10.10'},
                'weft':{'distribution':'umf-weft','version':'0.4.57'},
                'componentPrerequisiteSourceRefs':section}
        cohort_bytes=jbytes(cohort)
        section['core']['sourceRefs']['resourceFixture']['sha256']=digest(raw_by_role['resourceFixture'])
        census['installedFactory']['currentInputs']['fixtureSHA256']=digest(raw_by_role['resourceFixture'])
        raw_by_role['census']=jbytes(census)
        section['core']['sourceRefs']['census']['sha256']=digest(raw_by_role['census'])
        members[release_cohort.CORE_SOURCE_ROLES['census']]=raw_by_role['census']
        cohort['componentPrerequisiteSourceRefs']=section;cohort_bytes=jbytes(cohort)
        wheel_io=io.BytesIO()
        with zipfile.ZipFile(wheel_io,'w') as archive:
            archive.writestr('umf_core-0.10.10.dist-info/METADATA',b'Metadata-Version: 2.4\nName: umf-core\nVersion: 0.10.10\n')
            archive.writestr('umf/_rust_core.abi3.so',b'pure fixture native bytes')
        wheel_raw=wheel_io.getvalue();wheel_sha=digest(wheel_raw);members['wheelhouse/core.whl']=wheel_raw
        weft_raw=original_weft_wheel;weft_sha=digest(weft_raw);members['wheelhouse/weft.whl']=weft_raw
        import zipfile as zf
        with zf.ZipFile(io.BytesIO(weft_raw)) as z:
            module_sha=digest(z.read('weft/weft.abi3.so'));shim_sha=digest(z.read('weft/__init__.py'))
        expected=release_cohort.derive_component_expected(cohort_bytes,members,
            owner_identities={'core':{'sourceCommit':source,'wheelSha256':wheel_sha,
                'wheelPath':'wheelhouse/core.whl','modulePath':'_rust_core.abi3.so',
                'moduleSha256':digest(b'pure fixture native bytes')},
                'weft':{'sourceCommit':wc['sourceCommit'],'wheelSha256':weft_sha,'wheelPath':'wheelhouse/weft.whl',
                'modulePath':'weft.abi3.so','moduleSha256':module_sha,'shimSha256':shim_sha}},
            admitted_wheels={'core':{'path':'wheelhouse/core.whl','sha256':wheel_sha},
                'weft':{'path':'wheelhouse/weft.whl','sha256':weft_sha}})
        self.assertEqual((expected['source'],expected['controllerSource'],len(expected['factoryPairs']),
                          len(expected['rustCases']),len(expected['earlyControls'])),
                         (source,controller,51,477,18))
        from component_prerequisite_validators import FACTORY51,EARLY18,RUST477,PYTHON31,SAGA19,RESOURCES9
        WEFT_SDK_VALIDATOR_ID=qualified.WEFT_SDK_VALIDATOR_ID
        generated,_=c1_fixture(expected)
        prerequisites=[]
        def add_receipt(gate, value, companions=None):
            path='inputs/component/'+gate.replace('/','_')+'.json';raw=jbytes(value);members[path]=raw
            for name,member in (companions or {}).items():members[path.rpartition('/')[0]+'/'+name]=member
            role='weftHandoff' if gate==WEFT_SDK_VALIDATOR_ID else 'coreRegistry'
            validator=section['validatorSourceRefs'][role]
            prerequisites.append({'gateId':gate,'validatorId':gate,'receiptPath':path,'receiptSha256':digest(raw),
                'validatorSourcePath':validator['path'],'validatorSourceSha256':validator['sha256']})
        early=generated[EARLY18];add_receipt(FACTORY51,generated[FACTORY51])
        add_receipt(EARLY18,early['cost'],early['memberBytes'])
        rust=generated[RUST477];rust_companions={'compiled-census.json':rust['compiledBytes']}
        for index,case in enumerate(expected['rustCases']):
            rust_companions[f"rust-cases/{index}-case.log"]=rust['caseLogs'][(case['package'],case['target'],case['name'])]
        add_receipt(RUST477,rust['result'],rust_companions)
        py=generated[PYTHON31];py_companions={f"factory-group-{i}.xml":py['xml'][str(i)] for i in range(len(py['xml']))}
        lifecycle_cases=('tests/qualification/test_lifecycle.py::test_one','tests/qualification/test_lifecycle.py::test_two')
        identity={'artifactSource':source,'controllerSource':controller,'wheelSHA256':expected['wheelSha256'],
            'currentInputIdentity':expected['currentInputIdentity'],'completeWheelAndInstalledRecordVerified':True,
            'distributionOwnershipVerified':True}
        for role in ('identityBefore','identityAfter'):
            raw=jbytes(identity);py_companions[role+'.json']=raw
        py_companions['lifecycle.log']=b'2 lifecycle cases completed successfully\n'
        import xml.etree.ElementTree as ET
        lx=ET.Element('testsuite')
        for selector in lifecycle_cases:
            path,*parts=selector.split('::');ET.SubElement(lx,'testcase',classname=path.removesuffix('.py').replace('/','.'),name=parts[-1])
        py_companions['lifecycle.xml']=ET.tostring(lx)
        lifecycle={'profile':'umf.private-installed-saga-lifecycle2/1','status':'passed','passed':True,
            'source':controller,'run':expected['run'],'attempt':expected['attempt'],'cases':list(lifecycle_cases),
            'publishable':False,'readyForEnrollment':False,'currentInputIdentity':expected['currentInputIdentity'],
            'identityBefore':{'path':'identityBefore.json','sha256':digest(py_companions['identityBefore.json'])},
            'identityAfter':{'path':'identityAfter.json','sha256':digest(py_companions['identityAfter.json'])},
            'log':{'path':'lifecycle.log','sha256':digest(py_companions['lifecycle.log'])},
            'junit':{'path':'lifecycle.xml','sha256':digest(py_companions['lifecycle.xml'])}}
        py_companions['saga-lifecycle2-result.json']=jbytes(lifecycle)
        add_receipt(PYTHON31,py['aggregate'],py_companions);add_receipt(SAGA19,generated[SAGA19])
        add_receipt(RESOURCES9,generated[RESOURCES9]);add_receipt(WEFT_SDK_VALIDATOR_ID,ws)
        # Source refs, bytes, and synthetic identities form a closed test graph.
        files={'source/'+path:raw for path,raw in members.items() if path in (section['validatorSourceRefs']['coreRegistry']['path'],section['validatorSourceRefs']['weftHandoff']['path'])}
        files.update(members)
        for ref in section['validatorSourceRefs'].values():files['source/'+ref['path']]=members[ref['path']]
        owner_identities={'core':{'sourceCommit':source,'wheelSha256':wheel_sha,'wheelPath':'wheelhouse/core.whl',
                'modulePath':'_rust_core.abi3.so','moduleSha256':digest(b'pure fixture native bytes')},
                'weft':{'sourceCommit':wc['sourceCommit'],'wheelSha256':weft_sha,'wheelPath':'wheelhouse/weft.whl',
                    'modulePath':'weft.abi3.so','moduleSha256':module_sha,'shimSha256':shim_sha}}
        admitted_wheels={'core':{'path':'wheelhouse/core.whl','sha256':wheel_sha},
            'weft':{'path':'wheelhouse/weft.whl','sha256':weft_sha}}
        def invoke(selected_prerequisites=prerequisites, selected_files=files, selected_cohort=cohort_bytes):
            with patch.dict(qualified.WEFT_ORIGINAL_RECORDS,synthetic_weft_table,clear=True), \
                    patch.object(qualified,'WEFT_ORIGINAL_JOB',weft_job_id):
                return qualified.require_closed_component_prerequisites(selected_prerequisites,selected_files,
                    cohort_bytes=selected_cohort,owner_identities=owner_identities,admitted_wheels=admitted_wheels)
        result=invoke()
        self.assertEqual(set(result['coreC1']),{FACTORY51,EARLY18,RUST477,PYTHON31,SAGA19,RESOURCES9})
        self.assertEqual(result['weftSDK42'],{'read-check':'compiled','page-check':'compiled',
            'read-context-drift':'blocked','page-context-drift':'blocked'})
        with self.assertRaisesRegex(ValueError,'Missing/mismatched trusted Core C1 resource bytes'):
            damaged=dict(files);damaged.pop('spec/coreSchema.json')
            invoke(selected_files=damaged)
        with self.assertRaisesRegex(ValueError,'receipt path/hash mismatch'):
            damaged=dict(files);damaged[prerequisites[0]['receiptPath']]=b'{"passed":true}'
            invoke(selected_files=damaged)
        bad_cohort=json.loads(cohort_bytes)
        job_ref=bad_cohort['componentPrerequisiteSourceRefs']['weft']['originalMetadataRefs']['job']
        job_path=job_ref['path'];wrong_job=jbytes({'id':'987654323','run_id':weft_run_id,'run_attempt':1,
            'conclusion':'success','repository':{'full_name':'synthetic/weft'}})
        job_ref['sha256']=digest(wrong_job);bad_cohort_bytes=jbytes(bad_cohort)
        damaged=dict(files);damaged[job_path]=wrong_job
        with self.assertRaisesRegex(ValueError,'does not join authenticated raw metadata'):
            invoke(selected_files=damaged,selected_cohort=bad_cohort_bytes)

    def test_same_version_rebuilt_or_substituted_wheel_refuses(self):
        with self.assertRaisesRegex(ValueError, "byte-for-byte"):
            qualified.verify_qualified_bundle(self.archive, self.wheel + b"rebuilt",
                expected_source_commit=self.commit, expected_source_tree=self.tree)

    def test_candidate_wheel_filename_must_be_canonical_basename_joined_to_admitted_path(self):
        for filename in ("../umf_truss-0.0.56-py3-none-any.whl", "/tmp/umf_truss-0.0.56-py3-none-any.whl",
                         "nested/umf_truss-0.0.56-py3-none-any.whl", "nested\\umf_truss-0.0.56-py3-none-any.whl",
                         "umf_truss-0.0.56-py3-none-any.whl\x7f", "other-0.0.56-py3-none-any.whl"):
            with self.subTest(filename=filename):
                files = qualified._read_zip(self.archive)
                binding = json.loads(files["temporal-qualification-binding.json"])
                binding["candidateWheel"]["filename"] = filename
                with self.assertRaisesRegex(ValueError, "filename|path|member|Unsafe"):
                    qualified.verify_qualified_bundle(self.repack(files, binding), self.wheel,
                        expected_source_commit=self.commit, expected_source_tree=self.tree)

    def test_release_staging_rechecks_wheel_bundle_binding_and_artifact_join(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / self.binding["candidateWheel"]["filename"]).write_bytes(self.wheel)
            (root / "temporal-qualified-evidence.zip").write_bytes(self.archive)
            (root / "temporal-qualification-binding.json").write_bytes(jbytes(self.binding))
            (root / "temporal-qualified-member-manifest.json").write_text(json.dumps(self.binding["members"]))
            (root / "temporal-qualification-intake.json").write_text(json.dumps({
                "schema": "truss.temporal-qualified-wheel-intake/1", "sourceCommit": self.commit,
                "sourceTree": self.tree, "candidateWheelSha256": digest(self.wheel),
                "qualifiedBundleSha256": digest(self.archive), "runId": "123456", "runAttempt": "2",
                "artifactId": "7654321", "artifactSha256": "9" * 64,
            }))
            with self.assertRaisesRegex(ValueError, "Missing trusted component source refs: core"):
                qualified.verify_release_staging(root, source_commit=self.commit, source_tree=self.tree)

    def test_owner_wheel_module_hash_mismatch_refuses(self):
        files = qualified._read_zip(self.archive)
        binding = json.loads(files["temporal-qualification-binding.json"])
        hosted_path = binding["receipts"]["hostedInput"]["path"]
        hosted = json.loads(files[hosted_path])
        hosted["ownerIdentities"]["core"]["moduleSha256"] = "1" * 64
        files[hosted_path] = jbytes(hosted)
        with self.assertRaises(ValueError):
            qualified.verify_qualified_bundle(self.repack(files, binding), self.wheel,
                expected_source_commit=self.commit, expected_source_tree=self.tree)

    def test_source_tree_and_commit_movement_refuse(self):
        for commit, tree in (("c" * 40, self.tree), (self.commit, "d" * 40)):
            with self.subTest(commit=commit, tree=tree), self.assertRaisesRegex(ValueError, "source/tree"):
                qualified.verify_qualified_bundle(self.archive, self.wheel,
                    expected_source_commit=commit, expected_source_tree=tree)

    def test_partial_dispatch_references_refuse_and_non_temporal_blank_route_is_preserved(self):
        self.assertIsNone(qualified.validate_dispatch_inputs({}, temporal_candidate=False))
        complete = dict(zip(qualified.INPUT_NAMES, ("123", "456", "a" * 64)))
        for inputs, temporal in (({qualified.INPUT_NAMES[0]: "123"}, False), ({}, True), (complete, False)):
            with self.subTest(inputs=inputs, temporal=temporal), self.assertRaises(ValueError):
                qualified.validate_dispatch_inputs(inputs, temporal_candidate=temporal)

    def test_campaign_count_only_failure_stage_or_skipped_stage_refuses(self):
        files = qualified._read_zip(self.archive)
        binding = json.loads(files["temporal-qualification-binding.json"])
        for mutate in ("count", "stage", "skip"):
            changed = dict(files)
            campaign = json.loads(changed[binding["receipts"]["campaign"]["path"]])
            if mutate == "count":
                campaign["stages"] = []
            else:
                first = dict(campaign["stages"][0])
                if mutate == "stage": first["expectedIds"] = ["synthetic.changed"]
                else: first["skips"] = 1
                campaign["stages"] = [first, *campaign["stages"][1:]]
                changed[binding["receipts"]["stages"][first["stage"]]["path"]] = jbytes(first)
            changed[binding["receipts"]["campaign"]["path"]] = jbytes(campaign)
            bad = self.repack(changed, binding)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                qualified.verify_qualified_bundle(bad, self.wheel,
                    expected_source_commit=self.commit, expected_source_tree=self.tree)

    def test_cleanup_uncertainty_missing_receipt_or_owner_prerequisite_refuses(self):
        files = qualified._read_zip(self.archive)
        binding = json.loads(files["temporal-qualification-binding.json"])
        cleanup_path = "evidence/native/temporal/shared-worker-cleanup.json"
        cleanup = json.loads(files[cleanup_path]); cleanup["originalPostmasterPidAbsent"] = False
        files[cleanup_path] = jbytes(cleanup)
        with self.assertRaises(ValueError):
            qualified.verify_qualified_bundle(self.repack(files, binding), self.wheel,
                expected_source_commit=self.commit, expected_source_tree=self.tree)
        files = qualified._read_zip(self.archive); binding = json.loads(files["temporal-qualification-binding.json"])
        binding["componentPrerequisiteReceipts"] = []
        with self.assertRaisesRegex(ValueError, "Missing owner component"):
            qualified.verify_qualified_bundle(self.repack(files, binding), self.wheel,
                expected_source_commit=self.commit, expected_source_tree=self.tree)

    def test_github_workflow_attempt_job_artifact_and_download_digest_are_bound(self):
        raw = b"original outer artifact ZIP"
        run = {"id": 123456, "event": "workflow_dispatch", "path": qualified.WORKFLOW_PATH,
               "conclusion": "success", "run_attempt": 2, "head_sha": self.commit,
               "repository": {"full_name": "DocumentDrivenDX/truss"}}
        job = {"name": qualified.CAMPAIGN_JOB, "run_id": 123456, "run_attempt": 2, "conclusion": "success"}
        artifact = {"id": 7654321, "name": qualified.CAMPAIGN_ARTIFACT_PREFIX + "123456-2",
                    "expired": False, "digest": "sha256:" + digest(raw), "size_in_bytes": len(raw),
                    "workflow_run": {"id": 123456}}
        qualified.authenticate_github_metadata(run=run, job=job, artifact=artifact,
            repository="DocumentDrivenDX/truss", run_id="123456", artifact_id="7654321",
            artifact_sha256=digest(raw), source_commit=self.commit, artifact_zip=raw)
        for bad in ({**job, "run_attempt": 1}, {**job, "conclusion": "failure"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                qualified.authenticate_github_metadata(run=run, job=bad, artifact=artifact,
                    repository="DocumentDrivenDX/truss", run_id="123456", artifact_id="7654321",
                    artifact_sha256=digest(raw), source_commit=self.commit, artifact_zip=raw)

    def test_archive_rejects_path_escape_duplicate_and_symlink(self):
        for entries in (([("../escape", b"x")]),
                        ([('safe', b"1"), ('safe', b"2")]),
                        ([('link', b"x", 0o120777)])):
            raw = io.BytesIO()
            with ZipFile(raw, "w") as archive:
                for entry in entries:
                    name, data, *mode = entry
                    info = __import__("zipfile").ZipInfo(name)
                    if mode:
                        info.external_attr = mode[0] << 16
                    archive.writestr(info, data)
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                qualified._read_zip(raw.getvalue())

    @staticmethod
    def repack(files, binding):
        files = dict(files)
        binding = dict(binding)
        def update_refs(value):
            if type(value) is dict:
                if set(value) == {"path", "sha256"} and value["path"] in files:
                    value["sha256"] = digest(files[value["path"]])
                else:
                    for nested in value.values(): update_refs(nested)
            elif type(value) is list:
                for nested in value: update_refs(nested)
        update_refs(binding)
        binding["members"] = {name: {"sha256": digest(raw), "size": len(raw)}
                              for name, raw in files.items() if name != "temporal-qualification-binding.json"}
        files["temporal-qualification-binding.json"] = jbytes(binding)
        raw = io.BytesIO()
        with ZipFile(raw, "w") as archive:
            for name, body in files.items(): archive.writestr(name, body)
        return raw.getvalue()


if __name__ == "__main__":
    unittest.main()
