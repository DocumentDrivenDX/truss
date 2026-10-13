"""Selected native writer metadata checks, not an issuer or DDL lifetime proof."""
from hashlib import sha256

_BODY_SHA256='8c3c1418af9cd20ee7c85cee8babdc74cc0e16f7391b1c91074994cc9e54c1c1'

def require_data_writer_homes(cursor,owner_oid,identity,profile,home_oids):
    cursor.execute("""SELECT p.oid,p.proowner,l.lanname,l.lanpltrusted,
        p.prorettype OPERATOR(pg_catalog.=) 'pg_catalog.trigger'::pg_catalog.regtype,p.prokind::pg_catalog.text,
        p.provolatile::pg_catalog.text,p.prosecdef,p.proisstrict,p.proretset,
        p.proleakproof,p.proparallel::pg_catalog.text,p.pronargs,p.pronargdefaults,
        p.provariadic,p.proargtypes::pg_catalog.text,p.proallargtypes IS NULL,p.proargmodes IS NULL,
        p.proargnames IS NULL,p.proargdefaults IS NULL,
        p.proconfig OPERATOR(pg_catalog.=) ARRAY['search_path=pg_catalog, pg_temp']::pg_catalog.text[],p.prosrc,
        NOT EXISTS(SELECT 1 FROM pg_catalog.aclexplode(COALESCE(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
          WHERE a.grantee OPERATOR(pg_catalog.<>) p.proowner
             OR a.grantor OPERATOR(pg_catalog.<>) p.proowner
             OR a.privilege_type OPERATOR(pg_catalog.<>) 'EXECUTE' OR a.is_grantable),
        p.prosupport OPERATOR(pg_catalog.=) 0,p.probin IS NULL,p.prosqlbody IS NULL
        FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace
        JOIN pg_catalog.pg_language l ON l.oid OPERATOR(pg_catalog.=) p.prolang
        WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) 'security_data_writer_guard'
          AND p.pronargs OPERATOR(pg_catalog.=) 0 AND pg_catalog.octet_length(p.prosrc) OPERATOR(pg_catalog.<=) 8192""",prepare=False)
    rows=cursor.fetchmany(2)
    if len(rows)!=1:raise ValueError('Original data writer function required')
    row=rows[0];function_oid=row[0]
    if (row[1:21]!=(owner_oid,'plpgsql',True,True,'f','v',True,False,False,False,'u',0,0,0,'',True,True,True,True,True)
            or type(row[21]) is not str or sha256(row[21].encode('utf8')).hexdigest()!=_BODY_SHA256 or row[22] is not True or row[23:]!=(True,True,True)):
        raise ValueError('Original data writer function metadata required')
    for oid in home_oids:
        cursor.execute("SELECT relkind::pg_catalog.text,relpersistence::pg_catalog.text FROM pg_catalog.pg_class WHERE oid OPERATOR(pg_catalog.=) %s::pg_catalog.oid",(oid,),prepare=False)
        if cursor.fetchmany(2)!=[('r','p')]:raise ValueError('Original ordinary writer relation required')
        cursor.execute("""SELECT t.tgname,t.tgfoid,t.tgtype,t.tgenabled::pg_catalog.text,t.tgisinternal,
            t.tgconstraint,t.tgdeferrable,t.tginitdeferred,t.tgnargs,
            CASE WHEN pg_catalog.octet_length(t.tgargs) OPERATOR(pg_catalog.<=) 131092 THEN pg_catalog.encode(t.tgargs,'hex') ELSE NULL END,
            t.tgqual IS NULL,t.tgattr::pg_catalog.text,t.tgoldtable IS NULL,t.tgnewtable IS NULL
            FROM pg_catalog.pg_trigger t WHERE t.tgrelid OPERATOR(pg_catalog.=) %s::pg_catalog.oid
             AND (t.tgfoid OPERATOR(pg_catalog.=) %s::pg_catalog.oid
               OR t.tgname OPERATOR(pg_catalog.=) 'aa_security_data_gate'
               OR t.tgname OPERATOR(pg_catalog.=) 'zz_security_data_advance')
""",(oid,function_oid),prepare=False)
        actual=sorted(cursor.fetchmany(3),key=lambda value:value[0])
        args=(identity.hex()+'\0'+profile.hex()+'\0'+str(oid)+'\0').encode('ascii').hex()
        expected=[(name,function_oid,mask,'A',False,0,False,False,3,args,True,'',True,True)
                  for name,mask in [('aa_security_data_gate',62),('zz_security_data_advance',60)]]
        if actual!=expected:raise ValueError('Original always-on statement writer triggers required')
