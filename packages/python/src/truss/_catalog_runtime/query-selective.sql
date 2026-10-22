-- SPDX-License-Identifier: MIT OR Apache-2.0
-- ABI1.2 candidate sources. Canonical cells and original UMF key bytes stay unchanged.
-- Keep this index immediately searchable after managed writes; account for its
-- synchronous maintenance in the actual write/import qualification workload.
CREATE INDEX object_query_cells_gin ON truss.object USING gin (props jsonb_path_ops) WITH (fastupdate=off);

-- A derived ordering projection of the existing single-string UMF key tuple.
-- NULL means outside this index's bounded subset, never an absent business key.
CREATE FUNCTION truss.runtime_query_single_string_key(transport bytea) RETURNS text
LANGUAGE plpgsql IMMUTABLE STRICT SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE token text;tuple bytea;payload_size int;second int;offset_bytes int;
BEGIN
 IF octet_length(transport) NOT BETWEEN 37 AND 2100 THEN RETURN NULL;END IF;
 token:=convert_from(transport,'UTF8');
 IF token !~ '^umf-key-tuple-v1:hex:[0-9a-f]+$' OR (length(token)-21)%2<>0 THEN RETURN NULL;END IF;
 tuple:=decode(substring(token FROM 22),'hex');
 IF octet_length(tuple)<8 OR substring(tuple FROM 1 FOR 7)<>decode('554d464b310104','hex') THEN RETURN NULL;END IF;
 payload_size:=get_byte(tuple,7);offset_bytes:=8;
 IF payload_size>=128 THEN
  IF octet_length(tuple)<9 THEN RETURN NULL;END IF;
  second:=get_byte(tuple,8);
  IF second NOT BETWEEN 1 AND 8 THEN RETURN NULL;END IF;
  payload_size:=payload_size-128+128*second;offset_bytes:=9;
 END IF;
 IF payload_size>1024 OR octet_length(tuple)<>offset_bytes+payload_size THEN RETURN NULL;END IF;
 RETURN convert_from(substring(tuple FROM offset_bytes+1),'UTF8');
EXCEPTION WHEN character_not_in_repertoire OR invalid_parameter_value THEN RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_query_single_string_key(bytea) FROM PUBLIC;

-- The native namespace is installation/epoch/type/key/immutable-definition scoped,
-- with no root/person component. This index enforces the same authored uniqueness
-- over the admitted short single-string subset. Other key tuples remain valid.
CREATE UNIQUE INDEX object_key_query_string_order ON truss.object_key_bucket
 (type_id,key_num,(truss.runtime_query_single_string_key(key_bytes) COLLATE "C"))
 WHERE truss.runtime_query_single_string_key(key_bytes) IS NOT NULL;
CREATE INDEX object_key_query_string_exception ON truss.object_key_bucket(type_id,key_num)
 WHERE truss.runtime_query_single_string_key(key_bytes) IS NULL;

-- Shared selected-row checks retain the ordinary source's numeric/root/byte gates.
CREATE FUNCTION truss.runtime_query_checked_ids(binding jsonb,selected_type int,selected_ids bigint[])
RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE owner truss.type_def%ROWTYPE;object_row truss.object%ROWTYPE;selected_row record;numeric_properties jsonb;
 row_count int:=0;byte_count bigint:=0;root_identity jsonb;roots jsonb:='{}';root_entry jsonb;
