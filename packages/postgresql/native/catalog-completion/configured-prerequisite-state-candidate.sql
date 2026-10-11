-- Administrative complete non-feed row/metadata cut; no acceptance authority.
CREATE FUNCTION truss.runtime_capture_configured_prerequisite_state_candidate(w text,o text,g text)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb; stores jsonb:='{}'; rows jsonb; name text; metadata bytea; resources jsonb; profile_hex text;
BEGIN
 PERFORM truss.runtime_require_catalog_observation(w,o,g);
 PERFORM truss.runtime_require_operation_configuration_current(w,o,g);
 PERFORM truss.runtime_require_selected_archive_write_fence();
 SELECT encode(c.admission_profile_bytes,'hex') INTO STRICT profile_hex FROM truss.operation_configuration c
  WHERE c.original_writer_xid=pg_current_xact_id_if_assigned() AND c.operation_ordinal::text=o;
 resources:=truss.runtime_select_catalog_report_resources(w,o,g,profile_hex);
 metadata:=truss.runtime_capture_catalog_metadata_cut(w,o,g);
 PERFORM truss.runtime_require_catalog_observation(w,o,g);
 PERFORM truss.runtime_require_operation_configuration_current(w,o,g);
 PERFORM truss.runtime_require_selected_archive_write_fence();
 result:=jsonb_build_object('metadataHex',encode(metadata,'hex'),'resources',resources,
  'relations',(SELECT jsonb_agg(to_jsonb(c) ORDER BY c.oid) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'),
  'inheritance',(SELECT coalesce(jsonb_agg(to_jsonb(i) ORDER BY i.inhrelid,i.inhseqno),'[]'::jsonb) FROM pg_inherits i
   WHERE i.inhparent IN (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss')
    OR i.inhrelid IN (SELECT c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss')));
 FOR name IN SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='truss' AND c.relkind IN ('r','p')
  AND c.relname NOT IN ('feed_tx','feed_prerequisite','feed_configuration_prerequisite') ORDER BY c.relname COLLATE "C" LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(encode(record_send(t),''hex'') ORDER BY encode(record_send(t),''hex'') COLLATE "C"),''[]''::jsonb) FROM ONLY truss.%I t',name) INTO rows;
  stores:=jsonb_set(stores,ARRAY[name],rows);
 END LOOP;
 result:=result||jsonb_build_object('stores',stores);
 IF octet_length(result::text)>16777216 THEN RAISE EXCEPTION 'configured prerequisite state capacity' USING ERRCODE='54000'; END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_capture_configured_prerequisite_state_candidate(text,text,text) FROM PUBLIC;
