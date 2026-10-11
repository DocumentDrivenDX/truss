-- Fixed reference decimal(21,3) candidate, matching the pinned owner procedure.
-- Does not issue authored/native/resource/codec admission authority.
CREATE FUNCTION truss.reference_decimal_coefficient_original(token text) RETURNS text
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE parts text[] COLLATE pg_catalog."C"; fraction text COLLATE pg_catalog."C";
 digits text COLLATE pg_catalog."C"; exponent_text text COLLATE pg_catalog."C";
 shift numeric; cut int; kept int; coefficient text COLLATE pg_catalog."C";
BEGIN
 IF token IS NULL OR octet_length(token) NOT BETWEEN 1 AND 65536 THEN
  RAISE EXCEPTION 'bounded reference decimal token required' USING ERRCODE='22023';END IF;
 parts:=regexp_match(token COLLATE pg_catalog."C",'^(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$');
 IF parts IS NULL OR token COLLATE pg_catalog."C" ~ '[^0-9eE+.-]' THEN
  RAISE EXCEPTION 'complete reference JSON numeric grammar required' USING ERRCODE='22023';END IF;
 fraction:=coalesce(parts[3],'');digits:=ltrim(parts[2]||fraction,'0');
 -- Owner reference semantics: complete valid zero before nonzero exponent bound.
 IF digits='' THEN RETURN '0';END IF;
 exponent_text:=coalesce(parts[4],'0');
 IF length(exponent_text)>32 THEN
  RAISE EXCEPTION 'reference nonzero exponent subset exceeded' USING ERRCODE='54000';END IF;
 -- Exact bounded exponent counter only; no native cast of the original value.
 shift:=exponent_text::numeric-length(fraction)+3;
 IF shift<0 THEN
  IF -shift>length(digits) THEN RAISE EXCEPTION 'reference decimal rounding refused' USING ERRCODE='22023';END IF;
  cut:=(-shift)::int;kept:=length(digits)-cut;
  IF substring(digits FROM kept+1) COLLATE pg_catalog."C" ~ '[^0]' THEN
   RAISE EXCEPTION 'reference decimal rounding refused' USING ERRCODE='22023';END IF;
  coefficient:=substring(digits FROM 1 FOR kept);
 ELSE
  IF length(digits)+shift>21 THEN RAISE EXCEPTION 'reference decimal precision exceeded' USING ERRCODE='22023';END IF;
  coefficient:=digits||repeat('0',shift::int);
 END IF;
 IF length(coefficient)>21 THEN RAISE EXCEPTION 'reference decimal precision exceeded' USING ERRCODE='22023';END IF;
 IF coefficient='' THEN coefficient:='0';END IF;
 IF parts[1]='-' AND coefficient<>'0' THEN coefficient:='-'||coefficient;END IF;
 RETURN coefficient;
END;
$$;
REVOKE ALL ON FUNCTION truss.reference_decimal_coefficient_original(text) FROM PUBLIC;

CREATE FUNCTION truss.row_image_reference_decimal_original(original_image bytea) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE cells bytea[]; i int; coefficient text COLLATE pg_catalog."C";
BEGIN
 cells:=truss.row_touch_image_cells_original('scalar',original_image);
 IF truss.row_touch_integer_original(cells[1])<=0 OR truss.row_touch_integer_original(cells[2])<=0
  OR convert_from(cells[3],'UTF8') COLLATE pg_catalog."C"<>'decimal'
  OR cells[6] IS NULL OR cells[7] IS NULL
  OR cells[12] IS NULL OR cells[13] IS NULL
  OR octet_length(cells[12])=0 OR octet_length(cells[13])=0 THEN
  RAISE EXCEPTION 'complete original reference decimal carrier required' USING ERRCODE='22023';END IF;
 FOR i IN 4..11 LOOP
  IF i NOT IN (6,7) AND cells[i] IS NOT NULL THEN
   RAISE EXCEPTION 'exclusive reference decimal payload required' USING ERRCODE='22023';END IF;
 END LOOP;
 coefficient:=truss.reference_decimal_coefficient_original(convert_from(cells[7],'UTF8'));
 IF NOT truss.numeric_source_binary_equal_original(coefficient||'e-3',cells[6]) THEN
  RAISE EXCEPTION 'exact reference decimal native correspondence required' USING ERRCODE='22023';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_image_reference_decimal_original(bytea) FROM PUBLIC;
