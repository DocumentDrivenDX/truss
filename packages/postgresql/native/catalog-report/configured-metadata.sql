-- Private pre-effect metadata correspondence, not installed-source authority.
-- Full original rows are retained locally; fixture identities are never promoted.
CREATE FUNCTION truss.runtime_capture_catalog_metadata_cut(expected_writer text,expected_ordinal text,expected_generation text)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE context jsonb; name text; result jsonb; original bytea;
BEGIN
 PERFORM truss.runtime_require_operation_configuration_current(expected_writer,expected_ordinal,expected_generation);
 SELECT convert_from(o.original_context_bytes,'UTF8')::jsonb INTO STRICT context
 FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
  AND o.operation_ordinal::text=expected_ordinal AND o.phase='admitted';
 FOREACH name IN ARRAY ARRAY['installation_marker','source_epoch_current','source_epoch_registry',
   'installation_admission','operation_configuration','installation_archive'] LOOP
  EXECUTE format('LOCK TABLE truss.%I IN SHARE MODE NOWAIT',name);
  IF NOT EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='truss' AND c.relname=name AND c.relkind='r' AND NOT c.relrowsecurity)
   OR EXISTS(SELECT 1 FROM pg_inherits i WHERE i.inhparent=to_regclass(format('truss.%I',name))
    OR i.inhrelid=to_regclass(format('truss.%I',name))) THEN
   RAISE EXCEPTION 'complete ordinary metadata topology required' USING ERRCODE='0A000';
  END IF;
 END LOOP;
 IF (SELECT count(*) FROM truss.installation_marker)<>1
  OR NOT EXISTS(SELECT 1 FROM truss.installation_marker m
   WHERE m.singleton_id=1 AND m.installation_id=context->>'installationId'
    AND m.marker_interface_version='truss-bootstrap-marker/0.1.0' AND m.schema_name='truss')
  OR (SELECT count(*) FROM truss.source_epoch_current)<>1
  OR (SELECT count(*) FROM truss.source_epoch_registry)<>1
  OR (SELECT count(*) FROM truss.installation_admission)<>1
  OR (SELECT count(*) FROM truss.operation_configuration)<>1 THEN
  RAISE EXCEPTION 'fresh original metadata identity correspondence required' USING ERRCODE='55000';
 END IF;
 -- Recheck exact unique release membership under the retained archive table lock.
 PERFORM * FROM truss.runtime_select_catalog_report_release(expected_writer,expected_ordinal,
  expected_generation,(SELECT encode(c.admission_profile_bytes,'hex')
   FROM truss.operation_configuration c WHERE c.original_writer_xid=pg_current_xact_id_if_assigned()
    AND c.operation_ordinal::text=expected_ordinal));
 -- Revalidate after acquiring all native locks. This retains exact current rows,
 -- including opaque inventory bytes; no invented inventory interpretation.
 PERFORM truss.runtime_require_operation_configuration_current(expected_writer,expected_ordinal,expected_generation);
 SELECT jsonb_build_object('interfaceVersion','truss-catalog-metadata-cut/0.1',
  'marker',(SELECT to_jsonb(m) FROM truss.installation_marker m),
  'pointer',(SELECT to_jsonb(c) FROM truss.source_epoch_current c),
  'epoch',(SELECT to_jsonb(e) FROM truss.source_epoch_registry e),
  'configuration',(SELECT to_jsonb(c) FROM truss.operation_configuration c),
  'admission',(SELECT to_jsonb(a) FROM truss.installation_admission a),
  'releaseArchive',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.archive_row_id),'[]'::jsonb)
    FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
      AND a.artifact_role='input' AND a.artifact_identity='truss.catalog-report-release/0.1.0')) INTO result;
 original:=convert_to(result::text,'UTF8');
 IF octet_length(original)>32768 THEN
  RAISE EXCEPTION 'private original metadata response capacity' USING ERRCODE='54000';
 END IF;
 RETURN original;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_capture_catalog_metadata_cut(text,text,text) FROM PUBLIC;
