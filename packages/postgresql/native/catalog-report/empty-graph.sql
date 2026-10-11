-- Private first-catalog report evidence. Administrative empty-graph subset only.
-- Native exclusion lasts to host transaction end; no accepted report authority.
CREATE FUNCTION truss.runtime_collect_empty_catalog_graph()
RETURNS TABLE(writer_xid text,operation_ordinal text,effect_generation text,empty_scope text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER PARALLEL UNSAFE
SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; name text; relation_oid oid;
 kind "char"; populated boolean; filtered boolean;
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
 IF EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='truss' AND c.relkind IN ('r','p','f','v','m')
   AND NOT(c.relname=ANY(scope_names||ARRAY['setting','module_access','schema_rev',
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
 FOREACH name IN ARRAY scope_names LOOP
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
 RETURN QUERY SELECT op.original_writer_xid::text,op.operation_ordinal::text,
  op.effect_generation::text,to_jsonb(scope_names)::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_empty_catalog_graph() FROM PUBLIC;
