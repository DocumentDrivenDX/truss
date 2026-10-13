-- Source-side opaque destination receipt retention; no foreign commit attestation.
CREATE TABLE truss.runtime_feed_ack_receipt (
 registration_id uuid NOT NULL REFERENCES truss.runtime_feed_consumer(registration_id),
 prior_sha256 text NOT NULL,target_sha256 text NOT NULL,
 prior_bytes bytea NOT NULL,target_bytes bytea NOT NULL,
 binding jsonb NOT NULL,receipt_bytes bytea NOT NULL,
 PRIMARY KEY(registration_id,prior_sha256,target_sha256));
CREATE TRIGGER runtime_feed_ack_receipt_immutable BEFORE UPDATE OR DELETE ON truss.runtime_feed_ack_receipt
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
REVOKE ALL ON TABLE truss.runtime_feed_ack_receipt FROM PUBLIC;

CREATE FUNCTION truss.feed_ack_receipt_binding(selected_consumer text,prior bytea,target bytea,feed_sha text,
 destination text,request_sha text,publication text,receipt bytea,expected_release text,expected_digest text)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE p jsonb;t jsonb;x numeric;
BEGIN
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 IF prior IS NULL OR target IS NULL OR octet_length(prior) NOT BETWEEN 1 AND 16384 OR octet_length(target) NOT BETWEEN 1 AND 16384
 OR receipt IS NULL OR octet_length(receipt) NOT BETWEEN 1 AND 1048576
 OR destination IS NULL OR octet_length(destination) NOT BETWEEN 1 AND 1024 OR publication IS NULL OR octet_length(publication) NOT BETWEEN 1 AND 4096
 OR feed_sha IS NULL OR feed_sha !~ '^[0-9a-f]{64}$' OR request_sha IS NULL OR request_sha !~ '^[0-9a-f]{64}$'
 OR (convert_from(prior,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
 OR (convert_from(target,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE
 THEN RAISE EXCEPTION 'bounded exact ACK receipt binding required' USING ERRCODE='22023';END IF;
 p:=convert_from(prior,'UTF8')::jsonb;t:=convert_from(target,'UTF8')::jsonb;
 FOR x IN SELECT CASE WHEN j->>'nextXid' ~ '^(0|[1-9][0-9]{0,19})$' THEN (j->>'nextXid')::numeric ELSE NULL END FROM unnest(ARRAY[p,t]) j LOOP
  IF x IS NULL OR x>18446744073709551615 THEN RAISE EXCEPTION 'canonical ACK receipt cursor required' USING ERRCODE='22023';END IF;
 END LOOP;
 IF prior IS DISTINCT FROM truss.runtime_feed_cursor(selected_consumer,p->>'nextXid')
 OR target IS DISTINCT FROM truss.runtime_feed_cursor(selected_consumer,t->>'nextXid')
 OR (p->>'nextXid')::numeric>(t->>'nextXid')::numeric
 THEN RAISE EXCEPTION 'current original ACK receipt scope required' USING ERRCODE='22023';END IF;
 RETURN jsonb_build_object('installationId',p->>'installationId','sourceEpoch',p->>'sourceEpoch',
 'consumerId',selected_consumer,'registrationId',p->>'registrationId','feedSha256',feed_sha,
 'destinationId',destination,'requestSha256',request_sha,'publicationId',publication,'receiptSha256',encode(sha256(receipt),'hex'));
END;
$$;
REVOKE ALL ON FUNCTION truss.feed_ack_receipt_binding(text,bytea,bytea,text,text,text,text,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.acknowledge_feed_with_receipt(selected_consumer text,prior bytea,target bytea,feed_sha text,
 destination text,request_sha text,publication text,receipt bytea,expected_release text,expected_digest text)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE selected jsonb;stored truss.runtime_feed_ack_receipt%ROWTYPE;c truss.runtime_feed_consumer%ROWTYPE;ack jsonb;checkpoint bytea;
BEGIN
 selected:=truss.feed_ack_receipt_binding(selected_consumer,prior,target,feed_sha,destination,request_sha,publication,receipt,expected_release,expected_digest);
 SELECT * INTO STRICT c FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer FOR UPDATE NOWAIT;
 SELECT * INTO stored FROM truss.runtime_feed_ack_receipt WHERE registration_id=c.registration_id
 AND prior_sha256=encode(sha256(prior),'hex') AND target_sha256=encode(sha256(target),'hex');
 IF FOUND THEN
  IF stored.prior_bytes IS DISTINCT FROM prior OR stored.target_bytes IS DISTINCT FROM target OR stored.binding IS DISTINCT FROM selected OR stored.receipt_bytes IS DISTINCT FROM receipt
  THEN RAISE EXCEPTION 'immutable ACK receipt conflict' USING ERRCODE='P1001';END IF;
  checkpoint:=c.checkpoint_bytes;
  IF checkpoint IS DISTINCT FROM truss.runtime_feed_cursor(selected_consumer,convert_from(checkpoint,'UTF8')::jsonb->>'nextXid')
   OR (convert_from(checkpoint,'UTF8')::jsonb->>'nextXid')::numeric<(convert_from(target,'UTF8')::jsonb->>'nextXid')::numeric
  THEN RAISE EXCEPTION 'ACK receipt checkpoint correspondence required' USING ERRCODE='55000';END IF;
  ack:=jsonb_build_object('outcome','equal');
 ELSE
  IF prior=target THEN RAISE EXCEPTION 'first ACK receipt requires nonempty interval' USING ERRCODE='22023';END IF;
  IF c.checkpoint_bytes IS DISTINCT FROM prior THEN RAISE EXCEPTION 'ACK receipt cannot backfill prior acknowledgement' USING ERRCODE='P1001';END IF;
  ack:=convert_from(truss.acknowledge_feed(selected_consumer,prior,target,feed_sha,expected_release,expected_digest),'UTF8')::jsonb;
  INSERT INTO truss.runtime_feed_ack_receipt VALUES(c.registration_id,encode(sha256(prior),'hex'),encode(sha256(target),'hex'),prior,target,selected,receipt);
  SELECT checkpoint_bytes INTO STRICT checkpoint FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer;
  IF checkpoint IS DISTINCT FROM target OR NOT EXISTS(SELECT 1 FROM truss.runtime_feed_ack_receipt r WHERE r.registration_id=c.registration_id AND r.prior_bytes=prior AND r.target_bytes=target AND r.binding=selected AND r.receipt_bytes=receipt)
  THEN RAISE EXCEPTION 'atomic ACK receipt poststate required' USING ERRCODE='55000';END IF;
 END IF;
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 RETURN convert_to(jsonb_build_object('outcome',ack->>'outcome','binding',selected,'priorBase64',replace(encode(prior,'base64'),chr(10),''),
 'nextBase64',replace(encode(target,'base64'),chr(10),''),'checkpointBase64',replace(encode(checkpoint,'base64'),chr(10),''),'receiptBase64',replace(encode(receipt,'base64'),chr(10),''))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.acknowledge_feed_with_receipt(text,bytea,bytea,text,text,text,text,bytea,text,text) FROM PUBLIC;

CREATE FUNCTION truss.reconcile_feed_ack(selected_consumer text,prior bytea,target bytea,feed_sha text,
 destination text,request_sha text,publication text,receipt bytea,expected_release text,expected_digest text)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE selected jsonb;stored truss.runtime_feed_ack_receipt%ROWTYPE;c truss.runtime_feed_consumer%ROWTYPE;answer text;
BEGIN
 IF current_setting('transaction_read_only')<>'on' OR pg_current_xact_id_if_assigned() IS NOT NULL
 THEN RAISE EXCEPTION 'read-only unassigned transaction required for ACK reconciliation' USING ERRCODE='0A000';END IF;
 selected:=truss.feed_ack_receipt_binding(selected_consumer,prior,target,feed_sha,destination,request_sha,publication,receipt,expected_release,expected_digest);
 SELECT * INTO STRICT c FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer;
 SELECT * INTO stored FROM truss.runtime_feed_ack_receipt WHERE registration_id=c.registration_id
 AND prior_sha256=encode(sha256(prior),'hex') AND target_sha256=encode(sha256(target),'hex');
 answer:=CASE WHEN NOT FOUND THEN 'missing' WHEN stored.prior_bytes=prior AND stored.target_bytes=target AND stored.binding=selected AND stored.receipt_bytes=receipt THEN 'matched' ELSE 'conflicting' END;
 IF c.checkpoint_bytes IS DISTINCT FROM truss.runtime_feed_cursor(selected_consumer,convert_from(c.checkpoint_bytes,'UTF8')::jsonb->>'nextXid')
 OR answer<>'missing' AND (convert_from(c.checkpoint_bytes,'UTF8')::jsonb->>'nextXid')::numeric<(convert_from(stored.target_bytes,'UTF8')::jsonb->>'nextXid')::numeric
 THEN RAISE EXCEPTION 'ACK receipt checkpoint integrity required' USING ERRCODE='55000';END IF;
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 IF c.registration_id IS DISTINCT FROM (SELECT registration_id FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer)
 THEN RAISE EXCEPTION 'ACK receipt registration changed' USING ERRCODE='55P03';END IF;
 RETURN convert_to(jsonb_build_object('outcome',answer,'checkpointBase64',replace(encode(c.checkpoint_bytes,'base64'),chr(10),''),
 'binding',stored.binding,'priorBase64',replace(encode(stored.prior_bytes,'base64'),chr(10),''),'nextBase64',replace(encode(stored.target_bytes,'base64'),chr(10),''),
 'receiptBase64',replace(encode(stored.receipt_bytes,'base64'),chr(10),''))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.reconcile_feed_ack(text,bytea,bytea,text,text,text,text,bytea,text,text) FROM PUBLIC;
