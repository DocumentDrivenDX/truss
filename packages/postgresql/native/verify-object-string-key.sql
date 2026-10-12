-- Private writer helper: derive expected components from actual object rows.
-- Caller holds the object's mutation lock and the accepted catalog-head lock.
CREATE FUNCTION truss.verify_object_string_key(selected_object bigint,selected_type int,selected_key smallint,tuple_bytes bytea)
RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE object_row truss.object%ROWTYPE; key_row truss.key_def%ROWTYPE;
 component record;cell jsonb;actual_values text[]:=ARRAY[]::text[];counted int:=0;
BEGIN
 SELECT * INTO object_row FROM truss.object WHERE id=selected_object AND type_id=selected_type;
 IF NOT FOUND OR object_row.root_id IS NOT NULL THEN RETURN false; END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.type_def WHERE type_id=selected_type
   AND kind='record' AND NOT provisional AND retired_rev IS NULL) THEN RETURN false; END IF;
 SELECT * INTO key_row FROM truss.key_def WHERE type_id=selected_type AND key_num=selected_key AND retired_rev IS NULL;
 IF NOT FOUND OR cardinality(key_row.prop_ids) NOT BETWEEN 1 AND 1024 THEN RETURN false; END IF;
 FOR component IN SELECT p.prop_id,p.scalar_type,p.retired_rev,p.home,p.cardinality,p.nullability
  FROM unnest(key_row.prop_ids) WITH ORDINALITY k(prop_id,ord)
  JOIN truss.prop_def p ON p.prop_id=k.prop_id AND p.type_id=selected_type ORDER BY k.ord LOOP
  counted:=counted+1;
  IF component.scalar_type IS DISTINCT FROM 'string' OR component.retired_rev IS NOT NULL
   OR component.home IS DISTINCT FROM 'json' OR component.cardinality IS DISTINCT FROM 'one'
   OR component.nullability IS DISTINCT FROM 'required' THEN RETURN false; END IF;
  cell:=object_row.props->component.prop_id::text;
  IF jsonb_typeof(cell) IS DISTINCT FROM 'object' OR cell->>'kind' IS DISTINCT FROM 'string'
   OR jsonb_typeof(cell->'text') IS DISTINCT FROM 'string' OR cell-'kind'-'text'<>'{}'::jsonb THEN RETURN false; END IF;
  actual_values:=array_append(actual_values,cell->>'text');
 END LOOP;
 IF counted<>cardinality(key_row.prop_ids) THEN RETURN false; END IF;
 RETURN truss.verify_umf_string_key_tuple(tuple_bytes,actual_values);
END;
$$;
REVOKE ALL ON FUNCTION truss.verify_object_string_key(bigint,int,smallint,bytea) FROM PUBLIC;
