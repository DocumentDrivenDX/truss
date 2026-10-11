CREATE FUNCTION truss.runtime_capture_configured_completion_state_candidate(w text, o text, g text) RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE result jsonb; stores jsonb:='{}'; rows jsonb; name text; oid_value oid;
 descriptors jsonb:='{}'; descriptor jsonb; metadata bytea; resources jsonb; profile_hex text;
BEGIN
 IF current_user IS DISTINCT FROM session_user OR NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=current_user AND rolsuper)
  OR current_setting('transaction_isolation')<>'read committed' THEN
  RAISE EXCEPTION 'administrative fresh configured completion only' USING ERRCODE='42501'; END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_proc p WHERE p.oid=to_regprocedure('truss.runtime_observe_catalog_generation()')
  AND NOT p.prosecdef AND p.provolatile='v' AND NOT p.proisstrict AND NOT p.proleakproof
  AND p.prorettype='pg_catalog.trigger'::regtype AND p.prolang=(SELECT l.oid FROM pg_language l WHERE l.lanname='plpgsql')
  AND p.proparallel='u' AND p.proconfig=ARRAY['search_path=pg_catalog, pg_temp']
  AND encode(sha256(convert_to(p.prosrc,'UTF8')),'hex')='50e70fa7cb99454c0104e5e9d14858ba0e8b664cecd3680281173fcdb3d1ca59')
  OR EXISTS(SELECT 1 FROM (VALUES ('schema_head'),('catalog_acceptance_report')) v(name)
   WHERE NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=to_regclass('truss.'||v.name)
    AND t.tgname='runtime_catalog_generation' AND t.tgfoid=to_regprocedure('truss.runtime_observe_catalog_generation()')
    AND t.tgtype=29 AND t.tgenabled='A' AND t.tgnargs=0 AND t.tgqual IS NULL AND NOT t.tgisinternal)) THEN
  RAISE EXCEPTION 'exact selected generation observer required' USING ERRCODE='55000';
 END IF;
 PERFORM truss.runtime_require_catalog_observation(w,o,g);
 PERFORM truss.runtime_require_operation_configuration_current(w,o,g);
 PERFORM truss.runtime_require_selected_archive_write_fence();
 SELECT encode(c.admission_profile_bytes,'hex') INTO STRICT profile_hex FROM truss.operation_configuration c
  WHERE c.original_writer_xid=pg_current_xact_id_if_assigned() AND c.operation_ordinal::text=o;
 resources:=truss.runtime_select_catalog_report_resources(w,o,g,profile_hex);
 metadata:=truss.runtime_capture_catalog_metadata_cut(w,o,g);
 IF EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='truss' AND c.relkind IN ('f','v','m')) THEN
  RAISE EXCEPTION 'unsupported configured completion relation' USING ERRCODE='0A000'; END IF;
 IF EXISTS(SELECT 1 FROM pg_inherits i WHERE i.inhparent IN
  (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss')
  OR i.inhrelid IN (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss')) THEN
  RAISE EXCEPTION 'inheritance is outside fresh configured completion' USING ERRCODE='0A000'; END IF;
 FOR name IN SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='truss' AND c.relkind IN ('r','p') ORDER BY c.relname COLLATE "C" LOOP
  EXECUTE format('LOCK TABLE truss.%I IN SHARE MODE NOWAIT',name);
 END LOOP;
 FOR name,oid_value IN SELECT c.relname,c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='truss' AND c.relkind IN ('r','p') ORDER BY c.relname COLLATE "C" LOOP
  IF EXISTS(SELECT 1 FROM pg_class WHERE oid=oid_value AND relrowsecurity) THEN
   RAISE EXCEPTION 'unfiltered administrative completion rows required' USING ERRCODE='0A000'; END IF;
  EXECUTE format('SELECT coalesce(jsonb_agg(encode(record_send(t),''hex'') ORDER BY encode(record_send(t),''hex'') COLLATE "C"),''[]''::jsonb) FROM ONLY truss.%I t',name) INTO rows;
  stores:=jsonb_set(stores,ARRAY[name],rows);
  SELECT jsonb_build_object('relation',to_jsonb(c),
   'attributes',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.attnum),'[]'::jsonb) FROM pg_attribute a WHERE a.attrelid=oid_value),
   'defaults',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.adnum),'[]'::jsonb) FROM pg_attrdef a WHERE a.adrelid=oid_value),
   'constraints',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.oid),'[]'::jsonb) FROM pg_constraint a WHERE a.conrelid=oid_value),
   'indexes',(SELECT coalesce(jsonb_agg(jsonb_build_object('index',to_jsonb(a),'relation',to_jsonb(ic),'definition',pg_get_indexdef(a.indexrelid)) ORDER BY a.indexrelid),'[]'::jsonb) FROM pg_index a JOIN pg_class ic ON ic.oid=a.indexrelid WHERE a.indrelid=oid_value),
   'rules',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.oid),'[]'::jsonb) FROM pg_rewrite a WHERE a.ev_class=oid_value),
   'policies',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.oid),'[]'::jsonb) FROM pg_policy a WHERE a.polrelid=oid_value),
   'triggers',(SELECT coalesce(jsonb_agg(jsonb_build_object('trigger',to_jsonb(a),'procedure',to_jsonb(p),'function',pg_get_functiondef(a.tgfoid)) ORDER BY a.oid),'[]'::jsonb) FROM pg_trigger a JOIN pg_proc p ON p.oid=a.tgfoid WHERE a.tgrelid=oid_value))
   INTO descriptor FROM pg_class c WHERE c.oid=oid_value;
  descriptors:=jsonb_set(descriptors,ARRAY[name],descriptor);
  IF octet_length(stores::text)+octet_length(descriptors::text)>16777216 THEN
   RAISE EXCEPTION 'configured completion retention capacity' USING ERRCODE='54000'; END IF;
 END LOOP;
 result:=jsonb_build_object('stores',stores,'descriptors',descriptors,'resources',resources,'metadataHex',encode(metadata,'hex'),
  'relations',(SELECT jsonb_agg(to_jsonb(c) ORDER BY c.oid) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
  'routines',(SELECT jsonb_agg(jsonb_build_object('procedure',to_jsonb(p),'definition',pg_get_functiondef(p.oid)) ORDER BY p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND p.prokind IN ('f','p')),
  'namespace',(SELECT to_jsonb(n) FROM pg_namespace n WHERE n.nspname='truss'),
  'inheritance',(SELECT coalesce(jsonb_agg(to_jsonb(i) ORDER BY i.inhrelid,i.inhseqno),'[]'::jsonb) FROM pg_inherits i
   WHERE i.inhparent IN (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss')
    OR i.inhrelid IN (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss')));
 PERFORM truss.runtime_require_catalog_observation(w,o,g);
 PERFORM truss.runtime_require_operation_configuration_current(w,o,g);
 PERFORM truss.runtime_require_selected_archive_write_fence();
 IF octet_length(result::text)>16777216 THEN RAISE EXCEPTION 'configured completion total capacity' USING ERRCODE='54000'; END IF;
 RETURN result;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_capture_configured_completion_state_candidate(text, text, text) FROM public; CREATE FUNCTION truss.runtime_register_catalog_and_head_candidate(w text, o text, g text, registration_identity text, original_registration bytea, lifecycle_policy bytea, index_policy bytea) RETURNS TABLE (writer_xid text, operation_ordinal text, effect_generation text, revision text, report_utf8_hex text, scope text, accepted_report_qualified boolean, feed_qualified boolean) LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE produced record; before_state jsonb; after_state jsonb; expected_state jsonb;
 op truss.row_home_operation%ROWTYPE; planned_op truss.row_home_operation%ROWTYPE;
 old_head truss.schema_head%ROWTYPE; planned_head truss.schema_head%ROWTYPE; returned_head truss.schema_head%ROWTYPE;
 rev int; input jsonb;
BEGIN
 SELECT * INTO STRICT produced FROM truss.runtime_register_catalog_prerequisites_candidate(w,o,g,registration_identity,original_registration,lifecycle_policy,index_policy);
 SELECT t.* INTO STRICT op FROM truss.row_home_operation t WHERE t.original_writer_xid=pg_current_xact_id_if_assigned() AND t.operation_ordinal::text=o;
 input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 IF input->'binding' IS DISTINCT FROM jsonb_build_object('state','absent') OR input->'transforms' IS DISTINCT FROM '[]'::jsonb
  OR EXISTS(SELECT 1 FROM truss.rel_def WHERE definition_source_kind='operation_binding') THEN
  RAISE EXCEPTION 'unsupported pending binding or promotion completion' USING ERRCODE='0A000'; END IF;
 rev:=(convert_from(decode(produced.revision_payload_utf8_hex,'hex'),'UTF8')::jsonb->>'revision')::int;
 IF produced.effect_generation IS DISTINCT FROM op.effect_generation::text OR op.effect_generation=9223372036854775807 THEN
  RAISE EXCEPTION 'original bounded head generation required' USING ERRCODE='55000'; END IF;
 before_state:=truss.runtime_capture_configured_completion_state_candidate(w,o,produced.effect_generation);
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
 after_state:=truss.runtime_capture_configured_completion_state_candidate(w,o,planned_op.effect_generation::text);
 expected_state:=jsonb_set(before_state,ARRAY['stores','schema_head'],jsonb_build_array(encode(record_send(planned_head),'hex')));
 expected_state:=jsonb_set(expected_state,ARRAY['stores','row_home_operation'],jsonb_build_array(encode(record_send(planned_op),'hex')));
 IF after_state IS DISTINCT FROM expected_state THEN RAISE EXCEPTION 'complete configured post-head correspondence required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT w,o,planned_op.effect_generation::text,rev::text,produced.report_utf8_hex,
  'administrative_rollback_only_configured_head'::text,false,false;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_register_catalog_and_head_candidate(text, text, text, text, bytea, bytea, bytea) FROM public