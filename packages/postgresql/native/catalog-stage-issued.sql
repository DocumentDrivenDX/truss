-- Fixed original-driver staging composition. Provisional effects only: no
-- accepted report/head, PA authority, installation readiness or commit seal.
CREATE FUNCTION truss.runtime_stage_catalog_admitted(
 issued_ordinal bigint, definition_bytes bytea, input_bytes bytea,
 candidate_bytes bytea, obligation_bytes bytea, group_bytes bytea,
 documents_bytes bytea, declarations_bytes bytea, origin_bytes bytea,
 original_prestate bytea, original_context bytea)
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
 original_graph record; final_graph record;
 lifecycle jsonb; index_declarations jsonb;
 lifecycle_policy bytea:=decode('7b0a2020226964656e74697479223a202274727573732d66726573682d636174616c6f672d6c6966656379636c65222c0a20202276657273696f6e223a2022302e312e30222c0a20202273656c656374696f6e223a202266697273745f7265766973696f6e5f6e65775f6964656e7469746965735f6f6e6c79222c0a202022736f75726365436f6d706f6e656e7456657273696f6e223a2022302e3135222c0a2020227461726765745265706f7274496e7465726661636556657273696f6e223a202274727573732d616363657074616e63652d7265706f72742f302e332e302d70726f706f73616c222c0a202022676f7665726e696e6752756c6573223a205b0a20202020224144522d303034222c0a2020202022434f4e54524143542d3030332d726561637469766174696f6e2d696e76656e746f7279220a20205d2c0a20202272657175697265644f726967696e616c5374617465223a2022686561645f7a65726f5f656d7074795f7072696f725f636174616c6f675f616e645f686973746f7279222c0a2020226576656e74506c616e223a2022696e736572745f6f6e6c795f636f6d706c6574655f736f757263655f62696a656374696f6e222c0a202022726561637469766174696f6e73223a2022656d7074795f61667465725f6f726967696e616c5f616273656e63655f616e645f6576656e745f766572696669636174696f6e222c0a202022696e7374616c6c656450726f66696c65417574686f72697479223a2066616c73650a7d0a','hex');
 index_policy bytea:=decode('7b0a2020226964656e74697479223a202274727573732d616273656e742d62696e64696e672d696e6465782d6465636c61726174696f6e73222c0a20202276657273696f6e223a2022302e312e30222c0a20202273636f7065223a2022696d6d757461626c655f696e6465785f6a6f625f6465636c61726174696f6e735f6f6e6c79222c0a202022676f7665726e696e6752756c6573223a205b0a20202020224144522d3030322d4432222c0a20202020224144522d3030322d443131222c0a20202020224144522d3030322d443132222c0a2020202022434f4e54524143542d3030332d70656e64696e672d696e6465782d6465636c61726174696f6e73220a20205d2c0a202022736f75726365436f6d706f6e656e74223a207b0a20202020226964656e74697479223a202274727573732d7175616c69666965642d70726f70657274792d6c61796f75742d736f75726365222c0a202020202276657273696f6e223a2022302e3135222c0a2020202022736861323536223a202263633732356466353366306437346531336262353166646132393630336638636166653863306365653233373636373737383536366638316233336635303131220a20207d2c0a20202273656c656374696f6e223a207b0a202020202262696e64696e67223a2022616273656e74222c0a20202020227472616e73666f726d73223a2022656d707479222c0a2020202022696e6772657373223a20226e6174697665222c0a202020202273746f72616765486f6d65223a20226a736f6e220a20207d2c0a202022696e6465784465636c61726174696f6e536f7572636573223a205b0a20202020226578706c696369745f616363657074616e63655f62696e64696e67220a20205d2c0a202022646f63756d656e74457874656e73696f6e416e6451756572794a6f624465636c61726174696f6e73223a20226e6f6e655f696e5f746869735f706f6c696379222c0a202022616273656e7442696e64696e674465636c61726174696f6e73223a2022656d707479222c0a202022626173656c696e65456e666f7263656d656e74496e6465786573223a20226578636c756465645f66726f6d5f636174616c6f675f6a6f6273222c0a202022737461746973746963734465636c61726174696f6e73223a20226f7574736964655f746869735f6669656c64222c0a202022756e6b6e6f776e457874656e73696f6e53656d616e74696373223a202272657461696e65645f616e645f73657061726174656c795f756e7265736f6c766564222c0a202022696e7374616c6c656450726f66696c65417574686f72697479223a2066616c73652c0a20202272656164696e657373417574686f72697479223a2066616c73650a7d0a','hex');
