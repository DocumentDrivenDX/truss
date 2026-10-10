CREATE FUNCTION truss.row_image_columns_original(kind text) RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE target regclass; names text[]; types oid[]; required boolean[]; collations oid[];
 actual_names text[]; actual_types oid[]; actual_required boolean[]; actual_collations oid[];
 actual_modifiers int[]; dropped boolean[]; dimensions int[]; c oid:='pg_catalog."C"'::regcollation;
BEGIN
 IF current_setting('server_encoding')<>'UTF8' THEN RAISE EXCEPTION 'original UTF8 row image required' USING ERRCODE='55000';END IF;
 IF kind='state' THEN
  target:='truss.row_home_state'::regclass;
  names:=ARRAY['state_id','owner_kind','object_id','object_type_id','edge_id','relationship_type_id','property_owner_type_id','property_id','root_node_id','definition_bytes','home_profile_bytes','value_profile_bytes','source_bytes'];
  types:=ARRAY['int8'::regtype::oid,'text'::regtype::oid,'int8'::regtype::oid,'int4'::regtype::oid,'int8'::regtype::oid,'int4'::regtype::oid,'int4'::regtype::oid,'int4'::regtype::oid,'int8'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid];
  required:=ARRAY[true,true,false,false,false,false,true,true,true,true,true,true,true];
  collations:=ARRAY[0,c,0,0,0,0,0,0,0,0,0,0,0]::oid[];
 ELSIF kind='node' THEN
  target:='truss.row_home_node'::regclass;
  names:=ARRAY['state_id','node_id','parent_node_id','slot_kind','sequence_ordinal','map_key','record_field_identity_bytes','value_kind','definition_bytes','source_bytes'];
  types:=ARRAY['int8'::regtype::oid,'int8'::regtype::oid,'int8'::regtype::oid,'text'::regtype::oid,'int8'::regtype::oid,'text'::regtype::oid,'bytea'::regtype::oid,'text'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid];
  required:=ARRAY[true,true,false,true,false,false,false,true,true,true];
  collations:=ARRAY[0,0,0,c,0,c,0,c,0,0]::oid[];
 ELSIF kind='scalar' THEN
  target:='truss.row_home_scalar'::regclass;
  names:=ARRAY['state_id','node_id','scalar_kind','text_value','boolean_value','numeric_value','numeric_token','binary_value','temporal_text','temporal_instant','opaque_bytes','codec_definition_bytes','original_source_bytes'];
  types:=ARRAY['int8'::regtype::oid,'int8'::regtype::oid,'text'::regtype::oid,'text'::regtype::oid,'bool'::regtype::oid,'numeric'::regtype::oid,'text'::regtype::oid,'bytea'::regtype::oid,'text'::regtype::oid,'timestamptz'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid];
  required:=ARRAY[true,true,true,false,false,false,false,false,false,false,false,true,true];
  collations:=ARRAY[0,0,c,c,0,0,c,0,c,0,0,0,0]::oid[];
 ELSE RAISE EXCEPTION 'original row image kind required' USING ERRCODE='22023';END IF;
 SELECT array_agg(a.attname::text ORDER BY a.attnum),array_agg(a.atttypid ORDER BY a.attnum),
  array_agg(a.attnotnull ORDER BY a.attnum),array_agg(a.attcollation ORDER BY a.attnum),
  array_agg(a.atttypmod ORDER BY a.attnum),array_agg(a.attisdropped ORDER BY a.attnum),array_agg(a.attndims ORDER BY a.attnum)
 INTO actual_names,actual_types,actual_required,actual_collations,actual_modifiers,dropped,dimensions
 FROM pg_attribute a WHERE a.attrelid=target AND a.attnum>0;
 IF actual_names IS DISTINCT FROM names OR actual_types IS DISTINCT FROM types OR actual_required IS DISTINCT FROM required
  OR actual_collations IS DISTINCT FROM collations OR actual_modifiers IS DISTINCT FROM array_fill(-1,ARRAY[cardinality(names)])
  OR dropped IS DISTINCT FROM array_fill(false,ARRAY[cardinality(names)]) OR dimensions IS DISTINCT FROM array_fill(0,ARRAY[cardinality(names)])
  OR EXISTS(SELECT 1 FROM pg_inherits i WHERE i.inhrelid=target OR i.inhparent=target)
  OR (SELECT relkind FROM pg_class WHERE oid=target)<>'r' THEN
  RAISE EXCEPTION 'original complete row image column profile required' USING ERRCODE='55000';END IF;
