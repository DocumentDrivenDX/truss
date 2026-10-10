"""Compare historical review ASTs only; never selects or applies a migration."""
import copy
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
MODELS = REPO / "docs/helix/02-design/models"
paths = [MODELS / "truss-layout-qualified-property-0.15.proposal.umf.json",
         MODELS / "truss-layout-source-epoch-0.16.proposal.umf.json"]
documents = [json.loads(p.read_bytes()) for p in paths]


def statements(document):
    return document["modules"][0]["elements"][0]["extensions"]["umf.postgresql"]["root"]["members"]["stmts"]["items"]


source, target = map(statements, documents)
assert len(source) == 109 and len(target) == 112
left, right = copy.deepcopy(source), copy.deepcopy(target[:109])
for rows in (left, right):
    comment = rows[1]["members"]["stmt"]["members"]["CommentStmt"]["members"]["comment"]
    assert "REVIEW ONLY - unqualified" in comment["value"]
    comment["value"] = "explicitly excluded review comment"
assert left == right
added = []
for index, node in enumerate(target[109:], 109):
    statement = node["members"]["stmt"]["members"]
    kind = next(iter(statement))
    fields = statement[kind]["members"]
    name = fields["relation"]["members"]["relname"]["value"] if kind == "CreateStmt" else None
    added.append({"statementIndex": index, "nativeKind": kind, "relation": name,
                  "astSha256": hashlib.sha256(json.dumps(node, sort_keys=True, separators=(",", ":")).encode()).hexdigest()})
assert [r["relation"] for r in added] == ["source_epoch_registry", "source_epoch_current", None]
assert added[-1]["nativeKind"] == "GrantStmt"
export = REPO / "docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql"
assert export.read_text().rstrip().endswith("REVOKE ALL ON truss.source_epoch_registry, truss.source_epoch_current FROM public")
receipt = {"scope": "historical review-model structural candidate delta only; no complete installed source/target pair, conversion or route selection",
           "sources": [{"path": str(p.relative_to(REPO)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in [*paths, export]],
           "commonStatements": 109, "excludedDifference": "review-only schema comment",
           "addedStatements": added, "privilegeEffect": "revoke all on both epoch tables from public",
           "missingRouteComposition": ["complete installed routine/dependency/authority/resource profiles", "original epoch initialization and historical token/report/feed preservation", "registered original recovery/request/receipt homes and target publication", "independent populated preservation and fault expectations"],
           "m1Selected": False, "nativeImplementationQualified": False}
Path(__file__).with_name("migration-epoch-candidate-delta.json").write_text(json.dumps(receipt, indent=2) + "\n")
print("109 prior review statements retained except comment; two epoch tables and REVOKE appended; M1 remains unselected")