BEGIN
 FOREACH item IN ARRAY ARRAY[definition_bytes,input_bytes,candidate_bytes,
  obligation_bytes,group_bytes,documents_bytes,declarations_bytes,origin_bytes] LOOP
  IF item IS NULL OR octet_length(item) NOT BETWEEN 1 AND 1048576 THEN
   RAISE EXCEPTION 'bounded original catalog input required' USING ERRCODE='22023';
  END IF;
  total_bytes:=total_bytes+octet_length(item);
 END LOOP;
 IF octet_length(input_bytes)>16384 THEN
  RAISE EXCEPTION 'selected report input capacity exceeded' USING ERRCODE='54000';
 END IF;
 IF total_bytes>4194304 THEN
  RAISE EXCEPTION 'original declaration plan correspondence required' USING ERRCODE='22023';
 END IF;
 -- Reuse one actual admitted root; no admission or identity factory in this core.
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none'
  THEN session_user::text ELSE current_setting('role') END) THEN
  RAISE EXCEPTION 'original invoker actor boundary required' USING ERRCODE='55000';
 END IF;
 IF original_prestate IS NULL OR original_context IS NULL
  OR octet_length(original_prestate) NOT BETWEEN 1 AND 1048576
  OR octet_length(original_context) NOT BETWEEN 1 AND 1048576 THEN
  RAISE EXCEPTION 'bounded retained original admission required' USING ERRCODE='22023';
 END IF;
 IF (SELECT count(*) FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
   AND o.phase<>'application_finalized')<>1 THEN
  RAISE EXCEPTION 'sole current unfinished catalog operation required' USING ERRCODE='55000';
 END IF;
 SELECT o.original_writer_xid::text AS writer_xid,o.operation_ordinal::text AS ordinal,
  encode(o.original_context_bytes,'hex') AS context_hex INTO admitted
 FROM truss.row_home_operation o
 WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
  AND o.operation_ordinal=issued_ordinal AND o.operation_kind='catalog-acceptance'
  AND o.phase='admitted' AND o.effect_generation=0
  AND o.original_context_bytes=original_context
  AND o.original_definition_bytes=definition_bytes AND o.original_input_bytes=input_bytes
  AND o.original_prestate_bytes=original_prestate AND o.admitted_candidate_bytes=candidate_bytes
  AND o.effect_obligation_bytes=obligation_bytes AND o.original_group_custody_bytes=group_bytes;
 IF NOT FOUND THEN
  RAISE EXCEPTION 'original stored catalog operation correspondence required' USING ERRCODE='55000';
 END IF;
 prestate:=original_prestate;
 CASE convert_from(original_context,'UTF8')::jsonb->>'interfaceVersion'
 WHEN 'truss-native-operation-context/0.2' THEN
  PERFORM * FROM truss.runtime_collect_catalog_original_context(admitted.writer_xid,admitted.ordinal,'0');
 WHEN 'truss-native-operation-context/0.4' THEN
  PERFORM * FROM truss.runtime_collect_catalog_epoch_context(admitted.writer_xid,admitted.ordinal,'0');
 ELSE
  RAISE EXCEPTION 'supported complete original context grammar required' USING ERRCODE='0A000';
 END CASE;
 IF NOT EXISTS(SELECT 1 FROM truss.schema_head h WHERE h.id=1 AND h.rev=0)
  OR EXISTS(SELECT 1 FROM truss.schema_rev r WHERE r.rev<>0)
  OR convert_from(prestate,'UTF8')::jsonb->>'interfaceVersion'
     IS DISTINCT FROM 'truss-native-catalog-prestate/0.1' THEN
  RAISE EXCEPTION 'original fresh catalog head and prestate required' USING ERRCODE='0A000';
 END IF;
 PERFORM truss.runtime_verify_new_catalog_prestate(1);
 IF candidate_bytes IS DISTINCT FROM declarations_bytes THEN
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
 PERFORM truss.runtime_require_catalog_lifecycle_observers();
 IF convert_from(original_context,'UTF8')::jsonb->>'interfaceVersion'='truss-native-operation-context/0.4' THEN
  SELECT * INTO STRICT original_graph FROM truss.runtime_collect_configured_catalog_graph();
 ELSE
  SELECT * INTO STRICT original_graph FROM truss.runtime_collect_empty_catalog_graph();
 END IF;
 IF original_graph.writer_xid IS DISTINCT FROM admitted.writer_xid
  OR original_graph.operation_ordinal IS DISTINCT FROM admitted.ordinal
  OR original_graph.effect_generation IS DISTINCT FROM '0' THEN
  RAISE EXCEPTION 'original pre-effect graph cut required' USING ERRCODE='55000';
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
 IF truss.runtime_require_empty_provisional_catalog(revision) IS DISTINCT FROM '0' THEN
  RAISE EXCEPTION 'original empty provisional inventory required' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.since_rev=revision AND p.home IS DISTINCT FROM 'json')
  OR (SELECT count(*) FROM truss.prop_def p WHERE p.since_rev=revision)<>jsonb_array_length(properties) THEN
  RAISE EXCEPTION 'complete original JSON home allocation required' USING ERRCODE='55000';
 END IF;
 SELECT o.effect_generation INTO STRICT final_generation FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
   AND o.operation_ordinal=issued_ordinal AND o.phase='admitted';
 SELECT jsonb_build_object('interfaceVersion','truss-native-provisional-catalog/0.2',
  'revision',revision::text,'writerXid',admitted.writer_xid,'ordinal',admitted.ordinal,
  'effectGeneration',o.effect_generation::text,'accepted',false,
  'inventory',(SELECT coalesce(jsonb_agg(to_jsonb(i) ORDER BY i.family COLLATE "C",i.identity::text COLLATE "C"),'[]'::jsonb)
   FROM truss.runtime_collect_new_catalog_inventory(revision) i),
  'documents',(SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.ord::int),'[]'::jsonb) FROM truss.runtime_collect_report_documents(revision) d),
  'counts',(SELECT to_jsonb(c) FROM truss.runtime_collect_new_catalog_counts(revision) c)) INTO STRICT result
  FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
   AND o.operation_ordinal=issued_ordinal AND o.phase='admitted';
 lifecycle:=truss.runtime_collect_fresh_catalog_lifecycle(
  admitted.writer_xid,admitted.ordinal,final_generation::text,revision,lifecycle_policy);
 index_declarations:=truss.runtime_collect_absent_binding_index_declarations(
  admitted.writer_xid,admitted.ordinal,final_generation::text,revision,index_policy);
 IF convert_from(original_context,'UTF8')::jsonb->>'interfaceVersion'='truss-native-operation-context/0.4' THEN
  SELECT * INTO STRICT final_graph FROM truss.runtime_collect_configured_catalog_graph();
  IF final_graph.metadata_source IS DISTINCT FROM original_graph.metadata_source THEN
   RAISE EXCEPTION 'original configured metadata source cut required' USING ERRCODE='55000';
  END IF;
 ELSE
  SELECT * INTO STRICT final_graph FROM truss.runtime_collect_empty_catalog_graph();
 END IF;
 IF final_graph.writer_xid IS DISTINCT FROM original_graph.writer_xid
  OR final_graph.operation_ordinal IS DISTINCT FROM original_graph.operation_ordinal
  OR final_graph.empty_scope IS DISTINCT FROM original_graph.empty_scope
  OR final_graph.effect_generation IS DISTINCT FROM final_generation::text THEN
  RAISE EXCEPTION 'original final graph cut required' USING ERRCODE='55000';
 END IF;
 result:=result||jsonb_build_object('reportSources',jsonb_build_object(
  'start',to_jsonb(original_graph),'end',to_jsonb(final_graph),
  'lifecycle',lifecycle,'indexDeclarations',index_declarations));
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
 IF octet_length(original_result)>131072 THEN
  RAISE EXCEPTION 'selected provisional response capacity exceeded' USING ERRCODE='54000';
 END IF;
 RETURN QUERY SELECT admitted.writer_xid,admitted.ordinal,admitted.context_hex,encode(original_result,'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_catalog_admitted(bigint,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea) FROM PUBLIC;

-- Existing base-context entry retains capture → admission → staging behavior.
CREATE FUNCTION truss.runtime_stage_catalog_issued(
 issued_ordinal bigint, definition_bytes bytea, input_bytes bytea,
 candidate_bytes bytea, obligation_bytes bytea, group_bytes bytea,
 documents_bytes bytea, declarations_bytes bytea, origin_bytes bytea)
RETURNS TABLE(writer_xid text, ordinal text, context_hex text, provisional_result_hex text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE prestate bytea; admitted record; item bytea; total_bytes bigint:=0;
 input jsonb; declarations jsonb; documents jsonb; origin jsonb;
BEGIN
 FOREACH item IN ARRAY ARRAY[definition_bytes,input_bytes,candidate_bytes,
  obligation_bytes,group_bytes,documents_bytes,declarations_bytes,origin_bytes] LOOP
  IF item IS NULL OR octet_length(item) NOT BETWEEN 1 AND 1048576 THEN
   RAISE EXCEPTION 'bounded original catalog input required' USING ERRCODE='22023';
  END IF;
  total_bytes:=total_bytes+octet_length(item);
 END LOOP;
 IF octet_length(input_bytes)>16384 THEN
  RAISE EXCEPTION 'selected report input capacity exceeded' USING ERRCODE='54000';
 END IF;
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
 prestate:=decode(truss.runtime_capture_catalog_prestate(),'hex');
 SELECT a.* INTO STRICT admitted FROM truss.runtime_admit_operation(
  issued_ordinal,'catalog-acceptance',definition_bytes,input_bytes,prestate,
  candidate_bytes,obligation_bytes,group_bytes) a;
 RETURN QUERY SELECT * FROM truss.runtime_stage_catalog_admitted(
  issued_ordinal,definition_bytes,input_bytes,candidate_bytes,obligation_bytes,group_bytes,
  documents_bytes,declarations_bytes,origin_bytes,prestate,decode(admitted.context_hex,'hex'));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_catalog_issued(bigint,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea) FROM PUBLIC;
