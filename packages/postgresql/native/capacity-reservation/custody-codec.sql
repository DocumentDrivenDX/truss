-- Unadopted complete-row custody accounting codec, not storage/authority proof.
-- Original raw carriers remain unchanged. Physical tuple/index/WAL and native
-- work/allocator budgets require independent profile admission.
CREATE FUNCTION truss.custody_codec_columns_original(kind text)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE
  target regclass;
  expected_names text[];
  expected_types oid[];
  expected_required boolean[];
  names text[]; types oid[]; required boolean[]; modifiers integer[];
BEGIN
  IF current_setting('server_encoding') <> 'UTF8' THEN
    RAISE EXCEPTION 'original UTF8 custody image required' USING ERRCODE='55000';
  END IF;
  IF kind='operation' THEN
    target := 'truss.row_home_operation'::regclass;
    expected_names := ARRAY['original_writer_xid','operation_ordinal','operation_kind','phase',
      'effect_generation','readiness_generation','sealed_generation','application_generation',
      'original_context_bytes','original_definition_bytes','original_input_bytes','original_prestate_bytes',
      'admitted_candidate_bytes','effect_obligation_bytes','original_group_custody_bytes','application_result_bytes'];
    expected_types := ARRAY['xid8'::regtype::oid,'int8'::regtype::oid,'text'::regtype::oid,'text'::regtype::oid,
      'int8'::regtype::oid,'int8'::regtype::oid,'int8'::regtype::oid,'int8'::regtype::oid,
      'bytea'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid,
      'bytea'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid];
    expected_required := ARRAY[true,true,true,true,true,false,false,false,true,true,true,true,true,true,true,false];
  ELSIF kind='touch' THEN
    target := 'truss.row_home_touch'::regclass;
    expected_names := ARRAY['transaction_id','owner_kind','owner_id','owner_discriminator_id',
      'property_owner_type_id','property_id','dirty_generation','sealed_generation',
      'original_layout_bytes','original_home_bytes','original_owner_property_bytes','original_operation_bytes'];
    expected_types := ARRAY['xid8'::regtype::oid,'text'::regtype::oid,'int8'::regtype::oid,'int4'::regtype::oid,
      'int4'::regtype::oid,'int4'::regtype::oid,'int8'::regtype::oid,'int8'::regtype::oid,
      'bytea'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid,'bytea'::regtype::oid];
    expected_required := ARRAY[true,true,true,true,true,true,true,false,true,true,true,true];
  ELSE
    RAISE EXCEPTION 'original custody kind required' USING ERRCODE='22023';
  END IF;
  -- Include dropped/user columns: new, removed or replaced fields cannot vanish
  -- from accounting. This does not verify CHECKs/defaults/triggers/ACL/authority.
  SELECT array_agg(a.attname::text ORDER BY a.attnum),array_agg(a.atttypid ORDER BY a.attnum),
    array_agg(a.attnotnull ORDER BY a.attnum),array_agg(a.atttypmod ORDER BY a.attnum)
  INTO names,types,required,modifiers FROM pg_attribute a WHERE a.attrelid=target AND a.attnum>0;
  IF names IS DISTINCT FROM expected_names OR types IS DISTINCT FROM expected_types
    OR required IS DISTINCT FROM expected_required
    OR modifiers IS DISTINCT FROM array_fill(-1,ARRAY[cardinality(expected_names)]) THEN
    RAISE EXCEPTION 'original complete custody column profile required' USING ERRCODE='55000';
  END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.custody_codec_columns_original(text) FROM PUBLIC;

CREATE FUNCTION truss.custody_frame_original(kind text, cells bytea[])
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE
  expected_count integer;
  prefix bytea;
  item bytea;
  total bigint;
  result bytea;
BEGIN
  IF kind='operation' THEN expected_count:=16;
  ELSIF kind='touch' THEN expected_count:=12;
  ELSE RAISE EXCEPTION 'original custody kind required' USING ERRCODE='22023'; END IF;
  IF cells IS NULL OR array_ndims(cells) IS DISTINCT FROM 1
    OR array_lower(cells,1) IS DISTINCT FROM 1 OR cardinality(cells)<>expected_count THEN
    RAISE EXCEPTION 'complete ordered custody cells required' USING ERRCODE='22023';
  END IF;
  prefix:=convert_to('truss.custody.'||kind||'/0.1','UTF8')||decode('00','hex')||int2send(expected_count::smallint);
  total:=octet_length(prefix);
  FOREACH item IN ARRAY cells LOOP
    total:=total+9+coalesce(octet_length(item),0)::bigint;
    IF total>8388608 THEN RAISE EXCEPTION 'complete custody row bound' USING ERRCODE='54000'; END IF;
  END LOOP;
  -- Complete size preflight precedes frame construction. This bounds output,
  -- not native composite argument materialization or repeated copy work.
  result:=prefix;
  FOREACH item IN ARRAY cells LOOP
    IF item IS NULL THEN result:=result||decode('00','hex')||int8send(0);
    ELSE result:=result||decode('01','hex')||int8send(octet_length(item)::bigint)||item; END IF;
  END LOOP;
  RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.custody_frame_original(text,bytea[]) FROM PUBLIC;

CREATE FUNCTION truss.custody_operation_original(value truss.row_home_operation)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
BEGIN
  IF value IS NULL THEN RAISE EXCEPTION 'original operation row required' USING ERRCODE='22023'; END IF;
  PERFORM truss.custody_codec_columns_original('operation');
  RETURN truss.custody_frame_original('operation',ARRAY[
    convert_to(value.original_writer_xid::text,'UTF8'),convert_to(value.operation_ordinal::text,'UTF8'),
    convert_to(value.operation_kind,'UTF8'),convert_to(value.phase,'UTF8'),
    convert_to(value.effect_generation::text,'UTF8'),convert_to(value.readiness_generation::text,'UTF8'),
    convert_to(value.sealed_generation::text,'UTF8'),convert_to(value.application_generation::text,'UTF8'),
    value.original_context_bytes,value.original_definition_bytes,value.original_input_bytes,value.original_prestate_bytes,
    value.admitted_candidate_bytes,value.effect_obligation_bytes,value.original_group_custody_bytes,value.application_result_bytes]);
END;
$$;
REVOKE ALL ON FUNCTION truss.custody_operation_original(truss.row_home_operation) FROM PUBLIC;

CREATE FUNCTION truss.custody_touch_original(value truss.row_home_touch)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
BEGIN
  IF value IS NULL THEN RAISE EXCEPTION 'original touch row required' USING ERRCODE='22023'; END IF;
  PERFORM truss.custody_codec_columns_original('touch');
  RETURN truss.custody_frame_original('touch',ARRAY[
    convert_to(value.transaction_id::text,'UTF8'),convert_to(value.owner_kind,'UTF8'),
    convert_to(value.owner_id::text,'UTF8'),convert_to(value.owner_discriminator_id::text,'UTF8'),
    convert_to(value.property_owner_type_id::text,'UTF8'),convert_to(value.property_id::text,'UTF8'),
    convert_to(value.dirty_generation::text,'UTF8'),convert_to(value.sealed_generation::text,'UTF8'),
    value.original_layout_bytes,value.original_home_bytes,value.original_owner_property_bytes,value.original_operation_bytes]);
END;
$$;
REVOKE ALL ON FUNCTION truss.custody_touch_original(truss.row_home_touch) FROM PUBLIC;
