#!/usr/bin/env python3
"""Verify the Truss 0.0.50 CI package and managed/comparison artifact bytes.

This records artifact evidence only. It does not run native tests, start a
database, qualify Lakebase, or establish a public release/tag gate.
"""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import importlib.util
import json
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

QA = Path(__file__).parent
SOURCE_COMMIT = "0b61b5107ba453e4b18291203e307b67ac7da9f8"
VERSION = "0.0.50"
PACKAGE_ARTIFACT_ID = 12549011611
MANAGED_ARTIFACT_ID = 12550315188
WORKFLOW_RUN_ID = 40062344218
PACKAGE_API_DIGEST = "sha256:1ec3d3cd383e72fda79736974347abbc69e3f589a2aeb02ba251932b420c9a0b"
MANAGED_API_DIGEST = "sha256:28597d269ab2c370955ec93dc141e804fe4b077ee3966052d54d33d246a0aa18"
PACKAGE_VERIFIER_SHA256 = "dc71d308a72cfbc1b04dd58eb96ef0de5d721790305e27dff3d68919bb8815a7"
HELPER_SHA256 = "f0f313ad9058076a9f5cc0d479fa2cb50bdc4002669308f7033a26ebf0235e08"
DRIVER_SHA256 = "1a5163176f429bd923aaa0196233192b6c08347dfb1b736bcdd90c33270a00c4"
WHEEL_NAME = "truss_toolkit-0.0.50-py3-none-any.whl"
WHEEL_SHA256 = "179842a2310183efa2f68ab294892aa6beb0da6e5e79cdd2fea05bb3e16e1efb"
BASELINE_WHEEL_NAME = "truss_toolkit-0.0.49-py3-none-any.whl"
BASELINE_WHEEL_SHA256 = "7ea14b2787f02cbeec9ad99d835adbcc30c684fd5be8e0765a1d8198b50e7182"
NATIVE_MANIFEST_SHA256 = "288801f7177338328441b5d3ce9328af31740ebf513f04ea45e30ae316a9f3a4"
OWNER_ORACLE_COMMIT = "5ba77cff91a121a44c82f6bce32a78d8842161b5"
OWNER_ORACLE_BUN = "1.4.3"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"Non-finite JSON constant: {value}")


def read_json(path: Path) -> object:
    return json.loads(
        path.read_bytes(),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )


def _load_module(path: Path, name: str, expected_sha256: str) -> object:
    raw = path.read_bytes()
    require(sha256(raw) == expected_sha256, f"Unexpected source hash for {path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"Cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _api_binding(
    path: Path, *, artifact_id: int, digest: str
) -> dict[str, object]:
    value = read_json(path)
    require(type(value) is dict, "GitHub artifact API record must be an object")
    require(type(value.get("id")) is int and value["id"] == artifact_id, "Artifact ID mismatch")
    require(value.get("name") == ("python-package" if artifact_id == PACKAGE_ARTIFACT_ID else "managed-grants-qualification-ubuntu-24.04"), "Artifact name mismatch")
    require(value.get("expired") is False, "Artifact is expired")
    require(value.get("digest") == digest, "API-reported artifact digest mismatch")
    require(type(value.get("size_in_bytes")) is int and value["size_in_bytes"] > 0, "Artifact API size is invalid")
    workflow = value.get("workflow_run")
    require(type(workflow) is dict, "Artifact workflow binding is missing")
    require(type(workflow.get("id")) is int and workflow["id"] == WORKFLOW_RUN_ID, "Artifact workflow run mismatch")
    require(workflow.get("head_sha") == SOURCE_COMMIT, "Artifact workflow source mismatch")
    return {
        "artifactId": artifact_id,
        "name": value["name"],
        "workflowRunId": WORKFLOW_RUN_ID,
        "workflowHeadSha": SOURCE_COMMIT,
        "apiReportedZipDigest": digest.removeprefix("sha256:"),
        "digestKind": "GitHub API-reported artifact ZIP digest; not independently recomputed",
        "sizeInBytes": value["size_in_bytes"],
    }


def _source_identity(source_root: Path) -> dict[str, str]:
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source_root, text=True
    ).strip()
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=source_root,
        text=True,
    ).strip()
    require(head == SOURCE_COMMIT, "Source checkout HEAD mismatch")
    require(not status, "Source checkout is not clean")
    return {"commit": head, "status": "clean"}


