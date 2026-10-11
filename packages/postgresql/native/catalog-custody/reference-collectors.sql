CREATE FUNCTION truss.runtime_collect_catalog_custody_declarations_candidate() RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp SET timezone TO "UTC" SET datestyle TO "ISO, YMD" SET intervalstyle TO iso_8601 SET extra_float_digits TO 3 SET bytea_output TO hex SET standard_conforming_strings TO ON SET quote_all_identifiers TO OFF AS $$
DECLARE result jsonb; routine record; declaration text; members jsonb:='[]'; total bigint:=0;
BEGIN
 IF current_user IS DISTINCT FROM session_user OR NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=current_user AND rolsuper) THEN
  RAISE EXCEPTION 'administrative original declarations only' USING ERRCODE='42501'; END IF;
 IF (SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss')>1024
  OR EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss'
   AND (p.prokind NOT IN ('f','p') OR octet_length(p.prosrc)>1048576 OR octet_length(coalesce(p.proconfig::text,''))>65536))
  OR (SELECT coalesce(sum(octet_length(p.prosrc)::bigint),0) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss')>4194304 THEN
  RAISE EXCEPTION 'bounded complete original routine declarations required' USING ERRCODE='54000'; END IF;
 FOR routine IN SELECT p.* FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='truss' ORDER BY p.proname COLLATE "C",pg_get_function_identity_arguments(p.oid) COLLATE "C" LOOP
  declaration:=pg_get_functiondef(routine.oid);total:=total+octet_length(declaration)::bigint;
  IF octet_length(declaration)>1048576 OR total>4194304 THEN
   RAISE EXCEPTION 'original native declaration capacity' USING ERRCODE='54000'; END IF;
  members:=members||jsonb_build_array(jsonb_build_object(
   'name',routine.proname,'identityArguments',pg_get_function_identity_arguments(routine.oid),
   'definition',declaration,'owner',pg_get_userbyid(routine.proowner),
   'language',(SELECT lanname FROM pg_language WHERE oid=routine.prolang),
   'kind',routine.prokind,'volatility',routine.provolatile,'securityDefiner',routine.prosecdef,
   'strict',routine.proisstrict,'leakproof',routine.proleakproof,'parallel',routine.proparallel,
   'support',routine.prosupport::regprocedure::text,'configuration',to_jsonb(routine.proconfig),
   'acl',(SELECT coalesce(jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(a.grantor),
    'grantee',CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,
    'privilege',a.privilege_type,'grantable',a.is_grantable) ORDER BY pg_get_userbyid(a.grantor) COLLATE "C",CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END COLLATE "C",a.privilege_type),'[]'::jsonb)
    FROM aclexplode(coalesce(routine.proacl,acldefault('f',routine.proowner))) a)));
  IF octet_length(members::text)>4194304 THEN RAISE EXCEPTION 'complete declaration carrier capacity' USING ERRCODE='54000'; END IF;
 END LOOP;
 RETURN members;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_collect_catalog_custody_declarations_candidate() FROM public; CREATE FUNCTION truss.runtime_collect_catalog_custody_schema_candidate() RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp SET timezone TO "UTC" SET datestyle TO "ISO, YMD" SET intervalstyle TO iso_8601 SET extra_float_digits TO 3 SET bytea_output TO hex SET standard_conforming_strings TO ON SET quote_all_identifiers TO OFF AS $$
