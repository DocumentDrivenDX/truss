#!/usr/bin/env python3
"""Verify the 0.0.50 CI package artifact against its exact clean source tree.

This is a local package-artifact check. It does not verify an installed package,
run native tests, qualify Lakebase, or claim the full release gate passed.
"""

from __future__ import annotations

import argparse
import email
import email.policy
import hashlib
import importlib.util
import json
import re
import subprocess
import tarfile
import tomllib
import zipfile
from pathlib import Path

VERSION = "0.0.50"
SOURCE_COMMIT = "0b61b5107ba453e4b18291203e307b67ac7da9f8"
ARTIFACT_ID = 12549011611
WORKFLOW_RUN_ID = 40062344218
API_ARTIFACT_DIGEST = (
    "sha256:1ec3d3cd383e72fda79736974347abbc69e3f589a2aeb02ba251932b420c9a0b"
)
HELPER_SHA256 = "f0f313ad9058076a9f5cc0d479fa2cb50bdc4002669308f7033a26ebf0235e08"
EXPECTED_ASSETS = {
    "truss_toolkit-0.0.50-py3-none-any.whl",
    "truss_toolkit-0.0.50.tar.gz",
    "truss-hf-conformance-0.0.50.zip",
    "isolated-runtime-constraints.txt",
}


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


