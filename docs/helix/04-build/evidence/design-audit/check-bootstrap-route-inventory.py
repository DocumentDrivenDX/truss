"""Draft route inventory/pin consistency only; no route decoder/native qualification."""
from pathlib import Path
import hashlib
import json
import platform

root = Path(__file__).resolve().parents[3]
bindings = root / "02-design/contracts/bindings"
names = ["cast", "collation", "external-collation", "enum", "external-enum", "enum-child", "range", "external-range", "operator", "opclass", "opfamily", "access-method", "opfamily-operators", "opfamily-support", "opfamily-operators-child", "opfamily-support-child", "type", "external-type", "routine", "external-routine", "language", "aggregate", "transform", "transform-pairs", "relation", "external-relation", "column", "external-column", "default", "index", "external-index", "sequence", "external-sequence", "constraint", "external-constraint", "trigger", "external-trigger", "policy", "external-policy", "rewrite", "external-rewrite", "trigger-child", "policy-child", "rewrite-child", "inheritance", "external-inheritance", "partition", "external-partition", "dependency", "shared-dependency", "namespace", "target-database", "session-settings", "tablespace", "description", "shared-description", "extension", "extension-reference", "default-acl", "namespace-acl", "routine-acl", "relation-acl", "column-acl", "type-acl", "language-acl", "namespace-rights", "routine-rights", "sequence-rights", "relation-rights", "column-rights", "type-rights", "language-rights", "role-path"]
def require(condition, message):
    if not condition:
        raise ValueError(message)
receipts = root / "04-build/evidence/design-audit"
queries = {}
for name in ["cast", "guard", "type", "external-type-adjunct", "enum-child", "operator", "opfamily-members", "opfamily-child", "external", "routine", "routine-ancillary", "transform", "collector", "external-relation", "default", "external-constraint-hierarchy", "external-relation-guards", "guard-child", "hierarchy", "namespace", "target-context", "tablespace", "metadata", "shared", "namespace-acl", "routine-acl", "relation-grants", "type-language-acl", "namespace-rights", "callable-sequence-rights", "table-rights", "type-language-rights", "role-path"]:
    for observation in json.loads((receipts / ("bootstrap-" + name + "-source.json")).read_text())["observations"]:
        require(observation["path"] not in queries, "duplicate receipt source")
        queries[observation["path"]] = observation
source_inventory_path = receipts / "bootstrap-source-inventory.json"
source_inventory_raw = source_inventory_path.read_bytes()
source_inventory = json.loads(source_inventory_raw)
require(not source_inventory["failures"], "source inventory has failures")
expected_queries = set()
for item in source_inventory["checked"]:
    receipt_path = Path(item["receiptPath"])
    if not receipt_path.is_absolute():
        receipt_path = root.parent.parent / receipt_path
    raw_receipt = receipt_path.read_bytes()
    require(hashlib.sha256(raw_receipt).hexdigest() == item["receiptSha256"], "stale aggregate source receipt")
    for observation in json.loads(raw_receipt)["observations"]:
        require(observation["path"] not in expected_queries, "duplicate aggregate query")
        expected_queries.add(observation["path"])
