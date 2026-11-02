#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Capture an authentic Truss ABI1.2 compiler request or replay it in Weft 0.4.56.

The capture subcommand runs only the existing three-row ABI1.2 cursor baseline
and its observational capture companion. Replay never connects to PostgreSQL
and never executes compiler-produced SQL.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "packages/python/tests"
PUBLIC_TRUSS_054_WHEEL_SHA256 = "4aebc56e92fdbde6714d9b811860707d2ffc9b0edbc63cc91e9dc3488c042b52"
WEFT_056_CHECKSUM_URL = "https://github.com/DocumentDrivenDX/weft/releases/download/v0.4.56/SHA256SUMS"


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def payload_record(text: str) -> dict[str, object]:
    raw = text.encode("utf-8", errors="strict")
    return {"utf8": text, "base64": base64.b64encode(raw).decode("ascii"), "sha256": sha256(raw), "byteLength": len(raw)}


def validate_payloads(value: object, location: str = "capture") -> int:
    """Validate every redundant byte representation before any owner API call."""
    fields = {"utf8", "base64", "sha256", "byteLength"}
    if type(value) is dict:
        if (fields - {"sha256"}).intersection(value):
            if set(value) != fields or any(type(value[k]) is not str for k in fields - {"byteLength"}):
                raise ValueError(f"Malformed payload at {location}")
            raw = value["utf8"].encode("utf-8", errors="strict")
            if (type(value["byteLength"]) is not int or value["byteLength"] != len(raw)
                    or value["sha256"] != sha256(raw)
                    or base64.b64decode(value["base64"], validate=True) != raw
                    or base64.b64encode(raw).decode("ascii") != value["base64"]):
                raise ValueError(f"Payload bytes/hash/length differ at {location}")
            return 1
        return sum(validate_payloads(child, f"{location}.{key}") for key, child in value.items())
    if type(value) is list:
        return sum(validate_payloads(child, f"{location}[{index}]") for index, child in enumerate(value))
    return 0


def refuse_existing_output(path: Path) -> None:
    for candidate in (path, path.with_name(path.name + ".tmp"),
                      path.with_name(path.name + ".run.json"), path.with_name(path.name + ".cleanup.json")):
        if candidate.exists() or candidate.is_symlink():
            raise ValueError(f"Existing probe output refused: {candidate}")


def verify_wheel_module(wheel: Path, checksums: Path, installed_module: Path) -> dict[str, object]:
    if not wheel.name.startswith("umf_weft-0.4.56-"):
        raise ValueError("Public umf-weft 0.4.56 wheel required")
    entries = {}
    for line in checksums.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2:
            filename = parts[1].lstrip("*")
            if filename in entries:
                raise ValueError(f"Duplicate checksum entry: {filename}")
            entries[filename] = parts[0]
    wheel_sha = sha256(wheel.read_bytes())
    if entries.get(wheel.name) != wheel_sha:
        raise ValueError("Candidate wheel differs from official release checksums")
    with zipfile.ZipFile(wheel) as archive:
        members = [name for name in archive.namelist()
                   if name.startswith("weft/weft") and name.endswith((".so", ".pyd", ".dylib"))]
        if len(members) != 1:
            raise ValueError("Exactly one native Weft wheel module required")
        native_sha = sha256(archive.read(members[0]))
    if sha256(installed_module.read_bytes()) != native_sha:
        raise ValueError("Installed Weft native module differs from verified candidate wheel")
    return {"wheel": str(wheel), "wheelSha256": wheel_sha,
            "checksums": str(checksums), "checksumsSha256": sha256(checksums.read_bytes()),
            "officialChecksumsUrl": WEFT_056_CHECKSUM_URL,
            "wheelNativeMember": members[0], "nativeModule": str(installed_module),
            "nativeModuleSha256": native_sha}


