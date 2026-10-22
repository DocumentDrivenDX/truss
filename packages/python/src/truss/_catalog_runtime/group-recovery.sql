-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Receipt observation never executes a missing original request.
CREATE FUNCTION truss.runtime_authorize_retained_request(selected_receipt bigint) RETURNS uuid
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE receipt truss.request_receipt%ROWTYPE;writer jsonb;attempt truss.runtime_object_attempt%ROWTYPE;actor oid;owner record;
BEGIN
 actor:=truss.runtime_person(false);
 SELECT * INTO STRICT receipt FROM truss.request_receipt WHERE storage_row_id=selected_receipt;
 writer:=convert_from(receipt.original_writer_context_bytes,'UTF8')::jsonb;
 IF writer->>'profile' IS DISTINCT FROM 'truss-object-group-writer/0.1' THEN
  RAISE EXCEPTION 'retained request writer profile required' USING ERRCODE='0A000';END IF;
 SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=(writer->>'attemptId')::uuid;
 IF NOT attempt.complete OR attempt.actor_oid IS DISTINCT FROM actor
  OR attempt.receipt_id IS DISTINCT FROM receipt.storage_row_id
  OR attempt.writer_xid IS DISTINCT FROM receipt.original_writer_xid
  OR writer->>'xid' IS DISTINCT FROM attempt.writer_xid::text
  OR writer->>'actorOid' IS DISTINCT FROM attempt.actor_oid::text THEN
  RAISE EXCEPTION 'retained original request correspondence required' USING ERRCODE='55000';END IF;
 IF NOT truss.runtime_receipt_can_read(attempt.id) THEN
  RAISE EXCEPTION 'current retained request reader required' USING ERRCODE='P1403';END IF;
 FOR owner IN SELECT DISTINCT r.value->'identity'->'owner'->>'documentId' document_id,
  r.value->'identity'->'owner'->>'moduleId' module FROM jsonb_array_elements(attempt.results) r LOOP
  PERFORM truss.runtime_module_writer_qualified(owner.document_id,owner.module,actor);
 END LOOP;
 PERFORM truss.runtime_edge_authorize(attempt.id);
 RETURN attempt.id;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_authorize_retained_request(bigint) FROM PUBLIC;

CREATE FUNCTION truss.recover_group_request(original_input bytea,original_documents bytea,original_request bytea,
 expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE request jsonb;installation truss.catalog_runtime_installation%ROWTYPE;actor oid;ns bytea;rk bytea;
 receipt truss.request_receipt%ROWTYPE;attempt_id uuid;attempt truss.runtime_object_attempt%ROWTYPE;result jsonb;state text;code text;
BEGIN
 IF current_setting('transaction_read_only')<>'off' THEN
  RAISE EXCEPTION 'selected read-write receipt observation profile required' USING ERRCODE='0A000';END IF;
 actor:=truss.runtime_person(false);
 IF original_input IS NULL OR octet_length(original_input) NOT BETWEEN 1 AND 1048576
  OR original_documents IS NULL OR octet_length(original_documents) NOT BETWEEN 1 AND 4194304 THEN
  RAISE EXCEPTION 'bounded complete original recovery frame required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'selected receipt observer runtime required' USING ERRCODE='0A000';END IF;
 IF original_request IS NULL OR octet_length(original_request) NOT BETWEEN 1 AND 65536
  OR (convert_from(original_request,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'bounded original request frame required' USING ERRCODE='22023';END IF;
 request:=convert_from(original_request,'UTF8')::jsonb;
 IF request->>'state' IS DISTINCT FROM 'present' THEN
  RAISE EXCEPTION 'request-present frame required' USING ERRCODE='22023';END IF;
 IF request->'identity'->>'authorizedScopeIdentity' IS DISTINCT FROM
  'truss-person:'||installation.installation_id::text||':'||actor::text THEN
  RAISE EXCEPTION 'original person request scope required' USING ERRCODE='P1403';END IF;
 ns:=convert_to(request->'identity'->>'authorizedScopeIdentity','UTF8');
 rk:=convert_to(request->'identity'->>'requestId','UTF8');
 SELECT * INTO receipt FROM truss.request_receipt WHERE namespace_sha256=sha256(ns) AND request_sha256=sha256(rk)
  AND namespace_identity_utf8=ns AND request_id_utf8=rk;
 IF FOUND THEN
  attempt_id:=truss.runtime_authorize_retained_request(receipt.storage_row_id);
  IF receipt.payload_state='complete' THEN
   SELECT * INTO STRICT attempt FROM truss.runtime_object_attempt WHERE id=attempt_id;
   -- Semantic input equality remains the original request-conflict rule.
   -- Separate source/request bytes establish the frozen frame's original custody.
   IF attempt.documents_bytes IS DISTINCT FROM original_documents OR attempt.request_bytes IS DISTINCT FROM original_request THEN
    PERFORM truss.runtime_authorize_retained_request(receipt.storage_row_id);
    RAISE EXCEPTION 'original frozen source and request frame required' USING ERRCODE='22023';END IF;
  END IF;
 END IF;
 result:=convert_from(truss.object_group_begin_prepared(original_input,original_documents,original_request,
  expected_release,expected_digest,convert_to('[]','UTF8'),true,NULL),'UTF8')::jsonb;
 IF result->>'outcome'='miss' THEN
  RETURN convert_to('{"outcome":"unavailable","reason":"request_not_observed"}','UTF8');END IF;
 IF result->>'outcome'='execute' THEN
  RAISE EXCEPTION 'receipt-only observer cannot execute' USING ERRCODE='55000';END IF;
 RETURN convert_to(result::text,'UTF8');
EXCEPTION WHEN SQLSTATE '22023' OR SQLSTATE 'P1001' OR SQLSTATE 'P1403'
 OR SQLSTATE '0A000' OR SQLSTATE '54000' OR SQLSTATE '55P03' THEN
 GET STACKED DIAGNOSTICS state=RETURNED_SQLSTATE;
 IF state IN ('0A000','54000','55P03') THEN
  RETURN convert_to(jsonb_build_object('outcome','unavailable','reason',CASE state
   WHEN '0A000' THEN 'profile' WHEN '54000' THEN 'resource' ELSE 'observation' END)::text,'UTF8');END IF;
 code:=CASE state WHEN '22023' THEN 'invalid_input' WHEN 'P1001' THEN 'request_conflict' ELSE 'unauthorized_person' END;
 RETURN convert_to(jsonb_build_object('outcome','failed','code',code,'nativeState',state)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.recover_group_request(bytea,bytea,bytea,text,text) FROM PUBLIC;
