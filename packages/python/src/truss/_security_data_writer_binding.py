"""Selected native writer metadata checks, not an issuer or DDL lifetime proof."""
from hashlib import sha256

_BODY_SHA256='8c3c1418af9cd20ee7c85cee8babdc74cc0e16f7391b1c91074994cc9e54c1c1'

def _require_guard_function(cursor,owner_oid,name,result_type,body_sha256):
    cursor.execute("""SELECT p.oid,p.proowner,l.lanname,l.lanpltrusted,
        p.prorettype OPERATOR(pg_catalog.=) %s::pg_catalog.regtype,p.prokind::pg_catalog.text,
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
        WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) %s
          AND p.pronargs OPERATOR(pg_catalog.=) 0 AND pg_catalog.octet_length(p.prosrc) OPERATOR(pg_catalog.<=) 8192""",(result_type,name),prepare=False)
    rows=cursor.fetchmany(2)
    if len(rows)!=1:raise ValueError('Original data writer function required')
    row=rows[0];function_oid=row[0]
    if (row[1:21]!=(owner_oid,'plpgsql',True,True,'f','v',True,False,False,False,'u',0,0,0,'',True,True,True,True,True)
            or type(row[21]) is not str or sha256(row[21].encode('utf8')).hexdigest()!=body_sha256 or row[22] is not True or row[23:]!=(True,True,True)):
        raise ValueError('Original data writer function metadata required')
    return function_oid

def require_data_writer_homes(cursor,owner_oid,identity,profile,home_oids):
    function_oid=_require_guard_function(cursor,owner_oid,'security_data_writer_guard','pg_catalog.trigger',_BODY_SHA256)
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


_ROUTINE_BODY_SHA256='63273fb8fbbf98276d3c3637d92b9537648a6e724209f5b5e5e748f01171fddb'

def require_routine_source_hooks(cursor,owner_oid,hook_owner_oid):
    cursor.execute("SELECT pg_catalog.current_setting('event_triggers')",prepare=False)
    if cursor.fetchmany(2)!=[('on',)]:raise ValueError('Original active native event triggers required')
    function_oid=_require_guard_function(cursor,owner_oid,'security_routine_ddl_guard','pg_catalog.event_trigger',_ROUTINE_BODY_SHA256)
    cursor.execute('SELECT rolsuper FROM pg_catalog.pg_roles WHERE oid OPERATOR(pg_catalog.=) %s::pg_catalog.oid',(hook_owner_oid,),prepare=False)
    if cursor.fetchmany(2)!=[(True,)]:raise ValueError('Original native superuser hook owner required')
    cursor.execute("""SELECT e.evtname,e.evtevent::pg_catalog.text,e.evtowner,e.evtfoid,e.evtenabled::pg_catalog.text,
        pg_catalog.array_ndims(e.evttags) OPERATOR(pg_catalog.=) 1
        AND pg_catalog.array_lower(e.evttags,1) OPERATOR(pg_catalog.=) 1
        AND pg_catalog.cardinality(e.evttags) OPERATOR(pg_catalog.=) 3
        AND e.evttags OPERATOR(pg_catalog.@>) ARRAY['CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION']::pg_catalog.text[]
        FROM pg_catalog.pg_event_trigger e WHERE e.evtfoid OPERATOR(pg_catalog.=) %s::pg_catalog.oid
          OR e.evtname OPERATOR(pg_catalog.=) 'truss_security_routine_ddl_start'
          OR e.evtname OPERATOR(pg_catalog.=) 'truss_security_routine_ddl_end'""",(function_oid,),prepare=False)
    actual=sorted(cursor.fetchmany(3),key=lambda row:row[0])
    expected=[(name,event,hook_owner_oid,function_oid,'A',True) for name,event in
              [('truss_security_routine_ddl_end','ddl_command_end'),('truss_security_routine_ddl_start','ddl_command_start')]]
    if actual!=expected:raise ValueError('Original always-on routine source hooks required')
