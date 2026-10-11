-- Draft private capture; compose and qualify before installation.
CREATE FUNCTION truss.runtime_capture_catalog_prerequisite_custody_candidate(
 w text,o text,g text,registration_identity text,original_registration bytea,
 lifecycle_policy bytea,index_policy bytea)
RETURNS TABLE(writer_xid text,operation_ordinal text,effect_generation text,
 revision text,report_utf8_hex text,custody_record_hex text,scope text,
 accepted_report_qualified boolean,feed_qualified boolean)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET DateStyle='ISO, YMD'
SET IntervalStyle='iso_8601' SET extra_float_digits=3 SET bytea_output='hex'
SET standard_conforming_strings=on SET quote_all_identifiers=off AS $$
DECLARE op truss.row_home_operation%ROWTYPE; planned_op truss.row_home_operation%ROWTYPE;
 configuration truss.operation_configuration%ROWTYPE;
 revision_row truss.schema_rev%ROWTYPE; planned_report truss.catalog_acceptance_report%ROWTYPE;
 planned truss.catalog_revision_custody%ROWTYPE; returned truss.catalog_revision_custody%ROWTYPE;
 before_state jsonb; report_state jsonb; after_state jsonb; expected_state jsonb;
 produced record; profile bytea; profile_json jsonb; payload_profile bytea;
 original_documents bytea[]; document_record bytea; documents jsonb:='[]';
 original_configuration bytea; original_op bytea; original_revision bytea;
 original_bytes bigint; total_chunks bigint; context jsonb; clock_value timestamptz;
