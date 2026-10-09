"""Assess recorded Rust test-frontend responses; never qualifies native execution."""
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def assess(packet, rows):
    receipt = json.loads((HERE / f"consumer-{packet}-frontend.json").read_text())
    raw_inputs = (HERE / f"consumer-{packet}-frontend-inputs.json").read_bytes()
    assert hashlib.sha256(raw_inputs).hexdigest() == receipt["inputsSha256"]
    harness = HERE / "consumer-logical-frontend-harness.rs"
    assert hashlib.sha256(harness.read_bytes()).hexdigest() == receipt["harnessSha256"]
    inputs = json.loads(raw_inputs)
    expected = receipt["observations"]
    assert len(rows) == len(inputs) == len(expected)
    identities = [(r["source"], r["variant"]) for r in rows]
    assert len(set(identities)) == len(identities)
    for source, observed, saved in zip(inputs, rows, expected):
        identity = (source["source"], source["variant"])
        assert identity == (observed["source"], observed["variant"])
        assert identity == (saved["source"], saved["variant"])
        request, response = source["request"], observed["response"]
        assert response["status"] == saved["status"]
        assert response["diagnostics"] == saved["diagnostics"]
        wire = json.dumps(response, sort_keys=True, separators=(",", ":")).encode()
        assert hashlib.sha256(wire).hexdigest() == saved["responseSha256"]
        assert "sql" not in response
        if saved["status"] == "resolved":
            assert response["retainedModules"] == request["modules"]
            plan = response["logicalPlan"]
            assert plan["modulePins"] == [m["pin"] for m in request["modules"]]
            if packet == "application":
                assert plan["readProfile"] == request["readProfile"]
                if source["variant"] == "explicit-bounded-page-proposal":
                    assert plan["pageKey"]["id"] == "identity"
                    assert [f["element"] for f in plan["pageKey"]["fields"]] == ["UseCase.code"]
        else:
            assert "logicalPlan" not in response and "retainedModules" not in response


def main():
    packet, results_path = sys.argv[1:]
    assert packet in ("logical", "application")
    rows = json.loads(Path(results_path).read_text())
    assess(packet, rows)
    controls = [rows[:-1], rows + [rows[0]], list(reversed(rows))]
    for mutate in ("status", "pin", "source"):
        changed = copy.deepcopy(rows)
        if mutate == "status":
            changed[0]["response"]["status"] = "compiled"
        elif mutate == "source":
            changed[0]["source"] = "different-source"
        else:
            row = next(r for r in changed if r["response"]["status"] == "resolved")
            row["response"]["logicalPlan"]["modulePins"][0]["revision"] = "different"
        controls.append(changed)
    for changed in controls:
        try:
            assess(packet, changed)
        except AssertionError:
            continue
        raise AssertionError("Changed or incomplete observation was accepted")
    print(f"{packet}: {len(rows)} exact observations; six negative controls refused; frontend-only")


if __name__ == "__main__":
    main()