DECLARE relation_oid oid; result jsonb;
BEGIN
 IF current_user IS DISTINCT FROM session_user OR NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=current_user AND rolsuper) THEN
  RAISE EXCEPTION 'administrative original custody schema only' USING ERRCODE='42501'; END IF;
 relation_oid:=to_regclass('truss.catalog_revision_custody');
 IF relation_oid IS NULL THEN RAISE EXCEPTION 'original custody home absent' USING ERRCODE='55000'; END IF;
 LOCK TABLE truss.catalog_revision_custody IN SHARE MODE NOWAIT;
 IF (SELECT count(*) FROM pg_attribute WHERE attrelid=relation_oid)>128
  OR (SELECT count(*) FROM pg_constraint WHERE conrelid=relation_oid)>64
  OR (SELECT count(*) FROM pg_index WHERE indrelid=relation_oid)>32
  OR (SELECT count(*) FROM pg_trigger WHERE tgrelid=relation_oid OR tgconstraint IN
   (SELECT oid FROM pg_constraint WHERE conrelid=relation_oid))>64
  OR (SELECT count(*) FROM pg_rewrite WHERE ev_class=relation_oid)>32
  OR (SELECT count(*) FROM pg_policy WHERE polrelid=relation_oid)>32 THEN
  RAISE EXCEPTION 'bounded complete custody schema required' USING ERRCODE='54000'; END IF;
 SELECT jsonb_build_object(
  'relation',jsonb_build_object('kind',c.relkind,'persistence',c.relpersistence,'owner',pg_get_userbyid(c.relowner),
   'accessMethod',(SELECT amname FROM pg_am WHERE oid=c.relam),'options',to_jsonb(c.reloptions),
   'rowSecurity',c.relrowsecurity,'forceRowSecurity',c.relforcerowsecurity,'replicaIdentity',c.relreplident,
   'acl',(SELECT coalesce(jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(a.grantor),
    'grantee',CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,
    'privilege',a.privilege_type,'grantable',a.is_grantable) ORDER BY pg_get_userbyid(a.grantor) COLLATE "C",
     CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END COLLATE "C",a.privilege_type),'[]'::jsonb)
    FROM aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a)),
  'columns',(SELECT jsonb_agg(jsonb_build_object('number',a.attnum,'name',a.attname,'type',format_type(a.atttypid,a.atttypmod),
   'collation',CASE WHEN a.attcollation=0 THEN NULL ELSE a.attcollation::regcollation::text END,
   'notNull',a.attnotnull,'dropped',a.attisdropped,'identity',a.attidentity,'generated',a.attgenerated,
   'storage',a.attstorage,'compression',a.attcompression,'options',to_jsonb(a.attoptions),
   'acl',(SELECT coalesce(jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(acl.grantor),
    'grantee',CASE WHEN acl.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(acl.grantee) END,
    'privilege',acl.privilege_type,'grantable',acl.is_grantable) ORDER BY pg_get_userbyid(acl.grantor) COLLATE "C",
     CASE WHEN acl.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(acl.grantee) END COLLATE "C",acl.privilege_type),'[]'::jsonb)
    FROM aclexplode(CASE WHEN cardinality(a.attacl)>0 THEN a.attacl ELSE NULL::aclitem[] END) acl),
   'hasMissing',a.atthasmissing,'missing',CASE WHEN a.atthasmissing THEN a.attmissingval::text ELSE NULL END,
   'default',(SELECT pg_get_expr(d.adbin,d.adrelid) FROM pg_attrdef d WHERE d.adrelid=a.attrelid AND d.adnum=a.attnum))
   ORDER BY a.attnum) FROM pg_attribute a WHERE a.attrelid=relation_oid AND a.attnum>0),
  'constraints',(SELECT coalesce(jsonb_agg(jsonb_build_object('name',k.conname,'kind',k.contype,
   'definition',pg_get_constraintdef(k.oid),'validated',k.convalidated,'local',k.conislocal,'inherited',k.coninhcount,
   'parent',CASE WHEN k.conparentid=0 THEN NULL ELSE k.conparentid::text END) ORDER BY k.conname COLLATE "C"),'[]'::jsonb)
   FROM pg_constraint k WHERE k.conrelid=relation_oid),
  'indexes',(SELECT coalesce(jsonb_agg(jsonb_build_object('definition',pg_get_indexdef(i.indexrelid),
   'index',to_jsonb(i)-ARRAY['indexrelid','indrelid','indcollation','indclass','indexprs','indpred']::text[],
   'expressions',pg_get_expr(i.indexprs,i.indrelid),'predicate',pg_get_expr(i.indpred,i.indrelid),
   'relation',jsonb_build_object('name',ic.relname,'kind',ic.relkind,'owner',pg_get_userbyid(ic.relowner),
    'persistence',ic.relpersistence,'accessMethod',(SELECT amname FROM pg_am WHERE oid=ic.relam),'options',to_jsonb(ic.reloptions),
    'acl',(SELECT coalesce(jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(acl.grantor),
     'grantee',CASE WHEN acl.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(acl.grantee) END,
     'privilege',acl.privilege_type,'grantable',acl.is_grantable) ORDER BY pg_get_userbyid(acl.grantor) COLLATE "C",
      CASE WHEN acl.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(acl.grantee) END COLLATE "C",acl.privilege_type),'[]'::jsonb)
     FROM aclexplode(coalesce(ic.relacl,acldefault('r',ic.relowner))) acl)))
   ORDER BY ic.relname COLLATE "C"),'[]'::jsonb) FROM pg_index i JOIN pg_class ic ON ic.oid=i.indexrelid WHERE i.indrelid=relation_oid),
  'rules',(SELECT coalesce(jsonb_agg(jsonb_build_object('name',r.rulename,'definition',pg_get_ruledef(r.oid),'enabled',r.ev_enabled) ORDER BY r.rulename COLLATE "C"),'[]'::jsonb) FROM pg_rewrite r WHERE r.ev_class=relation_oid),
  'policies',(SELECT coalesce(jsonb_agg(jsonb_build_object('name',p.polname,'command',p.polcmd,'permissive',p.polpermissive,
   'roles',(SELECT jsonb_agg(CASE WHEN role_oid=0 THEN 'PUBLIC' ELSE pg_get_userbyid(role_oid) END ORDER BY CASE WHEN role_oid=0 THEN 'PUBLIC' ELSE pg_get_userbyid(role_oid) END COLLATE "C") FROM unnest(p.polroles) role_oid),
   'using',pg_get_expr(p.polqual,p.polrelid),'check',pg_get_expr(p.polwithcheck,p.polrelid)) ORDER BY p.polname COLLATE "C"),'[]'::jsonb)
   FROM pg_policy p WHERE p.polrelid=relation_oid),
  'triggers',(SELECT coalesce(jsonb_agg(jsonb_build_object('home',t.tgrelid::regclass::text,
   'name',CASE WHEN t.tgisinternal THEN NULL ELSE t.tgname END,'internal',t.tgisinternal,
   'constraint',(SELECT k.conname FROM pg_constraint k WHERE k.oid=t.tgconstraint),
   'function',t.tgfoid::regprocedure::text,'type',t.tgtype,'enabled',t.tgenabled,'arguments',encode(t.tgargs,'hex'),
   'argumentCount',t.tgnargs,'qualifier',pg_get_expr(t.tgqual,t.tgrelid),
   'deferrable',t.tgdeferrable,'initiallyDeferred',t.tginitdeferred,'attributes',t.tgattr::text,
   'oldTable',t.tgoldtable,'newTable',t.tgnewtable,'hasParent',t.tgparentid<>0)
   ORDER BY t.tgrelid::regclass::text COLLATE "C",t.tgtype,t.tgfoid::regprocedure::text COLLATE "C",(SELECT k.conname FROM pg_constraint k WHERE k.oid=t.tgconstraint) COLLATE "C",t.tgname COLLATE "C"),'[]'::jsonb)
   FROM pg_trigger t WHERE t.tgrelid=relation_oid OR t.tgconstraint IN(SELECT oid FROM pg_constraint WHERE conrelid=relation_oid)),
  'inheritance',(SELECT count(*) FROM pg_inherits WHERE inhparent=relation_oid OR inhrelid=relation_oid))
 INTO STRICT result FROM pg_class c WHERE c.oid=relation_oid;
 IF octet_length(result::text)>1048576 THEN RAISE EXCEPTION 'normalized custody schema capacity' USING ERRCODE='54000'; END IF;
 RETURN result;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_collect_catalog_custody_schema_candidate() FROM public; CREATE FUNCTION truss.runtime_collect_catalog_custody_target_descriptor_candidate() RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp SET timezone TO "UTC" SET datestyle TO "ISO, YMD" SET intervalstyle TO iso_8601 SET extra_float_digits TO 3 SET bytea_output TO hex SET standard_conforming_strings TO ON SET quote_all_identifiers TO OFF AS $$
