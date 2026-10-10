-- Private candidate address encoder. Inputs do not authenticate installation/xid.
-- Complete installed owner/ACL/dependency/resource qualification remains required.
CREATE OR REPLACE FUNCTION truss.operation_address_original(
  installation text, writer_xid xid8, operation_ordinal bigint
) RETURNS bytea
LANGUAGE plpgsql VOLATILE PARALLEL UNSAFE CALLED ON NULL INPUT SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE
  domain_text constant text := 'truss-row-operation-address/0.1.0';
  ceiling constant bigint := 8388608;
  raw bytea;
  size bigint;
  byte_value integer;
  i integer;
  output bytea;
BEGIN
  IF installation IS NULL OR octet_length(installation) NOT BETWEEN 1 AND ceiling
     OR writer_xid IS NULL OR operation_ordinal IS NULL OR operation_ordinal < 0 THEN
    RAISE EXCEPTION 'original address input domain required' USING ERRCODE='22023';
  END IF;
  IF getdatabaseencoding() <> 'UTF8' THEN
    RAISE EXCEPTION 'original UTF8 address profile required' USING ERRCODE='55000';
  END IF;
  -- Four quoted strings, three commas, two brackets and exact ASCII integers.
  size := 13 + octet_length(domain_text) + octet_length(writer_xid::text)
          + octet_length(operation_ordinal::text) + octet_length(installation);
  IF size > ceiling THEN
    RAISE EXCEPTION 'original address byte bound' USING ERRCODE='54000';
  END IF;
  raw := convert_to(installation,'UTF8');
  -- Count only escape expansion; each original UTF8 byte is already charged.
  FOR i IN 0..octet_length(raw)-1 LOOP
    byte_value := get_byte(raw,i);
    IF byte_value IN (34,92,8,9,10,12,13) THEN
      size := size + 1;
    ELSIF byte_value < 32 THEN
      size := size + 5;
    END IF;
    IF size > ceiling THEN
      RAISE EXCEPTION 'original address byte bound' USING ERRCODE='54000';
    END IF;
  END LOOP;
  output := convert_to('[' || array_to_string(ARRAY[
    to_json(domain_text)::text,to_json(installation)::text,
    to_json(writer_xid::text)::text,to_json(operation_ordinal::text)::text],',') || ']','UTF8');
  IF octet_length(output) <> size THEN
    RAISE EXCEPTION 'original address encoder size mismatch' USING ERRCODE='55000';
  END IF;
  RETURN output;
END;
$$;
REVOKE ALL ON FUNCTION truss.operation_address_original(text,xid8,bigint) FROM PUBLIC;
