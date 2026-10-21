# SPDX-License-Identifier: MIT OR Apache-2.0
"""Build the sole current UMF 0.10 catalog preparation bundle."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
umf = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
if umf is None:
    raise SystemExit("UMF Git checkout required")
dependencies = Path(os.environ.get("TRUSS_UMF_NODE_MODULES", str(umf / "node_modules"))).resolve()
target = root / "packages/python/src/truss/_umf_core10"
target.mkdir(parents=True, exist_ok=True)
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

built = subprocess.run(
    ["bun", "scripts/build-umf-runtime.ts", str(umf), "core10-catalog"],
    cwd=root,
    check=True,
    text=True,
    capture_output=True,
    timeout=120,
)
owner = Path(built.stdout.strip().splitlines()[-1])
for name in ("producer.js", "producer-manifest.json"):
    shutil.copyfile(owner / name, target / name)

bridge = subprocess.run(
    ["bun", "build", "packages/umf-bun/src/python-preparation-core10.ts", "--target=bun", "--format=esm", f"--outfile={target / 'preparation.mjs'}"],
    cwd=root,
    check=True,
    text=True,
    capture_output=True,
    timeout=120,
)

schema = root / "docs/helix/02-design/contracts/bindings/truss-acceptance-input-v0.1.schema.json"
if not schema.exists():
    schema = root / "docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json"
if not schema.exists():
    raise SystemExit("Pinned Truss preparation-input schema missing")
shutil.copyfile(schema, target / "acceptance-input-v0.1.schema.json")
keys = root / "packages/umf-bun/src/python-keys.mjs"
if not keys.exists():
    raise SystemExit("Current UMF key bridge missing")
shutil.copyfile(keys, target / "keys.mjs")

licenses = target / "licenses"
licenses.mkdir(exist_ok=True)
for package, filename in (("ajv", "LICENSE"), ("yaml", "LICENSE"),
                         ("fast-deep-equal", "LICENSE"), ("fast-uri", "LICENSE"),
                         ("json-schema-traverse", "LICENSE"), ("require-from-string", "license")):
    source = dependencies / package / filename
    if not source.exists():
        raise SystemExit(f"Bundled dependency license missing: {package}")
    shutil.copyfile(source, licenses / f"{package}.txt")

owner_manifest = json.loads((target / "producer-manifest.json").read_text())
paths = ["acceptance-input-v0.1.schema.json", "keys.mjs", "preparation.mjs", "producer-manifest.json", "producer.js"]
paths += [f"licenses/{path.name}" for path in sorted(licenses.iterdir()) if path.is_file()]
manifest = {
    "interfaceVersion": "truss-core10-catalog-producer/0.2.0",
    "runtimeVersion": subprocess.run(["bun", "--version"], check=True, text=True, capture_output=True).stdout.strip(),
    "owner": owner_manifest,
    "files": {name: digest(target / name) for name in paths},
    "scope": "Original UMF 0.10.0 core and selected DDD 0.1.0 document validation, plus Truss current-key realization; no native admission claim.",
}
encoded = json.dumps(manifest, indent=2) + "\n"
(target / "manifest.json").write_text(encoded)
(root / "packages/python/src/truss/_core10_catalog_release.py").write_text(
    '"""Generated current UMF 0.10 catalog producer pin."""\nMANIFEST_SHA256 = '
    + json.dumps(hashlib.sha256(encoded.encode()).hexdigest())
    + "\n"
)
print(json.dumps({"target": str(target), "ownerRevision": owner_manifest["revision"],
                  "producerSha256": owner_manifest["bundleSha256"],
                  "manifestSha256": hashlib.sha256(encoded.encode()).hexdigest()}))
