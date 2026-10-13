"""Selected named Subject native helper readback; no role/issuer lifetime proof."""
import json

def verify_catalog_subject_helpers_with_cursor(cursor,source,*,expected_callers=None):
    cursor.execute("SELECT c.relowner::pg_catalog.text,r.rolcanlogin::pg_catalog.text,r.rolsuper::pg_catalog.text,r.rolbypassrls::pg_catalog.text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_roles r ON r.oid OPERATOR(pg_catalog.=) c.relowner WHERE c.oid OPERATOR(pg_catalog.=) 'truss.object'::pg_catalog.regclass",prepare=False,binary=False)
    if cursor.description is None or len(cursor.description)!=4 or any(d.type_code!=25 for d in cursor.description):raise ValueError('Exact native helper owner descriptors required')
    owners=cursor.fetchmany(2)
    if len(owners)!=1 or owners[0][1:]!=('false','false','false'):raise ValueError('Original non-login ordinary helper owner required')
    owner=owners[0][0]
    if expected_callers is None:
        cursor.execute('SELECT oid::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) SESSION_USER',prepare=False,binary=False)
        if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=25:
            raise ValueError('Exact native helper caller role descriptor required')
        callers=cursor.fetchmany(2)
        if len(callers)!=1 or type(callers[0][0]) is not str:
            raise ValueError('Original unique native helper caller role required')
        caller=callers[0][0]
        expected_callers=(int(caller),)
    elif (type(expected_callers) is not tuple or not 1<=len(expected_callers)<=256
            or any(type(oid) is not int or not 1<=oid<=4294967295 for oid in expected_callers)
            or len(set(expected_callers))!=len(expected_callers)):
        raise ValueError('Exact registered Subject role identities required')
    bodies=[part.split('$$;',1)[0] for part in source.split('AS $$')[1:]]
    if len(bodies)!=2:raise ValueError('Exact original helper definitions required')
    for name,language,return_oid,names,modes,types,body in (
            ('catalog_subject_current','plpgsql','25',['actor','staff_id'],['i','t'],['25','25'],bodies[0]),
            ('catalog_subject_context','sql','2249',['actor','installation_id','database_oid','role_oid'],['i','t','t','t'],['25']*4,bodies[1])):
        cursor.execute("SELECT p.proowner::pg_catalog.text,l.lanname::pg_catalog.text,p.prokind::pg_catalog.text,p.pronargs::pg_catalog.text,p.proargtypes::pg_catalog.text,p.prorettype::pg_catalog.text,p.proretset::pg_catalog.text,p.proisstrict::pg_catalog.text,p.prosecdef::pg_catalog.text,p.provolatile::pg_catalog.text,p.proparallel::pg_catalog.text,p.proleakproof::pg_catalog.text,p.prosupport::pg_catalog.oid::pg_catalog.text,pg_catalog.to_jsonb(p.proconfig)::pg_catalog.text,p.prosrc,pg_catalog.to_jsonb(p.proargnames)::pg_catalog.text,pg_catalog.to_jsonb(p.proargmodes)::pg_catalog.text,pg_catalog.to_jsonb(p.proallargtypes)::pg_catalog.text,(p.prosqlbody IS NULL)::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace JOIN pg_catalog.pg_language l ON l.oid OPERATOR(pg_catalog.=) p.prolang WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) %s AND p.proargtypes OPERATOR(pg_catalog.=) '25'::pg_catalog.oidvector",(name,),prepare=False,binary=False)
        if cursor.description is None or len(cursor.description)!=19 or any(d.type_code!=25 for d in cursor.description):raise ValueError('Exact native helper TEXT descriptors required')
        expected=(owner,language,'f','1','25',return_oid,'true','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',body,json.dumps(names),json.dumps(modes),json.dumps(types),'true')
        if cursor.fetchmany(2)!=[expected]:raise ValueError('Exact installed catalog subject helper snapshot required')
        cursor.execute("SELECT a.grantee::pg_catalog.text,a.grantor::pg_catalog.text,a.privilege_type::pg_catalog.text,a.is_grantable::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) %s AND p.proargtypes OPERATOR(pg_catalog.=) '25'::pg_catalog.oidvector ORDER BY a.grantee,a.grantor,a.privilege_type,a.is_grantable",(name,),prepare=False,binary=False)
        if cursor.description is None or len(cursor.description)!=4 or any(d.type_code!=25 for d in cursor.description):
            raise ValueError('Exact native helper ACL descriptors required')
        expected_acl=sorted([(owner,owner,'EXECUTE','false')]+[(str(caller),owner,'EXECUTE','false') for caller in expected_callers],key=lambda row:int(row[0]))
        if int(owner) in expected_callers or cursor.fetchmany(len(expected_acl)+1)!=expected_acl:
            raise ValueError('Exact installed catalog subject helper ACL required')

