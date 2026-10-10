"""Run with the clean pinned-wheel Python; compiler-only synthetic fixture checks."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import weft
import weft.weft as native_extension

repository = Path(__file__).resolve().parents[5]
build = json.loads(Path(__file__).with_name("weft-python-wheel-development-smoke.json").read_text())
wheel = Path(build["wheel"]["path"])
if hashlib.sha256(wheel.read_bytes()).hexdigest() != build["wheel"]["sha256"]:
    raise ValueError("Original wheel bytes changed")
with zipfile.ZipFile(wheel) as archive:
    members = [name for name in archive.namelist() if name.endswith(".so")]
    if len(members) != 1:
        raise ValueError("Expected exactly one original native extension")
    native_bytes = archive.read(members[0])
if Path(native_extension.__file__).read_bytes() != native_bytes:
    raise ValueError("Loaded extension does not match original wheel payload")
if build["features"] != ["truss-postgresql-qualified"]:
    raise ValueError("Wrong original build feature tuple")
fixture = repository / "tests/weft/fixtures/qualified-count.request.json"
request = json.loads(fixture.read_text())
raw = weft.compile_json(json.dumps(request))
response = json.loads(raw)
if response["status"] != "compiled" or "count(*)::text" not in response["sql"]:
    raise ValueError("Independent count compilation expectation failed")
if response["backend"]["backendVersion"] != "0.1.0-qualified":
    raise ValueError("Wrong qualified backend")
grouped = json.loads(fixture.read_text())
grouped["sql"] = "SELECT c.name, COUNT(*) AS total FROM Customer c GROUP BY c.name ORDER BY c.name LIMIT 10"
grouped_raw = weft.compile_json(json.dumps(grouped))
grouped_response = json.loads(grouped_raw)
if grouped_response["status"] != "compiled" or "count(*)::text" not in grouped_response["sql"]:
    raise ValueError("Bounded ordered grouped count did not compile")
if not all(clause in grouped_response["sql"].upper() for clause in ["GROUP BY", "ORDER BY", "LIMIT"]):
    raise ValueError("Grouped count lost its required grouping/order/limit")
unbounded = json.loads(fixture.read_text())
unbounded["sql"] = "SELECT c.name, COUNT(*) AS total FROM Customer c GROUP BY c.name ORDER BY c.name"
unbounded_response = json.loads(weft.compile_json(json.dumps(unbounded)))
if unbounded_response["status"] != "blocked" or "sql" in unbounded_response:
    raise ValueError("Grouped count without LIMIT did not refuse")
changed = json.loads(fixture.read_text())
changed["target"]["targetProfile"] = "truss-reference-history/0.12"
refused = json.loads(weft.compile_json(json.dumps(changed)))
if refused["status"] != "blocked" or "sql" in refused:
    raise ValueError("Unsupported profile did not refuse before SQL publication")
for value in [None, {}, b"{}", 1]:
    try:
        weft.compile_json(value)
    except TypeError:
        continue
    raise ValueError("Wrong Python transport type accepted")
try:
    weft.compile_json("\ud800")
except UnicodeError:
    pass
else:
    raise ValueError("Invalid Unicode transport accepted")
if hasattr(weft, "compile_json_with_conformance_configuration"):
    raise ValueError("Test-only configuration export present")
receipt = {
    "scope": "public Python compiler-only count, profile and transport checks; synthetic upstream binding, no accepted Truss IDs or native execution",
    "python": sys.version,
    "weftVersion": weft.__version__,
    "wheelSha256": build["wheel"]["sha256"],
    "nativeExtensionSha256": hashlib.sha256(native_bytes).hexdigest(),
    "loadedExtensionMatchesOriginalWheel": True,
    "fixtureSha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
    "checkerSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "countResponseSha256": hashlib.sha256(raw.encode()).hexdigest(),
    "groupedResponseSha256": hashlib.sha256(grouped_raw.encode()).hexdigest(),
    "countCompiled": True,
    "boundedOrderedGroupedCountCompiled": True,
    "unboundedGroupedCountRefused": True,
    "unsupportedProfileRefused": True,
    "transportRefusals": 5,
    "testOnlyExportAbsent": True,
    "nativeExecuted": False,
    "qualifiedTrussPythonRuntime": False,
}
Path(__file__).with_name("weft-python-count-component.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
