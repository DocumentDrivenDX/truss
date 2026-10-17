"""Installation-wide lockdown for the initial protected read-only query profile.

The host quiesces ordinary sessions and new connections until activation commits.
Legacy data interfaces stay unavailable until they have equivalent policy checks.
"""
import json
import re
from psycopg import sql
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from ._installation_privileges import installation_administrator_with_cursor
from ._current_query_sources import capture_current_query_sources_with_cursor
from ._current_query_subjects import _verify_helper
from ._current_disclosure_originals import is_graph_disclosure_originals
from .catalog_runtime import _pin_cursor
from .current_query import CurrentQueryProtection

_MARKER='truss.current_query_protection_marker()'
_GRAPH_PROFILE='truss-current-graph-protection/0.1-candidate'
_SCALAR_PROFILE='truss-current-query-protection/0.1-candidate'


class GraphAuthorityProfileRequired(ValueError):
    pass

_METADATA=('truss.reader_catalog(integer,integer,text,text)',
           'truss.accepted_document(text,integer,text,text)')
_SUBJECT='truss.current_query_subject_current()'


_HOMES="""WITH RECURSIVE homes(oid) AS (
    SELECT c.oid FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'
    UNION SELECT CASE WHEN i.inhparent=h.oid THEN i.inhrelid ELSE i.inhparent END
    FROM pg_catalog.pg_inherits i JOIN homes h ON i.inhparent=h.oid OR i.inhrelid=h.oid)
"""

def require_unprotected_configuration(cursor,*,allow_uninstalled=False):
    """Serialize every supported regrant path with protection activation."""
    cursor.execute('SELECT pg_catalog.to_regprocedure(%s)',(_MARKER,),prepare=False)
    if cursor.fetchone()!=(None,):
        raise ValueError('Protected query installation requires an explicit protection migration')
    if allow_uninstalled:
        cursor.execute("SELECT pg_catalog.to_regclass('truss.catalog_runtime_installation')",prepare=False)
        if cursor.fetchone()==(None,):return
    cursor.execute('LOCK TABLE ONLY truss.catalog_runtime_installation IN SHARE ROW EXCLUSIVE MODE NOWAIT',prepare=False)
    cursor.execute('SELECT pg_catalog.to_regprocedure(%s)',(_MARKER,),prepare=False)
    if cursor.fetchone()!=(None,):
        raise ValueError('Protected query installation requires an explicit protection migration')


def _profile_body(sources,administrator,profile):
    return 'SELECT '+sql.Literal(json.dumps({'profile':profile,
        'installation':sources.installation_id,'inventory':sources.inventory_digest,'trustedAdministratorOid':administrator},sort_keys=True,separators=(',',':'))).as_string()+'::pg_catalog.text'


def _body(sources,administrator):
    profile=_GRAPH_PROFILE if is_graph_disclosure_originals(sources.query_originals) else _SCALAR_PROFILE
    return _profile_body(sources,administrator,profile)


def _marker_administrator(body,sources):
    if type(body) is not str:raise ValueError('Exact activation marker source required')
    match=re.fullmatch(r"SELECT '([^']+)'::pg_catalog.text",body)
    if match is None:raise ValueError('Exact activation marker source required')
    administrator=json.loads(match[1]).get('trustedAdministratorOid')
    if (type(administrator) is int and 0<administrator<2**32
            and is_graph_disclosure_originals(sources.query_originals)
            and body==_profile_body(sources,administrator,_SCALAR_PROFILE)):
        raise GraphAuthorityProfileRequired('Explicit quiesced Graph protection activation required')
    if type(administrator) is not int or not 0<administrator<2**32 or body!=_body(sources,administrator):
        raise ValueError('Original activating administrator identity required')
    return administrator


def _owner(cursor):
    cursor.execute('''SELECT i.owner_oid,r.rolname::text FROM ONLY truss.catalog_runtime_installation i
        JOIN pg_catalog.pg_roles r ON r.oid=i.owner_oid JOIN pg_catalog.pg_namespace n ON n.nspname='truss' AND n.nspowner=r.oid
        WHERE i.singleton AND NOT r.rolcanlogin AND NOT r.rolsuper AND NOT r.rolcreaterole
        AND NOT r.rolcreatedb AND NOT r.rolreplication AND NOT r.rolbypassrls AND NOT r.rolinherit''',prepare=False)
    rows=cursor.fetchmany(2)
    if len(rows)!=1:raise ValueError('Unprivileged original runtime owner required')
    return rows[0]


