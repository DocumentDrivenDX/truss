CREATE FUNCTION truss.runtime_write_catalog_report_wide_candidate(expected_writer text, expected_ordinal text, expected_generation text, registration_identity text, original_registration bytea, lifecycle_policy bytea, index_policy bytea) RETURNS TABLE (writer_xid text, operation_ordinal text, effect_generation text, report_utf8_hex text, scope text, accepted_report_qualified boolean, revision_payload_utf8_hex text) LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp SET bytea_output TO hex AS $$
DECLARE op truss.row_home_operation%ROWTYPE; current_op truss.row_home_operation%ROWTYPE;
 revision_row truss.schema_rev%ROWTYPE; revision_tree jsonb; revision_payload bytea; accepted_at_text text; report_identity text;
 context jsonb; input jsonb; registration jsonb; source record; before_graph record; after_graph record;
 revision int; documents jsonb; counts jsonb; lifecycle jsonb; indexes jsonb;
 origin jsonb; execution jsonb; execution_tree jsonb; origin_envelope jsonb; journal_envelope jsonb; fields jsonb; tree jsonb; members jsonb; assertion_tree jsonb;
 assertion_digest text; assertions jsonb; member jsonb; pin_name text; pin jsonb;
 original_report bytea; returned_report bytea; recipe_bytes bytea; recipe jsonb; artifact bytea; selected_artifact_identity text; profile_rows jsonb; final_profile_rows jsonb; identities text[]; catalog_before jsonb; catalog_after jsonb; table_name text; table_rows jsonb; schema_registry jsonb:='{}'::jsonb; schema_name text; schema_value jsonb; report_tree jsonb; before_resources jsonb; after_resources jsonb; original_registration_id bigint; count_rows bigint;
