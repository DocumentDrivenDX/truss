"""Pure structural discriminators for current Core C1 original result schemas.

Synthetic outputs exercise validator behavior only; they do not qualify a Core
artifact or stand in for original producer receipts.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[3] / "scripts/component_prerequisite_validators.py"
SPEC = importlib.util.spec_from_file_location("component_prerequisite_validators", MODULE)
assert SPEC is not None and SPEC.loader is not None
validators = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validators)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def junit(selectors):
    import xml.etree.ElementTree as ET
    root = ET.Element("testsuite")
    for selector in selectors:
        path, *parts = selector.split("::")
        classname = ".".join([path.removesuffix(".py").replace("/", "."), *parts[:-1]])
        ET.SubElement(root, "testcase", classname=classname, name=parts[-1])
    return ET.tostring(root)


def fixture(expected_override=None):
    resource_rows = [
        {"name": name, "path": f"resources/{name}", "bytes": i + 10, "sha256": f"{i + 1:064x}"}
        for i, name in enumerate(validators.RESOURCE_NAMES)
    ]
    manifest = {"profile": "umf.codegen.installed-source-manifest/1",
                "inputProfile": validators.FACTORY_INPUT, "resources": resource_rows}
    current = {"resourceFixtureSHA256": "f" * 64, "source": "fixture"}
    pairs = [{"case": f"case-{i}", "carrier": carrier, "resultSHA256": f"{i + 1:064x}"}
             for i in range(17) for carrier in ("dispatcher", "list", "tuple")]
    early = [f"tests/qualification/test_public.py::test_early_{i}" for i in range(18)]
    rust = [{"package": "umf-core", "target": "lib", "name": f"module_{i // 10}::rust_{i}"} for i in range(300)]
    rust += [{"package": "umf-schema", "target": "test:catalog", "name": f"schema_{i}"} for i in range(177)]
    groups = [{"group": "group-0", "cases": [f"tests/qualification/test_semantics.py::test_semantic_{i}" for i in range(16)]},
              {"group": "group-1", "cases": [f"tests/qualification/test_legacy.py::test_legacy_{i}" for i in range(15)]}]
    saga_inputs = {"fixtures/corpus.json": "a" * 64, "scripts/saga-portable/custody.ts": "b" * 64}
    expected = {"source": "1" * 40, "controllerSource": "2" * 40, "wheelSha256": "3" * 64,
                "nativeSha256": "4" * 64, "censusSha256": "5" * 64, "run": "123", "attempt": "2",
                "currentInputIdentity": current, "resourceManifest": manifest, "factoryPairs": pairs,
                "earlyControls": early, "rustCases": rust, "pythonGroups": groups,
                "sagaCorpusSha256": "6" * 64, "sagaInputs": saga_inputs}
    if expected_override is not None:
        expected = expected_override
        current = expected["currentInputIdentity"]
        manifest = expected["resourceManifest"]
        pairs = expected["factoryPairs"]
        early = expected["earlyControls"]
        rust = expected["rustCases"]
        groups = expected["pythonGroups"]
        saga_inputs = expected["sagaInputs"]
    actual_manifest = copy.deepcopy(manifest)
    for resource in actual_manifest["resources"]:
        resource["bytes"] = float(resource["bytes"])
    xml = junit(early)
    identity = {"profile": "umf.private-retained-installed-identity/1", "artifactSource": expected["source"],
                "controllerSource": expected["controllerSource"], "wheelSHA256": expected["wheelSha256"],
                "distributionOwnershipVerified": True, "completeWheelAndInstalledRecordVerified": True,
                "loadedModules": {"umf/_rust_core.abi3.so": {"sha256": expected["nativeSha256"]},
                                  "module-1": {}, "module-2": {}, "module-3": {}}}
    installed = {"status": "passed", "wheel_sha256": expected["wheelSha256"],
                 "native_sha256": expected["nativeSha256"]}
    member_bytes = {"public-controls.xml": xml, "measurement.json": b"pending measurement"}
    for when in ("before", "after"):
        member_bytes[f"identity-cost-{when}.json"] = canonical(identity)
        member_bytes[f"installed-record-cost-{when}.json"] = canonical(installed)
    members = {name: {"bytes": len(member_bytes[name]), "sha256": sha(member_bytes[name])}
               for name in validators.COST_MEMBERS}
    cost = {"profile": validators.CORE_COST_PROFILE, "inputProfile": validators.FACTORY_INPUT,
            "artifactSource": expected["source"], "controllerSource": expected["controllerSource"],
            "wheelSHA256": expected["wheelSha256"], "nativeSHA256": expected["nativeSha256"],
            "run": expected["run"], "attempt": expected["attempt"],
            "censusSHA256": expected["censusSha256"], "currentInputIdentity": current,
            "status": "cost-gate-passed", "fullyQualified": False, "requiredQualificationPassed": False,
            "publishable": False, "readyForEnrollment": False, "identityBeforePassed": True,
            "identityAfterPassed": True, "publicProbePassed": True, "publicControlsPassed": True,
            "expensiveTestCompilationAdmitted": True, "publicControlsExecution": "COMPLETED", "members": members}
    factory_pairs = []
    for pair in pairs:
        row = {"case": pair["case"], "carrier": pair["carrier"], "resultSHA256": pair["resultSHA256"],
               "completed": True, "sourceManifest": actual_manifest, "manifestSHA256": sha(canonical(actual_manifest))}
        for stage in ("constructor", "call", "manifest"):
            row[stage] = {"completed": True, "workCreated": True, "maximumWork": 1_000_000,
                          "returnedWork": 1, "attemptedWork": 1}
        factory_pairs.append(row)
    measurement = {"profile": validators.FACTORY_PROFILE, "inputProfile": validators.FACTORY_INPUT,
                   "status": "cost-complete", "actualCandidateSource": expected["source"],
                   "wheelSHA256": expected["wheelSha256"], "nativeSHA256": expected["nativeSha256"],
                   "closureSHA256": "7" * 64, "currentInputIdentity": current,
                   "maximumWork": 1_000_000, "inspectionCases": 17, "inspectionCalls": 51,
                   "freshConstructors": 51, "requestCustodyPreserved": True, "installedFilesUnchanged": True,
                   "publishable": False, "readyForEnrollment": False, "pairs": factory_pairs}
    member_bytes["measurement.json"] = canonical(measurement)
    cost["members"]["measurement.json"] = {"bytes": len(member_bytes["measurement.json"]),
                                               "sha256": sha(member_bytes["measurement.json"])}
    case_logs = {tuple((case["package"], case["target"], case["name"])):
                 f"running 1 test\ntest {case['name']} ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out\n".encode()
                 for case in rust}
    rust_results = [{**case, "passed": True, "exit": 0,
                     "logSHA256": sha(case_logs[(case["package"], case["target"], case["name"])])} for case in rust]
    compiled = {"source": expected["controllerSource"], "status": "authenticated-before-test-execution",
                "selectedCases": 477, "censusSHA256": expected["censusSha256"], "targets": [
                    {"package": "umf-core", "target": "lib", "executable": "/owned/a", "sha256": "9" * 64,
                     "listingSHA256": "a" * 64, "caseNames": [x["name"] for x in rust if x["package"] == "umf-core"] + ["unrelated_module::not_selected"]},
                    {"package": "umf-schema", "target": "test:catalog", "executable": "/owned/b", "sha256": "b" * 64,
                     "listingSHA256": "c" * 64, "caseNames": [x["name"] for x in rust if x["package"] == "umf-schema"]}]}
    rust_result = {"source": expected["source"], "status": "passed", "cases": 477, "passed": 477,
                   "censusSHA256": expected["censusSha256"], "compiledCensusSHA256": sha(canonical(compiled)),
                   "results": rust_results}
    group_xmls = {str(i): junit(g["cases"]) for i, g in enumerate(groups)}
    python_groups = [{"group": g["group"], "cases": g["cases"], "passed": True,
                      "xmlSHA256": sha(group_xmls[str(i)])} for i, g in enumerate(groups)]
    aggregate = {"profile": "umf.private-installed-factory-semantics/1", "inputProfile": validators.FACTORY_INPUT,
                 "artifactSource": expected["source"], "controllerSource": expected["controllerSource"],
                 "wheelSHA256": expected["wheelSha256"], "currentInputIdentity": current,
                 "costGateAuthenticated": True, "rustPassed": True, "sagaPassed": True,
                 "finalIdentityPassed": True, "requiredQualificationPassed": True,
                 "publishable": False, "readyForEnrollment": False, "pythonGroups": python_groups}
    saga = {"profile": "umf.saga.portable-host-receipt/2", "hostId": "python",
            "runtime": {"python": "3.11.17", "platform": "Linux", "arch": "x86_64"},
            "corpusSha256": expected["sagaCorpusSha256"], "qualificationInputs": saga_inputs,
            "cases": 19, "passed": 19, "results": [{"id": f"saga-{i}", "passed": True} for i in range(19)],
            "installedBinding": {"status": "passed", "wheelSha256": expected["wheelSha256"],
                                 "beforeNativeSha256": expected["nativeSha256"],
                                 "afterNativeSha256": expected["nativeSha256"]}}
    receipts = {validators.FACTORY51: measurement,
                validators.EARLY18: {"cost": cost, "xml": xml, "memberBytes": member_bytes},
                validators.RUST477: {"result": rust_result, "compiled": compiled, "compiledBytes": canonical(compiled), "caseLogs": case_logs},
                validators.PYTHON31: {"aggregate": aggregate, "xml": group_xmls},
                validators.SAGA19: saga, validators.RESOURCES9: actual_manifest}
    return receipts, expected


class CurrentC1PrerequisiteValidatorsTests(unittest.TestCase):
    def test_complete_six_original_c1_outputs_bind_exact_results(self):
        receipts, expected = fixture()
        result = validators.validate_component_prerequisites(receipts, expected)
        self.assertEqual(set(result), validators.REQUIRED)
        self.assertTrue(all(row["validated"] is True for row in result.values()))

    def test_existing_weft_owner_receipt_formats_cover_platform_sdk_browser_and_source_closure(self):
        source, tree = "1" * 40, "2" * 40
        canonical_umf, lock = "3" * 40, "4" * 64
        roles = {
            "linux-x86_64": ("x86_64-unknown-linux-gnu", "5" * 64, "6" * 64, "7" * 64, "123", None),
            "linux-aarch64": ("aarch64-unknown-linux-gnu", "8" * 64, "9" * 64, "a" * 64, "124", "b" * 40),
            "macos-arm64": ("aarch64-apple-darwin", "c" * 64, "d" * 64, "e" * 64, "125", "f" * 40),
        }
        wheel_names = {
            "linux-x86_64": "umf_weft-0.4.57-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            "linux-aarch64": "umf_weft-0.4.57-cp39-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            "macos-arm64": "umf_weft-0.4.57-cp39-abi3-macosx_11_0_arm64.whl",
        }
        profiles = {"linux-aarch64": "weft-current-arm64-controller-pair/1",
                    "macos-arm64": "weft-current-macos-controller-pair/1"}
        controllers = {"linux-aarch64": ("b" * 40, "c" * 40), "macos-arm64": ("f" * 40, "d" * 40)}
        platforms, qualification_wheels, observations, registration_pairs = {}, [], [], {}
        for platform, (target, wheel, native, shim, run_id, _) in roles.items():
            sdk_hash, packaging_hash = hashlib.sha256((platform + " sdk").encode()).hexdigest(), hashlib.sha256((platform + " packaging").encode()).hexdigest()
            checks = [{"id": k, "status": v} for k, v in validators.WEFT_ORIGINAL_CHECK_CALLS.items()]
            sdk = {"sourceCommit": source, "version": "0.4.57", "controls": 42,
                   "pinsBeforeAfter": {"wheelSha256": wheel, "nativeModuleSha256": native, "shimSha256": shim},
                   "checks": checks}
            packaging = {"status": "passed", "version": "0.4.57", "wheelSha256": wheel,
                         "nativeModuleSha256": native}
            profile = profiles.get(platform)
            component = {"status": "passed", "sourceCommit": source, "sourceTree": tree,
                         "workflowCommit": source if profile is None else controllers[platform][0],
                         "target": target, "canonicalUmf": canonical_umf, "cargoLockSha256": lock,
                         "nativeAdmission": False, "publicationAdmission": False,
                         "producerRunId": int(run_id), "producerRunAttempt": 1,
                         "wheelSha256": wheel, "nativeModuleSha256": native, "shimSha256": shim,
                         "sdkReportSha256": sdk_hash, "packagingReportSha256": packaging_hash}
            stage_key = "stageResults" if profile is None else "sdkStages"
            component[stage_key] = [{"name": "sdk42", "exitCode": 0}]
            if profile is not None:
                component.update(profile=profile, producerJobName="macos-pair" if platform == "macos-arm64" else "arm64-pair",
                    controllerCommit=controllers[platform][0], controllerTree=controllers[platform][1])
                registration_pairs["macos" if platform == "macos-arm64" else "arm64"] = {
                    "status": "reviewed", "sourceCommit": source, "sourceTree": tree,
                    "profile": profile, "controllerCommit": controllers[platform][0],
                    "controllerTree": controllers[platform][1]}
            else:
                component["producerRunConclusion"] = "success"
            platforms[platform] = {"component": component, "sdk": sdk, "packaging": packaging,
                                   "reportDigests": {"sdk": sdk_hash, "packaging": packaging_hash}}
            wheel_row = {"target": target, "wheelSha256": wheel, "nativeModuleSha256": native,
                         "shimSha256": shim, "sdkReportSha256": sdk_hash,
                         "packagingReportSha256": packaging_hash}
            if profile is not None:
                wheel_row.update(profile=profile, controllerCommit=controllers[platform][0],
                                 controllerTree=controllers[platform][1])
            qualification_wheels.append(wheel_row)
            observation = {"target": target, "runID": int(run_id), "originalAttempt": 1}
            if profile is None:
                observation["finalRunConclusion"] = "success"
            else:
                observation["actualJob"] = int(run_id) + 1000
            observations.append(observation)
        pins = {"schema": "weft-hosted-release-pins/1", "tag": "v0.4.57", "version": "0.4.57",
                "distribution": "umf-weft", "sourceCommit": source, "commit": source,
                "currentQualification": {"status": "checked", "profile": "weft-current-three-wheel-sdk-controller-pairs/1",
                    "sourceCommit": source, "sourceTree": tree,
                    "registration": {"schema": "weft-0457-controller-pair-registration/1"},
                    "wheels": qualification_wheels, "actualGitHubObservations": observations},
                "wheelSha256": {wheel_names[k]: row[1] for k, row in roles.items()}}
        registration = {"schema": "weft-0457-controller-pair-registration/1", "status": "reviewed",
                        "sourceCommit": source, "sourceTree": tree, **registration_pairs}
        wasm = {"status": "passed", "sourceCommit": source, "sourceTree": tree,
                "workflowCommit": source,
                "canonicalUmf": "git+https://github.com/DocumentDrivenDX/umf.git?rev=" + canonical_umf + "#" + canonical_umf,
                "cargoLockSha256": lock, "target": "wasm32-unknown-unknown", "NodeCases": 14,
                "ChromiumCases": 14, "nativeDatabaseExecution": False, "publicationAdmission": False}
        browser_summary = {"cases": 9, "byteParity": True, "wasmSha256": "9" * 64,
                           "browser": "151.0.7922.34", "playwrightVersion": "1.62.1"}
        release_assets = {"schema": "weft-release-assets/1", "sourceCommit": source,
            "status": "verified-before-publication", "expectedWheelCount": 3,
            "wheels": pins["wheelSha256"],
            "assetSha256": {name: "a" * 64 for name in ("SHA256SUMS", "release-pins.json",
                "current-controller-pair-registration.json", "current-wasm-manifest.json",
                "macos-browser-compiler-parity.json", "macos-browser-compiler-receipts.json",
                "current-source-manifest.json")}}
        records = {"releasePins": pins, "platforms": platforms, "wasmManifest": wasm,
            "controllerRegistration": registration, "browserParity": browser_summary,
            "browserReceipts": {"summary": browser_summary, "cases": [{"id": str(i)} for i in range(9)]},
            "releaseAssetDigests": release_assets}
        result = validators._validate_weft_published_owner_records(records, source_commit=source,
            source_tree=tree, canonical_umf=canonical_umf, cargo_lock_sha256=lock)
        self.assertEqual(result["platforms"], tuple(sorted(roles)))
        self.assertEqual((result["nodeCases"], result["chromiumCases"], result["browserCases"]), (14, 14, 9))
        broken = {**records, "platforms": dict(platforms)}
        del broken["platforms"]["macos-arm64"]
        with self.assertRaisesRegex(validators.Refusal, "three original Weft platform"):
            validators._validate_weft_published_owner_records(broken, source_commit=source,
                source_tree=tree, canonical_umf=canonical_umf, cargo_lock_sha256=lock)

    def test_missing_unknown_and_malformed_gate_ids_refuse(self):
        receipts, expected = fixture()
        del receipts[validators.SAGA19]
        with self.assertRaises(validators.Refusal):
            validators.validate_component_prerequisites(receipts, expected)
        receipts, expected = fixture()
        receipts["caller.selected-validator"] = receipts.pop(validators.SAGA19)
        with self.assertRaises(validators.Refusal):
            validators.validate_component_prerequisites(receipts, expected)

    def test_factory_manifest_or_pair_digest_must_match_source_oracle(self):
        receipts, expected = fixture()
        receipts[validators.FACTORY51]["pairs"][0]["resultSHA256"] = "f" * 64
        with self.assertRaises(validators.Refusal):
            validators.validate_one_component_prerequisite(validators.FACTORY51, receipts[validators.FACTORY51], expected)
        receipts, expected = fixture()
        receipts[validators.FACTORY51]["pairs"][0]["sourceManifest"]["resources"][0]["sha256"] = "f" * 64
        with self.assertRaises(validators.Refusal):
            validators.validate_one_component_prerequisite(validators.FACTORY51, receipts[validators.FACTORY51], expected)

    def test_early18_junit_exact_names_and_failed_skip_are_refused(self):
        receipts, expected = fixture()
        receipts[validators.EARLY18]["xml"] = receipts[validators.EARLY18]["xml"].replace(b"test_early_0", b"test_other_0")
        with self.assertRaises(validators.Refusal):
            validators.validate_one_component_prerequisite(validators.EARLY18, receipts[validators.EARLY18], expected)

    def test_rust477_original_named_rows_and_compiled_listing_are_bound(self):
        receipts, expected = fixture()
        good = receipts[validators.RUST477]
        self.assertEqual(validators.validate_one_component_prerequisite(
            validators.RUST477, good, expected)["validated"], True)
        changed = copy.deepcopy(good)
        changed["result"]["results"][0]["passed"] = False
        with self.assertRaises(validators.Refusal):
            validators.validate_one_component_prerequisite(validators.RUST477, changed, expected)

        def check_listing_mutation(target_index, mutate):
            receipts, pins = fixture()
            bundle = receipts[validators.RUST477]
            names = bundle["compiled"]["targets"][target_index]["caseNames"]
            mutate(names)
            bundle["compiledBytes"] = canonical(bundle["compiled"])
            bundle["result"]["compiledCensusSHA256"] = sha(bundle["compiledBytes"])
            with self.assertRaises(validators.Refusal):
                validators.validate_one_component_prerequisite(validators.RUST477, bundle, pins)

        check_listing_mutation(0, lambda names: names.append("module_0::unapproved"))
        check_listing_mutation(0, lambda names: names.remove("module_0::rust_0"))
        check_listing_mutation(0, lambda names: names.append("module_0::rust_0"))
        check_listing_mutation(1, lambda names: names.append("unapproved_integration_case"))

        receipts, expected = fixture()
        self.assertIn("unrelated_module::not_selected", receipts[validators.RUST477]["compiled"]["targets"][0]["caseNames"])
        self.assertEqual(validators.validate_one_component_prerequisite(
            validators.RUST477, receipts[validators.RUST477], expected)["validated"], True)
        receipts, expected = fixture()
        bundle = receipts[validators.RUST477]
        bundle["caseLogs"][("umf-core", "lib", "module_0::rust_0")] = b"1 failed"
        with self.assertRaises(validators.Refusal):
            validators.validate_one_component_prerequisite(validators.RUST477, bundle, expected)

    def test_python31_group_names_xml_and_run_identity_are_required(self):
        receipts, expected = fixture()
        receipts[validators.PYTHON31]["aggregate"]["pythonGroups"][1]["passed"] = False
        with self.assertRaises(validators.Refusal):
            validators.validate_one_component_prerequisite(validators.PYTHON31, receipts[validators.PYTHON31], expected)
        receipts, expected = fixture()
        receipts[validators.EARLY18]["cost"]["attempt"] = "3"
        with self.assertRaises(validators.Refusal):
            validators.validate_one_component_prerequisite(validators.EARLY18, receipts[validators.EARLY18], expected)

    def test_weft_four_existing_sdk_check_calls_join_original_owner_pins(self):
        pins = {"wheelSha256": "c" * 64, "nativeModuleSha256": "d" * 64, "shimSha256": "e" * 64}
        report = {"sourceCommit": "a" * 40, "version": "0.4.57", "controls": 42,
                  "pinsBeforeAfter": pins,
                  "checks": [{"id": "read-check", "status": "compiled"},
                             {"id": "page-check", "status": "compiled"},
                             {"id": "read-context-drift", "status": "blocked"},
                             {"id": "page-context-drift", "status": "blocked"}]}
        self.assertEqual(validators.validate_weft_existing_sdk_checks(
            report, source_commit="a" * 40, pins_before_after=pins), validators.WEFT_ORIGINAL_CHECK_CALLS)
        for mutate in (
            lambda value: value["checks"].pop(),
            lambda value: value["checks"][0].update(status="blocked"),
            lambda value: value["checks"].append({"id": "read-check", "status": "compiled"}),
            lambda value: value.update(sourceCommit="f" * 40),
            lambda value: value["pinsBeforeAfter"].update(wheelSha256="f" * 64),
        ):
            changed = copy.deepcopy(report)
            mutate(changed)
            with self.assertRaises(validators.Refusal):
                validators.validate_weft_existing_sdk_checks(
                    changed, source_commit="a" * 40, pins_before_after=pins)

    def test_saga19_and_nine_resource_source_roster_are_exact(self):
        receipts, expected = fixture()
        del receipts[validators.SAGA19]["results"][0]
        with self.assertRaises(validators.Refusal):
            validators.validate_one_component_prerequisite(validators.SAGA19, receipts[validators.SAGA19], expected)
        receipts, expected = fixture()
        receipts[validators.RESOURCES9]["resources"].pop()
        with self.assertRaises(validators.Refusal):
            validators.validate_one_component_prerequisite(validators.RESOURCES9, receipts[validators.RESOURCES9], expected)



# Clearly synthetic ORIGINAL-shaped bytes, never owner qualification evidence.
def core_owner_fixture():
    import io, tarfile, zipfile
    from datetime import datetime
    source_commit, controller, authority = '1'*40, '2'*40, '3'*40
    version='0.10.10'
    script,workflow=b'SYNTHETIC reviewed SDK controller bytes',b'SYNTHETIC reviewed workflow bytes'
    ctrl={'commit':controller,'tree':'4'*40,'script_sha256':sha(script),'workflow_sha256':sha(workflow)}
    sources={'scripts/test-sdk-install.ts':b'SYNTHETIC full139 and separate Saga source',
             'scripts/test-native-sdk-install.mjs':b'SYNTHETIC node/browser source',
             'scripts/saga-portable/installed-browser.ts':b'SYNTHETIC Chromium source',
             'crates/umf-core/src/canonical_codegen_literals.rs':b'SYNTHETIC DATA',
             'python/src/umf/action_runtime_resource_manifest.json':b'{}',
             'fixtures/saga/portable.json':b'{"cases":[]}',
             'tests/qualification/fixtures/inspector-construction-batch.json':b'SYNTHETIC census'}
    for name,path in zip(validators.RESOURCE_NAMES, ('spec/core/schema.json','spec/core/semantic-type-reference.schema.json','spec/core/extension-package.schema.json','spec/metamodel/generated/core-constraints.json','spec/metamodel/generated/domain-policy.json','spec/extensions/tables/package.json','spec/extensions/actions/package.json','spec/extensions/binding/package.json','spec/extensions/binding-stable/package.json')):sources[path]=name.encode()
    early=['python/tests/test_synthetic.py::test_early_'+str(i) for i in range(18)]
    later=['python/tests/test_synthetic.py::test_later_'+str(i) for i in range(31)]
    historical=['python/tests/test_retained_codegen_native.py::PublicRetainedFeasibilityTests::test_cold_constructor_and_each_17_vector_dispatch_list_tuple_call_fit_strict_1m']
    sources['tests/qualification/fixtures/inspector-construction-batch.json']=canonical({'installedFactory':{'publicControls':early,'python':[{'cases':later}], 'legacyDisposition':{'historicalOnly':historical}}})
    for path in ('python/hatch_build.py','python/umf_codegen/hatch_build.py','tools/verify_python_artifacts.py','tools/qualify_python_release_wheel.py','scripts/package-sdk-rust-default.ts','scripts/package-sdk.py','tools/generate_codegen_resource_literals.py'):sources[path]=('SYNTHETIC canonical recipe '+path).encode()
    def tar_bytes(mapping,prefix=''):
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w') as tar:
            for name,raw in sorted(mapping.items()):
                row=tarfile.TarInfo(prefix+name);row.mode=0o644;row.size=len(raw);tar.addfile(row,io.BytesIO(raw))
        return buf.getvalue()
    def git_tree(mapping):
        tree={}
        for path,raw in mapping.items():
            row=tree;parts=path.split('/')
            for name in parts[:-1]:row=row.setdefault(name,{})
            row[parts[-1]]=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).digest()
        def walk(row):
            data=b''
            for name,value in sorted(row.items(),key=lambda item:item[0]+('/' if isinstance(item[1],dict) else '')):
                directory=isinstance(value,dict);data+=(b'40000' if directory else b'100644')+b' '+name.encode()+b'\0'+(walk(value) if directory else value)
            return hashlib.sha1(b'tree '+str(len(data)).encode()+b'\0'+data).digest()
        return walk(tree).hex()
    src={'commit':source_commit,'tree':git_tree(sources)}
    protocols={'semantic':'0.10.0','engine':'umf-core-r2','codegen':'umf-codegen-r3-seven-ops-nine-resources/1'}
    inputs={p:sha(b) for p,b in sources.items()}
    resources={'action_runtime_resources/'+n+'.json':sha(n.encode()) for n in validators.RESOURCE_NAMES}
    recipes={p:inputs[p] for p in sources if p.startswith(('scripts/','tools/')) or p.endswith('hatch_build.py')}
    compatibility={'census_sha256':inputs['tests/qualification/fixtures/inspector-construction-batch.json'],
                   'early':early,'later':later,'historicalExcluded':historical}
    source_raw=tar_bytes(sources,'umf-v'+version+'/')
    def wheel(native):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('umf_core-'+version+'.dist-info/METADATA','Name: umf-core\nVersion: '+version+'\n')
            z.writestr('umf/_rust_core.abi3.so',native);z.writestr('umf/_bin/umf',b'SYNTHETIC embedded CLI')
            z.writestr('umf/__init__.py',b'SYNTHETIC package')
        return out.getvalue()
    sdk_files={name:('SYNTHETIC SDK '+name).encode() for name in ('dist/umf-node.js','dist/umf-browser.js','dist/rust-default-manifest.json','dist/umf_core_node.node','dist/loader-contract.js','dist/runtime/wasm/index.js','dist/runtime/wasm/pkg/umf_core_wasm.js','dist/runtime/wasm/pkg/umf_core_wasm_bg.wasm')}
    sdk_files['package.json']=canonical({'name':'@umf/core','version':version})
    sdk_manifest=canonical({'profile':'umf.sdk.distribution.rust-default/1','sha256':{n:sha(v) for n,v in sdk_files.items()}})
    sdk_files['manifest.json']=sdk_manifest
    sdk_raw=tar_bytes(sdk_files,'package/')
    sdk_members={'package/'+n:{'size':len(b),'sha256':sha(b)} for n,b in sdk_files.items()}
    codegen_buffer=io.BytesIO()
    with zipfile.ZipFile(codegen_buffer,'w') as z:z.writestr('umf_codegen-'+version+'.dist-info/METADATA','Name: umf-codegen\nVersion: '+version+'\nRequires-Dist: umf-core=='+version+'\n')
    common={'source':('full-source.tar',source_raw),'core-sdist':('umf_core-'+version+'.tar.gz',b'SYNTHETIC core sdist'),
            'codegen-wheel':('umf_codegen-'+version+'-py3-none-any.whl',codegen_buffer.getvalue()),
            'codegen-sdist':('umf_codegen-'+version+'.tar.gz',b'SYNTHETIC Codegen sdist')}
    roster={}
    for role,(name,raw) in common.items():
        roster[role]={'name':name,'platform':'linux-x86_64','member':name if role=='source' else 'common/'+name,'sha256':sha(raw),'bytes':len(raw),'mode':0o644}
    all_components=[];materials={};bindings={};native_by_platform={}
    for index,platform in enumerate(validators.CORE_PLATFORMS):
        native=('SYNTHETIC '+platform).encode();native_by_platform[platform]=sha(native)
        direct=wheel(native);rebuilt=wheel(native+b' REBUILT DISTINCT');standalone=b'SYNTHETIC standalone '+platform.encode()
        hosts={'core-wheel':('selected/core-'+platform+'.whl',direct),'standalone-cli':('standalone-'+platform,standalone),
               'sdk':('umf-sdk-'+platform+'.tgz',sdk_raw),'sdk-manifest':('sdk-manifest.json',sdk_manifest)}
        for role,(name,raw) in hosts.items():roster[platform+'/'+role]={'name':name.split('/')[-1],'platform':platform,'member':name,'sha256':sha(raw),'bytes':len(raw),'mode':0o755 if role=='standalone-cli' else 0o644}
        a={'id':'synthetic-'+platform,'profile':'umf.core-successor.candidate/2','purpose':'candidate-production','source':src,'controller':ctrl,'version':version,'platform':platform,'inputs':inputs,'recipes':recipes,'resources':resources,'protocols':protocols,'compatibility':compatibility,'common':None,'continuation':None,'bounds':{'workers':1,'seconds':5400,'log_bytes':1048576,'artifact_bytes':67108864}}
        original={'run':str(100+index),'job':str(200+index),'attempt':'1','workflow_sha':'5'*40,'controller_sha':controller,'platform':platform,'job_name':'linux' if index==0 else 'macos','upload_step':validators.CORE_UPLOAD}
        members={row['member']:common[role][1] for role,row in roster.items() if role in common}
        members.update({name:raw for name,raw in hosts.values()});members['raw/original.whl']=direct;members['rebuilt/rebuilt.whl']=rebuilt
        def save(name,value):members[name]=(json.dumps(value,indent=2)+'\n').encode();return {'path':name,'sha256':sha(members[name])}
        rebuild_receipt={'schema':'umf.python-artifact-qualification/1','source_payload_verification':'passed','distribution_version':version,'artifacts':{'sdist_rebuilt':{'sha256':sha(rebuilt)}}}
        save('core-artifact.json',rebuild_receipt)
        step_values={'job-setup':{'acquiredThisJob':True},'source':{'allModesSymlinksAndBlobBytesMatch':True,'tar_sha256':sha(source_raw)},'common':{'files':{row['name']:row['sha256'] for role,row in roster.items() if role in common and role!='source'}},
                     'wheel':{'wheel':sha(direct),'rawWheel':sha(direct),'standaloneCLI':sha(standalone),'sdist':roster['core-sdist']['sha256']},
                     'sdk':{'archive_sha256':sha(sdk_raw),'manifest_sha256':sha(sdk_manifest),'platform':platform,'checks':dict.fromkeys(validators.CORE_SDK_CHECKS,True)},
                     'rebuild':{'raw_sha256':sha(direct),'sdist_sha256':roster['core-sdist']['sha256'],'rebuilt_sha256':sha(rebuilt),'receipt_sha256':sha(members['core-artifact.json'])},
                     'final-identity':{'sourceUnchanged':True,'controllerUnchanged':True}}
        save('sdk-receipt.json',{'status':'built','sha256':sha(sdk_raw),'manifestSha256':sha(sdk_manifest)})
        for full in [True,False]:
            save(('full' if full else 'saga')+'-g03-sdk-install-custody.json',{'profile':'umf.sdk-installed-archive-custody/2' if full else 'umf.sdk-installed-saga-custody/1','archiveSha256':sha(sdk_raw),'sdkManifestSha256':sha(sdk_manifest),'installerSourceSha256':recipes['scripts/test-sdk-install.ts'],'existing139ConsumerChecks':'passed' if full else 'not-run-in-saga-phase','sagaResult':{'cases':19,'passed':19},'sagaQualificationInputs':inputs,'exactArchiveMembers':sdk_members,'installedMembers':sdk_members})
        save('installed-sdk-browser.json',{'profile':'umf.sdk-installed-browser-saga/1','artifactSourceS':source_commit,'controllerQ':controller,'archiveSha256':sha(sdk_raw),'qualificationInputs':inputs,'installedMembers':sdk_members,'result':{'cases':19,'passed':19},'hostCalls':0,'browser':'SYNTHETIC Chromium'})
        members['current/100-1/node.log']=canonical({'status':'passed','runtime':'node'})+b'\n'+canonical({'status':'passed','runtime':'node','chromium':{'version':'SYNTHETIC Chromium','status':'passed','nodeGlobalsAbsent':True}})+b'\n'
        inspections={};cell_files={}
        for cell in validators.CORE_CELLS:
            direct_cell=cell.startswith('direct-');w=direct if direct_cell else rebuilt;n=native if direct_cell else native+b' REBUILT DISTINCT'
            runtime={'cell':cell,'python':cell.split('-',1)[1],'implementation':'cpython','executable_sha256':'6'*64}
            compat={'profile':'umf.core-successor.named-compatibility/1','source':src,'inputProfile':'installed-canonical/1','census_sha256':compatibility['census_sha256'],'original':original,'wheel_sha256':sha(w),'native_sha256':sha(n),'groups':{}}
            for group in ('early','later'):
                xml=junit(compatibility[group]);members['compatibility-'+cell+'-'+group+'.xml']=xml;compat['groups'][group]={'cases':dict.fromkeys(compatibility[group],'passed'),'xml_sha256':sha(xml)}
            deep={'profile':'umf.core-successor.installed-inspection/3','source':src,'version':version,'resources':resources,'protocols':protocols,'maximumWork':1000000,'cases':17,'calls':51,'coldConstructors':51,'paidManifestReports':51,'inputProfile':'installed-canonical/1','data_sha256':inputs['crates/umf-core/src/canonical_codegen_literals.rs'],'resource_manifest_sha256':inputs['python/src/umf/action_runtime_resource_manifest.json'],'factory_manifest_sha256':'a'*64,'runtime':runtime,'wheel_sha256':sha(w),'native_sha256':sha(n),'compatibility':compat}
            deep.update(dict.fromkeys(('coldPerCall','constructorPassed','custodyPreserved','installedFilesUnchanged','loadedOwnershipVerified','recordVerified','embeddedCLIVerified','normalResolver','resourceSuccess','budgetRefusalVerified'),True))
            inspections[cell]=deep
            report={'status':'passed','distribution_version':version,'wheel_sha256':sha(w),'native_sha256':sha(n),'all_files_inside_platlib':True}
            install={'install':[{'metadata':{'name':name,'version':version},'download_info':{'url':'file:///synthetic/'+name+'.whl','archive_info':{'hashes':{'sha256':h}}}} for name,h in [('umf-core',sha(w)),('umf-codegen',roster['codegen-wheel']['sha256'])]]}
            saga={'profile':'umf.saga.portable-host-receipt/2','hostId':'python','cases':19,'passed':19,'installedBinding':{'wheelSha256':sha(w),'beforeNativeSha256':sha(n),'afterNativeSha256':sha(n)}}
            parts={'interpreter':('interpreter-',runtime),'install':('install-',install),'record':('record-',report),'postRecord':('record-post-',report),'inspection':('inspection-',deep),'saga':('saga-',saga)}
            evidence={}
            for label,(prefix,value) in parts.items():path=prefix+cell+'.json';save(path,value);evidence[label]=sha(members[path])
            members['freeze-'+cell+'.txt']=b'umf-core==0.10.10\numf-codegen==0.10.10\n';evidence['freeze']=sha(members['freeze-'+cell+'.txt'])
            members['native-'+cell+'.xml']=b'<testsuite><testcase name="synthetic-owner-native"/></testsuite>';evidence['native']=sha(members['native-'+cell+'.xml']);cell_files[cell]=evidence
        consumers={'cells':cell_files,'normalResolverCells':list(validators.CORE_CELLS)}
        for label,raw in [('embeddedCLI19',b'SYNTHETIC embedded CLI'),('standaloneCLI19',standalone)]:consumers[label]=save(label+'.json',{'host':'cli','cases':19,'passed':19,'artifacts':{'cliBinary':{'sha256':sha(raw)}}})
        step_values['consumers']=consumers;step_values['inspection']={'reports':{cell:cell_files[cell]['inspection'] for cell in validators.CORE_CELLS}}
        steps={name:{'status':'passed','evidence':save(name+'.json',step_values[name])} for name in validators.CORE_SDK_GATES}
        receipt={key:a[key] for key in ('profile','source','version','platform','controller','inputs','resources','protocols')};receipt.update(status='passed',failure=None,original=original,steps=steps,inspection=inspections,releaseQualified=False,nativeReleaseQualified=False,coupledQualified=False);save('component.json',receipt)
        material={'kind':'qualified','run':100+index,'job':200+index,'attempt':1,'artifact':300+index,'workflow':validators.CORE_OWNER_WORKFLOW,'workflow_sha':'5'*40,'controller':controller,'source':source_commit,'platform':platform,'job_name':original['job_name'],'upload_step':validators.CORE_UPLOAD,'sha256':sha(platform.encode()),'members':{p:sha(raw) for p,raw in members.items()}}
        run={'id':material['run'],'run_attempt':1,'head_sha':'5'*40,'path':validators.CORE_OWNER_WORKFLOW,'event':'workflow_dispatch','status':'completed','conclusion':'success','repository':{'full_name':'DocumentDrivenDX/umf','id':1382276802,'owner':{'id':273466046}}}
        job={'id':material['job'],'run_id':material['run'],'run_attempt':1,'head_sha':'5'*40,'name':original['job_name'],'labels':['ubuntu-24.04' if index==0 else 'macos-15'],'status':'completed','conclusion':'success','started_at':'2026-11-01T00:00:00Z','completed_at':'2026-11-01T00:01:00Z','steps':[{'name':validators.CORE_UPLOAD,'status':'completed','conclusion':'success','started_at':'2026-11-01T00:00:10Z','completed_at':'2026-11-01T00:00:50Z'}]}
        artifact={'id':material['artifact'],'expired':False,'digest':'sha256:'+material['sha256'],'name':'core-successor-'+original['job_name']+'-'+str(material['run'])+'-1','workflow_run':{'id':material['run'],'head_sha':'5'*40},'created_at':'2026-11-01T00:00:30Z'}
        bindings[platform]={'admission_id':a['id'],'material':material};materials[platform]={str(material['artifact']):{'run':run,'job':job,'artifact':artifact,'memberBytes':members}};all_components.append(a)
    aggregate={**all_components[0],'id':'synthetic-aggregate','purpose':'candidate-aggregate','components':bindings,'roster':roster}
    registry={'profile':'umf.core-successor.registry/2','admissions':[aggregate,*all_components]}
    readiness={key:aggregate[key] for key in ('source','version','controller','resources','inputs','protocols')};readiness.update(profile='umf.core-successor.material-readiness/1',status='material-gates-passed',originals={p:b['material'] for p,b in bindings.items()},assets=roster,releaseQualified=False,nativeReleaseQualified=False,coupledQualified=False,publicationAuthorized=False)
    bundle={'registryBytes':canonical(registry),'controllerBytes':{controller:{'script':script,'workflow':workflow}},'materials':materials,'readinessBytes':canonical(readiness)}
    selected={'sourceCommit':source_commit,'version':version,'wheelSha256':roster['linux-x86_64/core-wheel']['sha256'],'nativeSha256':native_by_platform['linux-x86_64'],'qualification':{'authorityCommit':authority,'authorityTree':'7'*40,'registrySha256':sha(bundle['registryBytes']),'admissionId':aggregate['id']}}
    return bundle,selected


class SelectedCoreOwnerReadinessTests(unittest.TestCase):
    def test_original_shaped_future_source_P_Q_platform_sdk_browser_positive(self):
        bundle,selected=core_owner_fixture()
        result=validators.validate_core_selected_owner_proofs(bundle,selected=selected)
        self.assertEqual(result['sourceCommit'],'1'*40)
        self.assertEqual(result['authorityCommit'],'3'*40)
        self.assertEqual(result['controllerCommits'],('2'*40,))
        self.assertEqual(result['platforms'],validators.CORE_PLATFORMS)
        self.assertEqual(result['version'],'0.10.10')
    def test_missing_selected_owner_admission_refuses_before_bundle_use(self):
        bundle,selected=core_owner_fixture();selected['qualification']=None
        with self.assertRaisesRegex(validators.Refusal,'Missing trusted selected Core owner admission'):
            validators.validate_core_selected_owner_proofs(None,selected=selected)
    def test_empty_or_wrong_P_registry_and_different_core_tuple_refuse(self):
        for mutate in [lambda b,s:s.update(sourceCommit='8'*40),lambda b,s:s.update(version='0.10.8'),lambda b,s:s.update(wheelSha256='8'*64),lambda b,s:s.update(nativeSha256='8'*64),lambda b,s:b.update(registryBytes=canonical({'profile':'umf.core-successor.registry/2','admissions':[]}))]:
            bundle,selected=core_owner_fixture();mutate(bundle,selected)
            with self.assertRaises(validators.Refusal):validators.validate_core_selected_owner_proofs(bundle,selected=selected)
    def test_original_hash_bound_gate_sdk_browser_dependency_and_platform_refusals(self):
        for target in ('sdk.json','full-g03-sdk-install-custody.json','installed-sdk-browser.json','install-direct-3.11.17.json','record-direct-3.11.17.json','interpreter-direct-3.13.16.json','native-direct-3.11.17.xml'):
            bundle,selected=core_owner_fixture();material=next(iter(bundle['materials']['linux-x86_64'].values()));del material['memberBytes'][target]
            with self.subTest(target=target),self.assertRaises(validators.Refusal):validators.validate_core_selected_owner_proofs(bundle,selected=selected)
        bundle,selected=core_owner_fixture();del bundle['materials']['macos-arm64']
        with self.assertRaises(validators.Refusal):validators.validate_core_selected_owner_proofs(bundle,selected=selected)
        bundle,selected=core_owner_fixture();registry=json.loads(bundle['registryBytes'])
        for row in registry['admissions']:row['compatibility']['early']=row['compatibility']['early'][:1]
        bundle['registryBytes']=canonical(registry);selected['qualification']['registrySha256']=sha(bundle['registryBytes'])
        with self.assertRaisesRegex(validators.Refusal,'compatibility roster'):
            validators.validate_core_selected_owner_proofs(bundle,selected=selected)
    def test_authenticated_but_semantically_wrong_originals_refuse(self):
        # Rebind all transport hashes to isolate semantic joins, not just a
        # stale SHA refusal. Registry remains synthetic trusted source fixture.
        mutations=[('sdk.json',lambda r:r['checks'].update(**{'node-browser':False})),('installed-sdk-browser.json',lambda r:r.update(hostCalls=1)),('full-g03-sdk-install-custody.json',lambda r:r.update(existing139ConsumerChecks='not-run-in-saga-phase')),('install-direct-3.11.17.json',lambda r:r['install'][1]['metadata'].update(version='0.10.8')),('record-direct-3.11.17.json',lambda r:r.update(native_sha256='9'*64))]
        for path,mutate in mutations:
            bundle,selected=core_owner_fixture();registry=json.loads(bundle['registryBytes']);readiness=json.loads(bundle['readinessBytes']);p='linux-x86_64';material=registry['admissions'][0]['components'][p]['material'];record=next(iter(bundle['materials'][p].values()));members=record['memberBytes'];value=json.loads(members[path]);mutate(value);members[path]=canonical(value);material['members'][path]=sha(members[path])
            # Gate references and consumer cell references must also bind new
            # bytes so downstream source semantics discriminate the mutation.
            component=json.loads(members['component.json'])
            for gate,row in component['steps'].items():
                evidence=json.loads(members[row['evidence']['path']])
                if row['evidence']['path']==path:row['evidence']['sha256']=sha(members[path])
                if gate=='consumers':
                    for cell,refs in evidence['cells'].items():
                        for key,prefix in [('install','install-'),('record','record-')]:
                            if path==prefix+cell+'.json':refs[key]=sha(members[path])
                    members['consumers.json']=canonical(evidence);row['evidence']['sha256']=sha(members['consumers.json']);material['members']['consumers.json']=sha(members['consumers.json'])
            members['component.json']=canonical(component);material['members']['component.json']=sha(members['component.json']);readiness['originals'][p]=material;bundle['registryBytes']=canonical(registry);selected['qualification']['registrySha256']=sha(bundle['registryBytes']);bundle['readinessBytes']=canonical(readiness)
            with self.subTest(path=path),self.assertRaises(validators.Refusal):validators.validate_core_selected_owner_proofs(bundle,selected=selected)

if __name__ == "__main__":
    unittest.main()
