-- Fixed original-driver staging composition. Provisional effects only: no
-- accepted report/head, PA authority, installation readiness or commit seal.
CREATE FUNCTION truss.runtime_stage_catalog_issued(
 issued_ordinal bigint, definition_bytes bytea, input_bytes bytea,
 candidate_bytes bytea, obligation_bytes bytea, group_bytes bytea,
 documents_bytes bytea, declarations_bytes bytea, origin_bytes bytea)
RETURNS TABLE(writer_xid text, ordinal text, context_hex text, provisional_result_hex text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE
 item bytea; total_bytes bigint:=0; input jsonb; declarations jsonb;
 documents jsonb; origin jsonb; prestate bytea; admitted record;
 doc jsonb; rec jsonb; field jsonb; key jsonb; rel jsonb;
 types jsonb; properties jsonb; candidates jsonb; relationships jsonb:='[]'::jsonb; revision int;
 owner_id int; components int[]; source_ids int[]; target_ids int[];
 result jsonb; original_result bytea; final_generation bigint;
BEGIN
 FOREACH item IN ARRAY ARRAY[definition_bytes,input_bytes,candidate_bytes,
  obligation_bytes,group_bytes,documents_bytes,declarations_bytes,origin_bytes] LOOP
  IF item IS NULL OR octet_length(item) NOT BETWEEN 1 AND 1048576 THEN
   RAISE EXCEPTION 'bounded original catalog input required' USING ERRCODE='22023';
  END IF;
  total_bytes:=total_bytes+octet_length(item);
 END LOOP;
 IF total_bytes>4194304 OR candidate_bytes IS DISTINCT FROM declarations_bytes THEN
  RAISE EXCEPTION 'original declaration plan correspondence required' USING ERRCODE='22023';
 END IF;
 input:=convert_from(input_bytes,'UTF8')::jsonb;
 declarations:=convert_from(declarations_bytes,'UTF8')::jsonb;
 documents:=convert_from(documents_bytes,'UTF8')::jsonb;
 origin:=convert_from(origin_bytes,'UTF8')::jsonb;
 IF input->'binding' IS DISTINCT FROM jsonb_build_object('state','absent')
  OR input->'transforms' IS DISTINCT FROM '[]'::jsonb
  OR jsonb_typeof(declarations) IS DISTINCT FROM 'array'
  OR jsonb_array_length(declarations)>4096
  OR jsonb_typeof(origin) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'selected original catalog staging profile required' USING ERRCODE='0A000';
 END IF;
 -- This producer checks forbidden prior shared admission before taking its
 -- own exclusion. Never pre-acquire EXCLUSIVE and mask that check.
 prestate:=decode(truss.runtime_capture_catalog_prestate(),'hex');
 SELECT a.* INTO STRICT admitted FROM truss.runtime_admit_operation(
  issued_ordinal,'catalog-acceptance',definition_bytes,input_bytes,prestate,
  candidate_bytes,obligation_bytes,group_bytes) a;
 IF NOT EXISTS(SELECT 1 FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.operation_ordinal=issued_ordinal
   AND o.operation_kind='catalog-acceptance' AND o.phase='admitted' AND o.effect_generation=0
   AND o.original_context_bytes=decode(admitted.context_hex,'hex')
   AND o.original_definition_bytes=definition_bytes AND o.original_input_bytes=input_bytes
   AND o.original_prestate_bytes=prestate AND o.admitted_candidate_bytes=candidate_bytes
   AND o.effect_obligation_bytes=obligation_bytes AND o.original_group_custody_bytes=group_bytes) THEN
  RAISE EXCEPTION 'original stored catalog operation correspondence required' USING ERRCODE='55000';
 END IF;
 PERFORM truss.runtime_require_catalog_input(input_bytes);
 PERFORM truss.runtime_require_catalog_document_carrier(documents);
 SELECT s.provisional_revision::int INTO STRICT revision
  FROM truss.runtime_stage_catalog_documents(documents,origin) s;
 SELECT coalesce(jsonb_agg(jsonb_build_object('documentId',r.value->>'documentId',
  'moduleId',r.value->>'moduleId','elementId',r.value->>'elementId')
  ORDER BY d.ord,r.ord),'[]'::jsonb) INTO candidates
  FROM jsonb_array_elements(declarations) WITH ORDINALITY d(value,ord)
  CROSS JOIN LATERAL jsonb_array_elements(d.value->'records') WITH ORDINALITY r(value,ord);
 types:='[]'::jsonb;
 IF jsonb_array_length(candidates)>0 THEN
  SELECT jsonb_agg(to_jsonb(t)) INTO types FROM truss.runtime_stage_new_types(revision,candidates) t;
 END IF;
 candidates:='[]'::jsonb;
 FOR doc IN SELECT value FROM jsonb_array_elements(declarations) LOOP
  IF jsonb_typeof(doc->'records') IS DISTINCT FROM 'array'
   OR jsonb_typeof(doc->'relationships') IS DISTINCT FROM 'array' THEN
   RAISE EXCEPTION 'complete original declaration families required' USING ERRCODE='22023';
  END IF;
  FOR rec IN SELECT value FROM jsonb_array_elements(doc->'records') LOOP
   SELECT (t.value->>'type_id')::int INTO STRICT owner_id FROM jsonb_array_elements(types) t
    WHERE t.value->>'document_id'=rec->>'documentId'
     AND t.value->>'module_id'=rec->>'moduleId' AND t.value->>'element_id'=rec->>'elementId';
   IF jsonb_typeof(rec->'fields') IS DISTINCT FROM 'array'
    OR jsonb_typeof(rec->'keys') IS DISTINCT FROM 'array' THEN
    RAISE EXCEPTION 'complete original Record plan required' USING ERRCODE='22023';
   END IF;
   FOR field IN SELECT value FROM jsonb_array_elements(rec->'fields') LOOP
    candidates:=candidates||jsonb_build_array(jsonb_build_object('ownerTypeId',owner_id::text,
     'fieldModule',field->>'fieldModule','field',field->'declaration','home','json'));
   END LOOP;
  END LOOP;
 END LOOP;
 properties:='[]'::jsonb;
 IF jsonb_array_length(candidates)>0 THEN
  SELECT jsonb_agg(to_jsonb(p)) INTO properties FROM truss.runtime_stage_new_properties(revision,candidates) p;
 END IF;
 candidates:='[]'::jsonb;
 FOR doc IN SELECT value FROM jsonb_array_elements(declarations) LOOP
  FOR rec IN SELECT value FROM jsonb_array_elements(doc->'records') LOOP
   SELECT (t.value->>'type_id')::int INTO STRICT owner_id FROM jsonb_array_elements(types) t
    WHERE t.value->>'document_id'=rec->>'documentId'
     AND t.value->>'module_id'=rec->>'moduleId' AND t.value->>'element_id'=rec->>'elementId';
   FOR key IN SELECT value FROM jsonb_array_elements(rec->'keys') LOOP
    SELECT array_agg((p.value->>'property_id')::int ORDER BY f.ord) INTO components
     FROM jsonb_array_elements(key->'fields') WITH ORDINALITY f(value,ord)
     JOIN jsonb_array_elements(properties) p ON p.value->>'owner_type_id'=owner_id::text
      AND p.value->>'field_module'=f.value->>'module' AND p.value->>'field_id'=f.value->>'element';
    IF cardinality(components) IS DISTINCT FROM jsonb_array_length(key->'fields') THEN
     RAISE EXCEPTION 'complete original key allocation required' USING ERRCODE='22023';
    END IF;
    candidates:=candidates||jsonb_build_array(jsonb_build_object(
     'ownerTypeId',owner_id::text,'keyId',key->>'id','primary',coalesce(key->'primary','false'::jsonb),
     'propertyIds',(SELECT jsonb_agg(c::text) FROM unnest(components) c)));
   END LOOP;
  END LOOP;
  relationships:=relationships||(doc->'relationships');
 END LOOP;
 IF jsonb_array_length(candidates)>0 THEN
  PERFORM * FROM truss.runtime_stage_new_keys(revision,candidates);
 END IF;
 FOR rel IN SELECT value FROM jsonb_array_elements(relationships)
  ORDER BY (value->>'documentId') COLLATE "C",(value->>'moduleId') COLLATE "C",
   (value->'declaration'->>'id') COLLATE "C" LOOP
   SELECT array_agg((t.value->>'type_id')::int ORDER BY f.ord) INTO source_ids
    FROM jsonb_array_elements(rel->'declaration'->'source') WITH ORDINALITY f(value,ord)
    JOIN jsonb_array_elements(types) t ON t.value->>'document_id'=rel->>'documentId'
     AND t.value->>'module_id'=f.value->>'module' AND t.value->>'element_id'=f.value->>'element';
   SELECT array_agg((t.value->>'type_id')::int ORDER BY f.ord) INTO target_ids
    FROM jsonb_array_elements(rel->'declaration'->'target') WITH ORDINALITY f(value,ord)
    JOIN jsonb_array_elements(types) t ON t.value->>'document_id'=rel->>'documentId'
     AND t.value->>'module_id'=f.value->>'module' AND t.value->>'element_id'=f.value->>'element';
   IF cardinality(source_ids) IS DISTINCT FROM jsonb_array_length(rel->'declaration'->'source')
    OR cardinality(target_ids) IS DISTINCT FROM jsonb_array_length(rel->'declaration'->'target') THEN
    RAISE EXCEPTION 'complete original endpoint allocation required' USING ERRCODE='22023';
   END IF;
   PERFORM truss.runtime_stage_new_relationship(revision,rel->>'documentId',rel->>'moduleId',
    rel->'declaration',source_ids,target_ids);
 END LOOP;
 PERFORM truss.runtime_verify_new_catalog_prestate(revision);
 PERFORM truss.edge_limit_verify_current_scope();
 IF EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.since_rev=revision AND p.home IS DISTINCT FROM 'json')
  OR (SELECT count(*) FROM truss.prop_def p WHERE p.since_rev=revision)<>jsonb_array_length(properties) THEN
  RAISE EXCEPTION 'complete original JSON home allocation required' USING ERRCODE='55000';
 END IF;
 SELECT o.effect_generation INTO STRICT final_generation FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
   AND o.operation_ordinal=issued_ordinal AND o.phase='admitted';
 SELECT jsonb_build_object('interfaceVersion','truss-native-provisional-catalog/0.1',
  'revision',revision::text,'writerXid',admitted.writer_xid,'ordinal',admitted.ordinal,
  'effectGeneration',o.effect_generation::text,'accepted',false,
  'inventory',(SELECT coalesce(jsonb_agg(to_jsonb(i) ORDER BY i.family COLLATE "C",i.identity::text COLLATE "C"),'[]'::jsonb)
   FROM truss.runtime_collect_new_catalog_inventory(revision) i),
  'documents',(SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.ord::int),'[]'::jsonb) FROM truss.runtime_collect_report_documents(revision) d),
  'counts',(SELECT to_jsonb(c) FROM truss.runtime_collect_new_catalog_counts(revision) c)) INTO STRICT result
  FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
   AND o.operation_ordinal=issued_ordinal AND o.phase='admitted';
 original_result:=convert_to(result::text,'UTF8');
 IF NOT EXISTS(SELECT 1 FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
   AND o.operation_ordinal=issued_ordinal AND o.phase='admitted'
   AND o.effect_generation=final_generation AND o.operation_kind='catalog-acceptance'
   AND o.original_context_bytes=decode(admitted.context_hex,'hex')
   AND o.original_definition_bytes=definition_bytes AND o.original_input_bytes=input_bytes
   AND o.original_prestate_bytes=prestate AND o.admitted_candidate_bytes=candidate_bytes
   AND o.effect_obligation_bytes=obligation_bytes AND o.original_group_custody_bytes=group_bytes) THEN
  RAISE EXCEPTION 'stale original catalog result cut' USING ERRCODE='55000';
 END IF;
 IF octet_length(original_result)>16384 THEN
  RAISE EXCEPTION 'selected provisional response capacity exceeded' USING ERRCODE='54000';
 END IF;
 RETURN QUERY SELECT admitted.writer_xid,admitted.ordinal,admitted.context_hex,encode(original_result,'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_catalog_issued(bigint,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea) FROM PUBLIC;
