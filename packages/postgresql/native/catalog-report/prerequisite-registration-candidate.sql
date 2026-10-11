-- Private fresh registration extension selects the separate wide-report chain.
-- Historical pending revision producer stays exact.
CREATE FUNCTION truss.runtime_register_catalog_prerequisites_candidate(
 w text,o text,g text,registration_identity text,original_registration bytea,lifecycle_policy bytea,index_policy bytea)
RETURNS TABLE(writer_xid text,operation_ordinal text,effect_generation text,report_utf8_hex text,
 revision_payload_utf8_hex text,document_prerequisites text,configuration_prerequisites text,
 membership_generation text,scope text,accepted_report_qualified boolean,feed_qualified boolean)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; cfg truss.operation_configuration%ROWTYPE;
 parent truss.feed_tx%ROWTYPE; doc truss.schema_doc%ROWTYPE; planned_doc truss.feed_prerequisite%ROWTYPE;
 planned_cfg truss.feed_configuration_prerequisite%ROWTYPE;
 recipe_bytes bytea; recipe jsonb; sources jsonb:='{}'; name text; identity text; original bytea;
 report record; returned record; before_state jsonb; after_state jsonb; revision int;
 document_profile bytea; configuration_profile bytea; owner_bytes bytea; artifact bytea;
 original_input jsonb; original_document jsonb; seen jsonb:='{}'; doc_identity text; document_ordinal int:=0;
 expected_docs bytea[]:=ARRAY[]::bytea[]; actual_docs bytea[]; expected_parent jsonb; expected_row jsonb;