def _managed_outcomes(
    managed_dir: Path,
    receipt: dict[str, object],
    gate_constants: dict[str, object],
    helper: object,
) -> dict[str, object]:
    outcomes = receipt.get("outcomes")
    require(type(outcomes) is list, "Managed outcomes are missing")
    helper._validate_managed_test_total(receipt)
    modules = gate_constants.get("MODULES")
    require(type(modules) is tuple, "Managed source MODULES must be a tuple")
    require(
        [row.get("module") for row in outcomes if type(row) is dict]
        == list(modules)
        and len(outcomes) == len(modules),
        "Managed outcome sequence differs from source MODULES",
    )
    log_names: set[str] = set()
    log_receipts: list[dict[str, object]] = []
    total_tests = 0
    for row in outcomes:
        require(type(row) is dict, "Managed outcome row is malformed")
        tests = row.get("tests")
        require(type(tests) is int and tests > 0, "Managed test count is invalid")
        require(
            row.get("passed") is True
            and type(row.get("returncode")) is int
            and row["returncode"] == 0
            and row.get("baselineRestored") is True
            and row.get("timedOut") is False,
            "Managed outcome did not pass with restoration",
        )
        log_name = row.get("log")
        require(
            type(log_name) is str
            and log_name.endswith(".log.gz")
            and PurePosixPath(log_name).name == log_name
            and log_name not in log_names,
            "Managed outcome log path is invalid or duplicated",
        )
        log_names.add(log_name)
        compressed = (managed_dir / log_name).read_bytes()
        require(type(row.get("logSha256")) is str, "Managed log digest is missing")
        expanded = gzip.decompress(compressed)
        require(
            sha256(compressed) == row["logSha256"],
            "Managed compressed log hash mismatch",
        )
        log_receipts.append(
            {
                "name": log_name,
                "compressedBytes": len(compressed),
                "compressedSha256": sha256(compressed),
                "decompressedBytes": len(expanded),
                "decompressedSha256": sha256(expanded),
                "matchesOutcome": True,
            }
        )
        total_tests += tests
    actual_logs = {path.name for path in managed_dir.glob("*.log.gz")}
    require(actual_logs == log_names, "Managed log artifact inventory differs from outcomes")
    require(type(receipt.get("tests")) is int and receipt["tests"] == total_tests == 174, "Managed test total mismatch")
    require(type(receipt.get("skipped")) is int and receipt["skipped"] == 0, "Managed gate has skips")
    return {"moduleCount": len(modules), "tests": total_tests, "logs": log_receipts}


