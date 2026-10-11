-- Original byte custody uses bounded consecutive chunks, never a digest substitute.
CREATE FUNCTION truss.runtime_registration_original_hex_chunks(original bytea)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE n int; pos int:=1; chunks jsonb:='[]'::jsonb;
BEGIN
 IF original IS NULL OR octet_length(original) NOT BETWEEN 1 AND 786432 THEN
  RAISE EXCEPTION 'bounded original registration byte custody required' USING ERRCODE='54000'; END IF;
 n:=octet_length(original);
 WHILE pos<=n LOOP
  chunks:=chunks||jsonb_build_array(encode(substring(original FROM pos FOR 32768),'hex'));
  pos:=pos+32768;
 END LOOP;
 RETURN chunks;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_registration_original_hex_chunks(bytea) FROM PUBLIC;

-- Private single-original-operation fresh catalog registration algorithm.
-- No public acceptance, prerequisite closure, finalization or commit authority.
CREATE FUNCTION truss.runtime_write_catalog_report_and_register_revision_candidate(
 expected_writer text,expected_ordinal text,expected_generation text,
 registration_identity text,original_registration bytea,lifecycle_policy bytea,index_policy bytea)
RETURNS TABLE(writer_xid text,operation_ordinal text,effect_generation text,
 report_utf8_hex text,revision_payload_utf8_hex text,parent_record_hex text,
 member_record_hex text,scope text,accepted_report_qualified boolean,feed_qualified boolean)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp
SET bytea_output='hex' AS $$
DECLARE op truss.row_home_operation%ROWTYPE; final_op truss.row_home_operation%ROWTYPE;
 context jsonb; profile_bytes bytea; profile jsonb; identity text;
 source_sql jsonb:='{}'::jsonb; source_name text; source_bytes bytea;
 identities text[]; archive_before jsonb; archive_after jsonb;
 report_result record; before_graph record; resources_before jsonb; resources_after jsonb;
 metadata_before bytea; metadata_after bytea; relation_before jsonb; relation_after jsonb;
 catalog_before jsonb:='{}'::jsonb; catalog_after jsonb:='{}'::jsonb;
 name text; populated boolean; rows_json jsonb; graph_scope jsonb; census_before jsonb; census_after jsonb;
 planned_parent truss.feed_tx%ROWTYPE; planned_member truss.feed_member%ROWTYPE;
 returned record; expected_snapshot jsonb; revision int; revision_row truss.schema_rev%ROWTYPE;
 documents jsonb; original_op_record bytea; original_revision_record bytea; original_document_records bytea[]; original_document_record bytea; aggregate_original_bytes bigint; total_chunks int; owner_bytes bytea; manifest_bytes bytea; key_profile bytea;
 payload_profile bytea; clock_bytes bytea; original_write_at timestamptz;
 payload bytea; report bytea; persisted_report bytea;
