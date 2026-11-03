-- SPDX-License-Identifier: MIT OR Apache-2.0
-- F8 noncompact2.1 inverse correspondence. Unenrolled until native0.76 closure.
-- UMF owns access meaning: this consumes the retained owner result, never
-- resolves extensions or infers temporal kind from a timestamp declaration.
CREATE FUNCTION truss.catalog_temporal_pointer(source jsonb,pointer text) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE part text;value jsonb:=source;decoded text;
BEGIN
 IF pointer IS NULL OR left(pointer,1)<>'/' THEN RAISE EXCEPTION 'original owner pointer required' USING ERRCODE='22023';END IF;
 FOREACH part IN ARRAY string_to_array(substring(pointer,2),'/') LOOP
  IF replace(replace(part,'~0',''),'~1','') LIKE '%~%' THEN RAISE EXCEPTION 'valid owner pointer required' USING ERRCODE='22023';END IF;
  decoded:=replace(replace(part,'~1','/'),'~0','~');
  IF jsonb_typeof(value)='array' THEN
   IF decoded !~ '^(0|[1-9][0-9]*)$' OR length(decoded)>9 THEN RAISE EXCEPTION 'canonical bounded owner array pointer required' USING ERRCODE='22023';END IF;
   value:=value->decoded::int;
  ELSIF jsonb_typeof(value)='object' THEN value:=value->decoded;
  ELSE RAISE EXCEPTION 'original owner pointer target required' USING ERRCODE='22023';END IF;
  IF value IS NULL THEN RAISE EXCEPTION 'original owner pointer target required' USING ERRCODE='22023';END IF;
 END LOOP;
 RETURN value;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_temporal_pointer(jsonb,text) FROM PUBLIC;

CREATE FUNCTION truss.catalog_temporal_declarations_valid(documents jsonb,declarations jsonb,summary jsonb) RETURNS void
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE document jsonb;decl jsonb;entry jsonb;packet jsonb;source jsonb;owner jsonb;
 record_decl jsonb;record_view jsonb;field_decl jsonb;field_view jsonb;authored jsonb;authored_record jsonb;authored_view jsonb;
 expected_descriptor jsonb;doc_count int;doc_index int;record_index int;field_index int;source_hash text;record_refs jsonb;
