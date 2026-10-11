-- PostgreSQL16 numeric_send candidate finite mathematical decoder.
-- Original producer/descriptor/facets/resources remain independently admitted.
CREATE FUNCTION truss.numeric_binary_witness_original(original bytea)
RETURNS TABLE(negative boolean,digits text,exponent bigint)
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE count_digits int; weight int; sign_code int; scale int; i int; value int;
 groups text[] COLLATE pg_catalog."C":=ARRAY[]::text[];
 coefficient text COLLATE pg_catalog."C"; normalized text COLLATE pg_catalog."C";
BEGIN
 IF original IS NULL OR octet_length(original) NOT BETWEEN 8 AND 32776 THEN
  RAISE EXCEPTION 'bounded original native numeric cell required' USING ERRCODE='22023';END IF;
 count_digits:=get_byte(original,0)*256+get_byte(original,1);
 weight:=get_byte(original,2)*256+get_byte(original,3);
 IF weight>=32768 THEN weight:=weight-65536;END IF;
 sign_code:=get_byte(original,4)*256+get_byte(original,5);
 scale:=get_byte(original,6)*256+get_byte(original,7);
 IF count_digits>16384 OR octet_length(original)<>8+2*count_digits
  OR sign_code NOT IN (0,16384) OR scale>16383 THEN
  RAISE EXCEPTION 'complete finite native numeric frame required' USING ERRCODE='22023';END IF;
 IF count_digits=0 THEN
  IF sign_code<>0 THEN RAISE EXCEPTION 'native positive zero profile required' USING ERRCODE='22023';END IF;
  negative:=false;digits:='0';exponent:=0;RETURN NEXT;RETURN;
 END IF;
 FOR i IN 0..count_digits-1 LOOP
  value:=get_byte(original,8+2*i)*256+get_byte(original,9+2*i);
  IF value>9999 OR (value=0 AND i IN (0,count_digits-1)) THEN
   RAISE EXCEPTION 'canonical native base10000 digits required' USING ERRCODE='22023';END IF;
  groups:=array_append(groups,lpad(value::text,4,'0'));
 END LOOP;
 coefficient:=ltrim(array_to_string(groups,''),'0');normalized:=rtrim(coefficient,'0');
 exponent:=4::bigint*(weight-count_digits+1)+(length(coefficient)-length(normalized));
 IF exponent< -scale THEN
  RAISE EXCEPTION 'native scale cannot hide significant digits' USING ERRCODE='22023';END IF;
 negative:=sign_code=16384;digits:=normalized;RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.numeric_binary_witness_original(bytea) FROM PUBLIC;

CREATE FUNCTION truss.numeric_source_binary_equal_original(source_token text,native_original bytea)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE source_value record; native_value record;
BEGIN
 SELECT * INTO STRICT source_value FROM truss.numeric_witness_original(source_token);
 SELECT * INTO STRICT native_value FROM truss.numeric_binary_witness_original(native_original);
 RETURN source_value.negative=native_value.negative
  AND source_value.digits COLLATE pg_catalog."C"=native_value.digits COLLATE pg_catalog."C"
  AND source_value.exponent=native_value.exponent;
END;
$$;
REVOKE ALL ON FUNCTION truss.numeric_source_binary_equal_original(text,bytea) FROM PUBLIC;
