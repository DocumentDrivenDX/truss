-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Fixed selected read-source table cut. Installer grants only the private executor.
CREATE FUNCTION truss.acquire_catalog_read_table_cut()
RETURNS pg_catalog.void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
  LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.catalog_subject_map IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.installation_archive IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.source_epoch_current IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.source_epoch_registry IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.policy_generation_guard IN SHARE MODE NOWAIT;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_catalog_read_table_cut() FROM PUBLIC;
