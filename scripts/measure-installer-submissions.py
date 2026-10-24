#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Local diagnostic for fresh Truss installation client submissions.

The report compares the installed package on sys.path with the source package
in this checkout. It records client-side Cursor.execute/nextset latency,
process CPU consumed during the installer call, and complete normalized
installation snapshots; it is not server or wire telemetry.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import selectors
import signal
import subprocess
import sys
import time
import tomllib
import zipfile
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from time import perf_counter_ns
from typing import Any, cast
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "packages/python/src"
OWNER_ROLE = "truss_installer_measure_owner"
CLIENT_ROLE = "truss_installer_measure_client"
EXPECTED_SERVER_VERSION = "180006"
CHILD_TIMEOUT_SECONDS = 180
CHILD_OUTPUT_LIMIT_BYTES = 96 * 1024 * 1024
BASELINE_VERSION = "0.0.49"
BASELINE_WHEEL_SHA256 = (
    "7ea14b2787f02cbeec9ad99d835adbcc30c684fd5be8e0765a1d8198b50e7182"
)
_ACTIVE_MEASUREMENT: ContextVar[dict[str, Any] | None] = ContextVar(
    "truss_installer_measurement", default=None
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf8")


def _object(value: Any) -> dict[str, Any]:
    """Narrow JSON-derived values before inspecting a nested object."""
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def _tree_digest(root: Path) -> dict[str, Any]:
    entries: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        entries.append((relative, len(raw), _sha256(raw)))
    material = "".join(f"{name}\0{size}\0{digest}\n" for name, size, digest in entries)
    return {
        "fileCount": len(entries),
        "totalBytes": sum(size for _, size, _ in entries),
        "sha256": _sha256(material.encode("utf8")),
    }


def _distribution_digest() -> dict[str, Any]:
    distribution = importlib.metadata.distribution("truss-toolkit")
    entries: list[tuple[str, int, str]] = []
    for member in distribution.files or ():
        path = Path(str(distribution.locate_file(member)))
        if not path.is_file():
            raise RuntimeError("Installed distribution file is missing")
        raw = path.read_bytes()
        entries.append((str(member).replace("\\", "/"), len(raw), _sha256(raw)))
    if not entries:
        raise RuntimeError("Installed distribution inventory is unavailable")
    entries.sort(key=lambda item: item[0])
    material = "".join(f"{name}\0{size}\0{digest}\n" for name, size, digest in entries)
    return {
        "version": distribution.version,
        "fileCount": len(entries),
        "totalBytes": sum(size for _, size, _ in entries),
        "sha256": _sha256(material.encode("utf8")),
    }


def _source_commit() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _module_hash(module: Any) -> str:
    path = Path(module.__file__).resolve()
    return _sha256(path.read_bytes())


def _require_server_version_profile(display_version: Any, numeric_version: Any) -> None:
    """Bind the package's display and numeric PostgreSQL 18.6 profile fields."""
    if (type(display_version) is not str or display_version != '18.6'
            or type(numeric_version) is not int
            or numeric_version != int(EXPECTED_SERVER_VERSION)):
        raise RuntimeError("Selected PostgreSQL 18.6 package profile required")


def _dependency_versions() -> dict[str, str | None]:
    names = ("psycopg", "psycopg-binary", "pgserver", "pgserver-pg18", "pg8000")
    result: dict[str, str | None] = {}
    for name in names:
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def _package_identity(
    truss: Any, catalog_runtime: Any, privileges: Any
) -> dict[str, Any]:
    from importlib.resources import files

    manifest_bytes = (
        files("truss").joinpath("_catalog_runtime/manifest.json").read_bytes()
    )
    manifest, release_digest, source_units = catalog_runtime._release()
    source_unit_hashes = [_sha256(unit.encode("utf8")) for unit in source_units]
    modules: dict[str, str | None] = {}
    for name in (
        "truss._installation_privileges",
        "truss._installation_sql_batch",
        "truss.catalog_runtime",
        "truss.psycopg_host",
    ):
        try:
            modules[name] = _module_hash(importlib.import_module(name))
        except ModuleNotFoundError:
            modules[name] = None
    module_paths = [
        Path(module.__file__).resolve()
        for module in (truss, privileges, catalog_runtime)
    ]
    source_loaded = all(
        path.is_relative_to(SOURCE_ROOT.resolve()) for path in module_paths
    )
    installed_loaded = all(
        not path.is_relative_to(SOURCE_ROOT.resolve()) for path in module_paths
    )
    if not source_loaded and not installed_loaded:
        raise RuntimeError(
            "Mixed source and installed Truss modules are not measurable"
        )
    distribution_version = importlib.metadata.version("truss-toolkit")
    source_project_version = None
    if source_loaded:
        with (ROOT / "packages/python/pyproject.toml").open("rb") as project_file:
            source_project_version = tomllib.load(project_file)["project"]["version"]
    identity: dict[str, Any] = {
        "environmentDistributionVersion": distribution_version,
        "sourceProjectVersion": source_project_version,
        "releaseId": manifest.get("releaseId"),
        "releaseSha256": release_digest,
        "manifestSha256": _sha256(manifest_bytes),
        "releaseSourceUnitCount": len(source_units),
        "releaseSourceBytes": sum(len(unit.encode("utf8")) for unit in source_units),
        "releaseSourceUnitSha256": _sha256(_canonical_bytes(source_unit_hashes)),
        "moduleSha256": modules,
        "dependencies": _dependency_versions(),
    }
    if source_loaded:
        identity["sourceFreeze"] = {
            "gitCommit": _source_commit(),
            "sourceTree": _tree_digest(SOURCE_ROOT / "truss"),
        }
        identity["installedDistribution"] = None
    else:
        identity["sourceFreeze"] = None
        identity["installedDistribution"] = _distribution_digest()
    return identity


def _verify_baseline_wheel(
    path_value: str,
    package: dict[str, Any],
    truss: Any,
    privileges: Any,
    catalog_runtime: Any,
) -> dict[str, Any]:
    wheel = Path(path_value)
    if not wheel.is_file():
        raise RuntimeError("Public49 baseline wheel custody file is unavailable")
    wheel_sha256 = _sha256(wheel.read_bytes())
    if wheel_sha256 != BASELINE_WHEEL_SHA256:
        raise RuntimeError(
            "Baseline wheel does not match the approved public49 archive"
        )
    if package.get("environmentDistributionVersion") != BASELINE_VERSION:
        raise RuntimeError("Baseline installed distribution is not public49")
    source_root = SOURCE_ROOT.resolve()
    prefix = Path(sys.prefix).resolve()
    package_root = Path(truss.__file__).resolve().parent
    import_roots = [
        Path(module.__file__).resolve()
        for module in (truss, privileges, catalog_runtime)
    ]
    if any(
        root.is_relative_to(source_root) or not root.is_relative_to(prefix)
        for root in import_roots
    ):
        raise RuntimeError(
            "Baseline package import is not from the installed environment"
        )
    payload_members: list[str] = []
    with zipfile.ZipFile(wheel) as archive:
        for member in sorted(
            name
            for name in archive.namelist()
            if name.startswith("truss/") and not name.endswith("/")
        ):
            relative_parts = PurePosixPath(member).parts
            if not relative_parts or relative_parts[0] != "truss":
                raise RuntimeError("Unexpected public49 payload path")
            installed_member = package_root.joinpath(*relative_parts[1:])
            if not installed_member.is_file():
                raise RuntimeError("Public49 package payload member is not installed")
            if archive.read(member) != installed_member.read_bytes():
                raise RuntimeError(
                    "Installed baseline payload differs from public49 wheel"
                )
            payload_members.append(member)
    if not payload_members:
        raise RuntimeError("Public49 wheel has no Truss package payload")
    return {
        "wheelSha256": wheel_sha256,
        "distributionVersion": BASELINE_VERSION,
        "installedImportRootUnderSysPrefix": True,
        "payloadMemberCount": len(payload_members),
        "payloadMembersEqual": True,
    }


def _json_rows(connection: Any, query: str) -> list[list[Any]]:
    rows = connection.execute(query, prepare=False).fetchall()
    return [list(row) for row in rows]


def _caller_state(connection: Any) -> list[Any]:
    row = connection.execute(
        """SELECT session_user::text,current_user::text,
                  pg_catalog.current_setting('role'),
                  pg_catalog.current_setting('search_path'),
                  pg_catalog.current_setting('transaction_isolation'),
                  pg_catalog.current_setting('transaction_read_only'),
                  pg_catalog.current_setting('transaction_deferrable'),
                  pg_catalog.current_setting('statement_timeout')"""
    ).fetchone()
    if row is None:
        raise RuntimeError("Caller identity and settings observation missing")
    return list(row)


def _installation_snapshot(connection: Any) -> dict[str, Any]:
    """Capture full installed identities/definitions/ACLs without native OIDs."""
    from psycopg import sql

    connection.execute("SET LOCAL search_path = pg_catalog, pg_temp", prepare=False)
    snapshot: dict[str, Any] = {
        "roles": _json_rows(
            connection,
            """SELECT rolname::text,rolsuper,rolinherit,rolcreaterole,rolcreatedb,
                      rolcanlogin,rolreplication,rolbypassrls,rolconnlimit,rolconfig
               FROM pg_catalog.pg_roles
               WHERE rolname IN ('truss_installer_measure_owner',
                                 'truss_installer_measure_client')
               ORDER BY rolname""",
        ),
        "roleMemberships": _json_rows(
            connection,
            """SELECT granted.rolname::text,member.rolname::text,grantor.rolname::text,
                      m.admin_option,m.inherit_option,m.set_option
               FROM pg_catalog.pg_auth_members m
               JOIN pg_catalog.pg_roles granted ON granted.oid=m.roleid
               JOIN pg_catalog.pg_roles member ON member.oid=m.member
               JOIN pg_catalog.pg_roles grantor ON grantor.oid=m.grantor
               WHERE granted.rolname IN ('truss_installer_measure_owner',
                                         'truss_installer_measure_client')
                  OR member.rolname IN ('truss_installer_measure_owner',
                                        'truss_installer_measure_client')
               ORDER BY granted.rolname,member.rolname,grantor.rolname""",
        ),
        "schema": _json_rows(
            connection,
            """SELECT n.nspname::text,r.rolname::text
               FROM pg_catalog.pg_namespace n
               JOIN pg_catalog.pg_roles r ON r.oid=n.nspowner
               WHERE n.nspname='truss'""",
        ),
        "relations": _json_rows(
            connection,
            """SELECT c.relname::text,c.relkind::text,c.relpersistence::text,
                      owner.rolname::text,c.relrowsecurity,c.relforcerowsecurity,
                      c.relispartition,c.relhasrules,
                      pg_catalog.pg_get_partkeydef(c.oid),
                      pg_catalog.pg_get_expr(c.relpartbound,c.oid,false),
                      CASE WHEN c.relkind IN ('v','m')
                           THEN pg_catalog.pg_get_viewdef(c.oid,false) END
               FROM pg_catalog.pg_class c
               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
               JOIN pg_catalog.pg_roles owner ON owner.oid=c.relowner
               WHERE n.nspname='truss'
               ORDER BY c.relname,c.relkind""",
        ),
        "columns": _json_rows(
            connection,
            """SELECT c.relname::text,a.attnum,a.attname::text,
                      pg_catalog.format_type(a.atttypid,a.atttypmod),a.attnotnull,
                      a.attidentity::text,a.attgenerated::text,a.attndims,
                      COALESCE(cn.nspname::text || '.' || co.collname::text,''),
                      pg_catalog.pg_get_expr(d.adbin,d.adrelid,false)
               FROM pg_catalog.pg_attribute a
               JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
               LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
               LEFT JOIN pg_catalog.pg_collation co ON co.oid=a.attcollation
               LEFT JOIN pg_catalog.pg_namespace cn ON cn.oid=co.collnamespace
               WHERE n.nspname='truss' AND a.attnum>0 AND NOT a.attisdropped
               ORDER BY c.relname,a.attnum""",
        ),
        "inheritance": _json_rows(
            connection,
            """SELECT child.relname::text,parent.relname::text,i.inhseqno,i.inhdetachpending
               FROM pg_catalog.pg_inherits i
               JOIN pg_catalog.pg_class child ON child.oid=i.inhrelid
               JOIN pg_catalog.pg_namespace child_ns ON child_ns.oid=child.relnamespace
               JOIN pg_catalog.pg_class parent ON parent.oid=i.inhparent
               WHERE child_ns.nspname='truss'
               ORDER BY child.relname,i.inhseqno,parent.relname""",
        ),
        "constraints": _json_rows(
            connection,
            """SELECT COALESCE(c.relname::text,''),con.conname::text,con.contype::text,
                      pg_catalog.pg_get_constraintdef(con.oid,true),con.convalidated,
                      con.condeferrable,con.condeferred
               FROM pg_catalog.pg_constraint con
               JOIN pg_catalog.pg_namespace n ON n.oid=con.connamespace
               LEFT JOIN pg_catalog.pg_class c ON c.oid=con.conrelid
               WHERE n.nspname='truss'
               ORDER BY c.relname,con.conname,con.contype""",
        ),
        "indexes": _json_rows(
            connection,
            """SELECT table_class.relname::text,index_class.relname::text,
                      index.indisunique,index.indisprimary,index.indisvalid,index.indisready,
                      pg_catalog.pg_get_indexdef(index.indexrelid)
               FROM pg_catalog.pg_index index
               JOIN pg_catalog.pg_class table_class ON table_class.oid=index.indrelid
               JOIN pg_catalog.pg_namespace n ON n.oid=table_class.relnamespace
               JOIN pg_catalog.pg_class index_class ON index_class.oid=index.indexrelid
               WHERE n.nspname='truss'
               ORDER BY table_class.relname,index_class.relname""",
        ),
        "sequenceSettings": _json_rows(
            connection,
            """SELECT c.relname::text,s.seqtypid::pg_catalog.regtype::text,
                      s.seqstart,s.seqincrement,s.seqmax,s.seqmin,s.seqcache,s.seqcycle
               FROM pg_catalog.pg_sequence s
               JOIN pg_catalog.pg_class c ON c.oid=s.seqrelid
               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='truss'
               ORDER BY c.relname""",
        ),
        "sequenceState": [],
        "triggers": _json_rows(
            connection,
            """SELECT c.relname::text,t.tgname::text,t.tgenabled::text,
                      t.tgisinternal,pg_catalog.pg_get_triggerdef(t.oid,false)
               FROM pg_catalog.pg_trigger t
               JOIN pg_catalog.pg_class c ON c.oid=t.tgrelid
               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='truss'
               ORDER BY c.relname,t.tgname""",
        ),
        "policies": _json_rows(
            connection,
            """SELECT c.relname::text,p.polname::text,p.polcmd::text,p.polpermissive,
                      ARRAY(SELECT r.rolname::text FROM pg_catalog.pg_roles r
                            WHERE r.oid=ANY(p.polroles) ORDER BY r.rolname),
                      pg_catalog.pg_get_expr(p.polqual,p.polrelid,false),
                      pg_catalog.pg_get_expr(p.polwithcheck,p.polrelid,false)
               FROM pg_catalog.pg_policy p
               JOIN pg_catalog.pg_class c ON c.oid=p.polrelid
               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='truss'
               ORDER BY c.relname,p.polname""",
        ),
        "rules": _json_rows(
            connection,
            """SELECT c.relname::text,r.rulename::text,r.ev_type::text,r.ev_enabled::text,
                      r.is_instead,pg_catalog.pg_get_ruledef(r.oid,false)
               FROM pg_catalog.pg_rewrite r
               JOIN pg_catalog.pg_class c ON c.oid=r.ev_class
               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='truss'
               ORDER BY c.relname,r.rulename""",
        ),
        "routines": _json_rows(
            connection,
            """SELECT p.proname::text,pg_catalog.pg_get_function_identity_arguments(p.oid),
                      p.prokind::text,owner.rolname::text,
                      pg_catalog.pg_get_function_result(p.oid),
                      pg_catalog.pg_get_functiondef(p.oid),p.prosecdef,p.proleakproof,
                      p.provolatile::text,p.proparallel::text,p.proconfig
               FROM pg_catalog.pg_proc p
               JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
               JOIN pg_catalog.pg_roles owner ON owner.oid=p.proowner
               WHERE n.nspname='truss'
               ORDER BY p.proname,pg_catalog.pg_get_function_identity_arguments(p.oid)""",
        ),
        "types": _json_rows(
            connection,
            """SELECT t.typname::text,t.typtype::text,
                      pg_catalog.format_type(t.oid,NULL),owner.rolname::text,
                      t.typcategory::text,t.typnotnull,t.typdefault,t.typdelim::text,
                      t.typbyval,t.typlen,t.typalign::text,t.typstorage::text,
                      CASE WHEN t.typbasetype=0 THEN ''::text
                           ELSE pg_catalog.format_type(t.typbasetype,t.typtypmod) END,
                      t.typtypmod,
                      COALESCE(cn.nspname::text || '.' || co.collname::text,'')
               FROM pg_catalog.pg_type t
               JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace
               JOIN pg_catalog.pg_roles owner ON owner.oid=t.typowner
               LEFT JOIN pg_catalog.pg_collation co ON co.oid=t.typcollation
               LEFT JOIN pg_catalog.pg_namespace cn ON cn.oid=co.collnamespace
               WHERE n.nspname='truss'
               ORDER BY t.typname,t.typtype""",
        ),
        "enumValues": _json_rows(
            connection,
            """SELECT typ.typname::text,e.enumsortorder,e.enumlabel::text
               FROM pg_catalog.pg_enum e
               JOIN pg_catalog.pg_type typ ON typ.oid=e.enumtypid
               JOIN pg_catalog.pg_namespace n ON n.oid=typ.typnamespace
               WHERE n.nspname='truss'
               ORDER BY typ.typname,e.enumsortorder""",
        ),
        "rangeTypes": _json_rows(
            connection,
            """SELECT typ.typname::text,
                      pg_catalog.format_type(r.rngsubtype,NULL),
                      COALESCE(coll_ns.nspname::text || '.' || coll.collname::text,''),
                      CASE WHEN r.rngmultitypid=0 THEN ''::text
                           ELSE pg_catalog.format_type(r.rngmultitypid,NULL) END,
                      opc_ns.nspname::text,opc.opcname::text
               FROM pg_catalog.pg_range r
               JOIN pg_catalog.pg_type typ ON typ.oid=r.rngtypid
               JOIN pg_catalog.pg_namespace n ON n.oid=typ.typnamespace
               LEFT JOIN pg_catalog.pg_collation coll ON coll.oid=r.rngcollation
               LEFT JOIN pg_catalog.pg_namespace coll_ns ON coll_ns.oid=coll.collnamespace
               JOIN pg_catalog.pg_opclass opc ON opc.oid=r.rngsubopc
               JOIN pg_catalog.pg_namespace opc_ns ON opc_ns.oid=opc.opcnamespace
               WHERE n.nspname='truss'
               ORDER BY typ.typname""",
        ),
        "objectAcls": _json_rows(
            connection,
            """WITH objects(kind,object_key,owner_oid,acl,acl_kind) AS (
                   SELECT 'schema',n.nspname::text,n.nspowner,n.nspacl,'n'::"char"
                     FROM pg_catalog.pg_namespace n WHERE n.nspname='truss'
                   UNION ALL
                   SELECT CASE WHEN c.relkind='S' THEN 'sequence' ELSE 'relation' END,
                          c.relname::text,c.relowner,c.relacl,
                          CASE WHEN c.relkind='S' THEN 's' ELSE 'r' END::"char"
                     FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                    WHERE n.nspname='truss' AND c.relkind NOT IN ('i','I')
                   UNION ALL
                   SELECT 'routine',p.proname::text || '(' ||
                          pg_catalog.pg_get_function_identity_arguments(p.oid) || ')',
                          p.proowner,p.proacl,'f'::"char"
                     FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
                    WHERE n.nspname='truss'
                   UNION ALL
                   SELECT 'type',t.typname::text,t.typowner,t.typacl,'T'::"char"
                     FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace
                    WHERE n.nspname='truss'), expanded AS (
                   SELECT o.kind,o.object_key,owner.rolname::text owner_name,
                          acl.grantor,acl.grantee,acl.privilege_type,acl.is_grantable,
                          NULL::text column_name
                     FROM objects o JOIN pg_catalog.pg_roles owner ON owner.oid=o.owner_oid
                     CROSS JOIN LATERAL pg_catalog.aclexplode(
                          COALESCE(o.acl,pg_catalog.acldefault(o.acl_kind,o.owner_oid))) acl
                   UNION ALL
                   SELECT 'column',c.relname::text,owner.rolname::text,
                          acl.grantor,acl.grantee,acl.privilege_type,acl.is_grantable,a.attname::text
                     FROM pg_catalog.pg_attribute a
                     JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
                     JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                     JOIN pg_catalog.pg_roles owner ON owner.oid=c.relowner
                     CROSS JOIN LATERAL pg_catalog.aclexplode(a.attacl) acl
                    WHERE n.nspname='truss' AND c.relkind IN ('r','p')
                      AND a.attnum>0 AND NOT a.attisdropped AND a.attacl IS NOT NULL)
                 SELECT e.kind,e.object_key,e.column_name,e.owner_name,
                        CASE WHEN e.grantee=0 THEN 'PUBLIC' ELSE grantee.rolname::text END,
                        CASE WHEN e.grantor=0 THEN 'PUBLIC' ELSE grantor.rolname::text END,
                        e.privilege_type::text,e.is_grantable
                   FROM expanded e
                   LEFT JOIN pg_catalog.pg_roles grantee ON grantee.oid=e.grantee
                   LEFT JOIN pg_catalog.pg_roles grantor ON grantor.oid=e.grantor
                  ORDER BY e.kind,e.object_key,e.column_name,e.grantee,e.grantor,e.privilege_type""",
        ),
        "defaultAcls": _json_rows(
            connection,
            """SELECT owner.rolname::text,COALESCE(n.nspname::text,''),d.defaclobjtype::text,
                      CASE WHEN acl.grantee=0 THEN 'PUBLIC' ELSE grantee.rolname::text END,
                      CASE WHEN acl.grantor=0 THEN 'PUBLIC' ELSE grantor.rolname::text END,
                      acl.privilege_type::text,acl.is_grantable
               FROM pg_catalog.pg_default_acl d
               JOIN pg_catalog.pg_roles owner ON owner.oid=d.defaclrole
               LEFT JOIN pg_catalog.pg_namespace n ON n.oid=d.defaclnamespace
               CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) acl
               LEFT JOIN pg_catalog.pg_roles grantee ON grantee.oid=acl.grantee
               LEFT JOIN pg_catalog.pg_roles grantor ON grantor.oid=acl.grantor
               ORDER BY owner.rolname,n.nspname,d.defaclobjtype,acl.grantee,
                        acl.grantor,acl.privilege_type""",
        ),
    }
    relation_names = [
        row[0]
        for row in connection.execute(
            """SELECT c.relname::text
               FROM pg_catalog.pg_class c
               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='truss' AND c.relkind IN ('r','p')
               ORDER BY c.relname"""
        ).fetchall()
    ]
    role_names_by_oid = {
        int(oid): role_name
        for oid, role_name in connection.execute(
            "SELECT oid::text,rolname::text FROM pg_catalog.pg_roles"
        ).fetchall()
    }
    rows_by_relation: dict[str, list[Any]] = {}
    installation_genesis_at: str | None = None
    for relation_name in relation_names:
        raw_rows = connection.execute(
            sql.SQL(
                "SELECT pg_catalog.to_jsonb(row_value)::text "
                "FROM {} AS row_value ORDER BY 1"
            ).format(sql.Identifier("truss", relation_name)),
            prepare=False,
        ).fetchall()
        normalized: list[Any] = []
        for (raw_row,) in raw_rows:
            value = json.loads(raw_row)
            if relation_name == "catalog_runtime_installation":
                if type(value) is not dict:
                    raise RuntimeError("Installation identity row must be an object")
                if value.get("singleton") is not True:
                    raise RuntimeError("Exact installation identity row required")
                for generated in ("installation_id", "source_epoch"):
                    identifier = value.get(generated)
                    if (
                        type(identifier) is not str
                        or str(UUID(identifier)) != identifier
                    ):
                        raise RuntimeError("Expected generated UUID identity field")
                    value[generated] = f"<generated:{generated}>"
                genesis_at = value.get("genesis_at")
                if (
                    type(genesis_at) is not str
                    or datetime.fromisoformat(genesis_at).tzinfo is None
                ):
                    raise RuntimeError("Expected timezone-aware installation timestamp")
                installation_genesis_at = genesis_at
                value["genesis_at"] = "<generated:genesis_at>"
                for field_name, expected_role in (
                    ("owner_oid", OWNER_ROLE),
                    ("registrar_oid", CLIENT_ROLE),
                ):
                    role_oid = value.get(field_name)
                    if (
                        type(role_oid) is not int
                        or role_names_by_oid.get(role_oid) != expected_role
                    ):
                        raise RuntimeError(
                            "Installation role identity did not match fixed role"
                        )
                    value[field_name] = expected_role
            normalized.append(value)
        if relation_name == "catalog_runtime_installation" and len(normalized) != 1:
            raise RuntimeError("Exactly one installed runtime identity row required")
        if relation_name == "schema_rev":
            if len(normalized) != 1 or normalized[0].get("rev") != 0:
                raise RuntimeError("Exact fresh schema revision row required")
            if "accepted_at" not in normalized[0]:
                raise RuntimeError("Generated schema revision timestamp missing")
            accepted_at = normalized[0]["accepted_at"]
            if (
                type(accepted_at) is not str
                or datetime.fromisoformat(accepted_at).tzinfo is None
            ):
                raise RuntimeError("Expected timezone-aware schema revision timestamp")
            source_revision = connection.execute(
                "SELECT pg_catalog.to_jsonb(accepted_at)::text "
                "FROM truss.schema_rev WHERE rev=0"
            ).fetchone()
            if source_revision is None or installation_genesis_at is None:
                raise RuntimeError("Installation timestamp source observation missing")
            # The released installer copies schema_rev.accepted_at directly into
            # genesis_at. Require that source-defined identity before normalization.
            if (
                accepted_at != installation_genesis_at
                or json.loads(source_revision[0]) != installation_genesis_at
            ):
                raise RuntimeError("Installation genesis timestamp source mismatch")
            normalized[0]["accepted_at"] = "<generated:genesis_at>"
        rows_by_relation[relation_name] = normalized
    snapshot["relationRows"] = rows_by_relation
    sequence_names = [
        row[0]
        for row in connection.execute(
            """SELECT c.relname::text
               FROM pg_catalog.pg_class c
               JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname='truss' AND c.relkind='S'
               ORDER BY c.relname"""
        ).fetchall()
    ]
    sequence_state: list[list[Any]] = []
    for sequence_name in sequence_names:
        row = connection.execute(
            sql.SQL("SELECT last_value,is_called FROM {} ").format(
                sql.Identifier("truss", sequence_name)
            ),
            prepare=False,
        ).fetchone()
        if row is None:
            raise RuntimeError("Sequence state observation missing")
        sequence_state.append([sequence_name, *row])
    snapshot["sequenceState"] = sequence_state
    encoded = _canonical_bytes(snapshot)
    if len(encoded) > 64 * 1024 * 1024:
        raise RuntimeError("Installation snapshot exceeded its local diagnostic bound")
    return snapshot


def _measure_cursor_execute(psycopg: Any, recorder: dict[str, Any]) -> None:
    original = psycopg.Cursor.execute

    def measured(cursor: Any, *args: Any, **kwargs: Any) -> Any:
        active = _ACTIVE_MEASUREMENT.get()
        if active is None:
            return original(cursor, *args, **kwargs)
        query = args[0] if args else kwargs.get("query")
        source_hashes = active["sourceUnitHashes"]
        if isinstance(query, str) and _sha256(query.encode("utf8")) in source_hashes:
            active["directSourceUnitExecuteSubmissions"] += 1
        started = perf_counter_ns()
        try:
            return original(cursor, *args, **kwargs)
        finally:
            elapsed = perf_counter_ns() - started
            active["cursorExecuteCount"] += 1
            active["cursorExecuteElapsedNs"] += elapsed
            active["cursorExecuteMaxNs"] = max(active["cursorExecuteMaxNs"], elapsed)

    psycopg.Cursor.execute = measured
    recorder["cursorExecuteOriginal"] = original

    original_nextset = getattr(psycopg.Cursor, "nextset", None)
    if original_nextset is not None:
        def measured_nextset(cursor: Any, *args: Any, **kwargs: Any) -> Any:
            active = _ACTIVE_MEASUREMENT.get()
            if active is None:
                return original_nextset(cursor, *args, **kwargs)
            started = perf_counter_ns()
            failed = False
            try:
                return original_nextset(cursor, *args, **kwargs)
            except BaseException:
                failed = True
                raise
            finally:
                elapsed = perf_counter_ns() - started
                active["cursorNextsetCount"] += 1
                active["cursorNextsetElapsedNs"] += elapsed
                active["cursorNextsetMaxNs"] = max(
                    active["cursorNextsetMaxNs"], elapsed
                )
                if failed:
                    active["cursorNextsetFailureCount"] += 1

        psycopg.Cursor.nextset = measured_nextset
        recorder["cursorNextsetOriginal"] = original_nextset


def _measure_ordered_ddl(module: Any, recorder: dict[str, Any]) -> None:
    original = getattr(module, "execute_ordered_ddl", None)
    if original is None:
        return

    def counted(cursor: Any, units: Any) -> Any:
        offered = 0

        def source_units():
            nonlocal offered
            for unit in units:
                offered += 1
                rendered = (
                    unit.as_string(cursor.connection)
                    if hasattr(unit, "as_string")
                    else unit
                )
                active = _ACTIVE_MEASUREMENT.get()
                if active is not None and isinstance(rendered, str):
                    if _sha256(rendered.encode("utf8")) in active["sourceUnitHashes"]:
                        active["orderedDdlSourceUnitCount"] += 1
                    else:
                        active["orderedDdlOtherUnitCount"] += 1
                yield unit

        active = _ACTIVE_MEASUREMENT.get()
        before = active["cursorExecuteCount"] if active is not None else 0
        try:
            return original(cursor, source_units())
        finally:
            if active is not None:
                active["orderedDdlHelperCalls"] += 1
                active["orderedDdlUnits"] += offered
                active["orderedDdlExecuteSubmissions"] += (
                    active["cursorExecuteCount"] - before
                )

    module.execute_ordered_ddl = counted
    recorder.setdefault("ddlOriginals", []).append((module, original))


def _restore_instrumentation(psycopg: Any, recorder: dict[str, Any]) -> None:
    if "cursorExecuteOriginal" in recorder:
        psycopg.Cursor.execute = recorder["cursorExecuteOriginal"]
    if "cursorNextsetOriginal" in recorder:
        psycopg.Cursor.nextset = recorder["cursorNextsetOriginal"]
    for module, original in reversed(recorder.get("ddlOriginals", [])):
        module.execute_ordered_ddl = original


def _measurement_summary(
    recorder: dict[str, Any], *, install_elapsed_ns: int, process_cpu_ns: int
) -> dict[str, Any]:
    """Copy bounded client/process counters, including partial failed attempts."""
    return {
        "installElapsedNs": install_elapsed_ns,
        "installerProcessCpuElapsedNs": process_cpu_ns,
        "cursorExecuteSubmissionCount": recorder["cursorExecuteCount"],
        "cursorExecuteElapsedNs": recorder["cursorExecuteElapsedNs"],
        "cursorExecuteMaximumNs": recorder["cursorExecuteMaxNs"],
        "cursorNextsetCallCount": recorder["cursorNextsetCount"],
        "cursorNextsetElapsedNs": recorder["cursorNextsetElapsedNs"],
        "cursorNextsetMaximumNs": recorder["cursorNextsetMaxNs"],
        "cursorNextsetFailureCount": recorder["cursorNextsetFailureCount"],
        "orderedDdlHelperCalls": recorder["orderedDdlHelperCalls"],
        "orderedDdlInputUnitCount": recorder["orderedDdlUnits"],
        "orderedDdlExecuteSubmissionCount": recorder["orderedDdlExecuteSubmissions"],
        "orderedDdlSourceUnitCount": recorder["orderedDdlSourceUnitCount"],
        "orderedDdlOtherUnitCount": recorder["orderedDdlOtherUnitCount"],
        "directSourceUnitExecuteSubmissionCount": recorder[
            "directSourceUnitExecuteSubmissions"
        ],
        "timingScope": (
            "client-side synchronous Cursor.execute/nextset and process CPU during "
            "the installer call; not wire/server telemetry"
        ),
        "processCpuScope": (
            "whole diagnostic child process CPU consumed during the synchronous "
            "installer call; includes instrumentation and any same-process work"
        ),
        "sourceUnitSubmissionSemantics": (
            "direct submissions hash-match one captured release source unit; "
            "ordered DDL counts are original units and helper command submissions"
        ),
        "sourceUnitSemantics": (
            "release source items and ordered DDL input units; a unit may contain "
            "multiple SQL statements"
        ),
    }


def _call_measured_install(recorder: dict[str, Any], install: Any) -> Any:
    """Time only the synchronous installer call, excluding hook setup/restoration."""
    wall_started = perf_counter_ns()
    cpu_started = time.process_time_ns()
    recorder["installAttempted"] = True
    try:
        return install()
    finally:
        recorder["installElapsedNs"] = perf_counter_ns() - wall_started
        recorder["installerProcessCpuElapsedNs"] = (
            time.process_time_ns() - cpu_started
        )


def _finish_measurement(
    psycopg: Any,
    recorder: dict[str, Any],
    token: Any,
    result: dict[str, Any],
    primary_error: BaseException | None,
) -> None:
    """Always restore hooks before building a diagnostic summary."""
    failures: list[str] = []
    try:
        _ACTIVE_MEASUREMENT.reset(token)
    except BaseException as error:  # noqa: BLE001 - preserve an installer exception
        failures.append(type(error).__name__)
    try:
        _restore_instrumentation(psycopg, recorder)
    except BaseException as error:  # noqa: BLE001 - preserve an installer exception
        failures.append(type(error).__name__)
    result["instrumentationHooksRestored"] = (
        "cursorExecuteOriginal" in recorder
        and psycopg.Cursor.execute is recorder["cursorExecuteOriginal"]
        and (
            "cursorNextsetOriginal" not in recorder
            or psycopg.Cursor.nextset is recorder["cursorNextsetOriginal"]
        )
        and all(
            module.execute_ordered_ddl is original
            for module, original in recorder.get("ddlOriginals", [])
        )
    )
    if result["instrumentationHooksRestored"] is not True:
        failures.append("InstrumentationHookRestorationFailed")
    if recorder["installAttempted"]:
        try:
            result["measurement"] = _measurement_summary(
                recorder,
                install_elapsed_ns=recorder["installElapsedNs"],
                process_cpu_ns=recorder["installerProcessCpuElapsedNs"],
            )
        except BaseException as error:  # noqa: BLE001 - diagnostics cannot mask install
            failures.append(type(error).__name__)
            result["measurementSummaryFailureType"] = type(error).__name__
    if failures:
        result["measurementFinalizationFailureTypes"] = failures
        if primary_error is None:
            raise RuntimeError("Measurement finalization failed")


def _install_once(worker_root: Path, phase: str) -> dict[str, Any]:
    if phase == "candidate":
        sys.path.insert(0, str(SOURCE_ROOT))
    elif any(Path(item or ".").resolve() == SOURCE_ROOT.resolve() for item in sys.path):
        sys.path[:] = [
            item
            for item in sys.path
            if Path(item or ".").resolve() != SOURCE_ROOT.resolve()
        ]

    import psycopg
    import truss
    from native_fixture import DatabaseFixture
    from truss import (
        CatalogRuntimeConfiguration,
        Error,
        InstallRefused,
        Ok,
        PendingCatalogInstallation,
        adopt_psycopg_host,
        catalog_runtime,
        create_reference_assembly,
    )
    from truss import _installation_privileges as privileges
    from truss._runtime_profile import SERVER_VERSION, SERVER_VERSION_NUM

    package = _package_identity(truss, catalog_runtime, privileges)
    if (
        phase == "baseline"
        and package["environmentDistributionVersion"] != BASELINE_VERSION
    ):
        raise RuntimeError("Installed baseline package version must be public49")
    dependencies = package["dependencies"]
    if (
        dependencies.get("psycopg") != "3.3.6"
        or dependencies.get("psycopg-binary") != "3.3.6"
    ):
        raise RuntimeError("Stock psycopg 3.3.6 dependencies are required")
    baseline_wheel_binding = None
    if phase == "baseline":
        wheel_path = os.environ.get("TRUSS_MEASURE_BASELINE_WHEEL")
        if not wheel_path:
            raise RuntimeError("Exact public49 baseline wheel path is required")
        baseline_wheel_binding = _verify_baseline_wheel(
            wheel_path, package, truss, privileges, catalog_runtime
        )
    if phase == "baseline" and package["sourceFreeze"] is not None:
        raise RuntimeError(
            "Baseline must resolve from the installed distribution, not source"
        )
    if phase == "candidate" and package["sourceFreeze"] is None:
        raise RuntimeError("Candidate must resolve from the selected source tree")
    _require_server_version_profile(SERVER_VERSION, SERVER_VERSION_NUM)

    fixture = DatabaseFixture(worker_root)
    recorder: dict[str, Any] = {
        "cursorExecuteCount": 0,
        "cursorExecuteElapsedNs": 0,
        "cursorExecuteMaxNs": 0,
        "cursorNextsetCount": 0,
        "cursorNextsetElapsedNs": 0,
        "cursorNextsetMaxNs": 0,
        "cursorNextsetFailureCount": 0,
        "installAttempted": False,
        "installElapsedNs": 0,
        "installerProcessCpuElapsedNs": 0,
        "orderedDdlHelperCalls": 0,
        "orderedDdlUnits": 0,
        "orderedDdlExecuteSubmissions": 0,
        "orderedDdlSourceUnitCount": 0,
        "orderedDdlOtherUnitCount": 0,
        "directSourceUnitExecuteSubmissions": 0,
        "sourceUnitHashes": {
            _sha256(unit.encode("utf8")) for unit in catalog_runtime._release()[2]
        },
    }
    connection = None
    host = None
    result: dict[str, Any] = {
        "phase": phase,
        "package": {"before": package, "after": None, "unchanged": None},
        "baselineWheel": baseline_wheel_binding,
        "budgetsMs": {"statement": 60000, "operation": 60000},
        "installation": {"status": "not_started"},
        "caller": {},
        "nativeAbsence": {},
        "measurement": None,
        "snapshot": None,
        "failureStage": None,
        "failureType": None,
    }
    stage = "fixture"
    try:
        uri = fixture.get_uri()
        if not isinstance(uri, str):
            raise TypeError("Fresh fixture connection URI must be text")
        connection = psycopg.connect(
            uri, autocommit=True, options="-c statement_timeout=60000"
        )
        server = connection.execute(
            "SELECT pg_catalog.current_setting('server_version_num')"
        ).fetchone()
        if server != (EXPECTED_SERVER_VERSION,):
            raise RuntimeError("Selected PostgreSQL 18.6 worker required")
        initial = connection.execute(
            """SELECT pg_catalog.to_regnamespace('truss') IS NOT NULL,
                      EXISTS(SELECT 1 FROM pg_catalog.pg_roles
                             WHERE rolname IN (%s,%s))""",
            (OWNER_ROLE, CLIENT_ROLE),
        ).fetchone()
        if initial is None or initial != (False, False):
            raise RuntimeError("Fresh installation namespace and roles required")
        result["nativeAbsence"]["before"] = {
            "trussSchema": initial[0],
            "fixedRoles": initial[1],
        }
        connection.execute(
            "CREATE TABLE public.installer_roundtrip_sentinel(id integer PRIMARY KEY, value text NOT NULL)"
        )
        connection.execute(
            "INSERT INTO public.installer_roundtrip_sentinel VALUES (1,'committed-caller-row')"
        )
        connection.execute("BEGIN")
        connection.execute(
            "INSERT INTO public.installer_roundtrip_sentinel VALUES (2,'pending-caller-row')"
        )
        result["caller"]["stateBeforeInstall"] = _caller_state(connection)
        host = adopt_psycopg_host(
            connection, statement_timeout_ms=60000, operation_timeout_ms=60000
        )
        tx_result = host.adopt_transaction()
        if not isinstance(tx_result, Ok):
            raise TypeError("Original caller transaction adoption failed")
        assembly_result = create_reference_assembly(CatalogRuntimeConfiguration(), host)
        if not isinstance(assembly_result, Ok):
            raise TypeError("Reference assembly construction failed")
        assembly = assembly_result.value
        stage = "install"
        token = _ACTIVE_MEASUREMENT.set(recorder)
        primary_error: BaseException | None = None
        try:
            _measure_cursor_execute(psycopg, recorder)
            _measure_ordered_ddl(catalog_runtime, recorder)
            _measure_ordered_ddl(privileges, recorder)
            installed = _call_measured_install(
                recorder,
                lambda: assembly.install_in_transaction(
                    tx_result.value, owner_role=OWNER_ROLE, registrar_role=CLIENT_ROLE
                ),
            )
        except BaseException as error:
            primary_error = error
            raise
        finally:
            _finish_measurement(
                psycopg, recorder, token, result, primary_error
            )
        if result["instrumentationHooksRestored"] is not True:
            raise RuntimeError("Measurement instrumentation was not restored")
        if isinstance(installed, Ok):
            if isinstance(installed.value, InstallRefused):
                installation_status = "refused"
                result["installation"] = {
                    "status": installation_status,
                    "resultVariant": "InstallRefused",
                    "refusalCode": installed.value.code,
                }
            elif isinstance(installed.value, PendingCatalogInstallation):
                installation_status = "success"
                result["installation"] = {
                    "status": installation_status,
                    "resultVariant": "PendingCatalogInstallation",
                    "refusalCode": None,
                }
            else:
                raise TypeError("Installer Ok result was not a pending installation")
        elif isinstance(installed, Error):
            installation_status = "failure"
            result["installation"] = {
                "status": installation_status,
                "resultVariant": "Error",
                "executionCode": installed.error.code,
                "sqlState": installed.error.sql_state,
                "catalogCode": installed.error.catalog_code,
            }
        else:
            raise TypeError("Installer returned an unknown result variant")
        result["caller"]["pendingSentinelVisibleAfterInstall"] = connection.execute(
            "SELECT value FROM public.installer_roundtrip_sentinel WHERE id=2"
        ).fetchone() == ("pending-caller-row",)
        caller_after = _caller_state(connection)
        result["caller"]["stateAfterInstall"] = caller_after
        result["caller"]["identityAndSettingsPreserved"] = (
            caller_after == result["caller"]["stateBeforeInstall"]
        )
        if installation_status == "success":
            result["snapshot"] = _installation_snapshot(connection)
            result["snapshotSha256"] = _sha256(_canonical_bytes(result["snapshot"]))
        result["caller"]["connectionQueryAfterInstall"] = connection.execute(
            "SELECT 42"
        ).fetchone() == (42,)
        stage = "rollback"
        if not host.detach():
            raise RuntimeError("Host detach was not confirmed")
        host = None
        connection.rollback()
        after = connection.execute(
            """SELECT pg_catalog.to_regnamespace('truss') IS NOT NULL,
                      EXISTS(SELECT 1 FROM pg_catalog.pg_roles
                             WHERE rolname IN (%s,%s)),
                      count(*) FILTER (WHERE id=1),count(*) FILTER (WHERE id=2)
               FROM public.installer_roundtrip_sentinel""",
            (OWNER_ROLE, CLIENT_ROLE),
        ).fetchone()
        if after is None:
            raise RuntimeError("Post-rollback caller state observation missing")
        result["nativeAbsence"]["afterRollback"] = {
            "trussSchema": after[0],
            "fixedRoles": after[1],
        }
        result["caller"]["committedSentinelRowsAfterRollback"] = after[2]
        result["caller"]["pendingSentinelRowsAfterRollback"] = after[3]
        result["caller"]["rollbackConfirmed"] = (
            after == (False, False, 1, 0)
            and result["caller"].get("pendingSentinelVisibleAfterInstall") is True
            and result["caller"].get("connectionQueryAfterInstall") is True
            and result["caller"].get("identityAndSettingsPreserved") is True
        )
        if not result["caller"]["rollbackConfirmed"]:
            raise RuntimeError(
                "Caller transaction or rollback preservation check failed"
            )
        result["status"] = "measured"
        result["failureStage"] = None
    except Exception as error:  # noqa: BLE001 - report failures without leaking diagnostics
        result["status"] = "failed"
        result["failureStage"] = stage
        result["failureType"] = type(error).__name__
    finally:
        if host is not None:
            try:
                result["caller"]["hostDetachedDuringCleanup"] = bool(host.detach())
            except Exception as error:  # noqa: BLE001 - cleanup failure is recorded by type only
                result["caller"]["hostDetachFailureType"] = type(error).__name__
        if connection is not None:
            try:
                connection.rollback()
            except Exception as error:  # noqa: BLE001 - cleanup failure is recorded by type only
                result["caller"]["cleanupRollbackFailureType"] = type(error).__name__
            try:
                connection.close()
            except Exception as error:  # noqa: BLE001 - cleanup failure is recorded by type only
                result["caller"]["connectionCloseFailureType"] = type(error).__name__
        try:
            fixture.cleanup()
            result["fixtureCleanup"] = "confirmed"
        except Exception as error:  # noqa: BLE001 - cleanup failure is recorded by type only
            result["fixtureCleanup"] = "failed"
            result["fixtureCleanupFailureType"] = type(error).__name__
            result["status"] = "failed"
            result["failureStage"] = "fixture_cleanup"
            result["failureType"] = type(error).__name__
        try:
            package_after = _package_identity(truss, catalog_runtime, privileges)
            result["package"]["after"] = package_after
            result["package"]["unchanged"] = _canonical_bytes(
                package
            ) == _canonical_bytes(package_after)
            if not result["package"]["unchanged"]:
                result["status"] = "failed"
                result["failureStage"] = "package_binding"
                result["failureType"] = "PackageChangedDuringMeasurement"
        except Exception as error:  # noqa: BLE001 - retain only closed failure type
            result["package"]["afterFailureType"] = type(error).__name__
            result["status"] = "failed"
            result["failureStage"] = "package_binding"
            result["failureType"] = type(error).__name__
    return result


def _child(phase: str) -> int:
    worker = os.environ.get("TRUSS_NATIVE_WORKER")
    if not worker:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "failureStage": "worker",
                    "failureType": "MissingWorker",
                }
            )
        )
        return 2
    try:
        result = _install_once(Path(worker), phase)
    except Exception as error:  # noqa: BLE001 - child reports only a closed failure type
        result = {
            "phase": phase,
            "status": "failed",
            "failureStage": "package_import_or_preflight",
            "failureType": type(error).__name__,
            "fixtureCleanup": "not_started",
        }
    encoded = json.dumps(
        result, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    if len(encoded.encode("utf8")) > CHILD_OUTPUT_LIMIT_BYTES:
        print(
            json.dumps(
                {
                    "phase": phase,
                    "status": "failed",
                    "failureStage": "child_output_bound",
                    "failureType": "ChildOutputLimitExceeded",
                    "fixtureCleanup": result.get("fixtureCleanup", "unknown"),
                },
                separators=(",", ":"),
            )
        )
        return 2
    print(encoded)
    installation = _object(result.get("installation"))
    caller = _object(result.get("caller"))
    package = _object(result.get("package"))
    return (
        0
        if result.get("status") == "measured"
        and installation.get("status") == "success"
        and installation.get("resultVariant") == "PendingCatalogInstallation"
        and caller.get("rollbackConfirmed") is True
        and result.get("fixtureCleanup") == "confirmed"
        and package.get("unchanged") is True
        and result.get("instrumentationHooksRestored") is True
        else 2
    )


def _child_environment(
    phase: str, worker_root: str, baseline_wheel: Path
) -> dict[str, str]:
    environment = dict(os.environ)
    environment["TRUSS_NATIVE_WORKER"] = worker_root
    environment.pop("PYTHONPATH", None)
    environment["TRUSS_MEASURE_BASELINE_WHEEL"] = str(baseline_wheel)
    if phase == "candidate":
        environment["PYTHONPATH"] = str(SOURCE_ROOT)
    return environment


def _child_group_alive(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    return True


def _wait_child_group(process_group_id: int, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while _child_group_alive(process_group_id):
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)
    return True


def _stop_child_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except PermissionError as error:
        raise RuntimeError("Cannot signal owned child process group") from error
    try:
        process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    if not _wait_child_group(process.pid, 3):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            raise RuntimeError("Cannot kill owned child process group") from error
        try:
            process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            pass
        if not _wait_child_group(process.pid, 3):
            raise RuntimeError("Owned child process group remained after SIGKILL")
    if process.poll() is None:
        process.wait(timeout=3)
    if _child_group_alive(process.pid):
        raise RuntimeError("Owned child process group remains after cleanup")


def _bounded_child_output(
    process: subprocess.Popen[str], timeout_seconds: float
) -> tuple[bytes, bool, bool]:
    if process.stdout is None:
        raise RuntimeError("Child output pipe is required")
    output = bytearray()
    selector = selectors.DefaultSelector()
    descriptor = process.stdout.fileno()
    os.set_blocking(descriptor, False)
    selector.register(descriptor, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout_seconds
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return bytes(output), True, False
            events = selector.select(min(remaining, 0.1))
            if not events:
                if process.poll() is not None:
                    break
                continue
            for key, _ in events:
                chunk = os.read(
                    key.fd,
                    min(65536, CHILD_OUTPUT_LIMIT_BYTES + 1 - len(output)),
                )
                if not chunk:
                    selector.unregister(key.fd)
                    continue
                output.extend(chunk)
                if len(output) > CHILD_OUTPUT_LIMIT_BYTES:
                    return bytes(output), False, True
        try:
            process.wait(timeout=max(0.001, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            return bytes(output), True, False
        return bytes(output), False, False
    finally:
        selector.close()


def _run_child(phase: str, worker_root: str, baseline_wheel: Path) -> dict[str, Any]:
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--phase", phase],
        cwd=ROOT,
        env=_child_environment(phase, worker_root, baseline_wheel),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )
    try:
        stdout_bytes, timed_out, output_over_limit = _bounded_child_output(
            process, CHILD_TIMEOUT_SECONDS
        )
    except BaseException as primary:
        try:
            _stop_child_group(process)
        except BaseException as cleanup_error:  # noqa: BLE001 - preserve primary cancellation
            primary.add_note(
                "Owned child cleanup also failed: " + type(cleanup_error).__name__
            )
        raise
    if timed_out:
        _stop_child_group(process)
        if process.stdout is not None:
            process.stdout.close()
        return {
            "phase": phase,
            "status": "failed",
            "failureStage": "child_timeout",
            "failureType": "ChildTimeoutExpired",
            "childExitCode": process.returncode,
        }
    if output_over_limit:
        try:
            _stop_child_group(process)
        except BaseException as cleanup_error:  # noqa: BLE001 - report owned-group cleanup failure
            if process.stdout is not None and not process.stdout.closed:
                process.stdout.close()
            return {
                "phase": phase,
                "status": "failed",
                "failureStage": "child_cleanup",
                "failureType": type(cleanup_error).__name__,
                "childExitCode": process.returncode,
            }
        if process.stdout is not None and not process.stdout.closed:
            process.stdout.close()
        return {
            "phase": phase,
            "status": "failed",
            "failureStage": "child_output_bound",
            "failureType": "ChildOutputLimitExceeded",
            "childExitCode": process.returncode,
        }
    if process.stdout is not None:
        process.stdout.close()
    if not _wait_child_group(process.pid, 0.1):
        _stop_child_group(process)
        return {
            "phase": phase,
            "status": "failed",
            "failureStage": "child_process_group",
            "failureType": "UnexpectedChildDescendant",
            "childExitCode": process.returncode,
        }
    stdout = stdout_bytes.decode("utf8", errors="replace")
    lines = stdout.splitlines()
    if len(lines) != 1:
        return {
            "phase": phase,
            "status": "failed",
            "failureStage": "child_protocol",
            "failureType": "InvalidChildOutput",
            "childExitCode": process.returncode,
        }
    try:
        value = json.loads(lines[0])
    except json.JSONDecodeError:
        value = {
            "phase": phase,
            "status": "failed",
            "failureStage": "child_protocol",
            "failureType": "InvalidChildJson",
            "childExitCode": process.returncode,
        }
    if not isinstance(value, dict):
        value = {
            "phase": phase,
            "status": "failed",
            "failureStage": "child_protocol",
            "failureType": "InvalidChildJsonShape",
            "childExitCode": process.returncode,
        }
    value["childExitCode"] = process.returncode
    return value


def _reserve_output(path: Path) -> int:
    if not path.parent.is_dir():
        raise ValueError("Output parent directory must already exist")
    return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)


def _write_reserved(descriptor: int, path: Path, value: dict[str, Any]) -> None:
    encoded = _canonical_bytes(value) + b"\n"
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(encoded)
            output.flush()
            os.fsync(output.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _verify_external_worker_baseline(worker_root: str) -> bool:
    from native_fixture import connect, inventory

    root = Path(worker_root)
    owner_path = root / "owner.json"
    if not owner_path.is_file():
        raise RuntimeError("External worker ownership record is unavailable")
    owner = json.loads(owner_path.read_text(encoding="utf8"))
    uri = owner.get("uri") if isinstance(owner, dict) else None
    baseline = owner.get("baseline") if isinstance(owner, dict) else None
    if type(uri) is not str or not uri or not isinstance(baseline, dict):
        raise RuntimeError("External worker baseline record is invalid")
    admin = connect(uri)
    try:
        return inventory(admin) == baseline
    finally:
        admin.close()


def _orchestrate(output: Path, baseline_wheel: Path) -> int:
    output_fd = _reserve_output(output)
    external_worker = os.environ.get("TRUSS_NATIVE_WORKER")
    worker_context: Any = None
    worker_started = False
    worker_root = external_worker
    report: dict[str, Any] = {
        "schemaVersion": 1,
        "createdAtUtc": datetime.now(UTC).isoformat(),
        "diagnostic": "truss-installer-client-submissions/0.1",
        "workerScope": "passed_owned_TRUSS_NATIVE_WORKER"
        if external_worker
        else "script_owned_WorkerCluster",
        "workerCleanup": "not_started",
        "workerBaselineRestored": False,
        "workerShutdown": "not_started",
        "postgresProfile": EXPECTED_SERVER_VERSION,
        "psycopgProfile": "stock psycopg 3.3.6, binary libpq",
        "measurements": {},
        "comparison": {
            "status": "unavailable",
            "baselineSnapshotSha256": None,
            "candidateSnapshotSha256": None,
            "snapshotEqual": None,
        },
        "scope": [
            "Two serial fresh DatabaseFixture databases on one owned PG18.6 worker.",
            "Only the exact public Cursor.execute call is wrapped, delegated unchanged, and timed client-side.",
            "Instrumentation records no submitted SQL text, connection URI, or parameters. The normalized native snapshot includes installed routine definitions, but no server or wire timings.",
            "A captured source unit may contain multiple SQL statements; counts are units and Cursor.execute submissions, not parsed SQL statements.",
            "Both installation attempts use the explicitly reported 60000 ms statement and operation budgets and are fully rolled back.",
            "The installed-object snapshot preserves rows and sequence states; it normalizes only generated installation_id/source_epoch UUIDs, genesis_at and its source-identical schema_rev.accepted_at, and owner/registrar OIDs after exact fixed-role binding.",
        ],
    }
    worker_error: Exception | None = None
    primary_interruption: BaseException | None = None
    cleanup_interruption: BaseException | None = None
    report_interruption: BaseException | None = None
    report_written = False
    try:
        try:
            if worker_root is None:
                # Import only after baseline sys.path was selected; this fixture imports Truss.
                if any(
                    Path(item or ".").resolve() == SOURCE_ROOT.resolve()
                    for item in sys.path
                ):
                    sys.path[:] = [
                        item
                        for item in sys.path
                        if Path(item or ".").resolve() != SOURCE_ROOT.resolve()
                    ]
                from native_fixture import WorkerCluster

                worker_context = WorkerCluster()
                worker_context.__enter__()
                worker_started = True
                worker_root = str(worker_context.root)
            baseline = _run_child("baseline", worker_root, baseline_wheel)
            candidate = _run_child("candidate", worker_root, baseline_wheel)
            report["measurements"] = {"baseline": baseline, "candidate": candidate}
            if worker_context is not None and worker_started:
                worker_context.verify_clean()
                report["workerBaselineRestored"] = True
            elif external_worker:
                report["workerBaselineRestored"] = _verify_external_worker_baseline(
                    external_worker
                )
            if not report["workerBaselineRestored"]:
                raise RuntimeError("Worker inventory did not return to its baseline")
            if (
                baseline.get("snapshot") is not None
                and candidate.get("snapshot") is not None
            ):
                same = baseline["snapshotSha256"] == candidate["snapshotSha256"]
                report["comparison"] = {
                    "status": "equal" if same else "different",
                    "baselineSnapshotSha256": baseline["snapshotSha256"],
                    "candidateSnapshotSha256": candidate["snapshotSha256"],
                    "snapshotEqual": same,
                }
        except BaseException as error:  # noqa: BLE001 - report only closed failure type
            if isinstance(error, Exception):
                worker_error = error
            else:
                primary_interruption = error
            report["workerSetupFailureType"] = type(error).__name__
    finally:
        if worker_context is not None and worker_started:
            try:
                worker_context.__exit__(None, None, None)
                report["workerShutdown"] = (
                    "confirmed"
                    if not Path(worker_context.root).exists()
                    else "unconfirmed"
                )
                report["workerCleanup"] = (
                    "confirmed"
                    if report["workerShutdown"] == "confirmed"
                    and report["workerBaselineRestored"] is True
                    else "failed"
                )
                if report["workerCleanup"] != "confirmed":
                    worker_error = RuntimeError("Owned worker cleanup unconfirmed")
            except BaseException as error:  # noqa: BLE001 - retain cancellation through cleanup
                report["workerCleanup"] = "failed"
                report["workerShutdown"] = "failed"
                report["workerCleanupFailureType"] = type(error).__name__
                if primary_interruption is not None:
                    primary_interruption.add_note(
                        "Worker shutdown also failed: " + type(error).__name__
                    )
                elif isinstance(error, Exception):
                    worker_error = error
                else:
                    cleanup_interruption = error
        elif external_worker:
            report["workerShutdown"] = "not_owned"
            report["workerCleanup"] = (
                "baseline_restored_external_owner"
                if report["workerBaselineRestored"] is True
                else "failed"
            )
        else:
            report["workerCleanup"] = (
                "start_failed" if worker_context else "not_started"
            )
        measurements = report.get("measurements", {})
        baseline = measurements.get("baseline", {})
        candidate = measurements.get("candidate", {})
        comparison = report["comparison"]
        gate_passed = (
            worker_error is None
            and primary_interruption is None
            and cleanup_interruption is None
            and baseline.get("childExitCode") == 0
            and candidate.get("childExitCode") == 0
            and baseline.get("installation", {}).get("status") == "success"
            and baseline.get("installation", {}).get("resultVariant")
            == "PendingCatalogInstallation"
            and candidate.get("installation", {}).get("status") == "success"
            and candidate.get("installation", {}).get("resultVariant")
            == "PendingCatalogInstallation"
            and baseline.get("caller", {}).get("rollbackConfirmed") is True
            and candidate.get("caller", {}).get("rollbackConfirmed") is True
            and baseline.get("fixtureCleanup") == "confirmed"
            and candidate.get("fixtureCleanup") == "confirmed"
            and baseline.get("package", {}).get("unchanged") is True
            and candidate.get("package", {}).get("unchanged") is True
            and baseline.get("baselineWheel", {}).get("wheelSha256")
            == BASELINE_WHEEL_SHA256
            and baseline.get("baselineWheel", {}).get("payloadMembersEqual") is True
            and baseline.get("instrumentationHooksRestored") is True
            and candidate.get("instrumentationHooksRestored") is True
            and comparison.get("snapshotEqual") is True
            and report["workerBaselineRestored"] is True
            and report["workerCleanup"]
            in ("confirmed", "baseline_restored_external_owner")
        )
        report["status"] = "passed" if gate_passed else "failed"
        try:
            _write_reserved(output_fd, output, report)
            report_written = True
        except BaseException as error:  # noqa: BLE001 - preserve earlier interruption
            report_interruption = error
            if primary_interruption is not None:
                primary_interruption.add_note(
                    "Writing diagnostic report also failed: " + type(error).__name__
                )
            elif cleanup_interruption is not None:
                cleanup_interruption.add_note(
                    "Writing diagnostic report also failed: " + type(error).__name__
                )
        finally:
            if not report_written:
                try:
                    os.close(output_fd)
                except OSError:
                    pass
                try:
                    output.unlink()
                except OSError:
                    pass
    if primary_interruption is not None:
        if cleanup_interruption is not None:
            primary_interruption.add_note(
                "Worker cleanup interruption also occurred: "
                + type(cleanup_interruption).__name__
            )
        raise primary_interruption.with_traceback(primary_interruption.__traceback__)
    if cleanup_interruption is not None:
        raise cleanup_interruption.with_traceback(cleanup_interruption.__traceback__)
    if report_interruption is not None:
        raise report_interruption.with_traceback(report_interruption.__traceback__)
    return 0 if gate_passed else 1


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline-wheel", type=Path)
    parser.add_argument(
        "--phase", choices=("baseline", "candidate"), help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    if args.phase is None and (args.output is None or args.baseline_wheel is None):
        parser.error("--output and --baseline-wheel are required")
    if args.phase is not None and (
        args.output is not None or args.baseline_wheel is not None
    ):
        parser.error(
            "--output and --baseline-wheel are only valid in orchestrator mode"
        )
    return args


def main() -> int:
    args = _arguments()
    if args.phase is not None:
        return _child(args.phase)
    return _orchestrate(
        Path(os.path.abspath(args.output)), Path(os.path.abspath(args.baseline_wheel))
    )


if __name__ == "__main__":
    raise SystemExit(main())
