"""Closed owner/property selector oracle; no native association/visibility proof."""
import copy
import hashlib
import json
import runpy
from pathlib import Path
h = runpy.run_path(str(Path(__file__).with_name("check-private-tree-state-observation.py")))
require, native, strings, cast, literal, column = [h[k] for k in ["require", "native", "strings", "cast", "literal", "column"]]
BASE, NAME = h["BASE"], "private-property-state-observation-v0.1.proposal"
def eq(left, right): return {"A_Expr": {"kind":"AEXPR_OP", "name":strings("="), "lexpr":left, "rexpr":right}}
expected = []
for kind, identity, discriminator in [("object","object_id","object_type_id"),("edge","edge_id","relationship_type_id")]:
    query = copy.deepcopy(h["EXPECTED"])
    predicates = [eq(column("owner_kind"), cast(literal(kind), "text"))]
    predicates += [eq(column(name), cast({"ParamRef":{"number":slot}}, "int8" if slot == 1 else "int4")) for slot,name in enumerate([identity, discriminator, "property_owner_type_id", "property_id"],1)]
    query["whereClause"] = {"BoolExpr":{"boolop":"AND_EXPR","args":predicates}}
    expected.append(query)
def main():
    model = json.loads((BASE/(NAME+".umf.json")).read_text())
    root = native(model["modules"][0]["elements"][0]["extensions"]["umf.postgresql"]["root"])
    queries = [s["stmt"]["SelectStmt"] for s in root["stmts"]]
    def audit(candidate): require(candidate == expected, "owner/property route substitution")
    audit(queries)
    controls = []
    for label in ["missing_edge_route", "edge_as_object", "relationship_as_property_owner", "missing_property", "foreign_owner_slot", "one_row_limit"]:
        changed = copy.deepcopy(queries)
        if label == "missing_edge_route": changed.pop()
        elif label == "edge_as_object": changed[1]["whereClause"]["BoolExpr"]["args"][0] = expected[0]["whereClause"]["BoolExpr"]["args"][0]
        elif label == "relationship_as_property_owner": changed[1]["whereClause"]["BoolExpr"]["args"][3]["A_Expr"]["lexpr"] = column("relationship_type_id")
        elif label == "missing_property": changed[0]["whereClause"]["BoolExpr"]["args"].pop()
        elif label == "foreign_owner_slot": changed[1]["whereClause"]["BoolExpr"]["args"][1]["A_Expr"]["rexpr"] = cast({"ParamRef":{"number":3}}, "int8")
        else: changed[1]["limitCount"]["A_Const"]["ival"]["ival"] = 1
        try: audit(changed)
        except ValueError: controls.append(label)
        else: raise ValueError("corruption passed: "+label)
    manifest = json.loads((BASE/"bindings"/(NAME+".json")).read_text())
    def audit_manifest(candidate):
        for suffix,key in [("sql","sourceSha256"),("umf.json","modelSha256")]: require(candidate[key] == hashlib.sha256((BASE/(NAME+"."+suffix)).read_bytes()).hexdigest(), key)
        require(len(candidate["statements"]) == 2, "statement membership")
        for ordinal,entry in enumerate(candidate["statements"]):
            require((entry["ordinal"],entry["ownerKind"]) == (ordinal,["object","edge"][ordinal]), "route identity")
            require([(p["position"],p["nativeCast"]) for p in entry["parameterSlots"]] == [(1,"pg_catalog.int8"),(2,"pg_catalog.int4"),(3,"pg_catalog.int4"),(4,"pg_catalog.int4")], "parameter inventory")
            require([(c["position"],c["name"]) for c in entry["columns"]] == list(enumerate(h["NAMES"])), "ordered columns")
            require(all(c["nativeResultType"] == "pg_catalog.text" and c["nativeNullPermitted"] is (i in {2,3,4,5}) for i,c in enumerate(entry["columns"])), "carrier/NULL mask")
        require(candidate["nativeExecution"] is False and candidate["complete"] is False and candidate["status"] == "planned_unadopted", "qualification inflation")
    audit_manifest(manifest)
    manifest_controls = []
    for label in ["route_kind_swap", "changed_catalog_cast", "missing_owner_parameter", "nullable_property", "complete_claim"]:
        changed = copy.deepcopy(manifest)
        if label == "route_kind_swap": changed["statements"][1]["ownerKind"] = "object"
        elif label == "changed_catalog_cast": changed["statements"][1]["parameterSlots"][2]["nativeCast"] = "pg_catalog.numeric"
        elif label == "missing_owner_parameter": changed["statements"][0]["parameterSlots"].pop(2)
        elif label == "nullable_property": changed["statements"][1]["columns"][7]["nativeNullPermitted"] = True
        else: changed["complete"] = True
        try: audit_manifest(changed)
        except ValueError: manifest_controls.append(label)
        else: raise ValueError("manifest corruption passed: "+label)
    result = {"scope":"Closed two-route source AST and manifest source/order/carrier/NULL/parameter correspondence; no native owner association, complete visibility or absence proof", "sourceSha256":manifest["sourceSha256"], "modelSha256":manifest["modelSha256"], "statements":2, "corruptionControls":controls, "manifestCorruptionControls":manifest_controls, "nativeExecution":False, "complete":False}
    Path(__file__).with_name("private-property-state-observation-oracle.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
