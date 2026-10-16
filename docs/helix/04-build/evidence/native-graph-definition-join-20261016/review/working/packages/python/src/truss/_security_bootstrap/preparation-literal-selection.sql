-- Private selected-literal execution component, not production admission.
-- Original immutable producer/source enrollment and excluded owner are premises.
CREATE FUNCTION truss.preparation_literal_parameters(statement pg_catalog.jsonb)
RETURNS pg_catalog.text[] LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE parameter pg_catalog.jsonb; parameters pg_catalog.text[]:='{}'; position pg_catalog.int4:=0;
BEGIN
 IF jsonb_typeof(statement->'parameters') IS DISTINCT FROM 'array'
  OR jsonb_array_length(statement->'parameters')>64 THEN
  RAISE EXCEPTION 'bounded original String parameters required' USING ERRCODE='0A000';END IF;
 FOR parameter IN SELECT value FROM jsonb_array_elements(statement->'parameters') LOOP
  position:=position+1;
  IF parameter->>'name' IS DISTINCT FROM 'p'||position::text
   OR jsonb_typeof(parameter->'value') IS DISTINCT FROM 'object'
   OR jsonb_typeof(parameter->'value'->'string') IS DISTINCT FROM 'string'
   OR (parameter->'value')-'string' IS DISTINCT FROM '{}'::jsonb THEN
   RAISE EXCEPTION 'exact original String parameter required' USING ERRCODE='0A000';END IF;
  parameters:=array_append(parameters,parameter->'value'->>'string');
 END LOOP;
 RETURN parameters;
END;
$$;
REVOKE ALL ON FUNCTION truss.preparation_literal_parameters(jsonb) FROM PUBLIC;

-- Leaves enforce positional native types even for empty results. RETURN QUERY
-- buffers internally: packet limits below do not bound scratch/temp allocation.
-- No ordinary caller receives these raw-SQL leaves.
CREATE FUNCTION truss.execute_preparation_literal_preflight(original_sql pg_catalog.text,original_parameters pg_catalog.text[])
RETURNS TABLE(violations pg_catalog.text) LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN QUERY EXECUTE original_sql USING original_parameters[1], original_parameters[2], original_parameters[3], original_parameters[4], original_parameters[5], original_parameters[6], original_parameters[7], original_parameters[8], original_parameters[9], original_parameters[10], original_parameters[11], original_parameters[12], original_parameters[13], original_parameters[14], original_parameters[15], original_parameters[16], original_parameters[17], original_parameters[18], original_parameters[19], original_parameters[20], original_parameters[21], original_parameters[22], original_parameters[23], original_parameters[24], original_parameters[25], original_parameters[26], original_parameters[27], original_parameters[28], original_parameters[29], original_parameters[30], original_parameters[31], original_parameters[32], original_parameters[33], original_parameters[34], original_parameters[35], original_parameters[36], original_parameters[37], original_parameters[38], original_parameters[39], original_parameters[40], original_parameters[41], original_parameters[42], original_parameters[43], original_parameters[44], original_parameters[45], original_parameters[46], original_parameters[47], original_parameters[48], original_parameters[49], original_parameters[50], original_parameters[51], original_parameters[52], original_parameters[53], original_parameters[54], original_parameters[55], original_parameters[56], original_parameters[57], original_parameters[58], original_parameters[59], original_parameters[60], original_parameters[61], original_parameters[62], original_parameters[63], original_parameters[64];
END;
$$;
REVOKE ALL ON FUNCTION truss.execute_preparation_literal_preflight(text,text[]) FROM PUBLIC;

