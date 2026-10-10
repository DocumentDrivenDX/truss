"""Independent two-stream source/transport oracle; no native execution."""
import copy
import hashlib
import json
import runpy
from pathlib import Path
helpers = runpy.run_path(str(Path(__file__).with_name("check-private-scalar-full-observation.py")))
require, native, strings, cast, function, literal = [helpers[k] for k in ["require", "native", "strings", "cast", "function", "literal"]]
BASE = helpers["BASE"]
name = "private-tree-full-observation-v0.1.proposal"
def col(alias, name): return {"ColumnRef": {"fields": strings(alias, name)}}
def stream(relation, alias, targets):
    return {"targetList": [{"ResTarget": {"name": n, "val": e}} for n, e in targets], "fromClause": [{"RangeVar": {"schemaname": "truss", "relname": relation, "inh": True, "relpersistence": "p", "alias": {"aliasname": alias}}}], "whereClause": {"A_Expr": {"kind": "AEXPR_OP", "name": strings("="), "lexpr": col(alias, "state_id"), "rexpr": cast({"ParamRef": {"number": 1}}, "int8")}}, "sortClause": [{"SortBy": {"node": col(alias, "node_id"), "sortby_dir": "SORTBY_DEFAULT", "sortby_nulls": "SORTBY_NULLS_DEFAULT"}}], "limitOption": "LIMIT_OPTION_DEFAULT", "op": "SETOP_NONE"}
names = ["state_id", "node_id", "parent_node_id", "slot_kind", "sequence_ordinal", "map_key", "record_field_identity_hex", "value_kind", "definition_bytes_hex", "node_source_bytes_hex"]
expressions = [cast(col("n", "state_id"), "text"), cast(col("n", "node_id"), "text"), cast(col("n", "parent_node_id"), "text"), col("n", "slot_kind"), cast(col("n", "sequence_ordinal"), "text"), col("n", "map_key"), function("encode", [col("n", "record_field_identity_bytes"), literal("hex")]), col("n", "value_kind"), function("encode", [col("n", "definition_bytes"), literal("hex")]), function("encode", [col("n", "source_bytes"), literal("hex")])]
expected = [stream("row_home_node", "n", zip(names, expressions)), stream("row_home_scalar", "s", zip(helpers["NAMES"], helpers["EXPRESSIONS"]))]
model_path = BASE / (name + ".umf.json")
model = json.loads(model_path.read_text())
root = native(model["modules"][0]["elements"][0]["extensions"]["umf.postgresql"]["root"])
queries = [s["stmt"]["SelectStmt"] for s in root["stmts"]]
def audit(candidate): require(candidate == expected, "two-stream query substitution")
audit(queries)
controls = []
for label in ["missing_stream", "state_scope_swap", "scalar_node_filter", "truncated_nodes", "lost_orphan_payload"]:
    changed = copy.deepcopy(queries)
    if label == "missing_stream": changed.pop()
    elif label == "state_scope_swap": changed[1]["whereClause"]["A_Expr"]["rexpr"]["TypeCast"]["arg"]["ParamRef"]["number"] = 2
    elif label == "scalar_node_filter": changed[1]["whereClause"]["A_Expr"]["lexpr"] = col("s", "node_id")
    elif label == "truncated_nodes": changed[0]["limitCount"] = {"A_Const": {"ival": {"ival": 2}}}
    else: changed[1]["targetList"].pop(12)
    try: audit(changed)
    except ValueError: controls.append(label)
    else: raise ValueError("corruption passed: " + label)
manifest = json.loads((BASE / "bindings" / (name + ".json")).read_text())
def audit_manifest(candidate):
    for suffix, key in [("sql", "sourceSha256"), ("umf.json", "modelSha256")]:
        require(candidate[key] == hashlib.sha256((BASE / (name + "." + suffix)).read_bytes()).hexdigest(), key)
    require(len(candidate["statements"]) == 2, "manifest statement membership")
    families = [("all_state_nodes", "truss.row_home_node"), ("all_state_scalar_payloads", "truss.row_home_scalar")]
    nullables = [{2, 4, 5, 6}, {3, 4, 5, 6, 7, 8, 9, 10}]
    for ordinal, (entry, columns) in enumerate(zip(candidate["statements"], [names, helpers["NAMES"]])):
        require(entry["ordinal"] == ordinal and (entry["family"], entry["relation"]) == families[ordinal], "manifest statement identity")
        require([(c["position"], c["name"]) for c in entry["columns"]] == list(enumerate(columns)), "manifest ordered membership")
        require(all(c["nativeResultType"] == "pg_catalog.text" and c["nativeNullPermitted"] is (i in nullables[ordinal]) for i, c in enumerate(entry["columns"])), "result carrier/NULL mask")
        require([(p["position"], p["nativeCast"]) for p in entry["parameterSlots"]] == [(1, "pg_catalog.int8")], "manifest scope")
    require(candidate["status"] == "planned_unadopted" and candidate["nativeExecution"] is False and candidate["complete"] is False, "qualification inflation")
audit_manifest(manifest)
manifest_controls = []
for label in ["stream_identity_swap", "nullable_node_definition", "nonnull_parent", "binary_native_carrier", "scalar_node_parameter", "native_claim"]:
    changed = copy.deepcopy(manifest)
    if label == "stream_identity_swap": changed["statements"][0]["family"] = "all_state_scalar_payloads"
    elif label == "nullable_node_definition": changed["statements"][0]["columns"][8]["nativeNullPermitted"] = True
    elif label == "nonnull_parent": changed["statements"][0]["columns"][2]["nativeNullPermitted"] = False
    elif label == "binary_native_carrier": changed["statements"][1]["columns"][7]["nativeResultType"] = "pg_catalog.bytea"
    elif label == "scalar_node_parameter": changed["statements"][1]["parameterSlots"].append({"position":2,"nativeCast":"pg_catalog.int8"})
    else: changed["complete"] = True
    try: audit_manifest(changed)
    except ValueError: manifest_controls.append(label)
    else: raise ValueError("manifest corruption passed: " + label)

result = {"scope": "Two complete fixed source ASTs and manifest source/order/type/NULL/parameter correspondence only; no native visibility, bounds, descriptors or decoding", "sourceSha256": manifest["sourceSha256"], "modelSha256": manifest["modelSha256"], "statements": 2, "corruptionControls": controls, "manifestCorruptionControls": manifest_controls, "nativeExecution": False, "complete": False}
Path(__file__).with_name("private-tree-full-observation-oracle.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