BEGIN
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.operation_ordinal::text=expected_ordinal FOR UPDATE;
 IF (SELECT count(*) FROM truss.row_home_operation)<>1 THEN
  RAISE EXCEPTION 'single original fresh catalog operation required' USING ERRCODE='55000'; END IF;
 context:=convert_from(op.original_context_bytes,'UTF8')::jsonb;
 -- Establish complete first-use absence before the report's first effect.
 SELECT * INTO STRICT before_graph FROM truss.runtime_collect_configured_catalog_graph();
 LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT;
 PERFORM truss.runtime_require_selected_archive_write_fence();
 identity:='packages/python/src/truss/_profiles/catalog-revision-registration-candidate.json';
 IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
  AND a.artifact_role='input' AND a.artifact_identity=identity)<>1 THEN
  RAISE EXCEPTION 'unique original revision registration recipe required' USING ERRCODE='55000'; END IF;
 SELECT a.artifact_bytes INTO STRICT profile_bytes FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=identity
   AND a.artifact_sha256=sha256(a.artifact_bytes)
   AND a.artifact_sha256=decode('cc5248ce8db93cf37f48386ebd7a5d1be48fb844369cc36b650c79e38223adaf','hex')
   AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8')) FOR SHARE NOWAIT;
 profile:=convert_from(profile_bytes,'UTF8')::jsonb;identities:=ARRAY[identity];
 FOREACH source_name IN ARRAY ARRAY['create','reserve','insert'] LOOP
  identity:=profile->'sources'->source_name->>'path';
  IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
   AND a.artifact_role='input' AND a.artifact_identity=identity)<>1 THEN
   RAISE EXCEPTION 'unique original registration statement source required' USING ERRCODE='55000'; END IF;
  SELECT a.artifact_bytes INTO STRICT source_bytes FROM truss.installation_archive a
   WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=identity
    AND a.artifact_sha256=sha256(a.artifact_bytes)
    AND encode(a.artifact_sha256,'hex')=profile->'sources'->source_name->>'sha256'
    AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8')) FOR SHARE NOWAIT;
  IF octet_length(source_bytes)>16384 THEN RAISE EXCEPTION 'registration statement capacity' USING ERRCODE='54000'; END IF;
  source_sql:=source_sql||jsonb_build_object(source_name,convert_from(source_bytes,'UTF8'));
  identities:=array_append(identities,identity);
 END LOOP;
 identity:=profile->'payloadProfile'->>'path';
 SELECT a.artifact_bytes INTO STRICT payload_profile FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=identity
   AND a.artifact_sha256=sha256(a.artifact_bytes)
   AND encode(a.artifact_sha256,'hex')=profile->'payloadProfile'->>'sha256';
 identities:=array_append(identities,identity);
 SELECT jsonb_agg(to_jsonb(a) ORDER BY a.archive_row_id) INTO archive_before FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=ANY(identities);
 -- The payload is obtained only by this direct native producer call.
 SELECT * INTO STRICT report_result FROM truss.runtime_write_catalog_report_candidate(
  expected_writer,expected_ordinal,expected_generation,registration_identity,original_registration,lifecycle_policy,index_policy);
 IF report_result.writer_xid IS DISTINCT FROM expected_writer OR report_result.operation_ordinal IS DISTINCT FROM expected_ordinal
  OR report_result.effect_generation IS DISTINCT FROM (op.effect_generation+1)::text OR report_result.scope IS DISTINCT FROM 'administrative_rollback_only_report_write'
  OR report_result.report_utf8_hex IS NULL OR report_result.revision_payload_utf8_hex IS NULL
  OR report_result.accepted_report_qualified IS DISTINCT FROM false THEN
  RAISE EXCEPTION 'original candidate report result required' USING ERRCODE='55000'; END IF;
 payload:=decode(report_result.revision_payload_utf8_hex,'hex');report:=decode(report_result.report_utf8_hex,'hex');
 revision:=(convert_from(payload,'UTF8')::jsonb->>'revision')::int;
 SELECT r.report_bytes INTO STRICT persisted_report FROM truss.catalog_acceptance_report r WHERE r.rev=revision;
 IF persisted_report IS DISTINCT FROM report THEN
  RAISE EXCEPTION 'original returned report persisted byte correspondence required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT before_graph FROM truss.runtime_collect_configured_catalog_graph();
 graph_scope:=before_graph.empty_scope::jsonb->'businessRelations';
 metadata_before:=decode(before_graph.empty_scope::jsonb->>'metadataUtf8Hex','hex');
 resources_before:=truss.runtime_select_catalog_report_resources(expected_writer,expected_ordinal,report_result.effect_generation,
  (SELECT encode(c.admission_profile_bytes,'hex') FROM truss.operation_configuration c WHERE c.original_writer_xid=op.original_writer_xid AND c.operation_ordinal=op.operation_ordinal));
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned();
 SELECT jsonb_agg(to_jsonb(c) ORDER BY c.oid) INTO relation_before FROM pg_class c
  JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss';
 SELECT coalesce(jsonb_agg(to_jsonb(i) ORDER BY i.inhrelid,i.inhseqno),'[]'::jsonb) INTO census_before FROM pg_inherits i
  WHERE i.inhparent IN (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss')
   OR i.inhrelid IN (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss');
 FOREACH name IN ARRAY ARRAY['schema_head','schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint','catalog_acceptance_report'] LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(encode(record_send(t),''hex'') ORDER BY encode(record_send(t),''hex'') COLLATE "C"),''[]''::jsonb) FROM truss.%I t',name) INTO rows_json;
  catalog_before:=jsonb_set(catalog_before,ARRAY[name],rows_json);
 END LOOP;
 revision:=(convert_from(payload,'UTF8')::jsonb->>'revision')::int;
 SELECT r.* INTO STRICT revision_row FROM truss.schema_rev r WHERE r.rev=revision;
 -- Capture required originals once; aggregate accounting precedes any hex expansion.
 original_op_record:=record_send(op);original_revision_record:=record_send(revision_row);
 SELECT array_agg(record_send(d) ORDER BY d.ord) INTO original_document_records FROM truss.schema_doc d WHERE d.rev=revision;
 IF original_op_record IS NULL OR op.original_context_bytes IS NULL OR original_revision_record IS NULL
  OR original_document_records IS NULL OR cardinality(original_document_records) NOT BETWEEN 1 AND 512 THEN
  RAISE EXCEPTION 'complete original owner custody inventory required' USING ERRCODE='55000'; END IF;
 aggregate_original_bytes:=octet_length(original_op_record)::bigint+octet_length(op.original_context_bytes)+octet_length(original_revision_record);
 total_chunks:=((octet_length(original_op_record)+32767)/32768)+((octet_length(op.original_context_bytes)+32767)/32768)+((octet_length(original_revision_record)+32767)/32768);
 FOREACH original_document_record IN ARRAY original_document_records LOOP
  IF original_document_record IS NULL THEN RAISE EXCEPTION 'original document byte custody required' USING ERRCODE='55000'; END IF;
  aggregate_original_bytes:=aggregate_original_bytes+octet_length(original_document_record);
  total_chunks:=total_chunks+((octet_length(original_document_record)+32767)/32768);
 END LOOP;
 IF aggregate_original_bytes>786432 OR total_chunks>1024 THEN
  RAISE EXCEPTION 'aggregate original registration owner capacity' USING ERRCODE='54000'; END IF;
 documents:='[]'::jsonb;
 FOREACH original_document_record IN ARRAY original_document_records LOOP
  documents:=documents||jsonb_build_array(truss.runtime_registration_original_hex_chunks(original_document_record));
 END LOOP;
 owner_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(jsonb_build_object(
  'scope','administrative_single_original_operation_fresh_catalog_rollback_only',
  'originalOperationRecordHexChunks',truss.runtime_registration_original_hex_chunks(original_op_record),
  'originalContextHexChunks',truss.runtime_registration_original_hex_chunks(op.original_context_bytes),
  'originalRevisionRecordHexChunks',truss.runtime_registration_original_hex_chunks(original_revision_record),
  'originalDocumentRecordHexChunks',documents)));
 manifest_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(profile->'manifestProfile'));
 key_profile:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(profile->'keyProfile'));
 planned_parent.source_epoch:=context->>'sourceEpoch';planned_parent.feed_profile:=profile->>'identity';
 planned_parent.original_writer_xid:=op.original_writer_xid;planned_parent.registration_counter:=0;
 planned_parent.prerequisite_registration_counter:=0;planned_parent.configuration_registration_counter:=0;
 planned_parent.membership_generation:=0;planned_parent.original_context_bytes:=op.original_context_bytes;
 planned_parent.manifest_profile_bytes:=manifest_bytes;
 EXECUTE source_sql->>'create' INTO STRICT returned USING planned_parent.source_epoch,planned_parent.feed_profile,op.original_context_bytes,manifest_bytes;
 expected_snapshot:=jsonb_build_object('source_epoch',planned_parent.source_epoch,'feed_profile',planned_parent.feed_profile,
  'original_writer_xid',op.original_writer_xid::text,'registration_counter','0','prerequisite_registration_counter','0',
  'configuration_registration_counter','0','membership_generation','0','finalized_generation',NULL,
  'original_context_bytes_hex',encode(op.original_context_bytes,'hex'),'manifest_profile_bytes_hex',encode(manifest_bytes,'hex'),
  'manifest_bytes_hex',NULL,'manifest_sha256_hex',NULL);
 IF to_jsonb(returned) IS DISTINCT FROM expected_snapshot
  OR (SELECT count(*) FROM truss.feed_tx)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t WHERE record_send(t)=record_send(planned_parent)) THEN
  RAISE EXCEPTION 'original pending parent insert readback required' USING ERRCODE='55000'; END IF;
 planned_parent.registration_counter:=1;planned_parent.membership_generation:=1;
 EXECUTE source_sql->>'reserve' INTO STRICT returned USING planned_parent.source_epoch,planned_parent.feed_profile,0::bigint,0::bigint,op.original_context_bytes,manifest_bytes;
 expected_snapshot:=jsonb_set(jsonb_set(expected_snapshot,'{registration_counter}','"1"'),'{membership_generation}','"1"');
 IF to_jsonb(returned) IS DISTINCT FROM expected_snapshot
  OR (SELECT count(*) FROM truss.feed_tx)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t WHERE record_send(t)=record_send(planned_parent)) THEN
  RAISE EXCEPTION 'original parent reservation readback required' USING ERRCODE='55000'; END IF;
 planned_member.source_epoch:=planned_parent.source_epoch;planned_member.feed_profile:=planned_parent.feed_profile;
 planned_member.original_writer_xid:=op.original_writer_xid;planned_member.registration_address:=1;
 planned_member.fact_kind:='revision';planned_member.original_fact_key_bytes:=truss.runtime_canonical_tree_bytes(
  truss.runtime_catalog_report_native_tree(jsonb_build_object('kind','revision','revision',revision::text)));
 planned_member.original_fact_key_profile_bytes:=key_profile;planned_member.original_payload_bytes:=payload;
 planned_member.original_payload_profile_bytes:=payload_profile;planned_member.original_payload_sha256:=sha256(payload);
 planned_member.original_owner_context_bytes:=owner_bytes;
 -- All source interpretation precedes the one original insertion clock capture.
 original_write_at:=clock_timestamp();
 IF NOT isfinite(original_write_at) OR extract(year FROM original_write_at AT TIME ZONE 'UTC') NOT BETWEEN 1 AND 9999 THEN
  RAISE EXCEPTION 'finite native member write clock required' USING ERRCODE='55000'; END IF;
 clock_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(jsonb_build_object(
  'profile',profile->'clockProfile','originalWriteAt',to_char(original_write_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))));
 planned_member.original_write_at:=original_write_at;planned_member.original_fact_clock_bytes:=clock_bytes;
 EXECUTE source_sql->>'insert' INTO STRICT returned USING planned_parent.source_epoch,planned_parent.feed_profile,1::bigint,1::bigint,
  'revision',planned_member.original_fact_key_bytes,key_profile,payload,payload_profile,sha256(payload),owner_bytes,
  original_write_at,clock_bytes,op.original_context_bytes,manifest_bytes;
 expected_snapshot:=jsonb_build_object('source_epoch',planned_member.source_epoch,'feed_profile',planned_member.feed_profile,
  'original_writer_xid',op.original_writer_xid::text,'registration_address','1','fact_kind','revision',
  'original_fact_key_bytes_hex',encode(planned_member.original_fact_key_bytes,'hex'),'original_fact_key_profile_bytes_hex',encode(key_profile,'hex'),
  'original_payload_bytes_hex',encode(payload,'hex'),'original_payload_profile_bytes_hex',encode(payload_profile,'hex'),
  'original_payload_sha256_hex',encode(sha256(payload),'hex'),'original_owner_context_bytes_hex',encode(owner_bytes,'hex'),
  'original_write_at',original_write_at::text,'original_fact_clock_bytes_hex',encode(clock_bytes,'hex'),'delivery_ordinal',NULL);
 IF to_jsonb(returned) IS DISTINCT FROM expected_snapshot THEN
  RAISE EXCEPTION 'original revision member returned snapshot required' USING ERRCODE='55000'; END IF;
 -- Independent final observations, preserving all original non-feed cuts.
 resources_after:=truss.runtime_select_catalog_report_resources(expected_writer,expected_ordinal,report_result.effect_generation,
  (SELECT encode(c.admission_profile_bytes,'hex') FROM truss.operation_configuration c WHERE c.original_writer_xid=op.original_writer_xid AND c.operation_ordinal=op.operation_ordinal));
 metadata_after:=truss.runtime_capture_catalog_metadata_cut(expected_writer,expected_ordinal,report_result.effect_generation);
 PERFORM truss.runtime_require_selected_archive_write_fence();
 SELECT jsonb_agg(to_jsonb(a) ORDER BY a.archive_row_id) INTO archive_after FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=ANY(identities);
 SELECT jsonb_agg(to_jsonb(c) ORDER BY c.oid) INTO relation_after FROM pg_class c
  JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss';
 SELECT coalesce(jsonb_agg(to_jsonb(i) ORDER BY i.inhrelid,i.inhseqno),'[]'::jsonb) INTO census_after FROM pg_inherits i
  WHERE i.inhparent IN (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss')
   OR i.inhrelid IN (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss');
 FOR name IN SELECT jsonb_array_elements_text(graph_scope) LOOP
  IF name IN ('feed_tx','feed_member') THEN CONTINUE; END IF;
  EXECUTE format('SELECT EXISTS(SELECT 1 FROM truss.%I)',name) INTO populated;
  IF populated THEN RAISE EXCEPTION 'original non-feed graph must remain empty' USING ERRCODE='55000'; END IF;
 END LOOP;
 FOREACH name IN ARRAY ARRAY['schema_head','schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint','catalog_acceptance_report'] LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(encode(record_send(t),''hex'') ORDER BY encode(record_send(t),''hex'') COLLATE "C"),''[]''::jsonb) FROM truss.%I t',name) INTO rows_json;
  catalog_after:=jsonb_set(catalog_after,ARRAY[name],rows_json);
 END LOOP;
 SELECT o.* INTO STRICT final_op FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned();
 IF resources_after IS DISTINCT FROM resources_before OR metadata_after IS DISTINCT FROM metadata_before
  OR archive_after IS DISTINCT FROM archive_before OR relation_after IS DISTINCT FROM relation_before
  OR census_after IS DISTINCT FROM census_before OR catalog_after IS DISTINCT FROM catalog_before
  OR record_send(final_op) IS DISTINCT FROM record_send(op)
  OR (SELECT count(*) FROM truss.row_home_operation)<>1
  OR (SELECT count(*) FROM truss.feed_tx)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t WHERE record_send(t)=record_send(planned_parent))
  OR (SELECT count(*) FROM truss.feed_member)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_member m WHERE record_send(m)=record_send(planned_member))
  OR EXISTS(SELECT 1 FROM truss.feed_prerequisite) OR EXISTS(SELECT 1 FROM truss.feed_configuration_prerequisite) THEN
  RAISE EXCEPTION 'complete original pending revision registration delta required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT expected_writer,expected_ordinal,report_result.effect_generation,report_result.report_utf8_hex,
  report_result.revision_payload_utf8_hex,encode(record_send(planned_parent),'hex'),encode(record_send(planned_member),'hex'),
  'administrative_single_original_operation_fresh_catalog_rollback_only'::text,false,false;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_write_catalog_report_and_register_revision_candidate(text,text,text,text,bytea,bytea,bytea) FROM PUBLIC;
