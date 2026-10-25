-- SPDX-License-Identifier: MIT OR Apache-2.0
-- ABI1.3 whole-source temporal guards. These functions validate the complete
-- bounded bag in the caller statement snapshot before returning any row.
CREATE FUNCTION truss.query_temporal_instant_key(token text) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE base text;fraction text;position_dot int;offset_text text;offset_minutes int:=0;whole_seconds bigint;
BEGIN
 IF token IS NULL OR octet_length(token)>128 OR token !~ '^[ -~]+$' THEN
  RAISE EXCEPTION 'bounded ASCII temporal instant required' USING ERRCODE='22023';END IF;
 IF token !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$'
  OR substring(token,1,4)::int=0 OR substring(token,12,2)::int>23
  OR substring(token,15,2)::int>59 OR substring(token,18,2)::int>59 THEN
  RAISE EXCEPTION 'finite known-offset instant required' USING ERRCODE='22023';END IF;
 IF right(token,1)='Z' THEN
  base:=left(token,length(token)-1);
 ELSE
  offset_text:=right(token,6);
  IF substring(offset_text,2,2)::int>23 OR substring(offset_text,5,2)::int>59
   OR offset_text='-00:00' THEN
   RAISE EXCEPTION 'known instant offset required' USING ERRCODE='22023';END IF;
  offset_minutes:=(substring(offset_text,2,2)::int*60+substring(offset_text,5,2)::int)
   * CASE WHEN left(offset_text,1)='-' THEN -1 ELSE 1 END;
  base:=left(token,length(token)-6);
 END IF;
 PERFORM make_date(substring(token,1,4)::int,substring(token,6,2)::int,substring(token,9,2)::int);
 position_dot:=position('.' in base);
 IF position_dot>0 THEN
  fraction:=substring(base from position_dot+1);
  IF length(fraction)>6 AND substring(fraction from 7) !~ '^0+$' THEN
   RAISE EXCEPTION 'instant precision exceeds exact microsecond subset' USING ERRCODE='22023';END IF;
 END IF;
 whole_seconds:=(make_date(substring(token,1,4)::int,substring(token,6,2)::int,substring(token,9,2)::int)-DATE '1970-01-01')::bigint*86400
  +substring(token,12,2)::int*3600+substring(token,15,2)::int*60+substring(token,18,2)::int-offset_minutes*60;
 IF whole_seconds < -62135596800 OR whole_seconds > 253402300799 THEN
  RAISE EXCEPTION 'UTC instant outside finite Gregorian range' USING ERRCODE='22023';END IF;
 RETURN truss.query_timestamp_instant_key(token,'umf-rfc3339-exact-instant/1.0.0');
EXCEPTION WHEN datetime_field_overflow OR invalid_text_representation THEN
 RAISE EXCEPTION 'Gregorian calendar instant required' USING ERRCODE='22023';
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_instant_key(text) FROM PUBLIC;

CREATE FUNCTION truss.query_temporal_requirements_valid(binding jsonb,selected_type int,requirements jsonb) RETURNS boolean
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE selected_record jsonb;requirement jsonb;field_identity jsonb;record_identity jsonb;property truss.prop_def%ROWTYPE;
 selected_field jsonb;source_doc truss.schema_doc%ROWTYPE;owner_access jsonb;owner_record jsonb;owner_field jsonb;matches int;kind text;
