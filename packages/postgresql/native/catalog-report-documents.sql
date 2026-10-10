-- Private complete archive inventory; not complete report/input/provenance admission.
CREATE FUNCTION truss.runtime_collect_report_documents(original_revision int)
RETURNS TABLE(doc_id text,doc_revision text,content_sha256 text,ord text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; source truss.schema_doc%ROWTYPE;
 count_documents bigint; distinct_documents bigint; first_ordinal int; last_ordinal int;
 total_bytes bigint;
BEGIN
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
   AND o.phase<>'application_finalized' FOR UPDATE;
 IF op.operation_kind<>'catalog-acceptance' OR op.phase<>'admitted'
   OR original_revision IS NULL OR original_revision<=0 THEN
  RAISE EXCEPTION 'original positive catalog admission required' USING ERRCODE='55000';
 END IF;
 LOCK TABLE truss.schema_head IN EXCLUSIVE MODE;
 IF NOT EXISTS(SELECT 1 FROM truss.schema_rev r WHERE r.rev=original_revision) THEN
  RAISE EXCEPTION 'original revision archive required' USING ERRCODE='55000';
 END IF;
 SELECT count(*),count(DISTINCT d.doc_id COLLATE "C"),min(d.ord),max(d.ord),
  coalesce(sum(octet_length(d.document)::bigint),0)
 INTO count_documents,distinct_documents,first_ordinal,last_ordinal,total_bytes
 FROM truss.schema_doc d WHERE d.rev=original_revision;
 IF count_documents>512 OR total_bytes>4194304 THEN
  RAISE EXCEPTION 'report document archive capacity exceeded' USING ERRCODE='54000';
 END IF;
 IF count_documents=0 OR distinct_documents<>count_documents
  OR first_ordinal<>0 OR last_ordinal::bigint<>count_documents-1 THEN
  RAISE EXCEPTION 'complete unique ordered document archive required' USING ERRCODE='55000';
 END IF;
 -- Complete preflight precedes result emission; no caller-supplied document inventory.
 FOR source IN SELECT d.* FROM truss.schema_doc d
  WHERE d.rev=original_revision ORDER BY d.ord LOOP
  IF source.doc_id IS NULL OR octet_length(source.doc_id) NOT BETWEEN 1 AND 4096
   OR source.doc_revision IS NULL OR octet_length(source.doc_revision) NOT BETWEEN 1 AND 4096 THEN
   RAISE EXCEPTION 'bounded original report document metadata required' USING ERRCODE='55000';
  END IF;
  PERFORM truss.runtime_verify_catalog_document(original_revision,source.doc_id);
 END LOOP;
 RETURN QUERY SELECT d.doc_id,d.doc_revision,d.content_sha256,d.ord::text
  FROM truss.schema_doc d WHERE d.rev=original_revision ORDER BY d.ord;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_report_documents(int) FROM PUBLIC;
