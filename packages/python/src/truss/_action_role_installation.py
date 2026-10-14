"""Initial private action-role enrollment from original registry tickets.

Administrative quiescence and qualified original owner preparation are premises.
No current membership/Subject/permit or arbitrary native writer is admitted.
Complete semantic keys are compared as bytes; digest indexes route only.
"""
from dataclasses import dataclass
from psycopg import sql
from .bulk_action_gateway import ActionRegistration
from ._action_identity_codec import encode_action_role
from .psycopg_host import PsycopgHost
from .execution import Error, ExecutionFailure
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_subject_installation import _text_rows


@dataclass(frozen=True, slots=True)
class PendingActionRoles:
    installation_id: str
    store_identity: bytes
    families: int
    bindings: int
    status: str = 'pending_commit'
    security_ready: bool = False


def bootstrap_action_roles_in_transaction(host, transaction, *, registration, entries, store_identity):
    """One fresh complete enrollment; existing home requires explicit migration."""
    try:
        if (type(host) is not PsycopgHost or type(registration) is not ActionRegistration
                or type(entries) is not tuple or not 1 <= len(entries) <= 64
                or type(store_identity) is not bytes or not 1 <= len(store_identity) <= 4096):
            raise ValueError('Original registry and bounded entries required')
        selected = []
        for entry in entries:
            if type(entry) is not tuple or len(entry) != 2:
                raise ValueError('Original ticket and explicit mapping required')
            ticket, mappings = entry
            policy = registration.family_policy(ticket)
            if (type(mappings) is not tuple or len(mappings) != len(policy.roles)
                    or any(type(row) is not tuple or len(row) != 2
                        or type(row[0]) is not str or type(row[1]) is not str
                        or not row[1] or '\0' in row[1] or len(row[1].encode()) > 63
                        for row in mappings)
                    or len({encode_action_role(row[0]) for row in mappings}) != len(mappings)
                    or {encode_action_role(row[0]) for row in mappings} != {encode_action_role(role) for role in policy.roles}):
                raise ValueError('Complete exact original role mapping required')
            selected.append((policy, tuple(mappings)))
        if len({p.family_identity for p, _ in selected}) != len(selected):
            raise ValueError('One complete original binding per family required')
    except (ValueError, TypeError, UnicodeError):
        return Error(ExecutionFailure('execution_obligation', 'Original registered action role enrollment refused'))

    def install(cursor, observed):
        _pin_cursor(cursor)
        prior = _text_rows(cursor, "SELECT pg_catalog.current_setting('search_path')::pg_catalog.text", limit=1)
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog,pg_temp',true)", prepare=False)
        cursor.fetchone()
        if _text_rows(cursor, "SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only')", limit=1) != [('180006','read committed','off')]:
            raise ValueError('Original action role installer context required')
        installed = _text_rows(cursor, 'SELECT installation_id::text,owner_oid::text FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT', limit=1)
        if len(installed) != 1:
            raise ValueError('Original action role installation required')
        identity, owner = installed[0]
        if not installation_administrator_with_cursor(cursor, int(owner))[2]:
            raise ValueError('Direct trusted role enrollment administrator required')
        owners = _text_rows(cursor, 'SELECT rolname::text,rolcanlogin::text,rolsuper::text,rolcreaterole::text,rolcreatedb::text,rolreplication::text,rolbypassrls::text FROM pg_catalog.pg_roles WHERE oid=%s::oid', (owner,), 1)
        if len(owners) != 1 or owners[0][1:] != ('false',)*6:
            raise ValueError('Original excluded action role owner required')
        rows = []
        for policy, mappings in selected:
            for role, native in mappings:
                found = _text_rows(cursor, "SELECT oid::text,rolcanlogin::text,rolsuper::text,rolcreaterole::text,rolcreatedb::text,rolreplication::text,rolbypassrls::text,pg_catalog.pg_has_role(oid,%s::oid,'MEMBER')::text FROM pg_catalog.pg_roles WHERE rolname=%s", (owner, native), 1)
                if len(found) != 1 or found[0][1:] != ('false',)*7:
                    raise ValueError('Explicit ordinary NOLOGIN action role required')
                rows.append((policy.family_identity, encode_action_role(role), int(found[0][0]), policy.action_pin))
        if sum(len(store_identity)+len(family)+len(role)+len(pin)+32 for family,role,oid,pin in rows) > 4194304:
            raise ValueError('Complete native action role enrollment capacity exceeded')
        # A surrogate PK avoids PostgreSQL B-tree's per-entry size ceiling.
        # Full semantic uniqueness is established by this closed fresh producer;
        # no native mutation API is admitted. Hashes are nonunique routing only.
        cursor.execute('CREATE TABLE truss.action_role_binding(binding_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,installation_id uuid NOT NULL REFERENCES truss.catalog_runtime_installation(installation_id),store_identity bytea NOT NULL CHECK(octet_length(store_identity) BETWEEN 1 AND 4096),family_identity bytea NOT NULL CHECK(octet_length(family_identity) BETWEEN 1 AND 4096),role_identity bytea NOT NULL CHECK(octet_length(role_identity) BETWEEN 1 AND 2048),native_role_oid oid NOT NULL,original_action_pin bytea NOT NULL CHECK(octet_length(original_action_pin) BETWEEN 1 AND 1048576),profile_id text NOT NULL CHECK(profile_id=\'umf.actions.roles\'),profile_version text NOT NULL CHECK(profile_version=\'1\'))', prepare=False)
        cursor.execute('CREATE INDEX action_role_binding_route ON truss.action_role_binding(pg_catalog.sha256(family_identity),pg_catalog.sha256(role_identity))', prepare=False)
        cursor.execute('REVOKE ALL ON truss.action_role_binding FROM PUBLIC', prepare=False)
        cursor.execute(sql.SQL('ALTER TABLE truss.action_role_binding OWNER TO {}').format(sql.Identifier(owners[0][0])), prepare=False)
        for family, role, oid, pin in rows:
            cursor.execute("INSERT INTO truss.action_role_binding(installation_id,store_identity,family_identity,role_identity,native_role_oid,original_action_pin,profile_id,profile_version) VALUES(%s,%s,%s,%s,%s,%s,'umf.actions.roles','1')", (identity,store_identity,family,role,oid,pin), prepare=False)
        actual = _text_rows(cursor, "SELECT pg_catalog.encode(family_identity,'hex'),pg_catalog.encode(role_identity,'hex'),native_role_oid::text,pg_catalog.encode(original_action_pin,'hex'),installation_id::text,pg_catalog.encode(store_identity,'hex') FROM ONLY truss.action_role_binding ORDER BY family_identity,role_identity", limit=4096)
        expected = [(family.hex(),role.hex(),str(oid),pin.hex(),identity,store_identity.hex()) for family,role,oid,pin in sorted(rows)]
        if actual != expected:
            raise ValueError('Complete original native action role readback required')
        acl = _text_rows(cursor, "SELECT a.grantee::text,a.grantor::text,a.is_grantable::text FROM pg_catalog.pg_class c CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault(CASE WHEN c.relkind='S' THEN 'S'::\"char\" ELSE 'r'::\"char\" END,c.relowner))) a WHERE c.oid IN ('truss.action_role_binding'::regclass,'truss.action_role_binding_binding_id_seq'::regclass)", limit=32)
        if not acl or any(row != (owner,owner,'false') for row in acl):
            raise ValueError('Private native role mapping and allocator ACL required')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)", (prior[0][0],), prepare=False)
        if cursor.fetchone() != (prior[0][0],):
            raise ValueError('Original role installer namespace restoration required')
        return PendingActionRoles(identity, store_identity, len(selected), len(rows))
    return host._run_operation(transaction, install)
