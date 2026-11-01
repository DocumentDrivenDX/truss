import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import patch

from truss._migration_recipe import plan_route


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/build-feed-source-custody-migration.py"
MIGRATIONS = ROOT / "packages/python/src/truss/_migrations"
RUNTIME = ROOT / "packages/python/src/truss/_catalog_runtime"


def _module():
    spec = importlib.util.spec_from_file_location("feed_custody_migration_builder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_validation_does_not_mutate_captured_target():
    builder = _module()
    source = json.loads((MIGRATIONS / f"{builder.SOURCE}.json").read_bytes())
    target = copy.deepcopy(source)
    inventory = target["inventory"]
    rows = inventory["routines"]
    for row in rows:
        if row[0] in builder.CHANGED_ROUTINES:
            row[2] += "\n-- custody fence"
    for name in sorted(builder.NEW_ROUTINES):
        rows.append([name, "", f"CREATE FUNCTION truss.{name}() RETURNS void"])
    table = "runtime_feed_source_custody"
    inventory["columns"].append([table, 1, "custody_id", "uuid", True])
    inventory["constraints"].append([table, "runtime_feed_source_custody_pkey", "p"])
    inventory["indexes"].append(["runtime_feed_source_custody_pkey", "CREATE UNIQUE INDEX"])
    inventory["relations"].extend([
        [table, "r"], ["runtime_feed_source_custody_pkey", "i"],
    ])
    inventory["triggers"].extend([
        [relation, trigger, "A", False, "CREATE TRIGGER"]
        for relation, trigger in builder.NEW_TRIGGERS
    ])
    captured = copy.deepcopy(inventory)

    verifier = ModuleType("truss._migration_verify")
    verifier.matches_inventory = lambda _inventory, _profile: True
    with patch.dict(sys.modules, {"truss._migration_verify": verifier}):
        builder._validate_inventory(source, target)

    assert inventory == captured


def test_generated_edge_binds_new_target_owner_and_existing_feed_grants():
    builder = _module()
    source = json.loads((MIGRATIONS / f"{builder.SOURCE}.json").read_bytes())
    target = copy.deepcopy(source)
    target_manifest_bytes = (RUNTIME / "manifest.json").read_bytes()
    target["manifest"] = json.loads(target_manifest_bytes)
    target["sha256"] = builder.digest(target_manifest_bytes)
    target["exactAcl"] = json.loads(
        (MIGRATIONS / f"{builder.SOURCE}.acl.json").read_bytes()
    )["acl"]
    old = builder.routine_map(source)
    rows = target["inventory"]["routines"]
    for row in rows:
        if row[0] in builder.CHANGED_ROUTINES:
            row[2] += "\n-- custody fence"
    for name in sorted(builder.NEW_ROUTINES):
        rows.append([name, "", f"CREATE FUNCTION truss.{name}() RETURNS void"])
    feed_acl = target["acl"]["feed"]
    for signature in builder.FEED_GRANTS:
        name, arguments = signature.split("(", 1)
        feed_acl.append(["routine", f"{name}({arguments.replace(',', ', ') }", "EXECUTE", False])
    target["definitionAlternatives"] = source.get("definitionAlternatives", [])

    manifest, generated = builder._package(source, target, target["sha256"])
    edge_name = f"edge-{builder.SOURCE}-{target['sha256']}.json"
    edge = json.loads(generated[edge_name])
    assert edge["source"] == builder.SOURCE
    assert edge["target"] == target["sha256"]
    assert edge["feedGrants"] == builder.FEED_GRANTS
    assert edge["moduleGrants"] == []
    assert any("runtime_feed_custody_prune_stale() OWNER TO {}" in sql
               for sql in edge["ownership"])
    assert "feed-custody.sql" in target["manifest"]["files"]
    assert manifest["target"] == target["sha256"]
    assert builder.SOURCE in manifest["sources"]
    for source_sha in manifest["sources"]:
        assert plan_route(manifest, source_sha)[-1]["target"] == target["sha256"]


def test_feed_grants_are_applied_to_registered_feed_roles_outside_module_access():
    execute = (ROOT / "packages/python/src/truss/_migration_execute.py").read_text()
    recipe = (ROOT / "packages/python/src/truss/_migration_recipe.py").read_text()
    assert "if recipe.get('feedGrants'):" in execute
    assert "FROM truss.runtime_feed_consumer c" in execute
    assert "JOIN pg_roles r ON r.oid=c.reader_oid" in execute
    assert "'feedGrants'" in recipe


def test_acl_generator_requires_exact_five_feed_grants_and_rejects_admin_prune():
    builder = _module()
    source = json.loads((MIGRATIONS / f"{builder.SOURCE}.json").read_bytes())
    target = copy.deepcopy(source)
    target["acl"]["owner"].append(["relation", "runtime_feed_source_custody", "SELECT", False])
    for name in builder.NEW_ROUTINES:
        target["acl"]["owner"].append(["routine", f"{name}()", "EXECUTE", False])
    for signature in builder.FEED_GRANTS:
        name, arguments = signature.split("(", 1)
        target["acl"]["feed"].append(
            ["routine", f"{name}({arguments.replace(',', ', ')}", "EXECUTE", False]
        )
    builder._validate_acl(source, target)
    target["acl"]["feed"].append(
        ["routine", "runtime_feed_custody_prune_stale()", "EXECUTE", False]
    )
    try:
        builder._validate_acl(source, target)
    except ValueError:
        pass
    else:
        raise AssertionError("feed roles must not receive stale-row prune authority")
