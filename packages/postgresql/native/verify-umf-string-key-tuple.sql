-- Private PostgreSQL implementation of UMF CONTRACT-040's UMFK1 string grammar.
-- The protected writer supplies values from actual rows in authored key order.
-- Qualified document/type/Key namespace checks belong to that writer.
CREATE FUNCTION truss.verify_umf_string_key_tuple(tuple_bytes bytea,actual_values text[]) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE SET search_path=pg_catalog,pg_temp AS $$
DECLARE position int:=5;total int;component_count int;value_count int;
 number bigint;multiplier bigint;digit int;octet int;prefix_count int;
 field_value text;payload bytea;expected_length int;
BEGIN
 IF tuple_bytes IS NULL OR actual_values IS NULL OR array_ndims(actual_values) IS DISTINCT FROM 1
  OR array_lower(actual_values,1) IS DISTINCT FROM 1 THEN RETURN false; END IF;
 total:=octet_length(tuple_bytes);value_count:=cardinality(actual_values);
 IF total NOT BETWEEN 7 AND 1048576 OR value_count NOT BETWEEN 1 AND 1024
  OR substring(tuple_bytes FROM 1 FOR 5)<>convert_to('UMFK1','UTF8') THEN RETURN false; END IF;
 number:=0;multiplier:=1;prefix_count:=0;
 LOOP
  IF position>=total OR prefix_count>=3 THEN RETURN false; END IF;
  octet:=get_byte(tuple_bytes,position);position:=position+1;prefix_count:=prefix_count+1;
  digit:=octet & 127;number:=number+digit*multiplier;
  IF number>1024 THEN RETURN false; END IF;
  IF octet<128 THEN
   IF prefix_count>1 AND digit=0 THEN RETURN false; END IF;
   EXIT;
  END IF;
  multiplier:=multiplier*128;
 END LOOP;
 component_count:=number::int;
 IF component_count<>value_count THEN RETURN false; END IF;
 FOREACH field_value IN ARRAY actual_values LOOP
  IF field_value IS NULL OR octet_length(field_value)>1048576 OR position>=total OR get_byte(tuple_bytes,position)<>4 THEN RETURN false; END IF;
  position:=position+1;number:=0;multiplier:=1;prefix_count:=0;
  LOOP
   IF position>=total OR prefix_count>=3 THEN RETURN false; END IF;
   octet:=get_byte(tuple_bytes,position);position:=position+1;prefix_count:=prefix_count+1;
   digit:=octet & 127;number:=number+digit*multiplier;
   IF number>1048576 THEN RETURN false; END IF;
   IF octet<128 THEN
    IF prefix_count>1 AND digit=0 THEN RETURN false; END IF;
    EXIT;
   END IF;
   multiplier:=multiplier*128;
  END LOOP;
  payload:=convert_to(field_value,'UTF8');expected_length:=octet_length(payload);
  IF number<>expected_length OR number>total-position
   OR substring(tuple_bytes FROM position+1 FOR expected_length)<>payload THEN RETURN false; END IF;
  position:=position+expected_length;
 END LOOP;
 RETURN position=total;
END;
$$;
REVOKE ALL ON FUNCTION truss.verify_umf_string_key_tuple(bytea,text[]) FROM PUBLIC;
