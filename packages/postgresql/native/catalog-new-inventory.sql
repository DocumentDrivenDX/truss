-- Private actual genuinely-new identity inventory. Not complete effects/report authority.
CREATE FUNCTION truss.runtime_collect_new_catalog_inventory(original_revision int)
RETURNS TABLE(family text,identity jsonb)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; item record; matched record; inventory jsonb; original_relationship jsonb; expected_endpoints jsonb; actual_endpoints jsonb;
BEGIN
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o WHERE
  o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' OR original_revision IS NULL OR original_revision<=0 THEN
  RAISE EXCEPTION 'original new catalog inventory admission required' USING ERRCODE='55000';
 END IF;
 LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
 IF EXISTS(SELECT 1 FROM truss.schema_head h WHERE h.rev>=original_revision) THEN
  RAISE EXCEPTION 'unpublished original revision required' USING ERRCODE='55000';
 END IF;
 PERFORM * FROM truss.runtime_collect_report_documents(original_revision);
 IF EXISTS(SELECT 1 FROM truss.type_def t WHERE t.retired_rev=original_revision OR (t.definition_rev=original_revision AND t.since_rev<>original_revision))
  OR EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.retired_rev=original_revision OR (p.definition_rev=original_revision AND p.since_rev<>original_revision))
  OR EXISTS(SELECT 1 FROM truss.key_def k WHERE k.retired_rev=original_revision OR (k.definition_rev=original_revision AND k.since_rev<>original_revision))
  OR EXISTS(SELECT 1 FROM truss.rel_def r WHERE r.retired_rev=original_revision OR (r.definition_rev=original_revision AND r.since_rev<>original_revision)) THEN
  RAISE EXCEPTION 'retained lifecycle requires complete effect collector' USING ERRCODE='0A000';
 END IF;
 FOR item IN SELECT t.* FROM truss.type_def t WHERE t.since_rev=original_revision LOOP
  SELECT * INTO STRICT matched FROM truss.runtime_match_record_identity(original_revision,item.document_id,item.module,item.element);
  IF matched.match_state<>'active' OR matched.storage_id<>item.type_id::text OR matched.creation_revision<>original_revision::text THEN
   RAISE EXCEPTION 'original new Record correspondence' USING ERRCODE='55000';
  END IF;
 END LOOP;
 FOR item IN SELECT p.* FROM truss.prop_def p WHERE p.since_rev=original_revision LOOP
  SELECT * INTO STRICT matched FROM truss.runtime_match_property_identity(original_revision,item.type_id,item.declaration_module,item.element);
  IF matched.match_state<>'active' OR matched.storage_id<>item.prop_id::text OR matched.creation_revision<>original_revision::text THEN
   RAISE EXCEPTION 'original new Field correspondence' USING ERRCODE='55000';
  END IF;
 END LOOP;
 FOR item IN SELECT k.* FROM truss.key_def k WHERE k.since_rev=original_revision LOOP
  SELECT * INTO STRICT matched FROM truss.runtime_match_key_identity(original_revision,item.type_id,item.key_id);
  IF matched.match_state<>'active' OR matched.owner_type_id<>item.type_id::text OR matched.key_number<>item.key_num::text OR matched.creation_revision<>original_revision::text THEN
   RAISE EXCEPTION 'original new Key correspondence' USING ERRCODE='55000';
  END IF;
 END LOOP;
 FOR item IN SELECT r.* FROM truss.rel_def r WHERE r.since_rev=original_revision LOOP
  SELECT * INTO STRICT matched FROM truss.runtime_match_relationship_identity(original_revision,item.document_id,item.module,item.rel_id);
  IF matched.match_state<>'active' OR matched.storage_id<>item.rel_type_id::text OR matched.creation_revision<>original_revision::text THEN
   RAISE EXCEPTION 'original new relationship correspondence' USING ERRCODE='55000';
  END IF;
  SELECT r.value INTO STRICT original_relationship FROM truss.schema_doc d
   CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m
   CROSS JOIN LATERAL jsonb_array_elements(m.value->'relationships') r
   WHERE d.rev=original_revision AND d.doc_id=item.document_id AND m.value->>'id'=item.module AND r.value->>'id'=item.rel_id;
  SELECT coalesce(jsonb_agg(jsonb_build_array(source.type_id::text,target.type_id::text) ORDER BY source.type_id,target.type_id),'[]'::jsonb)
   INTO expected_endpoints FROM jsonb_array_elements(original_relationship->'source') s
   CROSS JOIN jsonb_array_elements(original_relationship->'target') t
   JOIN truss.type_def source ON source.document_id=item.document_id AND source.module=s.value->>'module' AND source.element=s.value->>'element'
   JOIN truss.type_def target ON target.document_id=item.document_id AND target.module=t.value->>'module' AND target.element=t.value->>'element';
  IF jsonb_array_length(expected_endpoints)<>jsonb_array_length(original_relationship->'source')*jsonb_array_length(original_relationship->'target') THEN
   RAISE EXCEPTION 'complete original endpoint resolution required' USING ERRCODE='55000';
  END IF;
  SELECT coalesce(jsonb_agg(jsonb_build_array(e.source_type::text,e.target_type::text) ORDER BY e.source_type,e.target_type),'[]'::jsonb)
   INTO actual_endpoints FROM truss.rel_endpoint e WHERE e.rel_type_id=item.rel_type_id;
  IF expected_endpoints<>actual_endpoints THEN
   RAISE EXCEPTION 'actual endpoint tuples differ from original authored endpoints' USING ERRCODE='55000';
  END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(jsonb_build_object('family',q.family,'identity',q.identity) ORDER BY q.family COLLATE "C",q.identity::text COLLATE "C"),'[]'::jsonb)
 INTO inventory FROM (
  SELECT 'type'::text AS family,jsonb_build_array(t.type_id::text,t.document_id,t.module,t.element) AS identity FROM truss.type_def t WHERE t.since_rev=original_revision
  UNION ALL SELECT 'property',jsonb_build_array(p.prop_id::text,p.type_id::text,p.declaration_module,p.element) FROM truss.prop_def p WHERE p.since_rev=original_revision
  UNION ALL SELECT 'key',jsonb_build_array(k.type_id::text,k.key_id,k.key_num::text) FROM truss.key_def k WHERE k.since_rev=original_revision
  UNION ALL SELECT 'relationship',jsonb_build_array(r.rel_type_id::text,r.document_id,r.module,r.rel_id) FROM truss.rel_def r WHERE r.since_rev=original_revision
  UNION ALL SELECT 'endpoint',jsonb_build_array(e.rel_type_id::text,e.source_type::text,e.target_type::text) FROM truss.rel_endpoint e JOIN truss.rel_def r ON r.rel_type_id=e.rel_type_id WHERE r.since_rev=original_revision
 ) q;
 IF jsonb_array_length(inventory)>16384 OR octet_length(inventory::text)>1048576 THEN
  RAISE EXCEPTION 'new catalog inventory component capacity exceeded' USING ERRCODE='54000';
 END IF;
 RETURN QUERY SELECT value->>'family',value->'identity' FROM jsonb_array_elements(inventory);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_new_catalog_inventory(int) FROM PUBLIC;
