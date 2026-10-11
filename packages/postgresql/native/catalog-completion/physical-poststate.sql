-- Private administrative physical completion component. No semantic report
-- issuer, phase advancement, accepted publication or commit authority.
-- Concurrent administrative DDL and transitive routine/type/security dependency
-- closure are outside this qualification. SHARE locks exclude ordinary DML,
-- not all namespace/routine changes. Bounds cover retained materialized output,
-- not preallocation workspace or complete native resource accounting.
CREATE FUNCTION truss.runtime_capture_catalog_completion_physical(
 expected_writer text,expected_ordinal text,expected_generation text,revision int)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; name text; relation_oid oid;
 kind "char"; filtered boolean; row_count bigint; images jsonb;
 tables jsonb:='{}'::jsonb; descriptors jsonb:='{}'::jsonb; descriptor jsonb; total_bytes bigint:=0;
 names text[]:=ARRAY['schema_head','schema_rev','schema_doc','type_def','prop_def',
 'key_def','key_lifecycle_history','rel_def','rel_endpoint','relationship_lineage',
 'catalog_acceptance_report','object','edge','edge_limit','key_tombstone',
 'record_source','feed_consumer','journal','row_home_journal_stage','row_home_state',
 'row_home_node','row_home_scalar','row_home_touch','row_home_capacity',
 'key_bucket_guard','object_key_bucket','object_key_reservation_bucket','feed_tx',
 'feed_member','feed_prerequisite','feed_configuration_prerequisite',
 'complete_feed_consumer','complete_feed_administration_receipt',
 'complete_feed_seed_attempt','complete_feed_seed_artifact','key_migration_receipt',
 'request_receipt_route_guard','request_receipt','request_receipt_protection',
 'schema_change','setting','module_access','installation_marker',
 'installation_archive','installation_admission','row_home_operation'];
