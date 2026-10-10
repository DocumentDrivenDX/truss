"""Closed complete-owner enumeration oracle; no native view/completeness claim."""
import copy
import hashlib
import json
import runpy
from pathlib import Path
h = runpy.run_path(str(Path(__file__).with_name("check-private-property-state-observation.py")))
require,native,column,cast,strings = [h[k] for k in ["require","native","column","cast","strings"]]
BASE, NAME = h["BASE"], "private-owner-states-observation-v0.1.proposal"
ORDER = ["property_owner_type_id","property_id","state_id"]
expected = copy.deepcopy(h["expected"])
for query in expected:
    query["whereClause"]["BoolExpr"]["args"] = query["whereClause"]["BoolExpr"]["args"][:3]
    del query["limitCount"]
    query["limitOption"] = "LIMIT_OPTION_DEFAULT"
    query["sortClause"] = [{"SortBy":{"node":column(name),"sortby_dir":"SORTBY_DEFAULT","sortby_nulls":"SORTBY_NULLS_DEFAULT"}} for name in ORDER]
model = json.loads((BASE/(NAME+".umf.json")).read_text())
root = native(model["modules"][0]["elements"][0]["extensions"]["umf.postgresql"]["root"])
queries = [s["stmt"]["SelectStmt"] for s in root["stmts"]]
def audit(candidate): require(candidate == expected, "complete-owner source substitution")
audit(queries)
controls = []
for label in ["missing_route","property_filter","row_limit","text_collection_sort","lost_profile_bytes","owner_discriminator_swap"]:
    changed = copy.deepcopy(queries)
    if label == "missing_route": changed.pop()
    elif label == "property_filter": changed[1]["whereClause"]["BoolExpr"]["args"].append(h["expected"][1]["whereClause"]["BoolExpr"]["args"][4])
    elif label == "row_limit": changed[0]["limitCount"] = {"A_Const":{"ival":{"ival":2}}}
    elif label == "text_collection_sort": changed[0]["sortClause"][0]["SortBy"]["node"] = cast(column(ORDER[0]),"text")
    elif label == "lost_profile_bytes": changed[1]["targetList"].pop(11)
    else: changed[1]["whereClause"]["BoolExpr"]["args"][2]["A_Expr"]["lexpr"] = column("property_owner_type_id")
    try: audit(changed)
    except ValueError: controls.append(label)
    else: raise ValueError("corruption passed: "+label)
manifest = json.loads((BASE/"bindings"/(NAME+".json")).read_text())
def audit_manifest(candidate):
    for suffix,key in [("sql","sourceSha256"),("umf.json","modelSha256")]: require(candidate[key] == hashlib.sha256((BASE/(NAME+"."+suffix)).read_bytes()).hexdigest(),key)
    require(len(candidate["statements"]) == 2,"route membership")
    for ordinal,entry in enumerate(candidate["statements"]):
        require((entry["ordinal"],entry["ownerKind"]) == (ordinal,["object","edge"][ordinal]),"route identity")
        require([(p["position"],p["nativeCast"]) for p in entry["parameterSlots"]] == [(1,"pg_catalog.int8"),(2,"pg_catalog.int4")],"typed owner scope")
        require([(c["position"],c["name"]) for c in entry["columns"]] == list(enumerate(h["h"]["NAMES"])),"ordered header")
        require(all(c["nativeResultType"] == "pg_catalog.text" and c["nativeNullPermitted"] is (i in {2,3,4,5}) for i,c in enumerate(entry["columns"])),"type/NULL mask")
        require(entry["collectionOrder"] == ORDER,"native order inventory")
    require(candidate["nativeExecution"] is False and candidate["complete"] is False and candidate["status"] == "planned_unadopted","qualification inflation")
audit_manifest(manifest)
manifest_controls = []
for label in ["route_swap","extra_property_parameter","nullable_definition","missing_order_component","native_claim"]:
    changed = copy.deepcopy(manifest)
    if label == "route_swap": changed["statements"][1]["ownerKind"] = "object"
    elif label == "extra_property_parameter": changed["statements"][1]["parameterSlots"].append({"position":3,"nativeCast":"pg_catalog.int4"})
    elif label == "nullable_definition": changed["statements"][0]["columns"][9]["nativeNullPermitted"] = True
    elif label == "missing_order_component": changed["statements"][0]["collectionOrder"].pop()
    else: changed["nativeExecution"] = True
    try: audit_manifest(changed)
    except ValueError: manifest_controls.append(label)
    else: raise ValueError("manifest corruption passed: "+label)
result = {"scope":"Two complete-owner source ASTs and manifest source/order/type/NULL/parameter correspondence only; no native complete visibility, ownership, resource or whole-record decoding qualification","sourceSha256":manifest["sourceSha256"],"modelSha256":manifest["modelSha256"],"statements":2,"corruptionControls":controls,"manifestCorruptionControls":manifest_controls,"nativeExecution":False,"complete":False}
Path(__file__).with_name("private-owner-states-observation-oracle.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result))