BEGIN
 PERFORM truss.query_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type)
  THEN RAISE EXCEPTION 'selected query record required' USING ERRCODE='22023';END IF;
 IF selected_ids IS NULL OR cardinality(selected_ids)>(binding->>'maximumScanRows')::int THEN
  RAISE EXCEPTION 'bounded selected query source required' USING ERRCODE='54000';END IF;
 SELECT * INTO STRICT owner FROM truss.type_def t WHERE t.type_id=selected_type AND t.retired_rev IS NULL;
 SELECT coalesce(jsonb_agg(jsonb_build_object('propertyId',p.prop_id::text,'scalarType',p.scalar_type) ORDER BY p.prop_id),'[]'::jsonb)
 INTO numeric_properties FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.scalar_type IN ('integer','decimal');
 FOR selected_row IN
  SELECT o AS object_row,NOT EXISTS(
   SELECT 1 FROM jsonb_array_elements(numeric_properties) f
   CROSS JOIN LATERAL (SELECT o.props->(f.value->>'propertyId') AS cell) selected_cell
   WHERE selected_cell.cell IS NOT NULL AND selected_cell.cell<>'{"kind":"null"}'::jsonb
    AND truss.query_numeric_value(selected_cell.cell->>'text',f.value->>'scalarType') IS NOT TRUE
  ) AS numeric_valid
  FROM truss.object o WHERE o.type_id=selected_type AND o.id=ANY(selected_ids) LOOP
  object_row:=selected_row.object_row;row_count:=row_count+1;
  byte_count:=byte_count+octet_length(object_row.props::text);
  IF byte_count>(binding->>'maximumBytes')::int THEN RAISE EXCEPTION 'bounded selected query bytes required' USING ERRCODE='54000';END IF;
  root_identity:=truss.query_object_root(binding,object_row);
  IF root_identity IS NOT NULL THEN roots:=roots||jsonb_build_object((root_identity->>'typeId')||':'||(root_identity->>'id'),root_identity);END IF;
  IF byte_count+(CASE WHEN roots='{}'::jsonb THEN 0 ELSE octet_length(roots::text) END)>(binding->>'maximumBytes')::int THEN
   RAISE EXCEPTION 'bounded selected query root witnesses required' USING ERRCODE='54000';END IF;
  IF object_row.ver<=0 OR object_row.rev>(binding->>'catalogRevision')::int THEN
   RAISE EXCEPTION 'complete scalar source required' USING ERRCODE='0A000';END IF;
  IF NOT selected_row.numeric_valid THEN RAISE EXCEPTION 'exact native numeric domain unavailable' USING ERRCODE='22003';END IF;
  id:=object_row.id;props:=object_row.props;RETURN NEXT;
 END LOOP;
 IF row_count<>cardinality(selected_ids) THEN RAISE EXCEPTION 'complete selected object identities required' USING ERRCODE='55000';END IF;
 FOR root_entry IN SELECT value FROM jsonb_each(roots) LOOP
  IF NOT truss.runtime_can_read(root_entry->'owner'->>'documentId',root_entry->'owner'->>'moduleId') THEN
   RAISE EXCEPTION 'current buffered query aggregate root reader required' USING ERRCODE='P1403';END IF;
 END LOOP;
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_query_checked_ids(jsonb,int,bigint[]) FROM PUBLIC;

CREATE FUNCTION truss.query_selected_objects(binding jsonb,selected_type int,selected_cells jsonb)
RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE property_id text;cell jsonb;definition truss.prop_def%ROWTYPE;selected_ids bigint[];
BEGIN
 PERFORM truss.query_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type) THEN
  RAISE EXCEPTION 'selected query record required' USING ERRCODE='22023';END IF;
 IF octet_length(selected_cells::text)>8388608 THEN
  RAISE EXCEPTION 'bounded selected cell envelope required' USING ERRCODE='54000';END IF;
 IF jsonb_typeof(selected_cells) IS DISTINCT FROM 'object'
  OR (SELECT count(*) FROM jsonb_object_keys(selected_cells))<>1 THEN
  RAISE EXCEPTION 'one bounded exact selected cell required' USING ERRCODE='22023';END IF;
 SELECT key,value INTO STRICT property_id,cell FROM jsonb_each(selected_cells);
 IF cell->>'kind'='string' AND octet_length(cell->>'text')>1048576 THEN
  RAISE EXCEPTION 'bounded selected string operand required' USING ERRCODE='54000';END IF;
 SELECT * INTO definition FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id::text=property_id AND p.retired_rev IS NULL;
 IF NOT FOUND OR definition.home<>'json' OR definition.cardinality<>'one' OR definition.scalar_type NOT IN ('string','boolean')
  OR truss.valid_property_value(cell,definition) IS NOT TRUE OR cell->>'kind' IS DISTINCT FROM definition.scalar_type THEN
  RAISE EXCEPTION 'admitted exact string or boolean selection required' USING ERRCODE='22023';END IF;
 SELECT coalesce(array_agg(candidate.id),'{}'::bigint[]) INTO selected_ids
 FROM (SELECT o.id FROM truss.object o WHERE o.type_id=selected_type AND o.props @> selected_cells
  LIMIT (binding->>'maximumScanRows')::int+1) candidate;
 RETURN QUERY SELECT q.* FROM truss.runtime_query_checked_ids(binding,selected_type,selected_ids) q;
