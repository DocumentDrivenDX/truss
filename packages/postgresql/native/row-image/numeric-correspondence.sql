-- Selected JSON-token numeric row-image component; no codec/facet authority.
CREATE FUNCTION truss.row_image_numeric_correspondence_original(original_image bytea) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE cells bytea[]; family text COLLATE pg_catalog."C"; i int; native_value record;
BEGIN
 cells:=truss.row_touch_image_cells_original('scalar',original_image);
 family:=convert_from(cells[3],'UTF8');
 IF truss.row_touch_integer_original(cells[1])<=0 OR truss.row_touch_integer_original(cells[2])<=0
  OR family NOT IN ('integer','decimal') OR cells[6] IS NULL OR cells[7] IS NULL
  OR octet_length(cells[7])=0 OR octet_length(cells[12])=0 OR octet_length(cells[13])=0 THEN
  RAISE EXCEPTION 'complete selected numeric row carrier required' USING ERRCODE='22023';END IF;
 FOR i IN 4..11 LOOP
  IF i NOT IN (6,7) AND cells[i] IS NOT NULL THEN
   RAISE EXCEPTION 'family-exclusive numeric row carriers required' USING ERRCODE='22023';END IF;
 END LOOP;
 SELECT * INTO STRICT native_value FROM truss.numeric_binary_witness_original(cells[6]);

 IF NOT truss.numeric_source_binary_equal_original(convert_from(cells[7],'UTF8'),cells[6]) THEN
  RAISE EXCEPTION 'exact source native numeric correspondence required' USING ERRCODE='22023';END IF;
 IF family='integer' AND native_value.digits COLLATE pg_catalog."C"<>'0' AND native_value.exponent<0 THEN
  RAISE EXCEPTION 'integral native integer value required' USING ERRCODE='22023';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_image_numeric_correspondence_original(bytea) FROM PUBLIC;
