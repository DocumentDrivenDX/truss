import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
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
        if (row[0], row[1]) in builder.CHANGED_ROUTINES:
            row[2] += "\n-- custody fence"
    for name, arguments in sorted(builder.NEW_ROUTINE_IDENTITIES):
        rows.append([name, arguments, f"CREATE FUNCTION truss.{name}() RETURNS void"])
    table = "runtime_feed_source_custody"
    for ordinal, name in enumerate(sorted(builder.NEW_CUSTODY_COLUMNS), 1):
        inventory["columns"].append([table, ordinal, name])
    inventory["constraints"].extend([[table, name, "c"]
                                     for name in builder.NEW_CUSTODY_CONSTRAINTS])
    inventory["indexes"].extend([[name, "CREATE UNIQUE INDEX"]
                                 for name in builder.NEW_CUSTODY_INDEXES])
    inventory["relations"].extend([[name, "i"] for name in builder.NEW_CUSTODY_INDEXES])
    inventory["relations"].append([table, "r"])
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

    unexpected = copy.deepcopy(target)
    overload = next(row for row in unexpected["inventory"]["routines"]
                    if row[0] == "catalog_accept_with_keys" and "expected_revision" not in row[1])
    overload[2] += "\n-- unreviewed overload change"
    with patch.dict(sys.modules, {"truss._migration_verify": verifier}):
        try:
            builder._validate_inventory(source, unexpected)
        except ValueError as error:
            assert "existing routine changes" in str(error)
        else:
            raise AssertionError("unreviewed catalog_accept_with_keys overload change must be refused")

    extra = copy.deepcopy(target)
    extra["inventory"]["routines"].append([
        "open_feed_source_custody", "unreviewed text",
        "CREATE FUNCTION truss.open_feed_source_custody(unreviewed text)",
    ])
    with patch.dict(sys.modules, {"truss._migration_verify": verifier}):
        try:
            builder._validate_inventory(source, extra)
        except ValueError as error:
            assert "routine identities" in str(error)
        else:
            raise AssertionError("an extra custody overload must be refused")


def test_generated_edge_binds_new_target_owner_and_existing_feed_grants():
    builder = _module()
    source = json.loads((MIGRATIONS / f"{builder.SOURCE}.json").read_bytes())
    target = copy.deepcopy(source)
    target_manifest_bytes = (RUNTIME / "manifest.json").read_bytes()
    target["manifest"] = json.loads(target_manifest_bytes)
    target["manifest"]["files"]["feed-custody.sql"] = builder.digest(
        (RUNTIME / "feed-custody.sql").read_bytes()
    )
    target_manifest_bytes = builder.canonical(target["manifest"]) + b"\n"
    target["sha256"] = builder.digest(target_manifest_bytes)
    target["exactAcl"] = json.loads(
        (MIGRATIONS / f"{builder.SOURCE}.acl.json").read_bytes()
    )["acl"]
    old = builder.routine_map(source)
    rows = target["inventory"]["routines"]
    for row in rows:
        if (row[0], row[1]) in builder.CHANGED_ROUTINES:
            row[2] += "\n-- custody fence"
    for name, arguments in sorted(builder.NEW_ROUTINE_IDENTITIES):
        rows.append([name, arguments, f"CREATE FUNCTION truss.{name}() RETURNS void"])
    target["acl"]["public"].append(
        ["type", "_runtime_feed_source_custody", "USAGE", False]
    )
    feed_acl = target["acl"]["feed"]
    for signature in builder.FEED_GRANTS:
        name, arguments = signature.split("(", 1)
        feed_acl.append(["routine", f"{name}({arguments.replace(',', ', ') }", "EXECUTE", False])
    target["definitionAlternatives"] = source.get("definitionAlternatives", [])

    # `_package` is deliberately a one-shot predecessor→candidate operation.
    # The checked-in manifest is now the packaged candidate, so run this unit
    # against a temporary copy pinned to the archived predecessor manifest.
    with tempfile.TemporaryDirectory(prefix="feed-custody-generator-") as directory:
        migrations = Path(directory) / "_migrations"
        shutil.copytree(MIGRATIONS, migrations)
        package = Path(directory) / "package"
        shutil.copytree(builder.PACKAGE, package)
        (package / "_catalog_runtime/manifest.json").write_bytes(target_manifest_bytes)
        predecessor = next(
            path for path in migrations.glob("*.manifest.json")
            if json.loads(path.read_bytes()).get("target") == builder.SOURCE
        )
        (migrations / "manifest.json").write_bytes(predecessor.read_bytes())
        builder.MIGRATIONS = migrations
        builder.PACKAGE = package
        manifest, generated = builder._package(source, target, target["sha256"])
    edge_name = f"edge-{builder.SOURCE}-{target['sha256']}.json"
    edge = json.loads(generated[edge_name])
    assert edge["source"] == builder.SOURCE
    assert edge["target"] == target["sha256"]
    assert edge["feedGrants"] == builder.FEED_GRANTS
    assert edge["moduleGrants"] == []
    assert ["type", "_runtime_feed_source_custody", "USAGE", False] in target["acl"]["public"]
    assert any("runtime_feed_custody_prune_stale() OWNER TO {}" in sql
               for sql in edge["ownership"])
    assert any("runtime_feed_custody_lock_active(integer,integer,integer) OWNER TO {}" in sql
               for sql in edge["ownership"])
    assert any("REVOKE ALL ON FUNCTION truss.runtime_feed_custody_lock_active(integer,integer,integer) FROM PUBLIC"
               in sql for sql in edge["ownership"])
    assert "REVOKE ALL ON TYPE truss.runtime_feed_source_custody FROM PUBLIC" in edge["ownership"]
    assert "REVOKE ALL ON TYPE truss._runtime_feed_source_custody FROM PUBLIC" not in edge["ownership"]
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


