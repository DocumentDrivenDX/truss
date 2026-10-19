-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Real-data validation before compatible catalog publication.
CREATE FUNCTION truss.catalog_scalar_violations(declarations_bytes bytea) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE rec jsonb;field jsonb;node jsonb;selected_type int;property_id int;missing_count bigint;family_count bigint;retained_count bigint;facet_count bigint;
 rel jsonb;old_relation jsonb;tightening boolean;selected_relation truss.rel_def%ROWTYPE;side text;minimum int;maximum int;low_count bigint;high_count bigint;
 violations jsonb[]:=ARRAY[]::jsonb[];scope jsonb;scopes jsonb[]:=ARRAY[]::jsonb[];owner record;original_item jsonb;property_meta record;result bytea;
 field_checks jsonb[];field_ordinal int;candidate_name text;check_required boolean;check_family boolean;check_facets boolean;check_name boolean;counts record;
 stored_values_bytes bigint:=0;remaining_stored_values_bytes bigint;
BEGIN
 -- The caller holds the exclusive head lock, excluding supported graph writers.
 FOR rec IN SELECT r.value FROM jsonb_array_elements(convert_from(declarations_bytes,'UTF8')::jsonb) d
  CROSS JOIN LATERAL jsonb_array_elements(d.value->'records') r LOOP
  SELECT type_id INTO selected_type FROM truss.type_def t WHERE t.document_id=rec->>'documentId'
   AND t.module=rec->>'moduleId' AND t.element=rec->>'elementId' AND t.retired_rev IS NULL;
  IF NOT FOUND THEN CONTINUE;END IF;
  IF NOT truss.runtime_can_read(rec->>'documentId',rec->>'moduleId') THEN
   RAISE EXCEPTION 'current module read authority required for compatibility counts' USING ERRCODE='42501';END IF;
  scopes:=array_append(scopes,jsonb_build_object('documentId',rec->>'documentId','moduleId',rec->>'moduleId'));
  field_checks:=ARRAY[]::jsonb[];field_ordinal:=0;
  FOR field IN SELECT value FROM jsonb_array_elements(rec->'fields') LOOP
   field_ordinal:=field_ordinal+1;
   IF NOT truss.runtime_can_read(rec->>'documentId',field->>'fieldModule') THEN
    RAISE EXCEPTION 'current field module read authority required for compatibility counts' USING ERRCODE='42501';END IF;
   scopes:=array_append(scopes,jsonb_build_object('documentId',rec->>'documentId','moduleId',field->>'fieldModule'));
   IF field->'declaration'->>'cardinality' IN ('array','map') THEN
    IF truss.runtime_can_read(rec->>'documentId',field->'declaration'->'itemType'->>'module') IS NOT TRUE THEN RAISE EXCEPTION 'current item module read authority required for compatibility counts' USING ERRCODE='42501';END IF;
    scopes:=array_append(scopes,jsonb_build_object('documentId',rec->>'documentId','moduleId',field->'declaration'->'itemType'->>'module'));
   END IF;
   property_id:=NULL;original_item:=NULL;
   SELECT p.prop_id,p.item,p.name,p.nullability,p.cardinality,p.scalar_type,p.facets
    INTO property_meta FROM truss.prop_def p WHERE p.type_id=selected_type
    AND p.declaration_module=field->>'fieldModule' AND p.element=field->>'fieldId' AND p.retired_rev IS NULL;
   IF FOUND THEN property_id:=property_meta.prop_id;IF property_meta.cardinality IN ('array','map') THEN original_item:=property_meta.item;END IF;END IF;
   IF original_item IS NOT NULL THEN
    IF truss.runtime_item_chain_readable(original_item) IS NOT TRUE THEN RAISE EXCEPTION 'complete current item readers required for compatibility counts' USING ERRCODE='42501';END IF;
    FOR node IN SELECT value FROM jsonb_array_elements(jsonb_build_array(original_item)||coalesce(original_item->'descendants','[]'::jsonb)) LOOP
     scopes:=array_append(scopes,jsonb_build_object('documentId',node->>'documentId','moduleId',node->'reference'->>'module'));
    END LOOP;
   END IF;
   candidate_name:=coalesce(field->'declaration'->>'name',field->'declaration'->>'id');
   check_required:=property_id IS NOT NULL AND field->'declaration'->>'nullability'='required' AND property_meta.nullability IS DISTINCT FROM 'required';
   check_family:=property_id IS NOT NULL AND field->'declaration'->>'cardinality'='one'
    AND (property_meta.cardinality IS DISTINCT FROM 'one' OR property_meta.scalar_type IS DISTINCT FROM field->'declaration'->>'scalarType');
   check_facets:=property_id IS NOT NULL AND field->'declaration'->>'cardinality'='one'
    AND property_meta.facets IS DISTINCT FROM field->'declaration'->'facets';
   check_name:=property_id IS NOT NULL AND property_meta.name IS DISTINCT FROM candidate_name;
   -- Unchanged native constraints and names cannot invalidate existing rows;
   -- only changed fields enter the one per-type data census below.
   IF check_required OR check_family OR check_facets OR check_name THEN
    field_checks:=array_append(field_checks,jsonb_build_object('ordinal',field_ordinal,'propertyId',property_id,
     'name',candidate_name,'scalarType',field->'declaration'->>'scalarType','facets',field->'declaration'->'facets',
     'fieldModule',field->>'fieldModule','fieldId',field->>'fieldId','checkRequired',check_required,
     'checkFamily',check_family,'checkFacets',check_facets,'checkName',check_name));
   END IF;
  END LOOP;
  IF cardinality(field_checks)>0 THEN
   remaining_stored_values_bytes:=16777216-stored_values_bytes;
   FOR counts IN
    WITH checks AS MATERIALIZED (
     SELECT (c.value->>'ordinal')::int AS ordinal,(c.value->>'propertyId')::int AS property_id,
      c.value->>'name' AS property_name,c.value->>'scalarType' AS scalar_type,
      NULLIF(c.value->'facets','null'::jsonb) AS facets,
      (c.value->>'checkRequired')::boolean AS check_required,(c.value->>'checkFamily')::boolean AS check_family,
      (c.value->>'checkFacets')::boolean AS check_facets,(c.value->>'checkName')::boolean AS check_name,
      c.value->>'fieldModule' AS field_module,c.value->>'fieldId' AS field_id
     FROM jsonb_array_elements(to_jsonb(field_checks)) c(value)),
    objects AS MATERIALIZED (SELECT o.id,o.props,o.retained FROM truss.object o WHERE o.type_id=selected_type),
    cells AS MATERIALIZED (
     SELECT f.ordinal,o.id,c.value AS cell,f.scalar_type,f.facets,f.check_family,f.check_facets
     FROM objects o CROSS JOIN LATERAL jsonb_each(o.props) c
      JOIN checks f ON c.key=f.property_id::text AND (f.check_required OR f.check_family OR f.check_facets)),
    cell_validity AS MATERIALIZED (
     SELECT c.*,
      CASE WHEN c.cell IS NOT NULL AND c.cell<>'{"kind":"null"}'::jsonb AND (c.check_family OR c.check_facets)
       THEN truss.valid_scalar_cell(c.cell,c.scalar_type,true) IS TRUE ELSE false END AS valid_cell
     FROM cells c),
    cell_flags AS MATERIALIZED (
     SELECT c.*,
      c.cell IS NOT NULL AND c.cell<>'{"kind":"null"}'::jsonb AND c.check_family AND c.valid_cell IS NOT TRUE AS invalid_family,
      c.cell IS NOT NULL AND c.cell<>'{"kind":"null"}'::jsonb AND c.check_facets AND c.valid_cell
       AND truss.checked_scalar_facets(c.scalar_type,c.facets) IS TRUE
       AND truss.valid_scalar_property(c.cell,c.scalar_type,true,c.facets) IS NOT TRUE AS invalid_facets,
      c.cell IS NOT NULL AND c.cell<>'{"kind":"null"}'::jsonb AS present_nonnull
     FROM cell_validity c),
    retained_names AS MATERIALIZED (
     SELECT o.id,n.value AS property_name FROM objects o
      CROSS JOIN LATERAL jsonb_object_keys(CASE WHEN jsonb_typeof(o.retained)='object' THEN o.retained ELSE '{}'::jsonb END) n(value)),
    object_count AS (SELECT count(*) AS total FROM objects),
    property_stats AS (
     SELECT f.ordinal,
      count(*) FILTER(WHERE c.invalid_family) AS invalid_family,
      count(*) FILTER(WHERE c.invalid_facets) AS invalid_facets,
      coalesce(sum(octet_length(jsonb_build_object('objectId',c.id::text,'text',c.cell->>'text')::text)::bigint)
       FILTER(WHERE c.invalid_facets AND f.scalar_type IN ('string','binary')),0)::bigint AS stored_entry_bytes,
      count(*) FILTER(WHERE c.invalid_facets AND f.scalar_type IN ('string','binary'))::bigint AS stored_entry_count,
      count(*) FILTER(WHERE c.present_nonnull) AS present_nonnull
     FROM checks f LEFT JOIN cell_flags c ON c.ordinal=f.ordinal GROUP BY f.ordinal),
    budgeted_stats AS MATERIALIZED (
     SELECT s.*,
      CASE WHEN s.stored_entry_count=0 THEN 0 ELSE s.stored_entry_bytes+2*s.stored_entry_count END::bigint AS stored_value_bytes,
      sum(CASE WHEN s.stored_entry_count=0 THEN 0 ELSE s.stored_entry_bytes+2*s.stored_entry_count END)
       OVER(ORDER BY s.ordinal ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_stored_value_bytes
     FROM property_stats s),
    stored_arrays AS (
     SELECT b.ordinal,coalesce(jsonb_agg(jsonb_build_object('objectId',c.id::text,'text',c.cell->>'text') ORDER BY c.id)
       FILTER(WHERE c.invalid_facets AND c.scalar_type IN ('string','binary')
        AND b.cumulative_stored_value_bytes<=remaining_stored_values_bytes),'[]'::jsonb) AS stored_values
     FROM budgeted_stats b LEFT JOIN cell_flags c ON c.ordinal=b.ordinal
     GROUP BY b.ordinal,b.cumulative_stored_value_bytes),
    retained_counts AS (
     SELECT f.ordinal,count(*) AS collisions FROM checks f JOIN retained_names n ON n.property_name=f.property_name
      WHERE f.check_name GROUP BY f.ordinal)
   SELECT f.ordinal,f.field_module,f.field_id,
    CASE WHEN f.check_required THEN greatest(o.total-coalesce(p.present_nonnull,0),0) ELSE 0 END AS missing,
    coalesce(p.invalid_family,0) AS family,coalesce(p.invalid_facets,0) AS facets,
    coalesce(p.stored_value_bytes,0) AS stored_value_bytes,coalesce(a.stored_values,'[]'::jsonb) AS stored_values,
    coalesce(r.collisions,0) AS retained
   FROM checks f CROSS JOIN object_count o LEFT JOIN budgeted_stats p ON p.ordinal=f.ordinal
    LEFT JOIN stored_arrays a ON a.ordinal=f.ordinal
    LEFT JOIN retained_counts r ON r.ordinal=f.ordinal ORDER BY f.ordinal
   LOOP
    IF counts.stored_value_bytes>remaining_stored_values_bytes THEN
     RAISE EXCEPTION 'complete compatibility violation result exceeds byte limit' USING ERRCODE='54000';END IF;
    stored_values_bytes:=stored_values_bytes+counts.stored_value_bytes;
    remaining_stored_values_bytes:=remaining_stored_values_bytes-counts.stored_value_bytes;
    scope:=jsonb_build_object('documentId',rec->>'documentId','moduleId',rec->>'moduleId',
     'recordId',rec->>'elementId','fieldModuleId',counts.field_module,'fieldId',counts.field_id);
    IF counts.missing>0 THEN violations:=array_append(violations,scope||jsonb_build_object('rule','property.required','affectedObjectCount',counts.missing::text));END IF;
    IF counts.family>0 THEN violations:=array_append(violations,scope||jsonb_build_object('rule','property.scalar_type','affectedObjectCount',counts.family::text));END IF;
    IF counts.facets>0 THEN violations:=array_append(violations,scope||jsonb_build_object('rule','property.facets','affectedObjectCount',counts.facets::text)
     ||CASE WHEN counts.stored_values='[]'::jsonb THEN '{}'::jsonb ELSE jsonb_build_object('storedValues',counts.stored_values) END);END IF;
    IF counts.retained>0 THEN violations:=array_append(violations,scope||jsonb_build_object('rule','property.retained_name_collision','affectedObjectCount',counts.retained::text));END IF;
   END LOOP;
  END IF;
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
  scopes:=array_append(scopes,jsonb_build_object('documentId',selected_relation.document_id,'moduleId',selected_relation.module));
  FOR owner IN SELECT DISTINCT t.document_id,t.module FROM truss.rel_endpoint e JOIN truss.type_def t ON t.type_id IN(e.source_type,e.target_type) WHERE e.rel_type_id=selected_relation.rel_type_id LOOP
   IF truss.runtime_can_read(owner.document_id,owner.module) IS NOT TRUE THEN RAISE EXCEPTION 'complete endpoint reader required for compatibility counts' USING ERRCODE='42501';END IF;
   scopes:=array_append(scopes,jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module));
  END LOOP;
  IF NOT tightening THEN CONTINUE;END IF;
  FOREACH side IN ARRAY ARRAY['source','target'] LOOP
   minimum:=(rel->'declaration'->CASE WHEN side='source' THEN 'targetMultiplicity' ELSE 'sourceMultiplicity' END->>'min')::int;
   maximum:=CASE WHEN rel->'declaration'->CASE WHEN side='source' THEN 'targetMultiplicity' ELSE 'sourceMultiplicity' END->>'max'='*' THEN NULL ELSE (rel->'declaration'->CASE WHEN side='source' THEN 'targetMultiplicity' ELSE 'sourceMultiplicity' END->>'max')::int END;
   IF side='source' AND minimum<=selected_relation.target_min
      AND (maximum IS NULL OR selected_relation.target_max IS NOT NULL AND maximum>=selected_relation.target_max)
    OR side='target' AND minimum<=selected_relation.source_min
      AND (maximum IS NULL OR selected_relation.source_max IS NOT NULL AND maximum>=selected_relation.source_max) THEN CONTINUE;END IF;
   -- Bound each degree probe while retaining exact violation totals.
   IF side='source' THEN
    SELECT count(*) FILTER(WHERE degree<minimum),count(*) FILTER(WHERE maximum IS NOT NULL AND degree>maximum) INTO low_count,high_count FROM (
     SELECT (SELECT count(*) FROM (
      SELECT 1 FROM truss.edge e WHERE e.rel_type_id=selected_relation.rel_type_id AND e.source_id=o.id AND e.source_type=o.type_id
      LIMIT CASE WHEN maximum IS NULL THEN minimum::bigint ELSE maximum::bigint+1 END
     ) matching_edges) AS degree
     FROM truss.object o WHERE EXISTS(SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=selected_relation.rel_type_id AND e.source_type=o.type_id)) anchors;
   ELSE
    SELECT count(*) FILTER(WHERE degree<minimum),count(*) FILTER(WHERE maximum IS NOT NULL AND degree>maximum) INTO low_count,high_count FROM (
     SELECT (SELECT count(*) FROM (
      SELECT 1 FROM truss.edge e WHERE e.rel_type_id=selected_relation.rel_type_id AND e.target_id=o.id AND e.target_type=o.type_id
      LIMIT CASE WHEN maximum IS NULL THEN minimum::bigint ELSE maximum::bigint+1 END
     ) matching_edges) AS degree
     FROM truss.object o WHERE EXISTS(SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=selected_relation.rel_type_id AND e.target_type=o.type_id)) anchors;
   END IF;
   scope:=jsonb_build_object('documentId',selected_relation.document_id,'moduleId',selected_relation.module,'relationshipId',selected_relation.rel_id,'side',side);
   IF low_count>0 THEN violations:=array_append(violations,scope||jsonb_build_object('rule','relationship.min','affectedObjectCount',low_count::text));END IF;
   IF high_count>0 THEN violations:=array_append(violations,scope||jsonb_build_object('rule','relationship.max','affectedObjectCount',high_count::text));END IF;
  END LOOP;
 END LOOP;
 FOR owner IN SELECT DISTINCT item.value->>'documentId' AS document_id,item.value->>'moduleId' AS module_id FROM unnest(scopes) AS item(value) LOOP
  IF NOT truss.runtime_can_read(owner.document_id,owner.module_id) THEN
   RAISE EXCEPTION 'current module authority changed during compatibility validation' USING ERRCODE='42501';END IF;
 END LOOP;
 IF cardinality(violations)=0 THEN RETURN NULL;END IF;
 result:=convert_to(to_jsonb(violations)::text,'UTF8');
 IF octet_length(result)>16777216 THEN
  RAISE EXCEPTION 'complete compatibility violation result exceeds byte limit' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_scalar_violations(bytea) FROM PUBLIC;