def _private_homes(cursor,owner):
    cursor.execute(_HOMES+'''SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_class c JOIN homes h ON h.oid=c.oid
        WHERE (c.relowner<>%s OR EXISTS(
        SELECT 1 FROM pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault(CASE WHEN c.relkind='S' THEN 's'::"char" ELSE 'r'::"char" END,c.relowner))) a
        WHERE a.grantee<>c.relowner OR a.grantor<>c.relowner OR a.is_grantable)
        OR EXISTS(SELECT 1 FROM pg_catalog.pg_attribute a WHERE a.attrelid=c.oid AND a.attacl IS NOT NULL)))''',(owner,),prepare=False)
    if cursor.fetchone()!=(False,):raise ValueError('Owner-only complete runtime relations and columns required')


def _routine_attachments(cursor):
    # EXECUTE revocation does not detach existing triggers/operators/casts.
    # Only relation-owned attachments on the private native homes are admitted;
    # this profile has no expected inter-routine catalog dependency exception.
    cursor.execute(_HOMES+'''SELECT EXISTS(
        SELECT 1 FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_proc p ON p.oid=t.tgfoid
        JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss'
            AND NOT EXISTS(SELECT 1 FROM homes h WHERE h.oid=t.tgrelid))
        OR EXISTS(SELECT 1 FROM pg_catalog.pg_depend d JOIN pg_catalog.pg_proc p ON p.oid=d.refobjid
            AND d.refclassid='pg_catalog.pg_proc'::pg_catalog.regclass
            JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND NOT (
                (d.classid='pg_catalog.pg_trigger'::pg_catalog.regclass AND EXISTS(
                    SELECT 1 FROM pg_catalog.pg_trigger t JOIN homes h ON h.oid=t.tgrelid WHERE t.oid=d.objid))
                OR (d.classid='pg_catalog.pg_attrdef'::pg_catalog.regclass AND EXISTS(
                    SELECT 1 FROM pg_catalog.pg_attrdef a JOIN homes h ON h.oid=a.adrelid WHERE a.oid=d.objid))
                OR (d.classid='pg_catalog.pg_constraint'::pg_catalog.regclass AND EXISTS(
                    SELECT 1 FROM pg_catalog.pg_constraint c JOIN homes h ON h.oid=c.conrelid WHERE c.oid=d.objid))
                OR (d.classid='pg_catalog.pg_rewrite'::pg_catalog.regclass AND EXISTS(
                    SELECT 1 FROM pg_catalog.pg_rewrite r JOIN homes h ON h.oid=r.ev_class WHERE r.oid=d.objid))))''',prepare=False)
    if cursor.fetchone()!=(False,):raise ValueError('External routine attachments require an explicit protection migration')


def _allowed_oids(cursor,owner):
    allowed=[]
    for signature in (*_METADATA,_SUBJECT):
        cursor.execute('SELECT oid,proowner FROM pg_catalog.pg_proc WHERE oid=pg_catalog.to_regprocedure(%s)',(signature,),prepare=False)
        row=cursor.fetchone()
        if row is None or row[1]!=owner:raise ValueError('Complete exact protected metadata/Subject signatures required')
        allowed.append(row[0])
    if len(set(allowed))!=3:raise ValueError('Distinct protected facade signatures required')
    return allowed


