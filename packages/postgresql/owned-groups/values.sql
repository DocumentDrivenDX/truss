-- Ordered object-value simulation for the owned-group executor.
-- Uninstalled candidate. Caller supplies an admitted type and simulated prior image;
-- this function performs no graph write, allocation or authorization issuance.
CREATE FUNCTION truss.owned_object_values(selected_type int,operation jsonb,prior_props jsonb,prior_retained jsonb) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE authored jsonb;removed jsonb;props jsonb;retained jsonb;removed_props text[];removed_retained text[];set_props jsonb;set_retained jsonb;
 property truss.prop_def%ROWTYPE;values_json jsonb;keys_json jsonb;result_json jsonb;
BEGIN
 IF jsonb_typeof(operation) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'explicit operation value projection required' USING ERRCODE='22023';END IF;
 IF octet_length(operation::text)>1048576 OR coalesce(octet_length(prior_props::text),0)+coalesce(octet_length(prior_retained::text),0)>1048576 THEN
  RAISE EXCEPTION 'bounded value simulation input required' USING ERRCODE='54000';END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.type_def t WHERE t.type_id=selected_type AND t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL) THEN
  RAISE EXCEPTION 'current admitted Record required' USING ERRCODE='22023';END IF;
 IF operation->>'operation'='create_object' THEN
  IF prior_props IS NOT NULL OR prior_retained IS NOT NULL THEN RAISE EXCEPTION 'create has no prior image' USING ERRCODE='22023';END IF;
  authored:=operation->'values';removed:='[]';props:='{}';retained:='{}';
 ELSIF operation->>'operation'='update_object' THEN
  IF jsonb_typeof(prior_props) IS DISTINCT FROM 'object' OR (prior_retained IS NOT NULL AND jsonb_typeof(prior_retained) IS DISTINCT FROM 'object') THEN
   RAISE EXCEPTION 'complete simulated prior values required' USING ERRCODE='22023';END IF;
  authored:=operation->'set';removed:=operation->'unset';props:=prior_props;retained:=coalesce(prior_retained,'{}');
 ELSE RAISE EXCEPTION 'create or update value simulation required' USING ERRCODE='22023';END IF;
 IF jsonb_typeof(authored) IS DISTINCT FROM 'array' OR jsonb_typeof(removed) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'explicit authored arrays required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(authored)>1024 OR jsonb_array_length(removed)>1024 THEN RAISE EXCEPTION 'bounded authored values required' USING ERRCODE='54000';END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(authored) v WHERE v.value-ARRAY['name','value']<>'{}'::jsonb
   OR jsonb_typeof(v.value->'name') IS DISTINCT FROM 'string' OR octet_length(v.value->>'name') NOT BETWEEN 1 AND 4096
   OR truss.valid_flat_cell(v.value->'value') IS NOT TRUE)
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(removed) v WHERE jsonb_typeof(v.value) IS DISTINCT FROM 'string' OR octet_length(v.value#>>'{}') NOT BETWEEN 1 AND 4096)
  OR jsonb_array_length(authored)<>(SELECT count(DISTINCT v.value->>'name') FROM jsonb_array_elements(authored) v)
  OR jsonb_array_length(removed)<>(SELECT count(DISTINCT v.value) FROM jsonb_array_elements(removed) v)
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(authored) a JOIN jsonb_array_elements(removed) r ON a.value->>'name'=r.value#>>'{}') THEN
  RAISE EXCEPTION 'unique disjoint exact authored values required' USING ERRCODE='22023';END IF;
 -- Refuse unknown physical cells rather than silently dropping them while planning.
 IF EXISTS(SELECT 1 FROM jsonb_object_keys(props) k WHERE NOT EXISTS(
   SELECT 1 FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND p.prop_id::text=k))
  OR EXISTS(SELECT 1 FROM jsonb_each(retained) e WHERE truss.valid_flat_cell(e.value) IS NOT TRUE) THEN
  RAISE EXCEPTION 'supported complete prior value representation required' USING ERRCODE='0A000';END IF;
 SELECT coalesce(array_agg(p.prop_id::text) FILTER(WHERE p.prop_id IS NOT NULL),'{}'::text[]),
  coalesce(array_agg(u.name) FILTER(WHERE p.prop_id IS NULL),'{}'::text[])
 INTO removed_props,removed_retained
 FROM jsonb_array_elements_text(removed) u(name)
 LEFT JOIN truss.prop_def p ON p.type_id=selected_type AND p.retired_rev IS NULL AND p.name=u.name;
 props:=props-removed_props;retained:=retained-removed_retained;
 SELECT coalesce(jsonb_object_agg(p.prop_id::text,truss.canonical_flat_cell(a.value->'value')) FILTER(WHERE p.prop_id IS NOT NULL),'{}'::jsonb),
  coalesce(jsonb_object_agg(a.value->>'name',truss.canonical_flat_cell(a.value->'value')) FILTER(WHERE p.prop_id IS NULL),'{}'::jsonb)
 INTO set_props,set_retained
 FROM jsonb_array_elements(authored) a(value)
 LEFT JOIN truss.prop_def p ON p.type_id=selected_type AND p.retired_rev IS NULL AND p.name=a.value->>'name';
 props:=props||set_props;retained:=retained||set_retained;
 FOR property IN SELECT p.* FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL LOOP
  IF truss.valid_property_definition(property) IS NOT TRUE THEN RAISE EXCEPTION 'supported exact property definition required' USING ERRCODE='0A000';END IF;
  IF NOT props ? property.prop_id::text THEN
   IF property.nullability='required' THEN RAISE EXCEPTION 'missing required value' USING ERRCODE='22023';END IF;
  ELSIF truss.valid_property_value(props->property.prop_id::text,property) IS NOT TRUE THEN
   RAISE EXCEPTION 'exact declared value required' USING ERRCODE='22023';END IF;
 END LOOP;
 IF octet_length(convert_to(jsonb_build_object('props',props,'retained',retained)::text,'UTF8'))>1048576 THEN
  RAISE EXCEPTION 'bounded complete object values required' USING ERRCODE='54000';END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('name',v.name,'value',v.value) ORDER BY v.name COLLATE "C"),'[]'::jsonb) INTO values_json FROM (
  SELECT p.name,props->p.prop_id::text AS value FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL AND props ? p.prop_id::text
  UNION ALL SELECT key,value FROM jsonb_each(retained)) v;
 SELECT coalesce(jsonb_agg(jsonb_build_object('keyNumber',k.key_num::text,'keyId',k.key_id,'names',
  (SELECT jsonb_agg(p.name ORDER BY i.ord) FROM unnest(k.prop_ids) WITH ORDINALITY i(prop_id,ord)
   JOIN truss.prop_def p ON p.type_id=k.type_id AND p.prop_id=i.prop_id)) ORDER BY k.key_num),'[]'::jsonb)
  INTO keys_json FROM truss.key_def k WHERE k.type_id=selected_type AND k.retired_rev IS NULL;
 result_json:=jsonb_build_object('props',props,'retained',retained,'values',values_json,'keys',keys_json);
 IF octet_length(convert_to(result_json::text,'UTF8'))>4194304 THEN RAISE EXCEPTION 'bounded complete value simulation result required' USING ERRCODE='54000';END IF;
 RETURN result_json;
