-- UMF owns the grammar; this private native realization grants no admission.
CREATE FUNCTION truss.umf_key_uleb128(number bigint) RETURNS bytea
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result bytea:=''::bytea;digit int;
BEGIN
 IF number IS NULL OR number<0 THEN RAISE EXCEPTION 'unsigned key framing required' USING ERRCODE='22023';END IF;
 LOOP
  digit:=(number%128)::int;number:=number/128;
  result:=result||set_byte(decode('00','hex'),0,digit+CASE WHEN number>0 THEN 128 ELSE 0 END);
  EXIT WHEN number=0;
 END LOOP;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.umf_key_uleb128(bigint) FROM PUBLIC;

CREATE FUNCTION truss.umf_key_coefficient(token text,scale int,precision_limit int DEFAULT NULL) RETURNS text
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE mantissa text;digits text;exponent_token text;exponent_value bigint:=0;shift bigint;negative boolean;
BEGIN
 IF token IS NULL OR octet_length(token)>1048576 OR token !~ '^-?(0|[1-9][0-9]*)([.][0-9]+)?([eE][+-]?[0-9]+)?$'
  OR scale IS NULL OR scale<0 THEN RAISE EXCEPTION 'exact bounded numeric key required' USING ERRCODE='22023';END IF;
 mantissa:=split_part(lower(token),'e',1);negative:=left(token,1)='-';
 digits:=ltrim(replace(ltrim(mantissa,'-'),'.',''),'0');
 IF digits='' THEN RETURN '0';END IF;
 exponent_token:=split_part(lower(token),'e',2);
 IF exponent_token<>'' THEN
  exponent_token:=ltrim(ltrim(exponent_token,'+-'),'0');
  IF length(exponent_token)>18 THEN RAISE EXCEPTION 'numeric key expansion outside domain' USING ERRCODE='22023';END IF;
  exponent_value:=CASE WHEN exponent_token='' THEN 0 ELSE exponent_token::bigint END;
  IF split_part(lower(token),'e',2) LIKE '-%' THEN exponent_value:=-exponent_value;END IF;
 END IF;
 shift:=scale::bigint-length(split_part(mantissa,'.',2))+exponent_value;
 IF shift<0 THEN
  IF -shift>length(digits)-length(rtrim(digits,'0')) THEN RAISE EXCEPTION 'numeric key would require rounding' USING ERRCODE='22023';END IF;
  digits:=left(digits,(length(digits)+shift)::int);
 ELSE
  IF length(digits)::bigint+shift>least(coalesce(precision_limit,1048576),1048576) THEN
   RAISE EXCEPTION 'numeric key expansion exceeds bound' USING ERRCODE='22023';END IF;
  digits:=digits||repeat('0',shift::int);
 END IF;
 IF precision_limit IS NOT NULL AND length(digits)>precision_limit THEN RAISE EXCEPTION 'numeric key exceeds precision' USING ERRCODE='22023';END IF;
 RETURN CASE WHEN negative THEN '-' ELSE '' END||digits;
END;
$$;
REVOKE ALL ON FUNCTION truss.umf_key_coefficient(text,int,int) FROM PUBLIC;

