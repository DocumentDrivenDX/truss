CREATE OR REPLACE FUNCTION truss.operation_address_decode_original(original bytea) RETURNS TABLE (installation text, writer_xid xid8, operation_ordinal bigint) LANGUAGE plpgsql VOLATILE PARALLEL unsafe CALLED ON NULL INPUT SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE
  parsed jsonb;
  i integer;
  original_installation text;
  writer_text text;
  ordinal_text text;
  native_writer xid8;
  native_ordinal bigint;
BEGIN
  IF original IS NULL OR octet_length(original) NOT BETWEEN 1 AND 8388608 THEN
    RAISE EXCEPTION 'original address byte domain required' USING ERRCODE='22023';
  END IF;
  IF getdatabaseencoding() <> 'UTF8' THEN
    RAISE EXCEPTION 'original UTF8 address profile required' USING ERRCODE='55000';
  END IF;
  BEGIN
    parsed := convert_from(original,'UTF8')::jsonb;
  EXCEPTION WHEN invalid_text_representation OR character_not_in_repertoire THEN
    RAISE EXCEPTION 'original address syntax refused' USING ERRCODE='22023';
  END;
  -- Objects, including duplicate-key objects, can never become accepted scalars.
  IF jsonb_typeof(parsed) IS DISTINCT FROM 'array' THEN
    RAISE EXCEPTION 'original address array required' USING ERRCODE='22023';
  END IF;
  IF jsonb_array_length(parsed) <> 4 THEN
    RAISE EXCEPTION 'original address arity required' USING ERRCODE='22023';
  END IF;
  FOR i IN 0..3 LOOP
    IF jsonb_typeof(parsed->i) IS DISTINCT FROM 'string' THEN
      RAISE EXCEPTION 'original address strings required' USING ERRCODE='22023';
    END IF;
  END LOOP;
  IF parsed->>0 <> 'truss-row-operation-address/0.1.0' OR parsed->>1 = '' THEN
    RAISE EXCEPTION 'original address domain required' USING ERRCODE='22023';
  END IF;
  original_installation := parsed->>1;
  writer_text := parsed->>2;
  ordinal_text := parsed->>3;
  IF writer_text !~ '^(0|[1-9][0-9]{0,19})$'
     OR ordinal_text !~ '^(0|[1-9][0-9]{0,18})$' THEN
    RAISE EXCEPTION 'original address integer spelling required' USING ERRCODE='22023';
  END IF;
  BEGIN
    native_writer := writer_text::xid8;
    native_ordinal := ordinal_text::bigint;
  EXCEPTION WHEN invalid_text_representation OR numeric_value_out_of_range THEN
    RAISE EXCEPTION 'original address integer domain refused' USING ERRCODE='22023';
  END;
  IF native_ordinal < 0 OR truss.operation_address_original(
       original_installation,native_writer,native_ordinal) <> original THEN
    RAISE EXCEPTION 'original address spelling mismatch' USING ERRCODE='22023';
  END IF;
  RETURN QUERY SELECT original_installation,native_writer,native_ordinal;
END;
$$; REVOKE ALL ON FUNCTION truss.operation_address_decode_original(bytea) FROM public