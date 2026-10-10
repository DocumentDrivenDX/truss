"""Closed state-header source oracle; no native execution or authority claim."""
import copy
import hashlib
import json
import runpy
from pathlib import Path
h = runpy.run_path(str(Path(__file__).with_name("check-private-scalar-full-observation.py")))
require, native, strings, cast, function, literal = [h[k] for k in ["require", "native", "strings", "cast", "function", "literal"]]
BASE = h["BASE"]
NAME = "private-tree-state-observation-v0.1.proposal"
NAMES = ["state_id", "owner_kind", "object_id", "object_type_id", "edge_id", "relationship_type_id", "property_owner_type_id", "property_id", "root_node_id", "definition_bytes_hex", "home_profile_bytes_hex", "value_profile_bytes_hex", "state_source_bytes_hex"]
SOURCES = ["state_id", "owner_kind", "object_id", "object_type_id", "edge_id", "relationship_type_id", "property_owner_type_id", "property_id", "root_node_id", "definition_bytes", "home_profile_bytes", "value_profile_bytes", "source_bytes"]
def column(name): return {"ColumnRef": {"fields": strings("h", name)}}
expressions = [column(name) if i == 1 else function("encode", [column(name), literal("hex")]) if i >= 9 else cast(column(name), "text") for i, name in enumerate(SOURCES)]
EXPECTED = {"targetList": [{"ResTarget": {"name": name, "val": expr}} for name, expr in zip(NAMES, expressions)], "fromClause": [{"RangeVar": {"schemaname": "truss", "relname": "row_home_state", "inh": True, "relpersistence": "p", "alias": {"aliasname": "h"}}}], "whereClause": {"A_Expr": {"kind": "AEXPR_OP", "name": strings("="), "lexpr": column("state_id"), "rexpr": cast({"ParamRef": {"number": 1}}, "int8")}}, "limitCount": {"A_Const": {"ival": {"ival": 2}}}, "limitOption": "LIMIT_OPTION_COUNT", "op": "SETOP_NONE"}
def main():
    model = json.loads((BASE / (NAME + ".umf.json")).read_text())
    root = native(model["modules"][0]["elements"][0]["extensions"]["umf.postgresql"]["root"])
    require(len(root["stmts"]) == 1, "statement inventory")
    query = root["stmts"][0]["stmt"]["SelectStmt"]
    def audit(candidate): require(candidate == EXPECTED, "state header source substitution")
    audit(query)
    controls = []
    for label in ["swapped_owner_fields", "lost_home_profile", "wrong_definition_carrier", "narrow_state_parameter", "wrong_relation", "one_row_limit"]:
        changed = copy.deepcopy(query)
        if label == "swapped_owner_fields": changed["targetList"][3]["ResTarget"]["val"] = cast(column("relationship_type_id"), "text")
        elif label == "lost_home_profile": changed["targetList"].pop(10)
        elif label == "wrong_definition_carrier": changed["targetList"][9]["ResTarget"]["val"] = cast(column("definition_bytes"), "text")
        elif label == "narrow_state_parameter": changed["whereClause"]["A_Expr"]["rexpr"] = cast({"ParamRef": {"number": 1}}, "int4")
        elif label == "wrong_relation": changed["fromClause"][0]["RangeVar"]["relname"] = "row_home_node"
        else: changed["limitCount"]["A_Const"]["ival"]["ival"] = 1
        try: audit(changed)
        except ValueError: controls.append(label)
        else: raise ValueError("corruption passed: " + label)
    manifest = json.loads((BASE / "bindings" / (NAME + ".json")).read_text())
    def audit_manifest(candidate):
        for suffix, key in [("sql", "sourceSha256"), ("umf.json", "modelSha256")]: require(candidate[key] == hashlib.sha256((BASE / (NAME + "." + suffix)).read_bytes()).hexdigest(), key)
        require([(c["position"], c["name"]) for c in candidate["columns"]] == list(enumerate(NAMES)), "ordered columns")
        require(all(c["nativeResultType"] == "pg_catalog.text" and c["nativeNullPermitted"] is (i in {2,3,4,5}) for i,c in enumerate(candidate["columns"])), "carrier and NULL mask")
        require([(p["position"], p["nativeCast"]) for p in candidate["parameterSlots"]] == [(1,"pg_catalog.int8")], "parameters")
        require(candidate["status"] == "planned_unadopted" and candidate["nativeExecution"] is False and candidate["complete"] is False, "qualification inflation")
    audit_manifest(manifest)
    manifest_controls = []
    for label in ["nullable_root", "nonnull_object_pair", "extra_parameter", "native_claim"]:
        changed = copy.deepcopy(manifest)
        if label == "nullable_root": changed["columns"][8]["nativeNullPermitted"] = True
        elif label == "nonnull_object_pair": changed["columns"][2]["nativeNullPermitted"] = False
        elif label == "extra_parameter": changed["parameterSlots"].append({"position":2,"nativeCast":"pg_catalog.int8"})
        else: changed["nativeExecution"] = True
        try: audit_manifest(changed)
        except ValueError: manifest_controls.append(label)
        else: raise ValueError("manifest corruption passed: " + label)
    result = {"scope":"Closed state-header source AST and manifest ordered type/NULL/parameter/hash correspondence; no native owner association, authority or decoding", "sourceSha256":manifest["sourceSha256"], "modelSha256":manifest["modelSha256"], "columns":13, "corruptionControls":controls, "manifestCorruptionControls":manifest_controls, "nativeExecution":False, "complete":False}
    Path(__file__).with_name("private-tree-state-observation-oracle.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
