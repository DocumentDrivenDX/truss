-- Lock-only original Subject mapping cut; never current permission or a permit.
CREATE FUNCTION truss.acquire_action_subject_cut()
RETURNS pg_catalog.void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
 IF pg_catalog.current_setting('server_version_num') IS DISTINCT FROM '180006'
  OR pg_catalog.current_setting('transaction_isolation') IS DISTINCT FROM 'repeatable read'
  OR pg_catalog.current_setting('transaction_read_only') IS DISTINCT FROM 'off'
  OR pg_catalog.current_setting('role') IS DISTINCT FROM 'none' THEN
  RAISE EXCEPTION 'original Subject RR context required' USING ERRCODE='0A000';
 END IF;
 -- This cut precedes role/policy guards. Snapshot role flags are not authority.
 LOCK TABLE ONLY truss.action_subject_binding IN SHARE MODE NOWAIT;
 PERFORM 1 FROM ONLY truss.action_subject_binding b
  JOIN pg_catalog.pg_roles r ON r.oid=b.role_oid
  WHERE r.rolname=session_user
  FOR SHARE OF b NOWAIT;
 IF NOT FOUND THEN
  RAISE EXCEPTION 'original enrolled Subject required' USING ERRCODE='42501';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_action_subject_cut() FROM PUBLIC;