def _read_json(path: Path) -> object:
    return json.loads(
        path.read_bytes(),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _source_identity(root: Path) -> dict[str, str]:
    head = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain", "--untracked-files=all")
    require(head == SOURCE_COMMIT, "Source HEAD differs from the expected 0b61 commit")
    require(not status, "Source checkout is not clean")
    return {"commit": head, "status": "clean"}


def _api_artifact(api_value: object) -> dict[str, object]:
    require(type(api_value) is dict, "Release API response must be an object")
    rows: object
    if "artifacts" in api_value:
        rows = api_value["artifacts"]
    else:
        rows = [api_value]
    require(type(rows) is list, "Release API artifact list is malformed")
    selected = [
        row
        for row in rows
        if type(row) is dict and row.get("id") == ARTIFACT_ID
    ]
    require(len(selected) == 1, "Expected exactly one matching GitHub artifact")
    artifact = selected[0]
    require(artifact.get("name") == "python-package", "Artifact name mismatch")
    require(artifact.get("expired") is False, "GitHub artifact is expired")
    require(artifact.get("digest") == API_ARTIFACT_DIGEST, "API digest mismatch")
    run = artifact.get("workflow_run")
    require(type(run) is dict, "Artifact workflow run metadata is missing")
    require(run.get("id") == WORKFLOW_RUN_ID, "Artifact workflow run mismatch")
    require(
        run.get("head_sha") == SOURCE_COMMIT,
        "Artifact workflow source revision mismatch",
    )
    size = artifact.get("size_in_bytes")
    require(type(size) is int and size > 0, "Artifact size is invalid")
    return {
        "id": ARTIFACT_ID,
        "name": "python-package",
        "workflowRunId": WORKFLOW_RUN_ID,
        "workflowHeadSha": SOURCE_COMMIT,
        "apiReportedZipDigest": API_ARTIFACT_DIGEST,
        "digestKind": "GitHub API-reported artifact ZIP digest; not independently recomputed",
        "sizeInBytes": size,
    }


def _load_helper(path: Path) -> object:
    raw = path.read_bytes()
    require(sha256(raw) == HELPER_SHA256, "Reviewed artifact helper SHA-256 mismatch")
    spec = importlib.util.spec_from_file_location("verify_public50_artifacts", path)
    require(spec is not None and spec.loader is not None, "Cannot load reviewed helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expected_requires_dist(project: dict[str, object]) -> set[str]:
    dependencies = project.get("dependencies")
    optional = project.get("optional-dependencies")
    require(type(dependencies) is list, "Project base dependencies are malformed")
    require(type(optional) is dict, "Project optional dependencies are malformed")
    expected: set[str] = set()
    for dependency in dependencies:
        require(type(dependency) is str, "Project dependency is not a string")
        expected.add(dependency)
    for extra, values in optional.items():
        require(type(extra) is str and re.fullmatch(r"[A-Za-z0-9._-]+", extra), "Invalid extra name")
        require(type(values) is list, "Project extra dependencies are malformed")
        for dependency in values:
            require(type(dependency) is str, "Extra dependency is not a string")
            expected.add(f'{dependency}; extra == "{extra}"')
    return expected


def _verify_wheel_metadata(wheel_path: Path, project: dict[str, object]) -> dict[str, object]:
    require("readme" not in project, "Project unexpectedly declares readme metadata")
    expected_requires = _expected_requires_dist(project)
    with zipfile.ZipFile(wheel_path) as archive:
        metadata_names = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/METADATA") and not name.endswith("/")
        ]
        require(len(metadata_names) == 1, "Wheel must contain one METADATA file")
        raw = archive.read(metadata_names[0])
    message = email.message_from_bytes(raw, policy=email.policy.default)
    require(message.get("Name") == project.get("name"), "Wheel project name mismatch")
    require(message.get("Version") == VERSION, "Wheel version mismatch")
    require(message.get("Requires-Python") == project.get("requires-python"), "Python requirement mismatch")
    actual_requires = message.get_all("Requires-Dist", [])
    require(
        len(actual_requires) == len(expected_requires)
        and set(actual_requires) == expected_requires,
        "Wheel dependencies differ from pyproject",
    )
    if b"\r\n\r\n" in raw:
        headers, separator, body = raw.partition(b"\r\n\r\n")
        require(bool(separator), "Wheel METADATA separator is malformed")
        require(body == b"", "Wheel METADATA body is not empty as expected")
    elif b"\n\n" in raw:
        headers, separator, body = raw.partition(b"\n\n")
        require(bool(separator), "Wheel METADATA separator is malformed")
        require(body == b"", "Wheel METADATA body is not empty as expected")
    else:
        require(
            raw.endswith(b"\n"),
            "Header-only wheel METADATA has an invalid ending",
        )
        headers = raw
        body = b""
    require(
        not message.is_multipart() and message.get_payload() == "",
        "Parsed wheel METADATA payload is not empty",
    )
    return {
        "metadataPath": metadata_names[0],
        "name": message.get("Name"),
        "version": message.get("Version"),
        "requiresPython": message.get("Requires-Python"),
        "requiresDist": sorted(message.get_all("Requires-Dist", [])),
        "readmeDeclared": False,
        "metadataBodyBytes": len(body),
        "metadataHeadersSha256": sha256(headers),
    }


def _verify_sdist_readme(sdist_path: Path, source_readme: Path) -> dict[str, object]:
    expected = source_readme.read_bytes()
    with tarfile.open(sdist_path, "r:gz") as archive:
        matches = [member for member in archive.getmembers() if member.name.endswith("/README.md") and member.name.count("/") == 1]
        require(len(matches) == 1, "Sdist must contain exactly one root README.md")
        member = matches[0]
        require(member.isfile(), "Sdist root README.md must be a regular file")
        stream = archive.extractfile(member)
        require(stream is not None, "Sdist root README.md is unreadable")
        actual = stream.read()
    require(actual == expected, "Sdist README differs from source README")
    return {"member": member.name, "bytes": len(actual), "sha256": sha256(actual), "matchesSource": True}


def verify(source_root: Path, assets_dir: Path, release_api_path: Path, tag_commit: str) -> dict[str, object]:
    require(tag_commit == SOURCE_COMMIT, "Expected source commit is not the reviewed 0b61 commit")
    before = _source_identity(source_root)
    api_record = _api_artifact(_read_json(release_api_path))
    actual_names = {path.name for path in assets_dir.iterdir() if path.is_file()}
    require(actual_names == EXPECTED_ASSETS, "Downloaded package asset inventory mismatch")
    require(
        all(path.is_file() and not path.is_symlink() for path in assets_dir.iterdir()),
        "Package asset directory contains a symlink or non-file entry",
    )

    helper_path = Path(__file__).with_name("verify-public50-artifacts.py")
    helper = _load_helper(helper_path)
    project_path = source_root / "packages/python/pyproject.toml"
    project = tomllib.loads(project_path.read_text(encoding="utf-8"))["project"]
    require(project.get("version") == VERSION, "Source package version mismatch")
    require(project.get("name") == "truss-toolkit", "Source package name mismatch")

    wheel = assets_dir / "truss_toolkit-0.0.50-py3-none-any.whl"
    sdist = assets_dir / "truss_toolkit-0.0.50.tar.gz"
    hf_archive = assets_dir / "truss-hf-conformance-0.0.50.zip"
    constraints = assets_dir / "isolated-runtime-constraints.txt"
    payload = helper._source_payload(source_root)
    wheel_record = helper._verify_wheel_record(source_root, wheel)
    wheel_payload = helper._verify_wheel_payload(wheel, payload)
    sdist_payload = helper._verify_sdist_payload(sdist, payload)
    hf = helper._verify_hf_archive(source_root, hf_archive)
    constraints_source = source_root / "packages/python/isolated-runtime-constraints.txt"
    require(constraints.read_bytes() == constraints_source.read_bytes(), "Runtime constraints differ from source")

    package_metadata = _verify_wheel_metadata(wheel, project)
    readme = _verify_sdist_readme(sdist, source_root / "packages/python/README.md")
    after = _source_identity(source_root)
    require(before == after, "Source checkout changed during verification")

    asset_records = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256(path.read_bytes())}
        for path in sorted(assets_dir.iterdir())
        if path.is_file()
    }
    return {
        "schema": "truss-ci-package-artifact-verification/1",
        "status": "passed",
        "scope": "Downloaded CI package artifact bytes checked against clean source; not a release or runtime qualification",
        "source": {**before, "expectedCommit": SOURCE_COMMIT, "packageVersion": VERSION},
        "workflowArtifact": api_record,
        "reviewedHelper": {"path": str(helper_path), "sha256": HELPER_SHA256},
        "sourcePayload": {"files": len(payload), "sha256ByMember": {name: sha256(data) for name, data in sorted(payload.items())}},
        "wheel": {**asset_records[wheel.name], "record": wheel_record, "payload": wheel_payload, "metadata": package_metadata},
        "sdist": {**asset_records[sdist.name], "payload": sdist_payload, "readme": readme},
        "hfArchive": {**asset_records[hf_archive.name], **hf},
        "runtimeConstraints": {
            **asset_records[constraints.name],
            "matchesSource": True,
            "sourceSha256": sha256(constraints_source.read_bytes()),
        },
        "claims": {
            "sourcePayloadFiles": len(payload),
            "installedPackage": False,
            "nativeQualification": False,
            "fullReleaseGate": False,
            "publicRelease": False,
            "arrasQualification": False,
            "wanQualification": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--release-api", type=Path, required=True)
    parser.add_argument("--tag-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite verification output")
    report = verify(args.source_root.resolve(), args.assets.resolve(), args.release_api.resolve(), args.tag_commit)
    encoded = (json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(encoded)
    print(
        json.dumps(
            {
                "status": report["status"],
                "source": report["source"],
                "assetCount": len(EXPECTED_ASSETS),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
