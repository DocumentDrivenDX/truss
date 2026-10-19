-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Candidate metadata-only preparation cut; not authority or complete source custody.
-- Grant only an explicitly installed private ordinary engine executor.
-- Routine/role/ACL/DDL exclusion and fresh RC correspondence remain prerequisites.
CREATE FUNCTION truss.acquire_preparation_catalog_cut()
RETURNS pg_catalog.void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
 IF current_setting('server_version_num') IS DISTINCT FROM '180006'
  OR current_setting('transaction_isolation') IS DISTINCT FROM 'repeatable read'
  OR current_setting('transaction_read_only') IS DISTINCT FROM 'off'
  OR current_setting('role') IS DISTINCT FROM 'none' THEN
  RAISE EXCEPTION 'original PG18 RR read-write preparation required' USING ERRCODE='0A000';
 END IF;
 PERFORM 1 FROM pg_catalog.pg_roles r WHERE r.rolname=session_user
  AND r.rolcanlogin AND NOT r.rolsuper AND NOT r.rolcreaterole AND NOT r.rolcreatedb
  AND NOT r.rolreplication AND NOT r.rolbypassrls
  AND NOT pg_catalog.pg_has_role(r.oid,current_user,'MEMBER');
 IF NOT FOUND THEN RAISE EXCEPTION 'ordinary enrolled preparation executor required' USING ERRCODE='42501';END IF;
 -- These modes exclude metadata/epoch changes, not ordinary object/edge DML.
 -- NOWAIT refuses conflicts rather than waiting or replacing the original cut.
 LOCK TABLE ONLY truss.source_epoch_current IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.source_epoch_registry IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.catalog_runtime_installation IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.runtime_release IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.schema_head IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.schema_rev IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.schema_doc IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.schema_change IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.type_def IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.prop_def IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.key_def IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.rel_def IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.rel_endpoint IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.catalog_registration_request IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.catalog_acceptance_report IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.relationship_lineage IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.runtime_catalog_rebind_transition IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.runtime_catalog_key_backfill IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.installation_archive IN SHARE MODE NOWAIT;
 -- Lock original singleton versions under RR: a newer update refuses rather
 -- than authorizing a stale version. Append-only release/source correspondence
 -- still needs the fresh coordinator; these row locks do not establish it.
 PERFORM 1 FROM truss.source_epoch_current WHERE singleton_id=1 FOR SHARE NOWAIT;
 IF NOT FOUND THEN RAISE EXCEPTION 'original source epoch required' USING ERRCODE='55000';END IF;
 PERFORM 1 FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 IF NOT FOUND THEN RAISE EXCEPTION 'original catalog head required' USING ERRCODE='55000';END IF;
 PERFORM 1 FROM truss.catalog_runtime_installation WHERE singleton FOR SHARE NOWAIT;
 IF NOT FOUND THEN RAISE EXCEPTION 'original installation required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_preparation_catalog_cut() FROM PUBLIC;
