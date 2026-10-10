-- Candidate length-only custody accounting; no frame construction or transport.
-- Original column validator dependency must be installed and registered first.
CREATE FUNCTION truss.custody_size_original(kind text, lengths integer[])
RETURNS bigint LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE expected_count integer; item integer; total bigint;
BEGIN
  IF kind='operation' THEN expected_count:=16;
  ELSIF kind='touch' THEN expected_count:=12;
  ELSE RAISE EXCEPTION 'original custody kind required' USING ERRCODE='22023'; END IF;
  IF lengths IS NULL OR array_ndims(lengths) IS DISTINCT FROM 1
    OR array_lower(lengths,1) IS DISTINCT FROM 1 OR cardinality(lengths)<>expected_count THEN
    RAISE EXCEPTION 'complete ordered custody lengths required' USING ERRCODE='22023';
  END IF;
  total:=octet_length(convert_to('truss.custody.'||kind||'/0.1','UTF8'))+3;
  FOREACH item IN ARRAY lengths LOOP
    IF item<0 THEN RAISE EXCEPTION 'nonnegative original custody length required' USING ERRCODE='22023'; END IF;
    total:=total+9+coalesce(item,0)::bigint;
    IF total>8388608 THEN RAISE EXCEPTION 'complete custody row bound' USING ERRCODE='54000'; END IF;
  END LOOP;
  RETURN total;
END;
$$;
REVOKE ALL ON FUNCTION truss.custody_size_original(text,integer[]) FROM PUBLIC;

CREATE FUNCTION truss.custody_operation_size_original(value truss.row_home_operation)
RETURNS bigint LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
BEGIN
  IF value IS NULL THEN RAISE EXCEPTION 'original operation row required' USING ERRCODE='22023'; END IF;
  PERFORM truss.custody_codec_columns_original('operation');
  RETURN truss.custody_size_original('operation',ARRAY[
    octet_length(convert_to(value.original_writer_xid::text,'UTF8')),octet_length(convert_to(value.operation_ordinal::text,'UTF8')),
    octet_length(convert_to(value.operation_kind,'UTF8')),octet_length(convert_to(value.phase,'UTF8')),
    octet_length(convert_to(value.effect_generation::text,'UTF8')),octet_length(convert_to(value.readiness_generation::text,'UTF8')),
    octet_length(convert_to(value.sealed_generation::text,'UTF8')),octet_length(convert_to(value.application_generation::text,'UTF8')),
    octet_length(value.original_context_bytes),octet_length(value.original_definition_bytes),octet_length(value.original_input_bytes),octet_length(value.original_prestate_bytes),
    octet_length(value.admitted_candidate_bytes),octet_length(value.effect_obligation_bytes),octet_length(value.original_group_custody_bytes),octet_length(value.application_result_bytes)]);
END;
$$;
REVOKE ALL ON FUNCTION truss.custody_operation_size_original(truss.row_home_operation) FROM PUBLIC;

CREATE FUNCTION truss.custody_touch_size_original(value truss.row_home_touch)
RETURNS bigint LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
BEGIN
  IF value IS NULL THEN RAISE EXCEPTION 'original touch row required' USING ERRCODE='22023'; END IF;
  PERFORM truss.custody_codec_columns_original('touch');
  RETURN truss.custody_size_original('touch',ARRAY[
    octet_length(convert_to(value.transaction_id::text,'UTF8')),octet_length(convert_to(value.owner_kind,'UTF8')),
    octet_length(convert_to(value.owner_id::text,'UTF8')),octet_length(convert_to(value.owner_discriminator_id::text,'UTF8')),
    octet_length(convert_to(value.property_owner_type_id::text,'UTF8')),octet_length(convert_to(value.property_id::text,'UTF8')),
    octet_length(convert_to(value.dirty_generation::text,'UTF8')),octet_length(convert_to(value.sealed_generation::text,'UTF8')),
    octet_length(value.original_layout_bytes),octet_length(value.original_home_bytes),octet_length(value.original_owner_property_bytes),octet_length(value.original_operation_bytes)]);
END;
$$;
REVOKE ALL ON FUNCTION truss.custody_touch_size_original(truss.row_home_touch) FROM PUBLIC;
