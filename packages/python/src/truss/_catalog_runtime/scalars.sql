-- Exact scalar cells: lexical numbers/timestamps never pass through floats or
-- PostgreSQL's finite precision numeric/timestamp projections.
CREATE FUNCTION truss.valid_scalar_cell(cell jsonb,expected_family text DEFAULT NULL,allow_null boolean DEFAULT true) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE family text;token text;calendar date;offset_text text;
BEGIN
 IF cell IS NULL OR jsonb_typeof(cell)<>'object' THEN RETURN false;END IF;
 IF cell='{"kind":"null"}'::jsonb THEN RETURN allow_null;END IF;
 family:=cell->>'kind';
 IF expected_family IS NOT NULL AND family IS DISTINCT FROM expected_family THEN RETURN false;END IF;
 IF family='boolean' THEN RETURN jsonb_typeof(cell->'value')='boolean' AND cell=jsonb_build_object('kind',family,'value',cell->'value');END IF;
 IF family NOT IN ('string','integer','decimal','timestamp','binary') OR jsonb_typeof(cell->'text') IS DISTINCT FROM 'string'
  OR cell IS DISTINCT FROM jsonb_build_object('kind',family,'text',cell->'text') THEN RETURN false;END IF;
 token:=cell->>'text';
 IF octet_length(token)>1048576 THEN RETURN false;END IF;
 IF family='string' THEN RETURN true;
 ELSIF family='integer' THEN RETURN token ~ '^-?(0|[1-9][0-9]*)$';
 ELSIF family='decimal' THEN RETURN token ~ '^-?(0|[1-9][0-9]*)([.][0-9]+)?([eE][+-]?[0-9]+)?$';
 ELSIF family='binary' THEN
  IF token !~ '^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$' THEN RETURN false;END IF;
  RETURN replace(encode(decode(token,'base64'),'base64'),chr(10),'')=token;
 ELSIF family='timestamp' THEN
  IF token !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]+)?([Zz]|[+-][0-9]{2}:[0-9]{2})$'
   OR substring(token,1,4)::int=0 OR substring(token,12,2)::int>23 OR substring(token,15,2)::int>59 OR substring(token,18,2)::int>59 THEN RETURN false;END IF;
  calendar:=make_date(substring(token,1,4)::int,substring(token,6,2)::int,substring(token,9,2)::int);
  IF lower(right(token,1))<>'z' THEN
   offset_text:=right(token,6);
   IF substring(offset_text,2,2)::int>23 OR substring(offset_text,5,2)::int>59 THEN RETURN false;END IF;
  END IF;
  RETURN true;
 END IF;
 RETURN false;
EXCEPTION WHEN invalid_text_representation OR datetime_field_overflow OR invalid_parameter_value THEN RETURN false;
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_scalar_cell(jsonb,text,boolean) FROM PUBLIC;

CREATE FUNCTION truss.logical_scalar_cell(cell jsonb) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF truss.valid_scalar_cell(cell) IS NOT TRUE THEN RAISE EXCEPTION 'valid exact scalar cell required' USING ERRCODE='55000';END IF;
 IF cell->>'kind'='null' THEN RETURN 'null'::jsonb;
 ELSIF cell->>'kind'='string' THEN RETURN cell->'text';
 ELSIF cell->>'kind'='boolean' THEN RETURN cell->'value';
 ELSE RETURN cell;END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.logical_scalar_cell(jsonb) FROM PUBLIC;

-- Selected signed64 refinement; preserve original lexical bytes without casts.
CREATE FUNCTION truss.valid_scalar_property(cell jsonb,family text,allow_null boolean,facets jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE token text;limit_text text;mantissa text;exponent_token text;coefficient text;fraction_length int;shift int;trailing_zero_count int;exponent_value int:=0;
BEGIN
 IF truss.valid_scalar_cell(cell,family,allow_null) IS NOT TRUE THEN RETURN false;END IF;
 IF facets IS NULL OR facets='{}'::jsonb THEN RETURN true;END IF;
 IF family='decimal' AND facets IN ('{"precision":18,"scale":4}'::jsonb,'{"precision":18,"scale":2}'::jsonb) THEN
  IF cell='{"kind":"null"}'::jsonb THEN RETURN allow_null;END IF;
  token:=cell->>'text';mantissa:=split_part(lower(token),'e',1);
  fraction_length:=length(split_part(mantissa,'.',2));
  coefficient:=ltrim(replace(ltrim(mantissa,'-'),'.',''),'0');
  IF coefficient='' THEN RETURN true;END IF;
  exponent_token:=split_part(lower(token),'e',2);
  IF exponent_token<>'' THEN
   limit_text:=left(exponent_token,1);exponent_token:=ltrim(ltrim(exponent_token,'+-'),'0');
   IF length(exponent_token)>7 THEN RETURN false;END IF;
   exponent_value:=CASE WHEN exponent_token='' THEN 0 ELSE exponent_token::int END;
   IF limit_text='-' THEN exponent_value:=-exponent_value;END IF;
  END IF;
  shift:=(facets->>'scale')::int-fraction_length+exponent_value;
  trailing_zero_count:=length(coefficient)-length(rtrim(coefficient,'0'));
  -- Exact fixed-scale coefficient: no numeric typmod, casts or rounding.
  IF shift<0 AND -shift>trailing_zero_count THEN RETURN false;END IF;
  RETURN length(coefficient)+shift<=18;
 END IF;
 IF family IS DISTINCT FROM 'integer' OR facets IS DISTINCT FROM '{"integerWidth":{"bits":64,"signed":true}}'::jsonb THEN RETURN false;END IF;
 IF cell='{"kind":"null"}'::jsonb THEN RETURN allow_null;END IF;
 token:=cell->>'text';limit_text:='9223372036854775807';
 IF left(token,1)='-' THEN token:=substring(token,2);limit_text:='9223372036854775808';END IF;
 RETURN length(token)<19 OR (length(token)=19 AND token COLLATE pg_catalog."C"<=limit_text COLLATE pg_catalog."C");
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_scalar_property(jsonb,text,boolean,jsonb) FROM PUBLIC;
