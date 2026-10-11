-- Private NX02–NX05 mathematical component. Not source/facet/native admission.
-- Candidate JSON numeric grammar, bounded tokens and signed-bigint exponents.
CREATE FUNCTION truss.numeric_witness_original(token text)
RETURNS TABLE(negative boolean,digits text,exponent bigint)
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE parts text[] COLLATE pg_catalog."C"; fraction text COLLATE pg_catalog."C"; exponent_text text COLLATE pg_catalog."C"; parsed_exponent bigint;
 mantissa text COLLATE pg_catalog."C"; trimmed text COLLATE pg_catalog."C"; removed bigint;
BEGIN
 IF token IS NULL OR octet_length(token) NOT BETWEEN 1 AND 65536 THEN
  RAISE EXCEPTION 'bounded complete numeric token required' USING ERRCODE='22023';
 END IF;
 parts:=regexp_match(token COLLATE pg_catalog."C",'^(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$');
 IF parts IS NULL OR token COLLATE pg_catalog."C" ~ '[^0-9eE+.-]' THEN
  RAISE EXCEPTION 'complete candidate JSON numeric grammar required' USING ERRCODE='22023';
 END IF;
 fraction:=coalesce(parts[3],'');exponent_text:=coalesce(parts[4],'0');
 -- Parse the entire exponent before zero normalization. Leading zeros are legal
 -- exponent spelling; stripping them never skips grammar or token-byte bounds.
 exponent_text:=regexp_replace(exponent_text,'^([+-]?)0+','\1');
 IF exponent_text IN ('','+','-') THEN exponent_text:='0';END IF;
 IF length(exponent_text)>20 THEN
  RAISE EXCEPTION 'numeric exponent counter exhausted' USING ERRCODE='54000';
 END IF;
 BEGIN parsed_exponent:=exponent_text::bigint;
 EXCEPTION WHEN numeric_value_out_of_range THEN
  RAISE EXCEPTION 'numeric exponent counter exhausted' USING ERRCODE='54000';END;
 mantissa:=ltrim(parts[2]||fraction,'0');
 IF mantissa='' THEN
  negative:=false;digits:='0';exponent:=0;RETURN NEXT;RETURN;
 END IF;
 trimmed:=rtrim(mantissa,'0');removed:=length(mantissa)-length(trimmed);
 BEGIN exponent:=parsed_exponent+(removed-length(fraction)::bigint);
 EXCEPTION WHEN numeric_value_out_of_range THEN
  RAISE EXCEPTION 'normalized numeric exponent exhausted' USING ERRCODE='54000';END;
 negative:=parts[1]='-';digits:=trimmed;RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.numeric_witness_original(text) FROM PUBLIC;

CREATE FUNCTION truss.numeric_equal_original(left_token text,right_token text) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE left_value record; right_value record;
BEGIN
 SELECT * INTO STRICT left_value FROM truss.numeric_witness_original(left_token);
 SELECT * INTO STRICT right_value FROM truss.numeric_witness_original(right_token);
 RETURN left_value.negative=right_value.negative
  AND left_value.digits COLLATE pg_catalog."C"=right_value.digits COLLATE pg_catalog."C"
  AND left_value.exponent=right_value.exponent;
END;
$$;
REVOKE ALL ON FUNCTION truss.numeric_equal_original(text,text) FROM PUBLIC;
