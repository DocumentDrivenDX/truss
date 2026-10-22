# SPDX-License-Identifier: MIT OR Apache-2.0
"""Deployment-owned native Subject enrollment; never invocation authentication.

Trusted direct administrator and quiescent installation are required. SCRAM
credential exchange, role lifecycle/DDL custody and current action permission
remain separate. Caller owns COMMIT. This does not repurpose ontology Staff.
"""
from dataclasses import dataclass
from importlib.resources import files
from psycopg import sql
from .psycopg_host import PsycopgHost
from .execution import Error, ExecutionFailure
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor, require_empty_managed_grants_with_cursor
from ._security_catalog_subject_installation import _text_rows



@dataclass(frozen=True, slots=True)
class PendingActionSubjects:
    installation_id: str
    bindings: tuple[tuple[int, bytes, str], ...]
    mapping_cut: bool = False
    status: str = 'pending_commit'
    security_ready: bool = False


def bootstrap_action_subjects_in_transaction(host, transaction, *, bindings, with_action_roles=False):
    """Explicit native LOGIN→opaque identity/kind association, not a login API."""
    if (type(host) is not PsycopgHost or type(bindings) is not tuple or type(with_action_roles) is not bool
            or not 1 <= len(bindings) <= 256
            or any(type(row) is not tuple or len(row) != 3
                or type(row[0]) is not str or not row[0] or '\0' in row[0]
                or len(row[0].encode()) > 63
                or type(row[1]) is not bytes or not 1 <= len(row[1]) <= 4096
                or type(row[2]) is not str or row[2] not in ('human', 'service') for row in bindings)
            or len({row[0] for row in bindings}) != len(bindings)):
        return Error(ExecutionFailure('execution_obligation', 'Bounded original action Subject enrollment required'))

    def install(cursor, observed):
        _pin_cursor(cursor)
        require_empty_managed_grants_with_cursor(cursor, 'Action Subject')
        prior = _text_rows(cursor, "SELECT pg_catalog.current_setting('search_path')::pg_catalog.text", limit=1)
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog,pg_temp',true)", prepare=False)
        from ._current_query_protection import require_unprotected_configuration
        require_unprotected_configuration(cursor,allow_uninstalled=True)
        cursor.fetchone()
        if _text_rows(cursor, "SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only')", limit=1) != [('180006', 'read committed', 'off')]:
            raise ValueError('Original native action Subject installation context required')
        installed = _text_rows(cursor, 'SELECT installation_id::text,owner_oid::text FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT', limit=1)
        if len(installed) != 1:
            raise ValueError('Original action Subject installation required')
        identity, owner = installed[0]
        actor = installation_administrator_with_cursor(cursor, int(owner))
        if not actor[2]:
            raise ValueError('Direct trusted Subject enrollment administrator required')
        owner_row = _text_rows(cursor, 'SELECT rolname::text,rolcanlogin::text,rolsuper::text,rolcreaterole::text,rolcreatedb::text,rolreplication::text,rolbypassrls::text FROM pg_catalog.pg_roles WHERE oid=%s::oid', (owner,), 1)
        if len(owner_row) != 1 or owner_row[0][1:] != ('false',)*6:
            raise ValueError('Original private Subject owner required')
        if _text_rows(cursor, "SELECT (pg_catalog.to_regclass('truss.action_subject_binding') IS NULL)::text", limit=1) != [('true',)]:
            raise ValueError('Existing Subject enrollment requires explicit migration')
        enrolled = []
        for name, principal, kind in bindings:
            rows = _text_rows(cursor, "SELECT oid::text,rolcanlogin::text,rolsuper::text,rolcreaterole::text,rolcreatedb::text,rolreplication::text,rolbypassrls::text,pg_catalog.pg_has_role(oid,%s::oid,'MEMBER')::text FROM pg_catalog.pg_roles WHERE rolname=%s", (owner, name), 1)
            if len(rows) != 1 or rows[0][1:] != ('true','false','false','false','false','false','false'):
                raise ValueError('Original ordinary Subject login required')
            enrolled.append((int(rows[0][0]), principal, kind))
        cursor.execute('CREATE TABLE truss.action_subject_binding(installation_id uuid NOT NULL REFERENCES truss.catalog_runtime_installation(installation_id),role_oid oid PRIMARY KEY,principal_identity bytea NOT NULL CHECK(octet_length(principal_identity) BETWEEN 1 AND 4096),subject_kind text NOT NULL CHECK(subject_kind IN (\'human\',\'service\')),authentication_profile text NOT NULL CHECK(authentication_profile=\'truss.local-scram/0.1\'))', prepare=False)
        cursor.execute('REVOKE ALL ON TABLE truss.action_subject_binding FROM PUBLIC', prepare=False)
        cursor.execute(sql.SQL('ALTER TABLE truss.action_subject_binding OWNER TO {}').format(sql.Identifier(owner_row[0][0])), prepare=False)
        for oid, principal, kind in enrolled:
            cursor.execute("INSERT INTO truss.action_subject_binding VALUES(%s,%s,%s,%s,'truss.local-scram/0.1')", (identity, oid, principal, kind), prepare=False)
        acl = _text_rows(cursor, "SELECT a.grantee::text,a.grantor::text,a.privilege_type::text,a.is_grantable::text FROM pg_catalog.pg_class c CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE c.oid='truss.action_subject_binding'::regclass", limit=32)
        if not acl or any(row[0] != owner or row[1] != owner or row[3] != 'false' for row in acl):
            raise ValueError('Private original Subject enrollment ACL required')
        actual = _text_rows(cursor, "SELECT role_oid::text,pg_catalog.encode(principal_identity,'hex'),subject_kind::text,installation_id::text,authentication_profile::text FROM ONLY truss.action_subject_binding ORDER BY role_oid", limit=256)
        if actual != [(str(oid), principal.hex(), kind, identity, 'truss.local-scram/0.1') for oid, principal, kind in sorted(enrolled)]:
            raise ValueError('Exact original Subject enrollment readback required')
        source = files('truss').joinpath('_security_bootstrap', 'action-subject-cut.sql').read_bytes()
        cursor.execute(source.decode(), prepare=False)
        cursor.execute(sql.SQL('ALTER FUNCTION truss.acquire_action_subject_cut() OWNER TO {}').format(sql.Identifier(owner_row[0][0])), prepare=False)
        for name, principal, kind in bindings:
            cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(name)), prepare=False)
            cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.acquire_action_subject_cut() TO {}').format(sql.Identifier(name)), prepare=False)
        for oid, principal, kind in enrolled:
            if _text_rows(cursor, "SELECT pg_catalog.has_schema_privilege(%s::pg_catalog.oid,'truss','USAGE')::pg_catalog.text", (oid,), 1) != [('true',)]:
                raise ValueError('Original Subject cut namespace access required')
        grants = _text_rows(cursor, "SELECT a.grantee::text,a.grantor::text,a.privilege_type::text,a.is_grantable::text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid='truss.acquire_action_subject_cut()'::regprocedure ORDER BY a.grantee", limit=257)
        expected = sorted([(owner, owner, 'EXECUTE', 'false'), *[(str(oid), owner, 'EXECUTE', 'false') for oid, _, _ in enrolled]], key=lambda row: int(row[0]))
        if grants != expected:
            raise ValueError('Exact private Subject cut enrollment ACL required')
        if with_action_roles:
            for table in ('action_family_registration','action_role_binding'):
                home = _text_rows(cursor, "SELECT c.relowner::text,c.relkind::text,c.relpersistence::text,c.relrowsecurity::text,c.relforcerowsecurity::text FROM pg_catalog.pg_class c WHERE c.oid=pg_catalog.to_regclass(%s)", ('truss.'+table,), 1)
                if home != [(owner,'r','p','false','false')]:
                    raise ValueError('Original private action declaration/mapping home required')
            source = files('truss').joinpath('_security_bootstrap','action-mapping-cut.sql').read_bytes()
            cursor.execute(source.decode(),prepare=False)
            cursor.execute(sql.SQL('ALTER FUNCTION truss.acquire_action_mapping_cut() OWNER TO {}').format(sql.Identifier(owner_row[0][0])),prepare=False)
            for name, principal, kind in bindings:
                cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.acquire_action_mapping_cut() TO {}').format(sql.Identifier(name)),prepare=False)
            grants = _text_rows(cursor,"SELECT a.grantee::text,a.grantor::text,a.privilege_type::text,a.is_grantable::text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid='truss.acquire_action_mapping_cut()'::regprocedure ORDER BY a.grantee",limit=257)
            if grants != expected:
                raise ValueError('Exact combined mapping cut enrollment ACL required')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)", (prior[0][0],), prepare=False)
        if cursor.fetchone() != (prior[0][0],):
            raise ValueError('Original Subject installation context restoration required')
        return PendingActionSubjects(identity, tuple(sorted(enrolled)), mapping_cut=with_action_roles)
    return host._run_operation(transaction, install)
