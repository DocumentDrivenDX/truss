-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Native export sources v0.1: separately selected by the export compiler profile.
-- Ordinary binding scan/result limits do not cap these complete sources.
-- Each row remains byte-bounded; metadata admission and all value/root checks remain.

CREATE FUNCTION truss.query_export_objects(binding jsonb,selected_type int) RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE owner truss.type_def%ROWTYPE;object_row truss.object%ROWTYPE;property truss.prop_def%ROWTYPE;cell jsonb;
BEGIN
 PERFORM truss.query_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type) THEN RAISE EXCEPTION 'selected query record required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT owner FROM truss.type_def t WHERE t.type_id=selected_type AND t.retired_rev IS NULL;
 FOR property IN SELECT * FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL LOOP
  IF truss.valid_property_definition(property) IS NOT TRUE THEN RAISE EXCEPTION 'query value profile unavailable' USING ERRCODE='0A000';END IF;
 END LOOP;
 FOR object_row IN SELECT * FROM truss.object o WHERE o.type_id=selected_type ORDER BY o.id LOOP
  IF octet_length(object_row.props::text)>(binding->>'maximumBytes')::int THEN RAISE EXCEPTION 'bounded export source row required' USING ERRCODE='54000';END IF;
  PERFORM truss.query_object_root(binding,object_row);
  IF object_row.ver<=0 OR object_row.rev> (binding->>'catalogRevision')::int
   OR EXISTS(SELECT 1 FROM jsonb_object_keys(object_row.props) k WHERE NOT EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.prop_id::text=k)) THEN RAISE EXCEPTION 'complete scalar source required' USING ERRCODE='0A000';END IF;
  FOR property IN SELECT * FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL LOOP
   cell:=object_row.props->property.prop_id::text;
   IF cell IS NULL THEN IF property.nullability='required' THEN RAISE EXCEPTION 'required query value missing' USING ERRCODE='55000';END IF;
   ELSIF truss.valid_property_value(cell,property) IS NOT TRUE THEN RAISE EXCEPTION 'malformed query scalar' USING ERRCODE='55000';
   ELSIF property.scalar_type IN ('integer','decimal') AND cell->>'kind'<>'null' AND truss.query_numeric_value(cell->>'text',property.scalar_type) IS NOT TRUE THEN RAISE EXCEPTION 'exact native numeric domain unavailable' USING ERRCODE='22003';END IF;
  END LOOP;
  id:=object_row.id;props:=object_row.props;RETURN NEXT;
 END LOOP;
 -- Every root owner is in the selected original documents. Rechecking every
 -- selected module covers those owners without retaining a root-sized map.
 -- PostgreSQL buffers the complete validated source; work_mem/spill applies.
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_export_objects(jsonb,int) FROM PUBLIC;


CREATE FUNCTION truss.query_export_edges(binding jsonb,selected_relationship int) RETURNS TABLE(id bigint,source_id bigint,target_id bigint)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE relation truss.rel_def%ROWTYPE;edge_row truss.edge%ROWTYPE;source_object truss.object%ROWTYPE;target_object truss.object%ROWTYPE;
BEGIN
 PERFORM truss.query_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'relationships') r WHERE (r.value->>'relationshipTypeId')::int=selected_relationship) THEN RAISE EXCEPTION 'selected query relationship required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT relation FROM truss.rel_def r WHERE r.rel_type_id=selected_relationship AND r.retired_rev IS NULL;
 FOR edge_row IN SELECT * FROM truss.edge e WHERE e.rel_type_id=selected_relationship ORDER BY e.id LOOP
  IF octet_length(edge_row.props::text)>(binding->>'maximumBytes')::int THEN RAISE EXCEPTION 'bounded export edge row required' USING ERRCODE='54000';END IF;
  SELECT * INTO source_object FROM truss.object o WHERE o.id=edge_row.source_id AND o.type_id=edge_row.source_type;
  IF NOT FOUND THEN RAISE EXCEPTION 'query source endpoint missing' USING ERRCODE='55000';END IF;
  SELECT * INTO target_object FROM truss.object o WHERE o.id=edge_row.target_id AND o.type_id=edge_row.target_type;
  IF NOT FOUND OR edge_row.ver<=0 OR edge_row.rev>(binding->>'catalogRevision')::int OR source_object.ver<=0 OR target_object.ver<=0
   OR source_object.rev>(binding->>'catalogRevision')::int OR target_object.rev>(binding->>'catalogRevision')::int
   OR NOT EXISTS(SELECT 1 FROM truss.rel_endpoint e WHERE e.rel_type_id=selected_relationship AND e.source_type=edge_row.source_type AND e.target_type=edge_row.target_type) THEN
   RAISE EXCEPTION 'complete independent query endpoints required' USING ERRCODE='55000';END IF;
  PERFORM truss.query_object_root(binding,source_object);
  PERFORM truss.query_object_root(binding,target_object);
  id:=edge_row.id;source_id:=edge_row.source_id;target_id:=edge_row.target_id;RETURN NEXT;
 END LOOP;
 -- Complete selected-document admission covers every validated root owner.
 -- The complete edge bag is buffered under normal PostgreSQL work_mem/spill.
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_export_edges(jsonb,int) FROM PUBLIC;


