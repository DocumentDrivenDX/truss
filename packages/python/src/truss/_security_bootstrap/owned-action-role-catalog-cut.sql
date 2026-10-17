-- Private action entry points alone call this fixed privileged role cut.
CREATE FUNCTION truss.acquire_owned_action_role_catalog_cut()
RETURNS pg_catalog.void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  LOCK TABLE pg_catalog.pg_authid, pg_catalog.pg_auth_members IN SHARE MODE NOWAIT;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_owned_action_role_catalog_cut() FROM PUBLIC;
