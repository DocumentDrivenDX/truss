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
DECLARE basis jsonb;type_basis jsonb;selected record;property record;pin record;
 property_order jsonb;property_pins jsonb;property_access jsonb;type_pin text;query_record jsonb;compiled_records jsonb[]:='{}';document_revision text;properties_by_type jsonb;keys_by_type jsonb;missing_pins boolean;value_readers jsonb;valid_properties boolean;document_row record;records jsonb;relations jsonb;readers jsonb;closed boolean;items_valid boolean;
BEGIN
 -- The accepted head already contains the installed, validated native rows.
 -- Historical initialization retains its original reconstruction; the current
 -- revision does not parse and rebuild the complete catalog a second time.
 IF NEW.rev=(SELECT rev FROM truss.schema_head WHERE id=1)
  AND NOT EXISTS(SELECT 1 FROM truss.schema_rev WHERE rev>NEW.rev) THEN
  basis:=jsonb_build_object(
   'type_def',(SELECT coalesce(jsonb_agg(to_jsonb(t)),'[]'::jsonb) FROM truss.type_def t),
   'prop_def',(SELECT coalesce(jsonb_agg(to_jsonb(p)),'[]'::jsonb) FROM truss.prop_def p),
   'key_def',(SELECT coalesce(jsonb_agg(to_jsonb(k)),'[]'::jsonb) FROM truss.key_def k));
 ELSE basis:=truss.catalog_all_expected_records(NEW.rev);END IF;
 SELECT coalesce(jsonb_object_agg(type_id::text,properties),'{}'::jsonb) INTO properties_by_type
 FROM (SELECT (p.value->>'type_id')::int type_id,jsonb_agg(p.value ORDER BY (p.value->>'prop_id')::int) properties
  FROM jsonb_array_elements(basis->'prop_def') p GROUP BY (p.value->>'type_id')::int) grouped;
 SELECT coalesce(jsonb_object_agg(type_id::text,keys),'{}'::jsonb) INTO keys_by_type
 FROM (SELECT (k.value->>'type_id')::int type_id,jsonb_agg(k.value ORDER BY (k.value->>'key_num')::int) keys
  FROM jsonb_array_elements(basis->'key_def') k GROUP BY (k.value->>'type_id')::int) grouped;
 FOR selected IN SELECT * FROM jsonb_populate_recordset(NULL::truss.type_def,basis->'type_def') t
  WHERE t.kind='record' AND NOT t.provisional AND (t.retired_rev IS NULL OR t.retired_rev>NEW.rev) ORDER BY type_id LOOP
  type_basis:=jsonb_build_object('type_def',jsonb_build_array(to_jsonb(selected)),
   'prop_def',coalesce(properties_by_type->selected.type_id::text,'[]'::jsonb));
  SELECT d.definition_pin INTO STRICT type_pin FROM truss.runtime_definition_source d
   WHERE d.rev=selected.definition_rev AND d.ord=selected.definition_doc_ord AND d.doc_id=selected.definition_document_id
    AND d.module_id=selected.module AND d.element_id=selected.element AND d.kind='element' AND d.key_id='';
  SELECT coalesce(jsonb_agg(p.prop_id::text ORDER BY p.prop_id),'[]'::jsonb),
   coalesce(jsonb_object_agg(p.prop_id::text,d.definition_pin),'{}'::jsonb),
   coalesce(bool_or(d.definition_pin IS NULL OR p.definition_source_kind<>'accepted_document'),false)
   INTO property_order,property_pins,missing_pins
   FROM jsonb_populate_recordset(NULL::truss.prop_def,type_basis->'prop_def') p
   LEFT JOIN truss.runtime_definition_source d ON d.rev=p.definition_rev AND d.ord=p.definition_doc_ord
    AND d.doc_id=p.definition_document_id AND d.module_id=p.declaration_module AND d.element_id=p.element AND d.kind='element' AND d.key_id=''
   WHERE p.since_rev<=NEW.rev AND (p.retired_rev IS NULL OR p.retired_rev>NEW.rev);
  IF missing_pins THEN RAISE EXCEPTION 'complete original compiled schema pins required' USING ERRCODE='55000';END IF;
  SELECT doc_revision INTO STRICT document_revision FROM truss.schema_doc
   WHERE doc_id=selected.document_id AND rev<=NEW.rev ORDER BY rev DESC LIMIT 1;
  query_record:=jsonb_build_object('identity',jsonb_build_object('documentId',selected.document_id,
   'revision',document_revision,'module',selected.module,'element',selected.element),'typeId',selected.type_id::text,
   'keys',(SELECT coalesce(jsonb_agg(jsonb_build_object('keyId',k.key_id,'propertyIds',
    (SELECT jsonb_agg(v.prop_id::text ORDER BY v.ordinal) FROM unnest(k.prop_ids) WITH ORDINALITY v(prop_id,ordinal))) ORDER BY k.key_num),'[]'::jsonb)
    FROM jsonb_populate_recordset(NULL::truss.key_def,coalesce(keys_by_type->selected.type_id::text,'[]'::jsonb)) k WHERE k.type_id=selected.type_id AND (k.retired_rev IS NULL OR k.retired_rev>NEW.rev)),
   'fields',(SELECT coalesce(jsonb_agg(jsonb_build_object('identity',jsonb_build_object('documentId',selected.document_id,
    'revision',document_revision,'module',p.declaration_module,'element',p.element),'propertyId',p.prop_id::text) ORDER BY p.prop_id),'[]'::jsonb)
    FROM jsonb_populate_recordset(NULL::truss.prop_def,type_basis->'prop_def') p WHERE p.retired_rev IS NULL OR p.retired_rev>NEW.rev));
  SELECT coalesce(jsonb_agg(jsonb_build_object('documentId',document_id,'moduleId',module_id) ORDER BY document_id,module_id),'[]'::jsonb) INTO value_readers FROM (
   SELECT selected.document_id document_id,selected.module module_id
   UNION SELECT p.definition_document_id,p.declaration_module FROM jsonb_populate_recordset(NULL::truss.prop_def,type_basis->'prop_def') p WHERE p.retired_rev IS NULL OR p.retired_rev>NEW.rev
   UNION SELECT n.value->>'documentId',n.value->'reference'->>'module' FROM jsonb_populate_recordset(NULL::truss.prop_def,type_basis->'prop_def') p
    CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(p.item)||coalesce(p.item->'descendants','[]'::jsonb)) n
    WHERE (p.retired_rev IS NULL OR p.retired_rev>NEW.rev) AND p.cardinality IN ('array','map')) dependencies;
  SELECT coalesce(bool_and(truss.valid_property_definition(p)),true) INTO valid_properties FROM jsonb_populate_recordset(NULL::truss.prop_def,type_basis->'prop_def') p WHERE p.retired_rev IS NULL OR p.retired_rev>NEW.rev;
  -- Retain only interpretation dependencies, rather than another complete
  -- copy of every native property definition inside the compiled schema.
  SELECT coalesce(jsonb_object_agg(p.prop_id::text,jsonb_build_object(
   'itemsValid',CASE WHEN p.cardinality IN ('array','map') THEN truss.valid_item_chain(p.item) IS TRUE ELSE true END,
   'readers',(SELECT jsonb_agg(jsonb_build_object('documentId',document_id,'moduleId',module_id) ORDER BY document_id,module_id) FROM (
    SELECT p.definition_document_id document_id,p.declaration_module module_id
    UNION SELECT n.value->>'documentId',n.value->'reference'->>'module'
     FROM jsonb_array_elements(jsonb_build_array(p.item)||coalesce(p.item->'descendants','[]'::jsonb)) n
     WHERE p.cardinality IN ('array','map')) dependencies))),'{}'::jsonb) INTO property_access
   FROM jsonb_populate_recordset(NULL::truss.prop_def,type_basis->'prop_def') p
   WHERE p.since_rev<=NEW.rev AND (p.retired_rev IS NULL OR p.retired_rev>NEW.rev);
  compiled_records:=array_append(compiled_records,query_record);
  INSERT INTO truss.runtime_type_schema VALUES(NEW.rev,selected.type_id,jsonb_build_object(
   'typeId',selected.type_id::text,'revision',NEW.rev::text,'typePin',type_pin,
   'propertyOrder',property_order,'propertyPins',property_pins,'propertyAccess',property_access),value_readers,valid_properties);
 END LOOP;
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
