# SPDX-License-Identifier: MIT OR Apache-2.0
"""Read-only native inventories and bounded preservation census for migrations."""
import json
from hashlib import sha256
from psycopg import sql
from ._installation_privileges import installation_administrator_with_cursor


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()


# pg_get_* definitions resolve native identities independently of source SQL formatting.
_STRUCTURE = {
 'relations': """SELECT c.relname,c.relkind,c.relpersistence,c.relrowsecurity,c.relforcerowsecurity,
 c.reloptions,c.relispartition,pg_get_expr(c.relpartbound,c.oid),a.amname,t.spcname,pg_get_partkeydef(c.oid)
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace LEFT JOIN pg_am a ON a.oid=c.relam
 LEFT JOIN pg_tablespace t ON t.oid=c.reltablespace WHERE n.nspname='truss' ORDER BY c.relname""",
 'inheritance': """SELECT cn.nspname,c.relname,pn.nspname,p.relname,i.inhseqno,i.inhdetachpending
 FROM pg_inherits i JOIN pg_class c ON c.oid=i.inhrelid JOIN pg_namespace cn ON cn.oid=c.relnamespace
 JOIN pg_class p ON p.oid=i.inhparent JOIN pg_namespace pn ON pn.oid=p.relnamespace
 WHERE cn.nspname='truss' OR pn.nspname='truss'
 ORDER BY cn.nspname,c.relname,pn.nspname,p.relname,i.inhseqno""",
 'columns': """SELECT c.relname,a.attnum,a.attname,format_type(a.atttypid,a.atttypmod),
 a.attnotnull,a.attidentity,a.attgenerated,a.attisdropped,a.attstorage,a.attcompression,a.attndims,
 a.attoptions,cn.nspname,co.collname,pg_get_expr(d.adbin,d.adrelid)
 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
 LEFT JOIN pg_collation co ON co.oid=a.attcollation LEFT JOIN pg_namespace cn ON cn.oid=co.collnamespace
 LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
 WHERE n.nspname='truss' AND a.attnum>0 ORDER BY c.relname,a.attnum""",
 'constraints': """SELECT c.relname,k.conname,k.contype,k.convalidated,k.condeferrable,k.condeferred,
 pg_get_constraintdef(k.oid,false) FROM pg_constraint k JOIN pg_namespace n ON n.oid=k.connamespace
 LEFT JOIN pg_class c ON c.oid=k.conrelid WHERE n.nspname='truss' ORDER BY c.relname,k.conname""",
 'routines': """SELECT p.proname,pg_get_function_identity_arguments(p.oid),pg_get_functiondef(p.oid)
 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss'
 ORDER BY p.proname,pg_get_function_identity_arguments(p.oid)""",
 'indexes': """SELECT c.relname,pg_get_indexdef(c.oid),i.indisvalid,i.indisready,i.indislive
 FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='truss' ORDER BY c.relname""",
 'triggers': """SELECT c.relname,t.tgname,t.tgenabled,t.tgisinternal,pg_get_triggerdef(t.oid,false)
 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='truss' ORDER BY c.relname,t.tgname""",
 'sequences': """SELECT c.relname,format_type(s.seqtypid,NULL),s.seqstart::text,s.seqincrement::text,
 s.seqmax::text,s.seqmin::text,s.seqcache::text,s.seqcycle FROM pg_sequence s JOIN pg_class c ON c.oid=s.seqrelid
 JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' ORDER BY c.relname""",
 'types': """SELECT t.typname,t.typtype,format_type(t.typbasetype,t.typtypmod),t.typnotnull,t.typdefault,
 (SELECT array_agg(e.enumlabel ORDER BY e.enumsortorder) FROM pg_enum e WHERE e.enumtypid=t.oid)
 FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname='truss'
 AND t.typrelid=0 AND t.typelem=0 ORDER BY t.typname""",
 'policies': """SELECT c.relname,p.polname,p.polcmd,p.polpermissive,pg_get_expr(p.polqual,p.polrelid),
 pg_get_expr(p.polwithcheck,p.polrelid) FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid
 JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' ORDER BY c.relname,p.polname""",
 'rules': """SELECT c.relname,r.rulename,pg_get_ruledef(r.oid,false) FROM pg_rewrite r JOIN pg_class c ON c.oid=r.ev_class
 JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' ORDER BY c.relname,r.rulename""",
 'extras': """SELECT 'operator',o.oprname::text FROM pg_operator o JOIN pg_namespace n ON n.oid=o.oprnamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'opclass',o.opcname::text FROM pg_opclass o JOIN pg_namespace n ON n.oid=o.opcnamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'opfamily',o.opfname::text FROM pg_opfamily o JOIN pg_namespace n ON n.oid=o.opfnamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'conversion',o.conname::text FROM pg_conversion o JOIN pg_namespace n ON n.oid=o.connamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'collation',o.collname::text FROM pg_collation o JOIN pg_namespace n ON n.oid=o.collnamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'text_search_config',o.cfgname::text FROM pg_ts_config o JOIN pg_namespace n ON n.oid=o.cfgnamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'text_search_dictionary',o.dictname::text FROM pg_ts_dict o JOIN pg_namespace n ON n.oid=o.dictnamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'text_search_parser',o.prsname::text FROM pg_ts_parser o JOIN pg_namespace n ON n.oid=o.prsnamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'text_search_template',o.tmplname::text FROM pg_ts_template o JOIN pg_namespace n ON n.oid=o.tmplnamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'extension',o.extname::text FROM pg_extension o JOIN pg_namespace n ON n.oid=o.extnamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'statistics',o.stxname::text FROM pg_statistic_ext o JOIN pg_namespace n ON n.oid=o.stxnamespace WHERE n.nspname='truss'
 ORDER BY 1,2""",
}