-- The current acceptance route supplies exact original candidate documents.
CREATE FUNCTION truss.catalog_scalar_violations_with_sources(declarations_bytes bytea,documents_bytes bytea) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE rec jsonb;field jsonb;item jsonb;node jsonb;source_indexes jsonb;
 parsed_declarations jsonb;parsed_documents jsonb;scopes jsonb[]:=ARRAY[]::jsonb[];result bytea;
BEGIN
 parsed_declarations:=convert_from(declarations_bytes,'UTF8')::jsonb;
 parsed_documents:=convert_from(documents_bytes,'UTF8')::jsonb;
 WITH needed_documents AS MATERIALIZED (
  SELECT DISTINCT (r.value->>'documentId') COLLATE "C" document_id
  FROM jsonb_array_elements(parsed_declarations) d
  CROSS JOIN LATERAL jsonb_array_elements(d.value->'records') r
  WHERE EXISTS(SELECT 1 FROM jsonb_array_elements(r.value->'fields') f
   WHERE f.value->'declaration'->>'cardinality' IN ('array','map'))
 )
 SELECT coalesce(jsonb_object_agg(d.value->>'documentId',
   truss.catalog_item_source_index(d.value->>'originalText')),'{}'::jsonb)
 INTO source_indexes
 FROM jsonb_array_elements(parsed_documents) d
 JOIN needed_documents n ON n.document_id=d.value->>'documentId' COLLATE "C";
 FOR rec IN SELECT r.value FROM jsonb_array_elements(parsed_declarations) d CROSS JOIN LATERAL jsonb_array_elements(d.value->'records') r LOOP
  IF NOT EXISTS(SELECT 1 FROM truss.type_def t WHERE t.document_id=rec->>'documentId' AND t.module=rec->>'moduleId' AND t.element=rec->>'elementId' AND t.retired_rev IS NULL) THEN CONTINUE;END IF;
  FOR field IN SELECT value FROM jsonb_array_elements(rec->'fields') LOOP
   IF field->'declaration'->>'cardinality' NOT IN ('array','map') THEN CONTINUE;END IF;
   item:=truss.catalog_item_definition_indexed(source_indexes->(rec->>'documentId'),rec->>'documentId',1,0,field->'declaration'->'itemType');
   IF truss.runtime_item_chain_readable(item) IS NOT TRUE THEN RAISE EXCEPTION 'complete candidate item readers required for compatibility counts' USING ERRCODE='42501';END IF;
   FOR node IN SELECT value FROM jsonb_array_elements(jsonb_build_array(item)||coalesce(item->'descendants','[]'::jsonb)) LOOP
    scopes:=array_append(scopes,jsonb_build_object('documentId',node->>'documentId','moduleId',node->'reference'->>'module'));
   END LOOP;
  END LOOP;
 END LOOP;
 result:=truss.catalog_scalar_violations(declarations_bytes);
 FOR node IN SELECT value FROM unnest(scopes) AS item(value) LOOP
  IF truss.runtime_can_read(node->>'documentId',node->>'moduleId') IS NOT TRUE THEN RAISE EXCEPTION 'candidate item authority changed during compatibility counts' USING ERRCODE='42501';END IF;
 END LOOP;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_scalar_violations_with_sources(bytea,bytea) FROM PUBLIC;

