#!/usr/bin/env python3
"""Verify downloaded Truss 0.0.50 release assets against a clean source tag.

This verifies release metadata, bytes, package payloads, and public qualification
receipts. It does not run native tests, contact Lakebase, or qualify a service.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tarfile
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

VERSION = "0.0.50"
TAG = "v0.0.50"
NATIVE_MANIFEST_SHA256 = (
    "288801f7177338328441b5d3ce9328af31740ebf513f04ea45e30ae316a9f3a4"
)
SOURCE49 = {
    "filename": "truss_toolkit-0.0.49-py3-none-any.whl",
    "runtimeManifestSha256": NATIVE_MANIFEST_SHA256,
    "sha256": "7ea14b2787f02cbeec9ad99d835adbcc30c684fd5be8e0765a1d8198b50e7182",
    "tag": "v0.0.49",
}
SOURCE49_MIGRATION_MANIFEST_SHA256 = (
    "96addcdb95523f478d8f50b0b47198e47a860680c7400dd359711930e837e535"
)
EXPECTED_ASSETS = {
    "truss_toolkit-0.0.50-py3-none-any.whl",
    "truss_toolkit-0.0.50.tar.gz",
    "truss-hf-conformance-0.0.50.zip",
    "isolated-runtime-constraints.txt",
    "migration-qualification.json",
    "hf-conformance-qualification.json",
    "managed-grants-qualification.json",
    "catalog-registration-summary-v0.1.md",
    "catalog-rebind-report-v0.2.md",
    "catalog-rebind-report-v0.4.md",
    "catalog-source-reference-v0.1.md",
    "migration-qualification-evidence.tar.gz",
    "managed-grants-qualification-evidence.tar.gz",
    "logical-query-abi.json",
    "catalog-key-backfill-report-v0.1.md",
    "release-pins.json",
    "SHA256SUMS",
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_ARCHIVE_MEMBER = 128 * 1024 * 1024
MAX_ARCHIVE_TOTAL = 1024 * 1024 * 1024
INSTALLER_COMPARISON_SCOPE = (
    "One-time 0.0.50 release gate; exact public49 installed package versus source "
    "candidate on one script-owned fresh PostgreSQL18.6 worker. Client "
    "submissions/process CPU only; no server or wire timing."
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _integer_is(value: object, expected: int) -> bool:
    return type(value) is int and value == expected


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(
        path.read_bytes(),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_json_constant,
    )
    if type(value) is not dict:
        raise ValueError("Expected JSON object")
    return value


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"Non-finite JSON number: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def _safe_relative(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and not path.is_absolute()
        and path.as_posix() == name
        and "\\" not in name
        and "\x00" not in name
        and all(part not in ("", ".", "..") for part in path.parts)
    )


def _git_value(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _source_state(root: Path, tag_commit: str) -> dict[str, str]:
    require(
        HEX64.fullmatch(tag_commit) is not None
        or re.fullmatch(r"[0-9a-f]{40}", tag_commit) is not None,
        "Tag commit must be a lowercase full Git object ID",
    )
    head = _git_value(root, "rev-parse", "HEAD")
    status = _git_value(root, "status", "--porcelain", "--untracked-files=all")
    require(
        head == tag_commit, "Source checkout HEAD does not match supplied tag commit"
    )
    require(not status, "Source checkout is not clean")
    return {"head": head, "status": "clean"}


def _sha256sums(path: Path, expected_files: set[str]) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9._+-]+)", line)
        require(match is not None, "Malformed SHA256SUMS row")
        digest, name = match.groups()
        require(name not in entries, "Duplicate SHA256SUMS filename")
        entries[name] = digest
    require(
        set(entries) == expected_files - {"SHA256SUMS"}, "SHA256SUMS inventory mismatch"
    )
    return entries


def _dist_metadata(raw: bytes) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in raw.decode("utf-8").splitlines():
        if not line or line[0].isspace() or ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key in ("Name", "Version"):
            require(key not in fields, "Duplicate distribution metadata field")
            fields[key] = value
    require(
        fields == {"Name": "truss-toolkit", "Version": VERSION},
        "Distribution metadata mismatch",
    )
    return fields


def _verify_wheel_record(root: Path, wheel_path: Path) -> dict[str, object]:
    helper_path = root / "scripts/verify-weft-release-wheel.py"
    spec = importlib.util.spec_from_file_location(
        "release_wheel_record_helper", helper_path
    )
    require(
        spec is not None and spec.loader is not None,
        "Wheel RECORD verifier is unavailable",
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    with zipfile.ZipFile(wheel_path) as archive:
        infos = archive.infolist()
        record_name = helper._verify_record(archive, infos)
        metadata_names = [
            info.filename
            for info in infos
            if info.filename.endswith(".dist-info/METADATA") and not info.is_dir()
        ]
        require(len(metadata_names) == 1, "Wheel must contain exactly one METADATA")
        _dist_metadata(archive.read(metadata_names[0]))
        return {
            "record": record_name,
            "payloadMemberCount": sum(not info.is_dir() for info in infos),
            "metadata": metadata_names[0],
        }


def _source_payload(source_root: Path) -> dict[str, bytes]:
    package = source_root / "packages/python/src/truss"
    require(package.is_dir(), "Source Truss package directory is missing")
    result: dict[str, bytes] = {}
    for path in package.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlink in source package payload")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result[path.relative_to(package).as_posix()] = path.read_bytes()
    require(len(result) == 469, "Expected exact 469-file Truss source payload")
    return result


def _verify_wheel_payload(path: Path, payload: dict[str, bytes]) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        package_names = [
            name.removeprefix("truss/")
            for name in names
            if name.startswith("truss/") and not name.endswith("/")
        ]
        require(
            len(package_names) == len(set(package_names)),
            "Duplicate wheel package member",
        )
        require(
            set(package_names) == set(payload),
            "Wheel and source payload inventories differ",
        )
        for name, expected in payload.items():
            require(
                archive.read("truss/" + name) == expected,
                "Wheel payload differs from source",
            )
    return {"payloadFiles": len(payload), "payloadEqual": True}


def _verify_sdist_payload(path: Path, payload: dict[str, bytes]) -> dict[str, object]:
    prefix = f"truss_toolkit-{VERSION}/"
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        seen: set[str] = set()
        for member in members:
            require(_safe_relative(member.name), "Unsafe source distribution path")
            require(member.name not in seen, "Duplicate source distribution member")
            seen.add(member.name)
            require(
                member.isfile() or member.isdir(),
                "Unsupported source distribution member type",
            )
            require(
                member.size <= MAX_ARCHIVE_MEMBER,
                "Oversized source distribution member",
            )
        metadata = [member for member in members if member.name == prefix + "PKG-INFO"]
        require(len(metadata) == 1, "Source distribution PKG-INFO missing")
        stream = archive.extractfile(metadata[0])
        require(stream is not None, "Source distribution metadata unreadable")
        _dist_metadata(stream.read())
        package_members = {
            member.name.removeprefix(prefix + "src/truss/"): member
            for member in members
            if member.isfile() and member.name.startswith(prefix + "src/truss/")
        }
        require(
            set(package_members) == set(payload),
            "Sdist and source payload inventories differ",
        )
        for name, member in package_members.items():
            stream = archive.extractfile(member)
            require(
                stream is not None and stream.read() == payload[name],
                "Sdist payload differs from source",
            )
    return {"payloadFiles": len(payload), "payloadEqual": True}


def _verify_hf_archive(source_root: Path, archive_path: Path) -> dict[str, object]:
    corpus_path = source_root / "docs/helix/03-test/fixtures/hohfeld-followup-0.1.json"
    corpus = read_json(corpus_path)
    profile = corpus.get("profile")
    require(type(profile) is str, "HF conformance profile missing")
    producers = corpus.get("producers")
    require(type(producers) is dict, "HF producer inventory missing")
    producer_paths = list(producers)
    require(
        all(type(name) is str and _safe_relative(name) for name in producer_paths),
        "Unsafe HF producer path",
    )
    paths = [source_root / name for name in producer_paths]
    paths.extend([corpus_path, source_root / "scripts/run-hf-conformance.py"])
    fixture_root = source_root / "packages/python/tests/fixtures"
    paths.extend(
        path
        for path in fixture_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    paths.extend(
        source_root / "packages/python" / name
        for name in ("LICENSE.md", "LICENSE-MIT", "LICENSE-APACHE")
    )
    expected_files = {
        path.relative_to(source_root).as_posix(): sha256(path.read_bytes())
        for path in sorted(set(paths))
    }
    require(
        all((source_root / name).is_file() for name in expected_files),
        "HF producer source missing",
    )
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        require(len(names) == len(set(names)), "Duplicate HF archive member")
        require(all(_safe_relative(name) for name in names), "Unsafe HF archive member")
        require(archive.testzip() is None, "HF archive CRC check failed")
        total_size = 0
        for info in infos:
            require(info.file_size <= MAX_ARCHIVE_MEMBER, "Oversized HF archive member")
            total_size += info.file_size
        require(
            total_size <= MAX_ARCHIVE_TOTAL, "HF archive expanded size exceeds bound"
        )
        require(
            set(names)
            == set(expected_files) | {"conformance-manifest.json", "README.md"},
            "HF archive member inventory mismatch",
        )
        manifest = json.loads(
            archive.read("conformance-manifest.json"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
        require(type(manifest) is dict, "HF conformance manifest is malformed")
        require(
            set(manifest)
            == {
                "profile",
                "toolkitVersion",
                "nativeManifestSha256",
                "compilerVersion",
                "files",
                "scope",
            },
            "HF conformance manifest fields are not closed",
        )
        require(
            manifest.get("files") == expected_files,
            "HF manifest does not pin exact source members",
        )
        for name, digest in expected_files.items():
            require(
                sha256(archive.read(name)) == digest,
                "HF archived source member hash mismatch",
            )
        require(
            manifest.get("profile") == profile,
            "HF manifest profile differs from corpus",
        )
        require(
            manifest.get("toolkitVersion") == VERSION,
            "HF manifest toolkit version mismatch",
        )
        require(
            manifest.get("nativeManifestSha256") == NATIVE_MANIFEST_SHA256,
            "HF manifest native pin mismatch",
        )
        require(
            manifest.get("compilerVersion") == corpus.get("compilerVersion"),
            "HF compiler pin mismatch",
        )
    return {
        "profile": profile,
        "corpusSha256": sha256(corpus_path.read_bytes()),
        "memberCount": len(expected_files),
        "archiveSha256": sha256(archive_path.read_bytes()),
        "manifest": manifest,
    }


def _cohort_for_hf(
    source_root: Path, hf_receipt: dict[str, object]
) -> dict[str, object]:
    corpus = read_json(
        source_root / "docs/helix/03-test/fixtures/hohfeld-followup-0.1.json"
    )
    module_sha = hf_receipt.get("compilerNativeModuleSha256")
    revision = hf_receipt.get("compilerSourceRevision")
    cohorts = corpus.get("compilerCohorts")
    require(type(cohorts) is list, "HF compiler cohort inventory missing")
    matches = [
        cohort
        for cohort in cohorts
        if type(cohort) is dict
        and cohort.get("nativeModuleSha256") == module_sha
        and cohort.get("sourceRevision") == revision
        and cohort.get("platform") == "linux-x86_64"
    ]
    require(len(matches) == 1, "HF receipt does not select one Linux compiler cohort")
    return matches[0]


def _verify_hf_receipt(
    source_root: Path,
    receipt: dict[str, object],
    hf_archive: dict[str, object],
    tag_commit: str,
    pins: dict[str, object],
) -> dict[str, object]:
    corpus = read_json(
        source_root / "docs/helix/03-test/fixtures/hohfeld-followup-0.1.json"
    )
    require(
        receipt.get("sourceCommit") == tag_commit, "HF receipt source commit mismatch"
    )
    require(receipt.get("passed") is True, "HF public qualification did not pass")
    require(
        type(receipt.get("platform")) is str
        and receipt["platform"].lower().startswith("linux"),
        "HF receipt platform mismatch",
    )
    require(
        _integer_is(receipt.get("tests"), len(corpus.get("cases", []))),
        "HF test count mismatch",
    )
    require(
        _integer_is(receipt.get("skipped"), 0)
        and _integer_is(receipt.get("failures"), 0)
        and _integer_is(receipt.get("errors"), 0),
        "HF receipt contains skips or failures",
    )
    require(
        receipt.get("profile") == hf_archive.get("profile"),
        "HF receipt profile mismatch",
    )
    require(
        receipt.get("corpusSha256") == hf_archive.get("corpusSha256"),
        "HF corpus hash mismatch",
    )
    require(receipt.get("toolkit") == VERSION, "HF receipt Truss version mismatch")
    require(
        receipt.get("compiler") == corpus.get("compilerVersion"),
        "HF compiler version mismatch",
    )
    require(
        receipt.get("nativeManifestSha256") == NATIVE_MANIFEST_SHA256,
        "HF receipt native runtime mismatch",
    )
    cohort = _cohort_for_hf(source_root, receipt)
    require(
        pins.get("hfConformanceProfile") == receipt.get("profile"),
        "Release pin HF profile mismatch",
    )
    require(
        pins.get("hfConformanceCorpusSha256") == receipt.get("corpusSha256"),
        "Release pin HF corpus mismatch",
    )
    require(
        pins.get("hfConformanceTests") == receipt.get("tests"),
        "Release pin HF test count mismatch",
    )
    require(
        pins.get("weftSourceRevision") == cohort.get("sourceRevision"),
        "Release pin compiler source mismatch",
    )
    require(
        pins.get("weftNativeModuleSha256") == cohort.get("nativeModuleSha256"),
        "Release pin compiler module mismatch",
    )
    require(
        pins.get("weftWheelSha256") == cohort.get("wheelSha256"),
        "Release pin compiler wheel mismatch",
    )
    return {"tests": receipt["tests"], "cohort": cohort}


def _verify_tar(path: Path, *, required_members: set[str]) -> dict[str, object]:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names: list[str] = []
        total = 0
        for member in members:
            require(_safe_relative(member.name), "Unsafe evidence archive path")
            require(
                member.isfile() or member.isdir(), "Unsupported evidence archive member"
            )
            require(member.name not in names, "Duplicate evidence archive member")
            names.append(member.name)
            if member.isfile():
                require(
                    member.size <= MAX_ARCHIVE_MEMBER,
                    "Oversized evidence archive member",
                )
                total += member.size
        require(
            total <= MAX_ARCHIVE_TOTAL, "Evidence archive expanded size exceeds bound"
        )
        require(
            required_members <= set(names),
            "Required evidence file is absent from archive",
        )
    return {
        "memberCount": len(names),
        "expandedBytes": total,
        "archiveSha256": sha256(path.read_bytes()),
    }


def _read_tar_member(path: Path, name: str) -> bytes:
    with tarfile.open(path, "r:gz") as archive:
        member = archive.getmember(name)
        require(member.isfile(), "Required evidence member is not a regular file")
        stream = archive.extractfile(member)
        require(stream is not None, "Required evidence member is unreadable")
        return stream.read()


def _validate_migration_receipt(
    receipt: dict[str, object],
    manifest: dict[str, object],
    migration_sha: str,
    tag_commit: str,
) -> None:
    for key in ("tests", "failures", "errors", "skipped"):
        value = receipt.get(key)
        require(
            type(value) is int and value >= 0, "Migration receipt counter is invalid"
        )
    require(receipt.get("tests") == 107, "Migration receipt must contain all 107 tests")
    require(
        receipt.get("passed") is True
        and receipt.get("failures") == 0
        and receipt.get("errors") == 0
        and receipt.get("skipped") == 0,
        "Migration qualification did not pass cleanly",
    )
    require(
        receipt.get("sourceCommit") == tag_commit,
        "Migration receipt source commit mismatch",
    )
    require(receipt.get("platform") == "linux", "Migration receipt platform mismatch")
    require(
        receipt.get("package") == VERSION, "Migration receipt package version mismatch"
    )
    require(
        receipt.get("recipeSha256") == migration_sha,
        "Migration receipt index hash mismatch",
    )
    target = manifest.get("target")
    require(
        receipt.get("targetManifestSha256") == target,
        "Migration receipt target manifest mismatch",
    )
    sources = manifest.get("sources")
    require(
        type(sources) is list and all(type(value) is str for value in sources),
        "Migration source cohort is malformed",
    )
    expected_sources = sorted(set([*sources, target]))
    require(
        receipt.get("sources") == expected_sources,
        "Migration receipt source matrix is incomplete or unexpected",
    )
    source_wheels = manifest.get("sourceWheels")
    original_wheels = receipt.get("originalWheels")
    require(
        type(source_wheels) is dict and type(original_wheels) is dict,
        "Migration source wheel inventory is missing",
    )
    require(
        all(type(entry) is dict for entry in source_wheels.values()),
        "Migration source wheel row is malformed",
    )
    expected_originals = {
        label: {"filename": entry["filename"], "sha256": entry["sha256"]}
        for label, entry in source_wheels.items()
    }
    require(
        len(expected_originals) == len(source_wheels),
        "Migration source wheel row is malformed",
    )
    require(
        all(
            type(row) is dict and set(row) == {"filename", "sha256"}
            for row in original_wheels.values()
        ),
        "Migration receipt wheel row is malformed",
    )
    require(
        original_wheels == expected_originals,
        "Migration receipt wheel inventory differs from manifest",
    )


PUBLISHER_SIDECARS = dict(
    [
        (
            "isolated-runtime-constraints.txt",
            "packages/python/isolated-runtime-constraints.txt",
        ),
        (
            "catalog-registration-summary-v0.1.md",
            "docs/helix/02-design/contracts/catalog-registration-summary-v0.1.md",
        ),
        (
            "catalog-rebind-report-v0.2.md",
            "docs/helix/02-design/contracts/catalog-rebind-report-v0.2.md",
        ),
        (
            "catalog-rebind-report-v0.4.md",
            "docs/helix/02-design/contracts/catalog-rebind-report-v0.4.md",
        ),
        (
            "catalog-source-reference-v0.1.md",
            "docs/helix/02-design/contracts/catalog-source-reference-v0.1.md",
        ),
        (
            "catalog-key-backfill-report-v0.1.md",
            "docs/helix/02-design/contracts/catalog-key-backfill-report-v0.1.md",
        ),
        (
            "logical-query-abi.json",
            "packages/python/src/truss/_catalog_runtime/query-abi.json",
        ),
    ]
)


def _verify_publisher_sidecars(source_root: Path, assets_dir: Path) -> dict[str, str]:
    verified: dict[str, str] = {}
    for asset_name, source_name in PUBLISHER_SIDECARS.items():
        source_path = source_root / source_name
        asset_path = assets_dir / asset_name
        require(
            source_path.is_file() and not source_path.is_symlink(),
            "Publisher sidecar source is missing or unsafe",
        )
        source_bytes = source_path.read_bytes()
        asset_bytes = asset_path.read_bytes()
        require(
            asset_bytes == source_bytes,
            "Published sidecar differs from exact source derivation",
        )
        verified[asset_name] = sha256(source_bytes)
    return verified


def _validate_managed_test_total(receipt: dict[str, object]) -> None:
    outcomes = receipt.get("outcomes")
    require(
        type(outcomes) is list and all(type(row) is dict for row in outcomes),
        "Managed gate outcomes are malformed",
    )
    counts = [row.get("tests") for row in outcomes]
    require(
        all(type(count) is int and count >= 0 for count in counts),
        "Managed gate test count is invalid",
    )
    total = receipt.get("tests")
    require(
        type(total) is int and total == sum(counts),
        "Managed receipt total does not equal outcome test counts",
    )


MANAGED_INPUT_FILES = (
    "tests/fixtures/layout-migration-planning.json",
    "tests/fixtures/operation-ordinal-issuer.json",
    "docs/helix/03-test/acceptance-outer-json-expected.proposal.json",
    "docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json",
    "docs/helix/02-design/contracts/bindings/bootstrap-permit-arithmetic-v0.1.proposal.json",
    "docs/helix/03-test/python-exact-value-vectors.proposal.json",
    "docs/helix/04-build/evidence/receipt-position-locator-vectors.json",
    "docs/helix/02-design/contracts/row-operation-registry-observation-v0.1.proposal.sql",
)


def _managed_input_basis(source_root: Path) -> dict[str, str]:
    inputs: set[Path] = set()
    for directory in (
        "packages/python/tests",
        "packages/python/examples",
        "packages/browser/fixtures",
        "tests/fixtures",
        "scripts",
    ):
        inputs.update(
            path
            for path in (source_root / directory).rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        )
    inputs.update(source_root / name for name in MANAGED_INPUT_FILES)
    return {
        path.relative_to(source_root).as_posix(): sha256(path.read_bytes())
        for path in sorted(inputs)
    }


def _verify_release_metadata(
    release: dict[str, object], assets_dir: Path, tag_commit: str
) -> dict[str, object]:
    require(release.get("tag_name") == TAG, "GitHub release tag mismatch")
    require(
        release.get("draft") is False and release.get("prerelease") is False,
        "Release is draft or prerelease",
    )
    html_url = release.get("html_url")
    require(
        type(html_url) is str and html_url.endswith("/releases/tag/" + TAG),
        "Release URL does not identify expected tag",
    )
    rows = release.get("assets")
    require(
        type(rows) is list and len(rows) == len(EXPECTED_ASSETS),
        "GitHub release asset count mismatch",
    )
    api_assets: dict[str, dict[str, object]] = {}
    for row in rows:
        require(type(row) is dict, "Malformed GitHub release asset row")
        name = row.get("name")
        require(
            type(name) is str and name not in api_assets,
            "Duplicate or malformed GitHub asset name",
        )
        api_assets[name] = row
    require(
        set(api_assets) == EXPECTED_ASSETS,
        "GitHub release asset names differ from required17",
    )
    disk_entries = list(assets_dir.iterdir())
    require(
        all(entry.is_file() and not entry.is_symlink() for entry in disk_entries),
        "Assets directory contains non-file or symlink",
    )
    require(
        {entry.name for entry in disk_entries} == EXPECTED_ASSETS,
        "Downloaded asset directory inventory mismatch",
    )
    checks: dict[str, dict[str, object]] = {}
    for name, row in api_assets.items():
        path = assets_dir / name
        raw = path.read_bytes()
        digest = sha256(raw)
        api_digest = row.get("digest")
        require(
            type(api_digest) is str and api_digest == "sha256:" + digest,
            "GitHub asset SHA-256 mismatch",
        )
        require(
            type(row.get("size")) is int and row["size"] == len(raw),
            "GitHub asset size mismatch",
        )
        checks[name] = {"size": len(raw), "sha256": digest}
    sums = _sha256sums(assets_dir / "SHA256SUMS", EXPECTED_ASSETS)
    for name, digest in sums.items():
        require(checks[name]["sha256"] == digest, "SHA256SUMS digest mismatch")
    return {"releaseUrl": html_url, "tagCommitInput": tag_commit, "assets": checks}


def verify(args: argparse.Namespace) -> dict[str, object]:
    source_root = args.source_root.resolve(strict=True)
    assets_dir = args.assets.resolve(strict=True)
    release = read_json(args.release_api)
    source = _source_state(source_root, args.tag_commit)
    release_facts = _verify_release_metadata(release, assets_dir, args.tag_commit)
    sidecars = _verify_publisher_sidecars(source_root, assets_dir)

    project = tomllib.loads(
        (source_root / "packages/python/pyproject.toml").read_text()
    )
    project_info = project["project"]
    require(
        project_info["name"] == "truss-toolkit" and project_info["version"] == VERSION,
        "Source project metadata is not 0.0.50",
    )
    query_requirements = project_info["optional-dependencies"]["query"]
    require(
        type(query_requirements) is list
        and len(query_requirements) == 1
        and type(query_requirements[0]) is str
        and query_requirements[0].startswith("weft-sql=="),
        "Source compiler dependency is not exactly pinned",
    )
    compiler_version = query_requirements[0].removeprefix("weft-sql==")
    source_payload = _source_payload(source_root)
    wheel = assets_dir / "truss_toolkit-0.0.50-py3-none-any.whl"
    sdist = assets_dir / "truss_toolkit-0.0.50.tar.gz"
    wheel_record = _verify_wheel_record(source_root, wheel)
    wheel_payload = _verify_wheel_payload(wheel, source_payload)
    sdist_payload = _verify_sdist_payload(sdist, source_payload)

    native_manifest_path = (
        source_root / "packages/python/src/truss/_catalog_runtime/manifest.json"
    )
    native_manifest_raw = native_manifest_path.read_bytes()
    require(
        sha256(native_manifest_raw) == NATIVE_MANIFEST_SHA256,
        "Current native manifest is not the approved0.50 target",
    )
    migration_path = source_root / "packages/python/src/truss/_migrations/manifest.json"
    migration_raw = migration_path.read_bytes()
    migration_sha = sha256(migration_raw)
    migration = json.loads(
        migration_raw,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_json_constant,
    )
    require(type(migration) is dict, "Migration index is malformed")
    require(
        migration.get("interfaceVersion") == "truss-runtime-migration/0.1",
        "Migration interface mismatch",
    )
    require(
        migration.get("target") == NATIVE_MANIFEST_SHA256, "Migration target mismatch"
    )
    require(
        migration.get("sources")
        == [
            "9f6aab31802e9bebcd886f735ba9fe0bb405e69d3501a32f36cee8827b544d00",
            "71c4c3d4c05a2229c4cdec1643cabe0da7055965f0b0d23195e83ad780042a2e",
            "7ac989147f22d437b1ce0d814ebbfaa25aa868ab5495de125aa5e2bda7b963ea",
            "c4339ac7f09ab5a004c272ab00962107a970938004c1765ec4163e4d5ca9b6f0",
        ],
        "Migration source cohort changed",
    )
    require(
        migration.get("sourceWheels", {}).get("source49") == SOURCE49,
        "Exact public49 source wheel lineage mismatch",
    )
    files = migration.get("files")
    require(type(files) is dict, "Migration archive inventory missing")
    archived_name = SOURCE49_MIGRATION_MANIFEST_SHA256 + ".manifest.json"
    require(
        files.get(archived_name) == SOURCE49_MIGRATION_MANIFEST_SHA256,
        "Archived public49 migration manifest pin mismatch",
    )
    archived_path = (
        source_root / "packages/python/src/truss/_migrations" / archived_name
    )
    archived_raw = archived_path.read_bytes()
    require(
        sha256(archived_raw) == SOURCE49_MIGRATION_MANIFEST_SHA256,
        "Archived public49 manifest bytes mismatch",
    )
    archived = json.loads(
        archived_raw,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_json_constant,
    )
    require(
        archived.get("sourceWheels", {}).get("source49") is None,
        "Historical public49 manifest unexpectedly contains current source49",
    )

    pins = read_json(assets_dir / "release-pins.json")
    require(
        pins.get("tag") == TAG and pins.get("commit") == args.tag_commit,
        "Release pin source identity mismatch",
    )
    require(
        pins.get("distribution") == "truss-toolkit" and pins.get("version") == VERSION,
        "Release pin package identity mismatch",
    )
    require(
        pins.get("runtimeManifestSha256") == NATIVE_MANIFEST_SHA256,
        "Release pin native manifest mismatch",
    )
    require(
        pins.get("weftRelease") == "v" + compiler_version,
        "Release pin compiler dependency mismatch",
    )
    require(
        pins.get("migrationManifestSha256") == migration_sha,
        "Release pin migration index mismatch",
    )
    require(
        pins.get("migrationInterface") == migration.get("interfaceVersion"),
        "Release pin migration interface mismatch",
    )
    require(
        pins.get("migrationSources") == migration.get("sources")
        and pins.get("migrationTarget") == migration.get("target"),
        "Release pin migration cohort mismatch",
    )
    require(pins.get("runtimeSupport") == "latest-only", "Release is not latest-only")
    require(
        pins.get("nativePlatforms") == ["linux-x86_64"],
        "Unexpected native platform claim",
    )
    require(
        pins.get("managedGrantsInterface") == "truss-managed-grants/0.1",
        "Managed grants interface mismatch",
    )
    require(
        pins.get("actualLakebaseAcceptance") is False,
        "Artifact receipt overclaims Lakebase acceptance",
    )

    migration_receipt = read_json(assets_dir / "migration-qualification.json")
    _validate_migration_receipt(
        migration_receipt, migration, migration_sha, args.tag_commit
    )

    hf_archive_path = assets_dir / "truss-hf-conformance-0.0.50.zip"
    hf_archive = _verify_hf_archive(source_root, hf_archive_path)
    hf_receipt = read_json(assets_dir / "hf-conformance-qualification.json")
    hf_facts = _verify_hf_receipt(
        source_root, hf_receipt, hf_archive, args.tag_commit, pins
    )
    require(
        hf_receipt.get("compiler") == compiler_version,
        "HF receipt compiler differs from source dependency pin",
    )
    require(
        pins.get("hfConformanceArchive") == hf_archive_path.name,
        "Release pin HF archive name mismatch",
    )

    managed_receipt = read_json(assets_dir / "managed-grants-qualification.json")
    _validate_managed_test_total(managed_receipt)
    require(
        managed_receipt.get("sourceCommit") == args.tag_commit,
        "Managed grants source commit mismatch",
    )
    require(
        type(managed_receipt.get("platform")) is str
        and managed_receipt["platform"].lower().startswith("linux"),
        "Managed grants receipt platform mismatch",
    )
    require(
        managed_receipt.get("wheelSha256")
        == release_facts["assets"][wheel.name]["sha256"],
        "Managed grants wheel hash mismatch",
    )
    require(
        managed_receipt.get("nativeManifestSha256") == NATIVE_MANIFEST_SHA256,
        "Managed grants runtime pin mismatch",
    )
    require(
        managed_receipt.get("passed") is True and managed_receipt.get("skipped") == 0,
        "Managed grants qualification did not pass cleanly",
    )
    for field in (
        "workerStopped",
        "workerBaselineRestored",
        "inputsUnchanged",
        "payloadUnchanged",
    ):
        require(
            managed_receipt.get(field) is True,
            "Managed grants cleanup/source invariant failed",
        )
    require(
        managed_receipt.get("packageFilesVerified") == 469,
        "Managed grants source payload count mismatch",
    )
    require(
        managed_receipt.get("lakebaseAcceptance") == "not_run",
        "Managed receipt must leave Lakebase acceptance unrun",
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
        set(gate_constants) == {"MODULES", "UMF_OWNER_REVISION"},
        "Managed gate source pins missing",
    )
    require(
        managed_receipt.get("inputBasis") == _managed_input_basis(source_root),
        "Managed gate input basis differs from selected source checkout",
    )
    owner_oracle = managed_receipt.get("ownerOracle")
    require(
        type(owner_oracle) is dict
        and owner_oracle.get("inputsUnchanged") is True
        and owner_oracle.get("sourceClean") is True
        and owner_oracle.get("Bun") == "1.4.3"
        and owner_oracle.get("sourceCommit") == gate_constants["UMF_OWNER_REVISION"],
        "Managed independent owner oracle binding mismatch",
    )
    outcomes = managed_receipt.get("outcomes")
    require(type(outcomes) is list, "Managed gate outcomes missing")
    require(
        all(type(row) is dict for row in outcomes), "Malformed managed gate outcome"
    )
    require(
        [row["module"] for row in outcomes] == list(gate_constants["MODULES"]),
        "Managed gate module inventory mismatch",
    )
    for row in outcomes:
        require(
            type(row) is dict
            and row.get("passed") is True
            and row.get("returncode") == 0
            and type(row.get("tests")) is int
            and row["tests"] > 0
            and row.get("baselineRestored") is True
            and row.get("timedOut") is False,
            "Managed gate outcome did not pass cleanly",
        )
        log_name = row.get("log")
        require(
            type(log_name) is str
            and _safe_relative(log_name)
            and PurePosixPath(log_name).name == log_name,
            "Managed gate log path is unsafe",
        )

    migration_tar = _verify_tar(
        assets_dir / "migration-qualification-evidence.tar.gz",
        required_members={"qualification.json"},
    )
    managed_tar_path = assets_dir / "managed-grants-qualification-evidence.tar.gz"
    managed_tar = _verify_tar(
        managed_tar_path,
        required_members={
            "qualification.json",
            "installer-comparison/binding.json",
            "installer-comparison/report.json",
        },
    )
    # Validate the retained 49-versus-50 comparison from its public evidence bundle.
    with tarfile.open(managed_tar_path, "r:gz") as archive:
        binding_raw = archive.extractfile("installer-comparison/binding.json").read()
        comparison_raw = archive.extractfile("installer-comparison/report.json").read()
    binding = json.loads(
        binding_raw,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_json_constant,
    )
    comparison = json.loads(
        comparison_raw,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_json_constant,
    )
    expected_binding_keys = {
        "schemaVersion",
        "sourceCommit",
        "candidateWheelName",
        "candidateWheelSha256",
        "driverSha256",
        "baselineWheelName",
        "baselineWheelSha256",
        "baselineRuntimeManifestSha256",
        "reportName",
        "reportSha256",
        "scope",
    }
    require(
        set(binding) == expected_binding_keys
        and _integer_is(binding.get("schemaVersion"), 1),
        "Installer comparison binding is not closed",
    )
    driver_path = source_root / "scripts/measure-installer-submissions.py"
    require(
        binding.get("sourceCommit") == args.tag_commit,
        "Installer comparison source commit mismatch",
    )
    require(
        binding.get("candidateWheelName") == wheel.name,
        "Installer comparison candidate wheel name mismatch",
    )
    require(
        binding.get("candidateWheelSha256")
        == release_facts["assets"][wheel.name]["sha256"],
        "Installer comparison candidate wheel hash mismatch",
    )
    require(
        binding.get("driverSha256") == sha256(driver_path.read_bytes()),
        "Installer comparison driver hash mismatch",
    )
    require(
        binding.get("baselineWheelName") == SOURCE49["filename"]
        and binding.get("baselineWheelSha256") == SOURCE49["sha256"],
        "Installer comparison baseline wheel mismatch",
    )
    require(
        binding.get("baselineRuntimeManifestSha256") == NATIVE_MANIFEST_SHA256,
        "Installer comparison baseline native manifest mismatch",
    )
    require(
        binding.get("scope") == INSTALLER_COMPARISON_SCOPE,
        "Installer comparison scope mismatch",
    )
    require(
        binding.get("reportName") == "report.json"
        and binding.get("reportSha256") == sha256(comparison_raw),
        "Installer comparison report hash mismatch",
    )
    require(
        comparison.get("diagnostic") == "truss-installer-client-submissions/0.1"
        and comparison.get("status") == "passed",
        "Installer comparison did not pass",
    )
    require(
        comparison.get("workerScope") == "script_owned_WorkerCluster"
        and comparison.get("workerCleanup") == "confirmed"
        and comparison.get("workerShutdown") == "confirmed"
        and comparison.get("workerBaselineRestored") is True,
        "Installer comparison worker cleanup mismatch",
    )
    measurements = comparison.get("measurements")
    require(type(measurements) is dict, "Installer comparison measurements missing")
    for side in ("baseline", "candidate"):
        measured = measurements.get(side)
        require(
            type(measured) is dict
            and measured.get("status") == "measured"
            and measured.get("childExitCode") == 0,
            "Installer comparison phase did not complete successfully",
        )
        require(
            measured.get("installation", {}).get("status") == "success"
            and measured.get("installation", {}).get("resultVariant")
            == "PendingCatalogInstallation",
            "Installer comparison phase did not return pending installation",
        )
        require(
            measured.get("budgetsMs") == {"statement": 60000, "operation": 60000},
            "Installer comparison timeout budget mismatch",
        )
        require(
            measured.get("caller", {}).get("rollbackConfirmed") is True
            and measured.get("fixtureCleanup") == "confirmed"
            and measured.get("instrumentationHooksRestored") is True
            and measured.get("package", {}).get("unchanged") is True,
            "Installer comparison phase cleanup/caller proof mismatch",
        )
    require(
        measurements["baseline"].get("baselineWheel", {}).get("wheelSha256")
        == SOURCE49["sha256"],
        "Installer comparison baseline custody mismatch",
    )
    require(
        measurements["candidate"]
        .get("package", {})
        .get("before", {})
        .get("sourceFreeze", {})
        .get("gitCommit")
        == args.tag_commit,
        "Installer comparison candidate source mismatch",
    )
    baseline_calls = (
        measurements["baseline"]
        .get("measurement", {})
        .get("cursorExecuteSubmissionCount")
    )
    candidate_calls = (
        measurements["candidate"]
        .get("measurement", {})
        .get("cursorExecuteSubmissionCount")
    )
    require(
        type(baseline_calls) is int
        and type(candidate_calls) is int
        and baseline_calls > candidate_calls > 0,
        "Installer comparison submission count did not decrease",
    )
    spec = importlib.util.spec_from_file_location("installer_measurement", driver_path)
    require(
        spec is not None and spec.loader is not None,
        "Installer comparison validator unavailable",
    )
    measurement_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(measurement_module)
    measurement_module._validate_published_comparison(
        comparison,
        source_root=source_root / "packages/python/src/truss",
        candidate_wheel=wheel,
        source_commit=args.tag_commit,
        project_version=VERSION,
        target_manifest_sha256=NATIVE_MANIFEST_SHA256,
    )

    require(
        _read_tar_member(managed_tar_path, "qualification.json")
        == (assets_dir / "managed-grants-qualification.json").read_bytes(),
        "Managed archive qualification receipt differs from public receipt",
    )
    require(
        _read_tar_member(
            assets_dir / "migration-qualification-evidence.tar.gz", "qualification.json"
        )
        == (assets_dir / "migration-qualification.json").read_bytes(),
        "Migration archive qualification receipt differs from public receipt",
    )
    with tarfile.open(managed_tar_path, "r:gz") as archive:
        managed_archive_names = {member.name for member in archive.getmembers()}
    for row in outcomes:
        log_name = row["log"]
        require(
            log_name in managed_archive_names,
            "Managed gate log absent from evidence archive",
        )
        require(
            sha256(_read_tar_member(managed_tar_path, log_name))
            == row.get("logSha256"),
            "Managed gate log digest mismatch",
        )

    return {
        "status": "verified",
        "scope": "Downloaded public release bytes and source-bound metadata only",
        "version": VERSION,
        "tag": TAG,
        "source": source,
        "release": release_facts,
        "package": {
            "wheelRecord": wheel_record,
            "wheelPayload": wheel_payload,
            "sdistPayload": sdist_payload,
            "sourcePayloadFiles": len(source_payload),
            "publisherSidecars": sidecars,
        },
        "migration": {
            "manifestSha256": migration_sha,
            "source49": SOURCE49,
            "retainedPublic49ManifestSha256": SOURCE49_MIGRATION_MANIFEST_SHA256,
            "receiptTests": migration_receipt.get("tests"),
            "evidenceArchive": migration_tar,
        },
        "hfConformance": {
            "archive": {
                key: value for key, value in hf_archive.items() if key != "manifest"
            },
            "receiptTests": hf_facts["tests"],
            "compilerCohort": hf_facts["cohort"],
        },
        "managedGrants": {
            "receiptTests": managed_receipt.get("tests"),
            "evidenceArchive": managed_tar,
            "installerComparison": "passed",
        },
        "actualNativeQualification": "not_run",
        "lakebaseAcceptance": "not_run",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--release-api", required=True, type=Path)
    parser.add_argument("--tag-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output_fd = None
    try:
        output_fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        report = verify(args)
        report["verification"] = {
            "producer": Path(__file__).name,
            "producerSha256": sha256(Path(__file__).read_bytes()),
        }
        payload = json.dumps(report, sort_keys=True, indent=2).encode() + b"\n"
        os.write(output_fd, payload)
        os.fsync(output_fd)
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        SyntaxError,
        zipfile.BadZipFile,
        tarfile.TarError,
        subprocess.CalledProcessError,
    ) as error:
        if output_fd is not None:
            failure = {
                "status": "refused",
                "reasonType": type(error).__name__,
                "producer": Path(__file__).name,
                "producerSha256": sha256(Path(__file__).read_bytes()),
                "actualNativeQualification": "not_run",
                "lakebaseAcceptance": "not_run",
            }
            os.write(
                output_fd,
                json.dumps(failure, sort_keys=True, indent=2).encode() + b"\n",
            )
            os.fsync(output_fd)
        return 1
    finally:
        if output_fd is not None:
            os.close(output_fd)


if __name__ == "__main__":
    raise SystemExit(main())
