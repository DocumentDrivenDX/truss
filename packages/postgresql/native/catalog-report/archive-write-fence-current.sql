-- Private exact installed fence comparison; verifier/source authority is separate.
CREATE FUNCTION truss.runtime_require_selected_archive_write_fence() RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE archive_oid oid; archive_owner oid; routine_oid oid; routine record;
BEGIN
 SELECT c.oid,c.relowner INTO STRICT archive_oid,archive_owner FROM pg_catalog.pg_class c
 JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='truss' AND c.relname='installation_archive' AND c.relkind='r';
 IF (SELECT count(*) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='truss' AND p.proname='runtime_fence_selected_archive_writes')<>1
  OR NOT EXISTS(SELECT 1 FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
    WHERE n.nspname='truss' AND p.proname='runtime_fence_selected_archive_writes'
      AND octet_length(p.prosrc)=694) THEN
  RAISE EXCEPTION 'original installed archive write fence required' USING ERRCODE='55000';
 END IF;
 SELECT p.*,l.lanname INTO STRICT routine FROM pg_catalog.pg_proc p
 JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
 JOIN pg_catalog.pg_language l ON l.oid=p.prolang
 WHERE n.nspname='truss' AND p.proname='runtime_fence_selected_archive_writes';
 routine_oid:=routine.oid;
 IF routine.pronargs<>0 OR routine.proargtypes<>''::oidvector OR routine.provariadic<>0
  OR routine.proretset OR routine.prorettype<>'pg_catalog.trigger'::regtype
  OR routine.prokind<>'f' OR routine.lanname<>'plpgsql' OR routine.proowner<>archive_owner
  OR routine.prosecdef OR routine.proisstrict OR routine.proleakproof
  OR routine.provolatile<>'v' OR routine.proparallel<>'u' OR routine.prosupport<>0
  OR routine.probin IS NOT NULL OR routine.prosqlbody IS NOT NULL
  OR routine.proallargtypes IS NOT NULL OR routine.proargmodes IS NOT NULL
  OR routine.proargnames IS NOT NULL OR routine.pronargdefaults<>0
  OR routine.proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog, pg_temp']::text[]
  OR sha256(convert_to(routine.prosrc,'UTF8'))<>decode('9880d745800a1eb0e61f341053c04fdad219172815e95bbad20da369f50eefc9','hex')
  OR EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(routine.proacl,
    pg_catalog.acldefault('f',routine.proowner))) a
    WHERE a.privilege_type='EXECUTE' AND a.grantee<>routine.proowner)
  OR (SELECT count(*) FROM pg_catalog.pg_trigger t WHERE t.tgrelid=archive_oid AND NOT t.tgisinternal)<>1
  OR NOT EXISTS(SELECT 1 FROM pg_catalog.pg_trigger t WHERE t.tgrelid=archive_oid
    AND NOT t.tgisinternal AND t.tgname='runtime_selected_archive_write_fence'
    AND t.tgfoid=routine_oid AND t.tgtype=62 AND t.tgenabled='A'
    AND t.tgnargs=0 AND t.tgargs=decode('','hex') AND t.tgattr=''::int2vector
    AND t.tgqual IS NULL AND t.tgoldtable IS NULL AND t.tgnewtable IS NULL
    AND NOT t.tgdeferrable AND NOT t.tginitdeferred AND t.tgconstraint=0) THEN
  RAISE EXCEPTION 'original installed archive write fence required' USING ERRCODE='55000';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_require_selected_archive_write_fence() FROM PUBLIC;
