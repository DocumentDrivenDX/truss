"""Independent draft-fixture consistency only; no production/native qualification."""
from pathlib import Path
import hashlib
import json
import platform
import re

root = Path(__file__).resolve().parents[3]
bindings = root / "02-design/contracts/bindings"
def require(condition, message):
    if not condition:
        raise ValueError(message)
def read(name):
    p = bindings / name
    return json.loads(p.read_text()), {"path": str(p.relative_to(root)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
v, vh = read("command-complete-v0.1.vectors.proposal.json")
s, sh = read("savepoint-resource-v0.1.proposal.json")
f, fh = read("failure-order-v0.1.vectors.proposal.json")
require(v["interfaceVersion"] == "truss-postgresql-command-complete/0.1.0", "tag profile")
require(len(v["cases"]) == 14, "fixture inventory changed")
ids = set()
for c in v["cases"]:
    require(c["id"] not in ids, "duplicate case")
    ids.add(c["id"])
    tag = c["nativeTag"]
    match = re.fullmatch(r"(?:INSERT 0|DELETE|UPDATE|MERGE|SELECT|MOVE|FETCH|COPY) (0|[1-9][0-9]{0,19})", tag)
    accepted = tag.isascii() and len(tag) <= 128 and match is not None
    count = match.group(1) if accepted else None
    accepted = accepted and int(count) <= 18446744073709551615
    if not accepted:
        count = None
    require(accepted == c["expectedAdmission"] and count == c["expectedCount"], "inconsistent tag fixture: " + c["id"])
limits = s["limits"]
require(s["interfaceVersion"] == "truss-postgresql-savepoint-resource/0.1.0", "resource profile")
for key, value in limits.items():
    require(re.fullmatch(r"[1-9][0-9]*", value) is not None, "noncanonical positive limit: " + key)
x = {k: int(v) for k, v in limits.items()}
require(x["allControlSubmissions"] == x["normalControlSubmissions"] + x["cumulativeCleanupCommandSubmissions"], "category totals")
require(x["outstandingCleanupCommandPermits"] == 2 * x["outstandingTrussHandles"], "simultaneous cleanup")
require(x["cumulativeCleanupCommandSubmissions"] == 2 * x["createdAttempts"], "cumulative cleanup ceiling")
require(x["outstandingTrussHandles"] <= x["totalAdmittedNativeSavepointDepth"], "stack ceiling")
require(x["retainedHandleRecords"] == x["createdAttempts"], "record inventory")
require(x["retainedHandleRecords"] * x["oneHandleRecordAccountedBytes"] <= x["peakOwnedBytes"], "record-only footprint")
require(x["peakOwnedBytes"] <= x["cumulativeAllocationBytes"], "allocation ceilings")
require(f["interfaceVersion"] == "truss-postgresql-failure-order/0.1.0", "failure profile")
require(len(f["cases"]) == 12 and len({c["id"] for c in f["cases"]}) == 12, "failure inventory")
for c in f["cases"]:
    expected_scope = "whole_transaction" if c["expectedClassification"] == "retry" else "qualified_request_lookup" if c["expectedClassification"] == "commit_unknown" else "none"
    require(c["expectedRetryScope"] == expected_scope, "failure retry scope")
    require(c["automaticReplayPermitted"] is False and c["trussWholeCallerTerminationPermitted"] is False, "failure ownership")
cancelled = next(c for c in f["cases"] if c["id"] == "caller-cancel-contained")
require(cancelled["expectedOriginalGenerationAdmission"] == "closed_by_latched_cancellation" and cancelled["expectedNativeHostTransactionState"] == "usable_pending", "cancellation lifetime")
receipt = {"scope": "Draft tag-fixture grammar/expected-count, failure scope/ownership/cancellation-lifetime consistency and resource arithmetic only; excludes production parser, non-count tags, driver metadata, full metering, native execution and profile adoption", "status": "pass", "tagCases": len(ids), "sources": [vh, sh, fh], "failureCases": len(f["cases"]), "checkerSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "pythonVersion": platform.python_version()}
Path(__file__).with_name("executor-candidate-fixtures.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