def _validate_comparison(
    source_root: Path,
    package_assets: Path,
    managed_dir: Path,
    receipt: dict[str, object],
    helper: object,
) -> dict[str, object]:
    driver_path = source_root / "scripts/measure-installer-submissions.py"
    driver = _load_module(driver_path, "truss_measurement_driver", DRIVER_SHA256)
    binding_path = managed_dir / "installer-comparison/binding.json"
    report_path = managed_dir / "installer-comparison/report.json"
    binding = read_json(binding_path)
    comparison = read_json(report_path)
    require(type(binding) is dict and type(comparison) is dict, "Comparison evidence is malformed")
    expected_keys = {
        "schemaVersion", "sourceCommit", "candidateWheelName", "candidateWheelSha256",
        "driverSha256", "baselineWheelName", "baselineWheelSha256",
        "baselineRuntimeManifestSha256", "reportName", "reportSha256", "scope",
    }
    require(set(binding) == expected_keys, "Comparison binding fields are not closed")
    require(type(binding.get("schemaVersion")) is int and binding["schemaVersion"] == 1, "Comparison binding schema mismatch")
    report_raw = report_path.read_bytes()
    wheel_path = package_assets / WHEEL_NAME
    wheel_sha = sha256(wheel_path.read_bytes())
    require(wheel_sha == WHEEL_SHA256, "Candidate wheel digest mismatch")
    require(binding.get("sourceCommit") == SOURCE_COMMIT, "Comparison source commit mismatch")
    require(binding.get("candidateWheelName") == WHEEL_NAME and binding.get("candidateWheelSha256") == WHEEL_SHA256, "Candidate wheel binding mismatch")
    require(binding.get("driverSha256") == DRIVER_SHA256, "Comparison driver binding mismatch")
    require(binding.get("baselineWheelName") == BASELINE_WHEEL_NAME and binding.get("baselineWheelSha256") == BASELINE_WHEEL_SHA256, "Public49 baseline binding mismatch")
    require(binding.get("baselineRuntimeManifestSha256") == NATIVE_MANIFEST_SHA256, "Baseline runtime manifest mismatch")
    require(binding.get("reportName") == "report.json" and binding.get("reportSha256") == sha256(report_raw), "Comparison report digest mismatch")
    require(binding.get("scope") == helper.INSTALLER_COMPARISON_SCOPE, "Comparison scope mismatch")
    require(
        comparison.get("diagnostic") == "truss-installer-client-submissions/0.1"
        and comparison.get("status") == "passed",
        "Comparison did not pass",
    )
    require(
        comparison.get("workerScope") == "script_owned_WorkerCluster"
        and comparison.get("workerCleanup") == "confirmed"
        and comparison.get("workerShutdown") == "confirmed"
        and comparison.get("workerBaselineRestored") is True,
        "Comparison worker cleanup is not confirmed",
    )
    measurements = comparison.get("measurements")
    require(type(measurements) is dict, "Comparison measurements are missing")
    for phase_name in ("baseline", "candidate"):
        phase = measurements.get(phase_name)
        require(type(phase) is dict, "Comparison phase is missing")
        require(
            phase.get("status") == "measured"
            and type(phase.get("childExitCode")) is int
            and phase["childExitCode"] == 0,
            "Comparison phase did not complete successfully",
        )
        installation = phase.get("installation")
        require(
            type(installation) is dict
            and installation.get("status") == "success"
            and installation.get("resultVariant") == "PendingCatalogInstallation",
            "Comparison phase did not return pending installation",
        )
        require(
            phase.get("budgetsMs") == {"statement": 60000, "operation": 60000},
            "Comparison timeout budget mismatch",
        )
        caller = phase.get("caller")
        package = phase.get("package")
        require(
            type(caller) is dict
            and caller.get("rollbackConfirmed") is True
            and phase.get("fixtureCleanup") == "confirmed"
            and phase.get("instrumentationHooksRestored") is True
            and type(package) is dict
            and package.get("unchanged") is True,
            "Comparison phase cleanup or package-restoration evidence is missing",
        )
    baseline = measurements["baseline"]
    candidate = measurements["candidate"]
    baseline_wheel = baseline.get("baselineWheel")
    require(
        type(baseline_wheel) is dict
        and baseline_wheel.get("wheelSha256") == BASELINE_WHEEL_SHA256
        and baseline_wheel.get("distributionVersion") == "0.0.49"
        and baseline_wheel.get("payloadMembersEqual") is True,
        "Baseline public49 wheel custody mismatch",
    )
    candidate_before = candidate.get("package", {}).get("before", {})
    require(
        candidate_before.get("sourceFreeze", {}).get("gitCommit") == SOURCE_COMMIT,
        "Candidate source freeze mismatch",
    )
    base_calls = baseline.get("measurement", {}).get("cursorExecuteSubmissionCount")
    candidate_calls = candidate.get("measurement", {}).get("cursorExecuteSubmissionCount")
    require(
        type(base_calls) is int
        and type(candidate_calls) is int
        and base_calls > candidate_calls > 0,
        "Comparison submission counts do not show the recorded reduction",
    )
    phase_measurements: dict[str, dict[str, object]] = {}
    for label in ("baseline", "candidate"):
        phase_measurement = measurements[label].get("measurement")
        require(type(phase_measurement) is dict, "Comparison timing counters are missing")
        for key in (
            "installElapsedNs",
            "installerProcessCpuElapsedNs",
            "cursorExecuteSubmissionCount",
            "cursorNextsetCallCount",
            "cursorNextsetElapsedNs",
        ):
            value = phase_measurement.get(key)
            require(type(value) is int and value >= 0, f"Invalid comparison counter: {key}")
        phase_measurements[label] = {
            "installElapsedNs": phase_measurement["installElapsedNs"],
            "installElapsedSeconds": phase_measurement["installElapsedNs"] / 1_000_000_000,
            "installerProcessCpuElapsedNs": phase_measurement[
                "installerProcessCpuElapsedNs"
            ],
            "installerProcessCpuElapsedSeconds": phase_measurement[
                "installerProcessCpuElapsedNs"
            ]
            / 1_000_000_000,
            "cursorExecuteSubmissionCount": phase_measurement[
                "cursorExecuteSubmissionCount"
            ],
            "cursorNextsetCallCount": phase_measurement["cursorNextsetCallCount"],
            "cursorNextsetElapsedNs": phase_measurement["cursorNextsetElapsedNs"],
        }
    driver._validate_published_comparison(
        comparison,
        source_root=source_root / "packages/python/src/truss",
        candidate_wheel=wheel_path,
        source_commit=SOURCE_COMMIT,
        project_version=VERSION,
        target_manifest_sha256=NATIVE_MANIFEST_SHA256,
    )
    return {
        "bindingSha256": sha256(binding_path.read_bytes()),
        "reportSha256": sha256(report_raw),
        "reportStatus": comparison["status"],
        "workerCleanup": comparison["workerCleanup"],
        "workerShutdown": comparison["workerShutdown"],
        "snapshotSha256": comparison.get("comparison", {}).get("baselineSnapshotSha256"),
        "executeSubmissions": {"baseline": base_calls, "candidate": candidate_calls},
        "phaseMeasurements": phase_measurements,
    }