CREATE FUNCTION truss.encode_umf_scalar_key_tuple(cells jsonb,facets jsonb) RETURNS bytea
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result bytea;cell jsonb;facet jsonb;family text;payload bytea;tag int;position int:=0;
BEGIN
 IF jsonb_typeof(cells) IS DISTINCT FROM 'array' OR jsonb_typeof(facets) IS DISTINCT FROM 'array'
  OR jsonb_array_length(cells) NOT BETWEEN 1 AND 1024 OR jsonb_array_length(cells)<>jsonb_array_length(facets) THEN
  RAISE EXCEPTION 'complete ordered scalar key required' USING ERRCODE='22023';END IF;
 result:=convert_to('UMFK1','UTF8')||truss.umf_key_uleb128(jsonb_array_length(cells));
 FOR cell IN SELECT value FROM jsonb_array_elements(cells) LOOP
  family:=cell->>'kind';facet:=facets->position;position:=position+1;
  IF family IS NULL OR family NOT IN ('string','integer','decimal','boolean','binary')
   OR truss.valid_scalar_property(cell,family,false,facet) IS NOT TRUE THEN
   RAISE EXCEPTION 'admitted exact scalar key component required' USING ERRCODE='22023';END IF;
  CASE family
   WHEN 'string' THEN tag:=4;payload:=convert_to(cell->>'text','UTF8');
   WHEN 'binary' THEN tag:=5;payload:=decode(cell->>'text','base64');
   WHEN 'boolean' THEN tag:=1;payload:=decode(CASE WHEN (cell->>'value')::boolean THEN '01' ELSE '00' END,'hex');
   WHEN 'integer' THEN tag:=2;payload:=convert_to(truss.umf_key_coefficient(cell->>'text',0),'UTF8');
   WHEN 'decimal' THEN
    IF truss.valid_decimal_facets(facet) IS NOT TRUE THEN
     RAISE EXCEPTION 'selected native decimal key domain required' USING ERRCODE='0A000';END IF;
    tag:=3;payload:=truss.umf_key_uleb128((facet->>'scale')::numeric::bigint)||convert_to(truss.umf_key_coefficient(cell->>'text',(facet->>'scale')::numeric::int,(facet->>'precision')::numeric::int),'UTF8');
  END CASE;
  IF octet_length(result)::bigint+octet_length(payload)+8>1048576 THEN RAISE EXCEPTION 'key tuple budget exceeded' USING ERRCODE='54000';END IF;
  result:=result||set_byte(decode('00','hex'),0,tag)||truss.umf_key_uleb128(octet_length(payload))||payload;
 END LOOP;
 -- The stored transport is unchanged and includes two hex bytes per tuple byte.
 IF octet_length(result)::bigint*2+length('umf-key-tuple-v1:hex:')>1048576 THEN
  RAISE EXCEPTION 'key transport budget exceeded' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.encode_umf_scalar_key_tuple(jsonb,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.umf_key_field_values_valid(cells jsonb,fields jsonb,core text) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE field jsonb;cell jsonb;literal jsonb;candidate jsonb;facet jsonb;expected bytea;matched boolean;position int:=0;token text;kind text;
BEGIN
 IF core NOT IN ('0.7.0','0.8.0') OR jsonb_array_length(cells)<>jsonb_array_length(fields) THEN RETURN false;END IF;
 FOR field IN SELECT value FROM jsonb_array_elements(fields) LOOP
  cell:=cells->position;position:=position+1;kind:=field->>'scalarType';facet:=coalesce(field->'facets','{}');
  IF field->>'kind' IS DISTINCT FROM 'field' OR field->>'cardinality' IS DISTINCT FROM 'one'
   OR field->>'nullability' IS DISTINCT FROM 'required' OR cell->>'kind' IS DISTINCT FROM kind THEN RETURN false;END IF;
  token:=cell->>'text';
  IF core='0.8.0' AND kind IN ('integer','decimal') AND length(split_part(lower(token),'e',2))>32
   AND ltrim(replace(ltrim(split_part(lower(token),'e',1),'-'),'.',''),'0')<>'' THEN RETURN false;END IF;
  IF NOT field ? 'allowedValues' THEN CONTINUE;END IF;
  IF core<>'0.8.0' OR jsonb_typeof(field->'allowedValues') IS DISTINCT FROM 'array' THEN RETURN false;END IF;
  expected:=truss.encode_umf_scalar_key_tuple(jsonb_build_array(cell),jsonb_build_array(facet));matched:=false;
  FOR literal IN SELECT value FROM jsonb_array_elements(field->'allowedValues') LOOP
   CASE kind
    WHEN 'boolean' THEN candidate:=jsonb_build_object('kind',kind,'value',literal->'boolean');
    WHEN 'string' THEN candidate:=jsonb_build_object('kind',kind,'text',literal->'string');
    WHEN 'binary' THEN candidate:=jsonb_build_object('kind',kind,'text',replace(encode(decode(literal->>'binaryHex','hex'),'base64'),chr(10),''));
    WHEN 'integer' THEN candidate:=jsonb_build_object('kind',kind,'text',truss.umf_key_coefficient(literal->>'integerToken',0));
    WHEN 'decimal' THEN candidate:=jsonb_build_object('kind',kind,'text',literal->'decimalToken');
    ELSE RETURN false;
   END CASE;
   IF truss.encode_umf_scalar_key_tuple(jsonb_build_array(candidate),jsonb_build_array(facet))=expected THEN matched:=true;EXIT;END IF;
  END LOOP;
  IF NOT matched THEN RETURN false;END IF;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.umf_key_field_values_valid(jsonb,jsonb,text) FROM PUBLIC;

CREATE FUNCTION truss.derive_catalog_key_tuple(selected_type int,selected_key smallint,cells jsonb,planned_basis jsonb DEFAULT NULL) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE definition truss.key_def%ROWTYPE;owner truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;archive truss.schema_doc%ROWTYPE;
 record_source jsonb;key_source jsonb;field_source jsonb;reference jsonb;facets jsonb:='[]';fields jsonb:='[]';component int;position int:=0;
BEGIN
 IF planned_basis IS NULL THEN
  SELECT * INTO STRICT owner FROM truss.type_def WHERE type_id=selected_type AND kind='record' AND NOT provisional AND retired_rev IS NULL;
  SELECT * INTO STRICT definition FROM truss.key_def WHERE type_id=selected_type AND key_num=selected_key AND retired_rev IS NULL;
  SELECT * INTO STRICT archive FROM truss.schema_doc WHERE doc_id=owner.document_id ORDER BY rev DESC LIMIT 1;
 ELSE
  SELECT * INTO STRICT owner FROM jsonb_populate_recordset(NULL::truss.type_def,planned_basis->'type_def') t WHERE t.type_id=selected_type;
  SELECT * INTO STRICT definition FROM jsonb_populate_recordset(NULL::truss.key_def,planned_basis->'key_def') k WHERE k.type_id=selected_type AND k.key_num=selected_key;
  SELECT * INTO STRICT archive FROM jsonb_populate_recordset(NULL::truss.schema_doc,planned_basis->'schema_doc') d WHERE d.doc_id=owner.document_id ORDER BY d.rev DESC LIMIT 1;
 END IF;
 SELECT e.value INTO STRICT record_source FROM jsonb_array_elements(archive.document::jsonb->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e WHERE m.value->>'id'=owner.module AND e.value->>'id'=owner.element;
 SELECT value INTO STRICT key_source FROM jsonb_array_elements(record_source->'keys') WHERE value->>'id'=definition.key_id;
 IF key_source-ARRAY['id','name','fields','primary']<>'{}'::jsonb OR jsonb_array_length(key_source->'fields')<>cardinality(definition.prop_ids)
  OR jsonb_typeof(cells) IS DISTINCT FROM 'array' OR jsonb_array_length(cells)<>cardinality(definition.prop_ids) THEN
  RAISE EXCEPTION 'qualified ordered key definition required' USING ERRCODE='22023';END IF;
 FOREACH component IN ARRAY definition.prop_ids LOOP
  IF planned_basis IS NULL THEN SELECT * INTO STRICT property FROM truss.prop_def WHERE type_id=selected_type AND prop_id=component AND retired_rev IS NULL;
  ELSE SELECT * INTO STRICT property FROM jsonb_populate_recordset(NULL::truss.prop_def,planned_basis->'prop_def') p WHERE p.type_id=selected_type AND p.prop_id=component;END IF;
  reference:=jsonb_build_object('module',property.declaration_module,'element',property.element);
  IF key_source->'fields'->position IS DISTINCT FROM reference OR NOT record_source->'members' @> jsonb_build_array(reference) THEN
   RAISE EXCEPTION 'original key component references required' USING ERRCODE='0A000';END IF;
  SELECT e.value INTO STRICT field_source FROM jsonb_array_elements(archive.document::jsonb->'modules') m
   CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e WHERE m.value->>'id'=property.declaration_module AND e.value->>'id'=property.element;
  IF field_source->>'scalarType' IS DISTINCT FROM property.scalar_type OR coalesce(field_source->'facets','{}') IS DISTINCT FROM coalesce(property.facets,'{}') THEN
   RAISE EXCEPTION 'native key domain must match accepted source' USING ERRCODE='55000';END IF;
  facets:=facets||jsonb_build_array(coalesce(property.facets,'{}'));fields:=fields||jsonb_build_array(field_source);position:=position+1;
 END LOOP;
 IF truss.umf_key_field_values_valid(cells,fields,archive.umf_version) IS NOT TRUE THEN
  RAISE EXCEPTION 'key values outside accepted source domain' USING ERRCODE='22023';END IF;
 RETURN truss.encode_umf_scalar_key_tuple(cells,facets);
END;
$$;
REVOKE ALL ON FUNCTION truss.derive_catalog_key_tuple(int,smallint,jsonb,jsonb) FROM PUBLIC;
