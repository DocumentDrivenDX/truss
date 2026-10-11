-- Private original lexical slice helpers, not registered interpretation/authority.
CREATE FUNCTION truss.runtime_original_json_value_end(original bytea,start_position int)
RETURNS int LANGUAGE plpgsql IMMUTABLE STRICT SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE position int:=start_position; size int:=length(original); depth int:=0;
 quoted boolean:=false; escaped boolean:=false; token text;
BEGIN
 IF octet_length(original) NOT BETWEEN 1 AND 1048576 OR position<1 OR position>size THEN
  RAISE EXCEPTION 'bounded original JSON position required' USING ERRCODE='22023';
 END IF;
 WHILE position<=size LOOP
  token:=chr(get_byte(original,position-1));
  IF quoted THEN
   IF escaped THEN escaped:=false;
   ELSIF token=chr(92) THEN escaped:=true;
   ELSIF token='"' THEN quoted:=false; IF depth=0 THEN RETURN position+1; END IF;
   END IF;
  ELSIF token='"' THEN quoted:=true;
  ELSIF token IN ('{','[') THEN
   depth:=depth+1;
   IF depth>32 THEN RAISE EXCEPTION 'original JSON depth exceeded' USING ERRCODE='54000'; END IF;
  ELSIF token IN ('}',']') THEN
   IF depth=0 THEN RETURN position; END IF;
   depth:=depth-1; IF depth=0 THEN RETURN position+1; END IF;
  ELSIF depth=0 AND token IN (',',' ',chr(9),chr(10),chr(13)) THEN RETURN position;
  END IF;
  position:=position+1;
 END LOOP;
 IF quoted OR depth<>0 THEN RAISE EXCEPTION 'complete original JSON value required' USING ERRCODE='22023'; END IF;
 RETURN position;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_original_json_value_end(bytea,int) FROM PUBLIC;

-- Source-only, before pending effects: the existing complete core/source gate is
-- deliberately retained. Pending-aware inventory must be implemented separately.
CREATE FUNCTION truss.runtime_extract_original_association_mapping(original bytea,original_pointer text)
RETURNS bytea LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE position int:=1; finish int; member text;
 size int; wanted bigint; current_index bigint; start_mapping int; found_array boolean:=false;
BEGIN
 IF original_pointer IS NULL OR octet_length(original_pointer)>4096
  OR original_pointer !~ '^/mappings/(0|[1-9][0-9]{0,3})$' THEN
  RAISE EXCEPTION 'original mapping pointer required' USING ERRCODE='22023';
 END IF;
 wanted:=substr(original_pointer,11)::bigint;
 IF wanted>=4096 THEN RAISE EXCEPTION 'original mapping index exceeded' USING ERRCODE='54000'; END IF;
 size:=length(original);
 IF original IS NULL OR octet_length(original) NOT BETWEEN 1 AND 1048576 THEN
  RAISE EXCEPTION 'unique original mapping JSON required' USING ERRCODE='22023';
 END IF;
 WHILE position<=size LOOP
  EXIT WHEN chr(get_byte(original,position-1)) NOT IN (' ',chr(9),chr(10),chr(13));
  position:=position+1;
 END LOOP;
 IF position>size THEN RAISE EXCEPTION 'unique original mapping JSON required' USING ERRCODE='22023'; END IF;
 -- Whole original lexical depth is bounded before PostgreSQL JSON parsing.
 -- The root object counts as one container; quoted braces never count.
 BEGIN
  PERFORM truss.runtime_original_json_value_end(original,position);
 EXCEPTION WHEN SQLSTATE '22023' THEN
  RAISE EXCEPTION 'unique original mapping JSON required' USING ERRCODE='22023';
 END;
 IF NOT (convert_from(original,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
  RAISE EXCEPTION 'unique original mapping JSON required' USING ERRCODE='22023';
 END IF;
 position:=1;
 -- Scan original UTF-8 bytes rather than json/jsonb reserialization. JSON syntax
 -- and duplicate names (including escaped names) were independently checked.
 WHILE chr(get_byte(original,position-1)) IN (' ',chr(9),chr(10),chr(13)) LOOP position:=position+1; END LOOP;
 position:=position+1;
 WHILE position<=size LOOP
  WHILE chr(get_byte(original,position-1)) IN (' ',chr(9),chr(10),chr(13)) LOOP position:=position+1; END LOOP;
  IF chr(get_byte(original,position-1))='}' THEN EXIT; END IF;
  finish:=truss.runtime_original_json_value_end(original,position);
  member:=convert_from(substr(original,position,finish-position),'UTF8')::json #>> '{}';position:=finish;
  WHILE chr(get_byte(original,position-1)) IN (' ',chr(9),chr(10),chr(13)) LOOP position:=position+1; END LOOP;
  position:=position+1; -- validated colon
  WHILE chr(get_byte(original,position-1)) IN (' ',chr(9),chr(10),chr(13)) LOOP position:=position+1; END LOOP;
  IF member='mappings' THEN found_array:=true;EXIT; END IF;
  position:=truss.runtime_original_json_value_end(original,position);
  WHILE chr(get_byte(original,position-1)) IN (' ',chr(9),chr(10),chr(13)) LOOP position:=position+1; END LOOP;
  IF chr(get_byte(original,position-1))='}' THEN EXIT; END IF;
  position:=position+1; -- validated comma
 END LOOP;
 IF NOT found_array OR chr(get_byte(original,position-1))<>'[' THEN
  RAISE EXCEPTION 'original mapping array required' USING ERRCODE='22023';
 END IF;
 position:=position+1;current_index:=0;
 LOOP
  WHILE chr(get_byte(original,position-1)) IN (' ',chr(9),chr(10),chr(13)) LOOP position:=position+1; END LOOP;
  IF chr(get_byte(original,position-1))=']' THEN
   RAISE EXCEPTION 'original mapping index absent' USING ERRCODE='22023';
  END IF;
  start_mapping:=position;finish:=truss.runtime_original_json_value_end(original,position);
  IF current_index=wanted THEN
   IF chr(get_byte(original,start_mapping-1))<>'{' THEN
    RAISE EXCEPTION 'original mapping object required' USING ERRCODE='22023';
   END IF;
   RETURN substr(original,start_mapping,finish-start_mapping);
  END IF;
  current_index:=current_index+1;position:=finish;
  WHILE chr(get_byte(original,position-1)) IN (' ',chr(9),chr(10),chr(13)) LOOP position:=position+1; END LOOP;
  IF chr(get_byte(original,position-1))=']' THEN
   RAISE EXCEPTION 'original mapping index absent' USING ERRCODE='22023';
  END IF;
  position:=position+1;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_extract_original_association_mapping(bytea,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_collect_original_association_mapping(original_revision int,original_pointer text)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE observed record;
BEGIN
 SELECT * INTO STRICT observed FROM truss.runtime_collect_original_catalog_binding(original_revision);
 RETURN truss.runtime_extract_original_association_mapping(decode(observed.binding_hex,'hex'),original_pointer);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_original_association_mapping(int,text) FROM PUBLIC;
