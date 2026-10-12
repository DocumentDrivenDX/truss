"""Private one-time candidate security-home installation; no policy activation.

Direct trusted installation administrator and administrative quiescence required.
The supplied profile is authored configuration, not authenticated issuer evidence.
The caller settles the original transaction. No reuse, repair or migration.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from psycopg import sql
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from ._installation_privileges import installation_administrator_with_cursor
from .catalog_runtime import _release, _pin_cursor

_SOURCES = {'guard.sql': '0e1d881a2eccbcaf3d34ab8c4729a1aa21361c8c64b4ac142d706ee1da1312cf', 'claims.sql': '09515ed389247cea307ca04fc4ef45f90213a7881cd489758e5a1f854ce8e323', 'capacity.sql': '1ce1e6680dc681134423120e005df9161232e61fe1495495da177b82dbf69474'}
_HOMES = ('policy_generation_guard','policy_publication_claim','policy_publication_capacity')

@dataclass(frozen=True, slots=True)
class PendingSecurityHomes:
    installation_identity: bytes
    authored_profile: bytes
    max_retained: int
    status: str = 'pending_commit'
    security_ready: bool = False


def bootstrap_security_homes_in_transaction(host, transaction, *, installation_identity,
                                           authored_profile, max_retained):
    if (type(host) is not PsycopgHost or type(installation_identity) is not bytes
            or not 1 <= len(installation_identity) <= 32768
            or type(authored_profile) is not bytes or not 1 <= len(authored_profile) <= 32768
            or type(max_retained) is not int or not 1 <= max_retained <= 1048576):
        return Error(ExecutionFailure('execution_obligation','Exact bounded security-home configuration required'))
    def install(cursor, observed):
        _pin_cursor(cursor)
        manifest,release_digest,_ = _release()
        cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False)
        original_path=cursor.fetchone()[0]
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        cursor.execute("SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only')",prepare=False)
        if cursor.fetchone() != (manifest['postgresVersion'],'read committed','off'):
            raise ValueError('Original read-write read-committed supported server required')
        # Serializes participating installation work; not a complete authority fence.
        cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR UPDATE',prepare=False)
        if len(cursor.fetchall()) != 1:raise ValueError('Original installation head required')
        cursor.execute('SELECT installation_id::text,owner_oid,release_id,release_sha256 FROM truss.catalog_runtime_installation FOR SHARE',prepare=False)
        rows=cursor.fetchall()
        if len(rows)!=1:raise ValueError('Unique original installation required')
        identity,owner,release_id,digest=rows[0]
        cursor.execute('SELECT release_id,release_sha256 FROM truss.runtime_current_installation()',prepare=False)
        current=cursor.fetchall()
        if identity.encode('utf8')!=installation_identity or current!=[(manifest['releaseId'],release_digest)]:
            raise ValueError('Original installed release and identity correspondence required')
        actor=installation_administrator_with_cursor(cursor,owner)
        cursor.execute("SELECT nspowner FROM pg_catalog.pg_namespace WHERE nspname='truss'",prepare=False)
        if cursor.fetchone()!=(owner,):raise ValueError('Original installation namespace owner required')
        cursor.execute('SELECT rolname::text,rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolinherit FROM pg_catalog.pg_roles WHERE oid=%s',(owner,),prepare=False)
        owner_row=cursor.fetchone()
        if owner_row is None or owner_row[1:]!=(False,False,False,False,False,False,False):
            raise ValueError('Original private installation owner required')
        cursor.execute("SELECT relname FROM pg_catalog.pg_class WHERE relnamespace='truss'::regnamespace AND relname=ANY(%s)",(list(_HOMES),),prepare=False)
        if cursor.fetchall():raise ValueError('Existing security homes require original migration; no repair')
        for name,digest in _SOURCES.items():
            raw=files('truss').joinpath('_security_bootstrap',name).read_bytes()
            if sha256(raw).hexdigest()!=digest:raise ValueError('Original security-home source digest required')
            cursor.execute(raw.decode('utf8'),prepare=False)
        for home in _HOMES:
            # Default third-party grants are not erased to hide an unsafe setup.
            cursor.execute("SELECT a.grantee FROM pg_catalog.pg_class c CROSS JOIN LATERAL pg_catalog.aclexplode(c.relacl) a WHERE c.oid=%s::regclass",('truss.'+home,),prepare=False)
            if any(row[0] not in (0,actor[0]) for row in cursor.fetchall()):
                raise ValueError('Third-party security-home grant refused')
            cursor.execute(sql.SQL('ALTER TABLE truss.{} OWNER TO {}').format(sql.Identifier(home),sql.Identifier(owner_row[0])),prepare=False)
            cursor.execute(sql.SQL('REVOKE ALL ON truss.{} FROM PUBLIC').format(sql.Identifier(home)),prepare=False)
            cursor.execute("SELECT c.relowner,a.grantee FROM pg_catalog.pg_class c LEFT JOIN LATERAL pg_catalog.aclexplode(c.relacl) a ON true WHERE c.oid=%s::regclass",('truss.'+home,),prepare=False)
            if any(o!=owner or g not in (None,owner) for o,g in cursor.fetchall()):
                raise ValueError('Exact private security-home ownership and ACL required')
        cursor.execute('INSERT INTO truss.policy_generation_guard VALUES(1,%s,%s,1)',(installation_identity,authored_profile),prepare=False)
        cursor.execute('INSERT INTO truss.policy_publication_capacity VALUES(1,%s,%s,%s)',(installation_identity,authored_profile,max_retained),prepare=False)
        cursor.execute('SELECT singleton,installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard',prepare=False)
        if cursor.fetchall()!=[(1,installation_identity,authored_profile,1)]:
            raise ValueError('Exact original native guard seed required')
        cursor.execute('SELECT singleton,installation_identity_bytes,policy_profile_bytes,max_retained FROM truss.policy_publication_capacity',prepare=False)
        if cursor.fetchall()!=[(1,installation_identity,authored_profile,max_retained)]:
            raise ValueError('Exact original native capacity seed required')
        cursor.execute('SELECT 1 FROM truss.policy_publication_claim LIMIT 1',prepare=False)
        if cursor.fetchall():raise ValueError('Original empty publication registry required')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
        if cursor.fetchone()!=(original_path,):raise ValueError('Original search path restoration required')
        return PendingSecurityHomes(installation_identity,authored_profile,max_retained)
    return host._run_operation(transaction,install)
