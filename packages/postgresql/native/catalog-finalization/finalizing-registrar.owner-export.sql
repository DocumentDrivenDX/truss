CREATE FUNCTION truss.runtime_register_finalizing_revision_custody_candidate(w text, o text, g text) RETURNS TABLE (writer_xid text, operation_ordinal text, effect_generation text, parent_record_hex text, member_record_hex text, scope text, feed_qualified boolean) LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp SET timezone TO "UTC" SET datestyle TO "ISO, YMD" SET intervalstyle TO iso_8601 SET extra_float_digits TO 3 SET bytea_output TO hex SET standard_conforming_strings TO ON SET quote_all_identifiers TO OFF AS $$
DECLARE op truss.row_home_operation%ROWTYPE; custody truss.catalog_revision_custody%ROWTYPE;
 original_custody bytea; before_state jsonb; after_state jsonb; expected_state jsonb;
 planned_parent truss.feed_tx%ROWTYPE; planned_member truss.feed_member%ROWTYPE;
 returned record; expected_snapshot jsonb; context jsonb; profile jsonb; profile_bytes bytea;
 source_sql jsonb:='{}'; source_name text; identity text; raw bytea;
 payload bytea; payload_profile bytea; key_profile bytea; owner_bytes bytea;
 revision_row truss.schema_rev%ROWTYPE; configuration truss.operation_configuration%ROWTYPE;
 original_report bytea; expected_payload bytea; revision_tree jsonb; origin jsonb; journal_envelope jsonb;
 input jsonb; report_identity text; original_documents bytea[]; document_record bytea;
 documents jsonb:='[]'; original_configuration bytea; original_op bytea; original_revision bytea;
 original_bytes bigint; total_chunks bigint; expected_owner bytea;
 manifest_bytes bytea; clock_bytes bytea; original_write_at timestamptz; revision int;
