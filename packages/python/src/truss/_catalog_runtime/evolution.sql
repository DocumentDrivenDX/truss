-- Real-data validation before compatible catalog publication.
CREATE FUNCTION truss.catalog_scalar_violations(declarations_bytes bytea) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE rec jsonb;field jsonb;selected_type int;property_id int;missing_count bigint;family_count bigint;retained_count bigint;facet_count bigint;
 rel jsonb;old_relation jsonb;tightening boolean;selected_relation truss.rel_def%ROWTYPE;side text;minimum int;maximum int;low_count bigint;high_count bigint;
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
   IF field->'declaration'->>'cardinality' IN ('array','map') THEN
    IF truss.runtime_can_read(rec->>'documentId',field->'declaration'->'itemType'->>'module') IS NOT TRUE THEN RAISE EXCEPTION 'current item module read authority required for compatibility counts' USING ERRCODE='42501';END IF;
    scopes:=scopes||jsonb_build_array(jsonb_build_object('documentId',rec->>'documentId','moduleId',field->'declaration'->'itemType'->>'module'));
   END IF;
   SELECT prop_id INTO property_id FROM truss.prop_def p WHERE p.type_id=selected_type
    AND p.declaration_module=field->>'fieldModule' AND p.element=field->>'fieldId' AND p.retired_rev IS NULL;
   scope:=jsonb_build_object('documentId',rec->>'documentId','moduleId',rec->>'moduleId',
    'recordId',rec->>'elementId','fieldModuleId',field->>'fieldModule','fieldId',field->>'fieldId');
   SELECT count(*) FILTER (WHERE field->'declaration'->>'nullability'='required'
     AND (property_id IS NULL OR NOT o.props ? property_id::text OR o.props->property_id::text='{"kind":"null"}'::jsonb)),
    count(*) FILTER (WHERE field->'declaration'->>'cardinality'='one' AND property_id IS NOT NULL AND o.props ? property_id::text
     AND o.props->property_id::text<>'{"kind":"null"}'::jsonb
     AND truss.valid_scalar_cell(o.props->property_id::text,field->'declaration'->>'scalarType',true) IS NOT TRUE)
    ,count(*) FILTER (WHERE field->'declaration'->>'cardinality'='one' AND property_id IS NOT NULL AND o.props ? property_id::text
     AND o.props->property_id::text<>'{"kind":"null"}'::jsonb
     AND truss.valid_scalar_cell(o.props->property_id::text,field->'declaration'->>'scalarType',true) IS TRUE
     AND ((field->'declaration'->>'scalarType'='integer' AND field->'declaration'->'facets'='{"integerWidth":{"bits":64,"signed":true}}'::jsonb) OR (field->'declaration'->>'scalarType'='decimal' AND field->'declaration'->'facets'='{"precision":18,"scale":4}'::jsonb))
     AND truss.valid_scalar_property(o.props->property_id::text,field->'declaration'->>'scalarType',true,field->'declaration'->'facets') IS NOT TRUE)
    ,count(*) FILTER (WHERE property_id IS NULL AND o.retained ? (field->'declaration'->>'name'))
    INTO missing_count,family_count,facet_count,retained_count FROM truss.object o WHERE o.type_id=selected_type;
   IF missing_count>0 THEN violations:=violations||jsonb_build_array(scope||jsonb_build_object('rule','property.required','affectedObjectCount',missing_count::text));END IF;
   IF family_count>0 THEN violations:=violations||jsonb_build_array(scope||jsonb_build_object('rule','property.scalar_type','affectedObjectCount',family_count::text));END IF;
   IF facet_count>0 THEN violations:=violations||jsonb_build_array(scope||jsonb_build_object('rule','property.facets','affectedObjectCount',facet_count::text));END IF;
   IF retained_count>0 THEN violations:=violations||jsonb_build_array(scope||jsonb_build_object('rule','property.retained_name_collision','affectedObjectCount',retained_count::text));END IF;
  END LOOP;
 END LOOP;
 -- Existing independent relationship bounds are checked before publication.
 FOR rel IN SELECT r.value FROM jsonb_array_elements(convert_from(declarations_bytes,'UTF8')::jsonb) d
  CROSS JOIN LATERAL jsonb_array_elements(d.value->'relationships') r LOOP
  SELECT * INTO selected_relation FROM truss.rel_def WHERE document_id=rel->>'documentId' AND module=rel->>'moduleId'
   AND rel_id=rel->'declaration'->>'id' AND retired_rev IS NULL;
  IF NOT FOUND THEN CONTINUE;END IF;
  tightening:=(rel->'declaration'->'sourceMultiplicity'->>'min')::int>selected_relation.source_min
   OR (rel->'declaration'->'targetMultiplicity'->>'min')::int>selected_relation.target_min
   OR rel->'declaration'->'sourceMultiplicity'->>'max'<>'*' AND (selected_relation.source_max IS NULL OR (rel->'declaration'->'sourceMultiplicity'->>'max')::int<selected_relation.source_max)
   OR rel->'declaration'->'targetMultiplicity'->>'max'<>'*' AND (selected_relation.target_max IS NULL OR (rel->'declaration'->'targetMultiplicity'->>'max')::int<selected_relation.target_max);
  IF tightening THEN
   SELECT r.value INTO STRICT old_relation FROM truss.schema_doc d CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m
    CROSS JOIN LATERAL jsonb_array_elements(m.value->'relationships') r WHERE d.rev=selected_relation.definition_rev AND d.ord=selected_relation.definition_doc_ord
    AND d.doc_id=selected_relation.definition_document_id AND m.value->>'id'=selected_relation.module AND r.value->>'id'=selected_relation.rel_id;
   IF old_relation->'source' IS DISTINCT FROM rel->'declaration'->'source' OR old_relation->'target' IS DISTINCT FROM rel->'declaration'->'target' THEN
    RAISE EXCEPTION 'tightening requires unchanged endpoint declarations' USING ERRCODE='0A000';END IF;
  END IF;
  IF truss.runtime_can_read(selected_relation.document_id,selected_relation.module) IS NOT TRUE THEN
   RAISE EXCEPTION 'relationship reader required for compatibility counts' USING ERRCODE='42501';END IF;
  scopes:=scopes||jsonb_build_array(jsonb_build_object('documentId',selected_relation.document_id,'moduleId',selected_relation.module));
  FOR owner IN SELECT DISTINCT t.document_id,t.module FROM truss.rel_endpoint e JOIN truss.type_def t ON t.type_id IN(e.source_type,e.target_type) WHERE e.rel_type_id=selected_relation.rel_type_id LOOP
   IF truss.runtime_can_read(owner.document_id,owner.module) IS NOT TRUE THEN RAISE EXCEPTION 'complete endpoint reader required for compatibility counts' USING ERRCODE='42501';END IF;
   scopes:=scopes||jsonb_build_array(jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module));
  END LOOP;
  FOREACH side IN ARRAY ARRAY['source','target'] LOOP
   minimum:=(rel->'declaration'->CASE WHEN side='source' THEN 'targetMultiplicity' ELSE 'sourceMultiplicity' END->>'min')::int;
   maximum:=CASE WHEN rel->'declaration'->CASE WHEN side='source' THEN 'targetMultiplicity' ELSE 'sourceMultiplicity' END->>'max'='*' THEN NULL ELSE (rel->'declaration'->CASE WHEN side='source' THEN 'targetMultiplicity' ELSE 'sourceMultiplicity' END->>'max')::int END;
   SELECT count(*) FILTER(WHERE degree<minimum),count(*) FILTER(WHERE maximum IS NOT NULL AND degree>maximum) INTO low_count,high_count FROM (
    SELECT (SELECT count(*) FROM truss.edge e WHERE e.rel_type_id=selected_relation.rel_type_id AND
     CASE WHEN side='source' THEN e.source_id=o.id AND e.source_type=o.type_id ELSE e.target_id=o.id AND e.target_type=o.type_id END) AS degree
    FROM truss.object o WHERE EXISTS(SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=selected_relation.rel_type_id AND CASE WHEN side='source' THEN e.source_type=o.type_id ELSE e.target_type=o.type_id END)) anchors;
   scope:=jsonb_build_object('documentId',selected_relation.document_id,'moduleId',selected_relation.module,'relationshipId',selected_relation.rel_id,'side',side);
   IF low_count>0 THEN violations:=violations||jsonb_build_array(scope||jsonb_build_object('rule','relationship.min','affectedObjectCount',low_count::text));END IF;
   IF high_count>0 THEN violations:=violations||jsonb_build_array(scope||jsonb_build_object('rule','relationship.max','affectedObjectCount',high_count::text));END IF;
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