-- Classify each active declaration by the constraint that actually rejects it.
CREATE FUNCTION truss.catalog_enforcement(selected_revision int) RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT coalesce(jsonb_agg(entry ORDER BY entry->>'rule',entry->>'documentId',entry->>'moduleId',entry->>'elementId',coalesce(entry->>'keyId',''),coalesce(entry->>'side','')),'[]'::jsonb)
 FROM (
  SELECT jsonb_build_object('rule','key.unique','enforcement','engine','documentId',t.document_id,'moduleId',t.module,'elementId',t.element,'keyId',k.key_id,
   'evidence','write path checks business key uniqueness; key_bucket_guard protects lock identity only') AS entry
  FROM truss.key_def k JOIN truss.type_def t ON t.type_id=k.type_id
  WHERE k.since_rev<=selected_revision AND (k.retired_rev IS NULL OR k.retired_rev>selected_revision)
  UNION ALL
  SELECT jsonb_build_object('rule','relationship.endpoint_types','enforcement','database','documentId',r.document_id,'moduleId',r.module,'elementId',r.rel_id,'evidence','edge_endpoint_types_fk')
  FROM truss.rel_def r
  WHERE r.since_rev<=selected_revision AND (r.retired_rev IS NULL OR r.retired_rev>selected_revision)
   AND EXISTS(SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=r.rel_type_id)
  UNION ALL
  SELECT jsonb_build_object('rule','relationship.multiplicity','enforcement','engine','documentId',r.document_id,'moduleId',r.module,'elementId',r.rel_id,'evidence','write path count; edge_limit is not a constraint on truss.edge')
  FROM truss.rel_def r
  WHERE r.since_rev<=selected_revision AND (r.retired_rev IS NULL OR r.retired_rev>selected_revision)
   AND (r.source_min>0 OR r.target_min>0 OR r.source_max IS NOT NULL OR r.target_max IS NOT NULL)
  UNION ALL
  SELECT jsonb_build_object('rule','property.facets','enforcement','engine','documentId',t.document_id,'moduleId',p.declaration_module,'elementId',p.element,'evidence','runtime scalar validation, no table check')
  FROM truss.prop_def p JOIN truss.type_def t ON t.type_id=p.type_id
  WHERE p.since_rev<=selected_revision AND (p.retired_rev IS NULL OR p.retired_rev>selected_revision)
   AND truss.checked_scalar_facets(p.scalar_type,p.facets) IS TRUE
  UNION ALL
  SELECT jsonb_build_object('rule','property.facets','enforcement','none','documentId',t.document_id,'moduleId',p.declaration_module,'elementId',p.element,'evidence','facet is stored and not checked')
  FROM truss.prop_def p JOIN truss.type_def t ON t.type_id=p.type_id
  WHERE p.since_rev<=selected_revision AND (p.retired_rev IS NULL OR p.retired_rev>selected_revision)
   AND p.facets IS NOT NULL AND p.facets<>'{}'::jsonb
   AND truss.checked_scalar_facets(p.scalar_type,p.facets) IS NOT TRUE
 ) rules;
$$;
REVOKE ALL ON FUNCTION truss.catalog_enforcement(int) FROM PUBLIC;
