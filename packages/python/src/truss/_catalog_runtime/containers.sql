-- Compare complete authored item meaning separately from revision/source pins.
-- Historical flat items have no descendants; their original metadata is retained.
CREATE FUNCTION truss.catalog_item_meaning(item jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE nodes jsonb;node jsonb;result jsonb:='[]';
BEGIN
 IF item IS NULL OR jsonb_typeof(item) IS DISTINCT FROM 'object'
  OR jsonb_typeof(coalesce(item->'descendants','[]'::jsonb)) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'complete original item definition chain required' USING ERRCODE='22023';END IF;
 nodes:=jsonb_build_array(item)||coalesce(item->'descendants','[]'::jsonb);
 IF jsonb_array_length(nodes)>32 THEN RAISE EXCEPTION 'item definition depth limit' USING ERRCODE='54000';END IF;
 FOR node IN SELECT value FROM jsonb_array_elements(nodes) LOOP
  IF jsonb_typeof(node->'reference') IS DISTINCT FROM 'object'
   OR jsonb_typeof(node->'declaration') IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'complete authored item meaning required' USING ERRCODE='22023';END IF;
  result:=result||jsonb_build_array(jsonb_build_object('reference',node->'reference','declaration',node->'declaration'));
 END LOOP;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_item_meaning(jsonb) FROM PUBLIC;

-- One container level over exact scalar cells. Unknown retained containers have
-- no inferred item declaration; known properties validate their original item.
CREATE FUNCTION truss.valid_flat_cell(cell jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE member jsonb;cell_node jsonb;entry jsonb;pending jsonb:=jsonb_build_array(jsonb_build_object('cell',cell,'depth',0));depth int;count_nodes int:=0;
BEGIN
 IF cell IS NULL OR octet_length(cell::text)>1048576 THEN RETURN false;END IF;
 WHILE jsonb_array_length(pending)>0 LOOP
  entry:=pending->0;pending:=pending-0;cell_node:=entry->'cell';depth:=(entry->>'depth')::int;count_nodes:=count_nodes+1;
  IF depth>32 OR count_nodes>4096 THEN RETURN false;END IF;
  IF truss.valid_scalar_cell(cell_node) IS TRUE THEN CONTINUE;END IF;
  IF jsonb_typeof(cell_node) IS DISTINCT FROM 'object' THEN RETURN false;END IF;
  IF cell_node->>'kind'='sequence' THEN
   IF cell_node-ARRAY['kind','items']<>'{}'::jsonb OR jsonb_typeof(cell_node->'items') IS DISTINCT FROM 'array' OR jsonb_array_length(cell_node->'items')>1024 THEN RETURN false;END IF;
   FOR member IN SELECT value FROM jsonb_array_elements(cell_node->'items') LOOP
    pending:=pending||jsonb_build_array(jsonb_build_object('cell',member,'depth',depth+1));
   END LOOP;
  ELSIF cell_node->>'kind'='map' THEN
   IF cell_node-ARRAY['kind','entries']<>'{}'::jsonb OR jsonb_typeof(cell_node->'entries') IS DISTINCT FROM 'array' OR jsonb_array_length(cell_node->'entries')>1024 THEN RETURN false;END IF;
   IF jsonb_array_length(cell_node->'entries')<>(SELECT count(DISTINCT value->>'key' COLLATE "C") FROM jsonb_array_elements(cell_node->'entries')) THEN RETURN false;END IF;
   FOR member IN SELECT value FROM jsonb_array_elements(cell_node->'entries') LOOP
    IF jsonb_typeof(member) IS DISTINCT FROM 'object' OR member-ARRAY['key','value']<>'{}'::jsonb OR jsonb_typeof(member->'key') IS DISTINCT FROM 'string' OR octet_length(member->>'key')>4096 THEN RETURN false;END IF;
    pending:=pending||jsonb_build_array(jsonb_build_object('cell',member->'value','depth',depth+1));
   END LOOP;
  ELSE RETURN false;END IF;
  IF jsonb_array_length(pending)+count_nodes>4096 THEN RETURN false;END IF;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_flat_cell(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.canonical_flat_cell(cell jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF truss.valid_flat_cell(cell) IS NOT TRUE THEN RAISE EXCEPTION 'bounded exact container value required' USING ERRCODE='22023';END IF;
 IF cell->>'kind'='map' THEN RETURN jsonb_build_object('kind','map','entries',
  (SELECT coalesce(jsonb_agg(jsonb_build_object('key',value->'key','value',truss.canonical_flat_cell(value->'value')) ORDER BY value->>'key' COLLATE "C"),'[]') FROM jsonb_array_elements(cell->'entries')));END IF;
 IF cell->>'kind'='sequence' THEN RETURN jsonb_build_object('kind','sequence','items',
  (SELECT coalesce(jsonb_agg(truss.canonical_flat_cell(value) ORDER BY ordinality),'[]') FROM jsonb_array_elements(cell->'items') WITH ORDINALITY));END IF;
 RETURN cell;
END;
$$;
REVOKE ALL ON FUNCTION truss.canonical_flat_cell(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.valid_item_chain(item jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE nodes jsonb;node jsonb;declaration jsonb;seen jsonb:='[]';index_node int;family text;facets jsonb;
BEGIN
 IF item IS NULL OR jsonb_typeof(item) IS DISTINCT FROM 'object' OR jsonb_typeof(coalesce(item->'descendants','[]'::jsonb)) IS DISTINCT FROM 'array' THEN RETURN false;END IF;
 nodes:=jsonb_build_array(item)||coalesce(item->'descendants','[]'::jsonb);
 IF jsonb_array_length(nodes)>32 THEN RETURN false;END IF;
 FOR index_node IN 0..jsonb_array_length(nodes)-1 LOOP
  node:=nodes->index_node;declaration:=node->'declaration';family:=declaration->>'scalarType';facets:=declaration->'facets';
  IF jsonb_typeof(node->'reference') IS DISTINCT FROM 'object' OR seen @> jsonb_build_array(node->'reference')
   OR declaration->>'kind' IS DISTINCT FROM 'field' OR declaration->>'nullability' IS DISTINCT FROM 'required' THEN RETURN false;END IF;
  seen:=seen||jsonb_build_array(node->'reference');
  IF index_node=jsonb_array_length(nodes)-1 THEN
   IF declaration->>'cardinality' IS DISTINCT FROM 'one' OR family IS NULL OR family NOT IN ('string','integer','decimal','boolean','timestamp','binary','date') OR declaration ? 'itemType'
    OR NOT ((coalesce(facets,'{}')='{}'::jsonb OR family='integer' AND facets='{"integerWidth":{"bits":64,"signed":true}}'::jsonb OR family='decimal' AND truss.valid_decimal_facets(facets)) IS TRUE) THEN RETURN false;END IF;
  ELSE
   IF (declaration->>'cardinality' IN ('array','map')) IS NOT TRUE OR declaration ? 'scalarType' OR coalesce(facets,'{}')<>'{}'::jsonb
    OR declaration->'itemType' IS DISTINCT FROM nodes->(index_node+1)->'reference' THEN RETURN false;END IF;
  END IF;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_item_chain(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.valid_property_value(cell jsonb,property truss.prop_def) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE nodes jsonb;node jsonb;member jsonb;entry jsonb;declaration jsonb;pending jsonb:='[]';index_node int;
BEGIN
 IF property.cardinality='one' THEN RETURN property.home='json' AND coalesce(property.scalar_type,'') IN ('string','integer','decimal','boolean','timestamp','binary','date') AND property.nullability IN ('required','absent-allowed') AND property.item IS NULL AND truss.valid_scalar_property(cell,property.scalar_type,property.nullability='absent-allowed',property.facets);END IF;
 IF property.cardinality NOT IN ('array','map') OR property.scalar_type IS NOT NULL OR property.home IS DISTINCT FROM 'json'
  OR property.nullability NOT IN ('required','absent-allowed') OR coalesce(property.facets,'{}')<>'{}'::jsonb OR truss.valid_item_chain(property.item) IS NOT TRUE THEN RETURN false;END IF;
 IF cell='{"kind":"null"}'::jsonb THEN RETURN property.nullability='absent-allowed';END IF;
 IF truss.valid_flat_cell(cell) IS NOT TRUE OR cell->>'kind' IS DISTINCT FROM (CASE property.cardinality WHEN 'array' THEN 'sequence' ELSE 'map' END) THEN RETURN false;END IF;
 nodes:=jsonb_build_array(property.item)||coalesce(property.item->'descendants','[]'::jsonb);
 FOR member IN SELECT CASE property.cardinality WHEN 'array' THEN value ELSE value->'value' END FROM jsonb_array_elements(CASE property.cardinality WHEN 'array' THEN cell->'items' ELSE cell->'entries' END) LOOP
  pending:=pending||jsonb_build_array(jsonb_build_object('cell',member,'index',0));
 END LOOP;
 WHILE jsonb_array_length(pending)>0 LOOP
  entry:=pending->0;pending:=pending-0;member:=entry->'cell';index_node:=(entry->>'index')::int;node:=nodes->index_node;declaration:=node->'declaration';
  IF declaration->>'cardinality'='one' THEN
   IF truss.valid_scalar_property(member,declaration->>'scalarType',false,declaration->'facets') IS NOT TRUE THEN RETURN false;END IF;
  ELSE
   IF member->>'kind' IS DISTINCT FROM (CASE declaration->>'cardinality' WHEN 'array' THEN 'sequence' ELSE 'map' END) THEN RETURN false;END IF;
   FOR member IN SELECT CASE declaration->>'cardinality' WHEN 'array' THEN value ELSE value->'value' END FROM jsonb_array_elements(CASE declaration->>'cardinality' WHEN 'array' THEN member->'items' ELSE member->'entries' END) LOOP
    pending:=pending||jsonb_build_array(jsonb_build_object('cell',member,'index',index_node+1));
   END LOOP;
  END IF;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_property_value(jsonb,truss.prop_def) FROM PUBLIC;

CREATE FUNCTION truss.logical_flat_cell(cell jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF cell->>'kind' IN ('sequence','map') THEN RETURN truss.canonical_flat_cell(cell);END IF;
 RETURN truss.logical_scalar_cell(cell);
END;
$$;
REVOKE ALL ON FUNCTION truss.logical_flat_cell(jsonb) FROM PUBLIC;

-- Resolve one explicit same-document item Field from the exact source archive.
-- Item-only Fields are definitions; they never become synthetic record props.
CREATE FUNCTION truss.catalog_item_definition(original_text text,selected_document text,selected_revision int,selected_ordinal int,reference jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE source json;module_json json;fragment json;module_index int;element_index int;pointer text;original bytea;source_digest text;pin_input text;result jsonb;declaration jsonb;
 selected_reference jsonb:=reference;seen jsonb:='[]';chain jsonb:='[]';node jsonb;depth int:=0;
BEGIN
 source:=original_text::json;source_digest:=encode(sha256(convert_to(original_text,'UTF8')),'hex');
 LOOP
  depth:=depth+1;
  IF depth>32 THEN RAISE EXCEPTION 'item definition depth limit' USING ERRCODE='54000';END IF;
  IF jsonb_typeof(selected_reference) IS DISTINCT FROM 'object' OR selected_reference-ARRAY['module','element']<>'{}'::jsonb
   OR jsonb_typeof(selected_reference->'module') IS DISTINCT FROM 'string' OR jsonb_typeof(selected_reference->'element') IS DISTINCT FROM 'string' THEN
   RAISE EXCEPTION 'explicit qualified item Field required' USING ERRCODE='0A000';END IF;
  IF seen @> jsonb_build_array(selected_reference) THEN RAISE EXCEPTION 'acyclic item definition chain required' USING ERRCODE='0A000';END IF;
  seen:=seen||jsonb_build_array(selected_reference);
  SELECT m.value,m.ordinality::int-1 INTO STRICT module_json,module_index FROM json_array_elements(source->'modules') WITH ORDINALITY m WHERE m.value->>'id'=selected_reference->>'module';
  SELECT e.value,e.ordinality::int-1 INTO STRICT fragment,element_index FROM json_array_elements(module_json->'elements') WITH ORDINALITY e WHERE e.value->>'id'=selected_reference->>'element';
  declaration:=fragment::jsonb;
  IF declaration->>'kind' IS DISTINCT FROM 'field' OR declaration->>'nullability' IS DISTINCT FROM 'required' THEN
   RAISE EXCEPTION 'required original item Field required' USING ERRCODE='0A000';END IF;
  IF declaration->>'cardinality'='one' THEN
   IF coalesce(declaration->>'scalarType','') NOT IN ('string','integer','decimal','boolean','timestamp','binary','date') OR declaration ? 'itemType'
    OR NOT ((coalesce(declaration->'facets','{}'::jsonb)='{}'::jsonb OR declaration->>'scalarType'='integer' AND declaration->'facets'='{"integerWidth":{"bits":64,"signed":true}}'::jsonb OR declaration->>'scalarType'='decimal' AND truss.valid_decimal_facets(declaration->'facets')) IS TRUE) THEN
    RAISE EXCEPTION 'required exact scalar leaf Field required' USING ERRCODE='0A000';END IF;
  ELSIF declaration->>'cardinality' IN ('array','map') THEN
   IF declaration ? 'scalarType' OR coalesce(declaration->'facets','{}'::jsonb)<>'{}'::jsonb OR NOT declaration ? 'itemType' THEN
    RAISE EXCEPTION 'explicit unfaceted container item Field required' USING ERRCODE='0A000';END IF;
  ELSE RAISE EXCEPTION 'supported item Field cardinality required' USING ERRCODE='0A000';END IF;
  pointer:='/modules/'||module_index||'/elements/'||element_index;original:=convert_to(fragment::text,'UTF8');
  pin_input:='['||selected_revision||','||selected_ordinal||',"'||source_digest||'","'||pointer
   ||'",{"identity":"truss-original-json-definition","sha256":"08c2ec8c520b39ded40f270be0b26812db1d240d5bac1a00339b437200a2f58d","version":"0.1"},"'||encode(sha256(original),'hex')||'"]';
  node:=jsonb_build_object('reference',selected_reference,'documentId',selected_document,'catalogRevision',selected_revision::text,'documentOrdinal',selected_ordinal::text,
   'umfVersion',source->>'umf','sourceSha256',source_digest,'originalPointer',pointer,'originalFragment',fragment::text,'definitionPin',encode(sha256(convert_to(pin_input,'UTF8')),'hex'),'declaration',declaration);
  chain:=chain||jsonb_build_array(node);
  EXIT WHEN declaration->>'cardinality'='one';
  selected_reference:=declaration->'itemType';
 END LOOP;
 result:=chain->0;
 IF jsonb_array_length(chain)>1 THEN
  result:=result||jsonb_build_object('descendants',(SELECT jsonb_agg(value ORDER BY ordinality) FROM jsonb_array_elements(chain) WITH ORDINALITY WHERE ordinality>1));
 END IF;
 IF octet_length(result::text)>65536 THEN RAISE EXCEPTION 'item definition byte limit' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_item_definition(text,text,int,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.valid_property_definition(property truss.prop_def) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE example jsonb;
BEGIN
 IF property.cardinality IN ('array','map') THEN example:=CASE property.cardinality WHEN 'array' THEN '{"kind":"sequence","items":[]}'::jsonb ELSE '{"kind":"map","entries":[]}'::jsonb END;
 ELSIF property.scalar_type='boolean' THEN example:='{"kind":"boolean","value":false}'::jsonb;
 ELSE example:=jsonb_build_object('kind',property.scalar_type,'text',CASE property.scalar_type WHEN 'integer' THEN '0' WHEN 'decimal' THEN '0' WHEN 'date' THEN '2000-01-01' WHEN 'timestamp' THEN '2000-01-01T00:00:00Z' ELSE '' END);END IF;
 RETURN truss.valid_property_value(example,property) IS TRUE;
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_property_definition(truss.prop_def) FROM PUBLIC;

CREATE FUNCTION truss.runtime_item_chain_readable_qualified(item jsonb,qualified_actor oid) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE node jsonb;
BEGIN
 IF truss.valid_item_chain(item) IS NOT TRUE THEN RETURN false;END IF;
 FOR node IN SELECT value FROM jsonb_array_elements(jsonb_build_array(item)||coalesce(item->'descendants','[]'::jsonb)) LOOP
  IF truss.runtime_can_read_qualified(node->>'documentId',node->'reference'->>'module',qualified_actor) IS NOT TRUE THEN RETURN false;END IF;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_item_chain_readable_qualified(jsonb,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_item_chain_readable(item jsonb) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN truss.runtime_item_chain_readable_qualified(item,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_item_chain_readable(jsonb) FROM PUBLIC;

-- Interpretation requires current definition-module read authority. Object
-- effects still require the owning record module's writer, checked by callers.
-- Private actor is issued by the current native invocation, never retained
-- or accepted from a public caller. Module policy/membership checks stay live.
CREATE FUNCTION truss.runtime_object_values_readable_qualified(selected_type int,qualified_actor oid) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE selected truss.type_def;dependency record;compiled_readers jsonb;
BEGIN
 SELECT s.value_readers INTO compiled_readers FROM truss.runtime_type_schema s
  JOIN truss.type_def t ON t.type_id=s.type_id WHERE s.rev=(SELECT rev FROM truss.schema_head WHERE id=1)
   AND s.type_id=selected_type AND s.valid_properties AND t.kind='record' AND t.retired_rev IS NULL;
 IF FOUND THEN
  FOR dependency IN SELECT value->>'documentId' document_id,value->>'moduleId' module FROM jsonb_array_elements(compiled_readers) LOOP
   IF truss.runtime_can_read_qualified(dependency.document_id,dependency.module,qualified_actor) IS NOT TRUE THEN RETURN false;END IF;
  END LOOP;
  RETURN true;
 END IF;
 SELECT * INTO selected FROM truss.type_def WHERE type_id=selected_type AND kind='record' AND retired_rev IS NULL;
 IF NOT FOUND THEN RETURN false;END IF;
 IF EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.cardinality IN ('array','map') AND truss.valid_item_chain(p.item) IS NOT TRUE) THEN RETURN false;END IF;
 FOR dependency IN
  SELECT selected.document_id AS document_id,selected.module AS module
  UNION
  SELECT p.definition_document_id AS document_id,p.declaration_module AS module FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL
  UNION
  SELECT node.value->>'documentId',node.value->'reference'->>'module' FROM truss.prop_def p CROSS JOIN LATERAL jsonb_array_elements(jsonb_build_array(p.item)||coalesce(p.item->'descendants','[]'::jsonb)) node WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.cardinality IN ('array','map')
 LOOP
  IF truss.runtime_can_read_qualified(dependency.document_id,dependency.module,qualified_actor) IS NOT TRUE THEN RETURN false;END IF;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_values_readable_qualified(int,oid) FROM PUBLIC;

CREATE FUNCTION truss.runtime_object_values_readable(selected_type int) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 RETURN truss.runtime_object_values_readable_qualified(selected_type,truss.runtime_person(false));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_values_readable(int) FROM PUBLIC;
