-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Candidate lineage codec, private component only; not a general canonical report encoder.
CREATE FUNCTION truss.runtime_lineage_quote(value text) RETURNS text
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result text := '"'; ch text; point int; i int;
BEGIN
 IF value IS NULL OR octet_length(value) NOT BETWEEN 1 AND 65536 THEN
  RAISE EXCEPTION 'bounded original identity required' USING ERRCODE='22023';
 END IF;
 FOR i IN 1..length(value) LOOP
  ch:=substr(value,i,1); point:=ascii(ch);
  IF point<32 THEN result:=result || chr(92) || 'u00' || lpad(to_hex(point),2,'0');
  ELSIF ch='"' OR ch=chr(92) THEN result:=result || chr(92) || ch;
  ELSE result:=result || ch; END IF;
 END LOOP;
 RETURN result || '"';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_lineage_quote(text) FROM PUBLIC;
CREATE FUNCTION truss.runtime_lineage_bytes(category text, document_id text, module_id text, element_id text)
RETURNS bytea LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE d text:=truss.runtime_lineage_quote(document_id); m text:=truss.runtime_lineage_quote(module_id);
 e text:=truss.runtime_lineage_quote(element_id); payload text; profile text;
BEGIN
 IF category='record' THEN
  profile:='truss-type-lineage/0.1.0'; payload:='['||d||','||m||','||e||']';
 ELSIF category='authored' THEN
  profile:='truss-relationship-lineage-bytes/0.1.0';
  payload:='{"category":"authored","relationship":{"document":'||d||',"element":'||e||',"module":'||m||'}}';
 ELSE RAISE EXCEPTION 'unsupported lineage category' USING ERRCODE='22023'; END IF;
 RETURN convert_to('truss-canonical/0.1.0'||chr(10)||profile||chr(10)||payload,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_lineage_bytes(text,text,text,text) FROM PUBLIC;