def test_runtime_delta_allows_only_custody_and_current_release_guard_sources():
    builder = _module()
    old = {name: f"old-{name}" for name in builder.CUSTODY_CHANGED_SOURCES}
    old.update({"untouched.sql": "same"})
    source = {"manifest": {"files": old}}
    target = {"manifest": {
        "releaseId": builder.TARGET_RELEASE,
        "files": {**old, "feed-custody.sql": "custody"},
        "version": "0.75",
        "layoutProfile": {"identity": "same"},
    }}
    source["manifest"]["version"] = "0.74"
    source["manifest"]["layoutProfile"] = {"identity": "same"}
    builder._validate_runtime_manifest(source, target)
    target["manifest"]["files"]["untouched.sql"] = "unexpected-change"
    try:
        builder._validate_runtime_manifest(source, target)
    except ValueError:
        pass
    else:
        raise AssertionError("runtime manifest must reject changes outside custody source set")


def test_acl_generator_requires_exact_five_feed_grants_and_rejects_admin_prune():
    builder = _module()
    source = json.loads((MIGRATIONS / f"{builder.SOURCE}.json").read_bytes())
    source_exact = json.loads((MIGRATIONS / f"{builder.SOURCE}.acl.json").read_bytes())
    target = copy.deepcopy(source)
    target["acl"]["owner"].append(["relation", "runtime_feed_source_custody", "SELECT", False])
    for type_name in ("runtime_feed_source_custody", "_runtime_feed_source_custody"):
        target["acl"]["owner"].append(["type", type_name, "USAGE", False])
    for name in builder.NEW_ROUTINES:
        target["acl"]["owner"].append(["routine", f"{name}()", "EXECUTE", False])
    target["acl"]["public"].append(["type", "_runtime_feed_source_custody", "USAGE", False])
    target["exactAcl"] = copy.deepcopy(source_exact["acl"])
    for signature in builder.FEED_GRANTS:
        name, arguments = signature.split("(", 1)
        target["acl"]["feed"].append(
            ["routine", f"{name}({arguments.replace(',', ', ')}", "EXECUTE", False]
        )
        target["exactAcl"]["feed"].append(["routine", signature, "EXECUTE", False])
    builder._validate_acl(source, target, source_exact["acl"])
    target["acl"]["feed"].append(
        ["routine", "runtime_feed_custody_prune_stale()", "EXECUTE", False]
    )
    try:
        builder._validate_acl(source, target, source_exact["acl"])
    except ValueError:
        pass
    else:
        raise AssertionError("feed roles must not receive stale-row prune authority")