def confirm_native_stop(pg_ctl: Path, directory: Path, original_pid: int) -> dict[str, object]:
    """Keep data intact until pg_ctl and the original process both prove stop."""
    if type(original_pid) is not int or original_pid <= 0:
        raise ValueError("Observed positive original postmaster PID required")
    status = subprocess.run([str(pg_ctl), "-D", str(directory), "status"],
                            capture_output=True, text=True, timeout=15, check=False)
    pid_absent = False
    try:
        os.kill(original_pid, 0)
    except ProcessLookupError:
        pid_absent = True
    except PermissionError:
        pass
    proof = {"originalPostmasterPid": original_pid, "originalPostmasterPidAbsent": pid_absent,
             "pgCtlStatus": status.returncode, "pgCtlStdout": status.stdout,
             "pgCtlStderr": status.stderr,
             "confirmed": status.returncode == 3 and pid_absent}
    return proof


def classify(raw: object) -> dict[str, object]:
    if type(raw) is not str:
        return {"kind": "unexpected-return-type", "type": type(raw).__name__, "repr": repr(raw)}
    result: dict[str, object] = {"raw": payload_record(raw)}
    try:
        decoded = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        result.update(kind="non-json", errorType=type(error).__name__, error=str(error))
        return result
    result["json"] = decoded
    result["kind"] = ("compiled-or-checked" if type(decoded) is dict and decoded.get("status") == "compiled"
                      else "structured-refusal")
    return result


def invoke(api, *args) -> dict[str, object]:
    try:
        return classify(api(*args))
    except BaseException as error:  # retain native extension exceptions exactly
        return {"kind": "exception", "errorType": type(error).__name__, "error": str(error),
                "traceback": "".join(traceback.format_exception(type(error), error, error.__traceback__))}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def capture(args: argparse.Namespace) -> int:
    refuse_existing_output(args.output.absolute())
    output = args.output.resolve()
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError(f"Python 3.11 required, got {sys.version.split()[0]}")
    if importlib.metadata.version("umf-truss") != "0.0.54":
        raise RuntimeError("Installed public umf-truss==0.0.54 required")
    if importlib.metadata.version("weft-sql") != "0.4.51":
        raise RuntimeError("Installed original weft-sql==0.4.51 required")
    import truss
    if Path(truss.__file__).resolve().is_relative_to(ROOT / "packages/python/src"):
        raise RuntimeError("Public installed Truss wheel required; source fallback refused")
    truss_wheel = args.truss_wheel.resolve()
    weft_wheel = args.weft_wheel.resolve()
    pgserver_wheel = args.pgserver_wheel.resolve()
    checksum_file = args.pgserver_checksums.resolve()
    if sha256(truss_wheel.read_bytes()) != PUBLIC_TRUSS_054_WHEEL_SHA256:
        raise RuntimeError("Truss wheel does not match the audited public 0.0.54 artifact")
    from truss._current_query_originals import _CONSUMER_COHORTS
    import weft
    import weft.weft as native_weft
    module_sha = sha256(Path(native_weft.__file__).read_bytes())
    cohorts = [item for item in _CONSUMER_COHORTS if item["weftModuleSha256"] == module_sha]
    if len(cohorts) != 1 or sha256(weft_wheel.read_bytes()) != cohorts[0]["weftWheelSha256"]:
        raise RuntimeError("Weft wheel does not match the installed 0.4.51 frozen module cohort")
    pgserver_sums = {}
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            pgserver_sums[parts[1].lstrip("*")] = parts[0]
    if pgserver_sums.get(pgserver_wheel.name) != sha256(pgserver_wheel.read_bytes()):
        raise RuntimeError("pgserver wheel does not match the supplied checksum-verified release sums")
    os.environ["TRUSS_T4A_PUBLIC_WHEELS"] = json.dumps({
        "umfTruss054": {"path": str(truss_wheel), "sha256": sha256(truss_wheel.read_bytes())},
        "weftSql051": {"path": str(weft_wheel), "sha256": sha256(weft_wheel.read_bytes())},
        "pgserverPg186": {"path": str(pgserver_wheel), "sha256": sha256(pgserver_wheel.read_bytes()),
                          "sumsFile": str(checksum_file), "sumsFileSha256": sha256(checksum_file.read_bytes())},
    }, sort_keys=True)

    os.environ["TRUSS_T4A_CAPTURE_PATH"] = str(output)
    sys.path.insert(0, str(TESTS))
    import unittest

    test_name = "test_weft_abi12_cohort_probe_native.WeftABI12CohortProbeNativeTests"
    names = [f"{test_name}.test_actual_selected_cursor_decodes_all_batches_and_descriptors",
             f"{test_name}.test_capture_authentic_request_and_old_cohort_response"]
    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    from test_weft_abi12_cohort_probe_native import WeftABI12CohortProbeNativeTests
    cleanup = getattr(WeftABI12CohortProbeNativeTests, "cleanup_proof", {"confirmed": False})
    runtime_record = {
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "passed": result.wasSuccessful() and result.testsRun == 2 and not result.skipped and cleanup.get("confirmed") is True,
        "cleanup": cleanup,
    }
    _write_json(output.with_name(output.name + ".run.json"), runtime_record)
    if output.is_file():
        record = json.loads(output.read_text(encoding="utf-8"))
        record["testRunAndCleanup"] = runtime_record
        _write_json(output, record)
    print(json.dumps({"captureOutput": str(output), "testRunAndCleanup": runtime_record}, sort_keys=True))
    return 0 if runtime_record["passed"] else 1


