"""Native preparation authority *component*, not a fixed-cut/seal issuer.

Trusted engine capture and independently qualified source-head/DDL custody are
premises. All supplied comparison objects remain non-authoritative. Ordinary
READ COMMITTED facades stay unchanged. No public activation, lease or seal is
issued until original data/authority/source/completion custody is composed.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from uuid import uuid4
from psycopg import sql
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_subject_installation import _text_rows


@dataclass(frozen=True, slots=True)
class PendingPreparationAuthorityLock:
    installation_id: str
    owner_oid: int
    caller_oid: int
    source_sha256: str
    status: str = 'pending_commit'
    security_ready: bool = False


@dataclass(frozen=True, slots=True)
class PreparationDataComparison:
    """Native comparison copied inside original guarded engine cursor; no lease."""
    identity: tuple[str, ...]
    challenge: str
    previous_application_name: str
    security_ready: bool = False


def _data_identity(cursor):
    if _text_rows(cursor, "SELECT pg_catalog.current_setting('server_version_num')::text,pg_catalog.current_setting('transaction_isolation')::text,pg_catalog.current_setting('transaction_read_only')::text,pg_catalog.current_setting('role')::text", limit=1) != [('180006', 'repeatable read', 'off', 'none')]:
        raise ValueError('Original writable RR preparation context required')
    rows = _text_rows(cursor, """SELECT a.datid::text,a.usesysid::text,a.pid::text,
        a.backend_start::text,a.xact_start::text,pg_catalog.pg_current_xact_id()::text,
        pg_catalog.pg_current_snapshot()::text,current_user::text,session_user::text
        FROM pg_catalog.pg_stat_activity a WHERE a.pid=pg_catalog.pg_backend_pid()""", limit=1)
    if len(rows) != 1 or rows[0][7] != rows[0][8]:
        raise ValueError('Original preparation caller identity required')
    return tuple(rows[0])


def capture_preparation_data_with_cursor(cursor):
    """Engine-only, bounded native capture; never accepts a claimed principal."""
    identity = _data_identity(cursor)
    previous = _text_rows(cursor, "SELECT pg_catalog.current_setting('application_name')::text", limit=1)
    if len(previous) != 1:
        raise ValueError('Original preparation caller context required')
    challenge = 'truss-preparation-' + str(uuid4())
    if _text_rows(cursor, "SELECT pg_catalog.set_config('application_name',%s,true)::text", (challenge,), 1) != [(challenge,)]:
        raise ValueError('Original preparation challenge required')
    return PreparationDataComparison(identity, challenge, previous[0][0])


def verify_preparation_data_with_cursor(cursor, original):
    if type(original) is not PreparationDataComparison or _data_identity(cursor) != original.identity:
        raise ValueError('Original preparation data custody changed')
    if _text_rows(cursor, "SELECT pg_catalog.current_setting('application_name')::text", limit=1) != [(original.challenge,)]:
        raise ValueError('Original preparation context challenge changed')


def verify_preparation_peer_with_cursor(cursor, original):
    """Fresh original native peer comparison, not source/authority admission."""
    if type(original) is not PreparationDataComparison:
        raise ValueError('Original preparation data comparison required')
    if _text_rows(cursor, "SELECT pg_catalog.current_setting('transaction_isolation')::text,pg_catalog.current_setting('transaction_read_only')::text", limit=1) != [('read committed', 'off')]:
        raise ValueError('Fresh preparation coordinator context required')
    # Statistics snapshots must not hide an observed context/end change.
    cursor.execute('SELECT pg_catalog.pg_stat_clear_snapshot()', prepare=False)
    rows = _text_rows(cursor, """SELECT a.datid::text,a.usesysid::text,a.pid::text,
        a.backend_start::text,a.xact_start::text,a.application_name::text,
        (a.backend_xid::text=pg_catalog.mod(%s::numeric,4294967296)::text)::text
        FROM pg_catalog.pg_stat_activity a WHERE a.pid=%s::int4
        AND a.datid=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())
        AND a.state IN ('active','idle in transaction')""",
        (original.identity[5], original.identity[2]), 1)
    if rows != [(*original.identity[:5], original.challenge, 'true')]:
        raise ValueError('Original live preparation peer/cut custody required')


@dataclass(frozen=True, slots=True)
class PreparationOwnerObservation:
    """Whole current catalog owner observation, not an admitted operation scope."""
    installation_id: str
    revision: str
    caller_oid: str
    owners: tuple[tuple[str, str, str, str, str], ...]
    security_ready: bool = False


def observe_preparation_owners_with_cursor(cursor, issuer, original):
    """Current native caller/module grants; no consumer-authored owner union.

    Source/head exclusion and exact frozen/current source correspondence must be
    composed separately. This conservative component enumerates *every* module
    in latest accepted documents, not just the modules a caller names. It does
    not establish selected field/relationship/history or ontology action scope.
    """
    acquire_preparation_authority_lock_with_cursor(cursor, issuer)
    verify_preparation_peer_with_cursor(cursor, original)
    header = _text_rows(cursor, """SELECT i.installation_id::text,h.rev::text,
        i.owner_oid::text FROM truss.catalog_runtime_installation i
        CROSS JOIN truss.schema_head h WHERE i.singleton AND h.id=1""", limit=1)
    if len(header) != 1 or header[0][0] != issuer.installation_id:
        raise ValueError('Original current preparation installation required')
    caller = _text_rows(cursor, """SELECT r.oid::text,r.rolname::text,
        r.rolcanlogin::text,r.rolsuper::text,r.rolcreaterole::text,
        r.rolcreatedb::text,r.rolreplication::text,r.rolbypassrls::text,
        pg_catalog.pg_has_role(r.oid,%s::pg_catalog.oid,'MEMBER')::text
        FROM pg_catalog.pg_roles r WHERE r.oid=%s::pg_catalog.oid""",
        (header[0][2], original.identity[1]), 1)
    if caller != [(original.identity[1], original.identity[8], 'true',
                   'false', 'false', 'false', 'false', 'false', 'false')]:
        raise ValueError('Original ordinary current preparation person required')
    owners = _text_rows(cursor, """WITH RECURSIVE memberships(role_oid) AS (
        SELECT %s::pg_catalog.oid UNION
        SELECT m.roleid FROM pg_catalog.pg_auth_members m
        JOIN memberships p ON m.member=p.role_oid)
        SELECT d.doc_id::text,(m.value->>'id')::text,
        p.reader_role::text,p.writer_role::text,
        EXISTS(SELECT 1 FROM pg_catalog.pg_roles r JOIN memberships s
            ON s.role_oid=r.oid WHERE r.rolname::text IN(p.reader_role,p.writer_role))::text
        FROM truss.schema_doc d
        CROSS JOIN LATERAL pg_catalog.jsonb_array_elements(d.document::pg_catalog.jsonb->'modules') m(value)
        LEFT JOIN truss.module_access p ON p.document_id=d.doc_id AND p.module=m.value->>'id'
        WHERE d.rev<=%s::pg_catalog.int4 AND d.rev=(SELECT max(latest.rev)
            FROM truss.schema_doc latest WHERE latest.doc_id=d.doc_id AND latest.rev<=%s::pg_catalog.int4)
        ORDER BY d.doc_id COLLATE pg_catalog."C",(m.value->>'id') COLLATE pg_catalog."C"
        """,
        (original.identity[1], header[0][1], header[0][1]), 256)
    if (not owners or len({row[:2] for row in owners}) != len(owners)
            or any(any(not value or len(value.encode()) > 4096 for value in row[:4])
                   for row in owners)):
        raise ValueError('Complete bounded original preparation owners required')
    verify_preparation_peer_with_cursor(cursor, original)
    return PreparationOwnerObservation(header[0][0], header[0][1], original.identity[1], tuple(owners))


_SOURCE_SHA256 = '8105c84fa96b7afbfd9cedb01a6aef0fdecaaf1dec5d53b80804e0f0f2095481'

def _source():
    raw = files('truss').joinpath('_security_bootstrap', 'preparation-authority-lock.sql').read_bytes()
    if sha256(raw).hexdigest() != _SOURCE_SHA256:
        raise ValueError('Original preparation lock source pin required')
    return raw


def _verify(cursor, issuer):
    if type(issuer) is not PendingPreparationAuthorityLock:
        raise ValueError('Original preparation lock comparison required')
    raw = _source()
    if sha256(raw).hexdigest() != issuer.source_sha256:
        raise ValueError('Original preparation lock source required')
    body = raw.decode().split('AS $$', 1)[1].split('$$;', 1)[0]
    rows = _text_rows(cursor, """SELECT p.proowner::text,l.lanname::text,
        p.prokind::text,p.pronargs::text,p.proargtypes::text,p.prorettype::text,
        p.proretset::text,p.prosecdef::text,p.provolatile::text,p.proparallel::text,
        p.proleakproof::text,p.prosupport::oid::text,pg_catalog.to_jsonb(p.proconfig)::text,
        p.prosrc,(p.prosqlbody IS NULL)::text
        FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
        JOIN pg_catalog.pg_language l ON l.oid=p.prolang
        WHERE n.nspname='truss' AND p.proname='acquire_preparation_authority_lock'""", limit=1)
    if rows != [(str(issuer.owner_oid), 'plpgsql', 'f', '0', '', '2278',
                 'false', 'true', 'v', 'u', 'false', '0',
                 '["search_path=pg_catalog, pg_temp"]', body, 'true')]:
        raise ValueError('Exact preparation lock definition required')
    acl = _text_rows(cursor, """SELECT a.grantee::text,a.grantor::text,
        a.privilege_type::text,a.is_grantable::text FROM pg_catalog.pg_proc p
        CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,
        pg_catalog.acldefault('f',p.proowner))) a
        WHERE p.oid='truss.acquire_preparation_authority_lock()'::regprocedure
        ORDER BY a.grantee""", limit=3)
    expected = sorted([(str(oid), str(issuer.owner_oid), 'EXECUTE', 'false')
                       for oid in (issuer.owner_oid, issuer.caller_oid)], key=lambda row: int(row[0]))
    if acl != expected:
        raise ValueError('Exact private preparation lock ACL required')
    if _text_rows(cursor, """SELECT rolsuper::text,
        pg_catalog.pg_has_role(%s::oid,oid,'MEMBER')::text
        FROM pg_catalog.pg_roles WHERE oid=%s::oid""",
        (issuer.caller_oid, issuer.owner_oid), 1) != [('true', 'false')]:
        raise ValueError('Excluded privileged preparation lock owner required')


def bootstrap_preparation_authority_lock_in_transaction(host, transaction, *, executor_role):
    if (type(host) is not PsycopgHost or type(executor_role) is not str
            or not executor_role or '\0' in executor_role or len(executor_role.encode()) > 63):
        return Error(ExecutionFailure('execution_obligation', 'Bounded preparation executor required'))
    def install(cursor, observed):
        _pin_cursor(cursor)
        if _text_rows(cursor, "SELECT pg_catalog.current_setting('server_version_num')::text,pg_catalog.current_setting('transaction_isolation')::text,pg_catalog.current_setting('transaction_read_only')::text", limit=1) != [('180006', 'read committed', 'off')]:
            raise ValueError('Original fresh preparation lock installation required')
        target = _text_rows(cursor, 'SELECT installation_id::text,owner_oid::text FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT', limit=1)
        if len(target) != 1:
            raise ValueError('Original installation required')
        installation_administrator_with_cursor(cursor, int(target[0][1]))
        owner = _text_rows(cursor, 'SELECT oid::text FROM pg_catalog.pg_roles WHERE rolname=CURRENT_USER AND rolsuper', limit=1)
        caller = _text_rows(cursor, "SELECT oid::text,rolcanlogin::text,rolsuper::text,rolcreatedb::text,rolcreaterole::text,rolreplication::text,rolbypassrls::text FROM pg_catalog.pg_roles WHERE rolname=%s", (executor_role,), 1)
        if len(owner) != 1 or len(caller) != 1 or caller[0][1:] != ('true', 'false', 'false', 'false', 'false', 'false'):
            raise ValueError('Ordinary preparation executor and privileged installer required')
        if _text_rows(cursor, "SELECT oid::text FROM pg_catalog.pg_proc WHERE pronamespace='truss'::regnamespace AND proname='acquire_preparation_authority_lock'", limit=1):
            raise ValueError('Existing preparation lock requires explicit migration')
        raw = _source()
        cursor.execute(raw.decode(), prepare=False)
        cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.acquire_preparation_authority_lock() TO {}').format(sql.Identifier(executor_role)), prepare=False)
        cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(executor_role)), prepare=False)
        issuer = PendingPreparationAuthorityLock(target[0][0], int(owner[0][0]), int(caller[0][0]), sha256(raw).hexdigest())
        _verify(cursor, issuer)
        return issuer
    return host._run_operation(transaction, install)


def acquire_preparation_authority_lock_with_cursor(cursor, issuer):
    """Locks current authority inputs; neither supplied PID nor lease is accepted."""
    _verify(cursor, issuer)
    if _text_rows(cursor, 'SELECT oid::text FROM pg_catalog.pg_roles WHERE rolname=CURRENT_USER AND rolname=SESSION_USER', limit=1) != [(str(issuer.caller_oid),)]:
        raise ValueError('Original preparation executor required')
    cursor.execute('SELECT truss.acquire_preparation_authority_lock()', prepare=False)
    if cursor.description is None or len(cursor.description) != 1 or cursor.description[0].type_code != 2278 or cursor.fetchmany(2) != [('',)]:
        raise ValueError('Exact native preparation lock VOID result required')
    held = _text_rows(cursor, """SELECT n.nspname::text,c.relname::text FROM pg_catalog.pg_locks l
        JOIN pg_catalog.pg_class c ON c.oid=l.relation
        JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE l.pid=pg_catalog.pg_backend_pid() AND l.granted AND l.mode='ShareLock'
        AND ((n.nspname='truss' AND c.relname='module_access')
          OR (n.nspname='pg_catalog' AND c.relname IN ('pg_authid','pg_auth_members')))
        ORDER BY n.nspname,c.relname""", limit=3)
    if held != [('pg_catalog', 'pg_auth_members'), ('pg_catalog', 'pg_authid'), ('truss', 'module_access')]:
        raise ValueError('Original native preparation authority exclusions required')
    _verify(cursor, issuer)