BEGIN
 PERFORM truss.runtime_require_catalog_finalization_composition_candidate(w,o,g);
 SELECT * INTO STRICT op FROM truss.row_home_operation t WHERE t.original_writer_xid=pg_current_xact_id_if_assigned()
  AND t.operation_ordinal::text=o FOR UPDATE;
 IF (SELECT count(*) FROM truss.catalog_revision_custody t
  WHERE t.original_writer_xid=op.original_writer_xid AND t.operation_ordinal=op.operation_ordinal)<>1 THEN
  RAISE EXCEPTION 'unique original custody for current operation required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT custody FROM truss.catalog_revision_custody t WHERE t.original_writer_xid=op.original_writer_xid
  AND t.operation_ordinal=op.operation_ordinal FOR SHARE NOWAIT;
 IF (SELECT count(*) FROM truss.row_home_operation)<>1 OR (SELECT count(*) FROM truss.catalog_revision_custody)<>1
  OR custody.capture_generation::text IS DISTINCT FROM g OR op.effect_generation::text IS DISTINCT FROM g
  OR (SELECT count(*) FROM truss.schema_head)<>1 OR NOT EXISTS(SELECT 1 FROM truss.schema_head h WHERE h.id=1 AND h.rev=0)
  OR NOT EXISTS(SELECT 1 FROM truss.schema_rev r WHERE r.rev=custody.original_revision)
  OR NOT EXISTS(SELECT 1 FROM truss.catalog_acceptance_report r WHERE r.rev=custody.original_revision) THEN
  RAISE EXCEPTION 'single current original unpublished catalog custody required' USING ERRCODE='55000'; END IF;
 original_custody:=record_send(custody);context:=convert_from(op.original_context_bytes,'UTF8')::jsonb;
 before_state:=truss.runtime_capture_finalizing_completion_state_candidate(w,o,g);
 IF before_state->'stores'->'feed_tx' IS DISTINCT FROM '[]'::jsonb
  OR before_state->'stores'->'feed_member' IS DISTINCT FROM '[]'::jsonb
  OR before_state->'stores'->'feed_prerequisite' IS DISTINCT FROM '[]'::jsonb
  OR before_state->'stores'->'feed_configuration_prerequisite' IS DISTINCT FROM '[]'::jsonb THEN
  RAISE EXCEPTION 'single initial custody registration only' USING ERRCODE='55000'; END IF;
 LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT;
 PERFORM truss.runtime_require_selected_archive_write_fence();
 identity:='packages/python/src/truss/_profiles/catalog-finalizing-custody-registration-candidate.json';
 IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
  AND a.artifact_role='input' AND a.artifact_identity=identity)<>1 THEN
  RAISE EXCEPTION 'unique original custody registration recipe required' USING ERRCODE='55000'; END IF;
 SELECT a.artifact_bytes INTO STRICT profile_bytes FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=identity
  AND a.artifact_sha256=sha256(a.artifact_bytes) AND encode(a.artifact_sha256,'hex')='0706da4b4387b49834d095f2fbdc3dfb3ba4bb4e3ac22e7c0afdb64c7429e73b'
  AND a.artifact_identity_sha256=sha256(convert_to(identity,'UTF8'));
 IF octet_length(profile_bytes)>65536 THEN RAISE EXCEPTION 'recipe capacity' USING ERRCODE='54000'; END IF;
 profile:=convert_from(profile_bytes,'UTF8')::jsonb;
 FOREACH source_name IN ARRAY ARRAY['create','reserve','insert','producer','payload'] LOOP
  IF source_name='producer' THEN identity:=profile->'custodyProducer'->>'path';
  ELSIF source_name='payload' THEN identity:=profile->'payloadProfile'->>'path';
  ELSE identity:=profile->'sources'->source_name->>'path';END IF;
  IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
   AND a.artifact_role='input' AND a.artifact_identity=identity)<>1 THEN
   RAISE EXCEPTION 'unique original selected registration artifact required' USING ERRCODE='55000'; END IF;
  SELECT a.artifact_bytes INTO STRICT raw FROM truss.installation_archive a
   WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=identity
   AND a.artifact_sha256=sha256(a.artifact_bytes) AND a.artifact_identity_sha256=sha256(convert_to(identity,'UTF8'))
   AND encode(a.artifact_sha256,'hex')=CASE source_name WHEN 'producer' THEN profile->'custodyProducer'->>'sha256'
    WHEN 'payload' THEN profile->'payloadProfile'->>'sha256' ELSE profile->'sources'->source_name->>'sha256' END;
  IF source_name='producer' THEN
   IF raw IS DISTINCT FROM custody.original_producer_profile_bytes THEN RAISE EXCEPTION 'original custody producer required' USING ERRCODE='55000'; END IF;
  ELSIF source_name='payload' THEN
   IF raw IS DISTINCT FROM custody.original_payload_profile_bytes THEN RAISE EXCEPTION 'original custody payload profile required' USING ERRCODE='55000'; END IF;
  ELSE
   IF octet_length(raw)>16384 THEN RAISE EXCEPTION 'statement capacity' USING ERRCODE='54000';END IF;
   source_sql:=source_sql||jsonb_build_object(source_name,convert_from(raw,'UTF8'));
  END IF;
 END LOOP;
 revision:=custody.original_revision;payload:=custody.original_payload_bytes;payload_profile:=custody.original_payload_profile_bytes;
 key_profile:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(profile->'keyProfile'));
 IF key_profile IS DISTINCT FROM custody.original_fact_key_profile_bytes
  OR custody.original_fact_key_bytes IS DISTINCT FROM truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(jsonb_build_object('kind','revision','revision',revision::text))) THEN
  RAISE EXCEPTION 'original revision key profile correspondence required' USING ERRCODE='55000'; END IF;
 owner_bytes:=custody.original_owner_context_bytes;
 manifest_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(profile->'manifestProfile'));
 IF octet_length(custody.original_producer_profile_bytes)>65536
  OR octet_length(custody.original_fact_key_bytes)>65536 OR octet_length(custody.original_fact_key_profile_bytes)>65536
  OR octet_length(custody.original_payload_bytes)>4194304 OR octet_length(custody.original_payload_profile_bytes)>65536
  OR octet_length(custody.original_owner_context_bytes)>16777216 OR octet_length(custody.original_fact_clock_bytes)>65536
  OR NOT isfinite(custody.original_write_at)
  OR extract(year FROM custody.original_write_at AT TIME ZONE 'UTC') NOT BETWEEN 1 AND 9999 THEN
  RAISE EXCEPTION 'bounded finite original custody required' USING ERRCODE='54000'; END IF;
 clock_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(jsonb_build_object(
  'profile',profile->'clockProfile','originalWriteAt',to_char(custody.original_write_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))));
 IF clock_bytes IS DISTINCT FROM custody.original_fact_clock_bytes THEN
  RAISE EXCEPTION 'original retained clock profile and timestamp correspondence required' USING ERRCODE='55000'; END IF;
 -- Read-only independent correspondence; the registered bytes remain custody originals.
 SELECT * INTO STRICT revision_row FROM truss.schema_rev r WHERE r.rev=revision;
 SELECT r.report_bytes INTO STRICT original_report FROM truss.catalog_acceptance_report r WHERE r.rev=revision;
 IF (SELECT count(*) FROM truss.catalog_acceptance_report)<>1
  OR NOT isfinite(revision_row.accepted_at)
  OR extract(year FROM revision_row.accepted_at AT TIME ZONE 'UTC') NOT BETWEEN 1 AND 9999
  OR octet_length(original_report)>786432 OR octet_length(op.original_input_bytes)>1048576 THEN
  RAISE EXCEPTION 'bounded finite original report and revision required' USING ERRCODE='55000'; END IF;
 input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 origin:=truss.runtime_catalog_report_original_tree(decode(context->>'assertedOriginUtf8Hex','hex'));
 IF truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(revision_row.origin))
  IS DISTINCT FROM truss.runtime_canonical_tree_bytes(origin) THEN
  RAISE EXCEPTION 'original retained revision origin correspondence required' USING ERRCODE='55000'; END IF;
 journal_envelope:=truss.runtime_catalog_report_native_tree(jsonb_build_object('databaseRole',context->>'actingUser'));
 journal_envelope:=jsonb_set(journal_envelope,'{members}',journal_envelope->'members'||jsonb_build_array(
  jsonb_build_object('keyUtf8Hex','6173736572746564','node',truss.runtime_catalog_report_map_origin_tree(origin))));
 report_identity:='truss.candidate.catalog-report/'||encode(convert_to(context->>'installationId','UTF8'),'hex')
  ||'/'||encode(convert_to(context->>'sourceEpoch','UTF8'),'hex')||'/'||revision::text;
 revision_tree:=truss.runtime_catalog_report_native_tree(jsonb_build_object(
  'interfaceVersion','truss-feed-revision/0.1.0','revision',revision::text,
  'acceptedAt',to_char(revision_row.accepted_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'input',input,'report',jsonb_build_object('identity',report_identity,
   'bytesBase64',replace(encode(original_report,'base64'),chr(10),''),'sha256',encode(sha256(original_report),'hex'))));
 revision_tree:=jsonb_set(revision_tree,'{members}',revision_tree->'members'||jsonb_build_array(
  jsonb_build_object('keyUtf8Hex','6f726967696e','node',journal_envelope)));
 IF octet_length(revision_tree::text)>4194304 THEN RAISE EXCEPTION 'revision comparison tree capacity' USING ERRCODE='54000';END IF;
 expected_payload:=truss.runtime_revision_report_tree_bytes_wide_candidate(revision_tree,original_report);
 IF expected_payload IS DISTINCT FROM custody.original_payload_bytes THEN
  RAISE EXCEPTION 'original retained report and revision payload correspondence required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT configuration FROM truss.operation_configuration t
  WHERE t.original_writer_xid=op.original_writer_xid AND t.operation_ordinal=op.operation_ordinal;
 original_configuration:=record_send(configuration);original_op:=record_send(op);original_revision:=record_send(revision_row);
 SELECT array_agg(record_send(d) ORDER BY d.ord) INTO original_documents FROM truss.schema_doc d WHERE d.rev=revision;
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
 IF original_bytes>786432 OR total_chunks>1024 THEN RAISE EXCEPTION 'original custody codec capacity' USING ERRCODE='54000'; END IF;
 FOREACH document_record IN ARRAY original_documents LOOP
  documents:=documents||jsonb_build_array(truss.runtime_registration_original_hex_chunks(document_record));
 END LOOP;
 expected_owner:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(jsonb_build_object(
  'scope','administrative_single_original_operation_fresh_catalog_rollback_only',
  'originalConfigurationRecordHexChunks',truss.runtime_registration_original_hex_chunks(original_configuration),
  'originalOperationRecordHexChunks',truss.runtime_registration_original_hex_chunks(original_op),
  'originalContextHexChunks',truss.runtime_registration_original_hex_chunks(op.original_context_bytes),
  'originalRevisionRecordHexChunks',truss.runtime_registration_original_hex_chunks(original_revision),
  'originalDocumentRecordHexChunks',documents)));
 IF expected_owner IS DISTINCT FROM custody.original_owner_context_bytes THEN
  RAISE EXCEPTION 'original retained owner record correspondence required' USING ERRCODE='55000'; END IF;
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
 planned_member.fact_kind:='revision';planned_member.original_fact_key_bytes:=custody.original_fact_key_bytes;
 planned_member.original_fact_key_profile_bytes:=key_profile;planned_member.original_payload_bytes:=payload;
 planned_member.original_payload_profile_bytes:=payload_profile;planned_member.original_payload_sha256:=sha256(payload);
 planned_member.original_owner_context_bytes:=owner_bytes;
 -- Preserve the original custody clock; registration never samples a new clock.
 original_write_at:=custody.original_write_at;
 IF NOT isfinite(original_write_at) OR extract(year FROM original_write_at AT TIME ZONE 'UTC') NOT BETWEEN 1 AND 9999 THEN
  RAISE EXCEPTION 'finite native member write clock required' USING ERRCODE='55000'; END IF;
 clock_bytes:=custody.original_fact_clock_bytes;
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
 PERFORM truss.runtime_require_catalog_finalization_composition_candidate(w,o,g);
 after_state:=truss.runtime_capture_finalizing_completion_state_candidate(w,o,g);
 expected_state:=jsonb_set(before_state,'{stores,feed_tx}',jsonb_build_array(encode(record_send(planned_parent),'hex')));
 expected_state:=jsonb_set(expected_state,'{stores,feed_member}',jsonb_build_array(encode(record_send(planned_member),'hex')));
 IF after_state IS DISTINCT FROM expected_state OR NOT EXISTS(SELECT 1 FROM truss.catalog_revision_custody t
  WHERE record_send(t)=original_custody) THEN
  RAISE EXCEPTION 'complete independent original custody registration delta required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT w,o,g,encode(record_send(planned_parent),'hex'),encode(record_send(planned_member),'hex'),
  'administrative_rollback_only_pending_custody_feed'::text,false;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_register_finalizing_revision_custody_candidate(text, text, text) FROM public