CREATE FUNCTION truss.capacity_defer_check_original(constraint_oid oid, trigger_oid oid, routine_oid oid, owner_oid oid, routine_bytes bytea) RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE c pg_constraint%ROWTYPE; t pg_trigger%ROWTYPE; p pg_proc%ROWTYPE;
BEGIN
  IF constraint_oid IS NULL OR trigger_oid IS NULL OR routine_oid IS NULL OR owner_oid IS NULL
    OR routine_bytes IS NULL OR octet_length(routine_bytes) NOT BETWEEN 1 AND 1048576 THEN
    RAISE EXCEPTION 'bounded original constraint binding required' USING ERRCODE='22023';
  END IF;
  IF current_setting('session_replication_role')<>'origin' THEN
    RAISE EXCEPTION 'original native trigger execution mode required' USING ERRCODE='55000';
  END IF;
  -- Qualified names can denote more than one constraint. Reject before SET.
  IF (SELECT count(*) FROM pg_constraint n WHERE n.connamespace='truss'::regnamespace
      AND n.conname='capacity_cache_check')<>1 THEN
    RAISE EXCEPTION 'unique original owned constraint name required' USING ERRCODE='55000';
  END IF;
  SELECT n.* INTO STRICT c FROM pg_constraint n WHERE n.oid=constraint_oid;
  IF c.connamespace<>'truss'::regnamespace OR c.conname<>'capacity_cache_check'
    OR c.conrelid<>'truss.capacity_check_memo'::regclass OR c.contype<>'t'
    OR NOT c.condeferrable OR NOT c.condeferred OR NOT c.convalidated OR c.conparentid<>0 THEN
    RAISE EXCEPTION 'original native constraint correspondence required' USING ERRCODE='55000';
  END IF;
  IF (SELECT count(*) FROM pg_trigger n WHERE n.tgconstraint=constraint_oid)<>1 THEN
    RAISE EXCEPTION 'complete original constraint trigger correspondence required' USING ERRCODE='55000';
  END IF;
  SELECT n.* INTO STRICT t FROM pg_trigger n WHERE n.oid=trigger_oid;
  IF t.tgconstraint<>constraint_oid OR t.tgrelid<>c.conrelid OR t.tgname<>c.conname
    OR t.tgfoid<>routine_oid OR t.tgtype<>17 OR t.tgenabled<>'O' OR t.tgisinternal
    OR NOT t.tgdeferrable OR NOT t.tginitdeferred OR t.tgnargs<>0
    OR octet_length(t.tgargs)<>0 OR t.tgqual IS NOT NULL THEN
    RAISE EXCEPTION 'original enabled unconditional trigger required' USING ERRCODE='55000';
  END IF;
  SELECT n.* INTO STRICT p FROM pg_proc n WHERE n.oid=routine_oid;
  IF routine_oid<>'truss.capacity_cache_check_original()'::regprocedure
    OR p.proowner<>owner_oid OR p.prosecdef OR p.provolatile<>'v' OR p.proparallel<>'u'
    OR p.prokind<>'f' OR p.prorettype<>'trigger'::regtype OR p.pronargs<>0
    OR p.prolang<>(SELECT oid FROM pg_language WHERE lanname='plpgsql')
    OR p.proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog, pg_temp']
    OR convert_to(pg_get_functiondef(routine_oid),'UTF8') IS DISTINCT FROM routine_bytes
    OR EXISTS (SELECT 1 FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
      WHERE a.grantee=0 AND a.privilege_type='EXECUTE') THEN
    RAISE EXCEPTION 'original private routine bytes/attributes required' USING ERRCODE='55000';
  END IF;
  -- Complete original dependency/role/profile/DDL exclusion remains external;
  -- supplied OIDs and byte equality cannot authenticate their provenance.
  SET CONSTRAINTS truss.capacity_cache_check DEFERRED;
END;
$$; REVOKE ALL ON FUNCTION truss.capacity_defer_check_original(oid, oid, oid, oid, bytea) FROM public