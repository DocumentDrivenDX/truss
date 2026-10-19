-- SPDX-License-Identifier: MIT OR Apache-2.0
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
 prior_type_identity jsonb;prior_property_identity jsonb;prior_relation_identity jsonb;
 prior_type_id jsonb;prior_property_id jsonb;prior_property_name jsonb;prior_key_identity jsonb;
 prior_key_property jsonb;prior_key_max jsonb;prior_lineage_id jsonb;prior_endpoint_id jsonb;prior_revision_id jsonb;
 current_property_id jsonb;source_index jsonb;fresh_key_number jsonb;fresh_document_ids jsonb;fresh_type_identities jsonb;fresh_relation_identities jsonb;
 next_types jsonb[]:=ARRAY[]::jsonb[];next_properties jsonb[]:=ARRAY[]::jsonb[];next_relations jsonb[]:=ARRAY[]::jsonb[];
 next_keys jsonb[]:=ARRAY[]::jsonb[];next_lineages jsonb[]:=ARRAY[]::jsonb[];next_endpoints jsonb[]:=ARRAY[]::jsonb[];next_changes jsonb[]:=ARRAY[]::jsonb[];
 removed_type_ids int[]:=ARRAY[]::int[];removed_property_ids int[]:=ARRAY[]::int[];removed_relation_ids int[]:=ARRAY[]::int[];
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
 SELECT coalesce(jsonb_object_agg(jsonb_build_array(v.value->>'document_id',v.value->>'module',v.value->>'element')::text,v.value),'{}'::jsonb),
        coalesce(jsonb_object_agg(v.value->>'type_id',v.value),'{}'::jsonb)
  INTO prior_type_identity,prior_type_id FROM jsonb_array_elements(types) v;
 WITH prop_rows AS (SELECT value FROM jsonb_array_elements(properties)),names AS (
  SELECT jsonb_build_array(value->>'type_id',value->>'name')::text name_key,jsonb_agg(value->>'prop_id') prop_ids FROM prop_rows GROUP BY 1
 ) SELECT (SELECT coalesce(jsonb_object_agg(jsonb_build_array(value->>'type_id',value->>'declaration_module',value->>'element')::text,value),'{}'::jsonb) FROM prop_rows),
          (SELECT coalesce(jsonb_object_agg(value->>'prop_id',value),'{}'::jsonb) FROM prop_rows),
          coalesce((SELECT jsonb_object_agg(name_key,prop_ids) FROM names),'{}'::jsonb)
  INTO prior_property_identity,prior_property_id,prior_property_name;
 SELECT coalesce(jsonb_object_agg(jsonb_build_array(v.value->>'document_id',v.value->>'module',v.value->>'rel_id')::text,v.value),'{}'::jsonb)
  INTO prior_relation_identity FROM jsonb_array_elements(relations) v;
 SELECT coalesce(jsonb_object_agg(jsonb_build_array(v.value->>'type_id',v.value->>'key_id')::text,v.value),'{}'::jsonb),
        coalesce(jsonb_object_agg(jsonb_build_array(v.value->>'type_id',p.value#>>'{}')::text,'true'::jsonb),'{}'::jsonb),
        coalesce(jsonb_object_agg(v.value->>'type_id',to_jsonb(v.max_num)),'{}'::jsonb)
  INTO prior_key_identity,prior_key_property,prior_key_max
  FROM (SELECT k.value,max((k.value->>'key_num')::int) OVER(PARTITION BY k.value->>'type_id') max_num
         FROM jsonb_array_elements(keys) k) v
  LEFT JOIN LATERAL jsonb_array_elements(v.value->'prop_ids') p ON true;
 SELECT coalesce(jsonb_object_agg(v.value->>'rel_type_id','true'::jsonb),'{}'::jsonb)
  INTO prior_lineage_id FROM jsonb_array_elements(lineages) v;
 SELECT coalesce(jsonb_object_agg(jsonb_build_array(v.value->>'rel_type_id',v.value->>'source_type',v.value->>'target_type')::text,'true'::jsonb),'{}'::jsonb)
  INTO prior_endpoint_id FROM jsonb_array_elements(endpoints) v;
 SELECT coalesce(jsonb_object_agg(v.value->>'rev',v.value),'{}'::jsonb)
  INTO prior_revision_id FROM jsonb_array_elements(coalesce(prior->'schema_rev','[]'::jsonb)) v;
 -- Index immutable source declarations once for the whole revision. Public catalog preparation
 -- has already validated unique document/module/declaration identities.
 WITH documents AS (
  SELECT d.value->>'rev' rev,d.value->>'ord' ord,d.value->>'doc_id' doc_id,(d.value->>'document')::jsonb document
   FROM jsonb_array_elements(coalesce(prior->'schema_doc','[]'::jsonb)) d
  UNION ALL
  SELECT d.value->>'rev',d.value->>'ord',d.value->>'doc_id',(d.value->>'document')::jsonb
   FROM jsonb_array_elements(coalesce(fresh->'schema_doc','[]'::jsonb)) d
 ),source_rows AS (
  SELECT d.rev,d.ord,d.doc_id,m.value->>'id' module,'element' kind,e.value->>'id' authored_id,e.value source
   FROM documents d CROSS JOIN LATERAL jsonb_array_elements(d.document->'modules') m
   CROSS JOIN LATERAL jsonb_array_elements(coalesce(m.value->'elements','[]'::jsonb)) e
  UNION ALL
  SELECT d.rev,d.ord,d.doc_id,m.value->>'id','relationship',e.value->>'id',e.value
   FROM documents d CROSS JOIN LATERAL jsonb_array_elements(d.document->'modules') m
   CROSS JOIN LATERAL jsonb_array_elements(coalesce(m.value->'relationships','[]'::jsonb)) e
 ) SELECT coalesce(jsonb_object_agg(jsonb_build_array(rev,ord,doc_id,module,kind,authored_id)::text,source),'{}'::jsonb)
   INTO source_index FROM source_rows;
 -- Resolve every fresh identity and allocate new IDs in input order before validation. Loops below
 -- still perform each semantic decision and append history in the original type/property/relation order.
 WITH fresh_rows AS (
  SELECT f.value,f.ordinality,
   jsonb_build_array(f.value->>'document_id',f.value->>'module',f.value->>'element')::text identity_key
   FROM jsonb_array_elements(fresh->'type_def') WITH ORDINALITY f
 ),matched AS (
  SELECT f.*,p.value->>'type_id' existing_id FROM fresh_rows f LEFT JOIN jsonb_each(prior_type_identity) p ON p.key=f.identity_key
 ),assigned AS (
  SELECT *,CASE WHEN existing_id IS NULL THEN type_next+sum((existing_id IS NULL)::int) OVER(ORDER BY ordinality)
   ELSE existing_id::int END assigned_id FROM matched
 ) SELECT coalesce(jsonb_object_agg(value->>'type_id',to_jsonb(assigned_id)),'{}'::jsonb)
   INTO type_map FROM assigned;
 WITH fresh_rows AS (
  SELECT f.value,f.ordinality,(type_map->>(f.value->>'type_id'))::int assigned_type,
   jsonb_build_array(type_map->>(f.value->>'type_id'),f.value->>'declaration_module',f.value->>'element')::text identity_key
   FROM jsonb_array_elements(fresh->'prop_def') WITH ORDINALITY f
 ),matched AS (
  SELECT f.*,p.value->>'prop_id' existing_id,p.value existing_row FROM fresh_rows f LEFT JOIN jsonb_each(prior_property_identity) p ON p.key=f.identity_key
 ),assigned AS (
  SELECT *,CASE WHEN existing_id IS NULL THEN property_next+sum((existing_id IS NULL)::int) OVER(ORDER BY ordinality)
   ELSE existing_id::int END assigned_id FROM matched
 ) SELECT coalesce(jsonb_object_agg(value->>'prop_id',to_jsonb(assigned_id)),'{}'::jsonb),
          coalesce(jsonb_object_agg(jsonb_build_array(assigned_type::text,assigned_id::text)::text,
           value||jsonb_build_object('type_id',assigned_type,'prop_id',assigned_id,
   'since_rev',coalesce(existing_row->'since_rev',value->'since_rev'),'doc_ord',coalesce(existing_row->'doc_ord',value->'doc_ord'))),'{}'::jsonb)
   INTO property_map,current_property_id FROM assigned;
 WITH fresh_rows AS (
  SELECT f.value,f.ordinality,jsonb_build_array(f.value->>'document_id',f.value->>'module',f.value->>'rel_id')::text identity_key
   FROM jsonb_array_elements(fresh->'rel_def') WITH ORDINALITY f
 ),matched AS (
  SELECT f.*,p.value->>'rel_type_id' existing_id FROM fresh_rows f LEFT JOIN jsonb_each(prior_relation_identity) p ON p.key=f.identity_key
 ),assigned AS (
  SELECT *,CASE WHEN existing_id IS NULL THEN relationship_next+sum((existing_id IS NULL)::int) OVER(ORDER BY ordinality)
   ELSE existing_id::int END assigned_id FROM matched
 ) SELECT coalesce(jsonb_object_agg(value->>'rel_type_id',to_jsonb(assigned_id)),'{}'::jsonb)
   INTO relationship_map FROM assigned;
 WITH fresh_rows AS (
  SELECT f.value,f.ordinality,(type_map->>(f.value->>'type_id'))::int assigned_type,
   jsonb_build_array(type_map->>(f.value->>'type_id'),f.value->>'key_id')::text identity_key
   FROM jsonb_array_elements(fresh->'key_def') WITH ORDINALITY f
 ),matched AS (
  SELECT f.*,p.value->>'key_num' existing_num,coalesce((prior_key_max->>f.assigned_type::text)::int,0) max_num
   FROM fresh_rows f LEFT JOIN jsonb_each(prior_key_identity) p ON p.key=f.identity_key
 ),assigned AS (
  SELECT *,CASE WHEN existing_num IS NOT NULL THEN existing_num::int
   WHEN prior_type_id ? assigned_type::text THEN max_num+sum((existing_num IS NULL)::int) OVER(PARTITION BY assigned_type ORDER BY ordinality)
   ELSE (value->>'key_num')::int END assigned_num FROM matched
 ) SELECT coalesce(jsonb_object_agg(identity_key,to_jsonb(assigned_num)),'{}'::jsonb)
   INTO fresh_key_number FROM assigned;
 SELECT coalesce(jsonb_object_agg(d.value->>'doc_id','true'::jsonb),'{}'::jsonb) INTO fresh_document_ids
  FROM jsonb_array_elements(coalesce(fresh->'schema_doc','[]'::jsonb)) d;
 SELECT coalesce(jsonb_object_agg(identity_key,'true'::jsonb),'{}'::jsonb) INTO fresh_type_identities
  FROM (SELECT jsonb_build_array(v.value->>'document_id',v.value->>'module',v.value->>'element')::text identity_key
    FROM jsonb_array_elements(fresh->'type_def') v) q;
 SELECT coalesce(jsonb_object_agg(identity_key,'true'::jsonb),'{}'::jsonb) INTO fresh_relation_identities
  FROM (SELECT jsonb_build_array(v.value->>'document_id',v.value->>'module',v.value->>'rel_id')::text identity_key
    FROM jsonb_array_elements(fresh->'rel_def') v) q;
 SELECT max((v.value->>'rev')::int) INTO STRICT revision FROM jsonb_array_elements(fresh->'schema_rev') v;
 -- A submitted document cannot implicitly retire an omitted declaration.
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(types) p WHERE fresh_document_ids ? (p.value->>'document_id')
  AND NOT fresh_type_identities ? jsonb_build_array(p.value->>'document_id',p.value->>'module',p.value->>'element')::text) THEN
  RAISE EXCEPTION 'record retirement requires explicit support' USING ERRCODE='0A000';END IF;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'type_def') LOOP
  assigned:=(type_map->>(row->>'type_id'))::int;
  old:=prior_type_identity->jsonb_build_array(row->>'document_id',row->>'module',row->>'element')::text;
  candidate:=row||jsonb_build_object('type_id',assigned);
  IF old IS NOT NULL THEN
   old_source:=source_index->jsonb_build_array(old->>'definition_rev',old->>'definition_doc_ord',old->>'definition_document_id',old->>'module','element',old->>'element')::text;
   new_source:=source_index->jsonb_build_array(row->>'definition_rev',row->>'definition_doc_ord',row->>'definition_document_id',row->>'module','element',row->>'element')::text;
   IF old_source IS NULL OR new_source IS NULL THEN RAISE NO_DATA_FOUND;END IF;
   IF old_source=new_source THEN CONTINUE;END IF;
   IF old_source-ARRAY['members','name','keys'] IS DISTINCT FROM new_source-ARRAY['members','name','keys']
    OR EXISTS(SELECT value FROM jsonb_array_elements(coalesce(old_source->'keys','[]')) EXCEPT
              SELECT value FROM jsonb_array_elements(coalesce(new_source->'keys','[]')))
    OR EXISTS(SELECT value FROM jsonb_array_elements(old_source->'members') EXCEPT ALL
              SELECT value FROM jsonb_array_elements(new_source->'members')) THEN
    RAISE EXCEPTION 'existing record keys, meaning and retained members require explicit evolution support' USING ERRCODE='0A000';END IF;
   candidate:=candidate||jsonb_build_object('since_rev',old->'since_rev','doc_ord',old->'doc_ord');
   removed_type_ids[cardinality(removed_type_ids)+1]:=assigned;
  END IF;
  next_types[cardinality(next_types)+1]:=candidate;sequence:=sequence+1;
  IF old IS NOT NULL OR NOT compact_insertions THEN
  next_changes[cardinality(next_changes)+1]:=jsonb_build_object('rev',revision,'seq',sequence,'kind','type','def_id',assigned,'before',CASE WHEN old IS NULL THEN 'null'::jsonb ELSE to_jsonb(jsonb_populate_record(NULL::truss.type_def,old)) END,'after',to_jsonb(jsonb_populate_record(NULL::truss.type_def,candidate)));
  END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(value ORDER BY family,ordinal),'[]'::jsonb) INTO types FROM (
  SELECT v.value,0 family,v.ordinality ordinal FROM jsonb_array_elements(coalesce(prior->'type_def','[]'::jsonb)) WITH ORDINALITY v
   LEFT JOIN (SELECT DISTINCT id FROM unnest(removed_type_ids) AS removed(id)) removed ON removed.id=(v.value->>'type_id')::int
   WHERE removed.id IS NULL
  UNION ALL SELECT n.value,1,n.ordinality FROM unnest(next_types) WITH ORDINALITY n(value,ordinality)) merged;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'prop_def') LOOP
  assigned:=(type_map->> (row->>'type_id'))::int;
  old:=prior_property_identity->jsonb_build_array(assigned::text,row->>'declaration_module',row->>'element')::text;
  IF old IS NULL THEN
   IF prior_type_id ? assigned::text AND row->>'nullability' NOT IN ('required','absent-allowed') THEN
    RAISE EXCEPTION 'supported new field nullability required' USING ERRCODE='0A000';END IF;
  END IF;
  candidate:=row||jsonb_build_object('type_id',assigned,'prop_id',(property_map->> (row->>'prop_id'))::int);
  IF coalesce(prior_property_name ? jsonb_build_array(assigned::text,candidate->>'name')::text,false)
   AND EXISTS(SELECT 1 FROM jsonb_array_elements(prior_property_name->jsonb_build_array(assigned::text,candidate->>'name')::text) old_name
    WHERE old_name.value#>>'{}' IS DISTINCT FROM candidate->>'prop_id') THEN
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
    OR prior_key_property ? jsonb_build_array(assigned::text,old->>'prop_id')::text THEN
    RAISE EXCEPTION 'existing field change requires explicit evolution support' USING ERRCODE='0A000';END IF;
   END IF;
   candidate:=candidate||jsonb_build_object('since_rev',old->'since_rev','doc_ord',old->'doc_ord');
   removed_property_ids[cardinality(removed_property_ids)+1]:=(old->>'prop_id')::int;
  END IF;
  -- Public source validation already rejects duplicate property names within a type. The
  -- immutable prior-name map above preserves the planner's cross-revision collision refusal.
  next_properties[cardinality(next_properties)+1]:=candidate;sequence:=sequence+1;
  IF old IS NOT NULL OR NOT compact_insertions THEN
  next_changes[cardinality(next_changes)+1]:=jsonb_build_object('rev',revision,'seq',sequence,'kind','prop','def_id',(candidate->>'prop_id')::int,'before',CASE WHEN old IS NULL THEN 'null'::jsonb ELSE to_jsonb(jsonb_populate_record(NULL::truss.prop_def,old)) END,'after',to_jsonb(jsonb_populate_record(NULL::truss.prop_def,candidate)));
  END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(value ORDER BY family,ordinal),'[]'::jsonb) INTO properties FROM (
  SELECT v.value,0 family,v.ordinality ordinal FROM jsonb_array_elements(coalesce(prior->'prop_def','[]'::jsonb)) WITH ORDINALITY v
   LEFT JOIN (SELECT DISTINCT id FROM unnest(removed_property_ids) AS removed(id)) removed ON removed.id=(v.value->>'prop_id')::int
   WHERE removed.id IS NULL
  UNION ALL SELECT n.value,1,n.ordinality FROM unnest(next_properties) WITH ORDINALITY n(value,ordinality)) merged;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'key_def') LOOP
  assigned:=(type_map->> (row->>'type_id'))::int;remapped:='[]';
  SELECT coalesce(jsonb_agg(to_jsonb((property_map->>(p.value#>>'{}'))::int) ORDER BY p.ordinality),'[]'::jsonb)
   INTO remapped FROM jsonb_array_elements(row->'prop_ids') WITH ORDINALITY p;
  old:=prior_key_identity->jsonb_build_array(assigned::text,row->>'key_id')::text;
  IF old IS NOT NULL THEN
   IF old->'prop_ids' IS DISTINCT FROM remapped OR old->'is_primary' IS DISTINCT FROM row->'is_primary' THEN RAISE EXCEPTION 'existing key change requires backfill support' USING ERRCODE='0A000';END IF;
  ELSE
   IF prior_type_id ? assigned::text THEN
    IF (row->>'is_primary')::boolean IS NOT FALSE OR EXISTS(SELECT 1 FROM jsonb_array_elements(remapped) component
     CROSS JOIN LATERAL (SELECT current_property_id->jsonb_build_array(assigned::text,component.value#>>'{}')::text current_row,
       prior_property_id->>(component.value#>>'{}') prior_row) p
     WHERE p.current_row IS NULL
      OR p.current_row->>'nullability'<>'required' OR p.current_row->>'cardinality'<>'one'
      OR p.current_row->>'scalar_type' NOT IN ('string','integer','decimal','boolean','binary')
      OR NOT ((p.prior_row IS NOT NULL AND p.prior_row::jsonb->>'type_id'=assigned::text
         AND p.prior_row::jsonb->>'nullability'='required' AND p.prior_row::jsonb->>'cardinality'='one'
         AND p.prior_row::jsonb->>'scalar_type' IN ('string','integer','decimal','boolean','binary'))
       OR (p.current_row->>'since_rev')::int=revision AND p.prior_row IS NULL)) THEN
     RAISE EXCEPTION 'new alternate key requires existing or newly rebound required scalar components' USING ERRCODE='0A000';END IF;
   END IF;
   key_next:=(fresh_key_number->>jsonb_build_array(assigned::text,row->>'key_id')::text)::int;
   IF key_next>32767 THEN RAISE EXCEPTION 'owner-local key range exhausted' USING ERRCODE='54000';END IF;
   next_keys[cardinality(next_keys)+1]:=row||jsonb_build_object('type_id',assigned,'prop_ids',remapped,'key_num',key_next);
  END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(value ORDER BY family,ordinal),'[]'::jsonb) INTO keys FROM (
  SELECT v.value,0 family,v.ordinality ordinal FROM jsonb_array_elements(coalesce(prior->'key_def','[]'::jsonb)) WITH ORDINALITY v
  UNION ALL SELECT n.value,1,n.ordinality FROM unnest(next_keys) WITH ORDINALITY n(value,ordinality)) merged;
 -- Relationship IDs and lineage remain stable; independent multiplicity evolution retains endpoints.
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'rel_def') LOOP
  assigned:=(relationship_map->>(row->>'rel_type_id'))::int;
  old:=prior_relation_identity->jsonb_build_array(row->>'document_id',row->>'module',row->>'rel_id')::text;
  candidate:=row||jsonb_build_object('rel_type_id',assigned);
  IF old IS NOT NULL THEN
   old_source:=source_index->jsonb_build_array(old->>'definition_rev',old->>'definition_doc_ord',old->>'definition_document_id',old->>'module','relationship',old->>'rel_id')::text;
   new_source:=source_index->jsonb_build_array(row->>'definition_rev',row->>'definition_doc_ord',row->>'definition_document_id',row->>'module','relationship',row->>'rel_id')::text;
   IF old_source IS NULL OR new_source IS NULL THEN RAISE NO_DATA_FOUND;END IF;
   IF old_source=new_source THEN CONTINUE;END IF;
   IF (old_source-ARRAY['name','inverse','source','target','sourceMultiplicity','targetMultiplicity']) IS DISTINCT FROM (new_source-ARRAY['name','inverse','source','target','sourceMultiplicity','targetMultiplicity'])
    OR (old_source ? 'inverse') IS DISTINCT FROM (new_source ? 'inverse')
    OR (old_source->'name' IS DISTINCT FROM new_source->'name' AND (jsonb_typeof(old_source->'name') IS DISTINCT FROM 'string' OR jsonb_typeof(new_source->'name') IS DISTINCT FROM 'string'))
    OR (old_source->'inverse' IS DISTINCT FROM new_source->'inverse' AND (jsonb_typeof(old_source->'inverse') IS DISTINCT FROM 'string' OR jsonb_typeof(new_source->'inverse') IS DISTINCT FROM 'string'))
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(old_source->'source') x
              WHERE NOT ((new_source->'source') @> jsonb_build_array(x.value)))
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(old_source->'target') x
              WHERE NOT ((new_source->'target') @> jsonb_build_array(x.value))) THEN
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
   removed_relation_ids[cardinality(removed_relation_ids)+1]:=assigned;
  END IF;
  next_relations[cardinality(next_relations)+1]:=candidate;sequence:=sequence+1;
  IF old IS NOT NULL OR NOT compact_insertions THEN
  next_changes[cardinality(next_changes)+1]:=jsonb_build_object('rev',revision,'seq',sequence,'kind','rel','def_id',assigned,'before',CASE WHEN old IS NULL THEN 'null'::jsonb ELSE to_jsonb(jsonb_populate_record(NULL::truss.rel_def,old)) END,'after',to_jsonb(jsonb_populate_record(NULL::truss.rel_def,candidate)));
  END IF;
 END LOOP;
 SELECT coalesce(jsonb_agg(value ORDER BY family,ordinal),'[]'::jsonb) INTO relations FROM (
  SELECT v.value,0 family,v.ordinality ordinal FROM jsonb_array_elements(coalesce(prior->'rel_def','[]'::jsonb)) WITH ORDINALITY v
   LEFT JOIN (SELECT DISTINCT id FROM unnest(removed_relation_ids) AS removed(id)) removed ON removed.id=(v.value->>'rel_type_id')::int
   WHERE removed.id IS NULL
  UNION ALL SELECT n.value,1,n.ordinality FROM unnest(next_relations) WITH ORDINALITY n(value,ordinality)) merged;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'relationship_lineage') LOOP
  assigned:=(relationship_map->> (row->>'rel_type_id'))::int;
  IF NOT prior_lineage_id ? assigned::text THEN next_lineages[cardinality(next_lineages)+1]:=row||jsonb_build_object('rel_type_id',assigned);END IF;
 END LOOP;
 FOR row IN SELECT value FROM jsonb_array_elements(fresh->'rel_endpoint') LOOP
  candidate:=jsonb_build_object('rel_type_id',(relationship_map->> (row->>'rel_type_id'))::int,'source_type',(type_map->> (row->>'source_type'))::int,'target_type',(type_map->> (row->>'target_type'))::int);
  IF NOT prior_endpoint_id ? jsonb_build_array(candidate->>'rel_type_id',candidate->>'source_type',candidate->>'target_type')::text THEN
   next_endpoints[cardinality(next_endpoints)+1]:=candidate;END IF;
 END LOOP;
 WITH additions AS (
  SELECT n.value,n.ordinality,row_number() OVER(PARTITION BY n.value->>'rel_type_id' ORDER BY n.ordinality) duplicate_rank
   FROM unnest(next_lineages) WITH ORDINALITY n(value,ordinality)
 ) SELECT coalesce(jsonb_agg(value ORDER BY family,ordinal),'[]'::jsonb) INTO lineages FROM (
  SELECT v.value,0 family,v.ordinality ordinal FROM jsonb_array_elements(coalesce(prior->'relationship_lineage','[]'::jsonb)) WITH ORDINALITY v
  UNION ALL SELECT a.value,1,a.ordinality FROM additions a WHERE a.duplicate_rank=1) merged;
 WITH additions AS (
  SELECT n.value,n.ordinality,row_number() OVER(PARTITION BY n.value->>'rel_type_id',n.value->>'source_type',n.value->>'target_type' ORDER BY n.ordinality) duplicate_rank
   FROM unnest(next_endpoints) WITH ORDINALITY n(value,ordinality)
 ) SELECT coalesce(jsonb_agg(value ORDER BY family,ordinal),'[]'::jsonb) INTO endpoints FROM (
  SELECT v.value,0 family,v.ordinality ordinal FROM jsonb_array_elements(coalesce(prior->'rel_endpoint','[]'::jsonb)) WITH ORDINALITY v
  UNION ALL SELECT a.value,1,a.ordinality FROM additions a WHERE a.duplicate_rank=1) merged;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(relations) p WHERE fresh_document_ids ? (p.value->>'document_id')
  AND NOT fresh_relation_identities ? jsonb_build_array(p.value->>'document_id',p.value->>'module',p.value->>'rel_id')::text) THEN
  RAISE EXCEPTION 'relationship retirement requires explicit support' USING ERRCODE='0A000';END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(fresh->'schema_rev') f JOIN jsonb_each(prior_revision_id) p ON p.key=f.value->>'rev' WHERE p.value IS DISTINCT FROM f.value) THEN
  RAISE EXCEPTION 'original revision history required' USING ERRCODE='55000';END IF;
 SELECT coalesce(jsonb_agg(f.value ORDER BY f.ordinality),'[]'::jsonb) INTO remapped FROM jsonb_array_elements(fresh->'schema_rev') WITH ORDINALITY f
  WHERE NOT prior_revision_id ? (f.value->>'rev');
 SELECT coalesce(jsonb_agg(n.value ORDER BY n.ordinality),'[]'::jsonb) INTO changes FROM unnest(next_changes) WITH ORDINALITY n(value,ordinality);
 changes:=coalesce(prior->'schema_change','[]'::jsonb)||changes;
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
  SELECT d.value,d.ordinality::int-1 ord,truss.catalog_item_source_index(d.value->>'originalText') source_index
  FROM jsonb_array_elements(validated_documents) WITH ORDINALITY d),
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
    'item',CASE WHEN f.value->'declaration'->>'cardinality' IN ('array','map') THEN truss.catalog_item_definition_indexed(d.source_index,f.document_id,selected_revision,f.ord,f.value->'declaration'->'itemType') ELSE f.value->'declaration'->'itemType' END,
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