def structure(cursor):
    result={}
    # Native timestamptz deparse depends on the observing session. A scoped
    # transaction/savepoint gives even an idle autocommit observer a stable cut;
    # restore its timezone before returning to an existing caller transaction.
    with cursor.connection.transaction():
        cursor.execute("SELECT current_setting('TimeZone')",prepare=False)
        original_zone=cursor.fetchone()[0]
        cursor.execute("SET LOCAL TimeZone='UTC'",prepare=False)
        try:
            for key,query in _STRUCTURE.items():
                cursor.execute(query,prepare=False)
                result[key]=[list(row) for row in cursor.fetchall()]
        finally:
            cursor.execute("SELECT set_config('TimeZone',%s,true)",(original_zone,),prepare=False)
    # Internal FK trigger names embed OIDs; constraint definitions already account for them.
    result['triggers']=[row for row in result['triggers'] if not row[3]]
    return result


def context(cursor):
    cursor.execute('SELECT installation_id::text,owner_oid,registrar_oid,source_epoch::text FROM truss.catalog_runtime_installation',prepare=False)
    rows=cursor.fetchmany(2)
    if len(rows)!=1:raise ValueError('One original installation required')
    identity,owner,registrar,epoch=rows[0]
    installation_administrator_with_cursor(cursor,owner)
    cursor.execute("SELECT system_identifier::text FROM pg_control_system()",prepare=False)
    system=cursor.fetchone()[0]
    cursor.execute("SELECT oid::text,current_database() FROM pg_database WHERE datname=current_database()",prepare=False)
    oid,name=cursor.fetchone()
    return {'kind':'installed','installationId':identity,'sourceEpoch':epoch,
            'databaseIdentity':system+':'+oid+':'+name,'schemaName':'truss'},owner,registrar


def verify_profile(cursor,expected):
    cursor.execute("SELECT current_setting('server_version_num')",prepare=False)
    if cursor.fetchone()!=(expected['manifest']['postgresVersion'],):raise ValueError('Exact qualified PostgreSQL version required')
    cursor.execute('SELECT release_id,release_sha256,layout_profile,preparation_configuration FROM truss.runtime_current_installation()',prepare=False)
    wanted=(expected['manifest']['releaseId'],expected['sha256'],expected['manifest']['layoutProfile'],expected['configuration'])
    if cursor.fetchmany(2)!=[wanted]:raise ValueError('Installed release/layout/preparation profile drifted')


_ACL = """WITH objects AS (
 SELECT 'schema' AS kind,'truss'::text AS name,nspowner AS owner,nspacl AS acl,'n'::\"char\" AS code FROM pg_namespace WHERE nspname='truss'
 UNION ALL SELECT 'relation',c.relname::text,c.relowner,c.relacl,CASE WHEN c.relkind='S' THEN 's' ELSE 'r' END::\"char\"
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relkind NOT IN ('i','I')
 UNION ALL SELECT 'routine',p.proname||'('||oidvectortypes(p.proargtypes)||')',p.proowner,p.proacl,'f'::\"char\"
 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss'
 UNION ALL SELECT 'type',t.typname::text,t.typowner,t.typacl,'T'::\"char\" FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace
 WHERE n.nspname='truss')
 SELECT o.kind,o.name,o.owner,a.grantee,a.privilege_type,a.is_grantable,a.grantor FROM objects o
 CROSS JOIN LATERAL aclexplode(coalesce(o.acl,acldefault(o.code,o.owner))) a
 ORDER BY o.kind,o.name,a.grantee,a.privilege_type"""


