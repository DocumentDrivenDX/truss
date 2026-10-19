# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private fresh-install privilege boundary; no facade or readiness authority.

The trusted installer must quiesce administrative changes. The caller owns its
transaction. Existing runtime profiles are not reinterpreted by this primitive.
"""
from dataclasses import dataclass
from psycopg import sql
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost

@dataclass(frozen=True, slots=True)
class InstallationRoles:
    owner: str
    client: str

@dataclass(frozen=True, slots=True)
class InstallationPrivilegeReport:
    namespace_oid: int
    owner_oid: int
    client_oid: int
    relations: int
    routines: int
    types: int


def _name(value):
    return (type(value) is str and bool(value) and '\0' not in value
            and not value.startswith('pg_') and len(value.encode('utf8')) <= 63)


def _rows(cursor, query, params=()):
    cursor.execute(query, params, prepare=False)
    rows = cursor.fetchmany(4097)
    if len(rows) > 4096:
        raise ValueError('Installation object limit exceeded')
    return rows


def _objects(cursor, namespace):
    relations = _rows(cursor, '''SELECT oid,relname,relkind,relowner,relacl
        FROM pg_catalog.pg_class WHERE relnamespace=%s ORDER BY oid''', (namespace,))
    routines = _rows(cursor, '''SELECT oid,proname,prokind,proowner,proacl,
        pg_catalog.pg_get_function_identity_arguments(oid)
        FROM pg_catalog.pg_proc WHERE pronamespace=%s ORDER BY oid''', (namespace,))
    types = _rows(cursor, '''SELECT oid,typname,typtype,typowner,typacl,typrelid,typelem
        FROM pg_catalog.pg_type WHERE typnamespace=%s ORDER BY oid''', (namespace,))
    if len(relations) + len(routines) + len(types) > 4096:
        raise ValueError('Installation object limit exceeded')
    return relations, routines, types


def _verify(cursor, namespace, owner, client, original):
    relations, routines, types = _objects(cursor, namespace)
    for before, after, owner_index in zip(original, (relations, routines, types), (3,3,3), strict=True):
        if [(r[0],r[1],r[2]) for r in before] != [(r[0],r[1],r[2]) for r in after]:
            raise ValueError('Installation object identities changed')
        if any(r[owner_index] != owner for r in after):
            raise ValueError('Installation ownership mismatch')
    for role in (owner, client):
        flags = _rows(cursor, '''SELECT rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,
            rolreplication,rolbypassrls,rolinherit FROM pg_catalog.pg_roles WHERE oid=%s''', (role,))
        if flags != [(False,False,False,False,False,False,False)]:
            raise ValueError('Installation role attributes changed')
    cursor.execute('''SELECT nspowner,pg_catalog.has_schema_privilege(%s,oid,'USAGE'),
        pg_catalog.has_schema_privilege(%s,oid,'CREATE'),pg_catalog.pg_has_role(%s,%s,'MEMBER')
        FROM pg_catalog.pg_namespace WHERE oid=%s''', (client,client,client,owner,namespace), prepare=False)
    if cursor.fetchone() != (owner,True,False,False):
        raise ValueError('Installation namespace or owner authority mismatch')
    for oid,name,kind,*_ in relations:
        if kind in ('i','I'):
            continue
        privileges = 'USAGE,SELECT,UPDATE' if kind == 'S' else 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN'
        fn = 'has_sequence_privilege' if kind == 'S' else 'has_table_privilege'
        cursor.execute(sql.SQL('SELECT pg_catalog.{}(%s,%s,%s)').format(sql.Identifier(fn)), (client,oid,privileges), prepare=False)
        if cursor.fetchone()[0]:
            raise ValueError('Client relation privilege leaked')
        if kind != 'S':
            cursor.execute('''SELECT pg_catalog.has_any_column_privilege(%s,%s,'SELECT,INSERT,UPDATE,REFERENCES')''', (client,oid), prepare=False)
            if cursor.fetchone()[0]:
                raise ValueError('Client column privilege leaked')
    for oid,*_ in routines:
        cursor.execute('SELECT pg_catalog.has_function_privilege(%s,%s,\'EXECUTE\')', (client,oid), prepare=False)
        if cursor.fetchone()[0]:
            raise ValueError('Client private routine privilege leaked')
    for oid,*_ in types:
        cursor.execute('SELECT pg_catalog.has_type_privilege(%s,%s,\'USAGE\')', (client,oid), prepare=False)
        if cursor.fetchone()[0]:
            raise ValueError('Client private type privilege leaked')
    cursor.execute("SELECT pg_catalog.has_schema_privilege(%s,%s,'USAGE WITH GRANT OPTION')", (client,namespace), prepare=False)
    if cursor.fetchone()[0]:
        raise ValueError('Client schema grant authority leaked')
    defaults = _rows(cursor, """SELECT d.defaclobjtype,d.defaclnamespace,
        a.grantee,a.privilege_type,a.is_grantable FROM pg_catalog.pg_default_acl d
        CROSS JOIN LATERAL pg_catalog.aclexplode(d.defaclacl) a
        WHERE d.defaclrole=%s""", (owner,))
    if set(defaults) != {('f',0,owner,'EXECUTE',False),('T',0,owner,'USAGE',False)}:
        raise ValueError('Exact private function and type defaults required')
    return InstallationPrivilegeReport(namespace,owner,client,len(relations),len(routines),len(types))


def protect_installation_in_transaction(host, transaction, roles):
    """Protect existing fresh objects using one host-owned operation savepoint.

    No role reuse, settlement, retry, actor adoption or installation publication.
    Run after installer-owned metadata checks and before runtime admission.
    Client credentials and facade grants are deliberately absent at this stage.
    """
    if type(host) is not PsycopgHost or type(roles) is not InstallationRoles:
        return Error(ExecutionFailure('execution_obligation','Installation host and roles required'))
    try:
        valid = _name(roles.owner) and _name(roles.client) and roles.owner != roles.client
    except UnicodeError:
        valid = False
    if not valid:
        return Error(ExecutionFailure('execution_obligation','Distinct PostgreSQL role names required'))

    def install(cursor, observed):
        return protect_installation_with_cursor(cursor, roles)

    return host._run_operation(transaction,install)


def installation_administrator_with_cursor(cursor, owner_oid=None):
    """Direct trusted session administrator; consumer admission is separate.

    Existing installation ownership uses current native INHERIT edges, not
    definer-context cached membership. The caller pins search_path first.
    """
    cursor.execute("""SELECT oid,rolname::text,rolsuper,rolcreaterole,current_user=session_user,
        pg_catalog.current_setting('role')='none' FROM pg_catalog.pg_roles WHERE rolname=session_user""",prepare=False)
    actor=cursor.fetchone()
    if actor is None or actor[4:]!=(True,True) or not (actor[2] or actor[3]):
        raise ValueError('Direct trusted role administrator required')
    if owner_oid is not None and not actor[2]:
        cursor.execute("""WITH RECURSIVE inherited(role_oid) AS (
            SELECT %s::oid UNION SELECT m.roleid FROM pg_catalog.pg_auth_members m
            JOIN inherited i ON m.member=i.role_oid WHERE m.inherit_option)
            SELECT EXISTS(SELECT 1 FROM inherited WHERE role_oid=%s::oid)""",(actor[0],owner_oid),prepare=False)
        if cursor.fetchone()!=(True,):raise ValueError('Current inherited installation owner authority required')
    return actor[:4]


def protect_installation_with_cursor(cursor, roles):
    """Installer-only cursor body; caller supplies the existing guarded savepoint."""
    cursor.execute("SELECT pg_catalog.current_setting('search_path')", prepare=False)
    original_search_path = cursor.fetchone()[0]
    cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)", prepare=False)
    actor=installation_administrator_with_cursor(cursor)
    cursor.execute("SELECT pg_catalog.current_setting('transaction_read_only')='off'",prepare=False)
    if cursor.fetchone()!=(True,):raise ValueError('Read-write installation transaction required')
    if not actor[2]:
        cursor.execute("SELECT pg_catalog.has_database_privilege(%s,pg_catalog.current_database(),'CREATE WITH GRANT OPTION')",(actor[0],),prepare=False)
        if cursor.fetchone()!=(True,):raise ValueError('Database CREATE WITH GRANT OPTION or ownership required')
    cursor.execute('SELECT oid,nspowner,nspacl FROM pg_catalog.pg_namespace WHERE nspname=\'truss\'', prepare=False)
    namespace = cursor.fetchone()
    if namespace is None or namespace[1] != actor[0]:
        raise ValueError('Installer-owned Truss namespace required')
    if _rows(cursor,'SELECT oid FROM pg_catalog.pg_roles WHERE rolname IN (%s,%s)', (roles.owner,roles.client)):
        raise ValueError('Fresh installation role identities required')
    objects = _objects(cursor, namespace[0])
    relations,routines,types = objects
    relation_ids = {r[0] for r in relations}
    type_ids = {r[0] for r in types}
    if any(r[2] not in ('r','p','S','i','I') or r[3] != actor[0] for r in relations):
        raise ValueError('Unsupported installation relation or owner')
    if any(r[2] not in ('f','p') or r[3] != actor[0] or len(r[5].encode()) > 16384 for r in routines):
        raise ValueError('Unsupported installation routine or owner')
    if any(r[3] != actor[0] or not (r[2] in ('d','e') or
            r[2]=='c' and r[5] in relation_ids or r[2]=='b' and r[6] in type_ids)
            for r in types):
        raise ValueError('Unsupported installation type or owner')
    for catalog, field in [('pg_collation','collnamespace'),('pg_conversion','connamespace'),
            ('pg_operator','oprnamespace'),('pg_opclass','opcnamespace'),('pg_opfamily','opfnamespace'),
            ('pg_ts_config','cfgnamespace'),('pg_ts_dict','dictnamespace'),
            ('pg_ts_parser','prsnamespace'),('pg_ts_template','tmplnamespace'),('pg_statistic_ext','stxnamespace')]:
        if _rows(cursor,sql.SQL('SELECT oid FROM pg_catalog.{} WHERE {}=%s').format(sql.Identifier(catalog),sql.Identifier(field)), (namespace[0],)):
            raise ValueError('Unsupported installation object class')
    addresses = [('pg_namespace',namespace[0])] + [(c,row[0]) for c,rows in
            [('pg_class',relations),('pg_proc',routines),('pg_type',types)] for row in rows]
    for catalog, oid in addresses:
        cursor.execute('''SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_depend
            WHERE classid=%s::regclass AND objid=%s AND deptype='e')''', ('pg_catalog.'+catalog,oid), prepare=False)
        if cursor.fetchone()[0]:
            raise ValueError('Extension-owned installation object refused')
    # Reject third-party grants rather than silently rewriting unrelated access.
    acls = [namespace[2]] + [row[4] for rows in objects for row in rows]
    for acl in acls:
        if acl is not None:
            cursor.execute('SELECT grantee FROM pg_catalog.aclexplode(%s::aclitem[])', (acl,), prepare=False)
            if any(row[0] not in (0,actor[0]) for row in cursor.fetchall()):
                raise ValueError('Third-party installation grant refused')
    columns = _rows(cursor,'''SELECT a.attrelid,a.attname,a.attacl FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
        WHERE c.relnamespace=%s AND c.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped
        ORDER BY a.attrelid,a.attnum''',(namespace[0],))
    for _,_,acl in columns:
        if acl is not None:
            cursor.execute('SELECT grantee FROM pg_catalog.aclexplode(%s::aclitem[])',(acl,),prepare=False)
            if any(row[0] not in (0,actor[0]) for row in cursor.fetchall()):
                raise ValueError('Third-party installation column grant refused')
    for name in (roles.owner,roles.client):
        cursor.execute(sql.SQL('CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS').format(sql.Identifier(name)), prepare=False)
    owner = _rows(cursor,'SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s',(roles.owner,))[0][0]
    client = _rows(cursor,'SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s',(roles.client,))[0][0]
    if not actor[2]:
        # PostgreSQL already gives the role creator ADMIN authority. Enable
        # only inherited ownership and SET for that trusted creator.
        # None of these memberships is granted to a consumer or permission role.
        for option in ('INHERIT','SET'):
            cursor.execute(sql.SQL('GRANT {} TO {} WITH {} TRUE').format(sql.Identifier(roles.owner),sql.Identifier(actor[1]),sql.SQL(option)),prepare=False)
        cursor.execute('SELECT pg_catalog.current_database()',prepare=False);database=cursor.fetchone()[0]
        cursor.execute(sql.SQL('GRANT CREATE ON DATABASE {} TO {}').format(sql.Identifier(database),sql.Identifier(roles.owner)),prepare=False)
    cursor.execute(sql.SQL('ALTER SCHEMA truss OWNER TO {}').format(sql.Identifier(roles.owner)),prepare=False)
    if not actor[2]:
        cursor.execute(sql.SQL('REVOKE CREATE ON DATABASE {} FROM {}').format(sql.Identifier(database),sql.Identifier(roles.owner)),prepare=False)

    cursor.execute('REVOKE ALL ON SCHEMA truss FROM PUBLIC',prepare=False)
    for relation_oid,name,kind,*rest in relations:
        if kind in ('i','I'):continue
        kind_sql = sql.SQL('SEQUENCE' if kind=='S' else 'TABLE')
        qualified = sql.Identifier('truss',name)
        cursor.execute(sql.SQL('ALTER {} {} OWNER TO {}').format(kind_sql,qualified,sql.Identifier(roles.owner)),prepare=False)
        cursor.execute(sql.SQL('REVOKE ALL ON {} {} FROM PUBLIC').format(kind_sql,qualified),prepare=False)
        names = [sql.Identifier(c[1]) for c in columns if c[0]==relation_oid]
        if names:
            cursor.execute(sql.SQL('REVOKE ALL ({}) ON TABLE {} FROM PUBLIC').format(sql.SQL(',').join(names),qualified),prepare=False)
    for _,name,kind,_,_,args in routines:
        signature = sql.SQL('{}({})').format(sql.Identifier('truss',name),sql.SQL(args))
        kind_sql = sql.SQL('PROCEDURE' if kind=='p' else 'FUNCTION')
        cursor.execute(sql.SQL('ALTER {} {} OWNER TO {}').format(kind_sql,signature,sql.Identifier(roles.owner)),prepare=False)
        cursor.execute(sql.SQL('REVOKE ALL ON {} {} FROM PUBLIC').format(kind_sql,signature),prepare=False)
    for _,name,kind,*_ in types:
        if kind=='b':continue
        kind_sql = sql.SQL('DOMAIN' if kind=='d' else 'TYPE')
        if kind in ('d','e'):
            cursor.execute(sql.SQL('ALTER {} {} OWNER TO {}').format(kind_sql,sql.Identifier('truss',name),sql.Identifier(roles.owner)),prepare=False)
        cursor.execute(sql.SQL('REVOKE ALL ON TYPE {} FROM PUBLIC').format(sql.Identifier('truss',name)),prepare=False)
    for kind in ('FUNCTIONS','TYPES'):
        cursor.execute(sql.SQL('ALTER DEFAULT PRIVILEGES FOR ROLE {} REVOKE ALL ON {} FROM PUBLIC').format(sql.Identifier(roles.owner),sql.SQL(kind)),prepare=False)
    cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(roles.client)),prepare=False)
    report = _verify(cursor,namespace[0],owner,client,objects)
    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)", (original_search_path,), prepare=False)
    if cursor.fetchone()[0] != original_search_path:
        raise ValueError('Caller search path restoration failed')
    return report