def verify(
    source_root: Path,
    package_assets: Path,
    managed_dir: Path,
    package_api_path: Path,
    managed_api_path: Path,
) -> dict[str, object]:
    source_root = source_root.resolve()
    before = _source_identity(source_root)
    require(package_assets.is_dir() and managed_dir.is_dir(), "Artifact directories are missing")
    helper_path = QA / "verify-public50-artifacts.py"
    helper = _load_module(helper_path, "public50_artifact_helpers", HELPER_SHA256)
    package_verifier_path = QA / "verify-ci-0b61-package.py"
    package_verifier = _load_module(
        package_verifier_path, "ci_package_verifier", PACKAGE_VERIFIER_SHA256
    )
    package_api = _api_binding(
        package_api_path, artifact_id=PACKAGE_ARTIFACT_ID, digest=PACKAGE_API_DIGEST
    )
    managed_api = _api_binding(
        managed_api_path, artifact_id=MANAGED_ARTIFACT_ID, digest=MANAGED_API_DIGEST
    )
    package_report = package_verifier.verify(
        source_root, package_assets, package_api_path, SOURCE_COMMIT
    )
    managed_receipt_path = managed_dir / "qualification.json"
    receipt = read_json(managed_receipt_path)
    require(type(receipt) is dict, "Managed qualification receipt is malformed")
    require(receipt.get("sourceCommit") == SOURCE_COMMIT, "Managed receipt source commit mismatch")
    require(
        type(receipt.get("platform")) is str
        and receipt["platform"].lower().startswith("linux"),
        "Managed qualification is not from Linux",
    )
    require(receipt.get("wheelSha256") == WHEEL_SHA256, "Managed wheel hash mismatch")
    require(receipt.get("nativeManifestSha256") == NATIVE_MANIFEST_SHA256, "Managed native manifest mismatch")
    require(receipt.get("passed") is True, "Managed qualification did not pass")
    require(type(receipt.get("skipped")) is int and receipt["skipped"] == 0, "Managed qualification has skips")
    for field in ("workerStopped", "workerBaselineRestored", "inputsUnchanged", "payloadUnchanged"):
        require(receipt.get(field) is True, f"Managed qualification {field} is not true")
    require(type(receipt.get("packageFilesVerified")) is int and receipt["packageFilesVerified"] == 469, "Managed source payload count mismatch")
    require(receipt.get("lakebaseAcceptance") == "not_run", "Lakebase acceptance is not explicitly unrun")
    require(receipt.get("inputBasis") == helper._managed_input_basis(source_root), "Managed input basis differs from source")
    owner = receipt.get("ownerOracle")
    require(
        type(owner) is dict
        and owner.get("sourceCommit") == OWNER_ORACLE_COMMIT
        and owner.get("sourceClean") is True
        and owner.get("inputsUnchanged") is True
        and owner.get("Bun") == OWNER_ORACLE_BUN,
        "Independent owner-oracle receipt mismatch",
    )
    gate_tree = ast.parse(
        (source_root / "scripts/qualify-managed-platform-grants.py").read_bytes()
    )
    gate_constants = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in gate_tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {"MODULES", "UMF_OWNER_REVISION"}
    }
    require(
        set(gate_constants) == {"MODULES", "UMF_OWNER_REVISION"}
        and owner.get("sourceCommit") == gate_constants["UMF_OWNER_REVISION"],
        "Managed source oracle pins mismatch",
    )
    outcomes = _managed_outcomes(managed_dir, receipt, gate_constants, helper)
    comparison = _validate_comparison(source_root, package_assets, managed_dir, receipt, helper)
    require(
        {path.name for path in managed_dir.glob("installer-comparison/*") if path.is_file()}
        == {"binding.json", "report.json"},
        "Comparison artifact inventory mismatch",
    )
    require(
        {path.name for path in managed_dir.iterdir() if path.is_dir()}
        == {"installer-comparison"},
        "Managed artifact directory inventory mismatch",
    )
    require(
        {path.name for path in managed_dir.iterdir() if path.is_file()}
        == {"qualification.json", *[entry["name"] for entry in outcomes["logs"]]},
        "Managed artifact root inventory mismatch",
    )
    all_managed_paths = list(managed_dir.rglob("*"))
    require(
        all(not path.is_symlink() for path in all_managed_paths),
        "Managed artifact contains a symlink",
    )
    expected_managed_files = {
        "qualification.json",
        "installer-comparison/binding.json",
        "installer-comparison/report.json",
        *[entry["name"] for entry in outcomes["logs"]],
    }
    require(
        {
            path.relative_to(managed_dir).as_posix()
            for path in all_managed_paths
            if path.is_file()
        }
        == expected_managed_files,
        "Managed artifact recursive file inventory mismatch",
    )
    after = _source_identity(source_root)
    require(before == after, "Source changed during artifact verification")
    package_files = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256(path.read_bytes())}
        for path in sorted(package_assets.iterdir())
    }
    managed_files = {
        path.relative_to(managed_dir).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": sha256(path.read_bytes()),
        }
        for path in sorted(managed_dir.rglob("*"))
        if path.is_file()
    }
    return {
        "schema": "truss-ci-managed-comparison-artifact-verification/1",
        "status": "passed",
        "scope": "Linux CI installed-candidate managed tests and public49-installed versus source50 installer comparison; artifact evidence only",
        "source": {**before, "version": VERSION},
        "apiArtifacts": {"package": package_api, "managed": managed_api},
        "sourceBindings": {
            "publicVerifierSha256": HELPER_SHA256,
            "packageVerifierSha256": PACKAGE_VERIFIER_SHA256,
            "installerDriverSha256": DRIVER_SHA256,
            "expectedPackageFiles": 469,
        },
        "packageArtifact": {"files": package_files, "verification": package_report},
        "managedQualification": {
            "platform": receipt["platform"],
            "tests": outcomes["tests"],
            "modules": outcomes["moduleCount"],
            "sourcePayloadFiles": receipt["packageFilesVerified"],
            "inputBasisEntries": len(receipt["inputBasis"]),
            "inputBasisSha256": sha256(json.dumps(receipt["inputBasis"], sort_keys=True, separators=(",", ":")).encode()),
            "workerStopped": receipt["workerStopped"],
            "workerBaselineRestored": receipt["workerBaselineRestored"],
            "inputsUnchanged": receipt["inputsUnchanged"],
            "payloadUnchanged": receipt["payloadUnchanged"],
            "lakebaseAcceptance": "not_run",
            "ownerOracle": owner,
            "outcomeLogs": outcomes["logs"],
        },
        "installerComparison": comparison,
        "managedArtifactFiles": managed_files,
        "claims": {
            "publicRelease": False,
            "tagGate": False,
            "fullInstalled50Qualification": False,
            "installedPublic49VersusSource50Comparison": True,
            "arrasQualification": False,
            "wanQualification": False,
            "generalWallSpeedup": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--package-assets", type=Path, required=True)
    parser.add_argument("--managed-artifact", type=Path, required=True)
    parser.add_argument("--package-api", type=Path, required=True)
    parser.add_argument("--managed-api", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite validation output")
    report = verify(
        args.source_root,
        args.package_assets,
        args.managed_artifact,
        args.package_api,
        args.managed_api,
    )
    encoded = (json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(encoded)
    print(
        json.dumps(
            {
                "status": report["status"],
                "source": report["source"],
                "managedTests": report["managedQualification"]["tests"],
                "managedModules": report["managedQualification"]["modules"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
