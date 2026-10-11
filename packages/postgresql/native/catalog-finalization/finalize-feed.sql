-- Coordinates-only administrative composition candidate; commit barrier retained.
CREATE FUNCTION truss.runtime_finalize_original_catalog_feed_candidate(w text,o text,g text)
RETURNS TABLE(tree_bytes_hex text,wire_bytes_hex text,semantic_sha256_hex text,membership_generation text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp
SET TimeZone='UTC' SET DateStyle='ISO, YMD' SET bytea_output='hex' AS $$
DECLARE op truss.row_home_operation%ROWTYPE; cfg truss.operation_configuration%ROWTYPE;
 custody truss.catalog_revision_custody%ROWTYPE; parent truss.feed_tx%ROWTYPE;
 member truss.feed_member%ROWTYPE; expected_member truss.feed_member%ROWTYPE;
 expected_parent truss.feed_tx%ROWTYPE; docrow truss.feed_prerequisite%ROWTYPE;
 cfgrow truss.feed_configuration_prerequisite%ROWTYPE;
 cfgplan truss.feed_configuration_prerequisite%ROWTYPE;
 context jsonb; input jsonb; recipe jsonb; original bytea; sources jsonb:='{}'::jsonb;
 definition bytea; cfg_profile bytea; manifest record; returned record;
 name text; identity text; document jsonb; doc_identity text; seen jsonb:='{}'::jsonb;
 before_state jsonb; after_state jsonb; expected_state jsonb; expected_docs bytea[]:=ARRAY[]::bytea[];
 actual_docs bytea[]; cfg_capsule jsonb; cfg_artifact bytea; address bigint:=0; finalized boolean;
 expected_return jsonb; clear_return jsonb; original_custody bytea; original_operation bytea; original_configuration bytea; recipe_bytes bytea;
BEGIN
 -- This composition guard must be independently selected with the new complete
 -- roster/definition before parent creation. Old rosters are not reinterpreted.
 PERFORM truss.runtime_require_catalog_finalization_composition_candidate(w,o,g);
 SELECT * INTO STRICT op FROM truss.row_home_operation t WHERE t.original_writer_xid=pg_current_xact_id_if_assigned()
  AND t.operation_ordinal::text=o FOR UPDATE NOWAIT;
 SELECT * INTO STRICT cfg FROM truss.operation_configuration t WHERE t.original_writer_xid=op.original_writer_xid AND t.operation_ordinal=op.operation_ordinal FOR SHARE NOWAIT;
 SELECT * INTO STRICT custody FROM truss.catalog_revision_custody t WHERE t.original_writer_xid=op.original_writer_xid AND t.operation_ordinal=op.operation_ordinal FOR SHARE NOWAIT;
 original_custody:=record_send(custody);original_operation:=record_send(op);original_configuration:=record_send(cfg);context:=convert_from(op.original_context_bytes,'UTF8')::jsonb;
 IF op.effect_generation::text IS DISTINCT FROM g OR custody.capture_generation::text IS DISTINCT FROM g
  OR op.original_writer_xid::text IS DISTINCT FROM w OR cfg.source_epoch IS DISTINCT FROM context->>'sourceEpoch'
  OR cfg.installation_id IS DISTINCT FROM context->>'installationId'
  OR (SELECT count(*) FROM truss.row_home_operation)<>1 OR (SELECT count(*) FROM truss.catalog_revision_custody)<>1
  OR (SELECT count(*) FROM truss.schema_head)<>1 OR NOT EXISTS(SELECT 1 FROM truss.schema_head WHERE id=1 AND rev=0) THEN
  RAISE EXCEPTION 'single original pending catalog scope required' USING ERRCODE='55000'; END IF;
 PERFORM truss.runtime_require_finalizing_custody_correspondence_candidate(w,o,g);
 PERFORM truss.runtime_collect_finalizing_catalog_business_scope_candidate();
 LOCK TABLE truss.feed_tx,truss.feed_member,truss.feed_prerequisite,truss.feed_configuration_prerequisite IN SHARE ROW EXCLUSIVE MODE NOWAIT;
 LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT;
 PERFORM truss.runtime_require_selected_archive_write_fence();
 identity:='packages/python/src/truss/_profiles/catalog-feed-finalization-candidate.json';
 SELECT a.artifact_bytes INTO STRICT recipe_bytes FROM truss.installation_archive a
  WHERE a.installation_id=cfg.installation_id AND a.artifact_role='input' AND a.artifact_identity=identity
  AND a.artifact_sha256=sha256(a.artifact_bytes) AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8'));
 -- The entry guard pins this exact recipe and all dependency bytes independently.
 recipe:=convert_from(recipe_bytes,'UTF8')::jsonb;
 definition:=decode(recipe->>'manifestDefinitionHex','hex');
 cfg_profile:=decode(recipe->>'configurationProfileHex','hex');
 FOREACH name IN ARRAY ARRAY['clear-parent','clear-member','assign-ordinal','publish-manifest'] LOOP
  identity:=recipe->'sources'->name->>'path';
  SELECT a.artifact_bytes INTO STRICT original FROM truss.installation_archive a
   WHERE a.installation_id=cfg.installation_id AND a.artifact_role='input' AND a.artifact_identity=identity
   AND a.artifact_sha256=sha256(a.artifact_bytes) AND encode(a.artifact_sha256,'hex')=recipe->'sources'->name->>'sha256'
   AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8'));
  IF octet_length(original)>16384 THEN RAISE EXCEPTION 'finalization statement capacity' USING ERRCODE='54000'; END IF;
  sources:=sources||jsonb_build_object(name,convert_from(original,'UTF8'));
 END LOOP;
 SELECT * INTO STRICT parent FROM truss.feed_tx;
 SELECT * INTO STRICT member FROM truss.feed_member;
 before_state:=truss.runtime_capture_finalizing_completion_state_candidate(w,o,g);expected_state:=before_state;
 cfg_capsule:=jsonb_build_object('installationId',cfg.installation_id,'sourceEpoch',cfg.source_epoch,
  'targetIncarnation',cfg.target_incarnation,'generation',cfg.configuration_generation::text,
  'keyReuse',cfg.key_reuse,'journalMode',cfg.journal_mode,'admissionProfileHex',encode(cfg.admission_profile_bytes,'hex'),
  'configurationHex',encode(cfg.configuration_bytes,'hex'),'bindingHex',encode(cfg.selected_binding_bytes,'hex'),
  'inventoryHex',encode(cfg.installed_inventory_bytes,'hex'));
 SELECT * INTO STRICT manifest FROM truss.runtime_original_catalog_manifest_candidate(
  op.original_input_bytes,custody.original_revision::text,op.original_writer_xid::text,
  jsonb_build_object('sourceEpoch',cfg.source_epoch,'feedProfile',recipe->>'feedProfile',
   'scopeIdentity','administrative_single_original_operation_fresh_catalog_rollback_only'),
  definition,custody.original_payload_profile_bytes,custody.original_payload_bytes,
  convert_to(cfg_capsule::text,'UTF8'),cfg_profile);
 cfg_artifact:=decode((convert_from(manifest.manifest_bytes,'UTF8')::jsonb->'configurationPrerequisites'->0->'artifact'->>'bytesBase64'),'base64');
 expected_member.source_epoch:=cfg.source_epoch;expected_member.feed_profile:=recipe->>'feedProfile';
 expected_member.original_writer_xid:=op.original_writer_xid;expected_member.registration_address:=1;
 expected_member.fact_kind:='revision';expected_member.original_fact_key_bytes:=custody.original_fact_key_bytes;
 expected_member.original_fact_key_profile_bytes:=custody.original_fact_key_profile_bytes;
 expected_member.original_payload_bytes:=custody.original_payload_bytes;
 expected_member.original_payload_profile_bytes:=custody.original_payload_profile_bytes;
 expected_member.original_payload_sha256:=sha256(custody.original_payload_bytes);
 expected_member.original_owner_context_bytes:=custody.original_owner_context_bytes;
 expected_member.original_write_at:=custody.original_write_at;expected_member.original_fact_clock_bytes:=custody.original_fact_clock_bytes;
 -- Independently reconstruct every document prerequisite in original registration order.
 input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 FOR document IN SELECT value FROM jsonb_array_elements(input->'documents') LOOP
  doc_identity:=document->'artifact'->>'identity';
  IF seen ? doc_identity THEN CONTINUE; END IF;
  seen:=seen||jsonb_build_object(doc_identity,true);address:=address+1;
  docrow:=NULL;docrow.source_epoch:=cfg.source_epoch;docrow.feed_profile:=recipe->>'feedProfile';
  docrow.original_writer_xid:=op.original_writer_xid;docrow.prerequisite_address:=address;
  docrow.original_revision:=custody.original_revision;
  docrow.original_artifact_identity_bytes:=convert_to(doc_identity,'UTF8');
  docrow.original_definition_bytes:=decode(document->'artifact'->>'bytesBase64','base64');
  docrow.original_definition_profile_bytes:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(document->'umfProfile'));
  docrow.original_definition_sha256:=sha256(docrow.original_definition_bytes);
  docrow.original_owner_context_bytes:=custody.original_owner_context_bytes;
  expected_docs:=array_append(expected_docs,record_send(docrow));
 END LOOP;
 SELECT array_agg(record_send(p) ORDER BY p.prerequisite_address) INTO actual_docs FROM truss.feed_prerequisite p;
 cfgplan.source_epoch:=cfg.source_epoch;cfgplan.feed_profile:=recipe->>'feedProfile';cfgplan.original_writer_xid:=op.original_writer_xid;
 cfgplan.configuration_address:=1;cfgplan.original_installation_identity_bytes:=convert_to(cfg.installation_id,'UTF8');
 cfgplan.original_configuration_generation:=cfg.configuration_generation;
 cfgplan.original_configuration_profile_bytes:=cfg_profile;cfgplan.original_configuration_bytes:=cfg_artifact;
 cfgplan.original_producer_inventory_bytes:=cfg.installed_inventory_bytes;cfgplan.original_configuration_sha256:=sha256(cfg_artifact);
 cfgplan.original_owner_context_bytes:=custody.original_owner_context_bytes;
 SELECT * INTO STRICT cfgrow FROM truss.feed_configuration_prerequisite;
 expected_parent.source_epoch:=cfg.source_epoch;expected_parent.feed_profile:=recipe->>'feedProfile';
 expected_parent.original_writer_xid:=op.original_writer_xid;expected_parent.registration_counter:=1;
 expected_parent.prerequisite_registration_counter:=address;expected_parent.configuration_registration_counter:=1;
 expected_parent.membership_generation:=address+2;expected_parent.original_context_bytes:=op.original_context_bytes;
 expected_parent.manifest_profile_bytes:=definition;
 finalized:=parent.finalized_generation IS NOT NULL;
 IF finalized THEN
  expected_parent.finalized_generation:=address+2;expected_parent.manifest_bytes:=manifest.tree_bytes;
  expected_parent.manifest_sha256:=manifest.semantic_sha256;expected_member.delivery_ordinal:=0;
 END IF;
 IF (SELECT count(*) FROM truss.feed_tx)<>1 OR (SELECT count(*) FROM truss.feed_member)<>1
  OR (SELECT count(*) FROM truss.feed_configuration_prerequisite)<>1
  OR record_send(parent) IS DISTINCT FROM record_send(expected_parent)
  OR record_send(member) IS DISTINCT FROM record_send(expected_member)
  OR record_send(cfgrow) IS DISTINCT FROM record_send(cfgplan) OR actual_docs IS DISTINCT FROM expected_docs THEN
  RAISE EXCEPTION 'complete original feed registration correspondence required' USING ERRCODE='55000'; END IF;
 -- All originals and current full records passed before the first publication effect.
 expected_parent.finalized_generation:=NULL;expected_parent.manifest_bytes:=NULL;expected_parent.manifest_sha256:=NULL;
 clear_return:=jsonb_build_object('source_epoch',cfg.source_epoch,'feed_profile',expected_parent.feed_profile,
  'original_writer_xid',w,'membership_generation',(address+2)::text,'finalized_generation',NULL,'manifest_bytes_hex',NULL,'manifest_sha256_hex',NULL);
 EXECUTE sources->>'clear-parent' INTO STRICT returned USING cfg.source_epoch,expected_parent.feed_profile,address+2;
 IF to_jsonb(returned) IS DISTINCT FROM clear_return OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t WHERE record_send(t)=record_send(expected_parent)) THEN
  RAISE EXCEPTION 'full original parent clear correspondence required' USING ERRCODE='55000'; END IF;
 expected_state:=jsonb_set(expected_state,'{stores,feed_tx}',jsonb_build_array(encode(record_send(expected_parent),'hex')));
 after_state:=truss.runtime_capture_finalizing_completion_state_candidate(w,o,g);
 IF after_state IS DISTINCT FROM expected_state THEN RAISE EXCEPTION 'complete parent clear state delta required' USING ERRCODE='55000'; END IF;
 expected_member.delivery_ordinal:=NULL;
 expected_return:=jsonb_build_object('source_epoch',cfg.source_epoch,'feed_profile',expected_parent.feed_profile,
  'original_writer_xid',w,'registration_address','1','delivery_ordinal',NULL);
 EXECUTE sources->>'clear-member' INTO STRICT returned USING cfg.source_epoch,expected_parent.feed_profile;
 IF to_jsonb(returned) IS DISTINCT FROM expected_return OR NOT EXISTS(SELECT 1 FROM truss.feed_member t WHERE record_send(t)=record_send(expected_member)) THEN
  RAISE EXCEPTION 'full original member clear correspondence required' USING ERRCODE='55000'; END IF;
 expected_state:=jsonb_set(expected_state,'{stores,feed_member}',jsonb_build_array(encode(record_send(expected_member),'hex')));
 after_state:=truss.runtime_capture_finalizing_completion_state_candidate(w,o,g);
 IF after_state IS DISTINCT FROM expected_state THEN RAISE EXCEPTION 'complete member clear state delta required' USING ERRCODE='55000'; END IF;
 EXECUTE sources->>'assign-ordinal' INTO STRICT returned USING cfg.source_epoch,expected_parent.feed_profile,address+2,1::bigint,0::bigint;
 expected_return:=jsonb_set(expected_return,'{delivery_ordinal}','"0"');expected_member.delivery_ordinal:=0;
 IF to_jsonb(returned) IS DISTINCT FROM expected_return OR NOT EXISTS(SELECT 1 FROM truss.feed_member t WHERE record_send(t)=record_send(expected_member)) THEN
  RAISE EXCEPTION 'full original member ordinal correspondence required' USING ERRCODE='55000'; END IF;
 expected_state:=jsonb_set(expected_state,'{stores,feed_member}',jsonb_build_array(encode(record_send(expected_member),'hex')));
 after_state:=truss.runtime_capture_finalizing_completion_state_candidate(w,o,g);
 IF after_state IS DISTINCT FROM expected_state THEN RAISE EXCEPTION 'complete member ordinal state delta required' USING ERRCODE='55000'; END IF;
 EXECUTE sources->>'publish-manifest' INTO STRICT returned USING cfg.source_epoch,expected_parent.feed_profile,address+2,manifest.tree_bytes,manifest.semantic_sha256;
 expected_parent.finalized_generation:=address+2;expected_parent.manifest_bytes:=manifest.tree_bytes;expected_parent.manifest_sha256:=manifest.semantic_sha256;
 expected_return:=jsonb_set(jsonb_set(jsonb_set(clear_return,'{finalized_generation}',to_jsonb((address+2)::text)),
  '{manifest_bytes_hex}',to_jsonb(encode(manifest.tree_bytes,'hex'))),'{manifest_sha256_hex}',to_jsonb(encode(manifest.semantic_sha256,'hex')));
 IF to_jsonb(returned) IS DISTINCT FROM expected_return OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t WHERE record_send(t)=record_send(expected_parent)) THEN
  RAISE EXCEPTION 'full original manifest publication correspondence required' USING ERRCODE='55000'; END IF;
 PERFORM truss.runtime_require_catalog_finalization_composition_candidate(w,o,g);
 after_state:=truss.runtime_capture_finalizing_completion_state_candidate(w,o,g);
 expected_state:=jsonb_set(expected_state,'{stores,feed_tx}',jsonb_build_array(encode(record_send(expected_parent),'hex')));
 expected_state:=jsonb_set(expected_state,'{stores,feed_member}',jsonb_build_array(encode(record_send(expected_member),'hex')));
 IF after_state IS DISTINCT FROM expected_state
  OR (SELECT count(*) FROM truss.row_home_operation)<>1 OR NOT EXISTS(SELECT 1 FROM truss.row_home_operation t WHERE record_send(t)=original_operation)
  OR (SELECT count(*) FROM truss.operation_configuration)<>1 OR NOT EXISTS(SELECT 1 FROM truss.operation_configuration t WHERE record_send(t)=original_configuration)
  OR (SELECT count(*) FROM truss.catalog_revision_custody)<>1 OR NOT EXISTS(SELECT 1 FROM truss.catalog_revision_custody t WHERE record_send(t)=original_custody)
  OR (SELECT count(*) FROM truss.feed_tx)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_tx t WHERE record_send(t)=record_send(expected_parent))
  OR (SELECT count(*) FROM truss.feed_member)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_member t WHERE record_send(t)=record_send(expected_member))
  OR (SELECT count(*) FROM truss.feed_configuration_prerequisite)<>1 OR NOT EXISTS(SELECT 1 FROM truss.feed_configuration_prerequisite t WHERE record_send(t)=record_send(cfgplan))
  OR (SELECT array_agg(record_send(p) ORDER BY p.prerequisite_address) FROM truss.feed_prerequisite p) IS DISTINCT FROM expected_docs THEN
  RAISE EXCEPTION 'complete finalization state delta required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT encode(manifest.tree_bytes,'hex'),encode(manifest.manifest_bytes,'hex'),encode(manifest.semantic_sha256,'hex'),(address+2)::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_finalize_original_catalog_feed_candidate(text,text,text) FROM PUBLIC;
