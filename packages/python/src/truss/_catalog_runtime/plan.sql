-- Compact native catalog plan. Original source meaning; no full-operation snapshots.
CREATE FUNCTION truss.catalog_planned_changes(records jsonb) RETURNS SETOF truss.schema_change
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT (ROW((r.value->>'rev')::int,(r.value->>'seq')::int,r.value->>'kind',(r.value->>'def_id')::int,
  r.value->'before',r.value->'after')::truss.schema_change).* FROM jsonb_array_elements(records) r;
$$;
REVOKE ALL ON FUNCTION truss.catalog_planned_changes(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_plan_source(records jsonb,definition jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original jsonb;selected jsonb;
BEGIN
 SELECT (d.value->>'document')::jsonb INTO STRICT original FROM jsonb_array_elements(records->'schema_doc') d
  WHERE d.value->>'rev'=definition->>'definition_rev' AND d.value->>'ord'=definition->>'definition_doc_ord'
   AND d.value->>'doc_id'=definition->>'definition_document_id';
 SELECT e.value INTO STRICT selected FROM jsonb_array_elements(original->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN definition ? 'rel_id' THEN m.value->'relationships' ELSE m.value->'elements' END) e
  WHERE m.value->>'id'=definition->>'module' AND e.value->>'id'=coalesce(definition->>'rel_id',definition->>'element');
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_plan_source(jsonb,jsonb) FROM PUBLIC;

-- Compute a complete revision from an independently reconstructed prestate.
-- This planner is private; acceptance and its protected persistence are separate.
CREATE FUNCTION truss.catalog_revision_plan(prior jsonb,fresh jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET bytea_output=hex AS $$
DECLARE result jsonb:=prior;types jsonb:=coalesce(prior->'type_def','[]');properties jsonb:=coalesce(prior->'prop_def','[]');
 keys jsonb:=coalesce(prior->'key_def','[]');relations jsonb:=coalesce(prior->'rel_def','[]');
 lineages jsonb:=coalesce(prior->'relationship_lineage','[]');endpoints jsonb:=coalesce(prior->'rel_endpoint','[]');
 changes jsonb:=coalesce(prior->'schema_change','[]');type_map jsonb:='{}';property_map jsonb:='{}';relationship_map jsonb:='{}';
 row jsonb;old jsonb;candidate jsonb;old_source jsonb;new_source jsonb;component jsonb;remapped jsonb;
 tightening boolean;facet_map jsonb;compact_insertions boolean;
 assigned int;type_next int;property_next int;relationship_next int;key_next int;sequence int:=0;revision int;
BEGIN
 -- Original archives plus normalized rows already preserve newly inserted definitions.
 -- Retained-row changes still keep their complete before/after history.
 compact_insertions:=NOT EXISTS(SELECT 1 FROM jsonb_array_elements(fresh->'schema_doc') d
  WHERE d.value->'validation'->>'storageFormat' IS DISTINCT FROM 'truss-catalog-source/2');
 -- On the empty genesis there are no old identities to remap or evolve.
 -- Materialize each normalized source row and insertion event once.
 IF prior->'type_def'='[]'::jsonb AND prior->'prop_def'='[]'::jsonb AND prior->'key_def'='[]'::jsonb
  AND prior->'rel_def'='[]'::jsonb AND prior->'schema_doc'='[]'::jsonb
  AND prior->'relationship_lineage'='[]'::jsonb AND prior->'rel_endpoint'='[]'::jsonb
  AND prior->'schema_change'='[]'::jsonb AND jsonb_array_length(prior->'schema_rev')=1
  AND prior->'schema_rev'->0=fresh->'schema_rev'->0
  AND jsonb_array_length(fresh->'schema_rev')=2 AND fresh->'schema_rev'->1->>'rev'='1' THEN
  IF compact_insertions THEN RETURN fresh||jsonb_build_object('schema_change','[]'::jsonb);END IF;
  WITH events AS (
   SELECT 0 family,r.ordinality ordinal,'type' kind,(r.value->>'type_id')::int def_id,
    to_jsonb(jsonb_populate_record(NULL::truss.type_def,r.value)) after FROM jsonb_array_elements(fresh->'type_def') WITH ORDINALITY r
   UNION ALL
   SELECT 1,r.ordinality,'prop',(r.value->>'prop_id')::int,to_jsonb(jsonb_populate_record(NULL::truss.prop_def,r.value))
    FROM jsonb_array_elements(fresh->'prop_def') WITH ORDINALITY r
   UNION ALL
   SELECT 2,r.ordinality,'rel',(r.value->>'rel_type_id')::int,to_jsonb(jsonb_populate_record(NULL::truss.rel_def,r.value))
    FROM jsonb_array_elements(fresh->'rel_def') WITH ORDINALITY r),
  numbered AS (SELECT *,row_number() OVER(ORDER BY family,ordinal) seq FROM events)
  SELECT coalesce(jsonb_agg(jsonb_build_object('rev',1,'seq',seq,'kind',kind,'def_id',def_id,'before',NULL,'after',after) ORDER BY seq),'[]'::jsonb)
   INTO changes FROM numbered;
  RETURN fresh||jsonb_build_object('schema_change',changes);
 END IF;
 SELECT coalesce(max((v.value->>'type_id')::int),0) INTO type_next FROM jsonb_array_elements(types) v;
 SELECT coalesce(max((v.value->>'prop_id')::int),0) INTO property_next FROM jsonb_array_elements(properties) v;
 SELECT coalesce(max((v.value->>'rel_type_id')::int),0) INTO relationship_next FROM jsonb_array_elements(relations) v;
 SELECT max((v.value->>'rev')::int) INTO STRICT revision FROM jsonb_array_elements(fresh->'schema_rev') v;
 -- A submitted document cannot implicitly retire an omitted declaration.
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(types) p WHERE EXISTS(SELECT 1 FROM jsonb_array_elements(fresh->'schema_doc') d WHERE d.value->>'doc_id'=p.value->>'document_id')
  AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(fresh->'type_def') n WHERE n.value->>'document_id'=p.value->>'document_id' AND n.value->>'module'=p.value->>'module' AND n.value->>'element'=p.value->>'element')) THEN
  RAISE EXCEPTION 'record retirement requires explicit support' USING ERRCODE='0A000';END IF;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'type_def') LOOP
  SELECT v.value INTO old FROM jsonb_array_elements(types) v WHERE v.value->>'document_id'=row->>'document_id' AND v.value->>'module'=row->>'module' AND v.value->>'element'=row->>'element';
  IF old IS NULL THEN type_next:=type_next+1;assigned:=type_next;
  ELSE assigned:=(old->>'type_id')::int;END IF;
  type_map:=type_map||jsonb_build_object(row->>'type_id',assigned);
  candidate:=row||jsonb_build_object('type_id',assigned);
  IF old IS NOT NULL THEN
   old_source:=truss.catalog_plan_source(prior,old);new_source:=truss.catalog_plan_source(fresh,row);
   IF old_source=new_source THEN CONTINUE;END IF;
   IF old_source-ARRAY['members','name','keys'] IS DISTINCT FROM new_source-ARRAY['members','name','keys']
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(coalesce(old_source->'keys','[]')) k WHERE NOT EXISTS(SELECT 1 FROM jsonb_array_elements(coalesce(new_source->'keys','[]')) n WHERE n.value=k.value))
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(old_source->'members') m GROUP BY m.value HAVING count(*)>(SELECT count(*) FROM jsonb_array_elements(new_source->'members') n WHERE n.value=m.value)) THEN
    RAISE EXCEPTION 'existing record keys, meaning and retained members require explicit evolution support' USING ERRCODE='0A000';END IF;
   candidate:=candidate||jsonb_build_object('since_rev',old->'since_rev','doc_ord',old->'doc_ord');
   SELECT coalesce(jsonb_agg(v.value),'[]') INTO types FROM jsonb_array_elements(types) v WHERE v.value->>'type_id'<>assigned::text;
  END IF;
  types:=types||jsonb_build_array(candidate);sequence:=sequence+1;
  IF old IS NOT NULL OR NOT compact_insertions THEN
  changes:=changes||jsonb_build_array(jsonb_build_object('rev',revision,'seq',sequence,'kind','type','def_id',assigned,'before',CASE WHEN old IS NULL THEN 'null'::jsonb ELSE to_jsonb(jsonb_populate_record(NULL::truss.type_def,old)) END,'after',to_jsonb(jsonb_populate_record(NULL::truss.type_def,candidate))));
  END IF;
 END LOOP;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'prop_def') LOOP
  assigned:=(type_map->> (row->>'type_id'))::int;
  SELECT v.value INTO old FROM jsonb_array_elements(properties) v WHERE v.value->>'type_id'=assigned::text AND v.value->>'declaration_module'=row->>'declaration_module' AND v.value->>'element'=row->>'element';
  IF old IS NULL THEN
   IF EXISTS(SELECT 1 FROM jsonb_array_elements(prior->'type_def') t WHERE t.value->>'type_id'=assigned::text) AND row->>'nullability' NOT IN ('required','absent-allowed') THEN
    RAISE EXCEPTION 'supported new field nullability required' USING ERRCODE='0A000';END IF;
   property_next:=property_next+1;
  END IF;
  property_map:=property_map||jsonb_build_object(row->>'prop_id',CASE WHEN old IS NULL THEN property_next ELSE (old->>'prop_id')::int END);
  candidate:=row||jsonb_build_object('type_id',assigned,'prop_id',(property_map->> (row->>'prop_id'))::int);
  IF EXISTS(SELECT 1 FROM jsonb_array_elements(prior->'prop_def') p WHERE p.value->>'type_id'=assigned::text AND p.value->>'prop_id'<>candidate->>'prop_id' AND p.value->>'name'=candidate->>'name') THEN
   RAISE EXCEPTION 'field name occupied in prior catalog' USING ERRCODE='0A000';END IF;
  IF old IS NOT NULL THEN
   IF old->>'cardinality' IN ('array','map') THEN
    IF truss.catalog_item_meaning(old->'item') IS DISTINCT FROM truss.catalog_item_meaning(candidate->'item') THEN RAISE EXCEPTION 'container item evolution requires explicit support' USING ERRCODE='0A000';END IF;
    candidate:=candidate||jsonb_build_object('item',old->'item');
   END IF;
   IF old->'_originalField'=row->'_originalField' THEN CONTINUE;END IF;
   -- Name-only changes retain storage and key identities.
   IF ((old->'_originalField') - 'name') = ((row->'_originalField') - 'name') THEN
    NULL; -- Storage meaning and retained key components are unchanged.
   ELSE
   tightening:=(old->>'nullability'='absent-allowed' AND row->>'nullability'='required') IS TRUE;
   IF tightening THEN
    IF ((old->>'cardinality'='one' AND row->>'cardinality'='one' AND old->>'scalar_type' IN ('string','integer','decimal','boolean','timestamp','binary','date') AND row->>'scalar_type'=old->>'scalar_type') OR (old->>'cardinality' IN ('array','map') AND row->>'cardinality'=old->>'cardinality' AND truss.valid_property_definition(jsonb_populate_record(NULL::truss.prop_def,candidate)) IS TRUE)) IS DISTINCT FROM TRUE THEN
     RAISE EXCEPTION 'required tightening requires a supported retained scalar or flat container' USING ERRCODE='0A000';END IF;
    FOREACH facet_map IN ARRAY ARRAY[coalesce(old->'_originalField'->'facets','{}'::jsonb),coalesce(row->'_originalField'->'facets','{}'::jsonb)] LOOP
     IF truss.known_scalar_facets(old->>'scalar_type',facet_map) IS NOT TRUE THEN
      RAISE EXCEPTION 'required tightening needs known scalar facets' USING ERRCODE='0A000';END IF;
    END LOOP;
   END IF;
   -- Historical nullability-only folds keep their original admission. Actual
   -- facet changes require both maps to belong to this explicit native subset.
   IF coalesce(old->'_originalField'->'facets','{}'::jsonb) IS DISTINCT FROM coalesce(row->'_originalField'->'facets','{}'::jsonb) THEN
    IF truss.known_scalar_facets(old->>'scalar_type',old->'_originalField'->'facets') IS NOT TRUE
     OR truss.known_scalar_facets(row->>'scalar_type',row->'_originalField'->'facets') IS NOT TRUE THEN
     RAISE EXCEPTION 'known native scalar facet transition required' USING ERRCODE='0A000';END IF;
   END IF;
   IF ((old->'_originalField')-ARRAY['nullability','facets']) IS DISTINCT FROM ((row->'_originalField')-ARRAY['nullability','facets'])
    OR NOT (old->>'nullability'=row->>'nullability' OR old->>'nullability'='required' AND row->>'nullability'='absent-allowed' OR tightening)
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(keys) k WHERE k.value->>'type_id'=assigned::text AND k.value->'prop_ids' @> jsonb_build_array((old->>'prop_id')::int)) THEN
    RAISE EXCEPTION 'existing field change requires explicit evolution support' USING ERRCODE='0A000';END IF;
   END IF;
   candidate:=candidate||jsonb_build_object('since_rev',old->'since_rev','doc_ord',old->'doc_ord');
   SELECT coalesce(jsonb_agg(v.value),'[]') INTO properties FROM jsonb_array_elements(properties) v WHERE v.value->>'prop_id'<>old->>'prop_id';
  END IF;
  IF EXISTS(SELECT 1 FROM jsonb_array_elements(properties) p WHERE p.value->>'type_id'=assigned::text AND p.value->>'name'=candidate->>'name') THEN
   RAISE EXCEPTION 'retained field name collision requires rebind support' USING ERRCODE='0A000';END IF;
  properties:=properties||jsonb_build_array(candidate);sequence:=sequence+1;
  IF old IS NOT NULL OR NOT compact_insertions THEN
  changes:=changes||jsonb_build_array(jsonb_build_object('rev',revision,'seq',sequence,'kind','prop','def_id',(candidate->>'prop_id')::int,'before',CASE WHEN old IS NULL THEN 'null'::jsonb ELSE to_jsonb(jsonb_populate_record(NULL::truss.prop_def,old)) END,'after',to_jsonb(jsonb_populate_record(NULL::truss.prop_def,candidate))));
  END IF;
 END LOOP;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'key_def') LOOP
  assigned:=(type_map->> (row->>'type_id'))::int;remapped:='[]';
  FOR component IN SELECT value FROM jsonb_array_elements(row->'prop_ids') LOOP remapped:=remapped||jsonb_build_array((property_map->> (component#>>'{}'))::int);END LOOP;
  SELECT v.value INTO old FROM jsonb_array_elements(keys) v WHERE v.value->>'type_id'=assigned::text AND v.value->>'key_id'=row->>'key_id';
  IF old IS NOT NULL THEN
   IF old->'prop_ids' IS DISTINCT FROM remapped OR old->'is_primary' IS DISTINCT FROM row->'is_primary' THEN RAISE EXCEPTION 'existing key change requires backfill support' USING ERRCODE='0A000';END IF;
  ELSE
   IF EXISTS(SELECT 1 FROM jsonb_array_elements(prior->'type_def') t WHERE t.value->>'type_id'=assigned::text) THEN
    IF (row->>'is_primary')::boolean IS NOT FALSE OR EXISTS(SELECT 1 FROM jsonb_array_elements(remapped) component WHERE NOT EXISTS(
     SELECT 1 FROM jsonb_array_elements(properties) p WHERE p.value->>'type_id'=assigned::text AND p.value->>'prop_id'=component.value#>>'{}'
      AND (EXISTS(SELECT 1 FROM jsonb_array_elements(prior->'prop_def') old_property
        WHERE old_property.value->>'prop_id'=p.value->>'prop_id' AND old_property.value->>'type_id'=assigned::text
         AND old_property.value->>'nullability'='required' AND old_property.value->>'cardinality'='one'
         AND old_property.value->>'scalar_type' IN ('string','integer','decimal','boolean','binary'))
       OR ((p.value->>'since_rev')::int=revision AND NOT EXISTS(
        SELECT 1 FROM jsonb_array_elements(prior->'prop_def') old_property
         WHERE old_property.value->>'prop_id'=p.value->>'prop_id' AND old_property.value->>'type_id'=assigned::text)))
      AND p.value->>'nullability'='required' AND p.value->>'cardinality'='one' AND p.value->>'scalar_type' IN ('string','integer','decimal','boolean','binary'))) THEN
     RAISE EXCEPTION 'new alternate key requires existing or newly rebound required scalar components' USING ERRCODE='0A000';END IF;
    SELECT coalesce(max((k.value->>'key_num')::int),0)+1 INTO key_next FROM jsonb_array_elements(keys) k WHERE k.value->>'type_id'=assigned::text;
    IF key_next>32767 THEN RAISE EXCEPTION 'owner-local key range exhausted' USING ERRCODE='54000';END IF;
   ELSE key_next:=(row->>'key_num')::int;END IF;
   keys:=keys||jsonb_build_array(row||jsonb_build_object('type_id',assigned,'prop_ids',remapped,'key_num',key_next));
  END IF;
 END LOOP;
 -- Relationship IDs and lineage remain stable; independent multiplicity evolution retains endpoints.
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'rel_def') LOOP
  SELECT v.value INTO old FROM jsonb_array_elements(relations) v WHERE v.value->>'document_id'=row->>'document_id' AND v.value->>'module'=row->>'module' AND v.value->>'rel_id'=row->>'rel_id';
  IF old IS NULL THEN relationship_next:=relationship_next+1;assigned:=relationship_next;ELSE assigned:=(old->>'rel_type_id')::int;END IF;
  relationship_map:=relationship_map||jsonb_build_object(row->>'rel_type_id',assigned);
  candidate:=row||jsonb_build_object('rel_type_id',assigned);
  IF old IS NOT NULL THEN
   old_source:=truss.catalog_plan_source(prior,old);new_source:=truss.catalog_plan_source(fresh,row);
   IF old_source=new_source THEN CONTINUE;END IF;
   IF (old_source-ARRAY['name','inverse','source','target','sourceMultiplicity','targetMultiplicity']) IS DISTINCT FROM (new_source-ARRAY['name','inverse','source','target','sourceMultiplicity','targetMultiplicity'])
    OR (old_source ? 'inverse') IS DISTINCT FROM (new_source ? 'inverse')
    OR (old_source->'name' IS DISTINCT FROM new_source->'name' AND (jsonb_typeof(old_source->'name') IS DISTINCT FROM 'string' OR jsonb_typeof(new_source->'name') IS DISTINCT FROM 'string'))
    OR (old_source->'inverse' IS DISTINCT FROM new_source->'inverse' AND (jsonb_typeof(old_source->'inverse') IS DISTINCT FROM 'string' OR jsonb_typeof(new_source->'inverse') IS DISTINCT FROM 'string'))
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(old_source->'source') x WHERE NOT (new_source->'source') @> jsonb_build_array(x.value))
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(old_source->'target') x WHERE NOT (new_source->'target') @> jsonb_build_array(x.value)) THEN
    RAISE EXCEPTION 'relationship source meaning must be retained' USING ERRCODE='0A000';END IF;
   IF ((candidate->>'source_min')::int>(old->>'source_min')::int OR (candidate->>'target_min')::int>(old->>'target_min')::int
    OR candidate->'source_max'<>'null'::jsonb AND (old->'source_max'='null'::jsonb OR (candidate->>'source_max')::int<(old->>'source_max')::int)
    OR candidate->'target_max'<>'null'::jsonb AND (old->'target_max'='null'::jsonb OR (candidate->>'target_max')::int<(old->>'target_max')::int))
    AND (old_source->'source' IS DISTINCT FROM new_source->'source' OR old_source->'target' IS DISTINCT FROM new_source->'target') THEN
    RAISE EXCEPTION 'tightening requires unchanged endpoint declarations' USING ERRCODE='0A000';END IF;
   IF old->>'lifecycle' IS DISTINCT FROM 'independent' OR candidate->>'lifecycle' IS DISTINCT FROM 'independent'
    OR (old-ARRAY['name','source_min','source_max','target_min','target_max','definition_rev','definition_doc_ord','definition_document_id','doc_ord','since_rev']) IS DISTINCT FROM (candidate-ARRAY['name','source_min','source_max','target_min','target_max','definition_rev','definition_doc_ord','definition_document_id','doc_ord','since_rev'])
 THEN
    RAISE EXCEPTION 'relationship change requires unchanged independent endpoints and meaning' USING ERRCODE='0A000';END IF;
   candidate:=candidate||jsonb_build_object('since_rev',old->'since_rev','doc_ord',old->'doc_ord');
   SELECT coalesce(jsonb_agg(v.value),'[]') INTO relations FROM jsonb_array_elements(relations) v WHERE v.value->>'rel_type_id'<>assigned::text;
  END IF;
  relations:=relations||jsonb_build_array(candidate);sequence:=sequence+1;
  IF old IS NOT NULL OR NOT compact_insertions THEN
  changes:=changes||jsonb_build_array(jsonb_build_object('rev',revision,'seq',sequence,'kind','rel','def_id',assigned,'before',CASE WHEN old IS NULL THEN 'null'::jsonb ELSE to_jsonb(jsonb_populate_record(NULL::truss.rel_def,old)) END,'after',to_jsonb(jsonb_populate_record(NULL::truss.rel_def,candidate))));
  END IF;
 END LOOP;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'relationship_lineage') LOOP
  assigned:=(relationship_map->> (row->>'rel_type_id'))::int;
  IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(lineages) p WHERE p.value->>'rel_type_id'=assigned::text) THEN lineages:=lineages||jsonb_build_array(row||jsonb_build_object('rel_type_id',assigned));END IF;
 END LOOP;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'rel_endpoint') LOOP
  candidate:=jsonb_build_object('rel_type_id',(relationship_map->> (row->>'rel_type_id'))::int,'source_type',(type_map->> (row->>'source_type'))::int,'target_type',(type_map->> (row->>'target_type'))::int);
  IF NOT endpoints @> jsonb_build_array(candidate) THEN endpoints:=endpoints||jsonb_build_array(candidate);END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(relations) p WHERE EXISTS(SELECT 1 FROM jsonb_array_elements(fresh->'schema_doc') d WHERE d.value->>'doc_id'=p.value->>'document_id')
  AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(fresh->'rel_def') n WHERE n.value->>'document_id'=p.value->>'document_id' AND n.value->>'module'=p.value->>'module' AND n.value->>'rel_id'=p.value->>'rel_id')) THEN
  RAISE EXCEPTION 'relationship retirement requires explicit support' USING ERRCODE='0A000';END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(prior->'schema_rev') p JOIN jsonb_array_elements(fresh->'schema_rev') f ON p.value->>'rev'=f.value->>'rev' WHERE p.value IS DISTINCT FROM f.value) THEN
  RAISE EXCEPTION 'original revision history required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(f.value),'[]') INTO remapped FROM jsonb_array_elements(fresh->'schema_rev') f WHERE NOT EXISTS(SELECT 1 FROM jsonb_array_elements(prior->'schema_rev') p WHERE p.value->>'rev'=f.value->>'rev');
 result:=result||jsonb_build_object('schema_rev',coalesce(prior->'schema_rev','[]')||remapped,'schema_doc',coalesce(prior->'schema_doc','[]')||(fresh->'schema_doc'),
  'type_def',types,'prop_def',properties,'key_def',keys,'rel_def',relations,'relationship_lineage',lineages,'rel_endpoint',endpoints,'schema_change',changes);
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_revision_plan(jsonb,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_expected_records(declarations_bytes bytea,documents_bytes bytea,
 origin_bytes bytea,accepted_clock timestamptz,genesis_clock timestamptz,
 selected_revision int DEFAULT 1,type_offset int DEFAULT 0,property_offset int DEFAULT 0,relationship_offset int DEFAULT 0)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE validated_declarations jsonb;validated_documents jsonb;validated_origin jsonb;
BEGIN
 IF selected_revision<1 OR type_offset<0 OR property_offset<0 OR relationship_offset<0 THEN
  RAISE EXCEPTION 'valid catalog allocation basis required' USING ERRCODE='22023';END IF;
 validated_declarations:=convert_from(declarations_bytes,'UTF8')::jsonb;
 validated_documents:=convert_from(documents_bytes,'UTF8')::jsonb;
 validated_origin:=convert_from(origin_bytes,'UTF8')::jsonb;
 IF jsonb_typeof(validated_declarations) IS DISTINCT FROM 'array' OR jsonb_typeof(validated_documents) IS DISTINCT FROM 'array'
  OR jsonb_typeof(validated_origin) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'original record-plan shape required' USING ERRCODE='22023';END IF;
 RETURN (WITH docs AS MATERIALIZED (
  SELECT d.value,d.ordinality::int-1 ord FROM jsonb_array_elements(validated_documents) WITH ORDINALITY d),
 records AS MATERIALIZED (
  SELECT r.value,d.ord,type_offset+row_number() OVER(ORDER BY (r.value->>'documentId') COLLATE "C",(r.value->>'moduleId') COLLATE "C",(r.value->>'elementId') COLLATE "C")::int type_id
  FROM jsonb_array_elements(validated_declarations) a
  CROSS JOIN LATERAL jsonb_array_elements(a.value->'records') r JOIN docs d ON d.value->>'documentId'=r.value->>'documentId'),
 type_rows AS MATERIALIZED (
  SELECT r.type_id,jsonb_build_object('document_id',r.value->>'documentId','type_id',r.type_id,'module',r.value->>'moduleId',
   'element',r.value->>'elementId','kind','record','provisional',false,'since_rev',selected_revision,'doc_ord',r.ord,
   'lineage_profile','truss-type-lineage/0.1.0','lineage_bytes',chr(92)||'x'||encode(l.bytes,'hex'),
   'lineage_sha256',chr(92)||'x'||encode(sha256(l.bytes),'hex'),'definition_source_kind','accepted_document',
   'definition_rev',selected_revision,'definition_doc_ord',r.ord,'definition_document_id',r.value->>'documentId') value
  FROM records r CROSS JOIN LATERAL (SELECT truss.runtime_lineage_bytes('record',r.value->>'documentId',r.value->>'moduleId',r.value->>'elementId') bytes) l),
 field_input AS MATERIALIZED (
  SELECT r.type_id,r.ord,r.value->>'documentId' document_id,f.value,
   property_offset+row_number() OVER(ORDER BY (r.value->>'documentId') COLLATE "C",(r.value->>'moduleId') COLLATE "C",
    (r.value->>'elementId') COLLATE "C",(f.value->>'fieldModule') COLLATE "C",(f.value->'declaration'->>'id') COLLATE "C")::int prop_id
  FROM records r CROSS JOIN LATERAL jsonb_array_elements(r.value->'fields') f),
 prop_rows AS MATERIALIZED (
  SELECT f.type_id,f.prop_id,f.value->>'fieldModule' field_module,f.value->'declaration'->>'id' element_id,
   jsonb_build_object('prop_id',f.prop_id,'type_id',f.type_id,'element',f.value->'declaration'->>'id',
    'declaration_module',f.value->>'fieldModule','name',coalesce(f.value->'declaration'->>'name',f.value->'declaration'->>'id'),
    'scalar_type',f.value->'declaration'->>'scalarType','nullability',f.value->'declaration'->>'nullability',
    'cardinality',f.value->'declaration'->>'cardinality','facets',f.value->'declaration'->'facets',
    'item',CASE WHEN f.value->'declaration'->>'cardinality' IN ('array','map') THEN truss.catalog_item_definition(d.value->>'originalText',f.document_id,selected_revision,f.ord,f.value->'declaration'->'itemType') ELSE f.value->'declaration'->'itemType' END,
    'home','json','since_rev',selected_revision,'doc_ord',f.ord,'definition_source_kind','accepted_document',
    'definition_rev',selected_revision,'definition_doc_ord',f.ord,'definition_document_id',f.document_id,'_originalField',f.value->'declaration') value
  FROM field_input f JOIN docs d USING(ord)),
 key_input AS MATERIALIZED (
  SELECT r.type_id,r.ord,r.value->>'documentId' document_id,k.value,
   row_number() OVER(PARTITION BY r.type_id ORDER BY (k.value->>'id') COLLATE "C")::int key_num
  FROM records r CROSS JOIN LATERAL jsonb_array_elements(r.value->'keys') k),
 key_components AS (
  SELECT k.type_id,k.key_num,jsonb_agg(p.prop_id ORDER BY ref.ordinality) ids
  FROM key_input k CROSS JOIN LATERAL jsonb_array_elements(k.value->'fields') WITH ORDINALITY ref
  JOIN prop_rows p ON p.type_id=k.type_id AND p.field_module=ref.value->>'module' AND p.element_id=ref.value->>'element'
  GROUP BY k.type_id,k.key_num),
 key_rows AS (
  SELECT k.type_id,k.key_num,jsonb_build_object('type_id',k.type_id,'key_id',k.value->>'id','key_num',k.key_num,
   'prop_ids',coalesce(c.ids,'[]'::jsonb),'is_primary',coalesce((k.value->>'primary')::boolean,false),'since_rev',selected_revision,
   'definition_source_kind','accepted_document','definition_rev',selected_revision,'definition_doc_ord',k.ord,'definition_document_id',k.document_id) value
  FROM key_input k LEFT JOIN key_components c USING(type_id,key_num)),
 rel_input AS MATERIALIZED (
  SELECT r.value,d.ord,relationship_offset+row_number() OVER(ORDER BY (r.value->>'documentId') COLLATE "C",(r.value->>'moduleId') COLLATE "C",(r.value->'declaration'->>'id') COLLATE "C")::int rel_type_id
  FROM jsonb_array_elements(validated_declarations) a CROSS JOIN LATERAL jsonb_array_elements(a.value->'relationships') r
  JOIN docs d ON d.value->>'documentId'=r.value->>'documentId'),
 rel_rows AS MATERIALIZED (
  SELECT r.rel_type_id,jsonb_build_object('document_id',r.value->>'documentId','rel_type_id',r.rel_type_id,'module',r.value->>'moduleId',
   'rel_id',r.value->'declaration'->>'id','name',r.value->'declaration'->>'name',
   'source_min',(r.value->'declaration'->'sourceMultiplicity'->>'min')::int,'source_max',nullif(r.value->'declaration'->'sourceMultiplicity'->>'max','*')::int,
   'target_min',(r.value->'declaration'->'targetMultiplicity'->>'min')::int,'target_max',nullif(r.value->'declaration'->'targetMultiplicity'->>'max','*')::int,
   'lifecycle',r.value->'declaration'->>'targetLifecycle','directed',(r.value->'declaration'->>'directed')::boolean,
   'target_key',(r.value->'declaration'->'target'->-1)->>'key','composition',false,'since_rev',selected_revision,'doc_ord',r.ord,
   'definition_source_kind','accepted_document','definition_rev',selected_revision,'definition_doc_ord',r.ord,'definition_document_id',r.value->>'documentId') value
  FROM rel_input r),
 lineage_rows AS (
  SELECT r.rel_type_id,jsonb_build_object('rel_type_id',r.rel_type_id,'lineage_category','authored','identity_profile','truss-relationship-lineage-bytes/0.1.0',
   'original_identity_bytes',chr(92)||'x'||encode(l.bytes,'hex'),'identity_sha256',chr(92)||'x'||encode(sha256(l.bytes),'hex')) value
  FROM rel_input r CROSS JOIN LATERAL (SELECT truss.runtime_lineage_bytes('authored',r.value->>'documentId',r.value->>'moduleId',r.value->'declaration'->>'id') bytes) l),
 endpoint_rows AS (
  SELECT r.rel_type_id,s.ordinality source_ord,t.ordinality target_ord,
   jsonb_build_object('rel_type_id',r.rel_type_id,'source_type',sr.type_id,'target_type',tr.type_id) value
  FROM rel_input r CROSS JOIN LATERAL jsonb_array_elements(r.value->'declaration'->'source') WITH ORDINALITY s
  CROSS JOIN LATERAL jsonb_array_elements(r.value->'declaration'->'target') WITH ORDINALITY t
  JOIN records sr ON sr.value->>'documentId'=r.value->>'documentId' AND sr.value->>'moduleId'=s.value->>'module' AND sr.value->>'elementId'=s.value->>'element'
  JOIN records tr ON tr.value->>'documentId'=r.value->>'documentId' AND tr.value->>'moduleId'=t.value->>'module' AND tr.value->>'elementId'=t.value->>'element')
 SELECT jsonb_build_object(
  'schema_rev',CASE WHEN selected_revision=1 THEN jsonb_build_array(jsonb_build_object('rev',0,'accepted_at',genesis_clock,'origin','{}'::jsonb)) ELSE '[]'::jsonb END
   ||jsonb_build_array(jsonb_build_object('rev',selected_revision,'accepted_at',accepted_clock,'origin',validated_origin)),
  'schema_doc',(SELECT coalesce(jsonb_agg(jsonb_build_object('rev',selected_revision,'ord',d.ord,'doc_id',d.value->>'documentId','doc_revision',d.value->>'revision',
   'umf_version',d.value->>'umfVersion','content_sha256',encode(sha256(convert_to(d.value->>'originalText','UTF8')),'hex'),'document',d.value->>'originalText','validation',d.value->'validation') ORDER BY d.ord),'[]'::jsonb) FROM docs d),
  'type_def',(SELECT coalesce(jsonb_agg(value ORDER BY type_id),'[]'::jsonb) FROM type_rows),
  'prop_def',(SELECT coalesce(jsonb_agg(value ORDER BY prop_id),'[]'::jsonb) FROM prop_rows),
  'key_def',(SELECT coalesce(jsonb_agg(value ORDER BY type_id,key_num),'[]'::jsonb) FROM key_rows),
  'rel_def',(SELECT coalesce(jsonb_agg(value ORDER BY rel_type_id),'[]'::jsonb) FROM rel_rows),
  'relationship_lineage',(SELECT coalesce(jsonb_agg(value ORDER BY rel_type_id),'[]'::jsonb) FROM lineage_rows),
  'rel_endpoint',(SELECT coalesce(jsonb_agg(value ORDER BY rel_type_id,source_ord,target_ord),'[]'::jsonb) FROM endpoint_rows)));
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_expected_records(bytea,bytea,bytea,timestamptz,timestamptz,int,int,int,int) FROM PUBLIC;
