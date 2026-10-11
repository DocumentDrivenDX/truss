-- Configured first-catalog graph/metadata correspondence. Administrative component only.
-- Native exclusion lasts to host transaction end; no accepted report authority.
CREATE FUNCTION truss.runtime_collect_configured_catalog_graph()
RETURNS TABLE(writer_xid text,operation_ordinal text,effect_generation text,empty_scope text,metadata_source text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER PARALLEL UNSAFE
SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; name text; relation_oid oid;
 kind "char"; populated boolean; filtered boolean; context jsonb; configuration truss.operation_configuration%ROWTYPE;
 metadata jsonb;
 metadata_names text[]:=ARRAY['source_epoch_registry','source_epoch_current','operation_configuration','installation_admission'];
 scope_names text[]:=ARRAY['object','edge','edge_limit','key_tombstone','record_source',
 'feed_consumer','journal','row_home_journal_stage','row_home_state','row_home_node',
 'row_home_scalar','row_home_touch','row_home_capacity','key_bucket_guard',
 'object_key_bucket','object_key_reservation_bucket','feed_tx','feed_member',
 'feed_prerequisite','feed_configuration_prerequisite','complete_feed_consumer',
 'complete_feed_administration_receipt','complete_feed_seed_attempt',
 'complete_feed_seed_artifact','key_lifecycle_history','key_migration_receipt',
 'request_receipt_route_guard','request_receipt','request_receipt_protection',
 'schema_change'];
BEGIN
 IF pg_catalog.current_setting('transaction_isolation')<>'read committed' THEN
  RAISE EXCEPTION 'fresh statement snapshots required for empty graph evidence' USING ERRCODE='0A000';
 END IF;
 IF current_user IS DISTINCT FROM session_user OR NOT EXISTS(
  SELECT 1 FROM pg_roles r WHERE r.rolname=current_user AND r.rolsuper) THEN
  RAISE EXCEPTION 'administrative original visible graph profile required' USING ERRCODE='42501';
 END IF;
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized';
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted'
  OR (SELECT count(*) FROM truss.row_home_operation)<>1 THEN
  RAISE EXCEPTION 'one original fresh catalog operation required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted
  AND l.relation='truss.schema_head'::regclass AND l.mode IN ('ExclusiveLock','AccessExclusiveLock')) THEN
  RAISE EXCEPTION 'original catalog exclusion required' USING ERRCODE='55000';
 END IF;
 -- Metadata is an explicit native correspondence producer, never an exemption
 -- selected by a caller flag. All application graph homes remain empty.
 SELECT * INTO STRICT configuration FROM truss.operation_configuration c
  WHERE c.original_writer_xid=op.original_writer_xid AND c.operation_ordinal=op.operation_ordinal;
 context:=convert_from(op.original_context_bytes,'UTF8')::jsonb;
 IF context->>'interfaceVersion' IS DISTINCT FROM 'truss-native-operation-context/0.4' THEN
  RAISE EXCEPTION 'original configured context required' USING ERRCODE='55000';
 END IF;
 PERFORM truss.runtime_require_operation_configuration_current(
  op.original_writer_xid::text,op.operation_ordinal::text,op.effect_generation::text);
 IF EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='truss' AND c.relkind IN ('r','p','f','v','m')
   AND NOT(c.relname=ANY(scope_names||metadata_names||ARRAY['setting','module_access','schema_rev',
    'schema_head','schema_doc','type_def','prop_def','key_def','rel_def','rel_endpoint',
    'row_home_operation','relationship_lineage','catalog_acceptance_report',
    'installation_marker','installation_archive','installation_admission']))) THEN
  RAISE EXCEPTION 'uncovered physical graph scope' USING ERRCODE='0A000';
 END IF;
 IF op.effect_generation=0 AND EXISTS(SELECT 1 FROM pg_locks l
  JOIN pg_class c ON c.oid=l.relation JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE l.pid=pg_backend_pid() AND l.granted AND l.mode IN ('RowExclusiveLock','ShareRowExclusiveLock','ExclusiveLock','AccessExclusiveLock')
   AND n.nspname='truss' AND c.relname=ANY(scope_names)) THEN
  RAISE EXCEPTION 'earlier graph writes cannot become an empty original start cut' USING ERRCODE='55000';
 END IF;
 -- First acquire every participating native relation lock, then inspect emptiness.
 -- NOWAIT refuses a competing raw writer instead of waiting/retrying.
 FOREACH name IN ARRAY scope_names||metadata_names LOOP
  relation_oid:=to_regclass(format('truss.%I',name));
  IF relation_oid IS NULL THEN
   RAISE EXCEPTION 'complete selected graph relation missing' USING ERRCODE='55000';
  END IF;
  EXECUTE format('LOCK TABLE truss.%I IN SHARE MODE NOWAIT',name);
  SELECT c.relkind,c.relrowsecurity INTO STRICT kind,filtered FROM pg_class c WHERE c.oid=relation_oid;
  IF filtered OR (name='journal' AND (kind<>'p' OR pg_get_partkeydef(relation_oid) IS DISTINCT FROM 'RANGE (at)'))
   OR (name<>'journal' AND kind<>'r')
   OR EXISTS(SELECT 1 FROM pg_inherits i WHERE i.inhparent=relation_oid OR i.inhrelid=relation_oid) THEN
   RAISE EXCEPTION 'selected ordinary graph and empty journal root topology required' USING ERRCODE='0A000';
  END IF;
 END LOOP;
 FOREACH name IN ARRAY scope_names LOOP
  EXECUTE format('SELECT EXISTS(SELECT 1 FROM truss.%I)',name) INTO populated;
  IF populated THEN
   RAISE EXCEPTION 'nonempty graph needs original before/after effect report producer' USING ERRCODE='0A000';
  END IF;
 END LOOP;
 -- Acquire metadata table cuts before inspecting complete cardinality. The
 -- original current-context collector independently checks bytes/actor/epoch.
 IF (SELECT count(*) FROM truss.source_epoch_registry)<>1
  OR (SELECT count(*) FROM truss.source_epoch_current)<>1
  OR (SELECT count(*) FROM truss.operation_configuration)<>1
  OR (SELECT count(*) FROM truss.installation_admission)<>1
  OR NOT EXISTS(SELECT 1 FROM truss.source_epoch_registry r
    WHERE r.installation_id=configuration.installation_id AND r.source_epoch=configuration.source_epoch
     AND r.target_incarnation=configuration.target_incarnation AND r.transition_reason='initial'
     AND r.predecessor_epoch IS NULL AND encode(r.profile_bytes,'hex')=context->>'sourceEpochProfileHex'
     AND encode(r.evidence_bytes,'hex')=context->>'sourceEpochEvidenceHex'
     AND r.evidence_sha256=sha256(r.evidence_bytes))
  OR NOT EXISTS(SELECT 1 FROM truss.source_epoch_current c WHERE c.singleton_id=1
    AND c.installation_id=configuration.installation_id AND c.source_epoch=configuration.source_epoch) THEN
  RAISE EXCEPTION 'complete original first-installation metadata correspondence required' USING ERRCODE='55000';
 END IF;
 PERFORM truss.runtime_require_operation_configuration_current(
  op.original_writer_xid::text,op.operation_ordinal::text,op.effect_generation::text);
 metadata:=jsonb_build_object('interfaceVersion','truss-configured-catalog-metadata/0.1',
  'installationId',configuration.installation_id,'sourceEpoch',configuration.source_epoch,
  'targetIncarnation',configuration.target_incarnation,
  'configurationGeneration',configuration.configuration_generation::text,
  'contextSha256',encode(sha256(op.original_context_bytes),'hex'),
  'configurationSha256',encode(configuration.configuration_sha256,'hex'),
  'selectedBindingSha256',encode(configuration.selected_binding_sha256,'hex'),
  'installedInventorySha256',encode(configuration.installed_inventory_sha256,'hex'),
  'epochProfileSha256',encode(sha256(decode(context->>'sourceEpochProfileHex','hex')),'hex'),
  'epochEvidenceSha256',encode(sha256(decode(context->>'sourceEpochEvidenceHex','hex')),'hex'));
 RETURN QUERY SELECT op.original_writer_xid::text,op.operation_ordinal::text,
  op.effect_generation::text,to_jsonb(scope_names)::text,metadata::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_configured_catalog_graph() FROM PUBLIC;