require(expected_queries == set(queries), "route source receipt group coverage differs from original aggregate")
checked = []
routed_queries = set()
identities = set()
definition_specification_pins = 0
field_handoffs = []
definition_routes = {"tablespace": "tablespace","transform": "transform", "transform-pairs": "transform","cast": "cast","range": "range", "external-range": "range","collation": "collation", "external-collation": "collation", "namespace": "namespace", "sequence": "sequence", "external-sequence": "sequence", "enum": "enum", "external-enum": "enum", "enum-child": "enum", "language": "language"}
inline_routes = {"relation", "external-relation","column", "external-column","index", "external-index","constraint", "external-constraint","trigger", "external-trigger", "trigger-child","policy", "external-policy", "policy-child","rewrite", "external-rewrite", "rewrite-child","aggregate","routine", "external-routine","type", "external-type","inheritance", "external-inheritance", "partition", "external-partition","default","operator","opfamily-operators", "opfamily-support", "opfamily-operators-child", "opfamily-support-child","access-method", "opclass", "opfamily","target-database", "session-settings","description", "shared-description", "namespace-rights", "routine-rights", "sequence-rights", "relation-rights", "column-rights", "type-rights", "language-rights", "role-path", "dependency", "shared-dependency", "extension", "extension-reference", "namespace-acl", "routine-acl", "relation-acl", "column-acl", "type-acl", "language-acl", "default-acl"}
required = {"interfaceVersion", "routeIdentity", "status", "nativeClass", "selector", "artifacts", "parameterGrammar", "orderedColumns", "coverage", "requiredKnownFields", "preservation", "dependencyExtraction", "adjuncts", "resourceProfile", "resourceObligations", "refusal"}
for name in names:
    path = bindings / ("bootstrap-" + name + "-route-v0.1.proposal.json")
    raw = path.read_bytes()
    entry = json.loads(raw)
    require(set(entry) == required, "route field inventory changed: " + name)
    require(entry["interfaceVersion"] == "truss-bootstrap-route-entry/0.1.0", "route envelope")
    require(entry["routeIdentity"] not in identities, "duplicate route identity")
    identities.add(entry["routeIdentity"])
    require(len(entry["artifacts"]) == 3, "artifact inventory")
    query_path = entry["artifacts"][0]["path"]
    require(query_path in queries, "query lacks scoped source receipt")
    require(query_path not in routed_queries, "duplicate original query route")
    routed_queries.add(query_path)
    original = queries[query_path]
    for artifact, (path_key, hash_key) in zip(entry["artifacts"], [("path", "sourceSha256"), ("artifactPath", "artifactSha256"), ("exportPath", "exportSha256")]):
        require(artifact["path"] == original[path_key] and artifact["sha256"] == original[hash_key], "source receipt mismatch")
        target = Path(artifact["path"])
        if not target.is_absolute():
            target = root.parent.parent / target
        require(hashlib.sha256(target.read_bytes()).hexdigest() == artifact["sha256"], "stale artifact")
    archive_path = Path(entry["artifacts"][1]["path"])
    if not archive_path.is_absolute():
        archive_path = root.parent.parent / archive_path
    model = json.loads(archive_path.read_text())
    native_root = model["modules"][0]["elements"][0]["extensions"]["umf.postgresql"]["root"]
    statements = native_root["members"]["stmts"]["items"]
    require(len(statements) == 1, "not one original statement")
    select = statements[0]["members"]["stmt"]["members"]["SelectStmt"]["members"]
    aliases = []
    for target in select["targetList"]["items"]:
        target_members = target["members"]["ResTarget"]["members"]
        alias = target_members.get("name")
        if alias is None:
            value = target_members["val"]["members"]
            require(set(value) == {"ColumnRef"}, "unnamed computed result is unsupported")
            fields = value["ColumnRef"]["members"]["fields"]["items"]
            require(fields and all(set(f["members"]) == {"String"} for f in fields), "unnamed wildcard result unsupported")
            alias = fields[-1]["members"]["String"]["members"]["sval"]
        require(alias["kind"] == "string", "result lacks admitted native name")
        aliases.append(alias["value"])
    require(entry["orderedColumns"] == aliases, "ordered result differs from original SELECT targetList")
    require(entry["nativeClass"]["namespace"] == "pg_catalog" and entry["nativeClass"]["storageScope"] in {"database", "shared"}, "catalog scope")
    require(entry["resourceProfile"] == "truss-bootstrap-collector-resource/0.1.0", "resource profile")
    for key in ["orderedColumns", "requiredKnownFields", "adjuncts"]:
        require(entry[key] and len(set(entry[key])) == len(entry[key]), "empty/duplicate route list: " + key)
    require(entry["dependencyExtraction"] and entry["coverage"] and entry["refusal"], "missing semantic handoff")
    specification = entry["dependencyExtraction"].get("definitionSpecification")
    require((specification is not None) == (name in definition_routes), "definition specification inventory changed")
    if specification is not None:
        require(set(specification) == {"path", "sha256", "admission"}, "definition pin fields")
        expected = bindings / ("bootstrap-" + definition_routes[name] + "-definition-v0.1.proposal.json")
        require(specification["path"] == str(expected.relative_to(root.parent.parent)), "wrong definition specification")
        require(hashlib.sha256(expected.read_bytes()).hexdigest() == specification["sha256"], "stale definition specification")
        profile = json.loads(expected.read_text())
        fields = [f["nativeField"] for f in profile["fields"]]
        require(len(fields) == len(set(fields)) and len(profile["requiredRawFieldInventory"]) == len(set(profile["requiredRawFieldInventory"])) and set(fields) == set(profile["requiredRawFieldInventory"]), "definition field inventory mismatch")
        require(set(profile["requiredRawFieldInventory"]) == set(entry["requiredKnownFields"]), "definition differs from route required native fields")
        require(profile["interfaceVersion"] == "truss-bootstrap-" + definition_routes[name] + "-definition-profile/0.1.0", "wrong definition profile version")
        for field in profile["fields"]:
            require(all(isinstance(field.get(key), str) and field[key].strip() for key in (["nativeField", "domain", "meaning", "rawPreservation"] if definition_routes[name] == "sequence" else ["nativeField", "domain", "classification", "projection"] if definition_routes[name] in {"enum", "namespace"} else ["nativeField", "domain", "classification", "rawPreservation"])), "empty definition field admission")
        require(isinstance(profile.get("unknownFields"), str) and profile["unknownFields"].strip(), "missing unknown field policy")
        definition_specification_pins += 1
    inline_fields = entry["dependencyExtraction"].get("fieldClassification")
    require((inline_fields is not None) == (name in inline_routes), "inline classification inventory changed")
    if inline_fields is not None:
        require(isinstance(inline_fields, dict) and set(inline_fields) == set(entry["requiredKnownFields"]), "inline classification differs from required native fields")
        require(all(isinstance(value, str) and value.strip() for value in inline_fields.values()), "blank inline classification")
        require(isinstance(entry["dependencyExtraction"].get("canonicalProcedure"), str) and entry["dependencyExtraction"]["canonicalProcedure"].strip(), "missing inline canonical procedure")
    field_handoffs.append({"route": name, "routeIdentity": entry["routeIdentity"], "routePath": str(path.relative_to(root.parent.parent)), "routeSha256": hashlib.sha256(raw).hexdigest(), "requiredKnownFields": entry["requiredKnownFields"], "fieldSpecification": specification, "inlineFieldClassification": inline_fields, "interpretationStatus": "authored unadopted field specification; original native/canonical/dependency producers still open" if specification else "authored inline field classification/procedure; original native/canonical producers still open" if inline_fields else "no separately pinned field specification; inspect governing route/contract before authoring, existing interpretation may be inline", "requiredClosure": ["original descriptor/raw/projected-carrier correspondence", "total stable/operational/preserved-unsupported classification", "complete original reference/adjunct/authority closure", "canonical producer and relevant executable/comparator/environment qualification", "selected target/cut/resource/termination custody"]})
    checked.append({"path": str(path.relative_to(root)), "routeIdentity": entry["routeIdentity"], "sha256": hashlib.sha256(raw).hexdigest()})
