CREATE FUNCTION truss.runtime_catalog_report_native_tree(value jsonb, depth int = 0) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE children jsonb:='[]'::jsonb; entry record; kind text;
BEGIN
 IF value IS NULL OR depth IS NULL OR depth<0 OR depth>128 THEN
  RAISE EXCEPTION 'bounded native report value required' USING ERRCODE='22023';
 END IF;
 kind:=jsonb_typeof(value);
 CASE kind
 WHEN 'null' THEN RETURN jsonb_build_object('kind','null');
 WHEN 'boolean' THEN RETURN jsonb_build_object('kind','boolean','value',value);
 WHEN 'string' THEN RETURN jsonb_build_object('kind','string','utf8Hex',encode(convert_to(value #>> '{}','UTF8'),'hex'));
 WHEN 'array' THEN
  IF jsonb_array_length(value)>4096 THEN RAISE EXCEPTION 'native report array capacity' USING ERRCODE='54000'; END IF;
  FOR entry IN SELECT x FROM jsonb_array_elements(value) x LOOP
   children:=children||jsonb_build_array(truss.runtime_catalog_report_native_tree(entry.x,depth+1));
  END LOOP;
  RETURN jsonb_build_object('kind','array','items',children);
 WHEN 'object' THEN
  IF (SELECT count(*) FROM jsonb_object_keys(value))>4096 THEN RAISE EXCEPTION 'native report object capacity' USING ERRCODE='54000'; END IF;
  FOR entry IN SELECT key,x FROM jsonb_each(value) e(key,x) LOOP
   children:=children||jsonb_build_array(jsonb_build_object('keyUtf8Hex',encode(convert_to(entry.key,'UTF8'),'hex'),
    'node',truss.runtime_catalog_report_native_tree(entry.x,depth+1)));
  END LOOP;
  RETURN jsonb_build_object('kind','object','members',children);
 ELSE RAISE EXCEPTION 'numeric-free native report value required' USING ERRCODE='22023';
 END CASE;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_catalog_report_native_tree(jsonb, int) FROM public