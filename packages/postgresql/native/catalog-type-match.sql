-- Private candidate identity classification; not full definition/lifecycle admission.
CREATE FUNCTION truss.runtime_match_record_identity(revision int,document_id text,module_id text,element_id text)
RETURNS TABLE(match_state text,storage_id text,creation_revision text,retirement_revision text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; retained truss.type_def%ROWTYPE; original bytea;
BEGIN
 SELECT * INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' THEN
  RAISE EXCEPTION 'original catalog admission required' USING ERRCODE='55000';
 END IF;
 LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
 original:=truss.runtime_catalog_lineage(revision,'record',document_id,module_id,element_id);
 SELECT t.* INTO retained FROM truss.type_def t
  WHERE t.document_id COLLATE "C"=runtime_match_record_identity.document_id COLLATE "C"
   AND t.module COLLATE "C"=runtime_match_record_identity.module_id COLLATE "C" AND t.element COLLATE "C"=runtime_match_record_identity.element_id COLLATE "C" FOR SHARE;
 IF NOT FOUND THEN
  RETURN QUERY SELECT 'new'::text,NULL::text,NULL::text,NULL::text; RETURN;
 END IF;
 IF retained.definition_source_kind IS DISTINCT FROM 'accepted_document' THEN
  RAISE EXCEPTION 'source kind requires its own admitted original interpreter' USING ERRCODE='0A000';
 END IF;
 IF retained.kind<>'record' OR retained.provisional
   OR retained.lineage_profile COLLATE "C"<>'truss-type-lineage/0.1.0' COLLATE "C"
   OR retained.lineage_bytes IS DISTINCT FROM original
   OR truss.runtime_catalog_lineage(retained.definition_rev,'record',retained.definition_document_id,retained.module,retained.element) IS DISTINCT FROM original THEN
  RAISE EXCEPTION 'retained original lineage correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN QUERY SELECT CASE WHEN retained.retired_rev IS NULL THEN 'active' ELSE 'retired' END,
  retained.type_id::text,retained.since_rev::text,retained.retired_rev::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_match_record_identity(int,text,text,text) FROM PUBLIC;
