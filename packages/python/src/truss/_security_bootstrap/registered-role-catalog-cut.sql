-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Selected privileged lock issuer. Installer controls ownership and exact caller ACL.
-- No dynamic identifiers, catalog writes, caller inputs or capability reuse state.
CREATE FUNCTION truss.acquire_registered_role_catalog_cut()
RETURNS pg_catalog.void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  LOCK TABLE pg_catalog.pg_authid, pg_catalog.pg_auth_members IN SHARE MODE NOWAIT;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_registered_role_catalog_cut() FROM PUBLIC;
