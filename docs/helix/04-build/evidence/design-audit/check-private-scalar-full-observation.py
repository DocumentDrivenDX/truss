"""Closed source-AST oracle; no native execution or decoder qualification."""
import copy
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/helix/02-design/contracts"

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def native(value):
    kind = value["kind"]
    if kind == "object":
        return {key: native(item) for key, item in value["members"].items() if key != "location"}
    if kind == "array":
        return [native(item) for item in value["items"]]
    if kind == "number":
        return int(value["value"])
    return value.get("value")

def strings(*names):
    return [{"String": {"sval": name}} for name in names]

def column(name):
    return {"ColumnRef": {"fields": strings("s", name)}}

def cast(expression, type_name):
    return {"TypeCast": {"arg": expression, "typeName": {"names": strings("pg_catalog", type_name), "typemod": -1}}}

def literal(value):
    return {"A_Const": {"sval": {"sval": value}}}

def function(name, args):
    return {"FuncCall": {"funcname": strings("pg_catalog", name), "args": args, "funcformat": "COERCE_EXPLICIT_CALL"}}

NAMES = ["state_id", "node_id", "scalar_kind", "text_value", "boolean_value", "native_numeric_text", "original_numeric_token", "binary_value_hex", "temporal_text", "temporal_instant_text", "opaque_bytes_hex", "codec_bytes_hex", "source_bytes_hex", "metadata_date_style", "metadata_time_zone"]
EXPRESSIONS = [cast(column("state_id"), "text"), cast(column("node_id"), "text"), column("scalar_kind"), column("text_value"), cast(column("boolean_value"), "text"), cast(column("numeric_value"), "text"), column("numeric_token"), function("encode", [column("binary_value"), literal("hex")]), column("temporal_text"), cast(column("temporal_instant"), "text"), function("encode", [column("opaque_bytes"), literal("hex")]), function("encode", [column("codec_definition_bytes"), literal("hex")]), function("encode", [column("original_source_bytes"), literal("hex")]), function("current_setting", [literal("DateStyle")]), function("current_setting", [literal("TimeZone")])]
EXPECTED = {"targetList": [{"ResTarget": {"name": name, "val": expr}} for name, expr in zip(NAMES, EXPRESSIONS)], "fromClause": [{"RangeVar": {"schemaname": "truss", "relname": "row_home_scalar", "inh": True, "relpersistence": "p", "alias": {"aliasname": "s"}}}], "whereClause": {"BoolExpr": {"boolop": "AND_EXPR", "args": [{"A_Expr": {"kind": "AEXPR_OP", "name": strings("="), "lexpr": column(name), "rexpr": cast({"ParamRef": {"number": slot}}, "int8")}} for slot, name in enumerate(["state_id", "node_id"], 1)]}}, "limitCount": {"A_Const": {"ival": {"ival": 2}}}, "limitOption": "LIMIT_OPTION_COUNT", "op": "SETOP_NONE"}

def audit(query):
    require(query == EXPECTED, "Source query differs from closed independently authored projection/predicate oracle")

def main():
    model_path = BASE / "private-scalar-full-observation-v0.1.proposal.umf.json"
    model = json.loads(model_path.read_text())
    root = native(model["modules"][0]["elements"][0]["extensions"]["umf.postgresql"]["root"])
    require(len(root["stmts"]) == 1, "statement inventory")
    query = root["stmts"][0]["stmt"]["SelectStmt"]
    audit(query)
    controls = []
    for label in ["reordered_columns", "lost_source_bytes", "wrong_binary_carrier", "missing_node_predicate", "one_row_limit", "hidden_filter", "source_as_codec"]:
        altered = copy.deepcopy(query)
        if label == "reordered_columns": altered["targetList"][0], altered["targetList"][1] = altered["targetList"][1], altered["targetList"][0]
        elif label == "lost_source_bytes": altered["targetList"].pop(12)
        elif label == "wrong_binary_carrier": altered["targetList"][7]["ResTarget"]["val"] = cast(column("binary_value"), "text")
        elif label == "missing_node_predicate": altered["whereClause"]["BoolExpr"]["args"].pop()
        elif label == "one_row_limit": altered["limitCount"]["A_Const"]["ival"]["ival"] = 1
        elif label == "hidden_filter": altered["targetList"][7]["ResTarget"]["val"]["FuncCall"]["agg_filter"] = literal("true")
        else: altered["targetList"][11]["ResTarget"]["val"] = function("encode", [column("original_source_bytes"), literal("hex")])
        try:
            audit(altered)
        except ValueError:
            controls.append(label)
        else:
            raise ValueError("Corruption passed: " + label)
    manifest_path = BASE / "bindings/private-scalar-full-observation-v0.1.proposal.json"
    manifest = json.loads(manifest_path.read_text())
    source_path = BASE / "private-scalar-full-observation-v0.1.proposal.sql"
    def audit_manifest(candidate):
        require(candidate["sourceSha256"] == hashlib.sha256(source_path.read_bytes()).hexdigest(), "source pin")
        require(candidate["modelSha256"] == hashlib.sha256(model_path.read_bytes()).hexdigest(), "model pin")
        require([(c["position"], c["name"]) for c in candidate["columns"]] == list(enumerate(NAMES)), "manifest column order")
        require(all(c["nativeResultType"] == "pg_catalog.text" for c in candidate["columns"]), "result carrier type")
        nonnull = {0, 1, 2, 11, 12, 13, 14}
        require(all(c["nativeNullPermitted"] is (i not in nonnull) for i, c in enumerate(candidate["columns"])), "native NULL mask")
        require([(p["position"], p["nativeCast"]) for p in candidate["parameterSlots"]] == [(1, "pg_catalog.int8"), (2, "pg_catalog.int8")], "parameter inventory")
        require(candidate["nativeExecution"] is False and candidate["complete"] is False and candidate["status"] == "planned_unadopted", "qualification inflation")
    audit_manifest(manifest)
    manifest_controls = []
    for label in ["native_bytea_result", "nullable_codec", "nonnull_unused_binary", "missing_parameter", "narrow_identity_cast", "native_claim_inflation"]:
        altered = copy.deepcopy(manifest)
        if label == "native_bytea_result": altered["columns"][7]["nativeResultType"] = "pg_catalog.bytea"
        elif label == "nullable_codec": altered["columns"][11]["nativeNullPermitted"] = True
        elif label == "nonnull_unused_binary": altered["columns"][7]["nativeNullPermitted"] = False
        elif label == "missing_parameter": altered["parameterSlots"].pop()
        elif label == "narrow_identity_cast": altered["parameterSlots"][1]["nativeCast"] = "pg_catalog.int4"
        else: altered["nativeExecution"] = True
        try:
            audit_manifest(altered)
        except ValueError:
            manifest_controls.append(label)
        else:
            raise ValueError("Manifest corruption passed: " + label)

    result = {"scope": "Closed captured source projection/predicate AST and manifest source/order/type/null/parameter correspondence only; no native descriptors, visibility, decoding or PostgreSQL execution", "sourceSha256": manifest["sourceSha256"], "modelSha256": manifest["modelSha256"], "columns": 15, "corruptionControls": controls, "manifestCorruptionControls": manifest_controls, "nativeExecution": False, "complete": False}
    Path(__file__).with_name("private-scalar-full-observation-oracle.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
