CREATE FUNCTION truss.runtime_register_current_union_catalog_and_head_candidate(w text, o text, g text) RETURNS TABLE (writer_xid text, operation_ordinal text, effect_generation text, revision text, report_utf8_hex text, scope text, accepted_report_qualified boolean, feed_qualified boolean) LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp SET timezone TO "UTC" SET datestyle TO "ISO, YMD" SET intervalstyle TO iso_8601 SET extra_float_digits TO 3 SET bytea_output TO hex SET standard_conforming_strings TO ON SET quote_all_identifiers TO OFF AS $$
DECLARE produced record; before_state jsonb; after_state jsonb; expected_state jsonb;
 op truss.row_home_operation%ROWTYPE; planned_op truss.row_home_operation%ROWTYPE;
 old_head truss.schema_head%ROWTYPE; planned_head truss.schema_head%ROWTYPE; returned_head truss.schema_head%ROWTYPE;
 custody truss.catalog_revision_custody%ROWTYPE; original_custody bytea;
 rev int; input jsonb; configuration truss.operation_configuration%ROWTYPE; original_configuration bytea;
 finalized_feed jsonb; finalization record; table_name text; actual_rows jsonb;
BEGIN
 SELECT * INTO STRICT produced FROM truss.runtime_register_current_union_catalog_prerequisites_candidate(w,o,g);
 IF produced.writer_xid IS DISTINCT FROM w OR produced.operation_ordinal IS DISTINCT FROM o
  OR produced.effect_generation IS DISTINCT FROM g OR produced.accepted_report_qualified IS DISTINCT FROM false
  OR produced.feed_qualified IS DISTINCT FROM false THEN
  RAISE EXCEPTION 'original custody prerequisite completion required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT finalization FROM truss.runtime_finalize_current_union_catalog_feed_candidate(w,o,g);
 finalized_feed:='{}'::jsonb;
 FOREACH table_name IN ARRAY ARRAY['feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite'] LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(encode(record_send(t),''hex'') ORDER BY encode(record_send(t),''hex'') COLLATE "C"),''[]''::jsonb) FROM ONLY truss.%I t',table_name) INTO actual_rows;
  finalized_feed:=jsonb_set(finalized_feed,ARRAY[table_name],actual_rows);
 END LOOP;
 IF (SELECT count(*) FROM truss.feed_tx)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t
  WHERE encode(t.manifest_bytes,'hex')=finalization.tree_bytes_hex AND encode(t.manifest_sha256,'hex')=finalization.semantic_sha256_hex
  AND t.finalized_generation::text=finalization.membership_generation) THEN
  RAISE EXCEPTION 'original finalization result required before head' USING ERRCODE='55000'; END IF;
 SELECT t.* INTO STRICT op FROM truss.row_home_operation t WHERE t.original_writer_xid=pg_current_xact_id_if_assigned() AND t.operation_ordinal::text=o;
 SELECT * INTO STRICT custody FROM truss.catalog_revision_custody t WHERE t.original_writer_xid=op.original_writer_xid AND t.operation_ordinal=op.operation_ordinal;
 original_custody:=record_send(custody);rev:=custody.original_revision;
 SELECT * INTO STRICT configuration FROM truss.operation_configuration t WHERE t.original_writer_xid=op.original_writer_xid AND t.operation_ordinal=op.operation_ordinal;
 original_configuration:=record_send(configuration);
 input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 IF input->'binding' IS DISTINCT FROM jsonb_build_object('state','absent') OR input->'transforms' IS DISTINCT FROM '[]'::jsonb
  OR EXISTS(SELECT 1 FROM truss.rel_def WHERE definition_source_kind='operation_binding') THEN
  RAISE EXCEPTION 'unsupported pending binding or promotion completion' USING ERRCODE='0A000'; END IF;
 IF produced.effect_generation IS DISTINCT FROM op.effect_generation::text OR op.effect_generation=9223372036854775807 THEN
  RAISE EXCEPTION 'original bounded head generation required' USING ERRCODE='55000'; END IF;
 before_state:=truss.runtime_capture_current_union_completion_state_candidate(w,o,g);
 FOREACH table_name IN ARRAY ARRAY['feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite'] LOOP
  IF before_state->'stores'->table_name IS DISTINCT FROM finalized_feed->table_name THEN
   RAISE EXCEPTION 'pre-head collector changed original finalized feed' USING ERRCODE='55000'; END IF;
 END LOOP;
 SELECT h.* INTO STRICT old_head FROM truss.schema_head h WHERE h.id=1;
 IF (SELECT count(*) FROM truss.schema_head)<>1 OR old_head.rev IS DISTINCT FROM 0 OR rev<>1 THEN
  RAISE EXCEPTION 'selected fresh original head transition required' USING ERRCODE='55000'; END IF;
 planned_head:=old_head;planned_head.rev:=rev;
 planned_op:=op;planned_op.effect_generation:=op.effect_generation+1;planned_op.phase:='admitted';
 planned_op.readiness_generation:=NULL;planned_op.sealed_generation:=NULL;
 planned_op.application_generation:=NULL;planned_op.application_result_bytes:=NULL;
 UPDATE truss.schema_head h SET rev=planned_head.rev WHERE h.id=old_head.id AND h IS NOT DISTINCT FROM old_head RETURNING h.* INTO STRICT returned_head;
 IF record_send(returned_head) IS DISTINCT FROM record_send(planned_head) THEN
  RAISE EXCEPTION 'complete head RETURNING correspondence required' USING ERRCODE='55000'; END IF;
 PERFORM truss.runtime_require_current_catalog_union_composition_candidate(w,o,planned_op.effect_generation::text);
 after_state:=truss.runtime_capture_current_union_completion_state_candidate(w,o,planned_op.effect_generation::text);
 expected_state:=jsonb_set(before_state,'{stores,schema_head}',jsonb_build_array(encode(record_send(planned_head),'hex')));
 expected_state:=jsonb_set(expected_state,'{stores,row_home_operation}',jsonb_build_array(encode(record_send(planned_op),'hex')));
 FOREACH table_name IN ARRAY ARRAY['feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite'] LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(encode(record_send(t),''hex'') ORDER BY encode(record_send(t),''hex'') COLLATE "C"),''[]''::jsonb) FROM ONLY truss.%I t',table_name) INTO actual_rows;
  IF actual_rows IS DISTINCT FROM finalized_feed->table_name THEN RAISE EXCEPTION 'post-head original finalized feed changed' USING ERRCODE='55000'; END IF;
 END LOOP;
 IF after_state IS DISTINCT FROM expected_state
  OR (SELECT count(*) FROM truss.schema_head)<>1 OR NOT EXISTS(SELECT 1 FROM truss.schema_head t WHERE record_send(t)=record_send(planned_head))
  OR (SELECT count(*) FROM truss.row_home_operation)<>1 OR NOT EXISTS(SELECT 1 FROM truss.row_home_operation t WHERE record_send(t)=record_send(planned_op))
  OR (SELECT count(*) FROM truss.operation_configuration)<>1 OR NOT EXISTS(SELECT 1 FROM truss.operation_configuration t WHERE record_send(t)=original_configuration)
  OR (SELECT count(*) FROM truss.catalog_revision_custody)<>1 OR NOT EXISTS(SELECT 1 FROM truss.catalog_revision_custody t WHERE record_send(t)=original_custody) THEN
  RAISE EXCEPTION 'complete original custody post-head correspondence required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT w,o,planned_op.effect_generation::text,rev::text,produced.report_utf8_hex,
  'administrative_rollback_only_custody_configured_head'::text,false,false;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_register_current_union_catalog_and_head_candidate(text, text, text) FROM public