BEGIN
 PERFORM truss.runtime_require_catalog_observation(w,o,g);
 SELECT t.* INTO STRICT op FROM truss.row_home_operation t
  WHERE t.original_writer_xid=pg_current_xact_id_if_assigned() AND t.operation_ordinal::text=o;
 identity:='packages/python/src/truss/_profiles/catalog-prerequisite-registration-candidate.json';
 LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT;
 PERFORM truss.runtime_require_selected_archive_write_fence();
 IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=(convert_from(op.original_context_bytes,'UTF8')::jsonb->>'installationId')
  AND a.artifact_role='input' AND a.artifact_identity=identity)<>1 THEN RAISE EXCEPTION 'unique prerequisite recipe required' USING ERRCODE='55000'; END IF;
 SELECT a.artifact_bytes INTO STRICT recipe_bytes FROM truss.installation_archive a
  WHERE a.installation_id=(convert_from(op.original_context_bytes,'UTF8')::jsonb->>'installationId') AND a.artifact_role='input' AND a.artifact_identity=identity
   AND a.artifact_sha256=sha256(a.artifact_bytes) AND a.artifact_sha256=decode('293bce5ba248e558319eba57ecfe3b5f683d6d89b58033003e33b6aad38cde73','hex')
   AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8'));
 recipe:=convert_from(recipe_bytes,'UTF8')::jsonb;
 FOREACH name IN ARRAY ARRAY['catalog-reserve','configuration-reserve','catalog-insert','configuration-insert'] LOOP
  identity:=recipe->'sources'->name->>'path';
  IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=(convert_from(op.original_context_bytes,'UTF8')::jsonb->>'installationId')
   AND a.artifact_role='input' AND a.artifact_identity=identity)<>1 THEN RAISE EXCEPTION 'unique prerequisite statement source required' USING ERRCODE='55000'; END IF;
  SELECT a.artifact_bytes INTO STRICT original FROM truss.installation_archive a
   WHERE a.installation_id=(convert_from(op.original_context_bytes,'UTF8')::jsonb->>'installationId') AND a.artifact_role='input' AND a.artifact_identity=identity
    AND a.artifact_sha256=sha256(a.artifact_bytes) AND encode(a.artifact_sha256,'hex')=recipe->'sources'->name->>'sha256'
    AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8'));
  IF octet_length(original)>16384 THEN RAISE EXCEPTION 'prerequisite statement capacity' USING ERRCODE='54000'; END IF;
  sources:=sources||jsonb_build_object(name,convert_from(original,'UTF8'));
 END LOOP;
 original_input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 PERFORM truss.runtime_require_catalog_input(op.original_input_bytes);
 IF jsonb_array_length(original_input->'documents') NOT BETWEEN 1 AND 512 THEN RAISE EXCEPTION 'bounded original document inventory required' USING ERRCODE='54000'; END IF;
 configuration_profile:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(recipe->'configurationProfile'));
 -- The unchanged producer supplies originals and validates the first-use empty cut.
 SELECT * INTO STRICT report FROM truss.runtime_write_report_register_revision_wide_candidate(w,o,g,registration_identity,original_registration,lifecycle_policy,index_policy);
 revision:=(convert_from(decode(report.revision_payload_utf8_hex,'hex'),'UTF8')::jsonb->>'revision')::int;
 SELECT t.* INTO STRICT parent FROM truss.feed_tx t;
 SELECT m.original_owner_context_bytes INTO STRICT owner_bytes FROM truss.feed_member m;
 SELECT c.* INTO STRICT cfg FROM truss.operation_configuration c WHERE c.original_writer_xid=op.original_writer_xid AND c.operation_ordinal=op.operation_ordinal;
 before_state:=truss.runtime_capture_configured_prerequisite_state_candidate(w,o,report.effect_generation);
 IF (SELECT count(*) FROM truss.schema_doc d WHERE d.rev=revision) NOT BETWEEN 1 AND 512 THEN RAISE EXCEPTION 'complete bounded document prerequisites required' USING ERRCODE='54000'; END IF;
 -- Generation content excludes operation xid/ordinal/context digest and clocks.
 artifact:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(jsonb_build_object(
  'installation',cfg.installation_id,'sourceEpoch',cfg.source_epoch,'targetIncarnation',cfg.target_incarnation,
  'generation',cfg.configuration_generation::text,'keyReuse',cfg.key_reuse,'journalMode',cfg.journal_mode,
  'admissionProfileHexChunks',truss.runtime_registration_original_hex_chunks(cfg.admission_profile_bytes),
  'configurationHexChunks',truss.runtime_registration_original_hex_chunks(cfg.configuration_bytes),
  'bindingHexChunks',truss.runtime_registration_original_hex_chunks(cfg.selected_binding_bytes),
  'inventoryHexChunks',truss.runtime_registration_original_hex_chunks(cfg.installed_inventory_bytes))));
 IF octet_length(artifact)>4194304 THEN RAISE EXCEPTION 'generation artifact capacity' USING ERRCODE='54000'; END IF;
 FOR doc IN SELECT d.* FROM truss.schema_doc d WHERE d.rev=revision ORDER BY d.ord LOOP
  planned_doc.source_epoch:=parent.source_epoch;planned_doc.feed_profile:=parent.feed_profile;planned_doc.original_writer_xid:=parent.original_writer_xid;
  planned_doc.prerequisite_address:=parent.prerequisite_registration_counter+1;planned_doc.original_revision:=revision;
  original_document:=original_input->'documents'->document_ordinal;document_ordinal:=document_ordinal+1;
  IF original_document->>'documentId' IS DISTINCT FROM doc.doc_id OR original_document->>'documentRevision' IS DISTINCT FROM doc.doc_revision THEN
   RAISE EXCEPTION 'original document ordering and identity required' USING ERRCODE='55000'; END IF;
  doc_identity:=original_document->'artifact'->>'identity';
  planned_doc.original_artifact_identity_bytes:=convert_to(doc_identity,'UTF8');
  planned_doc.original_definition_bytes:=decode(original_document->'artifact'->>'bytesBase64','base64');
  document_profile:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(original_document->'umfProfile'));
  planned_doc.original_definition_profile_bytes:=document_profile;
  IF planned_doc.original_definition_bytes IS DISTINCT FROM convert_to(doc.document,'UTF8') THEN RAISE EXCEPTION 'complete original document bytes required' USING ERRCODE='55000'; END IF;
  IF seen ? doc_identity THEN
   IF seen->doc_identity IS DISTINCT FROM jsonb_build_object('bytes',encode(planned_doc.original_definition_bytes,'hex'),'profile',encode(document_profile,'hex')) THEN
    RAISE EXCEPTION 'conflicting original document artifact identity' USING ERRCODE='55000'; END IF;
   CONTINUE;
  END IF;
  seen:=seen||jsonb_build_object(doc_identity,jsonb_build_object('bytes',encode(planned_doc.original_definition_bytes,'hex'),'profile',encode(document_profile,'hex')));
  planned_doc.original_definition_sha256:=sha256(planned_doc.original_definition_bytes);planned_doc.original_owner_context_bytes:=owner_bytes;
  IF encode(planned_doc.original_definition_sha256,'hex') IS DISTINCT FROM doc.content_sha256 THEN RAISE EXCEPTION 'original document bytes digest correspondence required' USING ERRCODE='55000'; END IF;
  EXECUTE sources->>'catalog-reserve' INTO STRICT returned USING parent.source_epoch,parent.feed_profile,parent.prerequisite_registration_counter,parent.membership_generation,parent.original_context_bytes,parent.manifest_profile_bytes;
  parent.prerequisite_registration_counter:=parent.prerequisite_registration_counter+1;parent.membership_generation:=parent.membership_generation+1;
  IF to_jsonb(returned) IS DISTINCT FROM jsonb_build_object('source_epoch',parent.source_epoch,'feed_profile',parent.feed_profile,'original_writer_xid',parent.original_writer_xid::text,'registration_counter',parent.registration_counter::text,'prerequisite_registration_counter',parent.prerequisite_registration_counter::text,'configuration_registration_counter',parent.configuration_registration_counter::text,'membership_generation',parent.membership_generation::text,'finalized_generation',parent.finalized_generation::text,'original_context_bytes_hex',encode(parent.original_context_bytes,'hex'),'manifest_profile_bytes_hex',encode(parent.manifest_profile_bytes,'hex'),'manifest_bytes_hex',encode(parent.manifest_bytes,'hex'),'manifest_sha256_hex',encode(parent.manifest_sha256,'hex')) THEN RAISE EXCEPTION 'complete catalog reservation RETURNING correspondence required' USING ERRCODE='55000'; END IF;
  IF (SELECT count(*) FROM truss.feed_tx)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t WHERE record_send(t)=record_send(parent)) THEN RAISE EXCEPTION 'complete catalog reservation correspondence required' USING ERRCODE='55000'; END IF;
  EXECUTE sources->>'catalog-insert' INTO STRICT returned USING parent.source_epoch,parent.feed_profile,parent.prerequisite_registration_counter,parent.membership_generation,
   planned_doc.original_revision,planned_doc.original_artifact_identity_bytes,planned_doc.original_definition_bytes,document_profile,planned_doc.original_definition_sha256,owner_bytes,parent.original_context_bytes,parent.manifest_profile_bytes;
 IF to_jsonb(returned) IS DISTINCT FROM jsonb_build_object('source_epoch',planned_doc.source_epoch,'feed_profile',planned_doc.feed_profile,'original_writer_xid',planned_doc.original_writer_xid::text,'prerequisite_address',planned_doc.prerequisite_address::text,'original_revision',planned_doc.original_revision::text,'original_artifact_identity_bytes_hex',encode(planned_doc.original_artifact_identity_bytes,'hex'),'original_definition_bytes_hex',encode(planned_doc.original_definition_bytes,'hex'),'original_definition_profile_bytes_hex',encode(planned_doc.original_definition_profile_bytes,'hex'),'original_definition_sha256_hex',encode(planned_doc.original_definition_sha256,'hex'),'original_owner_context_bytes_hex',encode(planned_doc.original_owner_context_bytes,'hex')) THEN RAISE EXCEPTION 'complete prerequisite INSERT RETURNING correspondence required' USING ERRCODE='55000'; END IF;
  IF NOT EXISTS(SELECT 1 FROM truss.feed_prerequisite p WHERE record_send(p)=record_send(planned_doc)) THEN RAISE EXCEPTION 'complete original document prerequisite correspondence required' USING ERRCODE='55000'; END IF;
  expected_docs:=array_append(expected_docs,record_send(planned_doc));
 END LOOP;
 planned_cfg.source_epoch:=parent.source_epoch;planned_cfg.feed_profile:=parent.feed_profile;planned_cfg.original_writer_xid:=parent.original_writer_xid;
 planned_cfg.configuration_address:=1;planned_cfg.original_installation_identity_bytes:=convert_to(cfg.installation_id,'UTF8');
 planned_cfg.original_configuration_generation:=cfg.configuration_generation;planned_cfg.original_configuration_profile_bytes:=configuration_profile;
 planned_cfg.original_configuration_bytes:=artifact;planned_cfg.original_producer_inventory_bytes:=cfg.installed_inventory_bytes;
 planned_cfg.original_configuration_sha256:=sha256(artifact);planned_cfg.original_owner_context_bytes:=owner_bytes;
 EXECUTE sources->>'configuration-reserve' INTO STRICT returned USING parent.source_epoch,parent.feed_profile,parent.configuration_registration_counter,parent.membership_generation,parent.original_context_bytes,parent.manifest_profile_bytes;
 parent.configuration_registration_counter:=1;parent.membership_generation:=parent.membership_generation+1;
 IF to_jsonb(returned) IS DISTINCT FROM jsonb_build_object('source_epoch',parent.source_epoch,'feed_profile',parent.feed_profile,'original_writer_xid',parent.original_writer_xid::text,'registration_counter',parent.registration_counter::text,'prerequisite_registration_counter',parent.prerequisite_registration_counter::text,'configuration_registration_counter',parent.configuration_registration_counter::text,'membership_generation',parent.membership_generation::text,'finalized_generation',parent.finalized_generation::text,'original_context_bytes_hex',encode(parent.original_context_bytes,'hex'),'manifest_profile_bytes_hex',encode(parent.manifest_profile_bytes,'hex'),'manifest_bytes_hex',encode(parent.manifest_bytes,'hex'),'manifest_sha256_hex',encode(parent.manifest_sha256,'hex')) THEN RAISE EXCEPTION 'complete configuration reservation RETURNING correspondence required' USING ERRCODE='55000'; END IF;
 IF (SELECT count(*) FROM truss.feed_tx)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t WHERE record_send(t)=record_send(parent)) THEN RAISE EXCEPTION 'complete configuration reservation correspondence required' USING ERRCODE='55000'; END IF;
 EXECUTE sources->>'configuration-insert' INTO STRICT returned USING parent.source_epoch,parent.feed_profile,1::bigint,parent.membership_generation,
  planned_cfg.original_installation_identity_bytes,planned_cfg.original_configuration_generation,configuration_profile,artifact,cfg.installed_inventory_bytes,sha256(artifact),owner_bytes,parent.original_context_bytes,parent.manifest_profile_bytes;
 IF to_jsonb(returned) IS DISTINCT FROM jsonb_build_object('source_epoch',planned_cfg.source_epoch,'feed_profile',planned_cfg.feed_profile,'original_writer_xid',planned_cfg.original_writer_xid::text,'configuration_address',planned_cfg.configuration_address::text,'original_installation_identity_bytes_hex',encode(planned_cfg.original_installation_identity_bytes,'hex'),'original_configuration_generation',planned_cfg.original_configuration_generation::text,'original_configuration_profile_bytes_hex',encode(planned_cfg.original_configuration_profile_bytes,'hex'),'original_configuration_bytes_hex',encode(planned_cfg.original_configuration_bytes,'hex'),'original_producer_inventory_bytes_hex',encode(planned_cfg.original_producer_inventory_bytes,'hex'),'original_configuration_sha256_hex',encode(planned_cfg.original_configuration_sha256,'hex'),'original_owner_context_bytes_hex',encode(planned_cfg.original_owner_context_bytes,'hex')) THEN RAISE EXCEPTION 'complete prerequisite INSERT RETURNING correspondence required' USING ERRCODE='55000'; END IF;
 after_state:=truss.runtime_capture_configured_prerequisite_state_candidate(w,o,report.effect_generation);
 SELECT array_agg(record_send(p) ORDER BY p.prerequisite_address) INTO actual_docs FROM truss.feed_prerequisite p;
 IF document_ordinal<>jsonb_array_length(original_input->'documents') THEN RAISE EXCEPTION 'complete original prerequisite document inventory required' USING ERRCODE='55000'; END IF;
 IF after_state IS DISTINCT FROM before_state OR actual_docs IS DISTINCT FROM expected_docs
  OR (SELECT count(*) FROM truss.feed_tx)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t WHERE record_send(t)=record_send(parent))
  OR (SELECT count(*) FROM truss.feed_configuration_prerequisite)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_configuration_prerequisite p WHERE record_send(p)=record_send(planned_cfg)) THEN
  RAISE EXCEPTION 'complete configured prerequisite registration delta required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT w,o,report.effect_generation,report.report_utf8_hex,report.revision_payload_utf8_hex,
  parent.prerequisite_registration_counter::text,'1'::text,parent.membership_generation::text,
  'administrative_single_original_fresh_catalog_rollback_only'::text,false,false;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_register_catalog_prerequisites_candidate(text,text,text,text,bytea,bytea,bytea) FROM PUBLIC;
