# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private fresh-install privilege boundary; no facade or readiness authority.

The trusted installer must quiesce administrative changes. The caller owns its
transaction. Existing runtime profiles are not reinterpreted by this primitive.
"""
from dataclasses import dataclass
import json
from psycopg import sql
from .execution import Error, ExecutionFailure, _UnsupportedProfileIncompatibility
from .psycopg_host import PsycopgHost

@dataclass(frozen=True, slots=True)
class InstallationRoles:
    owner: str
    client: str
    tolerated_grantees: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class InstallationPrivilegeReport:
    namespace_oid: int
    owner_oid: int
    client_oid: int
    relations: int
    routines: int
    types: int
    managed_grants: dict
    original_objects: tuple = ()


_GRANT_POLICY_VERSION = 'truss-managed-grants/0.1'
_MAX_TOLERATED_GRANTEES = 32
_MAX_GRANT_OBSERVATIONS = 16384
_MAX_GRANT_EVIDENCE_BYTES = 4 * 1024 * 1024
_GRANT_OBJECT_CLASSES = frozenset({'schema', 'relation', 'sequence', 'routine', 'type', 'column'})
_GRANT_PHASES = frozenset({'pre_ownership', 'post_installation'})
_GRANT_PRIVILEGES = {
    'schema': frozenset({'USAGE','CREATE'}),
    'relation': frozenset({'SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'}),
    'sequence': frozenset({'USAGE','SELECT','UPDATE'}),
    'routine': frozenset({'EXECUTE'}), 'type': frozenset({'USAGE'}),
    'column': frozenset({'SELECT','INSERT','UPDATE','REFERENCES'}),
}


def _name(value):
    return (type(value) is str and bool(value) and '\0' not in value
            and not value.startswith('pg_') and len(value.encode('utf8')) <= 63)


def _policy_names(names, *, reserved=()):
    """Validate the bounded exact-name policy before issuing any database SQL."""
    if type(names) is not tuple or len(names) > _MAX_TOLERATED_GRANTEES:
        raise ValueError('At most 32 exact tolerated grantee names are allowed')
    blocked = set(reserved)
    result = []
    for name in names:
        try:
            valid = _name(name)
            size = len(name.encode('utf8')) if type(name) is str else 0
        except UnicodeError:
            valid = False
            size = 0
        if not valid:
            raise ValueError('Literal PostgreSQL role name required')
        if size == 0 or name == 'PUBLIC' or name in blocked:
            raise ValueError('Reserved tolerated grantee name')
        result.append(name)
    if len(set(result)) != len(result):
        raise ValueError('Duplicate tolerated grantee name')
    return tuple(sorted(result, key=lambda name: name.encode('utf8')))


def _canonical_evidence(policy, observations):
    """Serialize only bounded native identities and ACL facts, never authority."""
    rows = sorted(observations, key=lambda row: json.dumps(
        row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf8'))
    if len(rows) > _MAX_GRANT_OBSERVATIONS:
        raise ValueError('Managed grant observation limit exceeded')
    value = {
        'interfaceVersion': _GRANT_POLICY_VERSION,
        'roles': [{'name': name, 'oid': oid} for name, oid in policy],
        'observations': rows,
    }
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    if len(encoded.encode('utf8')) > _MAX_GRANT_EVIDENCE_BYTES:
        raise ValueError('Managed grant evidence limit exceeded')
    return value


def _resolved_tolerated_roles(cursor, names, *, owner, client, installer):
    names = _policy_names(names, reserved=(owner, client, installer))
    if not names:
        return ()
    rows = _rows(cursor, '''SELECT oid,rolname::text FROM pg_catalog.pg_roles
        WHERE rolname=ANY(%s) ORDER BY rolname''', (list(names),))
    resolved = {name: oid for oid, name in rows}
    if len(resolved) != len(names) or set(resolved) != set(names):
        raise ValueError('Every tolerated grantee must resolve to one current role')
    if len(set(resolved.values())) != len(resolved):
        raise ValueError('Tolerated grantee role identities must be distinct')
    return tuple((name, resolved[name]) for name in names)


def _role_name(cursor, oid):
    if oid == 0:
        return 'PUBLIC'
    rows = _rows(cursor, 'SELECT rolname::text FROM pg_catalog.pg_roles WHERE oid=%s', (oid,))
    if len(rows) != 1:
        raise ValueError('Native grant role identity is unavailable')
    return rows[0][0]


def _acl_observations(cursor, namespace, *, phase, installer_oid, tolerated_oids, admitted_oids=()):
    """Classify a set-oriented ACL census and retain only selected-role evidence."""
    cursor.execute('''WITH objects AS (
        SELECT 'schema'::text AS kind,n.oid,n.nspname::text AS name,NULL::text AS detail,
            n.nspowner AS owner,n.nspacl AS acl,'n'::"char" AS acl_kind
        FROM pg_catalog.pg_namespace n WHERE n.oid=%s
        UNION ALL SELECT CASE WHEN c.relkind='S' THEN 'sequence' ELSE 'relation' END,
            c.oid,c.relname::text,NULL::text,c.relowner,c.relacl,
            CASE WHEN c.relkind='S' THEN 's' ELSE 'r' END::"char"
        FROM pg_catalog.pg_class c WHERE c.relnamespace=%s AND c.relkind NOT IN ('i','I')
        UNION ALL SELECT 'routine',p.oid,p.proname::text,
            pg_catalog.pg_get_function_identity_arguments(p.oid),p.proowner,p.proacl,'f'::"char"
        FROM pg_catalog.pg_proc p WHERE p.pronamespace=%s
        UNION ALL SELECT 'type',t.oid,t.typname::text,NULL::text,t.typowner,t.typacl,'T'::"char"
        FROM pg_catalog.pg_type t WHERE t.typnamespace=%s), grants AS (
        SELECT o.kind,o.oid,o.name,o.detail,NULL::smallint AS attnum,NULL::text AS attname,
            a.grantor,a.grantee,a.privilege_type,a.is_grantable
        FROM objects o CROSS JOIN LATERAL pg_catalog.aclexplode(
            coalesce(o.acl,pg_catalog.acldefault(o.acl_kind,o.owner))) a
        UNION ALL SELECT 'column',a.attrelid,c.relname::text,NULL::text,a.attnum,a.attname::text,
            x.grantor,x.grantee,x.privilege_type,x.is_grantable
        FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
        CROSS JOIN LATERAL pg_catalog.aclexplode(a.attacl) x
        WHERE c.relnamespace=%s AND c.relkind IN ('r','p')
          AND a.attnum>0 AND NOT a.attisdropped AND a.attacl IS NOT NULL)
        SELECT g.kind,g.oid,g.name,g.detail,g.attnum,g.attname,g.grantor,g.grantee,
            g.privilege_type,g.is_grantable,
            CASE WHEN g.grantee=0 THEN 'PUBLIC' ELSE gr.rolname::text END,
            CASE WHEN g.grantor=0 THEN 'PUBLIC' ELSE go.rolname::text END
        FROM grants g LEFT JOIN pg_catalog.pg_roles gr ON gr.oid=g.grantee
        LEFT JOIN pg_catalog.pg_roles go ON go.oid=g.grantor
        ORDER BY g.kind,g.oid,g.attnum,g.grantee,g.grantor,g.privilege_type,g.is_grantable''',
        (namespace, namespace, namespace, namespace, namespace), prepare=False)
    observations = []
    while True:
        batch = cursor.fetchmany(1024)
        if not batch:
            break
        for (object_class, oid, name, detail, attnum, attname,
             grantor, grantee, privilege, grantable, grantee_name, grantor_name) in batch:
            if grantee not in (0, installer_oid, *tolerated_oids, *admitted_oids):
                if grantee_name is None:
                    raise ValueError('Native grant role identity is unavailable')
                raise _ThirdPartyGrantRefusal(grantee_name, object_class, phase)
            if grantee not in tolerated_oids:
                continue
            if grantor_name is None:
                raise ValueError('Native grant role identity is unavailable')
            observations.append({
                'class': object_class, 'objectOid': oid, 'name': name,
                'detail': detail,
                'column': None if attnum is None else {'number': attnum, 'name': attname},
                'granteeOid': grantee, 'grantorOid': grantor,
                'privilege': privilege, 'grantOption': grantable,
                'phase': phase, 'grantee': grantee_name, 'grantor': grantor_name,
            })
            if len(observations) > _MAX_GRANT_OBSERVATIONS:
                raise ValueError('Managed grant observation limit exceeded')
    return observations


def _require_allowed_grantees(observations, *, installer_oid, tolerated_oids):
    for observation in observations:
        grantee = observation['granteeOid']
        if grantee not in (0, installer_oid, *tolerated_oids):
            raise _ThirdPartyGrantRefusal(
                observation['grantee'], observation['class'], observation['phase'])


def _tolerated_privileges(observations, identities):
    selected = set(identities)
    return {
        (row['class'], row['objectOid'], row['detail'],
         None if row['column'] is None else (row['column']['number'], row['column']['name']),
         row['granteeOid'], row['privilege'], row['grantOption'])
        for row in observations if row['granteeOid'] in selected
    }


def finalize_installation_grants(cursor, report, roles, resolved_tolerated, installer_oid):
    """Take the final ACL census after every install-generated GRANT/COMMENT."""
    cursor.execute('SELECT rolname::text FROM pg_catalog.pg_roles WHERE oid=%s',(installer_oid,),prepare=False)
    installer_row=cursor.fetchone()
    if installer_row is None:
        raise ValueError('Installer role identity changed during installation')
    current_tolerated=_resolved_tolerated_roles(cursor, roles.tolerated_grantees,
        owner=roles.owner,client=roles.client,installer=installer_row[0])
    if current_tolerated != resolved_tolerated:
        raise ValueError('Tolerated role identity changed during installation')
    tolerated_oids = tuple(oid for _, oid in resolved_tolerated)
    policy = report.managed_grants
    before = [row for row in policy['observations'] if row['phase'] == 'pre_ownership']
    after = _acl_observations(cursor, report.namespace_oid, phase='post_installation',
        installer_oid=installer_oid, tolerated_oids=tolerated_oids,
        admitted_oids=(report.owner_oid, report.client_oid))
    for oid in tolerated_oids:
        cursor.execute("SELECT pg_catalog.pg_has_role(%s,%s,'MEMBER')",
            (report.client_oid,oid),prepare=False)
        if cursor.fetchone() == (True,):
            raise ValueError('Installation client can assume a tolerated raw-access role')
    from ._runtime_admission import person_entrypoints
    public_signatures = [entry['publicName']+'('+entry['signature'].split('(',1)[1]
        for entry in person_entrypoints()]
    client_signatures = ('catalog_accept(bytea,bytea,bytea,bytea,bytea,text)',
        'catalog_accept_preview(bytea,bytea,bytea,bytea,bytea,text)',
        'catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean)',
        'catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean,int,bytea)',
        'catalog_report(int)','catalog_status()','catalog_view_basis(int,int,int)',
        'reader_catalog_if_changed(int,int,text,text,text)','registrar_status(text,text)',
        'person_runtime_status(text,text,jsonb)','admin_install_recovery()',
        'grant_import_audit_access(text,text,text)')
    signatures = [*public_signatures, *client_signatures]
    allowed=[]
    public_oids=[]
    client_oids=[]
    for signature in signatures:
        cursor.execute('SELECT pg_catalog.to_regprocedure(%s)::oid',('truss.'+signature,),prepare=False)
        row=cursor.fetchone()
        if row is not None and row[0] is not None:
            allowed.append(row[0])
            if signature in public_signatures:
                public_oids.append(row[0])
            elif signature in client_signatures:
                client_oids.append(row[0])
    _verify(cursor,report.namespace_oid,report.owner_oid,report.client_oid,report.original_objects,
        allowed_routines=allowed)
    _verify_final_acl_rows(cursor, report.namespace_oid, report.owner_oid,
        report.client_oid, installer_oid, set(public_oids), set(client_oids), set(tolerated_oids))
    if _tolerated_privileges(before, tolerated_oids) != _tolerated_privileges(after, tolerated_oids):
        raise ValueError('Tolerated native grants changed during installation')
    return _canonical_evidence(resolved_tolerated, before + after)


def _verify_final_acl_rows(cursor, namespace, owner, client, installer, public_routines,
                           client_routines, tolerated_oids):
    """Require the final native ACL to equal the installer’s declared grants."""
    cursor.execute('''WITH objects AS (
        SELECT 'schema'::text kind,n.oid,n.nspname::text name,NULL::text detail,
            n.nspowner owner,n.nspacl acl,'n'::"char" acl_kind
        FROM pg_catalog.pg_namespace n WHERE n.oid=%s
        UNION ALL SELECT CASE WHEN c.relkind='S' THEN 'sequence' ELSE 'relation' END,
            c.oid,c.relname::text,NULL::text,c.relowner,c.relacl,
            CASE WHEN c.relkind='S' THEN 's' ELSE 'r' END::"char"
        FROM pg_catalog.pg_class c WHERE c.relnamespace=%s AND c.relkind NOT IN ('i','I')
        UNION ALL SELECT 'routine',p.oid,p.proname::text,
            pg_catalog.pg_get_function_identity_arguments(p.oid),p.proowner,p.proacl,'f'::"char"
        FROM pg_catalog.pg_proc p WHERE p.pronamespace=%s
        UNION ALL SELECT 'type',t.oid,t.typname::text,NULL::text,t.typowner,t.typacl,'T'::"char"
        FROM pg_catalog.pg_type t WHERE t.typnamespace=%s), grants AS (
        SELECT o.kind,o.oid,a.grantor,a.grantee,a.privilege_type,a.is_grantable
        FROM objects o CROSS JOIN LATERAL pg_catalog.aclexplode(
            coalesce(o.acl,pg_catalog.acldefault(o.acl_kind,o.owner))) a
        UNION ALL SELECT 'column',a.attrelid,x.grantor,x.grantee,x.privilege_type,x.is_grantable
        FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
        CROSS JOIN LATERAL pg_catalog.aclexplode(a.attacl) x
        WHERE c.relnamespace=%s AND c.relkind IN ('r','p')
          AND a.attnum>0 AND NOT a.attisdropped AND a.attacl IS NOT NULL)
        SELECT kind,oid,grantor,grantee,privilege_type,is_grantable
        FROM grants ORDER BY kind,oid,grantor,grantee,privilege_type,is_grantable''',
        (namespace,namespace,namespace,namespace,namespace),prepare=False)
    observed=[row for row in cursor.fetchall() if row[3] not in tolerated_oids]
    expected=set()
    permitted_grantors={owner,installer,*tolerated_oids}
    owner_privileges={
        'schema':('CREATE','USAGE'),
        'relation':('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'),
        'sequence':('USAGE','SELECT','UPDATE'),
        'routine':('EXECUTE',), 'type':('USAGE',),
    }
    cursor.execute('''SELECT 'schema',oid FROM pg_catalog.pg_namespace WHERE oid=%s
        UNION ALL SELECT CASE WHEN relkind='S' THEN 'sequence' ELSE 'relation' END,oid
          FROM pg_catalog.pg_class WHERE relnamespace=%s AND relkind NOT IN ('i','I')
        UNION ALL SELECT 'routine',oid FROM pg_catalog.pg_proc WHERE pronamespace=%s
        UNION ALL SELECT 'type',oid FROM pg_catalog.pg_type WHERE typnamespace=%s''',
        (namespace,namespace,namespace,namespace),prepare=False)
    for kind, oid in cursor.fetchall():
        for privilege in owner_privileges[kind]:
            expected.add((kind,oid,owner,privilege,False))
    cursor.execute('''SELECT oid FROM pg_catalog.pg_type
        WHERE typnamespace=%s AND typacl IS NULL''', (namespace,), prepare=False)
    for (oid,) in cursor.fetchall():
        # PostgreSQL's native default type ACL exposes USAGE to PUBLIC.
        expected.add(('type', oid, 0, 'USAGE', False))
    for privilege in ('USAGE',):
        expected.add(('schema',namespace,0,privilege,False))
        expected.add(('schema',namespace,client,privilege,False))
    cursor.execute('''SELECT oid FROM pg_catalog.pg_proc
        WHERE pronamespace=%s AND oid=ANY(%s::oid[])''',(namespace,list(public_routines)),prepare=False)
    for (oid,) in cursor.fetchall():
        expected.add(('routine',oid,0,'EXECUTE',False))
    cursor.execute('''SELECT oid FROM pg_catalog.pg_proc
        WHERE pronamespace=%s AND oid=ANY(%s::oid[])''',(namespace,list(client_routines)),prepare=False)
    for (oid,) in cursor.fetchall():
        expected.add(('routine',oid,client,'EXECUTE',False))
    admin_oids=set()
    for signature in ('admin_install_recovery()', 'grant_import_audit_access(text,text,text)'):
        cursor.execute('SELECT pg_catalog.to_regprocedure(%s)::oid',('truss.'+signature,),prepare=False)
        row=cursor.fetchone()
        if row is not None and row[0] is not None:
            admin_oids.add(row[0])
    for oid in admin_oids:
        expected.add(('routine',oid,installer,'EXECUTE',False))
    observed_keys={(kind,oid,grantee,privilege,grantable)
        for kind,oid,grantor,grantee,privilege,grantable in observed}
    expected_keys=expected
    unexpected=(observed_keys-expected_keys)|(expected_keys-observed_keys)
    if any(grantee == owner and grantor != owner
           for _, _, grantor, grantee, _, _ in observed):
        unexpected.add(('owner-grantor',))
    if any(grantor not in permitted_grantors for _,_,grantor,_,_,_ in observed):
        unexpected.add(('undeclared-grantor',))
    if unexpected:
        raise ValueError('Native ACL differs from exact installer-declared grants')


def installation_grant_policy_with_cursor(cursor):
    """Read the one durable policy and reject role replacement or corruption."""
    cursor.execute("""SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid=a.attrelid JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='truss' AND c.relname='catalog_runtime_installation'
          AND a.attname='managed_grants' AND a.attnum>0 AND NOT a.attisdropped)""",prepare=False)
    if cursor.fetchone() != (True,):
        return _canonical_evidence((),())
    cursor.execute('SELECT managed_grants FROM truss.catalog_runtime_installation WHERE singleton', prepare=False)
    rows = cursor.fetchmany(2)
    if len(rows) != 1 or type(rows[0][0]) is not dict:
        raise ValueError('One durable managed-grants policy required')
    value = rows[0][0]
    if (set(value) != {'interfaceVersion', 'roles', 'observations'}
            or value['interfaceVersion'] != _GRANT_POLICY_VERSION
            or type(value['roles']) is not list
            or type(value['observations']) is not list
            or len(value['roles']) > _MAX_TOLERATED_GRANTEES
            or len(value['observations']) > _MAX_GRANT_OBSERVATIONS):
        raise ValueError('Managed-grants policy shape or bounds changed')
    policy = []
    for item in value['roles']:
        if (type(item) is not dict or set(item) != {'name', 'oid'}
                or not _name(item['name']) or type(item['oid']) is not int
                or not 0 < item['oid'] < 2**32):
            raise ValueError('Managed-grants role identity is invalid')
        policy.append((item['name'], item['oid']))
    if (len({name for name, _ in policy}) != len(policy)
            or len({oid for _, oid in policy}) != len(policy)
            or tuple(sorted(policy, key=lambda pair: pair[0].encode('utf8'))) != tuple(policy)):
        raise ValueError('Managed-grants role identities are not canonical')
    for observation in value['observations']:
        column = observation.get('column') if type(observation) is dict else None
        detail = observation.get('detail') if type(observation) is dict else None
        if (type(observation) is not dict
                or set(observation) != {'class', 'objectOid', 'name', 'detail', 'column',
                    'granteeOid', 'grantorOid', 'privilege', 'grantOption', 'phase', 'grantee', 'grantor'}
                or type(observation['class']) is not str
                or observation['class'] not in _GRANT_OBJECT_CLASSES
                or type(observation['phase']) is not str
                or observation['phase'] not in _GRANT_PHASES
                or type(observation['objectOid']) is not int
                or not 0 < observation['objectOid'] < 2**32
                or type(observation['granteeOid']) is not int
                or not 0 < observation['granteeOid'] < 2**32
                or type(observation['grantorOid']) is not int
                or not 0 < observation['grantorOid'] < 2**32
                or type(observation['name']) is not str
                or not observation['name'] or '\0' in observation['name']
                or len(observation['name'].encode('utf8')) > 63
                or (detail is not None and (type(detail) is not str or len(detail.encode('utf8')) > 16384))
                or (column is not None and (type(column) is not dict or set(column) != {'number','name'}
                    or type(column['number']) is not int or column['number'] <= 0
                    or type(column['name']) is not str or not column['name'] or '\0' in column['name']
                    or len(column['name'].encode('utf8')) > 63))
                or type(observation['privilege']) is not str
                or observation['privilege'] not in _GRANT_PRIVILEGES[observation['class']]
                or type(observation['grantOption']) is not bool):
            raise ValueError('Managed-grants observation is invalid')
        for key in ('grantee','grantor'):
            if (type(observation[key]) is not str or not observation[key]
                    or '\0' in observation[key] or len(observation[key].encode('utf8')) > 63):
                raise ValueError('Managed-grants role observation is invalid')
        if (observation['phase'] == 'pre_ownership' and observation['granteeOid'] not in
                {oid for _, oid in policy}):
            raise ValueError('Managed-grants observation is not for a tolerated role')
        if observation['phase'] == 'post_installation' and observation['granteeOid'] not in {oid for _, oid in policy}:
            raise ValueError('Managed-grants observation is not for a tolerated role')
        if observation['granteeOid'] not in {oid for _, oid in policy}:
            raise ValueError('Managed-grants observation grantee is not selected')
        if (type(observation['column']) is dict and observation['column']['number'] > 32767):
            raise ValueError('Managed-grants column number is outside PostgreSQL bounds')
        if observation['grantee'] != next(name for name, oid in policy if oid == observation['granteeOid']):
            raise ValueError('Managed-grants grantee name/OID differs')
    if len({json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=False) for row in value['observations']}) != len(value['observations']):
        raise ValueError('Managed-grants observations are duplicated')
    if _canonical_evidence(policy, value['observations']) != value:
        raise ValueError('Managed-grants observations are not canonical')
    if policy:
        cursor.execute('SELECT oid,rolname::text FROM pg_catalog.pg_roles WHERE oid=ANY(%s) ORDER BY oid',
            ([oid for _, oid in policy],), prepare=False)
        current = {oid: name for oid, name in cursor.fetchall()}
        if current != {oid: name for name, oid in policy}:
            raise ValueError('Managed-grants native role identity drifted')
    return value


def require_empty_managed_grants_with_cursor(cursor, profile):
    """Refuse protected activation for profiles not yet qualified with policy."""
    managed = installation_grant_policy_with_cursor(cursor)
    if managed['roles']:
        raise _UnsupportedProfileIncompatibility(profile+' activation is incompatible with managed platform grants')


class _ThirdPartyGrantRefusal(ValueError):
    """Private marker translated only after PsycopgHost confirms rollback."""
    def __init__(self, role_name, object_class, phase):
        super().__init__('third-party installation grant')
        self.role_name = role_name
        self.object_class = object_class if object_class in _GRANT_OBJECT_CLASSES else None
        self.phase = phase if phase in _GRANT_PHASES else None


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


def _verify(cursor, namespace, owner, client, original, *, allowed_routines=()):
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
        if oid in allowed_routines:
            continue
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
    return InstallationPrivilegeReport(namespace,owner,client,len(relations),len(routines),len(types),{})


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


def protect_installation_with_cursor(cursor, roles, *, resolved_tolerated=None):
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
    tolerated = (_resolved_tolerated_roles(cursor, roles.tolerated_grantees,
        owner=roles.owner, client=roles.client, installer=actor[1])
        if resolved_tolerated is None else resolved_tolerated)
    if (type(tolerated) is not tuple
            or tuple(name for name, _ in tolerated) != _policy_names(
                roles.tolerated_grantees, reserved=(roles.owner, roles.client, actor[1]))):
        raise ValueError('Resolved tolerated grantee identity mismatch')
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
    columns = _rows(cursor,'''SELECT a.attrelid,a.attname,a.attacl FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
        WHERE c.relnamespace=%s AND c.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped
        ORDER BY a.attrelid,a.attnum''',(namespace[0],))
    tolerated_oids = tuple(oid for _, oid in tolerated)
    if tolerated:
        pre_observations = _acl_observations(cursor, namespace[0], phase='pre_ownership',
            installer_oid=actor[0], tolerated_oids=tolerated_oids)
    else:
        # Preserve the existing strict fast path when no policy is selected.
        acls = [('schema',namespace[2])] + [('sequence' if row[2]=='S' else 'relation', row[4])
            for row in relations if row[2] not in ('i','I')
        ] + [('routine',row[4]) for row in routines] + [('type',row[4]) for row in types]
        for object_class,acl in acls:
            if acl is not None:
                cursor.execute('SELECT grantee FROM pg_catalog.aclexplode(%s::aclitem[])', (acl,), prepare=False)
                foreign=next((row[0] for row in cursor.fetchall() if row[0] not in (0,actor[0])),None)
                if foreign is not None:
                    raise _ThirdPartyGrantRefusal(_role_name(cursor,foreign), object_class, 'pre_ownership')
        for _,_,acl in columns:
            if acl is not None:
                cursor.execute('SELECT grantee FROM pg_catalog.aclexplode(%s::aclitem[])',(acl,),prepare=False)
                found=cursor.fetchall()
                foreign=next((row[0] for row in found if row[0] not in (0,actor[0])),None)
                if foreign is not None:
                    raise _ThirdPartyGrantRefusal(_role_name(cursor,foreign), 'column', 'pre_ownership')
        pre_observations = []
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
    if tolerated:
        post_observations = _acl_observations(cursor, namespace[0], phase='post_installation',
            installer_oid=actor[0], tolerated_oids=tolerated_oids,
            admitted_oids=(owner,client))
    else:
        post_observations = []
    if _tolerated_privileges(pre_observations,tolerated_oids) != _tolerated_privileges(post_observations,tolerated_oids):
        raise ValueError('Tolerated native grants changed during installation')
    managed_grants = _canonical_evidence(tolerated, pre_observations + post_observations)
    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)", (original_search_path,), prepare=False)
    if cursor.fetchone()[0] != original_search_path:
        raise ValueError('Caller search path restoration failed')
    return InstallationPrivilegeReport(report.namespace_oid, report.owner_oid,
        report.client_oid, report.relations, report.routines, report.types, managed_grants,objects)
