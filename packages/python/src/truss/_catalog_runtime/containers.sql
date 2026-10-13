-- One container level over exact scalar cells. Unknown retained containers have
-- no inferred item declaration; known properties validate their original item.
CREATE FUNCTION truss.valid_flat_cell(cell jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE member jsonb;
BEGIN
 IF truss.valid_scalar_cell(cell) IS TRUE THEN RETURN true;END IF;
 IF cell IS NULL OR jsonb_typeof(cell) IS DISTINCT FROM 'object' OR octet_length(cell::text)>1048576 THEN RETURN false;END IF;
 IF cell->>'kind'='sequence' THEN
  IF cell-ARRAY['kind','items']<>'{}'::jsonb OR jsonb_typeof(cell->'items') IS DISTINCT FROM 'array' OR jsonb_array_length(cell->'items')>1024 THEN RETURN false;END IF;
  FOR member IN SELECT value FROM jsonb_array_elements(cell->'items') LOOP IF truss.valid_scalar_cell(member) IS NOT TRUE THEN RETURN false;END IF;END LOOP;
  RETURN true;
 ELSIF cell->>'kind'='map' THEN
  IF cell-ARRAY['kind','entries']<>'{}'::jsonb OR jsonb_typeof(cell->'entries') IS DISTINCT FROM 'array' OR jsonb_array_length(cell->'entries')>1024 THEN RETURN false;END IF;
  FOR member IN SELECT value FROM jsonb_array_elements(cell->'entries') LOOP
   IF jsonb_typeof(member) IS DISTINCT FROM 'object' OR member-ARRAY['key','value']<>'{}'::jsonb OR jsonb_typeof(member->'key') IS DISTINCT FROM 'string'
    OR octet_length(member->>'key')>4096 OR truss.valid_scalar_cell(member->'value') IS NOT TRUE THEN RETURN false;END IF;
  END LOOP;
  RETURN jsonb_array_length(cell->'entries')=(SELECT count(DISTINCT value->>'key' COLLATE "C") FROM jsonb_array_elements(cell->'entries'));
 END IF;
 RETURN false;
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_flat_cell(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.canonical_flat_cell(cell jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF truss.valid_flat_cell(cell) IS NOT TRUE THEN RAISE EXCEPTION 'bounded exact flat value required' USING ERRCODE='22023';END IF;
 IF cell->>'kind'='map' THEN RETURN jsonb_build_object('kind','map','entries',(SELECT coalesce(jsonb_agg(value ORDER BY value->>'key' COLLATE "C"),'[]') FROM jsonb_array_elements(cell->'entries')));END IF;
 RETURN cell;
END;
$$;
REVOKE ALL ON FUNCTION truss.canonical_flat_cell(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.valid_property_value(cell jsonb,property truss.prop_def) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE item jsonb;member jsonb;family text;facets jsonb;
BEGIN
 IF property.cardinality='one' THEN RETURN property.home='json' AND coalesce(property.scalar_type,'') IN ('string','integer','decimal','boolean','timestamp','binary') AND property.nullability IN ('required','absent-allowed') AND property.item IS NULL AND truss.valid_scalar_property(cell,property.scalar_type,property.nullability='absent-allowed',property.facets);END IF;
 IF property.cardinality NOT IN ('array','map') OR property.scalar_type IS NOT NULL OR property.home IS DISTINCT FROM 'json'
  OR property.nullability NOT IN ('required','absent-allowed') OR coalesce(property.facets,'{}')<>'{}'::jsonb THEN RETURN false;END IF;
 item:=property.item->'declaration';family:=item->>'scalarType';facets:=item->'facets';
 IF item->>'kind' IS DISTINCT FROM 'field' OR item->>'cardinality' IS DISTINCT FROM 'one' OR item->>'nullability' IS DISTINCT FROM 'required'
  OR family IS NULL OR family NOT IN ('string','integer','decimal','boolean','timestamp','binary') OR item ? 'itemType'
  OR NOT ((coalesce(facets,'{}')='{}'::jsonb OR family='integer' AND facets='{"integerWidth":{"bits":64,"signed":true}}'::jsonb OR family='decimal' AND facets IN ('{"precision":18,"scale":4}'::jsonb,'{"precision":18,"scale":2}'::jsonb)) IS TRUE) THEN RETURN false;END IF;
 IF cell='{"kind":"null"}'::jsonb THEN RETURN property.nullability='absent-allowed';END IF;
 IF truss.valid_flat_cell(cell) IS NOT TRUE OR cell->>'kind' IS DISTINCT FROM (CASE property.cardinality WHEN 'array' THEN 'sequence' ELSE 'map' END) THEN RETURN false;END IF;
 FOR member IN SELECT CASE property.cardinality WHEN 'array' THEN value ELSE value->'value' END FROM jsonb_array_elements(CASE property.cardinality WHEN 'array' THEN cell->'items' ELSE cell->'entries' END) LOOP
  IF truss.valid_scalar_property(member,family,false,facets) IS NOT TRUE THEN RETURN false;END IF;
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
BEGIN
 IF jsonb_typeof(reference) IS DISTINCT FROM 'object' OR reference-ARRAY['module','element']<>'{}'::jsonb
  OR jsonb_typeof(reference->'module') IS DISTINCT FROM 'string' OR jsonb_typeof(reference->'element') IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'explicit qualified item Field required' USING ERRCODE='0A000';END IF;
 source:=original_text::json;
 SELECT m.value,m.ordinality::int-1 INTO STRICT module_json,module_index FROM json_array_elements(source->'modules') WITH ORDINALITY m WHERE m.value->>'id'=reference->>'module';
 SELECT e.value,e.ordinality::int-1 INTO STRICT fragment,element_index FROM json_array_elements(module_json->'elements') WITH ORDINALITY e WHERE e.value->>'id'=reference->>'element';
 declaration:=fragment::jsonb;
 IF declaration->>'kind' IS DISTINCT FROM 'field' OR declaration->>'cardinality' IS DISTINCT FROM 'one' OR declaration->>'nullability' IS DISTINCT FROM 'required'
  OR coalesce(declaration->>'scalarType','') NOT IN ('string','integer','decimal','boolean','timestamp','binary') OR declaration ? 'itemType'
  OR NOT ((coalesce(declaration->'facets','{}'::jsonb)='{}'::jsonb OR declaration->>'scalarType'='integer' AND declaration->'facets'='{"integerWidth":{"bits":64,"signed":true}}'::jsonb OR declaration->>'scalarType'='decimal' AND declaration->'facets' IN ('{"precision":18,"scale":4}'::jsonb,'{"precision":18,"scale":2}'::jsonb)) IS TRUE) THEN RAISE EXCEPTION 'required singular exact scalar item Field required' USING ERRCODE='0A000';END IF;
 pointer:='/modules/'||module_index||'/elements/'||element_index;original:=convert_to(fragment::text,'UTF8');source_digest:=encode(sha256(convert_to(original_text,'UTF8')),'hex');
 pin_input:='['||selected_revision||','||selected_ordinal||',"'||source_digest||'","'||pointer
  ||'",{"identity":"truss-original-json-definition","sha256":"08c2ec8c520b39ded40f270be0b26812db1d240d5bac1a00339b437200a2f58d","version":"0.1"},"'||encode(sha256(original),'hex')||'"]';
 result:=jsonb_build_object('reference',reference,'documentId',selected_document,'catalogRevision',selected_revision::text,'documentOrdinal',selected_ordinal::text,
  'umfVersion',source->>'umf','sourceSha256',source_digest,'originalPointer',pointer,'originalFragment',fragment::text,'definitionPin',encode(sha256(convert_to(pin_input,'UTF8')),'hex'),'declaration',declaration);
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
 ELSE example:=jsonb_build_object('kind',property.scalar_type,'text',CASE property.scalar_type WHEN 'integer' THEN '0' WHEN 'decimal' THEN '0' WHEN 'timestamp' THEN '2000-01-01T00:00:00Z' ELSE '' END);END IF;
 RETURN truss.valid_property_value(example,property) IS TRUE;
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_property_definition(truss.prop_def) FROM PUBLIC;

-- Interpretation requires current definition-module read authority. Object
-- effects still require the owning record module's writer, checked by callers.
CREATE FUNCTION truss.runtime_object_values_readable(selected_type int) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE selected truss.type_def;dependency record;
BEGIN
 SELECT * INTO selected FROM truss.type_def WHERE type_id=selected_type AND kind='record' AND retired_rev IS NULL;
 IF NOT FOUND OR NOT truss.runtime_can_read(selected.document_id,selected.module) THEN RETURN false;END IF;
 FOR dependency IN
  SELECT p.definition_document_id AS document_id,p.declaration_module AS module FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL
  UNION
  SELECT p.item->>'documentId',p.item->'reference'->>'module' FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.cardinality IN ('array','map')
 LOOP
  IF truss.runtime_can_read(dependency.document_id,dependency.module) IS NOT TRUE THEN RETURN false;END IF;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_object_values_readable(int) FROM PUBLIC;
