-- Internal document persistence phase. No head/report/acceptance publication.
-- Caller must be the original protected acceptance producer; ordinary EXECUTE is revoked.
CREATE FUNCTION truss.runtime_stage_catalog_document(
  document_id text, document_revision text, umf_version text,
  original_document text, original_validation jsonb, original_origin jsonb
) RETURNS TABLE(provisional_revision text, document_sha256 text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  actual_xid xid8 := pg_current_xact_id_if_assigned();
  op truss.row_home_operation%ROWTYPE;
  revision bigint;
  digest text;
BEGIN
  IF actual_xid IS NULL THEN
    RAISE EXCEPTION 'original acceptance operation required' USING ERRCODE='55000';
  END IF;
  SELECT * INTO STRICT op FROM truss.row_home_operation AS o
    WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized' FOR UPDATE;
  IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted' THEN
    RAISE EXCEPTION 'original acceptance admission required' USING ERRCODE='55000';
  END IF;
  IF document_id IS NULL OR octet_length(document_id) NOT BETWEEN 1 AND 4096
      OR document_revision IS NULL OR octet_length(document_revision) NOT BETWEEN 1 AND 4096
      OR umf_version NOT IN ('0.7.0','0.8.0') OR umf_version IS NULL
      OR original_document IS NULL OR octet_length(original_document) NOT BETWEEN 1 AND 1048576
      OR original_validation IS NULL OR jsonb_typeof(original_validation)<>'object'
      OR original_origin IS NULL OR jsonb_typeof(original_origin)<>'object' THEN
    RAISE EXCEPTION 'original catalog artifact shape' USING ERRCODE='22023';
  END IF;
  -- Genesis and head transitions share this exclusion; current head alone does not allocate type/property IDs.
  LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
  SELECT coalesce(max(r.rev)::bigint,0)+1 INTO revision FROM truss.schema_rev AS r;
  IF revision>2147483647 THEN
    RAISE EXCEPTION 'catalog revision exhausted' USING ERRCODE='54000';
  END IF;
  digest := encode(sha256(convert_to(original_document,'UTF8')),'hex');
  INSERT INTO truss.schema_rev(rev,origin) VALUES(revision::int,original_origin);
  INSERT INTO truss.schema_doc(rev,ord,doc_id,doc_revision,umf_version,content_sha256,document,validation)
    VALUES(revision::int,0,document_id,document_revision,umf_version,digest,original_document,original_validation);
  RETURN QUERY SELECT revision::text,digest;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_catalog_document(text,text,text,text,jsonb,jsonb) FROM PUBLIC;
