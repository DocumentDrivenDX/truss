-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Separate preparation candidate. No caller inputs, credentials, data snapshot,
-- seal or authority result. Exact privileged owner/caller ACL is installer-owned.
-- Broad native role and module-policy exclusion; not complete helper/DDL closure.
CREATE FUNCTION truss.acquire_preparation_authority_lock()
RETURNS pg_catalog.void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  IF pg_catalog.current_setting('server_version_num') <> '180006'
     OR pg_catalog.current_setting('transaction_isolation') <> 'read committed'
     OR pg_catalog.current_setting('transaction_read_only') <> 'off' THEN
    RAISE EXCEPTION 'fresh writable preparation authority transaction required'
      USING ERRCODE = '0A000';
  END IF;
  -- Original data/source head admission must precede this issuer. No head
  -- acquisition here: it must not wait behind administration blocked by data.
  LOCK TABLE ONLY truss.module_access IN SHARE MODE NOWAIT;
  LOCK TABLE pg_catalog.pg_authid, pg_catalog.pg_auth_members IN SHARE MODE NOWAIT;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_preparation_authority_lock() FROM PUBLIC;