BEGIN
 IF binding->'queryAbi' IS DISTINCT FROM truss.query_temporal_abi()
  OR jsonb_typeof(requirements) IS DISTINCT FROM 'object'
  OR requirements-ARRAY['version','record','fields']<>'{}'::jsonb
  OR requirements->>'version' IS DISTINCT FROM 'truss.temporal-source-guard/0.1'
  OR jsonb_typeof(requirements->'record') IS DISTINCT FROM 'object'
  OR (requirements->'record')-ARRAY['documentId','revision','module','element']<>'{}'::jsonb
  OR jsonb_typeof(requirements->'fields') IS DISTINCT FROM 'array'
  OR jsonb_array_length(requirements->'fields') NOT BETWEEN 1 AND 128 THEN RETURN false;END IF;
 SELECT value INTO selected_record FROM jsonb_array_elements(binding->'records') r
  WHERE (r.value->>'typeId')::int=selected_type;
 IF selected_record IS NULL OR selected_record->'identity' IS DISTINCT FROM requirements->'record' THEN RETURN false;END IF;
 record_identity:=requirements->'record';
 SELECT d.* INTO source_doc FROM truss.schema_doc d WHERE d.doc_id=record_identity->>'documentId'
  AND d.doc_revision=record_identity->>'revision' AND d.rev<=(binding->>'catalogRevision')::int ORDER BY d.rev DESC LIMIT 1;
 IF NOT FOUND OR source_doc.content_sha256 IS DISTINCT FROM (SELECT pin.value->>'sha256' FROM jsonb_array_elements(binding->'documents') pin
   WHERE pin.value->>'documentId'=record_identity->>'documentId' AND pin.value->>'revision'=record_identity->>'revision') THEN RETURN false;END IF;
 owner_access:=source_doc.validation->'accessAdmission';
 IF source_doc.validation->'accessAdmissionProfile' IS DISTINCT FROM
  '{"profile":"truss.umf-access-admission-bridge/0.1-candidate","archiveSha256":"972396293616cf930a99c29249ff0490f131fc76c832931b6def2d3278f491cb","bundleSha256":"7f2a434b4b1bd0a2b8c1fe6ef47130f9f1543848a49445679c372d3fa6099856","manifestSha256":"5df7d94ab20d02c76b34016429207bb1d4fcb97f8c1e8d9fce234d1139725bcb"}'::jsonb
  OR jsonb_typeof(owner_access) IS DISTINCT FROM 'object' OR owner_access-ARRAY['records','diagnostics']<>'{}'::jsonb
  OR owner_access->'diagnostics'<>'[]'::jsonb OR jsonb_typeof(owner_access->'records') IS DISTINCT FROM 'array' THEN RETURN false;END IF;
 SELECT count(*),(jsonb_agg(r.value)->0) INTO matches,owner_record FROM jsonb_array_elements(owner_access->'records') r
  WHERE r.value->'ref'=jsonb_build_object('module',record_identity->>'module','element',record_identity->>'element');
 IF matches<>1 THEN RETURN false;END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(requirements->'fields') f
  WHERE jsonb_typeof(f.value) IS DISTINCT FROM 'object'
   OR f.value-ARRAY['field','kind','presence']<>'{}'::jsonb
   OR jsonb_typeof(f.value->'field') IS DISTINCT FROM 'object'
   OR (f.value->'field')-ARRAY['documentId','revision','module','element']<>'{}'::jsonb
   OR jsonb_typeof(f.value->'presence') IS DISTINCT FROM 'object'
   OR (f.value->'presence')-ARRAY['missing','null']<>'{}'::jsonb
   OR jsonb_typeof(f.value->'presence'->'missing') IS DISTINCT FROM 'boolean'
   OR jsonb_typeof(f.value->'presence'->'null') IS DISTINCT FROM 'boolean'
   OR jsonb_typeof(f.value->'kind') IS DISTINCT FROM 'string'
   OR f.value->>'kind' NOT IN ('date','instant','local')) THEN RETURN false;END IF;
 IF (SELECT count(*) FROM jsonb_array_elements(requirements->'fields')) <>
    (SELECT count(DISTINCT (value->'field')::text) FROM jsonb_array_elements(requirements->'fields')) THEN RETURN false;END IF;
 FOR requirement IN SELECT value FROM jsonb_array_elements(requirements->'fields') LOOP
  field_identity:=requirement->'field';kind:=requirement->>'kind';
  SELECT f.value INTO selected_field FROM jsonb_array_elements(selected_record->'fields') f
   WHERE f.value->'identity' IS NOT DISTINCT FROM field_identity;
  IF selected_field IS NULL THEN RETURN false;END IF;
  SELECT * INTO property FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id=(selected_field->>'propertyId')::int AND p.retired_rev IS NULL;
  IF NOT FOUND THEN RETURN false;END IF;
  SELECT count(*),(jsonb_agg(f.value)->0) INTO matches,owner_field FROM jsonb_array_elements(owner_record->'fields') f
   WHERE f.value->'ref'=jsonb_build_object('module',field_identity->>'module','element',field_identity->>'element');
  IF matches<>1 OR jsonb_typeof(owner_field->'row') IS DISTINCT FROM 'object'
   OR (owner_field->'row')-ARRAY['missing','null']<>'{}'::jsonb
   OR owner_field->'row' IS DISTINCT FROM requirement->'presence' THEN RETURN false;END IF;
  IF kind='date' THEN
   IF property.scalar_type<>'date' OR owner_field->>'scalarType'<>'date' OR owner_field ? 'temporal'
    OR property.native_temporal IS NOT NULL THEN RETURN false;END IF;
  ELSIF kind='instant' THEN
   IF property.scalar_type<>'timestamp' OR owner_field->>'scalarType'<>'timestamp' OR owner_field->>'temporal'<>'instant'
    OR property.native_temporal IS NOT NULL THEN RETURN false;END IF;
  ELSE
   IF property.scalar_type<>'localTimestamp' OR owner_field->>'scalarType'<>'timestamp' OR owner_field->>'temporal'<>'local'
    OR truss.valid_native_temporal_property(property) IS NOT TRUE
    OR property.native_temporal->>'profile'<>'truss.local-timestamp/0.1'
    OR property.native_temporal->>'kind'<>'local'
    OR property.native_temporal->'source'->>'documentId' IS DISTINCT FROM record_identity->>'documentId'
    OR property.native_temporal->'source'->>'sha256' IS DISTINCT FROM source_doc.content_sha256
    OR property.native_temporal->'source'->>'fieldViewPointer' IS DISTINCT FROM owner_field->>'viewPointer'
    OR property.native_temporal->'source'->'record' IS DISTINCT FROM record_identity-ARRAY['documentId','revision']
    OR property.native_temporal->'source'->'field' IS DISTINCT FROM field_identity-ARRAY['documentId','revision'] THEN RETURN false;END IF;
  END IF;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_requirements_valid(jsonb,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.query_temporal_objects(binding jsonb,selected_type int,requirements jsonb)
RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE owner truss.type_def%ROWTYPE;object_row truss.object%ROWTYPE;record_mapping jsonb;requirement jsonb;selected_field jsonb;property truss.prop_def%ROWTYPE;cell jsonb;
 row_count int:=0;byte_count bigint:=0;root_identity jsonb;roots jsonb:='{}';root_entry jsonb;
BEGIN
 PERFORM truss.query_scope(binding);
 IF truss.query_temporal_requirements_valid(binding,selected_type,requirements) IS NOT TRUE THEN
  RAISE EXCEPTION 'selected temporal source requirements required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT owner FROM truss.type_def t WHERE t.type_id=selected_type AND t.retired_rev IS NULL;
 SELECT value INTO STRICT record_mapping FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type;
 FOR object_row IN SELECT o.* FROM truss.object o WHERE o.type_id=selected_type ORDER BY o.id LIMIT (binding->>'maximumScanRows')::int+1 LOOP
  row_count:=row_count+1;byte_count:=byte_count+octet_length(object_row.props::text);
  IF row_count>(binding->>'maximumScanRows')::int OR byte_count>(binding->>'maximumBytes')::int THEN RAISE EXCEPTION 'bounded complete temporal source required' USING ERRCODE='54000';END IF;
  root_identity:=truss.query_object_root(binding,object_row);
  IF root_identity IS NOT NULL THEN roots:=roots||jsonb_build_object((root_identity->>'typeId')||':'||(root_identity->>'id'),root_identity);END IF;
  IF byte_count+(CASE WHEN roots='{}'::jsonb THEN 0 ELSE octet_length(roots::text) END)>(binding->>'maximumBytes')::int THEN RAISE EXCEPTION 'bounded temporal source root witnesses required' USING ERRCODE='54000';END IF;
  IF object_row.ver<=0 OR object_row.rev>(binding->>'catalogRevision')::int THEN RAISE EXCEPTION 'complete temporal source required' USING ERRCODE='55000';END IF;
  FOR requirement IN SELECT value FROM jsonb_array_elements(requirements->'fields') LOOP
   SELECT f.value INTO STRICT selected_field FROM jsonb_array_elements(record_mapping->'fields') f
    WHERE f.value->'identity' IS NOT DISTINCT FROM requirement->'field';
   SELECT * INTO STRICT property FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id=(selected_field->>'propertyId')::int AND p.retired_rev IS NULL;
   cell:=object_row.props->(property.prop_id::text);
   IF cell IS NULL THEN
    IF (requirement->'presence'->>'missing')::boolean IS NOT TRUE THEN RAISE EXCEPTION 'required temporal property missing' USING ERRCODE='22023';END IF;
   ELSIF cell='{"kind":"null"}'::jsonb THEN
    IF (requirement->'presence'->>'null')::boolean IS NOT TRUE THEN RAISE EXCEPTION 'required temporal property is null' USING ERRCODE='22023';END IF;
   ELSIF requirement->>'kind'='local' THEN
    IF truss.valid_property_value(cell,property) IS NOT TRUE OR cell->>'kind' IS DISTINCT FROM 'localTimestamp' THEN RAISE EXCEPTION 'invalid bounded local timestamp value' USING ERRCODE='22023';END IF;
   ELSIF requirement->>'kind'='date' THEN
    IF truss.valid_property_value(cell,property) IS NOT TRUE OR cell->>'kind' IS DISTINCT FROM 'date' THEN RAISE EXCEPTION 'invalid bounded date value' USING ERRCODE='22023';END IF;
   ELSE
    IF cell->>'kind' IS DISTINCT FROM 'timestamp' OR truss.query_temporal_instant_key(cell->>'text') IS NULL THEN RAISE EXCEPTION 'invalid bounded instant value' USING ERRCODE='22023';END IF;
   END IF;
  END LOOP;
  id:=object_row.id;props:=object_row.props;RETURN NEXT;
 END LOOP;
 IF row_count>(binding->>'maximumScanRows')::int THEN RAISE EXCEPTION 'bounded complete temporal source required' USING ERRCODE='54000';END IF;
 FOR root_entry IN SELECT value FROM jsonb_each(roots) LOOP
  IF NOT truss.runtime_can_read(root_entry->'owner'->>'documentId',root_entry->'owner'->>'moduleId') THEN RAISE EXCEPTION 'current buffered query aggregate root reader required' USING ERRCODE='P1403';END IF;
 END LOOP;
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_objects(jsonb,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.query_temporal_page_objects(binding jsonb,selected_type int,selected_key text,requirements jsonb)
RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 IF selected_key IS NULL OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r CROSS JOIN LATERAL jsonb_array_elements(r.value->'keys') k WHERE (r.value->>'typeId')::int=selected_type AND k.value->>'keyId'=selected_key) THEN
  RAISE EXCEPTION 'selected original page Key required' USING ERRCODE='22023';END IF;
 RETURN QUERY SELECT * FROM truss.query_temporal_objects(binding,selected_type,requirements);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_page_objects(jsonb,int,text,jsonb) FROM PUBLIC;