def _ordinary_roles(cursor,registration,administrator):
    # Include unenrolled outsiders: an external delegated read must not expose
    # protected data merely because its recipient has no Subject enrollment.
    cursor.execute('''SELECT oid FROM pg_catalog.pg_roles WHERE rolcanlogin AND oid<>%s::oid
        AND pg_catalog.has_database_privilege(oid,pg_catalog.current_database(),'CONNECT') ORDER BY oid''',(administrator,),prepare=False)
    roles=cursor.fetchmany(4097)
    if len(roles)>4096 or not {oid for oid,_ in registration.bindings}<=set(r[0] for r in roles):
        raise ValueError('Bounded complete ordinary protected LOGIN inventory required')
    for (role,) in roles:
        cursor.execute('''SELECT NOT EXISTS(SELECT 1 FROM pg_catalog.pg_roles forbidden WHERE
            (forbidden.oid=(SELECT owner_oid FROM truss.catalog_runtime_installation WHERE singleton)
             OR forbidden.rolname IN ('pg_read_server_files','pg_write_server_files','pg_execute_server_program'))
            AND pg_catalog.pg_has_role(%s::oid,forbidden.oid,'MEMBER'))''',(role,),prepare=False)
        if cursor.fetchone()!=(True,):raise ValueError('Ordinary protected LOGIN cannot inherit administrative authority')
        # A definer may also run through a pre-existing trigger without EXECUTE
        # permission at firing time. This first profile therefore admits no
        # external privileged definer, even when its own ACL appears private.
        cursor.execute(_HOMES+''', authority(active_oid,privilege_oid) AS (
            SELECT %s::oid,%s::oid UNION
            SELECT p.proowner,p.proowner FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
                WHERE p.prosecdef AND n.nspname<>'truss'
            UNION SELECT CASE WHEN m.admin_option OR (m.set_option AND s.active_oid=s.privilege_oid)
                THEN m.roleid ELSE s.active_oid END,m.roleid
                FROM authority s JOIN pg_catalog.pg_auth_members m ON m.member=s.privilege_oid
                WHERE m.inherit_option OR m.admin_option OR (m.set_option AND s.active_oid=s.privilege_oid)),
            exposed_views(oid) AS (
                SELECT oid FROM homes UNION
                SELECT r.ev_class FROM exposed_views v JOIN pg_catalog.pg_depend d ON d.refobjid=v.oid
                    AND d.refclassid='pg_catalog.pg_class'::pg_catalog.regclass
                    AND d.classid='pg_catalog.pg_rewrite'::pg_catalog.regclass
                JOIN pg_catalog.pg_rewrite r ON r.oid=d.objid)
            SELECT EXISTS(SELECT 1 FROM (SELECT DISTINCT active_oid FROM authority) s JOIN pg_catalog.pg_roles r ON r.oid=s.active_oid
                WHERE r.rolsuper OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication OR r.rolbypassrls
                OR pg_catalog.has_schema_privilege(r.oid,'truss','CREATE')
                OR EXISTS(SELECT 1 FROM pg_catalog.pg_class c JOIN homes h ON h.oid=c.oid
                    WHERE (c.relkind IN ('r','p','v','m','f') AND (pg_catalog.has_table_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
                        OR pg_catalog.has_any_column_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')))
                        OR (c.relkind='S' AND pg_catalog.has_sequence_privilege(r.oid,c.oid,'USAGE,SELECT,UPDATE')))
                OR EXISTS(SELECT 1 FROM exposed_views v JOIN pg_catalog.pg_class c ON c.oid=v.oid
                    JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname<>'truss' AND c.relkind IN ('r','p','v','m','f')
                    AND (pg_catalog.has_table_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE,DELETE')
                        OR pg_catalog.has_any_column_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE'))))''',(role,role),prepare=False)
        if cursor.fetchone()!=(False,):raise ValueError('Ordinary protected roles cannot reach raw or externally delegated runtime authority')


def verify_current_query_protection(cursor,sources,registration):
    owner,_=_owner(cursor)
    if registration.owner_oid!=owner:raise ValueError('Same protected Subject/runtime owner required')
    _verify_helper(cursor,registration)
    cursor.execute('''SELECT p.prosrc,p.proowner,p.prosecdef,p.provolatile,p.proretset,p.prorettype::int,p.pronargs,l.lanname::text,p.proconfig
        FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE p.oid=pg_catalog.to_regprocedure(%s)''',(_MARKER,),prepare=False)
    marker=cursor.fetchone()
    if marker is None:raise ValueError('Committed original protected-query activation required')
    administrator=_marker_administrator(marker[0],sources)
    if marker!=(_body(sources,administrator),owner,False,'v',False,25,0,'sql',['search_path=pg_catalog, pg_temp']):
        raise ValueError('Committed original protected-query activation required')
    allowed=_allowed_oids(cursor,owner)
    cursor.execute('''SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
        WHERE n.nspname='truss' AND (p.proowner<>%s OR EXISTS(
        SELECT 1 FROM pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
        WHERE a.grantor<>p.proowner OR a.is_grantable OR (a.grantee<>p.proowner
        AND (p.oid<>ALL(%s::oid[]) OR a.grantee=0)))))''',(owner,allowed),prepare=False)
    if cursor.fetchone()!=(False,):raise ValueError('Protected query requires closed ordinary routine grants')
    _private_homes(cursor,owner)
    _routine_attachments(cursor)
    _ordinary_roles(cursor,registration,administrator)