END;
$$;
REVOKE ALL ON FUNCTION truss.owned_object_values(int,jsonb,jsonb,jsonb) FROM PUBLIC;

-- Ordered object-value simulation for the owned-group executor.
-- Uninstalled candidate. Caller supplies an admitted type and simulated prior image;
-- this function performs no graph write, allocation or authorization issuance.
CREATE FUNCTION truss.runtime_owned_object_value_delta(selected_type int,operation jsonb,prior_props jsonb,prior_retained jsonb,selected_id bigint) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE authored jsonb;removed jsonb;props jsonb;retained jsonb;removed_props text[];removed_retained text[];set_props jsonb;set_retained jsonb;
 property truss.prop_def%ROWTYPE;values_json jsonb;keys_json jsonb;result_json jsonb;validated_prior boolean;
BEGIN
 SELECT EXISTS(SELECT 1 FROM truss.object o
  JOIN truss.runtime_type_schema compiled ON compiled.rev=o.rev AND compiled.type_id=o.type_id
  WHERE o.id=selected_id AND o.type_id=selected_type AND o.rev=(SELECT rev FROM truss.schema_head WHERE id=1)
   AND o.props=prior_props AND o.retained IS NOT DISTINCT FROM prior_retained
   AND compiled.valid_properties)
 INTO validated_prior;
 IF NOT validated_prior THEN RETURN truss.owned_object_values(selected_type,operation,prior_props,prior_retained);END IF;
 IF jsonb_typeof(operation) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'explicit operation value projection required' USING ERRCODE='22023';END IF;
 IF octet_length(operation::text)>1048576 OR coalesce(octet_length(prior_props::text),0)+coalesce(octet_length(prior_retained::text),0)>1048576 THEN
  RAISE EXCEPTION 'bounded value simulation input required' USING ERRCODE='54000';END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.type_def t WHERE t.type_id=selected_type AND t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL) THEN
  RAISE EXCEPTION 'current admitted Record required' USING ERRCODE='22023';END IF;
 IF operation->>'operation'='create_object' THEN
  IF prior_props IS NOT NULL OR prior_retained IS NOT NULL THEN RAISE EXCEPTION 'create has no prior image' USING ERRCODE='22023';END IF;
  authored:=operation->'values';removed:='[]';props:='{}';retained:='{}';
 ELSIF operation->>'operation'='update_object' THEN
  IF jsonb_typeof(prior_props) IS DISTINCT FROM 'object' OR (prior_retained IS NOT NULL AND jsonb_typeof(prior_retained) IS DISTINCT FROM 'object') THEN
   RAISE EXCEPTION 'complete simulated prior values required' USING ERRCODE='22023';END IF;
  authored:=operation->'set';removed:=operation->'unset';props:=prior_props;retained:=coalesce(prior_retained,'{}');
 ELSE RAISE EXCEPTION 'create or update value simulation required' USING ERRCODE='22023';END IF;
 IF jsonb_typeof(authored) IS DISTINCT FROM 'array' OR jsonb_typeof(removed) IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'explicit authored arrays required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(authored)>1024 OR jsonb_array_length(removed)>1024 THEN RAISE EXCEPTION 'bounded authored values required' USING ERRCODE='54000';END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(authored) v WHERE v.value-ARRAY['name','value']<>'{}'::jsonb
   OR jsonb_typeof(v.value->'name') IS DISTINCT FROM 'string' OR octet_length(v.value->>'name') NOT BETWEEN 1 AND 4096
   OR truss.valid_flat_cell(v.value->'value') IS NOT TRUE)
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(removed) v WHERE jsonb_typeof(v.value) IS DISTINCT FROM 'string' OR octet_length(v.value#>>'{}') NOT BETWEEN 1 AND 4096)
  OR jsonb_array_length(authored)<>(SELECT count(DISTINCT v.value->>'name') FROM jsonb_array_elements(authored) v)
  OR jsonb_array_length(removed)<>(SELECT count(DISTINCT v.value) FROM jsonb_array_elements(removed) v)
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(authored) a JOIN jsonb_array_elements(removed) r ON a.value->>'name'=r.value#>>'{}') THEN
  RAISE EXCEPTION 'unique disjoint exact authored values required' USING ERRCODE='22023';END IF;
 SELECT coalesce(array_agg(p.prop_id::text) FILTER(WHERE p.prop_id IS NOT NULL),'{}'::text[]),
  coalesce(array_agg(u.name) FILTER(WHERE p.prop_id IS NULL),'{}'::text[])
 INTO removed_props,removed_retained
 FROM jsonb_array_elements_text(removed) u(name)
 LEFT JOIN truss.prop_def p ON p.type_id=selected_type AND p.retired_rev IS NULL AND p.name=u.name;
 props:=props-removed_props;retained:=retained-removed_retained;
 SELECT coalesce(jsonb_object_agg(p.prop_id::text,truss.canonical_flat_cell(a.value->'value')) FILTER(WHERE p.prop_id IS NOT NULL),'{}'::jsonb),
  coalesce(jsonb_object_agg(a.value->>'name',truss.canonical_flat_cell(a.value->'value')) FILTER(WHERE p.prop_id IS NULL),'{}'::jsonb)
 INTO set_props,set_retained
 FROM jsonb_array_elements(authored) a(value)
 LEFT JOIN truss.prop_def p ON p.type_id=selected_type AND p.retired_rev IS NULL AND p.name=a.value->>'name';
 props:=props||set_props;retained:=retained||set_retained;
 FOR property IN SELECT p.* FROM truss.prop_def p WHERE p.type_id=selected_type AND p.retired_rev IS NULL
  AND p.name IN (SELECT value->>'name' FROM jsonb_array_elements(authored) UNION SELECT value#>>'{}' FROM jsonb_array_elements(removed)) LOOP
  IF truss.valid_property_definition(property) IS NOT TRUE THEN RAISE EXCEPTION 'supported exact property definition required' USING ERRCODE='0A000';END IF;
  IF NOT props ? property.prop_id::text THEN
   IF property.nullability='required' THEN RAISE EXCEPTION 'missing required value' USING ERRCODE='22023';END IF;
  ELSIF truss.valid_property_value(props->property.prop_id::text,property) IS NOT TRUE THEN
   RAISE EXCEPTION 'exact declared value required' USING ERRCODE='22023';END IF;
 END LOOP;
 IF octet_length(convert_to(jsonb_build_object('props',props,'retained',retained)::text,'UTF8'))>1048576 THEN
  RAISE EXCEPTION 'bounded complete object values required' USING ERRCODE='54000';END IF;
 result_json:=jsonb_build_object('props',props,'retained',retained);
 RETURN result_json;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_object_value_delta(int,jsonb,jsonb,jsonb,bigint) FROM PUBLIC;
