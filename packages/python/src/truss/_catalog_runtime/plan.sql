-- Compact native catalog plan. Original source meaning; no full-operation snapshots.
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
   'item',field.source->'declaration'->'itemType','home','json','since_rev',selected_revision,'doc_ord',docord,
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
