-- Private archived-text integrity check, not producer/schema/support admission.
CREATE FUNCTION truss.runtime_verify_catalog_document(revision int,document_id text)
RETURNS void LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE source truss.schema_doc%ROWTYPE; source_count bigint;
BEGIN
 SELECT count(*) INTO source_count FROM truss.schema_doc d
  WHERE d.rev=revision AND d.doc_id COLLATE "C"=document_id COLLATE "C";
 IF source_count<>1 THEN
  RAISE EXCEPTION 'unique original document archive required' USING ERRCODE='55000';
 END IF;
 SELECT d.* INTO STRICT source FROM truss.schema_doc d
  WHERE d.rev=revision AND d.doc_id COLLATE "C"=document_id COLLATE "C";
 IF source.document IS NULL OR octet_length(source.document) NOT BETWEEN 1 AND 1048576 THEN
  RAISE EXCEPTION 'bounded original document archive required' USING ERRCODE='55000';
 END IF;
 IF source.content_sha256 IS NULL OR source.content_sha256 COLLATE "C"
   IS DISTINCT FROM encode(sha256(convert_to(source.document,'UTF8')),'hex') COLLATE "C" THEN
  RAISE EXCEPTION 'original document archive digest mismatch' USING ERRCODE='55000';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_verify_catalog_document(int,text) FROM PUBLIC;
