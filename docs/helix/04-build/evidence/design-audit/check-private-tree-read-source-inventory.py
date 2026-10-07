"""Source inventory correspondence only; no native execution or installer."""
import copy
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
EXPECTED = [("private-property-state-observation",2),("private-tree-state-observation",1),("private-tree-full-observation",2),("private-scalar-full-observation",1)]
def require(ok, reason):
    if not ok: raise ValueError(reason)
def digest(path): return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def audit(candidate):
    require(candidate["status"] == "planned_unadopted" and candidate["nativeExecution"] is False and candidate["complete"] is False, "qualification inflation")
    require([(entry["family"],entry["statementCount"]) for entry in candidate["families"]] == EXPECTED, "original family membership")
    require(candidate["statementCount"] == 6 and candidate["artifactPinCount"] == 16, "scope counts")
    seen = set()
    for entry in candidate["families"]:
        name,count = entry["family"],entry["statementCount"]
        receipt_path = Path("docs/helix/04-build/evidence/design-audit")/(name+"-source.json")
        require(entry["captureReceipt"] == str(receipt_path) and entry["captureReceiptSha256"] == digest(receipt_path), "receipt identity/hash")
        receipt = json.loads((ROOT/receipt_path).read_text())
        require(receipt["ownerSource"] == candidate["ownerSource"], "mixed original UMF tuple")
        require(len(receipt["observations"]) == 1, "capture observations")
        observation = receipt["observations"][0]
        require(observation["complete"] is False and observation["declarationCount"] == 0 and len(observation["unhandled"]) == count, "partial extraction scope")
        expected_paths = {"path": f"docs/helix/02-design/contracts/{name}-v0.1.proposal.sql", "artifactPath": f"docs/helix/02-design/contracts/{name}-v0.1.proposal.umf.json", "exportPath": f"docs/helix/04-build/evidence/design-audit/{name}.owner-export.sql"}
        require(all(observation[key] == path for key,path in expected_paths.items()), "original family source identity")
        expected_pins = {}
        for key,hashkey in [("path","sourceSha256"),("artifactPath","artifactSha256"),("exportPath","exportSha256")]:
            path = Path(observation[key])
            require(digest(path) == observation[hashkey], "stale capture original")
            expected_pins[str(path)] = observation[hashkey]
        manifest_path = Path("docs/helix/02-design/contracts/bindings")/(name+"-v0.1.proposal.json")
        manifest = json.loads((ROOT/manifest_path).read_text())
        require(manifest["sourceSha256"] == observation["sourceSha256"] and manifest["modelSha256"] == observation["artifactSha256"], "manifest source/model")
        require(manifest["nativeExecution"] is False and manifest["complete"] is False, "manifest native inflation")
        expected_pins[str(manifest_path)] = digest(manifest_path)
        require(entry["artifactSha256"] == expected_pins, "original artifact membership/hash")
        require(not seen.intersection(expected_pins), "duplicate artifact identity")
        seen.update(expected_pins)
    require(len(seen) == 16, "full original artifact union")
inventory_path = HERE/"private-tree-read-source-inventory.proposal.json"
inventory = json.loads(inventory_path.read_text())
audit(inventory)
controls = []
for label in ["missing_family","duplicate_family","stale_artifact","changed_owner_tuple","complete_claim","narrow_statement_count"]:
    altered = copy.deepcopy(inventory)
    if label == "missing_family": altered["families"].pop()
    elif label == "duplicate_family": altered["families"][1] = copy.deepcopy(altered["families"][0])
    elif label == "stale_artifact": altered["families"][0]["artifactSha256"][next(iter(altered["families"][0]["artifactSha256"]))] = "0"*64
    elif label == "changed_owner_tuple": altered["ownerSource"]["commit"] = "foreign"
    elif label == "complete_claim": altered["complete"] = True
    else: altered["statementCount"] = 5
    try: audit(altered)
    except ValueError: controls.append(label)
    else: raise ValueError("corruption passed: "+label)
result = {"scope":"Four historical UMF source-capture families/six SELECT statements/sixteen artifact pins only; no source semantic, native descriptor, installation or decoder qualification", "inventorySha256":hashlib.sha256(inventory_path.read_bytes()).hexdigest(), "families":4,"statements":6,"artifactPins":16,"corruptionControls":controls,"nativeExecution":False,"complete":False}
(HERE/"private-tree-read-source-inventory-audit.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result))