CREATE FUNCTION truss.execute_preparation_literal_selection(original_sql pg_catalog.text,original_parameters pg_catalog.text[])
RETURNS TABLE(identity pg_catalog.text,version pg_catalog.text,key0 pg_catalog.text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN QUERY EXECUTE original_sql USING original_parameters[1], original_parameters[2], original_parameters[3], original_parameters[4], original_parameters[5], original_parameters[6], original_parameters[7], original_parameters[8], original_parameters[9], original_parameters[10], original_parameters[11], original_parameters[12], original_parameters[13], original_parameters[14], original_parameters[15], original_parameters[16], original_parameters[17], original_parameters[18], original_parameters[19], original_parameters[20], original_parameters[21], original_parameters[22], original_parameters[23], original_parameters[24], original_parameters[25], original_parameters[26], original_parameters[27], original_parameters[28], original_parameters[29], original_parameters[30], original_parameters[31], original_parameters[32], original_parameters[33], original_parameters[34], original_parameters[35], original_parameters[36], original_parameters[37], original_parameters[38], original_parameters[39], original_parameters[40], original_parameters[41], original_parameters[42], original_parameters[43], original_parameters[44], original_parameters[45], original_parameters[46], original_parameters[47], original_parameters[48], original_parameters[49], original_parameters[50], original_parameters[51], original_parameters[52], original_parameters[53], original_parameters[54], original_parameters[55], original_parameters[56], original_parameters[57], original_parameters[58], original_parameters[59], original_parameters[60], original_parameters[61], original_parameters[62], original_parameters[63], original_parameters[64];
END;
$$;
REVOKE ALL ON FUNCTION truss.execute_preparation_literal_selection(text,text[]) FROM PUBLIC;

CREATE FUNCTION truss.select_preparation_literal_rows(original_anchor pg_catalog.int4,original_nonce pg_catalog.uuid)
RETURNS pg_catalog.jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
DECLARE program truss.preparation_program_registration%ROWTYPE;
 selected_program_id pg_catalog.int8; invocation pg_catalog.jsonb; lowering pg_catalog.jsonb;
 request pg_catalog.jsonb; model pg_catalog.jsonb; target_record pg_catalog.jsonb; target_key pg_catalog.jsonb; key_field pg_catalog.jsonb;
 installation truss.catalog_runtime_installation%ROWTYPE; selected_document pg_catalog.jsonb; source record;
 binding pg_catalog.jsonb; columns pg_catalog.jsonb; preflight pg_catalog.jsonb;
 selected record; preflight_row record; preflight_rows pg_catalog.int4; completed pg_catalog.int4:=0;
 maximum pg_catalog.int4; maximum_bytes pg_catalog.int4; previous pg_catalog.int8:=0;
 item_count pg_catalog.int4:=0; row_bytes pg_catalog.int8:=2; row_value pg_catalog.jsonb;
 rows_value pg_catalog.jsonb:='[]'; result pg_catalog.jsonb;
BEGIN
 IF (SELECT setting::int FROM pg_catalog.pg_settings WHERE name='statement_timeout') NOT BETWEEN 1 AND 60000 THEN
  RAISE EXCEPTION 'caller-owned bounded statement timeout required' USING ERRCODE='0A000';END IF;
 PERFORM truss.require_preparation_literal_permit(original_anchor,original_nonce);
 selected_program_id:=truss.resolve_preparation_program_binding(original_anchor,original_nonce,pg_current_xact_id());
 SELECT * INTO STRICT program FROM ONLY truss.preparation_program_registration p WHERE p.program_id=selected_program_id;
 invocation:=convert_from(program.original_lowering,'UTF8')::jsonb;
 lowering:=(invocation->>'response')::jsonb;
 request:=convert_from(program.original_request,'UTF8')::jsonb;
 model:=(request->'model'->>'utf8')::jsonb;
 binding:=(convert_from(program.original_binding_artifact,'UTF8')::jsonb->>'utf8')::jsonb;
 maximum:=(request->'limits'->>'maxItems')::int;
 maximum_bytes:=least((request->'limits'->>'maxManifestBytes')::int,(binding->>'maximumBytes')::int);
 columns:=lowering->'columns';
 IF lowering->>'status' IS DISTINCT FROM 'lowered' OR maximum IS NULL OR maximum NOT BETWEEN 1 AND 10000
  OR jsonb_typeof(request->'limits'->'maxManifestBytes') IS DISTINCT FROM 'number'
  OR jsonb_typeof(binding->'maximumBytes') IS DISTINCT FROM 'number'
  OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216
  OR lowering->'bounds' IS DISTINCT FROM jsonb_build_object('maxItems',maximum,'fetchLimit',maximum+1)
  OR lowering->'ordering' IS DISTINCT FROM '{"kind":"native-integer-identity","direction":"asc"}'::jsonb
  OR jsonb_typeof(columns) IS DISTINCT FROM 'array' OR jsonb_array_length(columns)<>3
  OR columns->0 IS DISTINCT FROM '{"name":"identity","kind":"identity","field":null}'::jsonb
  OR columns->1 IS DISTINCT FROM '{"name":"version","kind":"version","field":null}'::jsonb
  OR (columns->2)-'field' IS DISTINCT FROM '{"name":"key0","kind":"key"}'::jsonb
  OR jsonb_typeof(lowering->'preflight') IS DISTINCT FROM 'array'
  OR jsonb_array_length(lowering->'preflight') NOT BETWEEN 1 AND 128 THEN
  RAISE EXCEPTION 'original bounded single-String-key selection profile required' USING ERRCODE='0A000';END IF;
 SELECT e.value INTO STRICT target_record FROM jsonb_array_elements(model->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e
  WHERE m.value->>'id'=request->'target'->>'module' AND e.value->>'id'=request->'target'->>'element'
   AND e.value->>'kind'='record';
 SELECT k.value INTO STRICT target_key FROM jsonb_array_elements(target_record->'keys') k
  WHERE k.value->>'id'=request->'target'->>'key';
 IF jsonb_array_length(target_key->'fields') IS DISTINCT FROM 1
  OR target_key->'fields'->0 IS DISTINCT FROM columns->2->'field' THEN
  RAISE EXCEPTION 'original single key column correspondence required' USING ERRCODE='0A000';END IF;
 SELECT e.value INTO STRICT key_field FROM jsonb_array_elements(model->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e
  WHERE m.value->>'id'=columns->2->'field'->>'module' AND e.value->>'id'=columns->2->'field'->>'element'
   AND e.value->>'kind'='field';
 IF key_field->>'scalarType' IS DISTINCT FROM 'string' OR key_field->>'cardinality' IS DISTINCT FROM 'one'
  OR key_field->>'nullability' IS DISTINCT FROM 'required' THEN
  RAISE EXCEPTION 'original required scalar String key required' USING ERRCODE='0A000';END IF;
 -- Original frozen binding, including active release (not genesis alone).
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF binding->>'installationId' IS DISTINCT FROM installation.installation_id::text
  OR binding->>'releaseId' IS DISTINCT FROM installation.release_id
  OR binding->>'releaseSha256' IS DISTINCT FROM installation.release_sha256
  OR (binding->>'catalogRevision')::int IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
  OR jsonb_typeof(binding->'documents') IS DISTINCT FROM 'array'
  OR jsonb_array_length(binding->'documents') NOT BETWEEN 1 AND 32 THEN
  RAISE EXCEPTION 'original frozen installation/catalog binding required' USING ERRCODE='55000';END IF;
 FOR selected_document IN SELECT value FROM jsonb_array_elements(binding->'documents') LOOP
  SELECT d.doc_revision,d.content_sha256 INTO source FROM truss.schema_doc d
   WHERE d.doc_id=selected_document->>'documentId' AND d.rev<=(binding->>'catalogRevision')::int ORDER BY d.rev DESC LIMIT 1;
  IF NOT FOUND OR source.doc_revision IS DISTINCT FROM selected_document->>'revision'
   OR source.content_sha256 IS DISTINCT FROM selected_document->>'sha256' THEN
   RAISE EXCEPTION 'original frozen document binding required' USING ERRCODE='55000';END IF;
 END LOOP;
 -- Every actual original population preflight precedes any selector submission.
 FOR preflight IN SELECT value FROM jsonb_array_elements(lowering->'preflight') LOOP
  preflight_rows:=0;
  FOR preflight_row IN SELECT * FROM truss.execute_preparation_literal_preflight(
    preflight->>'sql',truss.preparation_literal_parameters(preflight)) LOOP
   preflight_rows:=preflight_rows+1;
   IF preflight_rows<>1 OR preflight_row.violations IS DISTINCT FROM '0' THEN
    RAISE EXCEPTION 'original complete-population preflight refused' USING ERRCODE='55000';END IF;
  END LOOP;
  IF preflight_rows<>1 THEN
   RAISE EXCEPTION 'one original preflight TEXT count required' USING ERRCODE='55000';END IF;
  completed:=completed+1;
 END LOOP;
 FOR selected IN SELECT * FROM truss.execute_preparation_literal_selection(
   lowering->>'sql',truss.preparation_literal_parameters(lowering)) LOOP
  item_count:=item_count+1;
  IF item_count>maximum THEN RAISE EXCEPTION 'original selection overflow without trimming' USING ERRCODE='54000';END IF;
  IF selected.identity IS NULL OR selected.version IS NULL OR selected.key0 IS NULL
   OR selected.identity!~'^[1-9][0-9]{0,18}$' OR selected.version!~'^[1-9][0-9]{0,18}$'
   OR selected.identity::bigint<=previous OR selected.version::bigint<=0 THEN
   RAISE EXCEPTION 'original positive identity/version ordering required' USING ERRCODE='55000';END IF;
  previous:=selected.identity::bigint;
  row_value:=jsonb_build_array(selected.identity,selected.version,selected.key0);
  row_bytes:=row_bytes+octet_length(row_value::text)+CASE WHEN item_count>1 THEN 2 ELSE 0 END;
  IF row_bytes>maximum_bytes THEN RAISE EXCEPTION 'original diagnostic byte bound exceeded' USING ERRCODE='54000';END IF;
  rows_value:=rows_value||jsonb_build_array(row_value);
 END LOOP;
 result:=jsonb_build_object('protocol','truss.preparation-native-selection/0.1-candidate',
  'programId',selected_program_id::text,'columns',columns,'rows',rows_value,'preflightsCompleted',completed,
  'authority',false,'securityReady',false);
 IF octet_length(result::text)>maximum_bytes THEN
  RAISE EXCEPTION 'original complete diagnostic byte bound exceeded' USING ERRCODE='54000';END IF;
 PERFORM truss.require_preparation_literal_permit(original_anchor,original_nonce);
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.select_preparation_literal_rows(int4,uuid) FROM PUBLIC;
