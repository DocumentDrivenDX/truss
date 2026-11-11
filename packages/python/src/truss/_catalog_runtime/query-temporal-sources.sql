-- SPDX-License-Identifier: MIT OR Apache-2.0
-- F7 complete-source guards; candidate source, not enrolled by old native0.75.
CREATE FUNCTION truss.query_temporal_scope(binding jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_temporal_capability(binding->>'releaseId',binding->>'releaseSha256');
 PERFORM truss.query_scope_at_abi(binding,truss.query_temporal_abi());
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_scope(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.query_temporal_binding(selected_documents jsonb,maximum_scan_rows int,maximum_result_rows int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.require_temporal_capability(expected_release,expected_digest);
 RETURN truss.query_binding_at_abi(selected_documents,maximum_scan_rows,maximum_result_rows,maximum_bytes,expected_release,expected_digest,truss.query_temporal_abi());
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_binding(jsonb,int,int,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.query_temporal_requirements(binding jsonb,selected_type int,requirements jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE selected_record jsonb;source_doc truss.schema_doc%ROWTYPE;packet jsonb;owner_result jsonb;owner_record jsonb;owner_field jsonb;
 expected_fields jsonb:='[]';mapped_fields jsonb:='[]';identity jsonb;selected_field jsonb;property truss.prop_def%ROWTYPE;kind text;matches int;
BEGIN
 IF jsonb_typeof(requirements) IS DISTINCT FROM 'object' OR requirements-ARRAY['version','record','fields']<>'{}'::jsonb
  OR requirements->>'version' IS DISTINCT FROM 'truss.temporal-source-guard/0.2'
  OR jsonb_typeof(requirements->'fields') IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'complete closed temporal requirements required' USING ERRCODE='22023';END IF;
 SELECT count(*),(jsonb_agg(r.value)->0) INTO matches,selected_record FROM jsonb_array_elements(binding->'records') r WHERE r.value->>'typeId'=selected_type::text;
 IF matches<>1 OR selected_record->'identity' IS DISTINCT FROM requirements->'record' THEN
  RAISE EXCEPTION 'original selected temporal Record identity required' USING ERRCODE='22023';END IF;
 SELECT d.* INTO source_doc FROM truss.schema_doc d WHERE d.doc_id=selected_record->'identity'->>'documentId'
  AND d.doc_revision=selected_record->'identity'->>'revision' AND d.rev<=(binding->>'catalogRevision')::int ORDER BY d.rev DESC LIMIT 1;
 IF NOT FOUND OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'documents') d WHERE d.value->>'documentId'=source_doc.doc_id
  AND d.value->>'revision'=source_doc.doc_revision AND d.value->>'sha256'=source_doc.content_sha256) THEN
  RAISE EXCEPTION 'original temporal source changed' USING ERRCODE='55P03';END IF;
 packet:=source_doc.validation->'inspection';
 IF source_doc.validation->>'storageFormat' IS DISTINCT FROM 'truss-catalog-source/2.1'
  OR packet->>'operation' IS DISTINCT FROM 'inspectAccessViews' OR packet->>'documentId' IS DISTINCT FROM source_doc.doc_id
  OR packet->>'revision' IS DISTINCT FROM source_doc.doc_revision OR packet->>'contentSha256' IS DISTINCT FROM source_doc.content_sha256
  OR packet->>'resultSha256' IS DISTINCT FROM encode(sha256(convert_to(packet->>'resultJson','UTF8')),'hex') THEN
  RAISE EXCEPTION 'original admitted temporal owner custody required' USING ERRCODE='22023';END IF;
 owner_result:=(packet->>'resultJson')::jsonb;
 SELECT count(*),(jsonb_agg(r.value)->0) INTO matches,owner_record FROM jsonb_array_elements(owner_result->'records') r
  WHERE r.value->'ref'=jsonb_build_object('module',selected_record->'identity'->>'module','element',selected_record->'identity'->>'element');
 IF matches<>1 THEN RAISE EXCEPTION 'complete admitted owner Record required' USING ERRCODE='22023';END IF;
 FOR owner_field IN SELECT value FROM jsonb_array_elements(owner_record->'fields') LOOP
  kind:=CASE WHEN owner_field->>'scalarType'='date' THEN 'date'
   WHEN owner_field->>'scalarType'='timestamp' AND owner_field->>'temporal' IN ('instant','local') THEN owner_field->>'temporal' ELSE NULL END;
  IF owner_field->>'scalarType'='timestamp' AND kind IS NULL THEN
   RAISE EXCEPTION 'explicit admitted temporal kind required' USING ERRCODE='22023';END IF;
  IF kind IS NULL THEN CONTINUE;END IF;
  identity:=selected_record->'identity'||jsonb_build_object('module',owner_field->'ref'->>'module','element',owner_field->'ref'->>'element');
  SELECT count(*),(jsonb_agg(f.value)->0) INTO matches,selected_field FROM jsonb_array_elements(selected_record->'fields') f WHERE f.value->'identity'=identity;
  IF matches<>1 THEN RAISE EXCEPTION 'exact temporal native mapping required' USING ERRCODE='22023';END IF;
  SELECT * INTO property FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id=(selected_field->>'propertyId')::int AND p.retired_rev IS NULL;
  IF NOT FOUND OR property.scalar_type IS DISTINCT FROM (CASE kind WHEN 'local' THEN 'localTimestamp' WHEN 'instant' THEN 'timestamp' ELSE 'date' END)
   OR property.cardinality IS DISTINCT FROM 'one' OR coalesce(property.facets,'{}')<>'{}'::jsonb
   OR jsonb_typeof(owner_field->'row') IS DISTINCT FROM 'object'
   OR (owner_field->'row')-ARRAY['missing','null']<>'{}'::jsonb
   OR jsonb_typeof(owner_field->'row'->'missing') IS DISTINCT FROM 'boolean'
   OR jsonb_typeof(owner_field->'row'->'null') IS DISTINCT FROM 'boolean' THEN
   RAISE EXCEPTION 'original temporal family and row presence required' USING ERRCODE='22023';END IF;
  IF kind='local' THEN
   IF property.native_temporal IS DISTINCT FROM jsonb_build_object('profile','truss.local-timestamp/0.1','kind','local','source',
     jsonb_build_object('documentId',source_doc.doc_id,'sha256',source_doc.content_sha256,'record',owner_record->'ref',
      'field',owner_field->'ref','fieldViewPointer',owner_field->>'viewPointer')) THEN
    RAISE EXCEPTION 'original accepted native local source descriptor required' USING ERRCODE='22023';END IF;
  ELSIF property.native_temporal IS NOT NULL THEN
   RAISE EXCEPTION 'ordinary temporal family cannot inherit local descriptor' USING ERRCODE='22023';
  END IF;
  expected_fields:=expected_fields||jsonb_build_array(jsonb_build_object('field',identity,'kind',kind,'presence',owner_field->'row'));
  mapped_fields:=mapped_fields||jsonb_build_array(jsonb_build_object('propertyId',property.prop_id::text,'kind',kind,'presence',owner_field->'row'));
 END LOOP;
 IF expected_fields='[]'::jsonb OR requirements->'fields' IS DISTINCT FROM expected_fields THEN
  RAISE EXCEPTION 'all original temporal members exactly once in member order required' USING ERRCODE='22023';END IF;
 RETURN mapped_fields;
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_requirements(jsonb,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.query_temporal_objects(binding jsonb,selected_type int,requirements jsonb) RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE object_row truss.object%ROWTYPE;fields jsonb;field jsonb;cell jsonb;kind text;root_identity jsonb;roots jsonb:='{}';root_entry jsonb;
 row_count int:=0;byte_count bigint:=0;numeric_property record;
BEGIN
 PERFORM truss.query_temporal_scope(binding);
 fields:=truss.query_temporal_requirements(binding,selected_type,requirements);
 FOR object_row IN SELECT o.* FROM truss.object o WHERE o.type_id=selected_type ORDER BY o.id LIMIT (binding->>'maximumScanRows')::int+1 LOOP
  row_count:=row_count+1;byte_count:=byte_count+octet_length(object_row.props::text);
  IF row_count>(binding->>'maximumScanRows')::int OR byte_count>(binding->>'maximumBytes')::int THEN
   RAISE EXCEPTION 'complete bounded temporal source required' USING ERRCODE='54000';END IF;
  root_identity:=truss.query_object_root(binding,object_row);
  IF root_identity IS NOT NULL THEN roots:=roots||jsonb_build_object((root_identity->>'typeId')||':'||(root_identity->>'id'),root_identity);END IF;
  IF byte_count+(CASE WHEN roots='{}'::jsonb THEN 0 ELSE octet_length(roots::text) END)>(binding->>'maximumBytes')::int THEN
   RAISE EXCEPTION 'complete bounded temporal root witnesses required' USING ERRCODE='54000';END IF;
  IF object_row.ver<=0 OR object_row.rev>(binding->>'catalogRevision')::int THEN
   RAISE EXCEPTION 'complete current temporal source required' USING ERRCODE='0A000';END IF;
  FOR numeric_property IN SELECT p.prop_id,p.scalar_type FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.scalar_type IN ('integer','decimal') LOOP
   cell:=object_row.props->numeric_property.prop_id::text;
   IF cell IS NOT NULL AND cell<>'{"kind":"null"}'::jsonb AND truss.query_numeric_value(cell->>'text',numeric_property.scalar_type) IS NOT TRUE THEN
    RAISE EXCEPTION 'exact native numeric sibling domain unavailable' USING ERRCODE='22003';END IF;
  END LOOP;
  FOR field IN SELECT value FROM jsonb_array_elements(fields) LOOP
   cell:=object_row.props->(field->>'propertyId');kind:=field->>'kind';
   IF cell IS NULL THEN
    IF field->'presence'->'missing' IS DISTINCT FROM 'true'::jsonb THEN
     RAISE EXCEPTION 'required temporal source member missing' USING ERRCODE='22023';END IF;
   ELSIF cell='{"kind":"null"}'::jsonb THEN
    IF field->'presence'->'null' IS DISTINCT FROM 'true'::jsonb THEN
     RAISE EXCEPTION 'nonnullable temporal source member null' USING ERRCODE='22023';END IF;
   ELSE
    IF jsonb_typeof(cell) IS DISTINCT FROM 'object' OR jsonb_typeof(cell->'text') IS DISTINCT FROM 'string'
     OR cell IS DISTINCT FROM jsonb_build_object('kind',CASE kind WHEN 'local' THEN 'localTimestamp' WHEN 'instant' THEN 'timestamp' ELSE 'date' END,'text',cell->'text') THEN
     RAISE EXCEPTION 'exact original temporal source cell required' USING ERRCODE='22023';END IF;
    IF kind='local' AND truss.valid_local_timestamp_cell(cell) IS NOT TRUE THEN
     RAISE EXCEPTION 'canonical native local timestamp source required' USING ERRCODE='22023';END IF;
    PERFORM truss.query_temporal_canonical_text(kind,cell->>'text');
   END IF;
  END LOOP;
  -- PL/pgSQL's tuplestore buffers the complete function before the executor
  -- obtains its first row. No business filter/seek/limit enters this function.
  id:=object_row.id;props:=object_row.props;RETURN NEXT;
 END LOOP;
 FOR root_entry IN SELECT value FROM jsonb_each(roots) LOOP
  IF NOT truss.runtime_can_read(root_entry->'owner'->>'documentId',root_entry->'owner'->>'moduleId') THEN
   RAISE EXCEPTION 'current buffered temporal aggregate root reader required' USING ERRCODE='P1403';END IF;
 END LOOP;
 PERFORM truss.query_temporal_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_objects(jsonb,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.query_temporal_page_objects(binding jsonb,selected_type int,selected_key text,requirements jsonb) RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 PERFORM truss.query_temporal_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM truss.key_def k WHERE k.type_id=selected_type AND k.key_id=selected_key AND k.retired_rev IS NULL
  AND EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r CROSS JOIN LATERAL jsonb_array_elements(r.value->'keys') b
   WHERE r.value->>'typeId'=selected_type::text AND b.value->>'keyId'=k.key_id)) THEN
  RAISE EXCEPTION 'exact selected temporal native Key required' USING ERRCODE='22023';END IF;
 IF EXISTS(SELECT 1 FROM truss.key_def k CROSS JOIN LATERAL unnest(k.prop_ids) i(prop_id)
  LEFT JOIN truss.prop_def p ON p.type_id=k.type_id AND p.prop_id=i.prop_id AND p.retired_rev IS NULL
  WHERE k.type_id=selected_type AND k.key_id=selected_key AND k.retired_rev IS NULL
   AND (p.prop_id IS NULL OR p.scalar_type IS DISTINCT FROM 'string' OR p.cardinality IS DISTINCT FROM 'one'
    OR p.nullability IS DISTINCT FROM 'required' OR coalesce(p.facets,'{}')<>'{}'::jsonb)) THEN
  RAISE EXCEPTION 'complete required string temporal selected Key required' USING ERRCODE='0A000';END IF;
 RETURN QUERY SELECT * FROM truss.query_temporal_objects(binding,selected_type,requirements);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_page_objects(jsonb,int,text,jsonb) FROM PUBLIC;
