-- Explicit private-profile installation step, before any ordinary D cut.
-- Not part of the ordinary public runtime installer. Direct superuser only.
REVOKE EXECUTE ON FUNCTION
 pg_catalog.pg_advisory_lock(int4,int4),
 pg_catalog.pg_advisory_lock_shared(int4,int4),
 pg_catalog.pg_try_advisory_lock(int4,int4),
 pg_catalog.pg_try_advisory_lock_shared(int4,int4),
 pg_catalog.pg_advisory_xact_lock(int4,int4),
 pg_catalog.pg_advisory_xact_lock_shared(int4,int4),
 pg_catalog.pg_try_advisory_xact_lock(int4,int4),
 pg_catalog.pg_try_advisory_xact_lock_shared(int4,int4)
FROM PUBLIC;

CREATE FUNCTION truss.require_preparation_advisory_exclusion()
RETURNS pg_catalog.void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
DECLARE actor pg_catalog.oid; actor_role pg_catalog.pg_roles%ROWTYPE; signature pg_catalog.text; routine pg_catalog.oid; reachable_role record;
BEGIN
 SELECT * INTO STRICT actor_role FROM pg_catalog.pg_roles WHERE rolname=session_user;
 actor:=actor_role.oid;
 IF actor_role.rolsuper OR actor_role.rolcreaterole OR actor_role.rolcreatedb OR actor_role.rolreplication
  OR actor_role.rolbypassrls OR NOT actor_role.rolcanlogin THEN
  RAISE EXCEPTION 'ordinary original advisory-excluded actor required' USING ERRCODE='42501';END IF;
 FOREACH signature IN ARRAY ARRAY[
  'pg_catalog.pg_advisory_lock(int4,int4)','pg_catalog.pg_advisory_lock_shared(int4,int4)',
  'pg_catalog.pg_try_advisory_lock(int4,int4)','pg_catalog.pg_try_advisory_lock_shared(int4,int4)',
  'pg_catalog.pg_advisory_xact_lock(int4,int4)','pg_catalog.pg_advisory_xact_lock_shared(int4,int4)',
  'pg_catalog.pg_try_advisory_xact_lock(int4,int4)','pg_catalog.pg_try_advisory_xact_lock_shared(int4,int4)'] LOOP
  routine:=to_regprocedure(signature);
  IF routine IS NULL THEN
   RAISE EXCEPTION 'exact advisory acquisition primitive required' USING ERRCODE='42501';END IF;
  FOR reachable_role IN SELECT r.oid FROM pg_catalog.pg_roles r
   WHERE r.oid=actor OR pg_has_role(actor,r.oid,'SET') LOOP
   IF has_function_privilege(reachable_role.oid,routine,'EXECUTE') IS DISTINCT FROM false THEN
    RAISE EXCEPTION 'ordinary direct or SET-reachable advisory acquisition refused' USING ERRCODE='42501';END IF;
  END LOOP;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.require_preparation_advisory_exclusion() FROM PUBLIC;
