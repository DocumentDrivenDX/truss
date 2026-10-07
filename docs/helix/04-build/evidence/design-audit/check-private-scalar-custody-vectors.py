"""Audit independently authored fixture bytes/math; never execute a decoder."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
FIXTURE = ROOT / "docs/helix/03-test/test-plans/private-scalar-custody-vectors.proposal.json"

def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(data):
    require(data["nativeExecution"] is False, "native qualification inflation")
    cases = {case["id"]: case for case in data["cases"]}
    require(len(cases) == len(data["cases"]) == 12, "duplicate/missing cases")
    require(set(cases) == {f"SC{i:02}" for i in range(1, 13)}, "case inventory")
    require(cases["SC06"]["physicalStageExpected"] == "scalar_observation" and cases["SC06"]["expected"]["outcome"] == "refuse", "numeric layer conflation")
    require(cases["SC12"]["physicalStageExpected"] == "scalar_observation" and cases["SC12"]["expected"]["outcome"] == "refuse", "hidden payload layer conflation")
    require(all(case["expected"]["publicationPermitted"] is False for case in cases.values()), "scalar-stage publication inflation")
    expected_sources = {
        "SC01": '""', "SC02": '"é😀  "', "SC03": "false",
        "SC04": "18446744073709551615", "SC05": "-0.00",
        "SC06": "1.26", "SC07": '""', "SC08": "false",
        "SC09": '""', "SC11": '""', "SC12": '""',
    }
    for identity, source in expected_sources.items():
        row = cases[identity]["nativeObservations"]
        require(len(row) == 8, identity + " projection width")
        require(row[7] == source.encode("utf-8").hex(), identity + " source bytes")
    require(json.loads(expected_sources["SC02"]) == cases["SC02"]["logicalValue"], "Unicode expectation")
    require(json.loads(expected_sources["SC03"]) is False, "false expectation")
    require(int(expected_sources["SC04"]) == 2**64 - 1, "uint64 expectation")
    negative_zero = cases["SC05"]["nativeObservations"]
    require(Decimal(negative_zero[4]) == Decimal(negative_zero[5]), "zero equality")
    require(Decimal(negative_zero[5]).is_signed() and negative_zero[5] == "-0.00", "zero lexical custody")
    mismatch = cases["SC06"]["nativeObservations"]
    require(Decimal(mismatch[4]) != Decimal(mismatch[5]), "mismatch expectation")
    require(cases["SC07"]["nativeObservations"][2] is None, "NULL fixture")
    require(cases["SC09"]["nativeObservations"][6] == "0", "malformed carrier fixture")
    require(cases["SC10"]["expected"]["outcome"] == "require_separate_node_admission", "absence inference")
    require(cases["SC11"]["expected"]["outcome"] == "refuse_unavailable_bridge", "binary bridge inflation")
    require(cases["SC12"]["fullSlotPreflight"] == "conflicting_unprojected_payload", "hidden payload fixture")

if __name__ == "__main__":
    original = FIXTURE.read_bytes()
    audit(json.loads(original))
    result = {"scope": "Independent authored UTF-8 source bytes and finite numeric fixture facts only; no decoder, native descriptors, codec registration or host qualification", "fixtureSha256": hashlib.sha256(original).hexdigest(), "cases": 12, "nativeExecution": False, "complete": False}
    target = Path(__file__).with_name("private-scalar-custody-vectors-audit.json")
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
