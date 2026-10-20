#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Verify an exact frozen Weft wheel against its native module and RECORD."""
from __future__ import annotations

import argparse
import ast
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

_HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_NATIVE_SUFFIXES = (".so", ".dylib", ".pyd")


def _cohorts(source_path: Path) -> list[dict[str, str]]:
    """Read only explicit wheel/module pins from the source cohort AST."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    assignment = None
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_CONSUMER_COHORTS"
            for target in statement.targets
        ):
            if assignment is not None:
                raise ValueError("Duplicate _CONSUMER_COHORTS assignment")
            assignment = statement.value
    if not isinstance(assignment, ast.Tuple) or not assignment.elts:
        raise ValueError("Frozen _CONSUMER_COHORTS tuple required")

    result: list[dict[str, str]] = []
    for element in assignment.elts:
        if not isinstance(element, ast.Dict):
            raise ValueError("Each frozen consumer cohort must be an explicit dict")
        pair: dict[str, str] = {}
        for key_node, value_node in zip(element.keys, element.values):
            if key_node is None:
                if pair:
                    raise ValueError("Dictionary unpack cannot follow explicit frozen cohort pins")
                continue
            if not isinstance(key_node, ast.Constant) or type(key_node.value) is not str:
                raise ValueError("Dynamic keys are not allowed in frozen consumer cohorts")
            if key_node.value not in ("weftWheelSha256", "weftModuleSha256"):
                continue
            key = key_node.value
            if key in pair or not isinstance(value_node, ast.Constant) or type(value_node.value) is not str:
                raise ValueError(f"Malformed explicit {key} in frozen cohort")
            if not _HEX_SHA256.fullmatch(value_node.value):
                raise ValueError(f"Malformed SHA-256 pin for {key}")
            pair[key] = value_node.value
        if set(pair) != {"weftWheelSha256", "weftModuleSha256"}:
            raise ValueError("Each cohort needs explicit Weft wheel and module SHA-256 pins")
        result.append(pair)

    wheels = [row["weftWheelSha256"] for row in result]
    modules = [row["weftModuleSha256"] for row in result]
    if len(set(wheels)) != len(wheels) or len(set(modules)) != len(modules):
        raise ValueError("Duplicate or ambiguous frozen Weft cohort pins")
    return result


def _safe_member(name: str) -> bool:
    if name.endswith("/"):
        name = name[:-1]
    return (
        bool(name)
        and "\\" not in name
        and not name.startswith("/")
        and "\x00" not in name
        and all(part not in ("", ".", "..") for part in name.split("/"))
    )


def _record_digest(algorithm: str, payload: bytes) -> str:
    try:
        digest = hashlib.new(algorithm, payload).digest()
    except ValueError as error:
        raise ValueError(f"Unsupported RECORD hash algorithm: {algorithm}") from error
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _verify_record(archive: zipfile.ZipFile, infos: list[zipfile.ZipInfo]) -> str:
    names = [info.filename for info in infos]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate wheel archive member")
    for info in infos:
        if not _safe_member(info.filename):
            raise ValueError("Unsafe wheel archive member path")
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise ValueError("Symlinks are not allowed in the wheel archive")
        file_type = stat.S_IFMT(mode)
        if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ValueError("Unsupported wheel archive member type")
        if file_type == stat.S_IFDIR and not info.is_dir():
            raise ValueError("Malformed wheel directory member")

    record_names = [
        name for name in names
        if name.endswith(".dist-info/RECORD") and not name.endswith("/")
    ]
    if len(record_names) != 1:
        raise ValueError("Wheel must contain exactly one RECORD")
    record_name = record_names[0]
    records: dict[str, tuple[str, str]] = {}
    try:
        text = archive.read(record_name).decode("utf-8")
        rows = csv.reader(io.StringIO(text, newline=""), strict=True)
        for row in rows:
            if len(row) != 3:
                raise ValueError("Malformed wheel RECORD row")
            name, digest, size = row
            if not _safe_member(name) or name in records:
                raise ValueError("Unsafe or duplicate wheel RECORD path")
            records[name] = (digest, size)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("Malformed wheel RECORD") from error

    payload_names = {info.filename for info in infos if not info.is_dir()}
    if set(records) != payload_names:
        raise ValueError("Wheel payload and RECORD member sets differ")
    for name, (recorded_hash, recorded_size) in records.items():
        payload = archive.read(name)
        if name == record_name and not recorded_hash and not recorded_size:
            continue
        if not recorded_hash or not recorded_size:
            raise ValueError("Wheel RECORD hash and size are required for every payload")
        algorithm, separator, expected = recorded_hash.partition("=")
        if not separator or algorithm not in ("sha256", "sha384", "sha512"):
            raise ValueError("Unsupported or malformed wheel RECORD digest")
        if _record_digest(algorithm, payload) != expected:
            raise ValueError(f"Wheel RECORD hash mismatch: {name}")
        if not recorded_size.isdecimal() or int(recorded_size) != len(payload):
            raise ValueError(f"Wheel RECORD size mismatch: {name}")
    return record_name


def verify_wheel(wheel_path: Path, source_path: Path) -> dict[str, object]:
    cohorts = _cohorts(source_path)
    wheel_bytes = wheel_path.read_bytes()
    wheel_sha = hashlib.sha256(wheel_bytes).hexdigest()
    if sum(row["weftWheelSha256"] == wheel_sha for row in cohorts) != 1:
        raise ValueError("Wheel archive SHA-256 does not match one frozen cohort")
    try:
        with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as archive:
            infos = archive.infolist()
            record_name = _verify_record(archive, infos)
            native_members = [
                info.filename for info in infos
                if not info.is_dir()
                and info.filename.startswith("weft/weft")
                and info.filename.endswith(_NATIVE_SUFFIXES)
            ]
            if len(native_members) != 1:
                raise ValueError("Wheel must contain exactly one Weft native module")
            native_name = native_members[0]
            module_sha = hashlib.sha256(archive.read(native_name)).hexdigest()
    except (zipfile.BadZipFile, OSError) as error:
        raise ValueError("Invalid Weft wheel archive") from error

    selected = [row for row in cohorts if row["weftModuleSha256"] == module_sha]
    if len(selected) != 1:
        raise ValueError("Native Weft module does not select one frozen consumer cohort")
    if wheel_sha != selected[0]["weftWheelSha256"]:
        raise ValueError("Wheel archive SHA-256 does not match the selected frozen cohort")
    return {
        "status": "verified",
        "wheel": wheel_path.name,
        "wheelSha256": wheel_sha,
        "nativeModule": native_name,
        "nativeModuleSha256": module_sha,
        "record": record_name,
        "recordedPayloadCount": sum(1 for info in infos if not info.is_dir()),
        "cohortCount": len(cohorts),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("packages/python/src/truss/_current_query_originals.py"),
        help="source file containing the frozen query-cohort registry",
    )
    args = parser.parse_args(argv)
    try:
        result = verify_wheel(args.wheel, args.source)
    except (OSError, SyntaxError, ValueError) as error:
        print(json.dumps({"status": "refused", "reason": str(error)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
