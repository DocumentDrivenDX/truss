-- Private byte transport only; digests/canonical spelling do not issue custody.
CREATE FUNCTION truss.runtime_artifact_base64(original bytea) RETURNS text
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE native_text text; canonical text;
BEGIN
 IF original IS NULL THEN RAISE EXCEPTION 'original bytes required' USING ERRCODE='22023'; END IF;
 IF octet_length(original)>4194304 THEN RAISE EXCEPTION 'artifact byte capacity' USING ERRCODE='54000'; END IF;
 native_text:=pg_catalog.encode(original,'base64');
 -- Selected PostgreSQL native formatter inserts LF. Remove exactly that byte,
 -- then check the complete alphabet/padding grammar and full original parity.
 canonical:=pg_catalog.replace(native_text,chr(10),'');
 IF canonical !~ '^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$'
   OR pg_catalog.decode(canonical,'base64') IS DISTINCT FROM original THEN
  RAISE EXCEPTION 'native canonical artifact transport mismatch' USING ERRCODE='55000';
 END IF;
 RETURN canonical;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_artifact_base64(bytea) FROM PUBLIC;
CREATE FUNCTION truss.runtime_artifact_base64_decode(original text) RETURNS bytea
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE decoded bytea;
BEGIN
 IF original IS NULL THEN RAISE EXCEPTION 'original base64 required' USING ERRCODE='22023'; END IF;
 IF octet_length(original)>5592408 THEN RAISE EXCEPTION 'base64 input capacity' USING ERRCODE='54000'; END IF;
 IF original !~ '^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$' THEN
  RAISE EXCEPTION 'canonical base64 grammar required' USING ERRCODE='22023';
 END IF;
 decoded:=pg_catalog.decode(original,'base64');
 IF truss.runtime_artifact_base64(decoded) COLLATE "C"<>original COLLATE "C" THEN
  RAISE EXCEPTION 'canonical unused pad bits required' USING ERRCODE='22023';
 END IF;
 RETURN decoded;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_artifact_base64_decode(text) FROM PUBLIC;
CREATE FUNCTION truss.runtime_artifact_transport(original bytea)
RETURNS TABLE(bytes_base64 text,sha256 text)
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE digest bytea; encoded text;
BEGIN
 encoded:=truss.runtime_artifact_base64(original);digest:=pg_catalog.sha256(original);
 IF octet_length(digest)<>32 THEN RAISE EXCEPTION 'artifact digest domain required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT encoded,pg_catalog.encode(digest,'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_artifact_transport(bytea) FROM PUBLIC;
