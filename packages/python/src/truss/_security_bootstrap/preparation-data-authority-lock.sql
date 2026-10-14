-- Lock-only RR component. No permission, owner-union, lease, selection or seal.
-- The privileged installer fixes the original caller and source/ABI/ACL.
CREATE FUNCTION truss.acquire_preparation_data_authority_lock()
RETURNS pg_catalog.void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  IF pg_catalog.current_setting('server_version_num') <> '180006'
     OR pg_catalog.current_setting('transaction_isolation') <> 'repeatable read'
     OR pg_catalog.current_setting('transaction_read_only') <> 'off'
     OR pg_catalog.current_setting('role') <> 'none' THEN
    RAISE EXCEPTION 'original writable RR preparation authority lock required'
      USING ERRCODE = '0A000';
  END IF;
  -- Source/catalog guards precede this level. No source/head acquisition here.
  LOCK TABLE ONLY truss.module_access IN SHARE MODE NOWAIT;
  LOCK TABLE pg_catalog.pg_authid, pg_catalog.pg_auth_members IN SHARE MODE NOWAIT;
  -- An updated/deleted policy visible only in the earlier RR image refuses;
  -- this does not turn native role-table observations into fresh permission.
  IF (SELECT count(*) FROM ONLY truss.module_access) > 256 THEN
    RAISE EXCEPTION 'preparation policy scope bound exceeded' USING ERRCODE='54000';
  END IF;
  PERFORM 1 FROM ONLY truss.module_access
    ORDER BY document_id COLLATE pg_catalog."C",module COLLATE pg_catalog."C"
    FOR SHARE NOWAIT;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_preparation_data_authority_lock() FROM PUBLIC;
