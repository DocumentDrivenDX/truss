-- Private owner-local authored key classification, not complete key migration admission.
CREATE FUNCTION truss.runtime_match_key_identity(revision int,owner_id int,key_identity text)
RETURNS TABLE(match_state text,owner_type_id text,key_number text,creation_revision text,retirement_revision text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; owner truss.type_def%ROWTYPE;
 retained truss.key_def%ROWTYPE; source_count bigint;
BEGIN
 SELECT * INTO STRICT op FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' THEN RAISE EXCEPTION 'original catalog admission required' USING ERRCODE='55000'; END IF;
 LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
 SELECT t.* INTO STRICT owner FROM truss.type_def t WHERE t.type_id=owner_id FOR SHARE;
 PERFORM truss.runtime_catalog_lineage(revision,'record',owner.document_id,owner.module,owner.element);
 SELECT count(*) INTO source_count FROM truss.schema_doc d
  CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') r
  CROSS JOIN LATERAL jsonb_array_elements(r.value->'keys') k
  WHERE d.rev=revision AND d.doc_id=owner.document_id AND m.value->>'id'=owner.module
   AND r.value->>'id'=owner.element AND r.value->>'kind'='record' AND k.value->>'id'=key_identity;
 IF source_count<>1 THEN RAISE EXCEPTION 'unique original owner key required' USING ERRCODE='55000'; END IF;
 SELECT k.* INTO retained FROM truss.key_def k WHERE k.type_id=owner_id AND k.key_id COLLATE "C"=key_identity COLLATE "C" FOR SHARE;
 IF NOT FOUND THEN RETURN QUERY SELECT 'new'::text,owner_id::text,NULL::text,NULL::text,NULL::text; RETURN; END IF;
 IF retained.definition_source_kind IS DISTINCT FROM 'accepted_document' THEN
  RAISE EXCEPTION 'source kind requires its own admitted original interpreter' USING ERRCODE='0A000';
 END IF;
 SELECT count(*) INTO source_count FROM truss.schema_doc d
  CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') r
  CROSS JOIN LATERAL jsonb_array_elements(r.value->'keys') k
  WHERE d.rev=retained.definition_rev AND d.ord=retained.definition_doc_ord
   AND d.doc_id=retained.definition_document_id AND d.doc_id=owner.document_id
   AND m.value->>'id'=owner.module AND r.value->>'id'=owner.element AND r.value->>'kind'='record'
   AND k.value->>'id'=retained.key_id;
 IF source_count<>1 THEN RAISE EXCEPTION 'retained original owner key source required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT CASE WHEN retained.retired_rev IS NULL THEN 'active' ELSE 'retired' END,
  retained.type_id::text,retained.key_num::text,retained.since_rev::text,retained.retired_rev::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_match_key_identity(int,int,text) FROM PUBLIC;