DECLARE relation_oid oid; result jsonb;
BEGIN
 -- The normalized observation establishes bounded topology and native exclusion.
 PERFORM truss.runtime_collect_catalog_custody_schema_candidate();
 relation_oid:='truss.catalog_revision_custody'::regclass;
 SELECT jsonb_build_object('relation',to_jsonb(c),
  'attributes',(SELECT jsonb_agg(to_jsonb(a) ORDER BY a.attnum) FROM pg_attribute a WHERE a.attrelid=relation_oid),
  'defaults',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.adnum),'[]'::jsonb) FROM pg_attrdef a WHERE a.adrelid=relation_oid),
  'constraints',(SELECT jsonb_agg(to_jsonb(a) ORDER BY a.oid) FROM pg_constraint a WHERE a.conrelid=relation_oid),
  'indexes',(SELECT jsonb_agg(jsonb_build_object('index',to_jsonb(i),'relation',to_jsonb(ic),
   'attributes',(SELECT jsonb_agg(to_jsonb(a) ORDER BY a.attnum) FROM pg_attribute a WHERE a.attrelid=ic.oid),
   'definition',pg_get_indexdef(i.indexrelid)) ORDER BY i.indexrelid) FROM pg_index i JOIN pg_class ic ON ic.oid=i.indexrelid WHERE i.indrelid=relation_oid),
  'rules',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.oid),'[]'::jsonb) FROM pg_rewrite a WHERE a.ev_class=relation_oid),
  'policies',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.oid),'[]'::jsonb) FROM pg_policy a WHERE a.polrelid=relation_oid),
  'triggers',(SELECT jsonb_agg(to_jsonb(a) ORDER BY a.oid) FROM pg_trigger a WHERE a.tgrelid=relation_oid OR a.tgconstraint IN (SELECT oid FROM pg_constraint WHERE conrelid=relation_oid)))
 INTO STRICT result FROM pg_class c WHERE c.oid=relation_oid;

 IF octet_length(result::text)>1048576 THEN RAISE EXCEPTION 'original target descriptor capacity' USING ERRCODE='54000'; END IF;
 RETURN result;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_collect_catalog_custody_target_descriptor_candidate() FROM public