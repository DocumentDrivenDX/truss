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
 assigned int;type_next int;property_next int;relationship_next int;sequence int:=0;revision int;
BEGIN
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
   IF old_source-ARRAY['members','name'] IS DISTINCT FROM new_source-ARRAY['members','name']
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(old_source->'members') m GROUP BY m.value HAVING count(*)>(SELECT count(*) FROM jsonb_array_elements(new_source->'members') n WHERE n.value=m.value)) THEN
    RAISE EXCEPTION 'existing record keys, meaning and retained members require explicit evolution support' USING ERRCODE='0A000';END IF;
   candidate:=candidate||jsonb_build_object('since_rev',old->'since_rev','doc_ord',old->'doc_ord');
   SELECT coalesce(jsonb_agg(v.value),'[]') INTO types FROM jsonb_array_elements(types) v WHERE v.value->>'type_id'<>assigned::text;
  END IF;
  types:=types||jsonb_build_array(candidate);sequence:=sequence+1;
  changes:=changes||jsonb_build_array(jsonb_build_object('rev',revision,'seq',sequence,'kind','type','def_id',assigned,'before',CASE WHEN old IS NULL THEN 'null'::jsonb ELSE to_jsonb(jsonb_populate_record(NULL::truss.type_def,old)) END,'after',to_jsonb(jsonb_populate_record(NULL::truss.type_def,candidate))));
 END LOOP;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'prop_def') LOOP
  assigned:=(type_map->> (row->>'type_id'))::int;
  SELECT v.value INTO old FROM jsonb_array_elements(properties) v WHERE v.value->>'type_id'=assigned::text AND v.value->>'declaration_module'=row->>'declaration_module' AND v.value->>'element'=row->>'element';
  IF old IS NULL THEN
   IF EXISTS(SELECT 1 FROM jsonb_array_elements(prior->'type_def') t WHERE t.value->>'type_id'=assigned::text) AND row->>'nullability' IS DISTINCT FROM 'absent-allowed' THEN
    RAISE EXCEPTION 'new retained field must allow absence' USING ERRCODE='0A000';END IF;
   property_next:=property_next+1;
  END IF;
  property_map:=property_map||jsonb_build_object(row->>'prop_id',CASE WHEN old IS NULL THEN property_next ELSE (old->>'prop_id')::int END);
  candidate:=row||jsonb_build_object('type_id',assigned,'prop_id',(property_map->> (row->>'prop_id'))::int);
  IF old IS NOT NULL THEN
   IF old->>'cardinality' IN ('array','map') THEN
    IF old->'item'->'reference' IS DISTINCT FROM candidate->'item'->'reference' OR old->'item'->'declaration' IS DISTINCT FROM candidate->'item'->'declaration' THEN RAISE EXCEPTION 'container item evolution requires explicit support' USING ERRCODE='0A000';END IF;
    candidate:=candidate||jsonb_build_object('item',old->'item');
   END IF;
   IF old->'_originalField'=row->'_originalField' THEN CONTINUE;END IF;
   -- Historical nullability-only folds keep their original admission. Actual
   -- facet changes require both maps to belong to this explicit native subset.
   IF coalesce(old->'_originalField'->'facets','{}'::jsonb) IS DISTINCT FROM coalesce(row->'_originalField'->'facets','{}'::jsonb) THEN
    IF NOT ((coalesce(old->'_originalField'->'facets','{}'::jsonb)='{}'::jsonb
      OR old->>'scalar_type'='integer' AND old->'_originalField'->'facets'='{"integerWidth":{"bits":64,"signed":true}}'::jsonb
      OR old->>'scalar_type'='decimal' AND old->'_originalField'->'facets'='{"precision":18,"scale":4}'::jsonb) IS TRUE)
    OR NOT ((coalesce(row->'_originalField'->'facets','{}'::jsonb)='{}'::jsonb
      OR row->>'scalar_type'='integer' AND row->'_originalField'->'facets'='{"integerWidth":{"bits":64,"signed":true}}'::jsonb
      OR row->>'scalar_type'='decimal' AND row->'_originalField'->'facets'='{"precision":18,"scale":4}'::jsonb) IS TRUE) THEN
     RAISE EXCEPTION 'known native scalar facet transition required' USING ERRCODE='0A000';END IF;
   END IF;
   IF ((old->'_originalField')-ARRAY['nullability','facets']) IS DISTINCT FROM ((row->'_originalField')-ARRAY['nullability','facets'])
    OR NOT (old->>'nullability'=row->>'nullability' OR old->>'nullability'='required' AND row->>'nullability'='absent-allowed')
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(keys) k WHERE k.value->>'type_id'=assigned::text AND k.value->'prop_ids' @> jsonb_build_array((old->>'prop_id')::int)) THEN
    RAISE EXCEPTION 'existing field change requires explicit evolution support' USING ERRCODE='0A000';END IF;
   candidate:=candidate||jsonb_build_object('since_rev',old->'since_rev','doc_ord',old->'doc_ord');
   SELECT coalesce(jsonb_agg(v.value),'[]') INTO properties FROM jsonb_array_elements(properties) v WHERE v.value->>'prop_id'<>old->>'prop_id';
  END IF;
  IF EXISTS(SELECT 1 FROM jsonb_array_elements(properties) p WHERE p.value->>'type_id'=assigned::text AND p.value->>'name'=candidate->>'name') THEN
   RAISE EXCEPTION 'retained field name collision requires rebind support' USING ERRCODE='0A000';END IF;
  properties:=properties||jsonb_build_array(candidate);sequence:=sequence+1;
  changes:=changes||jsonb_build_array(jsonb_build_object('rev',revision,'seq',sequence,'kind','prop','def_id',(candidate->>'prop_id')::int,'before',CASE WHEN old IS NULL THEN 'null'::jsonb ELSE to_jsonb(jsonb_populate_record(NULL::truss.prop_def,old)) END,'after',to_jsonb(jsonb_populate_record(NULL::truss.prop_def,candidate))));
 END LOOP;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'key_def') LOOP
  assigned:=(type_map->> (row->>'type_id'))::int;remapped:='[]';
  FOR component IN SELECT value FROM jsonb_array_elements(row->'prop_ids') LOOP remapped:=remapped||jsonb_build_array((property_map->> (component#>>'{}'))::int);END LOOP;
  SELECT v.value INTO old FROM jsonb_array_elements(keys) v WHERE v.value->>'type_id'=assigned::text AND v.value->>'key_id'=row->>'key_id';
  IF old IS NOT NULL THEN
   IF old->'prop_ids' IS DISTINCT FROM remapped OR old->'is_primary' IS DISTINCT FROM row->'is_primary' THEN RAISE EXCEPTION 'existing key change requires backfill support' USING ERRCODE='0A000';END IF;
  ELSE
   IF EXISTS(SELECT 1 FROM jsonb_array_elements(prior->'type_def') t WHERE t.value->>'type_id'=assigned::text) THEN RAISE EXCEPTION 'new key on retained record requires backfill support' USING ERRCODE='0A000';END IF;
   keys:=keys||jsonb_build_array(row||jsonb_build_object('type_id',assigned,'prop_ids',remapped));
  END IF;
 END LOOP;
 -- Relationship IDs and lineage remain stable; only independent widening is admitted.
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'rel_def') LOOP
  SELECT v.value INTO old FROM jsonb_array_elements(relations) v WHERE v.value->>'document_id'=row->>'document_id' AND v.value->>'module'=row->>'module' AND v.value->>'rel_id'=row->>'rel_id';
  IF old IS NULL THEN relationship_next:=relationship_next+1;assigned:=relationship_next;ELSE assigned:=(old->>'rel_type_id')::int;END IF;
  relationship_map:=relationship_map||jsonb_build_object(row->>'rel_type_id',assigned);
  candidate:=row||jsonb_build_object('rel_type_id',assigned);
  IF old IS NOT NULL THEN
   old_source:=truss.catalog_plan_source(prior,old);new_source:=truss.catalog_plan_source(fresh,row);
   IF old_source=new_source THEN CONTINUE;END IF;
   IF (old_source-ARRAY['source','target','sourceMultiplicity','targetMultiplicity']) IS DISTINCT FROM (new_source-ARRAY['source','target','sourceMultiplicity','targetMultiplicity'])
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(old_source->'source') x WHERE NOT (new_source->'source') @> jsonb_build_array(x.value))
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(old_source->'target') x WHERE NOT (new_source->'target') @> jsonb_build_array(x.value)) THEN
    RAISE EXCEPTION 'relationship source meaning must be retained' USING ERRCODE='0A000';END IF;
   IF old->>'lifecycle' IS DISTINCT FROM 'independent' OR candidate->>'lifecycle' IS DISTINCT FROM 'independent'
    OR (old-ARRAY['source_min','source_max','target_min','target_max','definition_rev','definition_doc_ord','definition_document_id','doc_ord','since_rev']) IS DISTINCT FROM (candidate-ARRAY['source_min','source_max','target_min','target_max','definition_rev','definition_doc_ord','definition_document_id','doc_ord','since_rev'])
    OR (candidate->>'source_min')::int>(old->>'source_min')::int OR (candidate->>'target_min')::int>(old->>'target_min')::int
    OR old->'source_max'='null'::jsonb AND candidate->'source_max'<>'null'::jsonb
    OR old->'target_max'='null'::jsonb AND candidate->'target_max'<>'null'::jsonb
    OR candidate->'source_max'<>'null'::jsonb AND (candidate->>'source_max')::int<(old->>'source_max')::int
    OR candidate->'target_max'<>'null'::jsonb AND (candidate->>'target_max')::int<(old->>'target_max')::int THEN
    RAISE EXCEPTION 'relationship change must be independent widening' USING ERRCODE='0A000';END IF;
   candidate:=candidate||jsonb_build_object('since_rev',old->'since_rev','doc_ord',old->'doc_ord');
   SELECT coalesce(jsonb_agg(v.value),'[]') INTO relations FROM jsonb_array_elements(relations) v WHERE v.value->>'rel_type_id'<>assigned::text;
  END IF;
  relations:=relations||jsonb_build_array(candidate);sequence:=sequence+1;
  changes:=changes||jsonb_build_array(jsonb_build_object('rev',revision,'seq',sequence,'kind','rel','def_id',assigned,'before',CASE WHEN old IS NULL THEN 'null'::jsonb ELSE to_jsonb(jsonb_populate_record(NULL::truss.rel_def,old)) END,'after',to_jsonb(jsonb_populate_record(NULL::truss.rel_def,candidate))));
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
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE declarations jsonb; documents jsonb; origin jsonb;
 expected jsonb:='{}'; rows jsonb; actual jsonb; table_name text; doc jsonb; rec record;
 field record; key record; rel record; ref jsonb; planned_row jsonb; docord int; ownerid int;
 assigned int:=0; type_map jsonb:='[]'; property_map jsonb:='[]'; types jsonb:='[]';
 properties jsonb:='[]'; keys jsonb:='[]'; relationships jsonb:='[]'; lineages jsonb:='[]'; endpoints jsonb:='[]';
 identity_bytes bytea; source_ids int[]; target_ids int[]; components int[]; sourceid int; targetid int;
 prop_row truss.prop_def%ROWTYPE;
 target_key text; keynum int; expected_events bigint;
