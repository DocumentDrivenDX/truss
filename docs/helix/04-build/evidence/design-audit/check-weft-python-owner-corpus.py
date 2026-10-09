"""Pinned owner artifact parity only; no independent/native Truss execution."""
import gzip
import hashlib
import json
from pathlib import Path
import runpy
import sys
import weft

# Reuse the actual wheel/loaded-extension verification and focused controls.
runpy.run_path(str(Path(__file__).with_name("check-weft-python-count.py")))
component = json.loads(Path(__file__).with_name("weft-python-count-component.json").read_text())
source = Path(sys.argv[1]).read_bytes()
source_hash = hashlib.sha256(source).hexdigest()
if source_hash != "39039daf794bac5ff2bfd4761e72a605ed0f6f8be776e31673d661377f431763":
    raise ValueError("Changed original committed owner artifact corpus")
records = [json.loads(line) for line in gzip.decompress(source).decode().splitlines()]
if len(records) != 2181 or len({r["id"] for r in records}) != 2181:
    raise ValueError("Incomplete or duplicate owner corpus")
selected = [r for r in records if r["request"]["target"]["backendId"] == "truss.postgresql"]
if len(selected) != 1216:
    raise ValueError("Incomplete Truss subset")
cases = []
for record in selected:
    raw = weft.compile_json(json.dumps(record["request"], ensure_ascii=False))
    if json.loads(raw) != record["response"]:
        raise ValueError("Original owner artifact mismatch: " + record["id"])
    cases.append({"id": record["id"], "responseSha256": hashlib.sha256(raw.encode()).hexdigest()})
receipt = {
    "scope": "full Truss subset public Python compiler artifact parity with committed owner outputs; owner outputs are not an independent Truss oracle",
    "sourceRevision": "5856c73db0342363e64802905a94abb96209d757",
    "sourceArtifactSha256": source_hash,
    "wheelSha256": component["wheelSha256"],
    "nativeExtensionSha256": component["nativeExtensionSha256"],
    "checkerSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "cases": cases,
    "passed": len(cases),
    "excludedAshlarCases": 965,
    "comparison": "complete parsed response equality; no byte-order normalization claim",
    "nativeTrussExecuted": False,
    "qualifiedTrussPythonRuntime": False,
}
Path(__file__).with_name("weft-python-owner-corpus-parity.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"passed": len(cases), "nativeTrussExecuted": False}))