def replay(args: argparse.Namespace) -> int:
    refuse_existing_output(args.output.absolute())
    capture_path = args.capture.resolve()
    capture_bytes = capture_path.read_bytes()
    def unique_members(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate capture JSON member: {key}")
            result[key] = value
        return result
    captured = json.loads(capture_bytes, object_pairs_hook=unique_members)
    payload_count = validate_payloads(captured)
    if type(captured) is not dict or captured.get("schema") != "truss.weft-abi12-native-capture/0.1" or payload_count < 10:
        raise ValueError("Complete authentic capture payloads required")
    test_run = captured["testRunAndCleanup"]
    cleanup = test_run["cleanup"]
    if (test_run.get("passed") is not True or test_run.get("testsRun") != 2
            or any(test_run.get(key) != 0 for key in ("failures", "errors", "skipped"))
            or cleanup.get("confirmed") is not True or cleanup.get("pgCtlStatus") != 3
            or cleanup.get("originalPostmasterPidAbsent") is not True):
        raise ValueError("Successful original baseline/capture and confirmed native cleanup required")
    request = captured["compilerCall"]["request"]["utf8"]
    page_size = captured["compilerCall"]["pageSize"]
    after = captured["compilerCall"]["after"]
    engine_page_input = captured["enginePage"]["input"]["utf8"]
    original_program = captured["enginePage"]["program"]["utf8"]
    checker_call = captured["enginePage"]["checkerCall"]
    current_request = checker_call["currentRequest"]["utf8"]
    after_json = checker_call["afterJson"]["utf8"]
    call = captured["compilerCall"]
    for required_payload in (call["request"], call["arguments"][0], call["response"], call["bindingJson"],
                             captured["enginePage"]["input"], captured["enginePage"]["program"],
                             checker_call["program"], checker_call["currentRequest"],
                             checker_call["afterJson"], checker_call["result"]):
        if validate_payloads(required_payload) != 1:
            raise ValueError("Required original payload record is missing")
    if (call["arguments"] != [call["request"], page_size, after]
            or type(page_size) is not int or page_size != 2 or after is not None
            or json.loads(request)["target"]["bindingJson"] != call["bindingJson"]["utf8"]
            or json.loads(engine_page_input)["request"] != json.loads(request)
            or checker_call["program"] != captured["enginePage"]["program"]):
        raise ValueError("Captured original compiler/binding/program argument correspondence differs")

    sys.path.insert(0, str(ROOT / "packages/python/src"))
    import truss
    import truss._query_runtime as query_runtime
    import weft
    if (weft.__version__ != "0.4.56" or importlib.metadata.version("umf-weft") != "0.4.56"
            or sys.version_info[:2] != (3, 11)):
        raise RuntimeError("Replay requires the separate public umf-weft==0.4.56 probe environment")
    if Path(truss.__file__).resolve() != (ROOT / "packages/python/src/truss/__init__.py").resolve():
        raise RuntimeError("Replay must use this checkout's unmodified Truss source guard")

    native_path = Path(weft.weft.__file__).resolve()
    candidate_provenance = verify_wheel_module(args.weft_wheel.resolve(), args.weft_checksums.resolve(), native_path)
    guard = query_runtime.compiler()
    report: dict[str, object] = {
        "schema": "truss.weft-abi12-cohort-probe/0.1",
        "scope": "Raw ordinary ABI1.2 compatibility diagnostic only; no SQL execution, native acceptance, or adoption claim",
        "captureFile": str(capture_path),
        "captureFileSha256": sha256(capture_bytes),
        "captureSourceCommit": captured["sourceCommit"],
        "validatedPayloadCount": payload_count,
        "probeScript": {"path": str(Path(__file__).resolve()),
                        "sha256": sha256(Path(__file__).read_bytes())},
        "trussSource": {"path": str(Path(truss.__file__).resolve()),
                        "queryRuntimePath": str(Path(query_runtime.__file__).resolve()),
                        "queryRuntimeSha256": sha256(Path(query_runtime.__file__).read_bytes())},
        "candidate": {"distribution": "umf-weft", "version": importlib.metadata.version("umf-weft"),
                      "python": sys.version, "platform": platform.platform(),
                      **candidate_provenance},
        "guard": {"kind": "Truss-cohort-refusal" if guard is None else "unexpectedly-available",
                  "compilerReturnedNone": guard is None,
                  "sourceGuardVersion": weft.__version__},
        "inputs": {"request": captured["compilerCall"]["request"],
                   "pageSize": page_size, "after": after,
                   "enginePageInput": captured["enginePage"]["input"],
                   "originalEngineProgram": captured["enginePage"]["program"],
                   "checkerCall": checker_call},
        "raw": {},
    }
    if guard is not None:
        raise RuntimeError("Truss source guard did not refuse the 0.4.56 candidate")

    for api_name, call_args in (
        ("compile_truss_runtime_json", (request,)),
        ("compile_truss_runtime_page_json", (request, page_size, after)),
        ("compile_engine_page_json", (engine_page_input,)),
    ):
        api = getattr(weft, api_name, None)
        report["raw"][api_name] = ({"kind": "api-absent"} if not callable(api) else invoke(api, *call_args))

    fresh_page = report["raw"]["compile_engine_page_json"]
    fresh_program = None
    if fresh_page.get("kind") == "compiled-or-checked":
        fresh_program = fresh_page["raw"]["utf8"]
    selected_program = fresh_program if fresh_program is not None else original_program
    selected_program_origin = "fresh-056-engine-page" if fresh_program is not None else "captured-051-engine-page"
    checker_args = (selected_program, current_request, after_json)
    checker = getattr(weft, "check_engine_page_json", None)
    report["raw"]["check_engine_page_json"] = (
        {"kind": "api-absent"} if not callable(checker)
        else {"programOrigin": selected_program_origin, "result": invoke(checker, *checker_args)})
    report["raw"]["check_engine_page_json"]["inputs"] = {
        "program": payload_record(selected_program), "request": checker_call["currentRequest"],
        "afterJson": checker_call["afterJson"]}

    _write_json(args.output, report)
    print(json.dumps({"status": "recorded", "output": str(args.output.resolve()),
                      "outputSha256": sha256(args.output.read_bytes()),
                      "guard": report["guard"],
                      "rawKinds": {name: value.get("result", value).get("kind", "unknown")
                                   for name, value in report["raw"].items()}}, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--output", type=Path, required=True, help="path for authentic native capture JSON")
    capture_parser.add_argument("--truss-wheel", type=Path, required=True)
    capture_parser.add_argument("--weft-wheel", type=Path, required=True)
    capture_parser.add_argument("--pgserver-wheel", type=Path, required=True)
    capture_parser.add_argument("--pgserver-checksums", type=Path, required=True,
                                help="official SHA256SUMS retained by the pinned runtime installer")
    capture_parser.set_defaults(function=capture)
    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("--capture", type=Path, required=True)
    replay_parser.add_argument("--output", type=Path, required=True)
    replay_parser.add_argument("--weft-wheel", type=Path, required=True)
    replay_parser.add_argument("--weft-checksums", type=Path, required=True,
                               help="official v0.4.56 SHA256SUMS retained during runner setup")
    replay_parser.set_defaults(function=replay)
    args = parser.parse_args()
    try:
        return args.function(args)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
        print(json.dumps({"status": "refused", "errorType": type(error).__name__, "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
