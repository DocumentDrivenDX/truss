"""Private metadata-only cut consumer; complete source/authority bridge is required.

The security owner must admit original helper/DDL custody before invoking this
consumer and fresh source correspondence afterward. Native ACL enrollment here
is permission to acquire locks, not current policy or seal issuance authority.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from psycopg import sql
from .execution import Error,ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor
from ._security_catalog_assessment import SOURCE_TABLES
from ._security_catalog_subject_installation import _text_rows

_SOURCE_SHA256='4d10ae19b0c6771db3bef105bb99095497a437ee3e1d5d813e6bfe36aecab677'
_TABLES=('source_epoch_current','source_epoch_registry',*SOURCE_TABLES,'installation_archive')

def acquire_preparation_catalog_cut_with_cursor(cursor):
    raw=files('truss').joinpath('_security_bootstrap','preparation-catalog-cut.sql').read_bytes()
    if sha256(raw).hexdigest()!=_SOURCE_SHA256:raise ValueError('Original preparation catalog cut source required')
    body=raw.decode().split('AS $$',1)[1].split('$$;',1)[0]
    identity=_text_rows(cursor,"SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only'),pg_catalog.current_setting('role'),session_user::text,current_user::text",limit=1)
    if len(identity)!=1 or identity[0][:4]!=('180006','repeatable read','off','none') or identity[0][4]!=identity[0][5]:
        raise ValueError('Original ordinary RR preparation session required')
    original=_text_rows(cursor,"""SELECT p.oid::text,p.proowner::text,n.nspowner::text,p.prosrc,
        p.prosecdef::text,p.provolatile::text,p.proparallel::text,p.prorettype::text,
        p.proargtypes::text,p.proretset::text,pg_catalog.to_jsonb(p.proconfig)::text,
        l.lanname::text,p.prokind::text,p.proisstrict::text,p.proleakproof::text,p.prosupport::oid::text,
        r.rolcanlogin::text,r.rolsuper::text,r.rolcreaterole::text,r.rolcreatedb::text,r.rolreplication::text,r.rolbypassrls::text
        FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
        JOIN pg_catalog.pg_language l ON l.oid=p.prolang JOIN pg_catalog.pg_roles r ON r.oid=p.proowner
        WHERE n.nspname='truss' AND p.proname='acquire_preparation_catalog_cut' AND p.pronargs=0""",limit=1)
    if (len(original)!=1 or original[0][1]!=original[0][2]
        or original[0][3:]!=(body,'true','v','u','2278','','false','["search_path=pg_catalog, pg_temp"]',
            'plpgsql','f','false','false','0','false','false','false','false','false','false')):
        raise ValueError('Exact original private preparation cut issuer required')
    actor=_text_rows(cursor,"SELECT oid::text FROM pg_catalog.pg_roles WHERE rolname=session_user",limit=1)
    if len(actor)!=1:raise ValueError('Original native preparation executor required')
    grants=_text_rows(cursor,"""SELECT a.grantee::text,a.grantor::text,a.privilege_type::text,a.is_grantable::text
        FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
        WHERE p.oid=%s::oid ORDER BY a.grantee,a.grantor,a.privilege_type,a.is_grantable""",(original[0][0],),2)
    expected=sorted([(original[0][1],original[0][1],'EXECUTE','false'),(actor[0][0],original[0][1],'EXECUTE','false')],key=lambda r:int(r[0]))
    if grants!=expected:raise ValueError('Exact enrolled preparation executor ACL required')
    cursor.execute('SELECT truss.acquire_preparation_catalog_cut()',prepare=False,binary=False)
    if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=2278 or cursor.fetchmany(2)!=[('',)]:
        raise ValueError('Original preparation cut native completion required')
    held=_text_rows(cursor,"""SELECT c.relname::text,c.relowner::text,c.relkind::text,c.relpersistence::text,
        c.relrowsecurity::text,c.relforcerowsecurity::text,
        EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid=c.oid OR i.inhparent=c.oid)::text,
        EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.locktype='relation' AND l.pid=pg_catalog.pg_backend_pid()
            AND l.database=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())
            AND l.relation=c.oid AND l.mode='ShareLock' AND l.granted)::text
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='truss' AND c.relname=ANY(%s::text[]) ORDER BY c.relname""",(list(_TABLES),),len(_TABLES))
    if held!=[(n,original[0][1],'r','p','false','false','false','true') for n in sorted(_TABLES)]:
        raise ValueError('Complete original metadata-only preparation cut required')
    return None


@dataclass(frozen=True, slots=True)
class PendingPreparationCatalogCutIssuer:
    installation_id: str
    owner_oid: int
    executor_oid: int
    source_sha256: str
    status: str = 'pending_commit'
    security_ready: bool = False


def bootstrap_preparation_catalog_cut_in_transaction(host,transaction,*,executor_role):
    """Explicit adjunct installation; caller owns commit and administrative quiescence.

    This installs no coordinator, cut token, seal table or public bulk capability.
    Existing issuers require an explicit migration, never silent replacement.
    """
    if (type(host) is not PsycopgHost or type(executor_role) is not str or not executor_role
            or '\0' in executor_role or len(executor_role.encode())>63):
        return Error(ExecutionFailure('execution_obligation','Original bounded preparation executor required'))
    raw=files('truss').joinpath('_security_bootstrap','preparation-catalog-cut.sql').read_bytes()
    if sha256(raw).hexdigest()!=_SOURCE_SHA256:
        return Error(ExecutionFailure('execution_obligation','Original preparation cut source required'))
    def install(cursor,observed):
        _pin_cursor(cursor)
        prior=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::text",limit=1)
        if len(prior)!=1:raise ValueError('Original preparation installer path required')
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        from ._current_query_protection import require_unprotected_configuration
        require_unprotected_configuration(cursor,allow_uninstalled=True)
        state=_text_rows(cursor,"SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only')",limit=1)
        if state!=[('180006','read committed','off')]:raise ValueError('Original preparation cut installation transaction required')
        installed=_text_rows(cursor,'SELECT installation_id::text,owner_oid::text FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT',limit=1)
        if len(installed)!=1:raise ValueError('Original catalog installation required')
        owner_oid=int(installed[0][1]);installation_administrator_with_cursor(cursor,owner_oid)
        owner=_text_rows(cursor,"SELECT rolname::text,rolcanlogin::text,rolsuper::text,rolcreaterole::text,rolcreatedb::text,rolreplication::text,rolbypassrls::text FROM pg_catalog.pg_roles WHERE oid=%s::oid",(owner_oid,),1)
        if len(owner)!=1 or owner[0][1:]!=('false',)*6:raise ValueError('Original nonprivileged NOLOGIN catalog owner required')
        executor=_text_rows(cursor,"SELECT oid::text,rolcanlogin::text,rolsuper::text,rolcreaterole::text,rolcreatedb::text,rolreplication::text,rolbypassrls::text,pg_catalog.pg_has_role(oid,%s::oid,'MEMBER')::text FROM pg_catalog.pg_roles WHERE rolname=%s",(owner_oid,executor_role),1)
        if len(executor)!=1 or executor[0][1:]!=('true','false','false','false','false','false','false'):
            raise ValueError('Original ordinary enrolled preparation executor required')
        if _text_rows(cursor,"SELECT oid::text FROM pg_catalog.pg_proc WHERE pronamespace='truss'::regnamespace AND proname='acquire_preparation_catalog_cut'",limit=1):
            raise ValueError('Existing preparation cut issuer requires explicit migration')
        cursor.execute(raw.decode(),prepare=False)
        cursor.execute(sql.SQL('ALTER FUNCTION truss.acquire_preparation_catalog_cut() OWNER TO {}').format(sql.Identifier(owner[0][0])),prepare=False)
        cursor.execute('REVOKE ALL ON FUNCTION truss.acquire_preparation_catalog_cut() FROM PUBLIC',prepare=False)
        cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.acquire_preparation_catalog_cut() TO {}').format(sql.Identifier(executor_role)),prepare=False)
        cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(executor_role)),prepare=False)
        acl=_text_rows(cursor,"SELECT a.grantee::text,a.grantor::text,a.privilege_type::text,a.is_grantable::text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid='truss.acquire_preparation_catalog_cut()'::regprocedure ORDER BY a.grantee,a.grantor,a.privilege_type,a.is_grantable",limit=2)
        expected=sorted([(str(owner_oid),str(owner_oid),'EXECUTE','false'),(executor[0][0],str(owner_oid),'EXECUTE','false')],key=lambda r:int(r[0]))
        if acl!=expected:raise ValueError('Exact private preparation cut enrollment required')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
        if cursor.fetchone()!=(prior[0][0],):raise ValueError('Original preparation installer path restoration required')
        return PendingPreparationCatalogCutIssuer(installed[0][0],owner_oid,int(executor[0][0]),_SOURCE_SHA256)
    return host._run_operation(transaction,install)
