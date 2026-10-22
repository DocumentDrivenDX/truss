# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fail-closed checks for the released-runtime verification runner."""

from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path


_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_VERBOSE_TEST = re.compile(
    r"^(?P<name>test_[A-Za-z0-9_]+) \((?P<module>[A-Za-z0-9_.]+)\."
    r"(?P<class_name>[A-Za-z_][A-Za-z0-9_]*)\."
    r"(?P=name)\) \.\.\. (?P<outcome>.+)$"
)
_RUN_SUMMARY = re.compile(r"^Ran (?P<count>[0-9]+) tests? in .+$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_sha256sums(text: str, *, label: str = "SHA256SUMS") -> dict[str, str]:
    """Parse a standard sha256sum manifest with unique, basename-only assets."""
    entries: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"{label}:{line_number}: expected a digest and filename")
        digest, filename = parts
        filename = filename.lstrip("*").strip()
        if not _SHA256.fullmatch(digest):
            raise ValueError(f"{label}:{line_number}: invalid SHA-256 digest")
        if not filename or Path(filename).name != filename or filename in {".", ".."}:
            raise ValueError(f"{label}:{line_number}: expected a basename-only filename")
        if filename in entries:
            raise ValueError(f"{label}:{line_number}: duplicate filename {filename!r}")
        entries[filename] = digest.lower()
    if not entries:
        raise ValueError(f"{label}: no checksum entries")
    return entries


def verify_asset_checksum(path: Path, entries: dict[str, str], *, label: str) -> str:
    """Require a named manifest entry and an exact file digest match."""
    expected = entries.get(path.name)
    if expected is None:
        raise ValueError(f"{label}: no checksum entry for {path.name}")
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{label}: SHA-256 mismatch for {path.name}")
    return actual


def declared_test_inventory(path: Path, class_name: str) -> dict[str, object]:
    """Derive a unittest class's direct test methods and source digest from AST."""
    source = path.read_bytes()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        raise ValueError(f"Cannot parse test source {path}: {error}") from error
    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    ]
    if len(classes) != 1:
        raise ValueError(f"Expected exactly one top-level {class_name} in {path}")
    names = [
        node.name
        for node in classes[0].body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    if not names or len(names) != len(set(names)):
        raise ValueError(f"{class_name} has no tests or duplicate test method names")
    return {
        "sourceSha256": hashlib.sha256(source).hexdigest(),
        "names": sorted(names),
        "count": len(names),
    }


def validate_verbose_unittest_result(
    output: str,
    *,
    returncode: int,
    expected_module: str,
    expected_class: str,
    expected_names: list[str],
    source_sha256: str,
) -> dict[str, object]:
    """Require the exact AST-declared test set, all successful and unskipped."""
    executions: list[tuple[str, str]] = []
    for line in output.splitlines():
        if "PsycopgHostNativeTests." not in line and f".{expected_class}." not in line:
            continue
        match = _VERBOSE_TEST.fullmatch(line)
        if match is None:
            if f".{expected_class}." in line:
                raise ValueError(f"Unrecognized verbose unittest result: {line}")
            continue
        if match.group("class_name") != expected_class:
            continue
        if match.group("module") != expected_module:
            raise ValueError(
                f"Unexpected test module {match.group('module')!r}; expected {expected_module!r}"
            )
        executions.append((match.group("name"), match.group("outcome")))

    names = [name for name, _ in executions]
    if len(names) != len(set(names)):
        raise ValueError("Verbose unittest output contains duplicate driver test names")
    expected = set(expected_names)
    observed = set(names)
    if observed != expected:
        missing = sorted(expected - observed)
        unexpected = sorted(observed - expected)
        raise ValueError(f"Driver test inventory mismatch; missing={missing}, unexpected={unexpected}")
    nonpassing = [(name, outcome) for name, outcome in executions if outcome != "ok"]
    if nonpassing:
        raise ValueError(f"Driver tests did not all pass without skips: {nonpassing}")

    summaries = [
        int(match.group("count"))
        for line in output.splitlines()
        if (match := _RUN_SUMMARY.fullmatch(line.strip())) is not None
    ]
    if summaries != [len(expected_names)] or returncode != 0:
        raise ValueError(
            "Driver test command did not report the exact passing count and exit zero "
            f"(summaries={summaries}, returncode={returncode})"
        )
    if "OK" not in {line.strip() for line in output.splitlines()}:
        raise ValueError("Driver test command did not report unittest OK")

    return {
        "sourceSha256": source_sha256,
        "declaredCount": len(expected_names),
        "declaredNames": sorted(expected_names),
        "executedCount": len(names),
        "executedNames": names,
        "skippedCount": 0,
        "returnCode": returncode,
    }
