-- Private owner/Field identity classifier; no value/definition/lifecycle admission.
CREATE FUNCTION truss.runtime_match_property_identity(revision int,owner_id int,field_module text,field_element text)
RETURNS TABLE(match_state text,storage_id text,creation_revision text,retirement_revision text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; owner truss.type_def%ROWTYPE;
 retained truss.prop_def%ROWTYPE; source_count bigint;
BEGIN
 SELECT * INTO STRICT op FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' THEN RAISE EXCEPTION 'original catalog admission required' USING ERRCODE='55000'; END IF;
 LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
 SELECT t.* INTO STRICT owner FROM truss.type_def t WHERE t.type_id=owner_id FOR SHARE;
 PERFORM truss.runtime_catalog_lineage(revision,'record',owner.document_id,owner.module,owner.element);
 SELECT count(*) INTO source_count FROM truss.schema_doc d
  CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') r
  CROSS JOIN LATERAL jsonb_array_elements(r.value->'members') member
  CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') fm
  CROSS JOIN LATERAL jsonb_array_elements(fm.value->'elements') f
  WHERE d.rev=revision AND d.doc_id=owner.document_id AND m.value->>'id'=owner.module
   AND r.value->>'id'=owner.element AND r.value->>'kind'='record'
   AND member.value->>'module'=field_module AND member.value->>'element'=field_element
   AND fm.value->>'id'=field_module AND f.value->>'id'=field_element AND f.value->>'kind'='field';
 IF source_count<>1 THEN RAISE EXCEPTION 'unique original owner Field membership required' USING ERRCODE='55000'; END IF;
 SELECT p.* INTO retained FROM truss.prop_def p WHERE p.type_id=owner_id
  AND p.declaration_module COLLATE "C"=field_module COLLATE "C" AND p.element COLLATE "C"=field_element COLLATE "C" FOR SHARE;
 IF NOT FOUND THEN RETURN QUERY SELECT 'new'::text,NULL::text,NULL::text,NULL::text; RETURN; END IF;
 SELECT count(*) INTO source_count FROM truss.schema_doc d
  CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') f
  WHERE d.rev=retained.definition_rev AND d.ord=retained.definition_doc_ord
   AND d.doc_id=retained.definition_document_id AND d.doc_id=owner.document_id
   AND m.value->>'id'=retained.declaration_module AND f.value->>'id'=retained.element AND f.value->>'kind'='field';
 IF source_count<>1 THEN RAISE EXCEPTION 'retained original Field source correspondence required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT CASE WHEN retained.retired_rev IS NULL THEN 'active' ELSE 'retired' END,
  retained.prop_id::text,retained.since_rev::text,retained.retired_rev::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_match_property_identity(int,int,text,text) FROM PUBLIC;
