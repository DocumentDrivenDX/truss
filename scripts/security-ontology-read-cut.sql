-- Fixed original graph/source/role cut; no data export or caller parameters.
CREATE FUNCTION truss.acquire_ontology_read_cut() RETURNS pg_catalog.void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
  LOCK TABLE pg_catalog.pg_authid,pg_catalog.pg_auth_members IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.edge IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.schema_head IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.schema_rev IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.schema_doc IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.catalog_registration_request IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.catalog_acceptance_report IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.type_def IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.prop_def IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.key_def IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.rel_def IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.rel_endpoint IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.relationship_lineage IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.schema_change IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.catalog_runtime_installation IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.runtime_release IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.runtime_catalog_rebind_transition IN SHARE MODE NOWAIT;
  LOCK TABLE ONLY truss.catalog_subject_map IN SHARE MODE NOWAIT;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_ontology_read_cut() FROM PUBLIC;
