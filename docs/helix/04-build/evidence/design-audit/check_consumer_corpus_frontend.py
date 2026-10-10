"""Prepare/assess all original corpus SQL through the isolated test frontend."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
BLOCKED = {
    "read.relationship-filter-both-directions:0",
    "read.relationship-filter-both-directions:1",
    "read.relationship-filter-both-directions:2",
    "read.repeated-relationship-predicates-mean-both:2",
    "read.repeated-relationship-predicates-mean-both:3",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inputs():
    inventory = json.loads((HERE / "consumer-corpus-source-review.json").read_text())
    source = inventory["sources"][0]
    raw = Path(source["path"]).read_bytes()
    assert digest(raw) == source["sha256"]
    corpus = json.loads(raw)
    saved = (HERE / "consumer-logical-frontend-inputs.json").read_bytes()
    receipt = json.loads((HERE / "consumer-logical-frontend.json").read_text())
    assert digest(saved) == receipt["inputsSha256"]
    models = [m for m in json.loads(saved) if m["variant"] == "proposed"]
    queries = [(c["id"], i, s) for c in corpus["cases"] for i, s in enumerate(c["steps"]) if s["op"] == "query"]
    assert len(models) == 2 and len(queries) == 45
    cases = []
    for model in models:
        for case, index, step in queries:
            assert not step.get("params")
            request = copy.deepcopy(model["request"])
            request.update(dialect="weft-sql/0.2.0", sql=step["sql"], parameters={})
            cases.append({"source": model["source"], "variant": f"{case}:{index}", "request": request})
    return cases, source, receipt


def main():
    action, workspace = sys.argv[1:]
    workspace = Path(workspace)
    cases, source, pin = inputs()
    wire = json.dumps(cases).encode()
    target = workspace / "truss-consumer-frontend-inputs.json"
    if action == "prepare":
        target.write_bytes(wire)
        shutil.copyfile(HERE / "consumer-logical-frontend-harness.rs", workspace / "crates/weft-core/tests/truss_consumer_review.rs")
        print("Prepared 90 original SQL inputs; explicit named proposals; no bounded profile")
        return
    assert action == "assess" and target.read_bytes() == wire
    rows = json.loads((workspace / "crates/weft-core/truss-consumer-frontend-results.json").read_text())
    assert len(rows) == len(cases) == 90
    assert len({(r["source"], r["variant"]) for r in rows}) == 90
    observations = []
    for case, row in zip(cases, rows):
        assert (case["source"], case["variant"]) == (row["source"], row["variant"])
        response = row["response"]
        blocked = case["variant"] in BLOCKED
        assert response["status"] == ("blocked" if blocked else "resolved")
        assert "sql" not in response
        if blocked:
            assert [d["code"] for d in response["diagnostics"]] == ["WFT-NAME-MISSING"]
        else:
            assert response["diagnostics"] == []
            assert response["retainedModules"] == case["request"]["modules"]
            assert response["logicalPlan"]["modulePins"] == [m["pin"] for m in case["request"]["modules"]]
        observations.append({"source": row["source"], "caseStep": row["variant"], "sql": case["request"]["sql"], "status": response["status"], "diagnostics": response["diagnostics"], "responseSha256": digest(json.dumps(response, sort_keys=True, separators=(",", ":")).encode())})
    assert digest((workspace / "Cargo.lock").read_bytes()) == pin["cargoLockSha256"]
    receipt = {"scope": "All original consumer corpus SQL steps on two named proposals; Rust test frontend dialect 0.2 without bounded read profile; no execution, SQL lowering or adapter qualification", "revision": pin["revision"], "sourceArchiveSha256": pin["sourceArchiveSha256"], "corpus": source, "querySteps": 45, "distinctSql": len({c["request"]["sql"] for c in cases}), "inputsSha256": digest(wire), "checkerSha256": digest(Path(__file__).read_bytes()), "resolved": 80, "blocked": 10, "observations": observations, "nativeImplementationQualified": False}
    (HERE / "consumer-corpus-frontend.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("90 exact query observations assessed: 80 resolved, 10 relationship-equality refusals")


if __name__ == "__main__":
    main()