CREATE FUNCTION truss.query_export_page_objects(binding jsonb,selected_type int,selected_key text) RETURNS TABLE(id bigint,props jsonb)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE key_definition truss.key_def%ROWTYPE;component truss.prop_def%ROWTYPE;row record;counted int:=0;
BEGIN
 PERFORM truss.query_scope(binding);
 IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(binding->'records') r WHERE (r.value->>'typeId')::int=selected_type) THEN RAISE EXCEPTION 'selected query record required' USING ERRCODE='P1403';END IF;
 SELECT * INTO key_definition FROM truss.key_def k WHERE k.type_id=selected_type AND k.key_id=selected_key AND k.retired_rev IS NULL;
 IF NOT FOUND OR cardinality(key_definition.prop_ids) NOT BETWEEN 1 AND 1024 THEN RAISE EXCEPTION 'bounded authored page key required' USING ERRCODE='0A000';END IF;
 FOR component IN SELECT p.* FROM unnest(key_definition.prop_ids) WITH ORDINALITY k(prop_id,n) JOIN truss.prop_def p ON p.prop_id=k.prop_id AND p.type_id=selected_type ORDER BY k.n LOOP
  counted:=counted+1;
  IF component.retired_rev IS NOT NULL OR component.scalar_type NOT IN ('string','boolean','integer','decimal') OR component.nullability<>'required' OR component.cardinality<>'one' OR component.home<>'json' OR NOT ((component.scalar_type IN ('string','boolean') AND coalesce(component.facets,'{}')='{}'::jsonb OR component.scalar_type='integer' AND (coalesce(component.facets,'{}')='{}'::jsonb OR component.facets='{"integerWidth":{"bits":64,"signed":true}}'::jsonb) OR component.scalar_type='decimal' AND truss.valid_decimal_facets(component.facets)) IS TRUE) THEN RAISE EXCEPTION 'required exact page key components required' USING ERRCODE='0A000';END IF;
 END LOOP;
 IF counted<>cardinality(key_definition.prop_ids) THEN RAISE EXCEPTION 'complete page key required' USING ERRCODE='55000';END IF;
 FOR row IN SELECT q.* FROM truss.query_export_objects(binding,selected_type) q LOOP
  id:=row.id;props:=row.props;RETURN NEXT;
 END LOOP;
 -- The preceding SRF validates the complete export source in this snapshot.
 -- Validated typed tuple equality matches emitted C-text/bool/numeric ROW.
 IF EXISTS(SELECT 1 FROM (SELECT (SELECT jsonb_agg(CASE property.scalar_type WHEN 'boolean' THEN o.props->property.prop_id::text->'value' WHEN 'integer' THEN to_jsonb((o.props->property.prop_id::text->>'text')::numeric) WHEN 'decimal' THEN to_jsonb((o.props->property.prop_id::text->>'text')::numeric) ELSE to_jsonb(o.props->property.prop_id::text->>'text') END ORDER BY p.n)
  FROM unnest(key_definition.prop_ids) WITH ORDINALITY p(prop_id,n) JOIN truss.prop_def property ON property.prop_id=p.prop_id AND property.type_id=selected_type) AS key_values
  FROM truss.object o WHERE o.type_id=selected_type) source GROUP BY source.key_values HAVING count(*)>1) THEN
  RAISE EXCEPTION 'unique authored page key required' USING ERRCODE='55000';END IF;
 PERFORM truss.query_scope(binding);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_export_page_objects(jsonb,int,text) FROM PUBLIC;