BEGIN
 PERFORM truss.runtime_require_catalog_prerequisite_composition_candidate(w,o,g);
 SELECT * INTO STRICT op FROM truss.row_home_operation t
  WHERE t.original_writer_xid=pg_current_xact_id_if_assigned() AND t.operation_ordinal::text=o FOR UPDATE;
 SELECT * INTO STRICT configuration FROM truss.operation_configuration t
  WHERE t.original_writer_xid=op.original_writer_xid AND t.operation_ordinal=op.operation_ordinal;
 context:=convert_from(op.original_context_bytes,'UTF8')::jsonb;
 IF EXISTS(SELECT 1 FROM truss.catalog_revision_custody) THEN
  RAISE EXCEPTION 'single original custody capture only' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT produced FROM truss.runtime_collect_custody_catalog_graph_candidate();
 before_state:=truss.runtime_capture_configured_completion_state_candidate(w,o,g);
 original_configuration:=record_send(configuration);
 -- Closure admission selects these originals from retained installation inventory.
 SELECT a.artifact_bytes INTO STRICT profile FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
   AND a.artifact_identity='packages/python/src/truss/_profiles/catalog-prerequisite-custody-capture-candidate.json';
 profile_json:=convert_from(profile,'UTF8')::jsonb;
 SELECT a.artifact_bytes INTO STRICT payload_profile FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
   AND a.artifact_identity=profile_json->'payloadProfile'->>'path';
 SELECT * INTO STRICT produced FROM truss.runtime_write_custody_catalog_report_candidate(
  w,o,g,registration_identity,original_registration,lifecycle_policy,index_policy);
 IF produced.writer_xid IS DISTINCT FROM w OR produced.operation_ordinal IS DISTINCT FROM o
  OR produced.effect_generation IS DISTINCT FROM (op.effect_generation+1)::text
  OR produced.scope IS DISTINCT FROM 'administrative_rollback_only_report_write'
  OR produced.accepted_report_qualified IS DISTINCT FROM false
  OR produced.report_utf8_hex IS NULL OR produced.revision_payload_utf8_hex IS NULL THEN
  RAISE EXCEPTION 'original report producer result required' USING ERRCODE='55000'; END IF;
 planned:=NULL;planned.original_writer_xid:=op.original_writer_xid;
 planned.operation_ordinal:=op.operation_ordinal;
 planned.capture_generation:=op.effect_generation+1;
 planned.original_revision:=(convert_from(decode(produced.revision_payload_utf8_hex,'hex'),'UTF8')::jsonb->>'revision')::int;
 planned_report.rev:=planned.original_revision;
 planned_report.report_bytes:=decode(produced.report_utf8_hex,'hex');
 planned_op:=op;planned_op.effect_generation:=planned.capture_generation;
 report_state:=truss.runtime_capture_configured_completion_state_candidate(w,o,produced.effect_generation);
 expected_state:=jsonb_set(before_state,'{stores,catalog_acceptance_report}',jsonb_build_array(encode(record_send(planned_report),'hex')));
 expected_state:=jsonb_set(expected_state,'{stores,row_home_operation}',jsonb_build_array(encode(record_send(planned_op),'hex')));
 IF report_state IS DISTINCT FROM expected_state THEN
  RAISE EXCEPTION 'complete original report delta required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT op FROM truss.row_home_operation t
  WHERE t.original_writer_xid=planned.original_writer_xid AND t.operation_ordinal=planned.operation_ordinal;
 SELECT * INTO STRICT revision_row FROM truss.schema_rev r WHERE r.rev=planned.original_revision;
 original_op:=record_send(op);original_revision:=record_send(revision_row);
 SELECT array_agg(record_send(d) ORDER BY d.ord) INTO original_documents FROM truss.schema_doc d WHERE d.rev=planned.original_revision;
 IF original_documents IS NULL OR cardinality(original_documents) NOT BETWEEN 1 AND 512 THEN
  RAISE EXCEPTION 'complete original document custody required' USING ERRCODE='55000'; END IF;
 original_bytes:=octet_length(original_configuration)::bigint+octet_length(original_op)::bigint+
  octet_length(op.original_context_bytes)::bigint+octet_length(original_revision)::bigint;
 total_chunks:=((octet_length(original_configuration)+32767)/32768)+((octet_length(original_op)+32767)/32768)+
  ((octet_length(op.original_context_bytes)+32767)/32768)+((octet_length(original_revision)+32767)/32768);
 FOREACH document_record IN ARRAY original_documents LOOP
  IF document_record IS NULL THEN RAISE EXCEPTION 'original document bytes required' USING ERRCODE='55000'; END IF;
  original_bytes:=original_bytes+octet_length(document_record)::bigint;
  total_chunks:=total_chunks+((octet_length(document_record)+32767)/32768);
 END LOOP;
 IF original_bytes>786432 OR total_chunks>1024 THEN
  RAISE EXCEPTION 'original custody codec capacity' USING ERRCODE='54000'; END IF;
 FOREACH document_record IN ARRAY original_documents LOOP
  documents:=documents||jsonb_build_array(truss.runtime_registration_original_hex_chunks(document_record));
 END LOOP;
 planned.original_owner_context_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(jsonb_build_object(
  'scope','administrative_single_original_operation_fresh_catalog_rollback_only',
  'originalConfigurationRecordHexChunks',truss.runtime_registration_original_hex_chunks(original_configuration),
  'originalOperationRecordHexChunks',truss.runtime_registration_original_hex_chunks(original_op),
  'originalContextHexChunks',truss.runtime_registration_original_hex_chunks(op.original_context_bytes),
  'originalRevisionRecordHexChunks',truss.runtime_registration_original_hex_chunks(original_revision),
  'originalDocumentRecordHexChunks',documents)));
 planned.original_producer_profile_bytes:=profile;
 planned.original_fact_key_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(
  jsonb_build_object('kind','revision','revision',planned.original_revision::text)));
 planned.original_fact_key_profile_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(profile_json->'keyProfile'));
 planned.original_payload_bytes:=decode(produced.revision_payload_utf8_hex,'hex');
 planned.original_payload_profile_bytes:=payload_profile;
 clock_value:=clock_timestamp();
 IF NOT isfinite(clock_value) OR extract(year FROM clock_value AT TIME ZONE 'UTC') NOT BETWEEN 1 AND 9999 THEN
  RAISE EXCEPTION 'finite original custody clock required' USING ERRCODE='55000'; END IF;
 planned.original_write_at:=clock_value;
 planned.original_fact_clock_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(jsonb_build_object(
  'profile',profile_json->'clockProfile','originalWriteAt',to_char(clock_value AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))));
 INSERT INTO truss.catalog_revision_custody SELECT (planned).* RETURNING * INTO STRICT returned;
 IF record_send(returned) IS DISTINCT FROM record_send(planned)
  OR (SELECT count(*) FROM truss.catalog_revision_custody)<>1
  OR NOT EXISTS(SELECT 1 FROM truss.catalog_revision_custody t WHERE record_send(t)=record_send(planned)) THEN
  RAISE EXCEPTION 'complete original custody insertion/readback required' USING ERRCODE='55000'; END IF;
 PERFORM truss.runtime_require_catalog_prerequisite_composition_candidate(w,o,produced.effect_generation);
 after_state:=truss.runtime_capture_configured_completion_state_candidate(w,o,produced.effect_generation);
 expected_state:=jsonb_set(report_state,'{stores,catalog_revision_custody}',jsonb_build_array(encode(record_send(planned),'hex')));
 IF after_state IS DISTINCT FROM expected_state THEN
  RAISE EXCEPTION 'complete independent custody poststate required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT w,o,produced.effect_generation,planned.original_revision::text,produced.report_utf8_hex,
  encode(record_send(planned),'hex'),'administrative_rollback_only_catalog_custody'::text,false,false;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_capture_catalog_prerequisite_custody_candidate(text,text,text,text,bytea,bytea,bytea) FROM PUBLIC;