def acl(cursor,*,full_names=False):
    query=_ACL if full_names else _ACL.replace('SELECT o.kind,o.name,o.owner','SELECT o.kind,o.name::name::text,o.owner')
    cursor.execute(query,prepare=False)
    return [list(row) for row in cursor.fetchall()]


def roles(cursor,owner,registrar):
    result={owner:{'owner'},registrar:{'registrar'},0:{'public'}}
    def add(oid,kind):result.setdefault(oid,set()).add(kind)
    cursor.execute("SELECT DISTINCT a.grantee FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE n.nspname='truss' AND p.proname='admin_install_recovery' AND a.grantee<>p.proowner",prepare=False)
    for (oid,) in cursor.fetchall():
        if oid in (owner,registrar,0):continue
        cursor.execute('SELECT rolsuper OR rolcreaterole FROM pg_roles WHERE oid=%s',(oid,),prepare=False)
        if cursor.fetchone()!=(True,):raise ValueError('Unsafe installation administrator grant')
        add(oid,'administrator')
    cursor.execute('SELECT reader_role,writer_role FROM truss.module_access',prepare=False)
    for reader,writer in cursor.fetchall():
        cursor.execute('SELECT oid,rolname FROM pg_roles WHERE rolname=ANY(%s)',([reader,writer],),prepare=False)
        for oid,name in cursor.fetchall():add(oid,'reader' if name==reader else 'writer')
    for table,column,kind in [('runtime_feed_consumer','reader_oid','feed'),('runtime_import_audit_access','auditor_oid','audit')]:
        cursor.execute(sql.SQL('SELECT DISTINCT {} FROM truss.{}').format(sql.Identifier(column),sql.Identifier(table)),prepare=False)
        for (oid,) in cursor.fetchall():add(oid,kind)
    return result


def verify(cursor,expected,acl_profiles,*,full_names=False):
    if structure(cursor)!=expected:raise ValueError('Installed native definitions drifted')
    ctx,owner,registrar=context(cursor)
    cursor.execute("SELECT nspowner FROM pg_namespace WHERE nspname='truss'",prepare=False)
    if cursor.fetchone()!=(owner,):raise ValueError('Installation owner drifted')
    cursor.execute('SELECT rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolinherit FROM pg_roles WHERE oid=ANY(%s)',([owner,registrar],),prepare=False)
    if cursor.fetchall()!=[(False,)*7,(False,)*7]:raise ValueError('Installation roles drifted')
    mapping=roles(cursor,owner,registrar)
    for oid,kinds in mapping.items():
        if kinds & {'owner','registrar','administrator','public'}:continue
        cursor.execute("""WITH RECURSIVE memberships(oid) AS (SELECT %s::oid UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.oid)
            SELECT coalesce(bool_or(r.rolsuper OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication OR r.rolbypassrls OR r.oid IN (%s,%s)
                OR r.rolname IN ('pg_read_server_files','pg_write_server_files','pg_execute_server_program')),false)
            FROM memberships m JOIN pg_roles r ON r.oid=m.oid""",(oid,owner,registrar),prepare=False)
        if cursor.fetchone()!=(False,):raise ValueError('Unsafe module/feed/audit role membership')
    actual={oid:set() for oid in mapping}
    for kind,name,objowner,grantee,priv,grantable,grantor in acl(cursor,full_names=full_names):
        if objowner!=owner or grantee not in mapping or grantor not in (owner,grantee):
            raise ValueError('Unexpected native owner or grant: '+kind+' '+name)
        actual[grantee].add((kind,name,priv,grantable))
    for oid,kinds in mapping.items():
        wanted={tuple(row) for kind in kinds for row in acl_profiles[kind]}
        if actual[oid]!=wanted:raise ValueError('Installed privileges drifted: '+','.join(sorted(kinds)))
    # Attribute grants/default privileges are independent of relation ACLs.
    cursor.execute("SELECT count(*) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND a.attacl IS NOT NULL",prepare=False)
    if cursor.fetchone()!=(0,):raise ValueError('Unexpected column grants')
    cursor.execute("SELECT d.defaclobjtype,d.defaclnamespace,a.grantee,a.privilege_type,a.is_grantable FROM pg_default_acl d CROSS JOIN LATERAL aclexplode(d.defaclacl) a WHERE d.defaclrole=%s ORDER BY d.defaclobjtype",(owner,),prepare=False)
    if set(cursor.fetchall())!={('f',0,owner,'EXECUTE',False),('T',0,owner,'USAGE',False)}:raise ValueError('Private default grants drifted')
    return ctx