END;
$$; REVOKE ALL ON FUNCTION truss.row_image_columns_original(text) FROM public; CREATE FUNCTION truss.row_image_size_original(kind text, lengths int[]) RETURNS bigint LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE count integer;item integer;total bigint;
BEGIN
 IF kind IN ('state','scalar') THEN count:=13;
 ELSIF kind='node' THEN count:=10;
 ELSE RAISE EXCEPTION 'original row image kind required' USING ERRCODE='22023';END IF;
 IF lengths IS NULL OR array_ndims(lengths) IS DISTINCT FROM 1 OR array_lower(lengths,1) IS DISTINCT FROM 1
  OR cardinality(lengths)<>count THEN RAISE EXCEPTION 'complete row image lengths required' USING ERRCODE='22023';END IF;
 -- Domain+NUL, field count, then OID and signed length for each field. NULL
 -- contributes its frame header but no payload, independently of empty bytes.
 total:=octet_length(convert_to('truss.row-image.'||kind||'/0.1','UTF8'))+5+8*count;
 FOREACH item IN ARRAY lengths LOOP
  IF item<0 THEN RAISE EXCEPTION 'nonnegative row image length required' USING ERRCODE='22023';END IF;
  IF coalesce(item,0)>8388608-total THEN RAISE EXCEPTION 'original row image output bound' USING ERRCODE='54000';END IF;
  total:=total+coalesce(item,0);
 END LOOP;
 RETURN total;
END;
$$; REVOKE ALL ON FUNCTION truss.row_image_size_original(text, int[]) FROM public; CREATE FUNCTION truss.row_image_state_original(value truss.row_home_state) RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE result bytea;expected bigint;
BEGIN
 IF value IS NULL THEN RAISE EXCEPTION 'original state image required' USING ERRCODE='22023';END IF;
 PERFORM truss.row_image_columns_original('state');
 expected:=truss.row_image_size_original('state',ARRAY[8,octet_length(value.owner_kind),CASE WHEN value.object_id IS NULL THEN NULL ELSE 8 END,
  CASE WHEN value.object_type_id IS NULL THEN NULL ELSE 4 END,CASE WHEN value.edge_id IS NULL THEN NULL ELSE 8 END,
  CASE WHEN value.relationship_type_id IS NULL THEN NULL ELSE 4 END,4,4,8,octet_length(value.definition_bytes),
  octet_length(value.home_profile_bytes),octet_length(value.value_profile_bytes),octet_length(value.source_bytes)]);
 result:=convert_to('truss.row-image.state/0.1','UTF8')||decode('00','hex')||pg_catalog.record_send(value);
 IF octet_length(result)<>expected THEN RAISE EXCEPTION 'original row image size mismatch' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$; REVOKE ALL ON FUNCTION truss.row_image_state_original(truss.row_home_state) FROM public; CREATE FUNCTION truss.row_image_node_original(value truss.row_home_node) RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE result bytea;expected bigint;
BEGIN
 IF value IS NULL THEN RAISE EXCEPTION 'original node image required' USING ERRCODE='22023';END IF;
 PERFORM truss.row_image_columns_original('node');
 expected:=truss.row_image_size_original('node',ARRAY[8,8,CASE WHEN value.parent_node_id IS NULL THEN NULL ELSE 8 END,octet_length(value.slot_kind),
  CASE WHEN value.sequence_ordinal IS NULL THEN NULL ELSE 8 END,octet_length(value.map_key),
  octet_length(value.record_field_identity_bytes),octet_length(value.value_kind),octet_length(value.definition_bytes),octet_length(value.source_bytes)]);
 result:=convert_to('truss.row-image.node/0.1','UTF8')||decode('00','hex')||pg_catalog.record_send(value);
 IF octet_length(result)<>expected THEN RAISE EXCEPTION 'original row image size mismatch' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$; REVOKE ALL ON FUNCTION truss.row_image_node_original(truss.row_home_node) FROM public; CREATE FUNCTION truss.row_image_scalar_original(value truss.row_home_scalar) RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE result bytea;expected bigint;
BEGIN
 IF value IS NULL THEN RAISE EXCEPTION 'original scalar image required' USING ERRCODE='22023';END IF;
 PERFORM truss.row_image_columns_original('scalar');
 expected:=truss.row_image_size_original('scalar',ARRAY[8,8,octet_length(value.scalar_kind),octet_length(value.text_value),
  CASE WHEN value.boolean_value IS NULL THEN NULL ELSE 1 END,octet_length(pg_catalog.numeric_send(value.numeric_value)),
  octet_length(value.numeric_token),octet_length(value.binary_value),octet_length(value.temporal_text),
  CASE WHEN value.temporal_instant IS NULL THEN NULL ELSE 8 END,octet_length(value.opaque_bytes),
  octet_length(value.codec_definition_bytes),octet_length(value.original_source_bytes)]);
 result:=convert_to('truss.row-image.scalar/0.1','UTF8')||decode('00','hex')||pg_catalog.record_send(value);
 IF octet_length(result)<>expected THEN RAISE EXCEPTION 'original row image size mismatch' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$; REVOKE ALL ON FUNCTION truss.row_image_scalar_original(truss.row_home_scalar) FROM public