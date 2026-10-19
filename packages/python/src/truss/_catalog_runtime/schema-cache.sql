-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Compile immutable schema metadata once at revision initialization.
CREATE TABLE truss.runtime_type_schema (
 rev int NOT NULL REFERENCES truss.schema_rev(rev),type_id int NOT NULL,
 metadata jsonb NOT NULL,value_readers jsonb NOT NULL,valid_properties boolean NOT NULL,PRIMARY KEY(rev,type_id));
REVOKE ALL ON TABLE truss.runtime_type_schema FROM PUBLIC;
CREATE TRIGGER runtime_type_schema_immutable BEFORE UPDATE OR DELETE ON truss.runtime_type_schema
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_type_schema_no_truncate BEFORE TRUNCATE ON truss.runtime_type_schema
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
CREATE TABLE truss.runtime_document_schema(rev int NOT NULL REFERENCES truss.schema_rev(rev),doc_id text NOT NULL,metadata jsonb NOT NULL,PRIMARY KEY(rev,doc_id));
REVOKE ALL ON TABLE truss.runtime_document_schema FROM PUBLIC;
CREATE TRIGGER runtime_document_schema_immutable BEFORE UPDATE OR DELETE ON truss.runtime_document_schema FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_document_schema_no_truncate BEFORE TRUNCATE ON truss.runtime_document_schema FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
CREATE FUNCTION truss.runtime_owned_index_type_schema() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE basis jsonb;current_head boolean;compiled_records jsonb[]:='{}';missing_pins boolean;document_row record;records jsonb;relations jsonb;readers jsonb;closed boolean;items_valid boolean;
BEGIN
 -- The accepted head already contains the installed, validated native rows.
 -- Historical initialization retains its original reconstruction; the current
 -- revision does not parse and rebuild the complete catalog a second time.
 current_head:=NEW.rev=(SELECT rev FROM truss.schema_head WHERE id=1)
  AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>NEW.rev);
 IF NOT current_head THEN basis:=truss.catalog_all_expected_records(NEW.rev);END IF;
 -- Compile the entire revision as one typed relation. Every source/native
 -- check below is the same check as the former per-type statement loop.
 WITH types AS MATERIALIZED (
  SELECT t.* FROM truss.type_def t WHERE current_head AND t.kind='record' AND NOT t.provisional AND (t.retired_rev IS NULL OR t.retired_rev>NEW.rev)
  UNION ALL
  SELECT t.* FROM jsonb_populate_recordset(NULL::truss.type_def,basis->'type_def') t
  WHERE NOT current_head AND t.kind='record' AND NOT t.provisional AND (t.retired_rev IS NULL OR t.retired_rev>NEW.rev)),
 properties AS MATERIALIZED (
  SELECT p.* FROM truss.prop_def p WHERE current_head
  UNION ALL SELECT p.* FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE NOT current_head),
 keys AS MATERIALIZED (
  SELECT k.* FROM truss.key_def k WHERE current_head
  UNION ALL SELECT k.* FROM jsonb_populate_recordset(NULL::truss.key_def,basis->'key_def') k WHERE NOT current_head),
 documents AS MATERIALIZED (
  SELECT DISTINCT ON(doc_id) doc_id,doc_revision,umf_version,document::jsonb source
  FROM truss.schema_doc WHERE rev<=NEW.rev ORDER BY doc_id,rev DESC),
 elements AS MATERIALIZED (
  SELECT d.doc_id,d.umf_version,m.value->>'id' module_id,e.value->>'id' element_id,e.value element
  FROM documents d CROSS JOIN LATERAL jsonb_array_elements(d.source->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e),
 authored_keys AS MATERIALIZED (
  SELECT k.type_id,k.key_num,k.prop_ids,t.document_id,r.umf_version,r.element record_source,q.value key_source
  FROM keys k JOIN types t USING(type_id)
  JOIN elements r ON r.doc_id=t.document_id AND r.module_id=t.module AND r.element_id=t.element
  CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(r.element->'keys')='array' THEN r.element->'keys' ELSE '[]'::jsonb END) q
  WHERE k.since_rev<=NEW.rev AND (k.retired_rev IS NULL OR k.retired_rev>NEW.rev) AND q.value->>'id'=k.key_id),
 components AS MATERIALIZED (
  SELECT k.type_id,k.key_num,k.umf_version,k.prop_ids,i.ordinal,f.element field_source,p.facets,
   k.key_source-ARRAY['id','name','fields','primary']='{}'::jsonb
    AND CASE WHEN jsonb_typeof(k.key_source->'fields')='array' THEN jsonb_array_length(k.key_source->'fields') END=cardinality(k.prop_ids)
    AND k.key_source->'fields'->(i.ordinal::int-1)=jsonb_build_object('module',p.declaration_module,'element',p.element)
    AND k.record_source->'members' @> jsonb_build_array(jsonb_build_object('module',p.declaration_module,'element',p.element))
    AND f.element IS NOT NULL AND f.element->>'scalarType' IS NOT DISTINCT FROM p.scalar_type
    AND coalesce(f.element->'facets','{}')=coalesce(p.facets,'{}') qualified
  FROM authored_keys k CROSS JOIN LATERAL unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ordinal)
  JOIN properties p ON p.type_id=k.type_id AND p.prop_id=i.prop_id
  LEFT JOIN elements f ON f.doc_id=k.document_id AND f.module_id=p.declaration_module AND f.element_id=p.element),
 codecs AS MATERIALIZED (
  SELECT type_id,key_num,jsonb_build_object('profile','truss-native-key-codec-metadata/0.1',
   'typeId',type_id::text,'keyNumber',key_num::text,'fields',jsonb_agg(field_source ORDER BY ordinal),
   'facets',jsonb_agg(coalesce(facets,'{}') ORDER BY ordinal),'umfVersion',umf_version) metadata
  FROM components GROUP BY type_id,key_num,umf_version,prop_ids
  -- Unsupported accepted forms keep their original lazy key-operation refusal.
  HAVING bool_and(qualified IS TRUE) AND count(*)=cardinality(prop_ids)),
 key_codecs AS MATERIALIZED (
  SELECT type_id,jsonb_object_agg(key_num::text,metadata) metadata FROM codecs GROUP BY type_id),
 property_dependencies AS MATERIALIZED (
  SELECT p.type_id,p.prop_id,p.definition_document_id document_id,p.declaration_module module_id
  FROM properties p WHERE p.retired_rev IS NULL OR p.retired_rev>NEW.rev
  UNION
  SELECT p.type_id,p.prop_id,n.value->>'documentId',n.value->'reference'->>'module'
  FROM properties p CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(p.item)||coalesce(p.item->'descendants','[]'::jsonb)) n
  WHERE (p.retired_rev IS NULL OR p.retired_rev>NEW.rev) AND p.cardinality IN ('array','map')),
 property_readers AS MATERIALIZED (
  SELECT prop_id,jsonb_agg(jsonb_build_object('documentId',document_id,'moduleId',module_id) ORDER BY document_id,module_id) readers
  FROM property_dependencies GROUP BY prop_id),
 type_readers AS MATERIALIZED (
  SELECT type_id,jsonb_agg(jsonb_build_object('documentId',document_id,'moduleId',module_id) ORDER BY document_id,module_id) readers
  FROM (SELECT type_id,document_id,module module_id FROM types
   UNION SELECT type_id,document_id,module_id FROM property_dependencies) dependencies GROUP BY type_id),
 property_metadata AS MATERIALIZED (
  SELECT p.type_id,
   coalesce(jsonb_agg(p.prop_id::text ORDER BY p.prop_id) FILTER(WHERE p.since_rev<=NEW.rev),'[]'::jsonb) property_order,
   coalesce(jsonb_object_agg(p.prop_id::text,d.definition_pin) FILTER(WHERE p.since_rev<=NEW.rev),'{}'::jsonb) property_pins,
   coalesce(bool_or(d.definition_pin IS NULL OR p.definition_source_kind<>'accepted_document') FILTER(WHERE p.since_rev<=NEW.rev),false) missing_pins,
   coalesce(bool_and(truss.valid_property_definition(p::truss.prop_def)),true) valid_properties,
   coalesce(jsonb_object_agg(p.prop_id::text,jsonb_build_object(
    'itemsValid',CASE WHEN p.cardinality IN ('array','map') THEN truss.valid_item_chain(p.item) IS TRUE ELSE true END,
    'readers',r.readers)) FILTER(WHERE p.since_rev<=NEW.rev),'{}'::jsonb) property_access,
   jsonb_agg(jsonb_build_object('identity',jsonb_build_object('documentId',t.document_id,
    'revision',doc.doc_revision,'module',p.declaration_module,'element',p.element),'propertyId',p.prop_id::text) ORDER BY p.prop_id) query_fields
  FROM properties p JOIN types t USING(type_id) JOIN documents doc ON doc.doc_id=t.document_id
  LEFT JOIN property_readers r USING(prop_id)
  LEFT JOIN truss.runtime_definition_source d ON d.rev=p.definition_rev AND d.ord=p.definition_doc_ord
   AND d.doc_id=p.definition_document_id AND d.module_id=p.declaration_module AND d.element_id=p.element AND d.kind='element' AND d.key_id=''
  WHERE p.retired_rev IS NULL OR p.retired_rev>NEW.rev
  GROUP BY p.type_id),
 query_keys AS MATERIALIZED (
  SELECT type_id,jsonb_agg(jsonb_build_object('keyId',k.key_id,'propertyIds',
   (SELECT jsonb_agg(v.prop_id::text ORDER BY v.ordinal) FROM unnest(k.prop_ids) WITH ORDINALITY v(prop_id,ordinal))) ORDER BY k.key_num) keys
  FROM keys k WHERE k.retired_rev IS NULL OR k.retired_rev>NEW.rev GROUP BY type_id),
 compiled AS MATERIALIZED (
  SELECT t.type_id,
   jsonb_build_object('typeId',t.type_id::text,'revision',NEW.rev::text,'typePin',d.definition_pin,
    'propertyOrder',coalesce(p.property_order,'[]'::jsonb),'propertyPins',coalesce(p.property_pins,'{}'::jsonb),
    'propertyAccess',coalesce(p.property_access,'{}'::jsonb),'keyCodecs',coalesce(k.metadata,'{}'::jsonb)) metadata,
   r.readers value_readers,coalesce(p.valid_properties,true) valid_properties,
   coalesce(p.missing_pins,false) OR d.definition_pin IS NULL OR doc.doc_revision IS NULL missing_pins,
   jsonb_build_object('identity',jsonb_build_object('documentId',t.document_id,'revision',doc.doc_revision,'module',t.module,'element',t.element),
    'typeId',t.type_id::text,'keys',coalesce(q.keys,'[]'::jsonb),'fields',coalesce(p.query_fields,'[]'::jsonb)) query_record
  FROM types t LEFT JOIN property_metadata p USING(type_id) LEFT JOIN key_codecs k USING(type_id)
  LEFT JOIN type_readers r USING(type_id) LEFT JOIN query_keys q USING(type_id)
  LEFT JOIN documents doc ON doc.doc_id=t.document_id
  LEFT JOIN truss.runtime_definition_source d ON d.rev=t.definition_rev AND d.ord=t.definition_doc_ord AND d.doc_id=t.definition_document_id
   AND d.module_id=t.module AND d.element_id=t.element AND d.kind='element' AND d.key_id=''),
 inserted AS (
  INSERT INTO truss.runtime_type_schema(rev,type_id,metadata,value_readers,valid_properties)
  SELECT NEW.rev,type_id,metadata,value_readers,valid_properties FROM compiled RETURNING type_id)
 SELECT coalesce(array_agg(c.query_record ORDER BY c.type_id),'{}'::jsonb[]),coalesce(bool_or(c.missing_pins),false)
 INTO compiled_records,missing_pins FROM compiled c LEFT JOIN inserted i USING(type_id);
 IF missing_pins THEN RAISE EXCEPTION 'complete original compiled schema pins required' USING ERRCODE='55000';END IF;
 IF NEW.rev=(SELECT rev FROM truss.schema_head WHERE id=1) THEN
 FOR document_row IN SELECT DISTINCT ON(doc_id) doc_id,doc_revision,content_sha256,document FROM truss.schema_doc WHERE rev<=NEW.rev ORDER BY doc_id,rev DESC LOOP
  SELECT coalesce(jsonb_agg(record ORDER BY (record->>'typeId')::int),'[]'::jsonb) INTO records
   FROM unnest(compiled_records) record WHERE record->'identity'->>'documentId'=document_row.doc_id;
  SELECT coalesce(jsonb_agg(jsonb_build_object('identity',jsonb_build_object('documentId',r.document_id,'revision',document_row.doc_revision,
   'module',r.module,'relationship',r.rel_id),'relationshipTypeId',r.rel_type_id::text,'sourceTypeId',e.source_type::text,'targetTypeId',e.target_type::text)
   ORDER BY r.rel_type_id),'[]'::jsonb),coalesce(bool_and(s.document_id=document_row.doc_id AND t.document_id=document_row.doc_id AND s.kind='record' AND t.kind='record' AND NOT s.provisional AND NOT t.provisional AND s.retired_rev IS NULL AND t.retired_rev IS NULL),true)
   INTO relations,closed FROM truss.rel_def r JOIN truss.rel_endpoint e USING(rel_type_id)
   JOIN truss.type_def s ON s.type_id=e.source_type JOIN truss.type_def t ON t.type_id=e.target_type
   WHERE r.document_id=document_row.doc_id AND r.retired_rev IS NULL AND r.lifecycle IN ('independent','owned') AND r.directed
    AND NOT r.composition AND r.assoc_type_id IS NULL AND (SELECT count(*) FROM truss.rel_endpoint ep WHERE ep.rel_type_id=r.rel_type_id)=1;
  SELECT coalesce(jsonb_agg(jsonb_build_object('documentId',document_id,'moduleId',module_id) ORDER BY document_id,module_id),'[]'::jsonb) INTO readers FROM (
   SELECT document_row.doc_id document_id,m.value->>'id' module_id FROM jsonb_array_elements(document_row.document::jsonb->'modules') m
   UNION SELECT t.document_id,t.module FROM truss.type_def t WHERE t.document_id=document_row.doc_id AND t.kind='record' AND t.retired_rev IS NULL
   UNION SELECT p.definition_document_id,p.declaration_module FROM truss.prop_def p JOIN truss.type_def t USING(type_id) WHERE t.document_id=document_row.doc_id AND p.retired_rev IS NULL
   UNION SELECT t.document_id,p.declaration_module FROM truss.prop_def p JOIN truss.type_def t USING(type_id) WHERE t.document_id=document_row.doc_id AND p.retired_rev IS NULL
   UNION SELECT n.value->>'documentId',n.value->'reference'->>'module' FROM truss.prop_def p JOIN truss.type_def t USING(type_id)
    CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(p.item)||coalesce(p.item->'descendants','[]'::jsonb)) n
    WHERE t.document_id=document_row.doc_id AND p.retired_rev IS NULL AND p.cardinality IN ('array','map')) dependencies;
  SELECT NOT EXISTS(SELECT 1 FROM truss.prop_def p JOIN truss.type_def t USING(type_id)
   WHERE t.document_id=document_row.doc_id AND t.retired_rev IS NULL AND p.retired_rev IS NULL AND p.cardinality IN ('array','map') AND truss.valid_item_chain(p.item) IS NOT TRUE) INTO items_valid;
  INSERT INTO truss.runtime_document_schema VALUES(NEW.rev,document_row.doc_id,jsonb_build_object(
   'pin',jsonb_build_object('documentId',document_row.doc_id,'revision',document_row.doc_revision,'sha256',document_row.content_sha256),
   'records',records,'relationships',relations,'readers',readers,'closed',closed,'itemsValid',items_valid));
 END LOOP;
 END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_index_type_schema() FROM PUBLIC;
CREATE TRIGGER runtime_type_schema_capture AFTER UPDATE ON truss.schema_head
 FOR EACH ROW WHEN (NEW.rev>0 AND OLD.rev IS DISTINCT FROM NEW.rev) EXECUTE FUNCTION truss.runtime_owned_index_type_schema();

REVOKE ALL ON TYPE truss.runtime_type_schema,truss.runtime_document_schema FROM PUBLIC;
