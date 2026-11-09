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

    def test_synthetic_130_case_hash_joins_are_structural_only(self):
        files = qualified._read_zip(self.archive)
        binding = json.loads(files["temporal-qualification-binding.json"])
        admission, result, campaign, hosted = qualified._validate_campaign(files, binding)
        self.assertEqual((campaign["expectedTotal"], result["wheels"]["truss"]["wheelSha256"],
                          hosted["phase"], len(admission["componentPrerequisiteReceipts"])),
                         (130, digest(self.wheel), "qualify119", 1))
        with self.assertRaisesRegex(ValueError, "Unmapped component prerequisite validator"):
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
            with self.assertRaisesRegex(ValueError,'Unmapped component prerequisite validator'):
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
                with self.assertRaisesRegex(ValueError, "Unmapped component prerequisite validator"):
                    qualified.require_closed_component_prerequisites([prereq], files)
        with self.assertRaisesRegex(ValueError, "Unmapped component prerequisite validator"):
            qualified.require_closed_component_prerequisites(
                [{"gateId": "core.synthetic", "receipt": {"passed": True}}], {})

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
            with self.assertRaisesRegex(ValueError, "Unmapped component prerequisite validator"):
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