def matches_inventory(observed,profile):
    expected=profile['inventory']
    if observed.keys()!=expected.keys():return False
    rules={(r['surface'],*r['identity']):r['definitions'] for r in profile.get('definitionAlternatives',[])}
    initial={tuple(r['identity']):r['rows'] for r in profile.get('initializationAlternatives',[])}
    for category,rows in expected.items():
        actual=observed[category]
        if actual==rows:continue
        if category not in ('constraints','triggers','relations') or len(actual)!=len(rows):return False
        for before,after in zip(rows,actual,strict=True):
            if before==after:continue
            if category=='relations':
                permitted=initial.get((before[0],),[])
                if before not in permitted or after not in permitted:return False
                continue
            permitted=rules.get((category,*before[:2]),[])
            if before[:-1]!=after[:-1] or before[-1] not in permitted or after[-1] not in permitted:return False
    return True


def require_preserved_initialization(source,target):
    """Qualified source variants are distinct native instants, never conversions."""
    for rule in source.get('initializationAlternatives',[]):
        identity=rule['identity'][0]
        before=[r for r in source['inventory']['relations'] if r[0]==identity]
        after=[r for r in target['inventory']['relations'] if r[0]==identity]
        if len(before)!=1 or before!=after:raise ValueError('Migration changed original native initialization')


def verify_artifact(cursor,profile):
    observed=structure(cursor)
    if not matches_inventory(observed,profile):raise ValueError('Installed native definitions drifted')
    selected={**profile,'inventory':observed}
    return verify(cursor,observed,profile['acl'],full_names=profile.get('aclNameProfile')=='truss-native-acl-names/0.2'),selected


def profile_for(manifest,artifacts,digest):
    """Original immutable profile plus separately pinned exact ACL admission evidence."""
    profile=json.loads(artifacts[digest+'.json'])
    supplement=manifest.get('exactAclProfiles',{}).get(digest)
    if supplement is not None:
        selected=json.loads(artifacts[supplement])
        if selected['runtimeManifestSha256']!=digest or selected['aclNameProfile']!='truss-native-acl-names/0.2':
            raise ValueError('Original exact ACL profile correspondence required')
        profile={**profile,'acl':selected['acl'],'aclNameProfile':selected['aclNameProfile']}
    return profile


def installed_profile(cursor,manifest,artifacts):
    """Classify catalog definitions before calling any installation routine."""
    observed=structure(cursor)
    for digest in [manifest['target'],*manifest['sources']]:
        expected=profile_for(manifest,artifacts,digest)
        if matches_inventory(observed,expected):
            selected={**expected,'inventory':observed}
            ctx=verify(cursor,observed,expected['acl'],full_names=expected.get('aclNameProfile')=='truss-native-acl-names/0.2')
            verify_profile(cursor,selected)
            return ctx,selected
    raise ValueError('Installed native definitions drifted or source unsupported')


def preservation(cursor,expected,max_bytes=268435456):
    result={};total=0
    for name,kind,*_ in expected['relations']:
        if kind not in ('r','p','S'):continue
        if kind=='S':
            cursor.execute(sql.SQL('SELECT last_value::text,is_called FROM truss.{}').format(sql.Identifier(name)),prepare=False)
            result[name]=list(cursor.fetchone());continue
        digest=sha256();count=0
        # A named portal prevents psycopg buffering the entire table before the
        # byte limit can be checked. One row is bounded by the admitted source.
        with cursor.connection.cursor(name='truss_migration_census') as scan:
            if hasattr(cursor,'check'):cursor.check()
            scan.execute(sql.SQL('SELECT row_to_json(t)::text FROM truss.{} t ORDER BY row_to_json(t)::text COLLATE "C"').format(sql.Identifier(name)))
            while rows:=scan.fetchmany(1):
                if hasattr(cursor,'check'):cursor.check()
                for (row,) in rows:
                    raw=row.encode();total+=len(raw)
                    if total>max_bytes:raise ValueError('Migration preservation byte limit exceeded')
                    digest.update(len(raw).to_bytes(8,'big'));digest.update(raw);count+=1
        result[name]={'rows':count,'sha256':digest.hexdigest()}
    return result
