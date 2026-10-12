-- Real-data validation prerequisite; compatible persistence remains unavailable.
CREATE FUNCTION truss.catalog_scalar_violations(declarations_bytes bytea) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE rec jsonb;field jsonb;selected_type int;property_id int;missing_count bigint;family_count bigint;retained_count bigint;
 violations jsonb:='[]';scope jsonb;scopes jsonb:='[]';owner record;
BEGIN
 -- The caller holds the exclusive head lock, excluding supported graph writers.
 FOR rec IN SELECT r.value FROM jsonb_array_elements(convert_from(declarations_bytes,'UTF8')::jsonb) d
  CROSS JOIN LATERAL jsonb_array_elements(d.value->'records') r LOOP
  SELECT type_id INTO selected_type FROM truss.type_def t WHERE t.document_id=rec->>'documentId'
   AND t.module=rec->>'moduleId' AND t.element=rec->>'elementId' AND t.retired_rev IS NULL;
  IF NOT FOUND THEN CONTINUE;END IF;
  IF NOT truss.runtime_can_read(rec->>'documentId',rec->>'moduleId') THEN
   RAISE EXCEPTION 'current module read authority required for compatibility counts' USING ERRCODE='42501';END IF;
  scopes:=scopes||jsonb_build_array(jsonb_build_object('documentId',rec->>'documentId','moduleId',rec->>'moduleId'));
  FOR field IN SELECT value FROM jsonb_array_elements(rec->'fields') LOOP
   IF NOT truss.runtime_can_read(rec->>'documentId',field->>'fieldModule') THEN
    RAISE EXCEPTION 'current field module read authority required for compatibility counts' USING ERRCODE='42501';END IF;
   scopes:=scopes||jsonb_build_array(jsonb_build_object('documentId',rec->>'documentId','moduleId',field->>'fieldModule'));
   SELECT prop_id INTO property_id FROM truss.prop_def p WHERE p.type_id=selected_type
    AND p.declaration_module=field->>'fieldModule' AND p.element=field->>'fieldId' AND p.retired_rev IS NULL;
   scope:=jsonb_build_object('documentId',rec->>'documentId','moduleId',rec->>'moduleId',
    'recordId',rec->>'elementId','fieldModuleId',field->>'fieldModule','fieldId',field->>'fieldId');
   SELECT count(*) FILTER (WHERE field->'declaration'->>'nullability'='required'
     AND (property_id IS NULL OR NOT o.props ? property_id::text OR o.props->property_id::text='{"kind":"null"}'::jsonb)),
    count(*) FILTER (WHERE property_id IS NOT NULL AND o.props ? property_id::text
     AND o.props->property_id::text<>'{"kind":"null"}'::jsonb
     AND truss.valid_scalar_cell(o.props->property_id::text,field->'declaration'->>'scalarType',true) IS NOT TRUE)
    ,count(*) FILTER (WHERE property_id IS NULL AND o.retained ? (field->'declaration'->>'name'))
    INTO missing_count,family_count,retained_count FROM truss.object o WHERE o.type_id=selected_type;
   IF missing_count>0 THEN violations:=violations||jsonb_build_array(scope||jsonb_build_object('rule','property.required','affectedObjectCount',missing_count::text));END IF;
   IF family_count>0 THEN violations:=violations||jsonb_build_array(scope||jsonb_build_object('rule','property.scalar_type','affectedObjectCount',family_count::text));END IF;
   IF retained_count>0 THEN violations:=violations||jsonb_build_array(scope||jsonb_build_object('rule','property.retained_name_collision','affectedObjectCount',retained_count::text));END IF;
  END LOOP;
 END LOOP;
 FOR owner IN SELECT DISTINCT value->>'documentId' AS document_id,value->>'moduleId' AS module_id FROM jsonb_array_elements(scopes) LOOP
  IF NOT truss.runtime_can_read(owner.document_id,owner.module_id) THEN
   RAISE EXCEPTION 'current module authority changed during compatibility validation' USING ERRCODE='42501';END IF;
 END LOOP;
 IF violations='[]'::jsonb THEN RETURN NULL;END IF;
 RETURN convert_to(violations::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_scalar_violations(bytea) FROM PUBLIC;
