"""Run with the clean pinned-wheel Python; compiler-only synthetic fixture checks."""
import hashlib
import json
from pathlib import Path
import sys
import weft

repository = Path(__file__).resolve().parents[5]
fixture = repository / "tests/weft/fixtures/qualified-count.request.json"
request = json.loads(fixture.read_text())
raw = weft.compile_json(json.dumps(request))
response = json.loads(raw)
if response["status"] != "compiled" or "count(*)::text" not in response["sql"]:
    raise ValueError("Independent count compilation expectation failed")
if response["backend"]["backendVersion"] != "0.1.0-qualified":
    raise ValueError("Wrong qualified backend")
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
    "fixtureSha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
    "checkerSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "countResponseSha256": hashlib.sha256(raw.encode()).hexdigest(),
    "countCompiled": True,
    "unsupportedProfileRefused": True,
    "transportRefusals": 5,
    "testOnlyExportAbsent": True,
    "nativeExecuted": False,
    "qualifiedTrussPythonRuntime": False,
}
Path(__file__).with_name("weft-python-count-component.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
