-- Original declared report inputs in the installation archive, not installed
-- implementation/authority qualification. Identity is the exact release path.
CREATE FUNCTION truss.runtime_select_catalog_report_resources(
 expected_writer text,expected_ordinal text,expected_generation text,
 expected_configuration_profile_hex text)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE selected record; context jsonb; policy jsonb; item jsonb; row record;
 manifest jsonb:='[]'::jsonb; total bigint:=0; matches bigint;
BEGIN
 -- This original selector acquires the archive table cut before any lookup.
 SELECT * INTO STRICT selected FROM truss.runtime_select_catalog_report_release(
  expected_writer,expected_ordinal,expected_generation,expected_configuration_profile_hex);
 SELECT convert_from(o.original_context_bytes,'UTF8')::jsonb INTO STRICT context
 FROM truss.row_home_operation o WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
  AND o.operation_ordinal::text=expected_ordinal AND o.phase='admitted';
 policy:=convert_from(decode(selected.policy_hex,'hex'),'UTF8')::jsonb;
 IF jsonb_typeof(policy->'resources') IS DISTINCT FROM 'array'
  OR jsonb_array_length(policy->'resources') NOT BETWEEN 1 AND 256
  OR (SELECT count(DISTINCT convert_to(r->>'path','UTF8')) FROM jsonb_array_elements(policy->'resources') r)
       <>jsonb_array_length(policy->'resources') THEN
  RAISE EXCEPTION 'complete unambiguous original report resource declarations required' USING ERRCODE='55000';
 END IF;
 FOR item IN SELECT value FROM jsonb_array_elements(policy->'resources') LOOP
  IF jsonb_typeof(item) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(item))<>2
   OR NOT item ?& ARRAY['path','sha256'] OR jsonb_typeof(item->'path') IS DISTINCT FROM 'string'
   OR octet_length(item->>'path') NOT BETWEEN 1 AND 4096
   OR jsonb_typeof(item->'sha256') IS DISTINCT FROM 'string' OR item->>'sha256' !~ '^[0-9a-f]{64}$' THEN
   RAISE EXCEPTION 'closed original report resource declaration required' USING ERRCODE='55000';
  END IF;
  SELECT count(*) INTO matches FROM truss.installation_archive a
   WHERE convert_to(a.installation_id,'UTF8')=convert_to(context->>'installationId','UTF8')
    AND a.artifact_role COLLATE pg_catalog."C"='input'
    AND convert_to(a.artifact_identity,'UTF8')=convert_to(item->>'path','UTF8');
  IF matches<>1 THEN
   RAISE EXCEPTION 'unique original report resource archive required' USING ERRCODE='55000';
  END IF;
  -- Preflight the retained byte sizes before materializing and hashing the row.
  SELECT a.archive_row_id,octet_length(a.artifact_bytes)::bigint AS size INTO STRICT row
   FROM truss.installation_archive a WHERE convert_to(a.installation_id,'UTF8')=convert_to(context->>'installationId','UTF8')
    AND a.artifact_role COLLATE pg_catalog."C"='input'
    AND convert_to(a.artifact_identity,'UTF8')=convert_to(item->>'path','UTF8') FOR SHARE NOWAIT;
  IF row.size NOT BETWEEN 1 AND 1048576 OR total+row.size>4194304 THEN
   RAISE EXCEPTION 'original report resource retained byte capacity exceeded' USING ERRCODE='54000';
  END IF;
  total:=total+row.size;
  IF NOT EXISTS(SELECT 1 FROM truss.installation_archive a WHERE a.archive_row_id=row.archive_row_id
   AND a.artifact_sha256=decode(item->>'sha256','hex') AND a.artifact_sha256=sha256(a.artifact_bytes)
   AND a.artifact_identity_sha256=sha256(convert_to(item->>'path','UTF8'))) THEN
   RAISE EXCEPTION 'original report resource digest correspondence required' USING ERRCODE='55000';
  END IF;
  manifest:=manifest||jsonb_build_array(jsonb_build_object('path',item->>'path',
   'sha256',item->>'sha256','archiveRowId',row.archive_row_id::text,'bytes',row.size::text));
 END LOOP;
 PERFORM truss.runtime_require_operation_configuration_current(expected_writer,expected_ordinal,expected_generation);
 RETURN jsonb_build_object('interfaceVersion','truss-catalog-report-resources/0.1',
  'scope','original_declared_archive_inputs_only','writerXid',expected_writer,
  'operationOrdinal',expected_ordinal,'configurationGeneration',selected.configuration_generation,
  'releaseSha256',selected.policy_sha256,'resources',manifest,'totalBytes',total::text);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_select_catalog_report_resources(text,text,text,text) FROM PUBLIC;
