CREATE FUNCTION truss.row_image_state_length_original(value truss.row_home_state) RETURNS bigint LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
BEGIN
 IF value IS NULL THEN RAISE EXCEPTION 'original typed row required' USING ERRCODE='22023';END IF;
 PERFORM truss.row_image_columns_original('state');
 RETURN truss.row_image_size_original('state',ARRAY[8,octet_length(value.owner_kind),CASE WHEN value.object_id IS NULL THEN NULL ELSE 8 END,
  CASE WHEN value.object_type_id IS NULL THEN NULL ELSE 4 END,CASE WHEN value.edge_id IS NULL THEN NULL ELSE 8 END,
  CASE WHEN value.relationship_type_id IS NULL THEN NULL ELSE 4 END,4,4,8,octet_length(value.definition_bytes),
  octet_length(value.home_profile_bytes),octet_length(value.value_profile_bytes),octet_length(value.source_bytes)]);
END;
$$; REVOKE ALL ON FUNCTION truss.row_image_state_length_original(truss.row_home_state) FROM public; CREATE FUNCTION truss.row_image_node_length_original(value truss.row_home_node) RETURNS bigint LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
BEGIN
 IF value IS NULL THEN RAISE EXCEPTION 'original typed row required' USING ERRCODE='22023';END IF;
 PERFORM truss.row_image_columns_original('node');
 RETURN truss.row_image_size_original('node',ARRAY[8,8,CASE WHEN value.parent_node_id IS NULL THEN NULL ELSE 8 END,octet_length(value.slot_kind),
  CASE WHEN value.sequence_ordinal IS NULL THEN NULL ELSE 8 END,octet_length(value.map_key),
  octet_length(value.record_field_identity_bytes),octet_length(value.value_kind),octet_length(value.definition_bytes),octet_length(value.source_bytes)]);
END;
$$; REVOKE ALL ON FUNCTION truss.row_image_node_length_original(truss.row_home_node) FROM public; CREATE FUNCTION truss.row_image_scalar_length_original(value truss.row_home_scalar) RETURNS bigint LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
BEGIN
 IF value IS NULL THEN RAISE EXCEPTION 'original typed row required' USING ERRCODE='22023';END IF;
 PERFORM truss.row_image_columns_original('scalar');
 RETURN truss.row_image_size_original('scalar',ARRAY[8,8,octet_length(value.scalar_kind),octet_length(value.text_value),
  CASE WHEN value.boolean_value IS NULL THEN NULL ELSE 1 END,octet_length(pg_catalog.numeric_send(value.numeric_value)),
  octet_length(value.numeric_token),octet_length(value.binary_value),octet_length(value.temporal_text),
  CASE WHEN value.temporal_instant IS NULL THEN NULL ELSE 8 END,octet_length(value.opaque_bytes),
  octet_length(value.codec_definition_bytes),octet_length(value.original_source_bytes)]);
END;
$$; REVOKE ALL ON FUNCTION truss.row_image_scalar_length_original(truss.row_home_scalar) FROM public; CREATE FUNCTION truss.runtime_capture_row_images_original(selected_state bigint, maximum_rows bigint, maximum_bytes bigint) RETURNS TABLE (image_kind text, original_image bytea) LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE count_rows bigint;expected_bytes bigint;observed_rows bigint:=0;observed_bytes bigint:=0; item record;
BEGIN
 IF selected_state IS NULL OR selected_state<=0 OR maximum_rows IS NULL OR maximum_rows<0 OR maximum_bytes IS NULL OR maximum_bytes<0 THEN
  RAISE EXCEPTION 'original selected image bounds required' USING ERRCODE='22023';END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.row_home_state s WHERE s.state_id=selected_state) THEN
  RAISE EXCEPTION 'original selected state unavailable' USING ERRCODE='55000';END IF;
 SELECT sum(n) INTO count_rows FROM (
  SELECT count(*) n FROM truss.row_home_state s WHERE s.state_id=selected_state UNION ALL
  SELECT count(*) FROM truss.row_home_node n WHERE n.state_id=selected_state UNION ALL
  SELECT count(*) FROM truss.row_home_scalar v WHERE v.state_id=selected_state) q;
 IF count_rows>maximum_rows THEN RAISE EXCEPTION 'original image row allowance exceeded' USING ERRCODE='54000';END IF;
 -- Numeric cell size still serializes one numeric cell; not whole resource qualification.
 SELECT sum(bytes) INTO expected_bytes FROM (
  SELECT truss.row_image_state_length_original(s) bytes FROM truss.row_home_state s WHERE s.state_id=selected_state UNION ALL
  SELECT truss.row_image_node_length_original(n) FROM truss.row_home_node n WHERE n.state_id=selected_state UNION ALL
  SELECT truss.row_image_scalar_length_original(v) FROM truss.row_home_scalar v WHERE v.state_id=selected_state) q;
 IF expected_bytes>maximum_bytes THEN RAISE EXCEPTION 'original image byte allowance exceeded' USING ERRCODE='54000';END IF;
 FOR item IN SELECT 'state'::text kind,truss.row_image_state_original(s) image FROM truss.row_home_state s WHERE s.state_id=selected_state UNION ALL
  SELECT 'node',truss.row_image_node_original(n) FROM truss.row_home_node n WHERE n.state_id=selected_state UNION ALL
  SELECT 'scalar',truss.row_image_scalar_original(v) FROM truss.row_home_scalar v WHERE v.state_id=selected_state LOOP
  observed_rows:=observed_rows+1;
  IF observed_rows>count_rows OR octet_length(item.image)>expected_bytes-observed_bytes THEN RAISE EXCEPTION 'original image capture changed' USING ERRCODE='55000';END IF;
  observed_bytes:=observed_bytes+octet_length(item.image);
  image_kind:=item.kind;original_image:=item.image;RETURN NEXT;
 END LOOP;
 IF observed_rows<>count_rows OR observed_bytes<>expected_bytes THEN RAISE EXCEPTION 'original complete image capture changed' USING ERRCODE='55000';END IF;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_capture_row_images_original(bigint, bigint, bigint) FROM public