BEGIN
 IF jsonb_typeof(documents) IS DISTINCT FROM 'array' OR jsonb_typeof(declarations) IS DISTINCT FROM 'array'
  OR summary->>'interfaceVersion' IS DISTINCT FROM 'truss-registration-preparation/2.1'
  OR summary-ARRAY['interfaceVersion','documents']<>'{}'::jsonb OR jsonb_typeof(summary->'documents') IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'complete noncompact temporal preparation required' USING ERRCODE='22023';END IF;
 doc_count:=jsonb_array_length(documents);
 IF doc_count NOT BETWEEN 1 AND 512 OR jsonb_array_length(declarations)<>doc_count OR jsonb_array_length(summary->'documents')<>doc_count THEN
  RAISE EXCEPTION 'complete temporal document coverage required' USING ERRCODE='22023';END IF;
 FOR doc_index IN 0..doc_count-1 LOOP
  document:=documents->doc_index;decl:=declarations->doc_index;entry:=summary->'documents'->doc_index;packet:=entry->'inspection';
  IF jsonb_typeof(document->'originalText') IS DISTINCT FROM 'string' OR jsonb_typeof(packet) IS DISTINCT FROM 'object'
   OR packet-ARRAY['operation','ownerProfile','documentId','revision','contentSha256','selected','bindings','sourceId','resultJson','resultSha256']<>'{}'::jsonb
   OR packet->>'operation' IS DISTINCT FROM 'inspectAccessViews' OR packet->>'documentId' IS DISTINCT FROM document->>'documentId'
   OR packet->>'revision' IS DISTINCT FROM document->>'revision' OR entry->>'documentId' IS DISTINCT FROM document->>'documentId'
   OR jsonb_typeof(packet->'resultJson') IS DISTINCT FROM 'string' OR octet_length(packet->>'resultJson') NOT BETWEEN 1 AND 4194304 THEN
   RAISE EXCEPTION 'original temporal inspection invocation required' USING ERRCODE='22023';END IF;
  source_hash:=encode(sha256(convert_to(document->>'originalText','UTF8')),'hex');
  IF packet->>'contentSha256' IS DISTINCT FROM source_hash OR entry->>'contentSha256' IS DISTINCT FROM source_hash
   OR packet->>'resultSha256' IS DISTINCT FROM encode(sha256(convert_to(packet->>'resultJson','UTF8')),'hex') THEN
   RAISE EXCEPTION 'original temporal source and owner result digests required' USING ERRCODE='22023';END IF;
  IF packet->'ownerProfile' IS NULL OR jsonb_typeof(packet->'ownerProfile') IS DISTINCT FROM 'object'
   OR (packet->'ownerProfile')-ARRAY['identity','version','sha256']<>'{}'::jsonb
   OR jsonb_typeof(packet->'ownerProfile'->'identity') IS DISTINCT FROM 'string'
   OR jsonb_typeof(packet->'ownerProfile'->'version') IS DISTINCT FROM 'string'
   OR (packet->'ownerProfile'->>'sha256' ~ '^[0-9a-f]{64}$') IS NOT TRUE
   OR jsonb_typeof(packet->'bindings') IS DISTINCT FROM 'array' OR jsonb_typeof(packet->'sourceId') IS DISTINCT FROM 'string' THEN
   RAISE EXCEPTION 'exact original inspection profile and invocation required' USING ERRCODE='22023';END IF;
  source:=(document->>'originalText')::jsonb;owner:=(packet->>'resultJson')::jsonb;
  IF jsonb_typeof(owner->'records') IS DISTINCT FROM 'array' OR jsonb_typeof(owner->'diagnostics') IS DISTINCT FROM 'array'
   OR EXISTS(SELECT 1 FROM jsonb_array_elements(owner->'diagnostics') d WHERE jsonb_typeof(d.value)<>'object' OR d.value->>'severity' IN ('error','fatal'))
   OR jsonb_typeof(decl->'records') IS DISTINCT FROM 'array' OR jsonb_typeof(packet->'selected') IS DISTINCT FROM 'array' THEN
   RAISE EXCEPTION 'complete admitted owner result required' USING ERRCODE='22023';END IF;
  SELECT coalesce(jsonb_agg(jsonb_build_object('module',m.value->>'id','element',e.value->>'id') ORDER BY m.ordinality,e.ordinality),'[]')
   INTO record_refs FROM jsonb_array_elements(source->'modules') WITH ORDINALITY m
   CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') WITH ORDINALITY e WHERE e.value->>'kind'='record';
  IF packet->'selected' IS DISTINCT FROM record_refs OR jsonb_array_length(owner->'records')<>jsonb_array_length(record_refs)
   OR jsonb_array_length(decl->'records')<>jsonb_array_length(record_refs) THEN
   RAISE EXCEPTION 'complete original Record inverse coverage required' USING ERRCODE='22023';END IF;
  FOR record_index IN 0..jsonb_array_length(record_refs)-1 LOOP
   record_decl:=decl->'records'->record_index;record_view:=owner->'records'->record_index;
   authored_record:=truss.catalog_temporal_pointer(source,record_view->>'pointer');
   IF record_view->'ref' IS DISTINCT FROM record_refs->record_index OR record_view->'selected' IS DISTINCT FROM 'true'::jsonb
    OR record_decl->'declaration' IS DISTINCT FROM authored_record OR record_decl->>'documentId' IS DISTINCT FROM document->>'documentId'
    OR record_decl->>'moduleId' IS DISTINCT FROM record_view->'ref'->>'module' OR record_decl->>'elementId' IS DISTINCT FROM record_view->'ref'->>'element'
    OR jsonb_typeof(authored_record->'members') IS DISTINCT FROM 'array' OR jsonb_typeof(record_view->'fields') IS DISTINCT FROM 'array'
    OR jsonb_typeof(record_decl->'fields') IS DISTINCT FROM 'array' THEN
    RAISE EXCEPTION 'original selected Record correspondence required' USING ERRCODE='22023';END IF;
   IF jsonb_array_length(record_view->'fields')<>jsonb_array_length(authored_record->'members') OR jsonb_array_length(record_decl->'fields')<>jsonb_array_length(authored_record->'members') THEN
    RAISE EXCEPTION 'complete original Field inverse coverage required' USING ERRCODE='22023';END IF;
   FOR field_index IN 0..jsonb_array_length(authored_record->'members')-1 LOOP
    field_decl:=record_decl->'fields'->field_index;field_view:=record_view->'fields'->field_index;
    authored:=truss.catalog_temporal_pointer(source,field_view->>'pointer');
    IF field_view->'ref' IS DISTINCT FROM authored_record->'members'->field_index OR field_decl->'reference' IS DISTINCT FROM field_view->'ref'
     OR field_decl->'declaration' IS DISTINCT FROM authored OR field_decl->>'fieldModule' IS DISTINCT FROM field_view->'ref'->>'module'
     OR field_decl->>'fieldId' IS DISTINCT FROM field_view->'ref'->>'element' OR field_view->>'scalarType' IS DISTINCT FROM authored->>'scalarType' THEN
     RAISE EXCEPTION 'exact original Field and owner correspondence required' USING ERRCODE='22023';END IF;
    IF field_view->>'scalarType'='date' OR field_view->>'temporal' IN ('instant','local') THEN
     IF authored->>'cardinality' IS DISTINCT FROM 'one' OR coalesce(authored->'facets','{}')<>'{}'::jsonb
      OR authored ? 'allowedValues' OR authored ? 'default' THEN
      RAISE EXCEPTION 'selected temporal refinements and containers are unsupported' USING ERRCODE='0A000';END IF;
     IF EXISTS(SELECT 1 FROM jsonb_array_elements(coalesce(authored_record->'keys','[]')) k
      CROSS JOIN LATERAL jsonb_array_elements(k.value->'fields') f WHERE f.value=field_view->'ref') THEN
      RAISE EXCEPTION 'temporal Key fields are outside selected profile' USING ERRCODE='0A000';END IF;
     authored_view:=truss.catalog_temporal_pointer(source,field_view->>'viewPointer');
     IF authored_view->'field' IS DISTINCT FROM field_view->'ref' OR authored_view->'row' IS DISTINCT FROM field_view->'row'
      OR jsonb_typeof(field_view->'row') IS DISTINCT FROM 'object' OR (field_view->'row')-ARRAY['missing','null']<>'{}'::jsonb
      OR jsonb_typeof(field_view->'row'->'missing') IS DISTINCT FROM 'boolean' OR jsonb_typeof(field_view->'row'->'null') IS DISTINCT FROM 'boolean' THEN
      RAISE EXCEPTION 'original temporal FieldView presence required' USING ERRCODE='22023';END IF;
    END IF;
    IF field_view->>'temporal'='local' THEN
     authored_view:=truss.catalog_temporal_pointer(source,field_view->>'viewPointer');
     IF authored->>'scalarType' IS DISTINCT FROM 'timestamp' OR authored->>'cardinality' IS DISTINCT FROM 'one'
      OR authored_view->'field' IS DISTINCT FROM field_view->'ref' OR authored_view->'row' IS DISTINCT FROM field_view->'row' THEN
      RAISE EXCEPTION 'exact local FieldView source required' USING ERRCODE='22023';END IF;
     expected_descriptor:=jsonb_build_object('nativeScalarType','localTimestamp','nativeTemporal',jsonb_build_object(
      'profile','truss.local-timestamp/0.1','kind','local','source',jsonb_build_object('documentId',document->>'documentId','sha256',source_hash,
       'record',record_view->'ref','field',field_view->'ref','fieldViewPointer',field_view->>'viewPointer')));
     IF field_decl->'nativeDescriptor' IS DISTINCT FROM expected_descriptor THEN
      RAISE EXCEPTION 'exact local native descriptor required' USING ERRCODE='22023';END IF;
    ELSIF field_decl ? 'nativeDescriptor' THEN
     RAISE EXCEPTION 'native descriptor requires retained owner local selection' USING ERRCODE='22023';
    END IF;
   END LOOP;
  END LOOP;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_temporal_declarations_valid(jsonb,jsonb,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_temporal_support_profile() RETURNS jsonb
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ SELECT '{"identity":"truss-fresh-catalog-temporal-support","version":"0.2","sha256":"d73dee86befef723470855eab7baacf25ce90ee0b578b140377f23780352f779"}'::jsonb; $$;
REVOKE ALL ON FUNCTION truss.catalog_temporal_support_profile() FROM PUBLIC;
