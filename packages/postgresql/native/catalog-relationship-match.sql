-- Private authored identity classifier, not full definition/lifecycle validation.
CREATE FUNCTION truss.runtime_match_relationship_identity(revision int,document_id text,module_id text,element_id text)
RETURNS TABLE(match_state text,storage_id text,creation_revision text,retirement_revision text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; retained truss.rel_def%ROWTYPE;
 lineage truss.relationship_lineage%ROWTYPE; original bytea;
BEGIN
 SELECT * INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' THEN
  RAISE EXCEPTION 'original catalog admission required' USING ERRCODE='55000';
 END IF;
 LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
 original:=truss.runtime_catalog_lineage(revision,'authored',document_id,module_id,element_id);
 SELECT r.* INTO retained FROM truss.rel_def r
  WHERE r.document_id COLLATE "C"=runtime_match_relationship_identity.document_id COLLATE "C"
   AND r.module COLLATE "C"=runtime_match_relationship_identity.module_id COLLATE "C"
   AND r.rel_id COLLATE "C"=runtime_match_relationship_identity.element_id COLLATE "C" FOR SHARE;
 IF NOT FOUND THEN RETURN QUERY SELECT 'new'::text,NULL::text,NULL::text,NULL::text; RETURN; END IF;
 SELECT l.* INTO lineage FROM truss.relationship_lineage l WHERE l.rel_type_id=retained.rel_type_id FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'missing original relationship lineage' USING ERRCODE='55000'; END IF;
 IF retained.composition OR lineage.lineage_category COLLATE "C"<>'authored' COLLATE "C"
   OR lineage.identity_profile COLLATE "C"<>'truss-relationship-lineage-bytes/0.1.0' COLLATE "C"
   OR lineage.original_identity_bytes IS DISTINCT FROM original
   OR truss.runtime_catalog_lineage(retained.definition_rev,'authored',retained.definition_document_id,retained.module,retained.rel_id) IS DISTINCT FROM original THEN
  RAISE EXCEPTION 'retained original relationship correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN QUERY SELECT CASE WHEN retained.retired_rev IS NULL THEN 'active' ELSE 'retired' END,
  retained.rel_type_id::text,retained.since_rev::text,retained.retired_rev::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_match_relationship_identity(int,text,text,text) FROM PUBLIC;