BEGIN
 IF current_user IS DISTINCT FROM session_user OR NOT EXISTS(
  SELECT 1 FROM pg_roles r WHERE r.rolname=current_user AND r.rolsuper) THEN
  RAISE EXCEPTION 'administrative physical observation only' USING ERRCODE='42501';
 END IF;
 IF current_setting('transaction_isolation')<>'read committed' THEN
  RAISE EXCEPTION 'fresh native statement snapshot required' USING ERRCODE='0A000';
 END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 IF NOT EXISTS(SELECT 1 FROM pg_proc p WHERE p.oid=to_regprocedure('truss.runtime_observe_catalog_generation()')
  AND NOT p.prosecdef AND p.provolatile='v' AND NOT p.proisstrict AND NOT p.proleakproof
  AND p.prorettype='pg_catalog.trigger'::regtype AND p.prolang=(SELECT l.oid FROM pg_language l WHERE l.lanname='plpgsql')
  AND p.proparallel='u' AND p.proconfig=ARRAY['search_path=pg_catalog, pg_temp']
  AND encode(sha256(convert_to(p.prosrc,'UTF8')),'hex')='0667ae15087aa60407a9b131a3cb5760d6e85a2fc01dc7646c98f509632a7a10')
  OR EXISTS(SELECT 1 FROM (VALUES ('schema_head'),('catalog_acceptance_report')) v(name)
   WHERE NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=to_regclass('truss.'||v.name)
    AND t.tgname='runtime_catalog_generation' AND t.tgfoid=to_regprocedure('truss.runtime_observe_catalog_generation()')
    AND t.tgtype=29 AND t.tgenabled='A' AND t.tgnargs=0 AND t.tgqual IS NULL AND NOT t.tgisinternal)) THEN
  RAISE EXCEPTION 'exact selected generation observer required' USING ERRCODE='55000';
 END IF;
 IF revision IS NULL OR revision<=0 OR NOT EXISTS(SELECT 1 FROM truss.schema_rev r WHERE r.rev=revision) THEN
  RAISE EXCEPTION 'actual staged revision required' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='truss' AND c.relkind IN ('r','p','f','v','m')
   AND NOT c.relname=ANY(names||ARRAY['row_home_operation'])) THEN
  RAISE EXCEPTION 'uncovered physical completion relation' USING ERRCODE='0A000';
 END IF;
 -- Acquire the entire selected exclusion before collecting any row image.
 FOREACH name IN ARRAY names LOOP
  relation_oid:=to_regclass(format('truss.%I',name));
  IF relation_oid IS NULL THEN RAISE EXCEPTION 'physical completion relation missing' USING ERRCODE='55000'; END IF;
  EXECUTE format('LOCK TABLE truss.%I IN SHARE MODE NOWAIT',name);
  SELECT c.relkind,c.relrowsecurity INTO STRICT kind,filtered FROM pg_class c WHERE c.oid=relation_oid;
  IF filtered OR (name='journal' AND (kind<>'p' OR pg_get_partkeydef(relation_oid) IS DISTINCT FROM 'RANGE (at)'))
   OR (name<>'journal' AND kind<>'r')
   OR EXISTS(SELECT 1 FROM pg_inherits i WHERE i.inhparent=relation_oid OR i.inhrelid=relation_oid) THEN
   RAISE EXCEPTION 'unsupported physical completion topology' USING ERRCODE='0A000';
  END IF;
 END LOOP;
 IF (SELECT count(*) FROM truss.schema_head)<>1 OR NOT EXISTS(SELECT 1 FROM truss.schema_head WHERE id=1) THEN
  RAISE EXCEPTION 'singleton physical head required' USING ERRCODE='55000';
 END IF;
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned();
 IF convert_from(op.original_input_bytes,'UTF8')::jsonb->'binding' IS DISTINCT FROM jsonb_build_object('state','absent')
  OR convert_from(op.original_input_bytes,'UTF8')::jsonb->'transforms' IS DISTINCT FROM '[]'::jsonb THEN
  RAISE EXCEPTION 'selected absent binding and no transform physical profile required' USING ERRCODE='0A000';
 END IF;
 IF (SELECT count(*) FROM truss.row_home_operation)<>1 THEN
  RAISE EXCEPTION 'one original component operation required' USING ERRCODE='55000';
 END IF;
 FOREACH name IN ARRAY names LOOP
  EXECUTE format('SELECT count(*) FROM truss.%I',name) INTO row_count;
  IF row_count>16384 THEN RAISE EXCEPTION 'physical row retention bound exceeded' USING ERRCODE='54000'; END IF;
  EXECUTE format('SELECT coalesce(jsonb_agg(image ORDER BY image COLLATE "C"),''[]''::jsonb) FROM (SELECT encode(record_send(r),''hex'') AS image FROM truss.%I r) s',name) INTO images;
  relation_oid:=to_regclass(format('truss.%I',name));
  SELECT jsonb_build_object(
   'relation',to_jsonb(c),
   'attributes',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.attnum),'[]'::jsonb) FROM pg_attribute a WHERE a.attrelid=relation_oid),
   'defaults',(SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.adnum),'[]'::jsonb) FROM pg_attrdef d WHERE d.adrelid=relation_oid),
   'constraints',(SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.oid),'[]'::jsonb) FROM pg_constraint k WHERE k.conrelid=relation_oid),
   'indexes',(SELECT coalesce(jsonb_agg(jsonb_build_object('index',to_jsonb(i),'relation',to_jsonb(ic),'definition',pg_get_indexdef(i.indexrelid)) ORDER BY i.indexrelid),'[]'::jsonb) FROM pg_index i JOIN pg_class ic ON ic.oid=i.indexrelid WHERE i.indrelid=relation_oid),
   'rules',(SELECT coalesce(jsonb_agg(to_jsonb(rw) ORDER BY rw.oid),'[]'::jsonb) FROM pg_rewrite rw WHERE rw.ev_class=relation_oid),
   'policies',(SELECT coalesce(jsonb_agg(to_jsonb(pol) ORDER BY pol.oid),'[]'::jsonb) FROM pg_policy pol WHERE pol.polrelid=relation_oid),
   'triggers',(SELECT coalesce(jsonb_agg(jsonb_build_object('trigger',to_jsonb(t),'procedure',to_jsonb(p),'function',pg_get_functiondef(t.tgfoid)) ORDER BY t.oid),'[]'::jsonb) FROM pg_trigger t JOIN pg_proc p ON p.oid=t.tgfoid WHERE t.tgrelid=relation_oid))
   INTO descriptor FROM pg_class c WHERE c.oid=relation_oid;
  descriptors:=descriptors||jsonb_build_object(name,descriptor);
  total_bytes:=total_bytes+octet_length(images::text)+octet_length(descriptor::text);
  IF total_bytes>16777216 THEN RAISE EXCEPTION 'physical image retention bound exceeded' USING ERRCODE='54000'; END IF;
  tables:=tables||jsonb_build_object(name,images);
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='truss' AND c.relkind IN ('r','p','f','v','m') AND NOT c.relname=ANY(names)) THEN
  RAISE EXCEPTION 'uncovered final physical completion relation' USING ERRCODE='0A000';
 END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 RETURN jsonb_build_object('interfaceVersion','truss-catalog-completion-physical/0.1',
  'writerXid',expected_writer,'operationOrdinal',expected_ordinal,
  'effectGeneration',expected_generation,'revision',revision::text,
  'head',(SELECT to_jsonb(h) FROM truss.schema_head h WHERE h.id=1),
  'operation',to_jsonb(op),'tables',tables,'descriptors',descriptors);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_capture_catalog_completion_physical(text,text,text,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_verify_catalog_completion_physical(
 expected_writer text,expected_ordinal text,expected_generation text,revision int,
 original_prestate jsonb,original_report bytea)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE fresh jsonb; expected_tables jsonb; planned_head truss.schema_head%ROWTYPE;
 planned_report truss.catalog_acceptance_report%ROWTYPE; report_images jsonb;
 old_generation bigint; planned_operation jsonb; planned_operation_row truss.row_home_operation%ROWTYPE;
BEGIN
 IF original_prestate IS NULL OR jsonb_typeof(original_prestate)<>'object'
  OR (SELECT count(*) FROM jsonb_object_keys(original_prestate))<>9
  OR NOT original_prestate ?& ARRAY['interfaceVersion','writerXid','operationOrdinal','effectGeneration','revision','head','operation','tables','descriptors']
  OR original_prestate->>'interfaceVersion' IS DISTINCT FROM 'truss-catalog-completion-physical/0.1'
  OR original_prestate->>'writerXid' IS DISTINCT FROM expected_writer
  OR original_prestate->>'operationOrdinal' IS DISTINCT FROM expected_ordinal
  OR original_prestate->>'revision' IS DISTINCT FROM revision::text
  OR original_prestate->>'effectGeneration' !~ '^(0|[1-9][0-9]{0,18})$'
  OR octet_length(original_prestate::text)>16777216
  OR original_report IS NULL OR octet_length(original_report) NOT BETWEEN 1 AND 4194304 THEN
  RAISE EXCEPTION 'complete retained physical component inputs required' USING ERRCODE='55000';
 END IF;
 old_generation:=(original_prestate->>'effectGeneration')::bigint;
 IF old_generation>9223372036854775805 OR expected_generation IS DISTINCT FROM (old_generation+2)::text THEN
  RAISE EXCEPTION 'fresh report and head event generation required' USING ERRCODE='55000';
 END IF;
 fresh:=truss.runtime_capture_catalog_completion_physical(expected_writer,expected_ordinal,expected_generation,revision);
 planned_head:=jsonb_populate_record(NULL::truss.schema_head,original_prestate->'head');
 IF planned_head.id IS DISTINCT FROM 1 OR planned_head.rev IS NULL OR planned_head.rev>=revision THEN
  RAISE EXCEPTION 'original unpublished singleton head required' USING ERRCODE='55000';
 END IF;
 planned_head.rev:=revision;
 planned_report.rev:=revision;planned_report.report_bytes:=original_report;
 expected_tables:=original_prestate->'tables';
 SELECT jsonb_agg(image ORDER BY image COLLATE "C") INTO report_images FROM (
  SELECT value AS image FROM jsonb_array_elements_text(expected_tables->'catalog_acceptance_report')
  UNION ALL SELECT encode(record_send(planned_report),'hex')) r;
 expected_tables:=expected_tables||jsonb_build_object(
  'schema_head',jsonb_build_array(encode(record_send(planned_head),'hex')),
  'catalog_acceptance_report',report_images);
 planned_operation:=(original_prestate->'operation')||jsonb_build_object(
  'effect_generation',old_generation+2,'phase','admitted','readiness_generation',NULL,
  'sealed_generation',NULL,'application_generation',NULL,'application_result_bytes',NULL);
 planned_operation_row:=jsonb_populate_record(NULL::truss.row_home_operation,planned_operation);
 expected_tables:=expected_tables||jsonb_build_object('row_home_operation',jsonb_build_array(encode(record_send(planned_operation_row),'hex')));
 IF fresh->'tables' IS DISTINCT FROM expected_tables
  OR fresh->'descriptors' IS DISTINCT FROM original_prestate->'descriptors'
  OR fresh->'operation' IS DISTINCT FROM planned_operation THEN
  RAISE EXCEPTION 'complete current physical completion correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN jsonb_build_object('scope','catalog_completion_physical_only',
  'writerXid',expected_writer,'operationOrdinal',expected_ordinal,
  'effectGeneration',expected_generation,'revision',revision::text,
  'acceptedReportQualified',false,'freshPhysicalState',fresh);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_verify_catalog_completion_physical(text,text,text,int,jsonb,bytea) FROM PUBLIC;

CREATE FUNCTION truss.runtime_capture_catalog_completion_prestate(
 expected_writer text,expected_ordinal text,expected_generation text,revision int)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb;
BEGIN
 result:=truss.runtime_capture_catalog_completion_physical(expected_writer,expected_ordinal,expected_generation,revision);
 IF (result->'head'->>'rev')::int>=revision
  OR EXISTS(SELECT 1 FROM truss.catalog_acceptance_report r WHERE r.rev=revision) THEN
  RAISE EXCEPTION 'unpublished head and absent target report required' USING ERRCODE='55000';
 END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_capture_catalog_completion_prestate(text,text,text,int) FROM PUBLIC;