BEGIN
 IF expected_writer IS NULL OR expected_ordinal IS NULL OR expected_generation IS NULL
  OR registration_identity IS NULL OR octet_length(registration_identity) NOT BETWEEN 1 AND 4096
  OR original_registration IS NULL OR octet_length(original_registration) NOT BETWEEN 1 AND 65536 THEN
  RAISE EXCEPTION 'bounded original candidate registration required' USING ERRCODE='22023'; END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.operation_ordinal::text=expected_ordinal
   AND o.phase='admitted' AND o.operation_kind='catalog-acceptance' FOR UPDATE;
 context:=convert_from(op.original_context_bytes,'UTF8')::jsonb;
 IF context->>'interfaceVersion' IS DISTINCT FROM 'truss-native-operation-context/0.4' THEN
  RAISE EXCEPTION 'original configured candidate context required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT before_graph FROM truss.runtime_collect_configured_catalog_graph();
 -- This registration is explicitly candidate-only. It is NOT one of the four
 -- original production authority sources, even when all profile pins match.
 PERFORM truss.runtime_require_unique_source_json(convert_from(original_registration,'UTF8')::json);
 registration:=convert_from(original_registration,'UTF8')::jsonb;
 IF jsonb_typeof(registration) IS DISTINCT FROM 'object'
  OR (SELECT count(*) FROM jsonb_object_keys(registration))<>8
  OR NOT registration ?& ARRAY['interfaceVersion','scope','layoutProfile','reportProfile',
      'captureProfile','originMappingProfile','enforcementProfile','composition']
  OR registration->>'interfaceVersion' IS DISTINCT FROM 'truss-catalog-report-candidate-registration/0.1'
  OR registration->>'scope' IS DISTINCT FROM 'administrative_rollback_only_report_write' THEN
  RAISE EXCEPTION 'explicit administrative candidate registration required' USING ERRCODE='55000'; END IF;
 FOREACH pin_name IN ARRAY ARRAY['layoutProfile','reportProfile','captureProfile','originMappingProfile','enforcementProfile'] LOOP
  pin:=registration->pin_name;
  IF jsonb_typeof(pin) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(pin))<>3
   OR NOT pin ?& ARRAY['identity','version','sha256']
   OR EXISTS(SELECT 1 FROM jsonb_each(pin) e WHERE jsonb_typeof(e.value) IS DISTINCT FROM 'string' OR octet_length(e.value #>> '{}') NOT BETWEEN 1 AND 4096)
   OR pin->>'sha256' !~ '^[0-9a-f]{64}$' THEN
   RAISE EXCEPTION 'complete candidate profile pins required' USING ERRCODE='55000'; END IF;
 END LOOP;
 IF registration->'enforcementProfile' IS DISTINCT FROM jsonb_build_object(
  'identity','truss-catalog-enforcement-projection','version','0.1.0',
  'sha256','678e52ea00fa984b19162441a33b33ab3d822b58f8ae2c69195dc1d5d658c4b1') THEN
  RAISE EXCEPTION 'selected candidate enforcement projection required' USING ERRCODE='55000'; END IF;
 SELECT count(*) INTO count_rows FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
   AND convert_to(a.artifact_identity,'UTF8')=convert_to(registration_identity,'UTF8');
 IF count_rows<>1 THEN RAISE EXCEPTION 'unique original candidate registration archive required' USING ERRCODE='55000'; END IF;
 SELECT a.archive_row_id INTO STRICT original_registration_id FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
   AND convert_to(a.artifact_identity,'UTF8')=convert_to(registration_identity,'UTF8')
   AND a.artifact_bytes=original_registration AND a.artifact_sha256=sha256(original_registration)
   AND a.artifact_identity_sha256=sha256(convert_to(registration_identity,'UTF8')) FOR SHARE NOWAIT;
 IF registration->'composition' IS DISTINCT FROM jsonb_build_object('identity','packages/python/src/truss/_profiles/catalog-report-wide-composition-candidate.json','sha256','d77cf6b399774166da481f0f0e7850271243e8911175b2bb225f9a628d418aba') THEN
  RAISE EXCEPTION 'recognized full candidate composition recipe required' USING ERRCODE='55000'; END IF;
 identities:=ARRAY[registration_identity,'packages/python/src/truss/_profiles/catalog-report-wide-composition-candidate.json'];
 IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
  AND a.artifact_role='input' AND a.artifact_identity='packages/python/src/truss/_profiles/catalog-report-wide-composition-candidate.json')<>1 THEN
  RAISE EXCEPTION 'unique original candidate recipe archive required' USING ERRCODE='55000'; END IF;
 SELECT a.artifact_bytes INTO STRICT recipe_bytes FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity='packages/python/src/truss/_profiles/catalog-report-wide-composition-candidate.json'
   AND a.artifact_sha256=sha256(a.artifact_bytes) AND a.artifact_sha256=decode('d77cf6b399774166da481f0f0e7850271243e8911175b2bb225f9a628d418aba','hex')
   AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8')) FOR SHARE NOWAIT;
 recipe:=convert_from(recipe_bytes,'UTF8')::jsonb;
 FOREACH pin_name IN ARRAY ARRAY['reportProfile','captureProfile','originMappingProfile','enforcementProfile'] LOOP
  selected_artifact_identity:=recipe->'profileArtifacts'->pin_name->>'path';
  identities:=array_append(identities,selected_artifact_identity);
  IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
    AND a.artifact_role='input' AND convert_to(a.artifact_identity,'UTF8')=convert_to(selected_artifact_identity,'UTF8'))<>1 THEN
   RAISE EXCEPTION 'unique full candidate profile archive required' USING ERRCODE='55000'; END IF;
  SELECT a.artifact_bytes INTO STRICT artifact FROM truss.installation_archive a
   WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
    AND convert_to(a.artifact_identity,'UTF8')=convert_to(selected_artifact_identity,'UTF8')
    AND a.artifact_sha256=sha256(a.artifact_bytes)
    AND a.artifact_sha256=decode(recipe->'profileArtifacts'->pin_name->>'sha256','hex')
    AND a.artifact_identity_sha256=sha256(convert_to(selected_artifact_identity,'UTF8')) FOR SHARE NOWAIT;
  pin:=convert_from(artifact,'UTF8')::jsonb;
  IF registration->pin_name IS DISTINCT FROM jsonb_build_object('identity',pin->>'identity','version',pin->>'version',
     'sha256',encode(sha256(artifact),'hex'))
   OR (pin_name='captureProfile' AND encode(artifact,'hex') IS DISTINCT FROM context->>'assertedOriginCaptureProfileHex') THEN
   RAISE EXCEPTION 'original full candidate profile correspondence required' USING ERRCODE='55000'; END IF;
 END LOOP;
 before_resources:=truss.runtime_select_catalog_report_resources(expected_writer,expected_ordinal,expected_generation,
  (SELECT encode(c.admission_profile_bytes,'hex') FROM truss.operation_configuration c
   WHERE c.original_writer_xid=op.original_writer_xid AND c.operation_ordinal=op.operation_ordinal));
 FOREACH schema_name IN ARRAY ARRAY['exact-value-v0.1.schema.json','history-record-v0.1.schema.json','history-event-v0.1.schema.json',
  'acceptance-input-v0.1.schema.json','acceptance-rejection-v0.1.schema.json','enforcement-report-v0.1.schema.json',
  'acceptance-report-v0.1.schema.json','history-retain-payload-v0.1.proposal.schema.json','history-event-v0.2.proposal.schema.json',
  'acceptance-report-v0.3.proposal.schema.json'] LOOP
  selected_artifact_identity:='packages/python/src/truss/_report_schemas/'||schema_name;
  SELECT convert_from(a.artifact_bytes,'UTF8')::jsonb INTO STRICT schema_value FROM truss.installation_archive a
   WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=selected_artifact_identity;
  IF schema_registry ? (schema_value->>'$id') THEN RAISE EXCEPTION 'unique selected report schema identity required' USING ERRCODE='55000'; END IF;
  schema_registry:=schema_registry||jsonb_build_object(schema_value->>'$id',schema_value);
  identities:=array_append(identities,selected_artifact_identity);
 END LOOP;
 -- The revision composition is independently selected source semantics, not authority.
 selected_artifact_identity:='packages/python/src/truss/_profiles/catalog-revision-wide-report-composition-candidate.json';
 IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
  AND a.artifact_role='input' AND a.artifact_identity=selected_artifact_identity)<>1 THEN
  RAISE EXCEPTION 'unique original revision composition archive required' USING ERRCODE='55000'; END IF;
 SELECT a.artifact_bytes INTO STRICT artifact FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=selected_artifact_identity
   AND a.artifact_sha256=sha256(a.artifact_bytes) AND a.artifact_sha256=decode('9269939c2151779c919826ef30beccfea51269f06da1d6241e8f6bb6d80e6253','hex')
   AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8')) FOR SHARE NOWAIT;
 identities:=array_append(identities,selected_artifact_identity);
 SELECT jsonb_agg(to_jsonb(a) ORDER BY a.archive_row_id) INTO profile_rows FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=ANY(identities);
 catalog_before:='{}'::jsonb;
 FOREACH table_name IN ARRAY ARRAY['schema_head','schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint'] LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text COLLATE "C"),''[]''::jsonb) FROM truss.%I t',table_name) INTO table_rows;
  catalog_before:=jsonb_set(catalog_before,ARRAY[table_name],table_rows);
 END LOOP;
 IF octet_length(catalog_before::text)>4194304 THEN RAISE EXCEPTION 'candidate catalog comparison capacity' USING ERRCODE='54000'; END IF;
 PERFORM truss.runtime_require_catalog_input(op.original_input_bytes);
 input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 IF registration->'layoutProfile' IS DISTINCT FROM input->'layoutProfile' THEN
  RAISE EXCEPTION 'original input layout candidate correspondence required' USING ERRCODE='55000'; END IF;
 IF (SELECT count(*) FROM truss.schema_rev WHERE rev>0)<>1
  OR NOT EXISTS(SELECT 1 FROM truss.schema_head WHERE id=1 AND rev=0)
  OR EXISTS(SELECT 1 FROM truss.catalog_acceptance_report) THEN
  RAISE EXCEPTION 'unpublished first revision candidate required' USING ERRCODE='55000'; END IF;
 SELECT rev INTO STRICT revision FROM truss.schema_rev WHERE rev>0;
 SELECT * INTO STRICT source FROM truss.runtime_collect_catalog_source_candidate(
  op.admitted_candidate_bytes,decode(convert_from(op.admitted_candidate_bytes,'UTF8')::jsonb->>'declarationsUtf8Hex','hex'));
 PERFORM * FROM truss.runtime_collect_new_catalog_inventory(revision);
 SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.ord::int),'[]'::jsonb) INTO documents
  FROM truss.runtime_collect_report_documents(revision) d;
 SELECT to_jsonb(c) INTO STRICT counts FROM truss.runtime_collect_new_catalog_counts(revision) c;
 lifecycle:=truss.runtime_collect_fresh_catalog_lifecycle(expected_writer,expected_ordinal,expected_generation,revision,lifecycle_policy);
 indexes:=truss.runtime_collect_absent_binding_index_declarations(expected_writer,expected_ordinal,expected_generation,revision,index_policy);
 origin:=truss.runtime_catalog_report_original_tree(decode(context->>'assertedOriginUtf8Hex','hex'));
 execution:=jsonb_build_object('installationId',context->>'installationId','sourceEpoch',context->>'sourceEpoch',
  'origin',jsonb_build_object('databaseRole',context->>'actingUser'),
  'journalOrigin',jsonb_build_object('databaseRole',context->>'actingUser'),
  'originMappingProfile',registration->'originMappingProfile','captureProfile',registration->'captureProfile',
  'contextEvidence',jsonb_build_object('identity','truss.original-native-operation-context4/'||expected_writer||'/'||expected_ordinal,
   'bytesBase64',replace(encode(op.original_context_bytes,'base64'),chr(10),''),
   'sha256',encode(sha256(op.original_context_bytes),'hex')));
 execution_tree:=truss.runtime_catalog_report_native_tree(execution);
 origin_envelope:=truss.runtime_catalog_report_native_tree(jsonb_build_object('databaseRole',context->>'actingUser'));
 journal_envelope:=jsonb_set(origin_envelope,'{members}',origin_envelope->'members'||jsonb_build_array(jsonb_build_object(
  'keyUtf8Hex','6173736572746564','node',truss.runtime_catalog_report_map_origin_tree(origin))));
 origin_envelope:=jsonb_set(origin_envelope,'{members}',origin_envelope->'members'||jsonb_build_array(jsonb_build_object(
  'keyUtf8Hex','6173736572746564','node',origin)));
 SELECT jsonb_agg(CASE m->>'keyUtf8Hex' WHEN '6f726967696e' THEN jsonb_set(m,'{node}',origin_envelope)
  WHEN '6a6f75726e616c4f726967696e' THEN jsonb_set(m,'{node}',journal_envelope) ELSE m END)
  INTO members FROM jsonb_array_elements(execution_tree->'members') m;
 execution_tree:=jsonb_set(execution_tree,'{members}',members);
 fields:=jsonb_build_object('interfaceVersion','truss-acceptance-report/0.3.0-proposal',
  'reportProfile',registration->'reportProfile','rev',revision::text,
  'acceptedInput',input,'documents',documents,'counts',jsonb_build_object(
   'typesAdded',counts->'types_added','propertiesAdded',counts->'properties_added','keysAdded',counts->'keys_added',
   'relationshipsAdded',counts->'relationships_added','endpointsAdded',counts->'endpoints_added','elementsRetired',counts->'elements_retired'),
  'provisional','[]'::jsonb,'rebinds','[]'::jsonb,'pending_indexes',indexes->'declaredJobs',
  'lifecycleProfile',lifecycle->'lifecycleProfile','reactivations',lifecycle->'reactivations');
 tree:=truss.runtime_catalog_report_native_tree(fields); members:=tree->'members'||jsonb_build_array(jsonb_build_object('keyUtf8Hex','6f726967696e616c457865637574696f6e','node',execution_tree));
 FOR member IN SELECT value FROM jsonb_array_elements(source.host_sources->'members') LOOP
  IF member->>'keyUtf8Hex'=encode(convert_to('assertionEntries','UTF8'),'hex') THEN assertion_tree:=member->'node';
  ELSE members:=members||jsonb_build_array(member); END IF;
 END LOOP;
 IF assertion_tree IS NULL OR assertion_tree->>'kind' IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'original complete candidate assertion inventory required' USING ERRCODE='55000'; END IF;
 FOR member IN SELECT value FROM jsonb_array_elements(assertion_tree->'items') LOOP
  IF member->>'kind' IS DISTINCT FROM 'object' OR jsonb_typeof(member->'members') IS DISTINCT FROM 'array'
   OR jsonb_array_length(member->'members')<>6
   OR (SELECT count(*) FROM jsonb_array_elements(member->'members') m WHERE decode(m->>'keyUtf8Hex','hex')
    IN (convert_to('assertion','UTF8'),convert_to('source','UTF8'),convert_to('ruleName','UTF8'),convert_to('ruleNameOrigin','UTF8'),convert_to('enforcement','UTF8'),convert_to('reason','UTF8')))<>6
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(member->'members') m WHERE m->>'keyUtf8Hex'=encode(convert_to('enforcement','UTF8'),'hex')
    AND m->'node'=jsonb_build_object('kind','string','utf8Hex',encode(convert_to('none','UTF8'),'hex')))
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(member->'members') m WHERE m->>'keyUtf8Hex'=encode(convert_to('reason','UTF8'),'hex')
    AND m->'node'=jsonb_build_object('kind','string','utf8Hex',encode(convert_to('unqualified','UTF8'),'hex'))) THEN
   RAISE EXCEPTION 'selected six-field none unqualified assertion projection required' USING ERRCODE='55000'; END IF;
 END LOOP;
 assertion_digest:=encode(sha256(convert_to('truss-canonical/0.1.0'||chr(10)||'truss-catalog-assertion-inventory/0.1.0'||chr(10),'UTF8')
   ||truss.runtime_canonical_tree_bytes(assertion_tree)),'hex');
 assertions:=truss.runtime_catalog_report_native_tree(jsonb_build_object('interfaceVersion','truss-enforcement-report/0.1.0',
  'catalogRevision',revision::text,'reportProfile',registration->'enforcementProfile','layoutProfile',input->'layoutProfile',
  'scope',jsonb_build_object('kind','complete'),'assertionInventorySha256',assertion_digest));
 assertions:=jsonb_set(assertions,'{members}',assertions->'members'||jsonb_build_array(jsonb_build_object(
  'keyUtf8Hex',encode(convert_to('entries','UTF8'),'hex'),'node',assertion_tree)));
 members:=members||jsonb_build_array(jsonb_build_object('keyUtf8Hex',encode(convert_to('assertions','UTF8'),'hex'),'node',assertions));
 IF jsonb_array_length(members)<>19 THEN RAISE EXCEPTION 'complete nineteen-field candidate report required' USING ERRCODE='55000'; END IF;
 report_tree:=jsonb_build_object('kind','object','members',members);
 original_report:=truss.runtime_canonical_tree_bytes(report_tree);
 IF NOT truss.runtime_catalog_report_shape_matches(report_tree,schema_registry->'urn:truss:proposal:acceptance-report:0.3.0',
  schema_registry,'urn:truss:proposal:acceptance-report:0.3.0') THEN
  RAISE EXCEPTION 'complete selected candidate report shape required' USING ERRCODE='22023'; END IF;
 -- Only an administrative algorithm fixture calls this. No public assembly
 -- selection, accepted result, head transition or commit seal is issued here.
 INSERT INTO truss.catalog_acceptance_report(rev,report_bytes) VALUES(revision,original_report)
  RETURNING report_bytes INTO STRICT returned_report;
 IF returned_report IS DISTINCT FROM original_report OR NOT EXISTS(
  SELECT 1 FROM truss.catalog_acceptance_report r WHERE r.rev=revision AND r.report_bytes=original_report)
  OR (SELECT count(*) FROM truss.catalog_acceptance_report)<>1 THEN
  RAISE EXCEPTION 'original report insert and independent byte readback required' USING ERRCODE='55000'; END IF;
 -- Build the revision wire from the same retained originals, never a later
 -- caller-supplied report or a fresh acceptance clock.
 SELECT r.* INTO STRICT revision_row FROM truss.schema_rev r WHERE r.rev=revision;
 IF truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(revision_row.origin))
  IS DISTINCT FROM truss.runtime_canonical_tree_bytes(origin) THEN
  RAISE EXCEPTION 'original revision parent origin correspondence required' USING ERRCODE='55000'; END IF;
 IF NOT isfinite(revision_row.accepted_at)
  OR extract(year FROM revision_row.accepted_at AT TIME ZONE 'UTC') NOT BETWEEN 1 AND 9999 THEN
  RAISE EXCEPTION 'finite selected revision acceptance timestamp required' USING ERRCODE='22023'; END IF;
 accepted_at_text:=to_char(revision_row.accepted_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"');
 report_identity:='truss.candidate.catalog-report/'||encode(convert_to(context->>'installationId','UTF8'),'hex')
  ||'/'||encode(convert_to(context->>'sourceEpoch','UTF8'),'hex')||'/'||revision::text;
 IF ((octet_length(original_report)::bigint+2)/3)*4>1048576 THEN
  RAISE EXCEPTION 'revision report artifact scalar capacity' USING ERRCODE='54000'; END IF;
 IF octet_length(original_report)>4194304 OR octet_length(op.original_input_bytes)>1048576
  OR ((octet_length(original_report)::bigint+2)/3)*4+octet_length(op.original_input_bytes)>4194304 THEN
  RAISE EXCEPTION 'revision wire expansion capacity' USING ERRCODE='54000'; END IF;
 revision_tree:=truss.runtime_catalog_report_native_tree(jsonb_build_object(
  'interfaceVersion','truss-feed-revision/0.1.0','revision',revision::text,'acceptedAt',accepted_at_text,
  'input',input,'report',jsonb_build_object('identity',report_identity,
   'bytesBase64',replace(encode(original_report,'base64'),chr(10),''),
   'sha256',encode(sha256(original_report),'hex'))));
 revision_tree:=jsonb_set(revision_tree,'{members}',revision_tree->'members'||jsonb_build_array(
  jsonb_build_object('keyUtf8Hex','6f726967696e','node',journal_envelope)));
 IF octet_length(revision_tree::text)>4194304 THEN
  RAISE EXCEPTION 'revision tagged tree capacity' USING ERRCODE='54000'; END IF;
 revision_payload:=truss.runtime_revision_report_tree_bytes_wide_candidate(revision_tree,original_report);
 IF octet_length(revision_payload)>4194304 THEN
  RAISE EXCEPTION 'revision payload capacity' USING ERRCODE='54000'; END IF;
 SELECT jsonb_agg(to_jsonb(a) ORDER BY a.archive_row_id) INTO final_profile_rows FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=ANY(identities);
 catalog_after:='{}'::jsonb;
 FOREACH table_name IN ARRAY ARRAY['schema_head','schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint'] LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text COLLATE "C"),''[]''::jsonb) FROM truss.%I t',table_name) INTO table_rows;
  catalog_after:=jsonb_set(catalog_after,ARRAY[table_name],table_rows);
 END LOOP;
 after_resources:=truss.runtime_select_catalog_report_resources(expected_writer,expected_ordinal,(op.effect_generation+1)::text,
  (SELECT encode(c.admission_profile_bytes,'hex') FROM truss.operation_configuration c
   WHERE c.original_writer_xid=op.original_writer_xid AND c.operation_ordinal=op.operation_ordinal));
 IF after_resources IS DISTINCT FROM before_resources THEN
  RAISE EXCEPTION 'original complete report resource final cut required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT after_graph FROM truss.runtime_collect_configured_catalog_graph();
 SELECT o.* INTO STRICT current_op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.operation_ordinal=op.operation_ordinal;
 IF current_op.effect_generation<>op.effect_generation+1
  OR catalog_after IS DISTINCT FROM catalog_before OR final_profile_rows IS DISTINCT FROM profile_rows
  OR (to_jsonb(current_op)-'effect_generation') IS DISTINCT FROM (to_jsonb(op)-'effect_generation')
  OR (to_jsonb(after_graph)-'effect_generation') IS DISTINCT FROM (to_jsonb(before_graph)-'effect_generation')
  OR NOT EXISTS(SELECT 1 FROM truss.installation_archive a WHERE a.archive_row_id=original_registration_id
    AND a.artifact_bytes=original_registration AND a.artifact_sha256=sha256(original_registration)) THEN
  RAISE EXCEPTION 'original candidate report final source cut required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT op.original_writer_xid::text,op.operation_ordinal::text,current_op.effect_generation::text,
  encode(original_report,'hex'),'administrative_rollback_only_report_write'::text,false,encode(revision_payload,'hex');
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_write_catalog_report_wide_candidate(text, text, text, text, bytea, bytea, bytea) FROM public