END;
$$;
REVOKE ALL ON FUNCTION truss.query_selected_objects(jsonb,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.query_seek_objects(binding jsonb,selected_type int,selected_key text,after_value text,page_limit int)
RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE key_definition truss.key_def%ROWTYPE;component truss.prop_def%ROWTYPE;selected_ids bigint[];row record;
BEGIN
 PERFORM truss.query_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type) THEN
  RAISE EXCEPTION 'selected query record required' USING ERRCODE='22023';END IF;
 IF page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 1000 THEN
  RAISE EXCEPTION 'bounded ordered page source required' USING ERRCODE='22023';END IF;
 SELECT * INTO key_definition FROM truss.key_def k WHERE k.type_id=selected_type AND k.key_id=selected_key AND k.retired_rev IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'original authored page key required' USING ERRCODE='22023';END IF;
 IF cardinality(key_definition.prop_ids)=1 THEN
  SELECT * INTO component FROM truss.prop_def p WHERE p.type_id=selected_type AND p.prop_id=key_definition.prop_ids[1] AND p.retired_rev IS NULL;
 END IF;
 IF component.scalar_type IS DISTINCT FROM 'string' OR component.nullability IS DISTINCT FROM 'required' OR component.cardinality IS DISTINCT FROM 'one'
  OR component.home IS DISTINCT FROM 'json' OR coalesce(component.facets,'{}')<>'{}'::jsonb
  OR EXISTS(SELECT 1 FROM truss.object_key_bucket k WHERE k.type_id=selected_type AND k.key_num=key_definition.key_num
   AND truss.runtime_query_single_string_key(k.key_bytes) IS NULL) THEN
  RETURN QUERY SELECT q.* FROM truss.query_page_objects(binding,selected_type,selected_key) q;RETURN;
 END IF;
 -- Separate first/continuation statements retain directly indexable ordered predicates.
 IF after_value IS NULL THEN
  SELECT coalesce(array_agg(candidate.object_id),'{}'::bigint[]) INTO selected_ids FROM (
   SELECT k.object_id FROM truss.object_key_bucket k WHERE k.type_id=selected_type AND k.key_num=key_definition.key_num
    AND truss.runtime_query_single_string_key(k.key_bytes) IS NOT NULL
   ORDER BY truss.runtime_query_single_string_key(k.key_bytes) COLLATE "C"
   LIMIT least(page_limit,(binding->>'maximumScanRows')::int+1)) candidate;
 ELSE
  SELECT coalesce(array_agg(candidate.object_id),'{}'::bigint[]) INTO selected_ids FROM (
   SELECT k.object_id FROM truss.object_key_bucket k WHERE k.type_id=selected_type AND k.key_num=key_definition.key_num
    AND truss.runtime_query_single_string_key(k.key_bytes) IS NOT NULL
    AND (truss.runtime_query_single_string_key(k.key_bytes) COLLATE "C")>(after_value COLLATE "C")
   ORDER BY truss.runtime_query_single_string_key(k.key_bytes) COLLATE "C"
   LIMIT least(page_limit,(binding->>'maximumScanRows')::int+1)) candidate;
 END IF;
 FOR row IN SELECT q.* FROM truss.runtime_query_checked_ids(binding,selected_type,selected_ids) q LOOP
  IF NOT EXISTS(SELECT 1 FROM truss.object_key_bucket k WHERE k.type_id=selected_type AND k.key_num=key_definition.key_num AND k.object_id=row.id
   AND truss.runtime_query_single_string_key(k.key_bytes) IS NOT DISTINCT FROM row.props->component.prop_id::text->>'text') THEN
   RAISE EXCEPTION 'original canonical ordered key correspondence required' USING ERRCODE='55000';END IF;
  id:=row.id;props:=row.props;RETURN NEXT;
 END LOOP;
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_seek_objects(jsonb,int,text,text,int) FROM PUBLIC;
