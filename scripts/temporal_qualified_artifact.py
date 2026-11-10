#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Closed, source-only verification for reuse of a qualified Truss wheel.

This module never executes a workflow, fetches an artifact, imports Truss, or
claims that caller-supplied qualification fields are true. GitHub metadata and
artifact bytes are supplied by the workflow intake; this code joins them to the
original campaign evidence and the exact release wheel bytes.
"""
from __future__ import annotations

import hashlib
import ast
import json
from email.parser import BytesParser
from pathlib import PurePosixPath
import re
from zipfile import BadZipFile, ZipFile
import io
import subprocess


SCHEMA = "truss.temporal-qualified-wheel-binding/1"
WORKFLOW_PATH = ".github/workflows/python-runtime.yml"
CAMPAIGN_JOB = "temporal-candidate"
CAMPAIGN_ARTIFACT_PREFIX = "temporal-candidate-qualify119-"
EXPECTED_COUNTS = {
    "temporal": 39, "public54": 1, "ordinary": 11, "hf": 62,
    "baseline": 6, "journal": 10, "public55": 1,
}
INPUT_NAMES = (
    "temporal_qualification_run_id",
    "temporal_qualification_artifact_id",
    "temporal_qualification_artifact_sha256",
)
WEFT_SDK_VALIDATOR_ID = "weft.sdk-custody-42/1"
WEFT_ORIGINAL_RECORDS = {
    "/private/tmp/weft-temporal-canonical-S/final-R-c623b94b/linux-x86-retained/component.json":
        ("inputs/weft-final-R-c623b94b/linux-x86-retained/component.json",
         "a10a8961da065c5b39f77a0181ad3d474ece4c1e2c5de151d616e293d52f0c6f"),
    "/private/tmp/weft-temporal-canonical-S/final-R-c623b94b/linux-x86-retained/sdk-smoke.json":
        ("inputs/weft-final-R-c623b94b/linux-x86-retained/sdk-smoke.json",
         "93a3910abd94baaa2e68387be666ad29f24b1c4092667629db7be11ea30b72f7"),
    "/private/tmp/weft-temporal-canonical-S/final-R-c623b94b/linux-x86-retained/packaging.json":
        ("inputs/weft-final-R-c623b94b/linux-x86-retained/packaging.json",
         "0d5565fa0277aca1f0ba0215d786f51f8a28dcd6b0777d6c97005803dd0ea00b"),
}
WEFT_ORIGINAL_RUN = "41686658658"
WEFT_ORIGINAL_ATTEMPT = "1"
WEFT_ORIGINAL_JOB = "126094501575"


def _fail(message: str) -> None:
    raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hex(value: object, length: int = 64) -> str:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{%d}" % length, value) is None or set(value) == {"0"}:
        _fail("Expected nonzero lowercase SHA256" if length == 64 else "Expected full Git commit")
    return value


def _relative(value: object) -> str:
    if type(value) is not str:
        _fail("Expected closed relative member path")
    path = PurePosixPath(value)
    if (not value or value in (".", "..") or path.is_absolute() or ".." in path.parts
            or str(path) != value or "\\" in value or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        _fail("Unsafe or noncanonical member path")
    return value


def validate_dispatch_inputs(inputs: dict[str, object], *, temporal_candidate: bool) -> dict[str, str] | None:
    """Require all three provenance selectors for the temporal candidate."""
    if type(inputs) is not dict:
        _fail("Release dispatch input object required")
    values = [inputs.get(name, "") for name in INPUT_NAMES]
    if any(type(value) is not str for value in values):
        _fail("Qualification references must be strings")
    present = [bool(value) for value in values]
    if any(present) and not all(present):
        _fail("Partial temporal qualification references refuse release")
    if any(present) and not temporal_candidate:
        _fail("Qualification references are valid only for the selected temporal candidate route")
    if temporal_candidate and not all(present):
        _fail("Temporal candidate requires original qualify119 run and artifact references")
    if not any(present):
        return None
    run_id, artifact_id, digest = values
    if re.fullmatch(r"[1-9][0-9]{0,19}", run_id) is None or re.fullmatch(r"[1-9][0-9]{0,19}", artifact_id) is None:
        _fail("Actual positive workflow run and artifact IDs required")
    return {"runId": run_id, "artifactId": artifact_id, "artifactSha256": _hex(digest)}


def temporal_candidate(root) -> bool:
    """Select the existing temporal candidate by its checked-in runtime identity."""
    manifest = json.loads((root / "packages/python/src/truss/_catalog_runtime/manifest.json").read_bytes())
    return manifest.get("releaseId") == "truss-catalog-runtime/0.76-temporal-candidate"


def authenticate_github_metadata(*, run: dict, job: dict, artifact: dict,
                                 repository: str, run_id: str, artifact_id: str,
                                 artifact_sha256: str, source_commit: str,
                                 artifact_zip: bytes) -> None:
    """Check captured GitHub API objects against the actual downloaded ZIP."""
    if type(run) is not dict or type(job) is not dict or type(artifact) is not dict:
        _fail("Captured GitHub run/job/artifact metadata required")
    if (str(run.get("id")) != run_id or run.get("event") != "workflow_dispatch"
            or run.get("path") != WORKFLOW_PATH or run.get("conclusion") != "success"
            or str(run.get("run_attempt")) != str(job.get("run_attempt"))
            or str(run.get("head_sha")) != source_commit
            or run.get("repository", {}).get("full_name") != repository):
        _fail("Qualification workflow run provenance differs from selected source")
    if (job.get("name") != CAMPAIGN_JOB or str(job.get("run_id")) != run_id
            or str(job.get("run_attempt")) != str(run.get("run_attempt"))
            or job.get("conclusion") != "success"):
        _fail("Original successful qualify119 job required")
    expected_name = CAMPAIGN_ARTIFACT_PREFIX + run_id + "-" + str(run.get("run_attempt"))
    if (str(artifact.get("id")) != artifact_id or artifact.get("name") != expected_name
            or artifact.get("expired") is not False):
        _fail("Original completed qualify119 artifact identity differs")
    workflow_run = artifact.get("workflow_run")
    if workflow_run is not None and str(workflow_run.get("id")) != run_id:
        _fail("Artifact is not attached to the selected workflow run")
    _hex(artifact_sha256)
    if artifact.get("digest") != "sha256:" + artifact_sha256:
        _fail("GitHub artifact digest metadata differs")
    if sha256(artifact_zip) != artifact_sha256:
        _fail("Downloaded original artifact ZIP digest differs")
    if type(artifact.get("size_in_bytes")) is not int or artifact.get("size_in_bytes") != len(artifact_zip):
        _fail("Downloaded original artifact size differs")


def _read_zip(raw: bytes) -> dict[str, bytes]:
    try:
        archive = ZipFile(io.BytesIO(raw))
    except (BadZipFile, OSError) as error:
        raise ValueError("Original campaign artifact is not a valid ZIP") from error
    with archive:
        files: dict[str, bytes] = {}
        for info in archive.infolist():
            name = _relative(info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if info.is_dir() or mode == 0o120000 or info.flag_bits & 0x1 or name in files:
                _fail("Duplicate, directory, encrypted, or symlink ZIP member")
            files[name] = archive.read(info)
        return files


def _json(files: dict[str, bytes], path: str) -> dict:
    path = _relative(path)
    try:
        value = json.loads(files[path])
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Missing or invalid original receipt: " + path) from error
    if type(value) is not dict:
        _fail("Receipt must be a JSON object: " + path)
    return value


def _wheel_identity(raw: bytes, distribution: str, version: str, *, package: str | None = None,
                    module_path: str | None = None, module_sha256: str | None = None) -> None:
    try:
        with ZipFile(io.BytesIO(raw)) as wheel:
            names = wheel.namelist()
            metadata_files = [name for name in names if name.endswith(".dist-info/METADATA")]
            if len(names) != len(set(names)) or len(metadata_files) != 1:
                _fail("Owner wheel requires unique members and one METADATA file")
            metadata = BytesParser().parsebytes(wheel.read(metadata_files[0]))
            normalized = metadata.get("Name", "").lower().replace("_", "-")
            if normalized != distribution.lower().replace("_", "-") or metadata.get("Version") != version:
                _fail("Owner wheel distribution/version differs from admitted cohort")
            if package is not None:
                module = package + "/" + module_path
                if module not in names or sha256(wheel.read(module)) != module_sha256:
                    _fail("Owner module bytes differ from source identity")
    except BadZipFile as error:
        raise ValueError("Admitted owner wheel is not a valid wheel archive") from error


def _receipt_ref(files: dict[str, bytes], ref: object) -> bytes:
    if type(ref) is not dict or set(ref) != {"path", "sha256"}:
        _fail("Receipt reference must contain only path and SHA256")
    path = _relative(ref["path"])
    expected = _hex(ref["sha256"])
    if path not in files or sha256(files[path]) != expected:
        _fail("Original receipt reference does not match retained bytes: " + path)
    return files[path]


def _original_weft_record(ref, files):
    """Resolve the three preserved absolute Weft refs through the closed archive map."""
    if type(ref) is not dict or set(ref) != {'path', 'sha256'}:
        _fail('Malformed original Weft handoff reference')
    mapping = WEFT_ORIGINAL_RECORDS.get(ref.get('path'))
    if mapping is None or ref.get('sha256') != mapping[1]:
        _fail('Original Weft path/hash is not in the closed correspondence')
    member, expected = mapping
    raw = files.get(member)
    if type(raw) is not bytes or sha256(raw) != expected:
        _fail('Missing/mismatched authenticated original Weft archive member: ' + member)
    return raw


def _join_original_weft(handoff, section, metadata, owner, admitted):
    run, job, artifact = metadata['run'], metadata['job'], metadata['artifact']
    if (type(owner) is not dict or type(admitted) is not dict
            or handoff.get('sourceCommit') != section['sourceCommit']
            or handoff.get('sourceTree') != section['sourceTree']
            or str(handoff.get('runID')) != str(run.get('id'))
            or str(handoff.get('originalAttempt')) != str(run.get('run_attempt'))
            or str(handoff.get('actualJobID')) != str(job.get('id'))
            or str(handoff.get('actualJobID')) != WEFT_ORIGINAL_JOB
            or handoff.get('actualJobConclusion') != job.get('conclusion')
            or str(job.get('run_id')) != str(run.get('id'))
            or str(job.get('run_attempt')) != str(run.get('run_attempt'))
            or str(artifact.get('workflow_run', {}).get('id', run.get('id'))) != str(run.get('id'))
            or str(artifact.get('workflow_run', {}).get('run_attempt', run.get('run_attempt'))) != str(run.get('run_attempt'))
            or handoff.get('wheel', {}).get('sha256') != admitted.get('sha256')
            or handoff.get('wheel', {}).get('sha256') != owner.get('wheelSha256')
            or handoff.get('nativeModule', {}).get('sha256') != owner.get('moduleSha256')
            or handoff.get('shimSha256') != owner.get('shimSha256')):
        _fail('Original Weft handoff does not join authenticated raw metadata and admitted owner bytes')


def _lifecycle_cases(producer_bytes):
    tree = ast.parse(producer_bytes)
    assignments = {target.id: ast.literal_eval(node.value) for node in tree.body
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Tuple, ast.List))
        for target in node.targets if isinstance(target, ast.Name) and target.id == 'LIFECYCLE2_CASES'}
    cases = assignments.get('LIFECYCLE2_CASES')
    if type(cases) not in (tuple, list) or len(cases) != 2:
        _fail('Pinned exact two-case lifecycle2 source roster required')
    normalized = list(cases)
    if len(set(normalized)) != 2 or any(type(item) is not str or not item for item in normalized):
        _fail('Pinned lifecycle2 source roster is malformed or duplicated')
    return normalized


def _runner_wheel_correspondence(admission: dict, hosted: dict) -> dict[str, dict[str, str]]:
    """Join preserved absolute admission paths to hosted archive-relative wheel members."""
    wheelhouse_text = admission.get("wheelhouse")
    wheels = admission.get("wheels")
    hosted_wheels = hosted.get("wheels")
    if (type(wheelhouse_text) is not str or type(wheels) is not dict
            or set(wheels) != {"truss", "core", "access", "weft"}
            or type(hosted_wheels) is not dict or set(hosted_wheels) != set(wheels)):
        _fail("Original admitted wheelhouse and hosted wheel rosters required")
    wheelhouse = PurePosixPath(wheelhouse_text)
    if not wheelhouse.is_absolute() or ".." in wheelhouse.parts or str(wheelhouse) != wheelhouse_text:
        _fail("Original runner wheelhouse must be an absolute canonical path")
    correspondence = {}
    for owner, row in wheels.items():
        if type(row) is not dict or type(row.get("path")) is not str:
            _fail("Original absolute runner wheel path required: " + owner)
        original = PurePosixPath(row["path"])
        if (not original.is_absolute() or ".." in original.parts or str(original) != row["path"]
                or not original.is_relative_to(wheelhouse)):
            _fail("Original runner wheel path is outside its admitted wheelhouse: " + owner)
        relative = original.relative_to(wheelhouse)
        if not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
            _fail("Original runner wheel path has an invalid wheelhouse suffix: " + owner)
        archive_path = (PurePosixPath("wheelhouse") / relative).as_posix()
        hosted_row = hosted_wheels[owner]
        if (type(hosted_row) is not dict or set(hosted_row) != {"path", "sha256"}
                or hosted_row.get("path") != archive_path
                or hosted_row.get("sha256") != row.get("sha256")):
            _fail("Original runner path does not join the exact hosted wheel member: " + owner)
        _hex(row.get("sha256"))
        correspondence[owner] = {"admissionPath": row["path"], "archivePath": archive_path,
                                  "sha256": row["sha256"]}
    return correspondence


def _authenticated_component_results(prerequisites: object, files: dict[str, bytes], validator_refs: dict):
    """Load only fixed, hash-referenced producer result objects for the registry."""
    from component_prerequisite_validators import REQUIRED

    if type(prerequisites) is not list or not prerequisites:
        _fail("Missing original Core C1 component receipts; native-campaign admission is refused")
    results = {}
    weft_sdk_result = None
    lifecycle_result = None
    for row in prerequisites:
        if type(row) is not dict or set(row) != {
                "gateId", "validatorId", "receiptPath", "receiptSha256",
                "validatorSourcePath", "validatorSourceSha256"}:
            _fail("Original component receipt reference is incomplete or unknown")
        gate_id = row["gateId"]
        if gate_id not in REQUIRED and gate_id != WEFT_SDK_VALIDATOR_ID:
            _fail("Unknown or caller-selected component validator ID")
        if row["validatorId"] != gate_id:
            _fail("Unknown or caller-selected component validator ID")
        if gate_id in results:
            _fail("Duplicate original component result: " + gate_id)
        path = _relative(row["receiptPath"])
        digest = _hex(row["receiptSha256"])
        raw = files.get(path)
        if raw is None or sha256(raw) != digest:
            _fail("Original component receipt path/hash mismatch: " + gate_id)
        source_path = _relative(row["validatorSourcePath"])
        source_digest = _hex(row["validatorSourceSha256"])
        expected_validator = validator_refs['weftHandoff' if gate_id == WEFT_SDK_VALIDATOR_ID else 'coreRegistry']
        if source_path != expected_validator['path'] or source_digest != expected_validator['sha256']:
            _fail("Original component validator source does not match the closed cohort role: " + gate_id)
        source = files.get("source/" + source_path)
        if source is None or sha256(source) != source_digest:
            _fail("Original component validator source path/hash mismatch: " + gate_id)
        try:
            result = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Original component result is not JSON: " + gate_id) from error
        if type(result) is not dict:
            _fail("Original component result object required: " + gate_id)
        parent = path.rpartition('/')[0]
        def sibling(name):
            candidate = (parent + '/' if parent else '') + name
            value = files.get(candidate, files.get('inputs/' + candidate))
            if type(value) is not bytes:
                _fail('Missing original component producer companion: ' + candidate)
            return value
        from component_prerequisite_validators import (
            FACTORY51, EARLY18, RUST477, PYTHON31, SAGA19, RESOURCES9,
        )
        if gate_id == WEFT_SDK_VALIDATOR_ID:
            pass
        elif gate_id == FACTORY51:
            results[gate_id] = result
        elif gate_id == EARLY18:
            cost = result
            member_bytes = {}
            for name, binding in cost.get('members', {}).items():
                value = sibling(name)
                if (type(binding) is not dict or len(value) != binding.get('bytes')
                        or sha256(value) != binding.get('sha256')):
                    _fail('Original cost-gate companion path/hash mismatch: ' + str(name))
                member_bytes[name] = value
            results[gate_id] = {'cost': cost, 'xml': member_bytes.get('public-controls.xml'),
                                'memberBytes': member_bytes}
        elif gate_id == RUST477:
            compiled_raw = sibling('compiled-census.json')
            compiled = json.loads(compiled_raw)
            case_logs = {}
            for index, row_result in enumerate(result.get('results', [])):
                identity = (row_result.get('package'), row_result.get('target'), row_result.get('name'))
                case_logs[identity] = sibling('rust-cases/' + str(index) + '-case.log')
            results[gate_id] = {'result': result, 'compiled': compiled,
                                'compiledBytes': compiled_raw, 'caseLogs': case_logs}
        elif gate_id == PYTHON31:
            xmls = {}
            for index in range(len(result.get('pythonGroups', []))):
                xmls[str(index)] = sibling('factory-group-' + str(index) + '.xml')
            results[gate_id] = {'aggregate': result, 'xml': xmls}
            try:lifecycle_result=json.loads(sibling('saga-lifecycle2-result.json'))
            except (UnicodeDecodeError,json.JSONDecodeError) as error:
                raise ValueError('Original lifecycle2 result is malformed') from error
        elif gate_id == SAGA19:
            results[gate_id] = result
        elif gate_id == RESOURCES9:
            measurement_ref = next((row for row in prerequisites if row.get('gateId') == FACTORY51), None)
            if measurement_ref is None:
                _fail('Missing original factory measurement for resource manifest crosschecks')
            measurement_path = _relative(measurement_ref['receiptPath'])
            measurement_raw = files.get(measurement_path, files.get('inputs/' + measurement_path))
            if type(measurement_raw) is not bytes or sha256(measurement_raw) != measurement_ref['receiptSha256']:
                _fail('Original resource/factory measurement reference differs')
            measurement = json.loads(measurement_raw)
            pairs = measurement.get('pairs')
            if type(pairs) is not list or len(pairs) != 51:
                _fail('Original paid 51-pair resource manifests are missing')
            manifest = pairs[0].get('sourceManifest')
            if any(row.get('sourceManifest') != manifest for row in pairs):
                _fail('Original paid source manifests differ across the 51 factory pairs')
            results[gate_id] = manifest
        else:
            _fail('Unknown component prerequisite gate')
        if gate_id == WEFT_SDK_VALIDATOR_ID:
            if weft_sdk_result is not None:
                _fail("Duplicate original Weft SDK42 result")
            weft_sdk_result = result
    if set(results) != REQUIRED:
        missing = sorted(REQUIRED - set(results))
        _fail("Missing original Core C1 result(s): " + ", ".join(missing))
    return results, weft_sdk_result, lifecycle_result


def require_closed_component_prerequisites(prerequisites: object, files: dict[str, bytes], *,
                                           cohort_bytes: bytes,
                                           owner_identities: dict,
                                           admitted_wheels: dict,
                                           weft_sdk: dict | None = None,
                                           weft_source_commit: str | None = None,
                                           weft_pins: dict | None = None) -> dict:
    """Invoke the frozen Core registry and existing Weft SDK-call validator.

    Expected pins are derived here from the authenticated source-controlled
    cohort references and original admitted wheel/owner identities. Callers
    cannot supply an expected map. Receipt content is data only; no bundled
    code is imported or executed.
    """
    from component_prerequisite_validators import (
        REQUIRED, WEFT_ORIGINAL_CHECK_CALLS, validate_component_prerequisites,
        validate_weft_existing_sdk_checks,
    )

    from release_cohort import derive_component_expected, component_source_refs, _read_source_refs
    from pathlib import Path
    expected = derive_component_expected(cohort_bytes, files,
        owner_identities=owner_identities, admitted_wheels=admitted_wheels)
    section = component_source_refs(cohort_bytes)
    authenticated_sources = _read_source_refs(section, files)
    for role in ('coreRegistry', 'weftHandoff'):
        ref = section['validatorSourceRefs'][role]
        local_path = Path(__file__).with_name(Path(ref['path']).name)
        if (not local_path.is_file()
                or local_path.read_bytes() != authenticated_sources[ref['path']]):
            _fail('Executed fixed validator differs from authenticated source bytes: ' + role)
    results, referenced_weft_sdk, lifecycle = _authenticated_component_results(
        prerequisites, files, section['validatorSourceRefs'])
    try:
        checked = validate_component_prerequisites(results, expected)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Original Core C1 prerequisite validation refused: " + str(error)) from error
    if set(checked) != REQUIRED:
        _fail("Core C1 registry did not validate its complete fixed gate set")
    handoff_ref = section['weft']['handoff']
    raw_handoff = files.get(handoff_ref['path'], files.get('inputs/' + handoff_ref['path']))
    if type(raw_handoff) is not bytes or sha256(raw_handoff) != handoff_ref['sha256']:
        _fail('Missing trusted Weft handoff reference/bytes')
    handoff = json.loads(raw_handoff)
    def original_reader(ref):
        return _original_weft_record(ref, files)
    # Import only the fixed Truss source module, never code from an evidence member.
    import importlib.util
    handoff_module_path = Path(__file__).with_name('prepare-temporal-binary-enrollment.py')
    spec = importlib.util.spec_from_file_location('truss_fixed_final_weft_validator', handoff_module_path)
    if spec is None or spec.loader is None:
        _fail('Fixed original Weft validator source is unavailable')
    handoff_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handoff_module)
    joined_weft_sdk = handoff_module.final_weft_component(
        handoff, section['weft']['sourceCommit'],
        section['weft']['canonicalCoreSourceCommit'], section['weft']['cargoLockSha256'],
        record_reader=original_reader)
    # The handoff's internally consistent proof graph must also be the exact
    # independently admitted wheel/module/shim and authenticated raw run graph.
    weft_section = section['weft']
    weft_meta = {role: json.loads(authenticated_sources[ref['path']])
                 for role, ref in weft_section['originalMetadataRefs'].items()}
    admitted_weft = admitted_wheels.get('weft')
    owner_weft = owner_identities.get('weft')
    _join_original_weft(handoff, weft_section, weft_meta, owner_weft, admitted_weft)
    if weft_sdk is not None and weft_sdk != joined_weft_sdk:
        _fail('Caller and original Weft handoff SDK42 bytes disagree')
    weft_sdk = joined_weft_sdk
    if referenced_weft_sdk is not None and weft_sdk != referenced_weft_sdk:
        _fail("Separate and original Weft SDK42 receipt bytes disagree")
    weft_pins = {'wheelSha256': admitted_weft['sha256'],
                 'nativeModuleSha256': owner_weft['moduleSha256'],
                 'shimSha256': owner_weft['shimSha256']}
    weft_source_commit = section['weft']['sourceCommit']
    if type(weft_pins) is not dict or set(weft_pins) != {"wheelSha256", "nativeModuleSha256", "shimSha256"}:
        _fail("Missing admitted Weft wheel/native/shim pins")
    try:
        weft_checks = validate_weft_existing_sdk_checks(
            weft_sdk, source_commit=weft_source_commit, pins_before_after=weft_pins)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Original Weft SDK42 validation refused: " + str(error)) from error
    if weft_checks != WEFT_ORIGINAL_CHECK_CALLS:
        _fail("Original Weft SDK42 check-call outcomes differ")
    core_bytes=_read_source_refs(section,files)
    census=json.loads(core_bytes[section['core']['sourceRefs']['census']['path']])
    factory=census.get('installedFactory',{})
    history=factory.get('legacyDisposition')
    if (type(history) is not dict or history.get('oldProbeUnchanged') is not True
            or history.get('warmed51IsFactoryEvidence') is not False
            or type(history.get('separateExplicitHistory')) is not str
            or not history['separateExplicitHistory']):
        _fail('Original Core History1 explicit disposition is missing or changed')
    producer=core_bytes[section['core']['producerSourceRefs']['tools/run_inspector_attribution_lanes.py']['path']]
    normalized_cases = _lifecycle_cases(producer)
    if (type(lifecycle) is not dict or lifecycle.get('profile')!='umf.private-installed-saga-lifecycle2/1'
            or lifecycle.get('status')!='passed' or lifecycle.get('passed') is not True
            or lifecycle.get('source')!=expected['controllerSource']
            or str(lifecycle.get('run'))!=expected['run'] or str(lifecycle.get('attempt'))!=expected['attempt']
            or lifecycle.get('cases')!=normalized_cases
            or lifecycle.get('publishable') is not False or lifecycle.get('readyForEnrollment') is not False
            or lifecycle.get('currentInputIdentity')!=expected['currentInputIdentity']):
        _fail('Original same-job lifecycle2 prerequisite is missing or misbound')
    for role in ('identityBefore','identityAfter','log','junit'):
        ref=lifecycle.get(role)
        if type(ref) is not dict or type(ref.get('path')) is not str:
            _fail('Original lifecycle2 '+role+' reference is missing')
        python_ref=next(row for row in prerequisites if row.get('gateId')=='core.c1.python-cases-31/1')
        parent=_relative(python_ref['receiptPath']).rpartition('/')[0]
        member=(parent+'/' if parent else '')+_relative(ref['path'])
        raw=files.get(member,files.get('inputs/'+member))
        if (type(raw) is not bytes or sha256(raw)!=_hex(ref.get('sha256'))
                or (type(ref.get('bytes')) is int and len(raw)!=ref['bytes'])):
            _fail('Original lifecycle2 '+role+' bytes/hash differ')
        if role.startswith('identity'):
            identity=json.loads(raw)
            if (identity.get('artifactSource')!=expected['source']
                    or identity.get('controllerSource')!=expected['controllerSource']
                    or identity.get('wheelSHA256')!=expected['wheelSha256']
                    or identity.get('currentInputIdentity')!=expected['currentInputIdentity']
                    or identity.get('completeWheelAndInstalledRecordVerified') is not True
                    or identity.get('distributionOwnershipVerified') is not True):
                _fail('Original lifecycle2 same-wheel identity differs: '+role)
        elif role=='junit':
            from component_prerequisite_validators import _junit
            _junit(raw,normalized_cases,'Original lifecycle2')
    stage_records={'historyDisposition':history,'lifecycle2':lifecycle,
                   'weftOwnerSource':{key: section['weft'][key] for key in
                       ('sourceCommit','sourceTree','canonicalCoreSourceCommit','cargoLockSha256')}}
    return {"coreC1": checked, "weftSDK42": weft_checks,
            "stagePrerequisites":stage_records}


def committed_source_snapshot(root, source_commit: str, source_tree: str, paths, *, evidence_roots=()) -> dict[str, bytes]:
    """Require every consumed source file to equal its committed blob at campaign capture."""
    from pathlib import Path
    from temporal_qualification_support import assert_qualification_checkout
    root = Path(root).resolve()
    assert_qualification_checkout(root, source_commit, source_tree, evidence_roots=evidence_roots)
    snapshot = {}
    for selected in paths:
        relative = _relative(selected)
        path = root / relative
        if path.is_symlink() or not path.is_file():
            _fail("Consumed qualification source must be a regular committed file: " + relative)
        try:
            committed = subprocess.check_output(["git", "show", source_commit + ":" + relative], cwd=root)
        except subprocess.CalledProcessError as error:
            raise ValueError("Consumed qualification source is absent from the admitted commit: " + relative) from error
        current = path.read_bytes()
        if current != committed:
            _fail("Consumed qualification source differs from its committed source bytes: " + relative)
        snapshot[relative] = committed
    return snapshot


def _validate_campaign(files: dict[str, bytes], binding: dict) -> tuple[dict, dict, dict, dict]:
    refs = binding.get("receipts")
    required = {"admission", "admissionResult", "campaign", "ledger", "census", "cohort", "hostedInput", "stages"}
    if type(refs) is not dict or set(refs) != required or type(refs["stages"]) is not dict:
        _fail("Closed original admission/campaign/ledger/census/stage receipt roster required")
    if set(refs["stages"]) != set(EXPECTED_COUNTS):
        _fail("All seven original campaign stage receipts required")
    admission = _json(files, _relative(refs["admission"]["path"]))
    admission_result = _json(files, _relative(refs["admissionResult"]["path"]))
    campaign = _json(files, _relative(refs["campaign"]["path"]))
    ledger = _json(files, _relative(refs["ledger"]["path"]))
    census = _json(files, _relative(refs["census"]["path"]))
    for ref in (refs["admission"], refs["admissionResult"], refs["campaign"], refs["ledger"], refs["census"], refs["cohort"], refs["hostedInput"]):
        _receipt_ref(files, ref)
    cohort = _json(files, refs["cohort"]["path"])
    if (sha256(files[refs["cohort"]["path"]]) != binding.get("cohortSha256")
            or cohort.get("schema") != "truss-release-cohort/1"
            or cohort.get("truss") != {"distribution": "umf-truss", "version": binding["candidateWheel"].get("version")}):
        _fail("Selected source cohort does not bind candidate wheel distribution/version")
    hosted = _json(files, refs["hostedInput"]["path"])
    owners = hosted.get("ownerIdentities")
    if (hosted.get("schema") != "truss-temporal-hosted-input/1" or hosted.get("ready") is not True
            or hosted.get("phase") != "qualify119" or hosted.get("sourceCommit") != binding.get("sourceCommit")
            or hosted.get("sourceTree") != binding.get("sourceTree") or owners != binding.get("ownerIdentities")):
        _fail("Original ready qualify119 hosted-input/source/owner identities required")
    hosted_files = hosted.get("files")
    if type(hosted_files) is not dict or not hosted_files:
        _fail("Original hosted-input file manifest required")
    for relative_name, expected_hash in hosted_files.items():
        name = _relative("inputs/" + relative_name)
        if name not in files or sha256(files[name]) != _hex(expected_hash):
            _fail("Original hosted-input file bytes differ: " + name)
    if type(owners) is not dict or set(owners) != {"core", "weft", "truss"}:
        _fail("Original Core/Weft/Truss owner identity records required")
    core, weft, truss = owners["core"], owners["weft"], owners["truss"]
    expected_resources = {"coreSchema", "referenceSchema", "packageSchema", "constraints", "domainPolicy",
                          "tablesPackage", "actionsPackage", "bindingPackage", "stableBindingPackage"}
    if (type(core) is not dict or type(weft) is not dict or type(truss) is not dict
            or type(core.get("resources")) is not dict or set(core["resources"]) != expected_resources):
        _fail("Original Core resource and owner module identity roster required")
    for owner in (core, weft):
        for key in ("sourceCommit", "moduleSha256", "wheelSha256"):
            _hex(owner.get(key), 40 if key == "sourceCommit" else 64)
    _hex(core.get("resourceSourceCommit"), 40); _hex(core.get("resourceManifestSha256")); _hex(truss.get("nativeManifestSha256"))
    for resource in core["resources"].values():
        if type(resource) is not dict or set(resource) != {"path", "sha256"}:
            _fail("Closed canonical resource path/hash record required")
        _relative(resource["path"]); _hex(resource["sha256"])
    hosted_wheels = hosted.get("wheels")
    if type(hosted_wheels) is not dict or set(hosted_wheels) != {"truss", "core", "access", "weft"}:
        _fail("Original four-owner hosted wheel roster required")
    runner_wheels = _runner_wheel_correspondence(admission, hosted)
    if binding.get("originalWheelPaths") != runner_wheels:
        _fail("Original absolute admission paths do not join the retained archive-relative wheel members")
    if ledger.get("schema") != "truss-temporal-case-ledger/1" or ledger.get("expectedCounts") != EXPECTED_COUNTS:
        _fail("Original reviewed 130-case ledger required")
    expected_stages = ledger.get("stages")
    if type(expected_stages) is not dict or set(expected_stages) != set(EXPECTED_COUNTS):
        _fail("Original seven-stage selector ledger required")
    all_selectors = []
    for stage, count in EXPECTED_COUNTS.items():
        rows = expected_stages[stage]
        if type(rows) is not list or len(rows) != count:
            _fail("Original exact case count differs: " + stage)
        selectors = [row.get("test") for row in rows if type(row) is dict]
        if len(selectors) != count or any(type(item) is not str or not item for item in selectors) or len(set(selectors)) != count:
            _fail("Original unique exact selectors required: " + stage)
        all_selectors.extend(selectors)
    if len(all_selectors) != 130 or len(set(all_selectors)) != 130:
        _fail("Original 130 selectors must remain unique across stages")
    if campaign.get("passed") is not True or campaign.get("expectedCounts") != EXPECTED_COUNTS or campaign.get("expectedTotal") != 130:
        _fail("Full original 130-case campaign did not pass")
    if campaign.get("error") is not None or campaign.get("ledgerSha256") != sha256(files[refs["ledger"]["path"]]):
        _fail("Campaign error or ledger digest mismatch")
    _hex(campaign.get("admissionSha256"))
    if campaign["admissionSha256"] != sha256(files[refs["admission"]["path"]]):
        _fail("Campaign admission bytes differ")
    if (campaign.get("sourceCommit") != binding.get("sourceCommit")
            or admission.get("sourceCommit") != binding.get("sourceCommit")
            or admission.get("sourceTree") != binding.get("sourceTree")):
        _fail("Campaign/admission source commit differs")
    stages = campaign.get("stages")
    if type(stages) is not list or [row.get("stage") for row in stages if type(row) is dict] != list(EXPECTED_COUNTS):
        _fail("All seven original campaign stage results in order required")
    if census.get("total") != 130 or census.get("nativeExecuted") != 0 or census.get("ledgerSha256") != sha256(files[refs["ledger"]["path"]]):
        _fail("Original exact selector census required")
    for row in stages:
        stage = row["stage"]
        _receipt_ref(files, refs["stages"][stage])
        original = _json(files, refs["stages"][stage]["path"])
        selectors = [case["test"] for case in expected_stages[stage]]
        if (original != row or row.get("expectedIds") != selectors or row.get("expectedCases") != EXPECTED_COUNTS[stage]
                or row.get("testsRun") != EXPECTED_COUNTS[stage] or row.get("passed") is not True
                or row.get("inventoryVerified") is not True or row.get("cleanupConfirmed") is not True
                or any(row.get(key) != 0 for key in ("skips", "expectedFailures", "unexpectedSuccesses", "failures", "errors"))):
            _fail("Original stage selectors/results/cleanup are incomplete: " + stage)
        observations = row.get("observations")
        if type(observations) is not list:
            _fail("Original per-case driver observations required: " + stage)
        for selector in selectors:
            passed = [item for item in observations if type(item) is dict and item.get("id") == selector and item.get("status") == "passed"]
            allowed_status = {"passed", "subcase-passed"}
            if len(passed) != 1 or any(type(item) is dict and item.get("id") == selector and item.get("status") not in allowed_status for item in observations):
                _fail("Missing, duplicate, or nonpassing original case observation: " + selector)
        cleanup_paths = (["evidence/native/" + stage + "/shared-worker-cleanup.json"] if stage in ("temporal", "journal")
                         else [refs["stages"][stage]["path"].rsplit("/",1)[0] + "/isolated-cleanup.json"])
        for cleanup_path in cleanup_paths:
            cleanup = _json(files, cleanup_path)
            if stage in ("temporal", "journal"):
                if (cleanup.get("confirmed") is not True or cleanup.get("dataDeleted") is not True
                        or cleanup.get("pgCtlStatus") != 3 or cleanup.get("originalPostmasterPidAbsent") is not True
                        or type(cleanup.get("originalPostmasterPid")) is not int or cleanup["originalPostmasterPid"] <= 0):
                    _fail("Original worker cleanup proof is incomplete: " + stage)
            else:
                clusters = cleanup.get("clusters")
                if (type(clusters) is not list or not clusters or cleanup.get("uncertainPaths")
                        or cleanup.get("cleanupErrors")
                        or not all(type(item.get("originalPostmasterPid")) is int and item["originalPostmasterPid"] > 0
                            and item.get("confirmed") is True and item.get("dataDeleted") is True
                            and item.get("pgCtlStatus") == 3 and item.get("originalPostmasterPidAbsent") is True
                            for item in clusters if type(item) is dict)
                        or not all(type(item) is dict for item in clusters)):
                    _fail("Original owned-cluster cleanup proof is incomplete: " + stage)
        census_stage = census.get("stages", {}).get(stage, {})
        if census_stage.get("count") != EXPECTED_COUNTS[stage] or census_stage.get("ids") != selectors:
            _fail("Original source census selectors differ: " + stage)
    return admission, admission_result, campaign, hosted, None


def verify_qualified_bundle(archive_bytes: bytes, release_wheel: bytes, *, expected_source_commit: str,
                            expected_source_tree: str, github: dict | None = None) -> dict:
    """Verify an original qualification archive and exact release wheel bytes.

    `github`, when supplied, is a captured run/job/artifact metadata object and
    is validated by `authenticate_github_metadata` at the workflow intake.
    """
    files = _read_zip(archive_bytes)
    binding_path = "temporal-qualification-binding.json"
    binding = _json(files, binding_path)
    expected_keys = {"schema", "sourceCommit", "sourceTree", "cohortSha256", "ownerIdentities", "originalWheelPaths", "candidateWheel",
                     "installed", "componentPrerequisiteReceipts", "receipts", "members", "workflow"}
    if set(binding) != expected_keys or binding.get("schema") != SCHEMA:
        _fail("Closed temporal qualification binding schema required")
    if binding.get("sourceCommit") != expected_source_commit or binding.get("sourceTree") != expected_source_tree:
        _fail("Qualified source/tree must equal the release tag source")
    _hex(binding.get("cohortSha256")); _hex(expected_source_commit, 40); _hex(expected_source_tree, 40)
    candidate = binding.get("candidateWheel")
    if type(candidate) is not dict or set(candidate) != {"distribution", "version", "filename", "path", "sha256", "size"}:
        _fail("Exact candidate wheel identity required")
    wheel_path = _relative(candidate.get("path")); wheel = files.get(wheel_path)
    filename = candidate.get("filename")
    if type(filename) is not str:
        _fail("Exact candidate wheel basename required")
    _relative(filename)
    if (PurePosixPath(filename).name != filename or "/" in filename or "\\" in filename
            or filename in (".", "..") or any(ord(c) < 32 or ord(c) == 127 for c in filename)
            or filename != PurePosixPath(wheel_path).name):
        _fail("Candidate wheel filename must be its canonical admitted-wheel basename")
    if (wheel is None or wheel != release_wheel or sha256(wheel) != _hex(candidate.get("sha256"))
            or candidate.get("size") != len(wheel) or not filename.endswith(".whl")):
        _fail("Release wheel is not the original qualifying wheel byte-for-byte")
    if candidate.get("distribution") != "umf-truss" or type(candidate.get("version")) is not str:
        _fail("Selected Truss distribution metadata required")
    try:
        with ZipFile(io.BytesIO(wheel)) as source_wheel:
            wheel_names = source_wheel.namelist()
            metadata_paths = [name for name in wheel_names if name.endswith(".dist-info/METADATA")]
            if len(wheel_names) != len(set(wheel_names)) or len(metadata_paths) != 1:
                _fail("Original wheel requires unique members and one distribution metadata file")
            metadata = BytesParser().parsebytes(source_wheel.read(metadata_paths[0]))
            if (metadata.get("Name", "").lower().replace("_", "-") != candidate["distribution"]
                    or metadata.get("Version") != candidate["version"]):
                _fail("Original wheel distribution/version metadata differs")
            manifest_name = "truss/_catalog_runtime/manifest.json"
            if manifest_name not in wheel_names:
                _fail("Selected temporal candidate wheel manifest is missing")
            runtime_manifest = json.loads(source_wheel.read(manifest_name))
            if runtime_manifest.get("releaseId") != "truss-catalog-runtime/0.76-temporal-candidate":
                _fail("Qualified wheel is outside the selected temporal candidate route")
    except BadZipFile as error:
        raise ValueError("Candidate wheel is not a valid wheel archive") from error
    members = binding.get("members")
    if type(members) is not dict or set(members) != set(files) - {binding_path}:
        _fail("Closed retained-member manifest differs from archive")
    for path, record in members.items():
        _relative(path)
        if (type(record) is not dict or set(record) != {"sha256", "size"}
                or record.get("sha256") != sha256(files[path]) or record.get("size") != len(files[path])):
            _fail("Retained member hash/size differs: " + path)
    admission, admission_result, campaign, hosted, component_result = _validate_campaign(files, binding)
    cohort = _json(files, binding["receipts"]["cohort"]["path"])
    installed = binding.get("installed")
    if (type(installed) is not dict or installed.get("candidateWheelSha256") != candidate["sha256"]
            or installed.get("nativeManifestSha256") != admission_result.get("nativeManifestSha256")
            or installed.get("runtimeAssets") != admission_result.get("runtimeAssets")):
        _fail("Installed candidate/native identity does not join admission")
    required_runtime_assets = {
        "_catalog_runtime/query-abi.json", "_catalog_runtime/query-temporal-abi.json",
        "_catalog_runtime/query-temporal.sql", "_catalog_runtime/query-temporal-sources.sql",
        "_catalog_runtime/query-temporal-cursor.sql", "_catalog_runtime/temporal-storage.sql",
    }
    runtime_assets = installed.get("runtimeAssets")
    if type(runtime_assets) is not dict or set(runtime_assets) != required_runtime_assets:
        _fail("Original installed SQL/ABI asset identities are incomplete")
    with ZipFile(io.BytesIO(wheel)) as source_wheel:
        for path, identity in runtime_assets.items():
            member = "truss/" + path
            if (type(identity) is not dict or set(identity) != {"sha256", "size"}
                    or member not in source_wheel.namelist()):
                _fail("Original installed runtime asset is absent: " + path)
            data = source_wheel.read(member)
            if identity.get("sha256") != sha256(data) or identity.get("size") != len(data):
                _fail("Original installed SQL/ABI bytes differ: " + path)
    wheel_map = admission.get("wheels")
    hosted_wheels = hosted.get("wheels")
    owners = hosted.get("ownerIdentities")
    truss = owners.get("truss") if type(owners) is dict else None
    if (type(wheel_map) is not dict or set(wheel_map) != {"truss", "core", "access", "weft"}
            or type(admission_result.get("wheels")) is not dict or set(admission_result["wheels"]) != set(wheel_map)):
        _fail("Original exact four-owner wheel closure required")
    for owner, truss_row in wheel_map.items():
        correspondence = binding["originalWheelPaths"].get(owner)
        if type(correspondence) is not dict or set(correspondence) != {"admissionPath", "archivePath", "sha256"}:
            _fail("Original wheel path correspondence record required: " + owner)
        if (truss_row.get("path") != correspondence.get("admissionPath")
                or truss_row.get("sha256") != correspondence.get("sha256")):
            _fail("Original absolute admission wheel row differs from its retained path correspondence: " + owner)
        member = _relative("inputs/" + correspondence.get("archivePath", ""))
        original_bytes = files.get(member)
        selected_sha = _hex(truss_row.get("sha256"))
        observed = admission_result["wheels"][owner]
        if (original_bytes is None or sha256(original_bytes) != selected_sha
                or hosted_wheels.get(owner) != {"path": correspondence["archivePath"], "sha256": selected_sha}
                or observed.get("wheelSha256") != selected_sha
                or observed.get("version") != cohort.get(owner, {}).get("version")):
            _fail("Original four-owner wheel bytes/version do not join cohort: " + owner)
        package = {"truss": "truss", "core": "umf", "access": "umf_access", "weft": "weft"}[owner]
        owner_identity = owners.get(owner)
        _wheel_identity(original_bytes, cohort[owner]["distribution"], cohort[owner]["version"],
            package=package if owner in ("core", "weft") else None,
            module_path=owner_identity.get("modulePath") if owner in ("core", "weft") else None,
            module_sha256=owner_identity.get("moduleSha256") if owner in ("core", "weft") else None)
        if owner == "core":
            for resource in owner_identity["resources"].values():
                resource_path = _relative("inputs/" + resource["path"])
                if resource_path not in files or sha256(files[resource_path]) != resource["sha256"]:
                    _fail("Canonical Core resource bytes differ from owner identity: " + resource["path"])
        if owner == "truss":
            with ZipFile(io.BytesIO(original_bytes)) as selected_wheel:
                manifest_path = "truss/_catalog_runtime/manifest.json"
                if manifest_path not in selected_wheel.namelist() or sha256(selected_wheel.read(manifest_path)) != truss["nativeManifestSha256"]:
                    _fail("Truss native manifest differs from original owner identity")
    truss_row = wheel_map["truss"]
    if truss_row.get("sha256") != candidate["sha256"]:
        _fail("Candidate wheel differs from original four-owner admission")
    if hosted.get("candidateWheel") != binding["originalWheelPaths"]["truss"]["archivePath"]:
        _fail("Original candidate wheel path differs from hosted-input manifest")
    prerequisites = binding.get("componentPrerequisiteReceipts")
    if type(prerequisites) is not list or not prerequisites:
        _fail("Missing owner component prerequisite receipts; source binding remains unqualified")
    if admission.get("componentPrerequisiteReceipts") != prerequisites:
        _fail("Component prerequisite receipt roster differs from admitted source")
    cohort_ref = binding['receipts']['cohort']
    cohort_bytes = files[_relative(cohort_ref['path'])]
    from release_cohort import component_source_refs
    from component_prerequisite_validators import selected_core_owner_context
    source_section = component_source_refs(cohort_bytes)
    component_result = require_closed_component_prerequisites(prerequisites, files,
        cohort_bytes=cohort_bytes, owner_identities=owners, admitted_wheels=hosted_wheels)
    if github is not None:
        if type(github) is not dict or github.get("sourceCommit") != expected_source_commit:
            _fail("Authenticated GitHub metadata/source binding required")
        if campaign.get("workflowRunId") != str(github.get("runId")) or campaign.get("workflowRunAttempt") != str(github.get("runAttempt")):
            _fail("Campaign original run/attempt differs from authenticated metadata")
        workflow = binding.get("workflow")
        if (type(workflow) is not dict or workflow.get("runId") != str(github.get("runId"))
                or workflow.get("runAttempt") != str(github.get("runAttempt"))
                or workflow.get("job") != CAMPAIGN_JOB or workflow.get("path") != WORKFLOW_PATH
                or workflow.get("event") != "workflow_dispatch"):
            _fail("Binding workflow claims differ from authenticated run/job")
    return {"status": "verified-original-bytes", "sourceCommit": expected_source_commit,
            "sourceTree": expected_source_tree, "candidateWheelSha256": candidate["sha256"],
            "campaignCases": 130, "workflowRunId": campaign.get("workflowRunId"),
            "workflowRunAttempt": campaign.get("workflowRunAttempt"),
            "componentResult":component_result,"campaign130":campaign,
            "selectedCore": selected_core_owner_context(
                cohort_bytes, owner=owners['core'], wheel=wheel_map['core']),
            "weftOwnerSource": {key: source_section['weft'][key] for key in
                ('sourceCommit','sourceTree','canonicalCoreSourceCommit','cargoLockSha256')},
            "admission":admission,"admissionResult":admission_result,"cohort":cohort}


def create_binding(root, *, campaign_dir, input_root, candidate_wheel, cohort_path, source_commit, source_tree,
                   workflow_run_id, workflow_run_attempt, workflow_job, workflow_path=WORKFLOW_PATH):
    """Create a closed retained bundle from original campaign/input files."""
    from pathlib import Path
    root = Path(root); campaign_dir = Path(campaign_dir); input_root = Path(input_root)
    candidate_wheel = Path(candidate_wheel); cohort_path = Path(cohort_path)
    if not campaign_dir.is_dir() or not input_root.is_dir():
        _fail("Original campaign and hosted input roots required")
    actual_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    actual_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True).strip()
    if actual_commit != source_commit or actual_tree != source_tree:
        _fail("Qualified candidate must be the exact clean campaign source commit/tree")
    campaign_path = campaign_dir / "campaign-result.json"
    admission_result_path = campaign_dir / "admission-result.json"
    census_path = campaign_dir / "census.json"
    admission_result = json.loads(admission_result_path.read_bytes())
    verified_input = json.loads((input_root / "verified-input.json").read_bytes())
    admission_path = Path(verified_input.get("admission", ""))
    if admission_path.is_symlink() or not admission_path.is_file():
        # verified-input stores the absolute path selected by the original manifest.
        _fail("Original final admission bytes are not retained in verified inputs")
    admission = json.loads(admission_path.read_bytes())
    hosted = json.loads((input_root / "hosted-input.json").read_bytes())
    correspondence = _runner_wheel_correspondence(admission, hosted)
    for owner, row in correspondence.items():
        member = input_root / row["archivePath"]
        if member.is_symlink() or not member.is_file() or sha256(member.read_bytes()) != row["sha256"]:
            _fail("Original admitted runner wheel does not map to exact retained archive bytes: " + owner)
    truss_member = input_root / correspondence["truss"]["archivePath"]
    if candidate_wheel.is_symlink() or not candidate_wheel.is_file() or candidate_wheel.resolve() != truss_member.resolve():
        _fail("Capture candidate wheel path does not identify the original Truss wheel member")
    prerequisite = admission.get("componentPrerequisiteReceipts")
    if type(prerequisite) is not list or not prerequisite:
        _fail("Missing component prerequisite receipts; retain ordinary partial-failure artifact")
    wheel_bytes = candidate_wheel.read_bytes()
    digest = sha256(wheel_bytes)
    wheel_ref = admission.get("wheels", {}).get("truss", {})
    if wheel_ref.get("sha256") != digest:
        _fail("Candidate wheel is not the original admitted wheel")
    campaign = json.loads(campaign_path.read_bytes())
    if campaign.get("passed") is not True:
        _fail("Only a complete original 130-case campaign can produce the qualified bundle")
    # Preserve every source/input/evidence file beneath the roots. The nested
    # archive's own binding is excluded from its closed member manifest.
    members: dict[str, bytes] = {}
    for base, prefix in ((input_root, "inputs"), (campaign_dir.parent, "evidence")):
        for path in sorted(base.rglob("*")):
            if path.is_file() and not path.is_symlink():
                member = _relative(prefix + "/" + path.relative_to(base).as_posix())
                members[member] = path.read_bytes()
    original_input_archive = root / "input.zip"
    if original_input_archive.is_file():
        members["inputs/original-hosted-input.zip"] = original_input_archive.read_bytes()
    for stage in EXPECTED_COUNTS:
        evidence_root = root / "docs/helix/04-build/evidence/design-audit" / ("temporal-candidate-" + campaign_dir.name + "-" + stage)
        if evidence_root.is_dir():
            for path in sorted(evidence_root.rglob("*")):
                if path.is_file() and not path.is_symlink():
                    member = _relative("evidence/native/" + stage + "/" + path.relative_to(evidence_root).as_posix())
                    members[member] = path.read_bytes()
    if not admission_path.resolve().is_relative_to(input_root.resolve()):
        _fail("Original admission must be a retained hosted-input member")
    admission_member = "inputs/" + admission_path.resolve().relative_to(input_root.resolve()).as_posix()
    if admission_member not in members:
        members[admission_member] = admission_path.read_bytes()
    # Retain the exact current selector ledger and its source hash.
    ledger_relative = "scripts/temporal-native-case-ledger.json"
    def ref(path: str) -> dict:
        return {"path": path, "sha256": sha256(members[path])}
    if cohort_path.is_symlink() or not cohort_path.is_file():
        _fail("Cohort source must be a regular committed file")
    cohort_relative = cohort_path.resolve().relative_to(root.resolve()).as_posix()
    prerequisites = prerequisite
    validator_paths = [_relative(row.get("validatorSourcePath")) for row in prerequisites]
    source_snapshot = committed_source_snapshot(root, source_commit, source_tree,
        [cohort_relative, ledger_relative, *validator_paths],
        evidence_roots=admission.get("generatedEvidenceRoots", ()))
    members["source/temporal-native-case-ledger.json"] = source_snapshot[ledger_relative]
    cohort_bytes = source_snapshot[cohort_relative]
    for row in prerequisites:
        validator_path = _relative(row.get("validatorSourcePath"))
        validator_bytes = source_snapshot[validator_path]
        if sha256(validator_bytes) != _hex(row.get("validatorSourceSha256")):
            _fail("Reviewed prerequisite validator source hash differs: " + validator_path)
        members["source/" + validator_path] = validator_bytes
    campaign_ref = ref("evidence/campaign/campaign-result.json")
    admission_result_ref = ref("evidence/campaign/admission-result.json")
    census_ref = ref("evidence/campaign/census.json")
    stage_refs = {name: ref("evidence/campaign/" + name + "/result.json") for name in EXPECTED_COUNTS}
    cohort_member = "source/truss-release-cohort.json"
    members[cohort_member] = cohort_bytes
    tree = {
        "schema": SCHEMA, "sourceCommit": source_commit, "sourceTree": source_tree,
        "ownerIdentities": json.loads(members["inputs/hosted-input.json"]).get("ownerIdentities"),
        "originalWheelPaths": correspondence,
        "cohortSha256": sha256(cohort_bytes),
        "candidateWheel": {"distribution": "umf-truss", "version": admission_result.get("wheels", {}).get("truss", {}).get("version"),
            "filename": candidate_wheel.name, "path": "inputs/" + candidate_wheel.resolve().relative_to(input_root.resolve()).as_posix(),
            "sha256": digest, "size": len(wheel_bytes)},
        "installed": {"candidateWheelSha256": digest,
            "nativeManifestSha256": json.loads(members[admission_result_ref["path"]]).get("nativeManifestSha256"),
            "runtimeAssets": json.loads(members[admission_result_ref["path"]]).get("runtimeAssets")},
        "componentPrerequisiteReceipts": prerequisites,
        "receipts": {"admission": ref(admission_member), "admissionResult": admission_result_ref,
            "campaign": campaign_ref, "ledger": {"path": "source/temporal-native-case-ledger.json", "sha256": sha256(members["source/temporal-native-case-ledger.json"])},
            "census": census_ref, "cohort": ref(cohort_member),
            "hostedInput": ref("inputs/hosted-input.json"), "stages": stage_refs},
        "members": {name: {"sha256": sha256(data), "size": len(data)} for name,data in members.items()},
        "workflow": {"runId": str(workflow_run_id), "runAttempt": str(workflow_run_attempt),
            "job": workflow_job, "path": workflow_path, "event": "workflow_dispatch"}}
    wheel_member = tree["candidateWheel"]["path"]
    if not wheel_member:
        _fail("Exact original candidate wheel is not present in admitted wheelhouse")
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        for name,data in sorted(members.items()):
            archive.writestr(name,data)
        archive.writestr("temporal-qualification-binding.json", json.dumps(tree,sort_keys=True,separators=(",",":" )).encode()+b"\n")
    return output.getvalue()


def intake_artifact(*, artifact_zip: bytes, run: dict, job: dict, artifact: dict, repository: str,
                    run_id: str, artifact_id: str, artifact_sha256: str, source_commit: str,
                    source_tree: str, output_dir) -> dict:
    """Authenticate the original Actions artifact, then stage exact release bytes."""
    authenticate_github_metadata(run=run, job=job, artifact=artifact, repository=repository,
        run_id=run_id, artifact_id=artifact_id, artifact_sha256=artifact_sha256,
        source_commit=source_commit, artifact_zip=artifact_zip)
    outer = _read_zip(artifact_zip)
    nested = [raw for name,raw in outer.items() if name.endswith("/temporal-qualified-evidence.zip")
              or name == "temporal-qualified-evidence.zip"]
    if len(nested) != 1:
        _fail("One authenticated original qualified evidence bundle required")
    evidence = nested[0]
    inner = _read_zip(evidence)
    binding = _json(inner, "temporal-qualification-binding.json")
    candidate = binding.get("candidateWheel", {})
    wheel_path = _relative(candidate.get("path"))
    wheel = inner.get(wheel_path)
    if wheel is None:
        _fail("Original candidate wheel missing from authenticated evidence bundle")
    result = verify_qualified_bundle(evidence, wheel, expected_source_commit=source_commit,
        expected_source_tree=source_tree, github={"sourceCommit": source_commit, "runId": run_id,
        "runAttempt": str(run.get("run_attempt"))})
    output_dir = __import__("pathlib").Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    wheel_out = output_dir / candidate["filename"]
    if wheel_out.exists():
        _fail("Refuse pre-existing release wheel destination")
    wheel_out.write_bytes(wheel)
    (output_dir / "temporal-qualified-evidence.zip").write_bytes(evidence)
    (output_dir / "temporal-qualification-binding.json").write_bytes(inner["temporal-qualification-binding.json"])
    (output_dir / "temporal-qualified-member-manifest.json").write_text(
        json.dumps(binding["members"], sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (output_dir / "temporal-qualification-intake.json").write_text(json.dumps({
        "schema": "truss.temporal-qualified-wheel-intake/1", "repository": repository,
        "runId": run_id, "runAttempt": str(run.get("run_attempt")), "jobId": job.get("id"),
        "artifactId": artifact_id, "artifactName": artifact.get("name"),
        "artifactSha256": artifact_sha256, "artifactZipSize": len(artifact_zip),
        "sourceCommit": source_commit, "sourceTree": source_tree,
        "qualifiedBundleSha256": sha256(evidence), "candidateWheelSha256": result["candidateWheelSha256"]
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {**result, "wheelPath": str(wheel_out), "evidencePath": str(output_dir / "temporal-qualified-evidence.zip")}


def verify_release_staging(directory, *, source_commit: str, source_tree: str) -> dict:
    """Recheck the exact release wheel and qualification assets at each boundary."""
    from pathlib import Path
    root = Path(directory)
    binding_bytes = (root / "temporal-qualification-binding.json").read_bytes()
    bundle = (root / "temporal-qualified-evidence.zip").read_bytes()
    binding = json.loads(binding_bytes)
    wheel = root / binding["candidateWheel"]["filename"]
    if not wheel.is_file() or wheel.is_symlink():
        _fail("Staged exact qualified wheel is missing or unsafe")
    result = verify_qualified_bundle(bundle, wheel.read_bytes(), expected_source_commit=source_commit,
        expected_source_tree=source_tree)
    inner = _read_zip(bundle)
    if inner.get("temporal-qualification-binding.json") != binding_bytes:
        _fail("Staged binding document differs from original qualification bundle")
    intake = json.loads((root / "temporal-qualification-intake.json").read_bytes())
    manifest = json.loads((root / "temporal-qualified-member-manifest.json").read_bytes())
    _hex(intake.get("artifactSha256"))
    if re.fullmatch(r"[1-9][0-9]{0,19}", str(intake.get("artifactId"))) is None:
        _fail("Staged authenticated artifact identifier is invalid")
    if (intake.get("schema") != "truss.temporal-qualified-wheel-intake/1"
            or intake.get("sourceCommit") != source_commit or intake.get("sourceTree") != source_tree
            or intake.get("candidateWheelSha256") != result["candidateWheelSha256"]
            or intake.get("qualifiedBundleSha256") != sha256(bundle)
            or str(intake.get("runId")) != binding["workflow"].get("runId")
            or str(intake.get("runAttempt")) != binding["workflow"].get("runAttempt")
            or manifest != binding.get("members")):
        _fail("Staged intake/member manifest does not join authenticated qualification")
    return {**result, "artifactId": intake["artifactId"], "artifactSha256": intake["artifactSha256"],
            "artifactRunId": intake["runId"], "artifactRunAttempt": intake["runAttempt"]}


if __name__ == "__main__":
    import argparse
    import os
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-bundle", action="store_true")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--campaign-dir", type=Path)
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--candidate-wheel", type=Path)
    parser.add_argument("--cohort", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--source-tree")
    parser.add_argument("--workflow-run-id", default=os.environ.get("GITHUB_RUN_ID"))
    parser.add_argument("--workflow-run-attempt", default=os.environ.get("GITHUB_RUN_ATTEMPT"))
    parser.add_argument("--workflow-job", default=CAMPAIGN_JOB)
    parser.add_argument("--intake", action="store_true")
    parser.add_argument("--run-json", type=Path)
    parser.add_argument("--job-json", type=Path)
    parser.add_argument("--artifact-json", type=Path)
    parser.add_argument("--artifact-zip", type=Path)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--run-id")
    parser.add_argument("--artifact-id")
    parser.add_argument("--artifact-sha256")
    args = parser.parse_args()
    if args.create_bundle:
        if any(value is None for value in (args.root,args.campaign_dir,args.input_root,args.candidate_wheel,args.cohort,args.output,args.source_commit,args.source_tree,args.workflow_run_id,args.workflow_run_attempt)):
            parser.error("Actual successful campaign, original inputs, candidate wheel and workflow identities required")
        raw = create_binding(args.root,campaign_dir=args.campaign_dir,input_root=args.input_root,candidate_wheel=args.candidate_wheel,
            cohort_path=args.cohort,source_commit=args.source_commit,source_tree=args.source_tree,
            workflow_run_id=args.workflow_run_id,workflow_run_attempt=args.workflow_run_attempt,workflow_job=args.workflow_job)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_bytes(raw)
        print(json.dumps({"schema":SCHEMA,"bundleSha256":sha256(raw),"size":len(raw)},sort_keys=True))
    elif args.intake:
        if any(value is None for value in (args.run_json,args.job_json,args.artifact_json,args.artifact_zip,args.repository,args.run_id,args.artifact_id,args.artifact_sha256,args.source_commit,args.source_tree,args.output)):
            parser.error("Authenticated original run/job/artifact metadata and source identity required")
        result=intake_artifact(artifact_zip=args.artifact_zip.read_bytes(),run=json.loads(args.run_json.read_bytes()),
            job=json.loads(args.job_json.read_bytes()),artifact=json.loads(args.artifact_json.read_bytes()),repository=args.repository,
            run_id=args.run_id,artifact_id=args.artifact_id,artifact_sha256=args.artifact_sha256,
            source_commit=args.source_commit,source_tree=args.source_tree,output_dir=args.output)
        print(json.dumps(result,sort_keys=True))
    else:
        parser.error("Select exactly one of --create-bundle or --intake")