def activate_current_query_protection_in_transaction(host,transaction,*,subject_registration):
    """Quiesced trusted bootstrap; commit before opening protected callers.

    No commit, disconnection, implicit upgrade or regrant is performed here.
    """
    from .current_query import CurrentQuerySubjectRegistration
    if type(host) is not PsycopgHost or type(subject_registration) is not CurrentQuerySubjectRegistration:
        return Error(ExecutionFailure('execution_obligation','Original protection host and Subject registration required'))
    def activate(cursor,observed):
        _pin_cursor(cursor)
        cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False)
        prior=cursor.fetchone()[0]
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        installation_administrator_with_cursor(cursor)
        require_unprotected_configuration(cursor)
        cursor.execute('''SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_stat_activity WHERE datid=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())
            AND pid<>pg_catalog.pg_backend_pid() AND backend_type='client backend')''',prepare=False)
        if cursor.fetchone()!=(False,):raise ValueError('Quiesce all ordinary sessions and new connections before activation')
        cursor.execute('LOCK TABLE pg_catalog.pg_authid,pg_catalog.pg_auth_members IN SHARE MODE NOWAIT',prepare=False)
        sources=capture_current_query_sources_with_cursor(cursor)
        if sources.query_originals is None:raise ValueError('Complete protected query originals required')
        owner,owner_name=_owner(cursor)
        installation_administrator_with_cursor(cursor,owner)
        _verify_helper(cursor,subject_registration)
        if (subject_registration.owner_oid,subject_registration.installation_id,subject_registration.source_receipt)!=(owner,sources.installation_id,sources.source_receipt):
            raise ValueError('Original protected Subject/source correspondence required')
        _private_homes(cursor,owner)
        allowed=_allowed_oids(cursor,owner)
        cursor.execute('SELECT oid FROM pg_catalog.pg_roles WHERE rolname=SESSION_USER',prepare=False)
        administrator=cursor.fetchone()[0]
        cursor.execute(sql.SQL('CREATE FUNCTION truss.current_query_protection_marker() RETURNS text LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS {}').format(sql.Literal(_body(sources,administrator))),prepare=False)
        cursor.execute(sql.SQL('ALTER FUNCTION truss.current_query_protection_marker() OWNER TO {}').format(sql.Identifier(owner_name)),prepare=False)
        cursor.execute('REVOKE ALL ON FUNCTION truss.current_query_protection_marker() FROM PUBLIC',prepare=False)
        cursor.execute('''SELECT p.proname::text,pg_catalog.pg_get_function_identity_arguments(p.oid),a.grantee,r.rolname::text
            FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
            CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
            LEFT JOIN pg_catalog.pg_roles r ON r.oid=a.grantee WHERE n.nspname='truss' AND a.grantee<>p.proowner
            AND p.oid<>ALL(%s::oid[])
            ORDER BY p.oid,a.grantee''',(allowed,),prepare=False)
        grants=cursor.fetchmany(4097)
        if len(grants)>4096:raise ValueError('Bounded runtime grant inventory required')
        for name,args,grantee,role in grants:
            recipient=sql.SQL('PUBLIC') if grantee==0 else sql.Identifier(role)
            cursor.execute(sql.SQL('REVOKE ALL PRIVILEGES ON ROUTINE truss.{}({}) FROM {} CASCADE').format(sql.Identifier(name),sql.SQL(args),recipient),prepare=False)
        verify_current_query_protection(cursor,sources,subject_registration)
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior,),prepare=False)
        if cursor.fetchone()!=(prior,):raise ValueError('Protection installation search path restoration required')
        return CurrentQueryProtection(sources.installation_id,sources.inventory_digest,administrator)
    return host._run_operation(transaction,activate)
