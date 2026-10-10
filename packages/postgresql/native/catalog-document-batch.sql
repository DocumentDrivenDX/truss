-- Internal complete ordered document-set persistence. No acceptance/head publication.
CREATE FUNCTION truss.runtime_stage_catalog_documents(documents jsonb,original_origin jsonb)
RETURNS TABLE(provisional_revision text,document_count text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  op truss.row_home_operation%ROWTYPE;
  item jsonb;
  revision bigint;
  ordinal int:=0;
  total_bytes bigint:=0;
  distinct_ids bigint;
BEGIN
  SELECT * INTO STRICT op FROM truss.row_home_operation o
    WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase<>'application_finalized' FOR UPDATE;
  IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted'
      OR documents IS NULL OR jsonb_typeof(documents)<>'array'
      OR jsonb_array_length(documents) NOT BETWEEN 1 AND 512
      OR octet_length(documents::text)>4194304
      OR original_origin IS NULL OR jsonb_typeof(original_origin)<>'object' THEN
    RAISE EXCEPTION 'original document set admission required' USING ERRCODE='22023';
  END IF;
  FOR item IN SELECT value FROM jsonb_array_elements(documents) LOOP
    IF jsonb_typeof(item)<>'object' OR NOT item ?& ARRAY['documentId','revision','umfVersion','originalText','validation']
        OR (SELECT count(*) FROM jsonb_object_keys(item))<>5
        OR EXISTS(SELECT 1 FROM jsonb_each(item) e WHERE e.key IN ('documentId','revision','umfVersion','originalText') AND jsonb_typeof(e.value)<>'string')
        OR octet_length(item->>'documentId') NOT BETWEEN 1 AND 4096
        OR octet_length(item->>'revision') NOT BETWEEN 1 AND 4096
        OR item->>'umfVersion' NOT IN ('0.7.0','0.8.0')
        OR octet_length(item->>'originalText') NOT BETWEEN 1 AND 1048576
        OR jsonb_typeof(item->'validation')<>'object' THEN
      RAISE EXCEPTION 'original document set carrier' USING ERRCODE='22023';
    END IF;
    total_bytes:=total_bytes+octet_length(item->>'originalText');
  END LOOP;
  IF total_bytes>4194304 THEN RAISE EXCEPTION 'document set bytes exhausted' USING ERRCODE='54000'; END IF;
  SELECT count(DISTINCT value->>'documentId') INTO distinct_ids FROM jsonb_array_elements(documents);
  IF distinct_ids<>jsonb_array_length(documents) THEN RAISE EXCEPTION 'duplicate original document' USING ERRCODE='22023'; END IF;
  LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
  SELECT coalesce(max(r.rev)::bigint,0)+1 INTO revision FROM truss.schema_rev r;
  IF revision>2147483647 THEN RAISE EXCEPTION 'catalog revision exhausted' USING ERRCODE='54000'; END IF;
  INSERT INTO truss.schema_rev(rev,origin) VALUES(revision::int,original_origin);
  FOR item IN SELECT value FROM jsonb_array_elements(documents) LOOP
    INSERT INTO truss.schema_doc(rev,ord,doc_id,doc_revision,umf_version,content_sha256,document,validation)
    VALUES(revision::int,ordinal,item->>'documentId',item->>'revision',item->>'umfVersion',
      encode(sha256(convert_to(item->>'originalText','UTF8')),'hex'),item->>'originalText',item->'validation');
    ordinal:=ordinal+1;
  END LOOP;
  RETURN QUERY SELECT revision::text,ordinal::text;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_catalog_documents(jsonb,jsonb) FROM PUBLIC;