require(routed_queries == expected_queries, "original source query lacks route")
actual = {p.name for p in bindings.glob("bootstrap-*-route-v0.1.proposal.json")}
require(actual == {"bootstrap-" + n + "-route-v0.1.proposal.json" for n in names}, "unreviewed route inventory")
result = {"scope": "Seventy-three draft route entry identities/required-field/list inventories, original top-level SELECT target aliases and 219 source/model/export pins against scoped receipts and current bytes, with exact path-set coverage of the original aggregate source query inventory; no query parsing, exact semantic decoder/extractor, mandatory closure, registry adoption or native support proof", "status": "pass", "routes": checked, "artifactPins": 3 * len(checked), "sourceQueriesCovered": len(routed_queries), "definitionSpecificationPins": definition_specification_pins, "sourceInventorySha256": hashlib.sha256(source_inventory_raw).hexdigest(), "checkerSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "pythonVersion": platform.python_version()}
Path(__file__).with_name("bootstrap-route-inventory.json").write_text(json.dumps(result, indent=2) + "\n")
handoff_output = {"scope": "Current authored route required-field and separate specification inventory only; unpinned routes may have inline governing procedures and are not automatically missing semantics. No complete design/adoption/native qualification claim", "routes": field_handoffs, "routeCount": len(field_handoffs), "separateSpecificationReferences": definition_specification_pins, "distinctSpecificationPaths": sorted({item["fieldSpecification"]["path"] for item in field_handoffs if item["fieldSpecification"]}), "inlineClassificationRoutes": sorted(inline_routes), "withoutExplicitClassification": [item["route"] for item in field_handoffs if not item["fieldSpecification"] and not item["inlineFieldClassification"]], "withoutSeparateSpecification": [item["route"] for item in field_handoffs if not item["fieldSpecification"]], "routeInventorySha256": hashlib.sha256(Path(__file__).with_name("bootstrap-route-inventory.json").read_bytes()).hexdigest(), "checkerSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
Path(__file__).with_name("bootstrap-field-handoffs.json").write_text(json.dumps(handoff_output, indent=2) + "\n")
print(json.dumps({"routes": len(checked), "artifactPins": result["artifactPins"], "status": "pass"}))
