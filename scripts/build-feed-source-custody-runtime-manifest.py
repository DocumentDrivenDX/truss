#!/usr/bin/env python3
"""Refresh the content pins for the review-only feed custody runtime candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "packages/python/src/truss/_catalog_runtime"
MANIFEST = RUNTIME / "manifest.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_bytes())
    if manifest.get("releaseId") not in (
        "truss-catalog-runtime/0.74-candidate",
        "truss-catalog-runtime/0.75-candidate",
    ):
        raise SystemExit("unexpected source runtime candidate lineage")
    manifest["releaseId"] = "truss-catalog-runtime/0.75-candidate"
    manifest["version"] = "0.75"
    for name in ("runtime.sql", "read.sql", "query.sql"):
        if name not in manifest["files"]:
            raise SystemExit(f"missing pinned runtime source: {name}")
    manifest["files"]["feed-custody.sql"] = ""
    for name in sorted(manifest["files"]):
        path = RUNTIME / name
        if not path.is_file():
            raise SystemExit(f"missing pinned runtime source: {name}")
        manifest["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