BEGIN
 IF selected_revision<1 OR type_offset<0 OR property_offset<0 OR relationship_offset<0 THEN
  RAISE EXCEPTION 'valid catalog allocation basis required' USING ERRCODE='22023';END IF;
 assigned:=type_offset;
 declarations:=convert_from(declarations_bytes,'UTF8')::jsonb;
 documents:=convert_from(documents_bytes,'UTF8')::jsonb; origin:=convert_from(origin_bytes,'UTF8')::jsonb;
 IF jsonb_typeof(declarations) IS DISTINCT FROM 'array' OR jsonb_typeof(documents) IS DISTINCT FROM 'array'
  OR jsonb_typeof(origin) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'original record-plan shape required' USING ERRCODE='22023'; END IF;
 -- Clock and allocation rules are the selected native staging rules, not values
 -- copied from the poststate. Genesis is unchanged original prestate.
 rows:=jsonb_build_array(jsonb_build_object('rev',selected_revision,'accepted_at',accepted_clock,'origin',origin));
 IF selected_revision=1 THEN rows:=jsonb_build_array(jsonb_build_object('rev',0,'accepted_at',genesis_clock,'origin','{}'::jsonb))||rows;END IF;
 expected:=jsonb_set(expected,'{schema_rev}',rows);
 rows:='[]'; docord:=0;
 FOR doc IN SELECT value FROM jsonb_array_elements(documents) LOOP
  rows:=rows||jsonb_build_array(jsonb_build_object('rev',selected_revision,'ord',docord,'doc_id',doc->>'documentId',
   'doc_revision',doc->>'revision','umf_version',doc->>'umfVersion','content_sha256',
   encode(sha256(convert_to(doc->>'originalText','UTF8')),'hex'),'document',doc->>'originalText','validation',doc->'validation'));
  docord:=docord+1;
 END LOOP;
 expected:=jsonb_set(expected,'{schema_doc}',rows);
 FOR rec IN SELECT r.value FROM jsonb_array_elements(declarations) d
  CROSS JOIN LATERAL jsonb_array_elements(d.value->'records') r
  ORDER BY (r.value->>'documentId') COLLATE "C",(r.value->>'moduleId') COLLATE "C",(r.value->>'elementId') COLLATE "C" LOOP
  assigned:=assigned+1;
  SELECT ordinality::int-1 INTO STRICT docord FROM jsonb_array_elements(documents) WITH ORDINALITY d(value,ordinality)
   WHERE d.value->>'documentId'=rec.value->>'documentId';
  identity_bytes:=truss.runtime_lineage_bytes('record',rec.value->>'documentId',rec.value->>'moduleId',rec.value->>'elementId');
  planned_row:=jsonb_build_object('document_id',rec.value->>'documentId','type_id',assigned,'module',rec.value->>'moduleId',
   'element',rec.value->>'elementId','kind','record','provisional',false,'since_rev',selected_revision,'doc_ord',docord,
   'lineage_profile','truss-type-lineage/0.1.0','lineage_bytes',chr(92)||'x'||encode(identity_bytes,'hex'),
   'lineage_sha256',chr(92)||'x'||encode(sha256(identity_bytes),'hex'),'definition_source_kind','accepted_document',
   'definition_rev',selected_revision,'definition_doc_ord',docord,'definition_document_id',rec.value->>'documentId');
  types:=types||jsonb_build_array(planned_row);
  type_map:=type_map||jsonb_build_array(jsonb_build_object('source',rec.value,'typeId',assigned,'docOrd',docord));
 END LOOP;
 expected:=jsonb_set(expected,'{type_def}',types); assigned:=property_offset;
 FOR field IN SELECT t.value AS owner,f.value AS source FROM jsonb_array_elements(type_map) t
  CROSS JOIN LATERAL jsonb_array_elements(t.value->'source'->'fields') f
  ORDER BY (t.value->'source'->>'documentId') COLLATE "C",(t.value->'source'->>'moduleId') COLLATE "C",
   (t.value->'source'->>'elementId') COLLATE "C",(f.value->>'fieldModule') COLLATE "C",(f.value->'declaration'->>'id') COLLATE "C" LOOP
  assigned:=assigned+1; ownerid:=(field.owner->>'typeId')::int; docord:=(field.owner->>'docOrd')::int;
  planned_row:=jsonb_build_object('prop_id',assigned,'type_id',ownerid,'element',field.source->'declaration'->>'id',
   'declaration_module',field.source->>'fieldModule','name',field.source->'declaration'->>'name',
   'scalar_type',field.source->'declaration'->>'scalarType','nullability',field.source->'declaration'->>'nullability',
   'cardinality',field.source->'declaration'->>'cardinality','facets',field.source->'declaration'->'facets',
   'item',CASE WHEN field.source->'declaration'->>'cardinality' IN ('array','map') THEN truss.catalog_item_definition((documents->docord)->>'originalText',field.owner->'source'->>'documentId',selected_revision,docord,field.source->'declaration'->'itemType') ELSE field.source->'declaration'->'itemType' END,'home','json','since_rev',selected_revision,'doc_ord',docord,
   'definition_source_kind','accepted_document','definition_rev',selected_revision,'definition_doc_ord',docord,
   'definition_document_id',field.owner->'source'->>'documentId','_originalField',field.source->'declaration');
  properties:=properties||jsonb_build_array(planned_row);
  property_map:=property_map||jsonb_build_array(planned_row);
 END LOOP;
 expected:=jsonb_set(expected,'{prop_def}',properties);
 FOR rec IN SELECT value FROM jsonb_array_elements(type_map) LOOP
  keynum:=0; ownerid:=(rec.value->>'typeId')::int;
  FOR key IN SELECT value FROM jsonb_array_elements(rec.value->'source'->'keys') ORDER BY (value->>'id') COLLATE "C" LOOP
   keynum:=keynum+1; components:=ARRAY[]::int[];
   FOR ref IN SELECT value FROM jsonb_array_elements(key.value->'fields') LOOP
    SELECT (p.value->>'prop_id')::int INTO STRICT assigned FROM jsonb_array_elements(property_map) p
     WHERE (p.value->>'type_id')::int=ownerid AND p.value->>'declaration_module'=ref->>'module' AND p.value->>'element'=ref->>'element';
    components:=array_append(components,assigned);
   END LOOP;
   keys:=keys||jsonb_build_array(jsonb_build_object('type_id',ownerid,'key_id',key.value->>'id','key_num',keynum,
    'prop_ids',to_jsonb(components),'is_primary',coalesce((key.value->>'primary')::boolean,false),'since_rev',selected_revision,
    'definition_source_kind','accepted_document','definition_rev',selected_revision,'definition_doc_ord',(rec.value->>'docOrd')::int,
    'definition_document_id',rec.value->'source'->>'documentId'));
  END LOOP;
 END LOOP;
 expected:=jsonb_set(expected,'{key_def}',keys); assigned:=relationship_offset;
 FOR rel IN SELECT r.value FROM jsonb_array_elements(declarations) d
  CROSS JOIN LATERAL jsonb_array_elements(d.value->'relationships') r
  ORDER BY (r.value->>'documentId') COLLATE "C",(r.value->>'moduleId') COLLATE "C",(r.value->'declaration'->>'id') COLLATE "C" LOOP
  assigned:=assigned+1; source_ids:=ARRAY[]::int[]; target_ids:=ARRAY[]::int[];
  SELECT ordinality::int-1 INTO STRICT docord FROM jsonb_array_elements(documents) WITH ORDINALITY d(value,ordinality)
   WHERE d.value->>'documentId'=rel.value->>'documentId';
  FOR ref IN SELECT value FROM jsonb_array_elements(rel.value->'declaration'->'source') LOOP
   SELECT (t.value->>'typeId')::int INTO STRICT sourceid FROM jsonb_array_elements(type_map) t
    WHERE t.value->'source'->>'documentId'=rel.value->>'documentId' AND t.value->'source'->>'moduleId'=ref->>'module' AND t.value->'source'->>'elementId'=ref->>'element';
   source_ids:=array_append(source_ids,sourceid);
  END LOOP;
  target_key:=NULL;
  FOR ref IN SELECT value FROM jsonb_array_elements(rel.value->'declaration'->'target') LOOP
   SELECT (t.value->>'typeId')::int INTO STRICT targetid FROM jsonb_array_elements(type_map) t
    WHERE t.value->'source'->>'documentId'=rel.value->>'documentId' AND t.value->'source'->>'moduleId'=ref->>'module' AND t.value->'source'->>'elementId'=ref->>'element';
   target_ids:=array_append(target_ids,targetid);
   IF ref ? 'key' THEN target_key:=ref->>'key'; END IF;
  END LOOP;
  planned_row:=jsonb_build_object('document_id',rel.value->>'documentId','rel_type_id',assigned,'module',rel.value->>'moduleId',
   'rel_id',rel.value->'declaration'->>'id','name',rel.value->'declaration'->>'name',
   'source_min',(rel.value->'declaration'->'sourceMultiplicity'->>'min')::int,
   'source_max',nullif(rel.value->'declaration'->'sourceMultiplicity'->>'max','*')::int,
   'target_min',(rel.value->'declaration'->'targetMultiplicity'->>'min')::int,
   'target_max',nullif(rel.value->'declaration'->'targetMultiplicity'->>'max','*')::int,
   'lifecycle',rel.value->'declaration'->>'targetLifecycle','directed',(rel.value->'declaration'->>'directed')::boolean,
   'target_key',target_key,'composition',false,'since_rev',selected_revision,'doc_ord',docord,
   'definition_source_kind','accepted_document','definition_rev',selected_revision,'definition_doc_ord',docord,'definition_document_id',rel.value->>'documentId');
  relationships:=relationships||jsonb_build_array(planned_row);
  identity_bytes:=truss.runtime_lineage_bytes('authored',rel.value->>'documentId',rel.value->>'moduleId',rel.value->'declaration'->>'id');
  lineages:=lineages||jsonb_build_array(jsonb_build_object('rel_type_id',assigned,'lineage_category','authored',
   'identity_profile','truss-relationship-lineage-bytes/0.1.0','original_identity_bytes',chr(92)||'x'||encode(identity_bytes,'hex'),
   'identity_sha256',chr(92)||'x'||encode(sha256(identity_bytes),'hex')));
  FOREACH sourceid IN ARRAY source_ids LOOP FOREACH targetid IN ARRAY target_ids LOOP
   endpoints:=endpoints||jsonb_build_array(jsonb_build_object('rel_type_id',assigned,'source_type',sourceid,'target_type',targetid));
  END LOOP; END LOOP;
 END LOOP;
 expected:=expected||jsonb_build_object('rel_def',relationships,'relationship_lineage',lineages,'rel_endpoint',endpoints);
 RETURN expected;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_expected_records(bytea,bytea,bytea,timestamptz,timestamptz,int,int,int,int) FROM PUBLIC;
