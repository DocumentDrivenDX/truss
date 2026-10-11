-- Private administrative FV03 source extraction for the selected new catalog.
-- An obligation is required even with no graph rows and no feed registration.
-- This does not admit a report or issue a FeedRevisionFact/manifest/commit proof.
CREATE FUNCTION truss.runtime_collect_catalog_revision_obligation(
 expected_writer text,expected_ordinal text,expected_generation text,
 original_prestate jsonb,original_report bytea)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE revision int; verified jsonb; fresh jsonb; source_prestate jsonb;
 name text; op truss.row_home_operation%ROWTYPE;
 parent truss.schema_rev%ROWTYPE; input jsonb; doc truss.schema_doc%ROWTYPE;
 expected jsonb; documents jsonb:='[]'::jsonb; result jsonb;
BEGIN
 -- The revision comes from the original transition, never a feed row/key.
 IF original_prestate IS NULL OR original_prestate->>'revision' IS NULL
  OR original_prestate->>'revision' !~ '^[1-9][0-9]{0,9}$' THEN
  RAISE EXCEPTION 'original positive revision transition required' USING ERRCODE='55000';
 END IF;
 revision:=(original_prestate->>'revision')::int;
 fresh:=truss.runtime_capture_catalog_completion_physical(
  expected_writer,expected_ordinal,expected_generation,revision);
 -- Feed registration is not a source of required revision obligations. Keep
 -- every original descriptor and every other table image, while excluding the
 -- four downstream feed-store row images from this source-only comparison.
 -- The full completion verifier itself remains unchanged.
 source_prestate:=original_prestate;
 FOREACH name IN ARRAY ARRAY['feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite'] LOOP
  source_prestate:=jsonb_set(source_prestate,ARRAY['tables',name],fresh->'tables'->name);
 END LOOP;
 verified:=truss.runtime_verify_catalog_completion_physical(
  expected_writer,expected_ordinal,expected_generation,revision,source_prestate,original_report);
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned();
 PERFORM truss.runtime_require_catalog_input(op.original_input_bytes);
 input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 IF jsonb_typeof(input->'documents') IS DISTINCT FROM 'array'
  OR jsonb_array_length(input->'documents') NOT BETWEEN 1 AND 512
  OR (SELECT count(*) FROM truss.schema_doc d WHERE d.rev=revision)
      <>jsonb_array_length(input->'documents') THEN
  RAISE EXCEPTION 'complete revision source inventory required' USING ERRCODE='55000';
 END IF;
 SELECT r.* INTO STRICT parent FROM truss.schema_rev r WHERE r.rev=revision;
 FOR doc IN SELECT d.* FROM truss.schema_doc d WHERE d.rev=revision ORDER BY d.ord LOOP
  IF doc.ord<0 OR doc.ord>=jsonb_array_length(input->'documents') THEN
   RAISE EXCEPTION 'original document order required' USING ERRCODE='55000';
  END IF;
  expected:=input->'documents'->doc.ord;
  IF doc.doc_id IS DISTINCT FROM expected->>'documentId'
   OR doc.doc_revision IS DISTINCT FROM expected->>'documentRevision'
   OR doc.content_sha256 IS DISTINCT FROM expected->'artifact'->>'sha256'
   OR doc.content_sha256 IS DISTINCT FROM encode(sha256(convert_to(doc.document,'UTF8')),'hex')
   OR convert_to(doc.document,'UTF8') IS DISTINCT FROM decode(expected->'artifact'->>'bytesBase64','base64')
   OR doc.umf_version IS DISTINCT FROM (doc.document::jsonb)->>'umf' THEN
   RAISE EXCEPTION 'original revision document byte correspondence required' USING ERRCODE='55000';
  END IF;
  documents:=documents||jsonb_build_array(jsonb_build_object(
   'ordinal',doc.ord::text,'documentId',doc.doc_id,'documentRevision',doc.doc_revision,
   'umfVersion',doc.umf_version,'contentSha256',doc.content_sha256,
   'originalDocumentHex',encode(convert_to(doc.document,'UTF8'),'hex'),
   'nativeRecordHex',encode(record_send(doc),'hex')));
 END LOOP;
 result:=jsonb_build_object(
  'interfaceVersion','truss-catalog-revision-obligation/0.1',
  'scope','original_catalog_revision_required_fact_only',
  'writerXid',expected_writer,'operationOrdinal',expected_ordinal,
  'effectGeneration',expected_generation,'revision',revision::text,
  'priorHeadRevision',original_prestate->'head'->>'rev',
  'requiredFactKind','revision','requiredFactCount','1',
  'payload',jsonb_build_object('state','unavailable','reason','complete_report_issuer_missing'),
  'acceptedReportQualified',false,'feedFactQualified',false,
  'originalInputHex',encode(op.original_input_bytes,'hex'),
  'originalOperationRecordHex',encode(record_send(op),'hex'),
  'originalRevisionRecordHex',encode(record_send(parent),'hex'),
  'originalReportHex',encode(original_report,'hex'),
  'documents',documents);
 IF octet_length(result::text)>16777216 THEN
  RAISE EXCEPTION 'revision source retention bound exceeded' USING ERRCODE='54000';
 END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_catalog_revision_obligation(text,text,text,jsonb,bytea) FROM PUBLIC;
