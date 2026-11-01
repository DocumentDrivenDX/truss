-- Versioned source custody over one exact Truss feed interval.
-- External destination registration and protected ACK authority remain owned
-- by the Ashlar source holder; these bytes are retained only for correspondence.
CREATE TABLE truss.runtime_feed_source_custody (
 custody_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 backend_pid integer NOT NULL,
 lock_key_a integer NOT NULL CHECK(lock_key_a BETWEEN 1 AND 2147483647),
 lock_key_b integer NOT NULL CHECK(lock_key_b BETWEEN 1 AND 2147483647),
 opened_xid xid8 NOT NULL,
 consumer_id text NOT NULL UNIQUE,
 registration_id uuid NOT NULL,
 installation_id text NOT NULL,
 source_epoch text NOT NULL,
 release_id text NOT NULL,
 release_sha256 text NOT NULL,
 prior_bytes bytea NOT NULL,
 target_bytes bytea NOT NULL,
 feed_sha256 text NOT NULL,
 payload_bytes bytea NOT NULL,
 maximum_facts integer NOT NULL,
 maximum_bytes integer NOT NULL,
 request_bytes bytea NOT NULL,
 destination_registration_bytes bytea NOT NULL,
 ack_scope_bytes bytea NOT NULL,
 destination_id text NOT NULL,
 request_sha256 text NOT NULL,
 publication_id text NOT NULL,
 internal_token text NOT NULL,
 internal_token_sha256 bytea NOT NULL,
 phase text NOT NULL CHECK(phase IN ('before_ack','ack_unresolved')),
 ack_xid xid8,
 ack_receipt_bytes bytea,
 CHECK(octet_length(prior_bytes) BETWEEN 1 AND 16384),
 CHECK(octet_length(target_bytes) BETWEEN 1 AND 16384),
 CHECK(octet_length(payload_bytes) BETWEEN 1 AND 16777216),
 CHECK(octet_length(request_bytes) BETWEEN 1 AND 16777216),
 CHECK(octet_length(destination_registration_bytes) BETWEEN 1 AND 1048576),
 CHECK(octet_length(ack_scope_bytes) BETWEEN 1 AND 1048576),
 CHECK(octet_length(internal_token_sha256)=32),
 CHECK(octet_length(internal_token) BETWEEN 32 AND 128),
 CHECK(maximum_facts BETWEEN 1 AND 65536),
 CHECK(maximum_bytes BETWEEN 1 AND 16777216),
 CHECK(feed_sha256 ~ '^[0-9a-f]{64}$'),
 CHECK(release_sha256 ~ '^[0-9a-f]{64}$'));
REVOKE ALL ON TABLE truss.runtime_feed_source_custody FROM PUBLIC;

-- A session-level two-int advisory lock is the liveness witness. pg_locks is
-- globally observable and is matched on the complete lock identity, database,
-- owning backend, mode and grant state; a reused PID alone cannot keep custody.
CREATE FUNCTION truss.runtime_feed_custody_lock_active(selected_pid integer,
 selected_key_a integer,selected_key_b integer)
RETURNS boolean LANGUAGE sql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
 SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_locks l
  WHERE l.locktype='advisory' AND l.database=(SELECT oid FROM pg_catalog.pg_database
    WHERE datname=pg_catalog.current_database())
   AND l.classid=selected_key_a::oid AND l.objid=selected_key_b::oid AND l.objsubid=2
   AND l.pid=selected_pid AND l.mode='ExclusiveLock' AND l.granted)
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_custody_lock_active(integer,integer,integer) FROM PUBLIC;

CREATE FUNCTION truss.runtime_feed_custody_assert_mutable(selected_consumer text)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE active truss.runtime_feed_source_custody%ROWTYPE; supplied text;
BEGIN
 SELECT * INTO active FROM truss.runtime_feed_source_custody WHERE consumer_id=selected_consumer;
 IF FOUND THEN
  supplied:=current_setting('truss.feed_source_custody_token',true);
  IF supplied IS NULL OR supplied='' OR sha256(convert_to(supplied,'UTF8')) IS DISTINCT FROM active.internal_token_sha256
  OR active.backend_pid IS DISTINCT FROM pg_backend_pid()
  OR NOT truss.runtime_feed_custody_lock_active(active.backend_pid,active.lock_key_a,active.lock_key_b) THEN
   RAISE EXCEPTION 'feed source custody fences this consumer' USING ERRCODE='55P03';
  END IF;
  RETURN;
 END IF;
 -- No active holder exists. A concurrent open takes the consumer row FOR
 -- UPDATE NOWAIT before publishing its custody row; this is the race fence.
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_custody_assert_mutable(text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_feed_custody_prune_stale()
RETURNS integer LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE removed integer;
BEGIN
 DELETE FROM truss.runtime_feed_source_custody c
 WHERE NOT truss.runtime_feed_custody_lock_active(c.backend_pid,c.lock_key_a,c.lock_key_b);
 GET DIAGNOSTICS removed=ROW_COUNT;
 RETURN removed;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_custody_prune_stale() FROM PUBLIC;

CREATE FUNCTION truss.runtime_feed_custody_consumer_guard()
RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 IF TG_OP='DELETE' THEN
  PERFORM truss.runtime_feed_custody_assert_mutable(OLD.consumer_id);
  RETURN OLD;
 END IF;
 IF TG_OP='UPDATE' THEN
  PERFORM truss.runtime_feed_custody_assert_mutable(OLD.consumer_id);
  PERFORM truss.runtime_feed_custody_assert_mutable(NEW.consumer_id);
  IF OLD.consumer_id IS DISTINCT FROM NEW.consumer_id THEN
   RAISE EXCEPTION 'feed consumer identity is immutable' USING ERRCODE='55000';
  END IF;
  RETURN NEW;
 END IF;
 PERFORM truss.runtime_feed_custody_assert_mutable(NEW.consumer_id);
 RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_custody_consumer_guard() FROM PUBLIC;
CREATE TRIGGER runtime_feed_source_custody_guard
 BEFORE INSERT OR UPDATE OR DELETE ON truss.runtime_feed_consumer
 FOR EACH ROW EXECUTE FUNCTION truss.runtime_feed_custody_consumer_guard();
ALTER TABLE truss.runtime_feed_consumer ENABLE ALWAYS TRIGGER runtime_feed_source_custody_guard;

CREATE FUNCTION truss.runtime_feed_custody_truncate_guard()
RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM truss.runtime_feed_source_custody) THEN
  RAISE EXCEPTION 'active feed source custody prevents truncate' USING ERRCODE='55P03';
 END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_custody_truncate_guard() FROM PUBLIC;
CREATE TRIGGER runtime_feed_source_custody_consumer_truncate
 BEFORE TRUNCATE ON truss.runtime_feed_consumer
 FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_feed_custody_truncate_guard();
CREATE TRIGGER runtime_feed_source_custody_receipt_truncate
 BEFORE TRUNCATE ON truss.runtime_feed_ack_receipt
 FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_feed_custody_truncate_guard();
ALTER TABLE truss.runtime_feed_consumer ENABLE ALWAYS TRIGGER runtime_feed_source_custody_consumer_truncate;
ALTER TABLE truss.runtime_feed_ack_receipt ENABLE ALWAYS TRIGGER runtime_feed_source_custody_receipt_truncate;

CREATE FUNCTION truss.open_feed_source_custody(selected_consumer text,expected_prior bytea,
 expected_target bytea,expected_feed_sha text,selected_payload bytea,maximum_facts integer,
 maximum_bytes integer,request_original bytea,destination_registration bytea,ack_scope bytea,
 selected_destination text,selected_request_sha text,selected_publication text,
 expected_release text,expected_digest text,selected_lock_key_a integer,selected_lock_key_b integer,selected_token text)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE selected_page bytea; page jsonb; cursor jsonb; consumer truss.runtime_feed_consumer%ROWTYPE;
 registration uuid; installation truss.catalog_runtime_installation%ROWTYPE; custody uuid; token text;
 stale truss.runtime_feed_source_custody%ROWTYPE;
BEGIN
 IF selected_consumer IS NULL OR octet_length(selected_consumer) NOT BETWEEN 1 AND 4096
  OR expected_prior IS NULL OR expected_target IS NULL OR selected_payload IS NULL
  OR octet_length(selected_payload)>16777216 OR expected_feed_sha !~ '^[0-9a-f]{64}$'
  OR maximum_facts NOT BETWEEN 1 AND 65536 OR maximum_bytes NOT BETWEEN 1 AND 16777216
  OR request_original IS NULL OR octet_length(request_original) NOT BETWEEN 1 AND 16777216
  OR destination_registration IS NULL OR octet_length(destination_registration) NOT BETWEEN 1 AND 1048576
  OR ack_scope IS NULL OR octet_length(ack_scope) NOT BETWEEN 1 AND 1048576 THEN
  RAISE EXCEPTION 'bounded exact source custody selection required' USING ERRCODE='22023';
 END IF;
 IF selected_destination IS NULL OR octet_length(selected_destination) NOT BETWEEN 1 AND 1024
  OR selected_request_sha IS NULL OR selected_request_sha !~ '^[0-9a-f]{64}$' OR selected_publication IS NULL
  OR octet_length(selected_publication) NOT BETWEEN 1 AND 4096 THEN
  RAISE EXCEPTION 'bounded exact external ACK scope binding required' USING ERRCODE='22023';
 END IF;
 IF selected_request_sha IS DISTINCT FROM encode(sha256(request_original),'hex') THEN
  RAISE EXCEPTION 'request hash must bind original request bytes' USING ERRCODE='55000';
 END IF;
 IF selected_lock_key_a IS NULL OR selected_lock_key_b IS NULL OR selected_token IS NULL
  OR octet_length(selected_token) NOT BETWEEN 32 AND 128
  OR selected_lock_key_a NOT BETWEEN 1 AND 2147483647 OR selected_lock_key_b NOT BETWEEN 1 AND 2147483647
  OR NOT truss.runtime_feed_custody_lock_active(pg_backend_pid(),selected_lock_key_a,selected_lock_key_b) THEN
  RAISE EXCEPTION 'original live source host marker required' USING ERRCODE='55P03';
 END IF;
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 -- Consumer row serialization closes the race with ACK/re-registration.
 SELECT * INTO STRICT consumer FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer FOR UPDATE NOWAIT;
 -- Session lock release is automatic on connection loss and survives a caller
 -- rollback. It never depends on pid reuse or pg_stat_activity visibility.
 SELECT * INTO stale FROM truss.runtime_feed_source_custody WHERE consumer_id=selected_consumer;
 IF FOUND THEN
  IF truss.runtime_feed_custody_lock_active(stale.backend_pid,stale.lock_key_a,stale.lock_key_b) THEN
   RAISE EXCEPTION 'live feed source custody already exists' USING ERRCODE='55P03';
  END IF;
  DELETE FROM truss.runtime_feed_source_custody WHERE custody_id=stale.custody_id;
 END IF;
 IF consumer.checkpoint_bytes IS DISTINCT FROM expected_prior THEN
  RAISE EXCEPTION 'feed source checkpoint moved before custody open' USING ERRCODE='55P03';
 END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'selected feed runtime changed' USING ERRCODE='0A000';
 END IF;
 selected_page:=truss.reread_feed(selected_consumer,expected_prior,expected_target,expected_feed_sha,
  maximum_facts,maximum_bytes,expected_release,expected_digest);
 page:=convert_from(selected_page,'UTF8')::jsonb;
 IF decode(page->>'payloadBase64','base64') IS DISTINCT FROM selected_payload
  OR decode(page->>'priorBase64','base64') IS DISTINCT FROM expected_prior
  OR decode(page->>'nextBase64','base64') IS DISTINCT FROM expected_target
  OR page->>'registrationId' IS DISTINCT FROM consumer.registration_id::text
  OR page->>'outcome'='empty_interval' OR sha256(selected_payload) IS DISTINCT FROM decode(expected_feed_sha,'hex') THEN
  RAISE EXCEPTION 'exact retained nonempty feed page required' USING ERRCODE='55000';
 END IF;
 cursor:=convert_from(expected_prior,'UTF8')::jsonb;
 IF (cursor->>'installationId') IS DISTINCT FROM installation.installation_id::text
  OR (cursor->>'sourceEpoch') IS NULL OR (cursor->>'registrationId') IS DISTINCT FROM consumer.registration_id::text THEN
  RAISE EXCEPTION 'exact feed installation, epoch and registration required' USING ERRCODE='55000';
 END IF;
 custody:=gen_random_uuid(); token:=selected_token;
 INSERT INTO truss.runtime_feed_source_custody(custody_id,backend_pid,lock_key_a,lock_key_b,opened_xid,consumer_id,registration_id,
  installation_id,source_epoch,release_id,release_sha256,prior_bytes,target_bytes,feed_sha256,payload_bytes,
  maximum_facts,maximum_bytes,request_bytes,destination_registration_bytes,ack_scope_bytes,destination_id,
  request_sha256,publication_id,internal_token,internal_token_sha256,phase)
 VALUES(custody,pg_backend_pid(),selected_lock_key_a,selected_lock_key_b,pg_current_xact_id(),selected_consumer,consumer.registration_id,installation.installation_id,
  cursor->>'sourceEpoch',expected_release,expected_digest,expected_prior,expected_target,expected_feed_sha,
  selected_payload,maximum_facts,maximum_bytes,request_original,destination_registration,ack_scope,
  selected_destination,selected_request_sha,selected_publication,token,sha256(convert_to(token,'UTF8')),'before_ack');
 RETURN convert_to(jsonb_build_object('custodyId',custody::text,'selectionSha256',encode(sha256(
  convert_to(jsonb_build_object('consumerId',selected_consumer,'registrationId',consumer.registration_id::text,
   'installationId',installation.installation_id,'sourceEpoch',cursor->>'sourceEpoch','releaseId',expected_release,
   'releaseSha256',expected_digest,'priorBase64',replace(encode(expected_prior,'base64'),chr(10),''),
   'nextBase64',replace(encode(expected_target,'base64'),chr(10),''),'feedSha256',expected_feed_sha,
   'requestSha256',encode(sha256(request_original),'hex'),'destinationRegistrationSha256',encode(sha256(destination_registration),'hex'),
   'ackScopeSha256',encode(sha256(ack_scope),'hex'))::text,'UTF8')),'hex'))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.open_feed_source_custody(text,bytea,bytea,text,bytea,integer,integer,bytea,bytea,bytea,text,text,text,text,text,integer,integer,text) FROM PUBLIC;

CREATE FUNCTION truss.renew_feed_source_custody(custody uuid,request_original bytea,
 destination_registration bytea,ack_scope bytea,selected_phase text,expected_release text,expected_digest text,
 selected_lock_key_a integer,selected_lock_key_b integer,selected_token text)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE active truss.runtime_feed_source_custody%ROWTYPE; consumer truss.runtime_feed_consumer%ROWTYPE;
 checkpoint bytea; observed bytea; receipt truss.runtime_feed_ack_receipt%ROWTYPE; outcome text;
BEGIN
 SELECT * INTO STRICT active FROM truss.runtime_feed_source_custody WHERE custody_id=custody;
 IF active.backend_pid IS DISTINCT FROM pg_backend_pid()
  OR active.lock_key_a IS DISTINCT FROM selected_lock_key_a OR active.lock_key_b IS DISTINCT FROM selected_lock_key_b
  OR sha256(convert_to(selected_token,'UTF8')) IS DISTINCT FROM active.internal_token_sha256
  OR NOT truss.runtime_feed_custody_lock_active(active.backend_pid,active.lock_key_a,active.lock_key_b)
  OR coalesce(pg_current_xact_id_if_assigned()=active.opened_xid,false)
  OR active.release_id IS DISTINCT FROM expected_release OR active.release_sha256 IS DISTINCT FROM expected_digest
  OR active.request_bytes IS DISTINCT FROM request_original
  OR active.destination_registration_bytes IS DISTINCT FROM destination_registration
  OR active.ack_scope_bytes IS DISTINCT FROM ack_scope
  OR selected_phase NOT IN ('before_ack','ack_unresolved') THEN
  RAISE EXCEPTION 'original feed source custody authority required' USING ERRCODE='55P03';
 END IF;
 PERFORM truss.runtime_feed_authorize(active.consumer_id,expected_release,expected_digest);
 SELECT * INTO STRICT consumer FROM truss.runtime_feed_consumer WHERE consumer_id=active.consumer_id;
 IF consumer.registration_id IS DISTINCT FROM active.registration_id THEN RAISE EXCEPTION 'feed registration changed' USING ERRCODE='55P03'; END IF;
 observed:=truss.reread_feed(active.consumer_id,active.prior_bytes,active.target_bytes,active.feed_sha256,
  active.maximum_facts,active.maximum_bytes,expected_release,expected_digest);
 IF decode((convert_from(observed,'UTF8')::jsonb)->>'payloadBase64','base64') IS DISTINCT FROM active.payload_bytes THEN
  RAISE EXCEPTION 'original feed page changed' USING ERRCODE='55000'; END IF;
 checkpoint:=consumer.checkpoint_bytes;
 SELECT * INTO receipt FROM truss.runtime_feed_ack_receipt WHERE registration_id=active.registration_id
  AND prior_sha256=encode(sha256(active.prior_bytes),'hex') AND target_sha256=encode(sha256(active.target_bytes),'hex');
 outcome:=CASE WHEN NOT FOUND THEN 'missing' WHEN receipt.prior_bytes=active.prior_bytes
  AND receipt.target_bytes=active.target_bytes AND receipt.receipt_bytes IS NOT NULL
  AND receipt.binding->>'feedSha256'=active.feed_sha256
  AND receipt.binding->>'destinationId'=active.destination_id
  AND receipt.binding->>'requestSha256'=active.request_sha256
  AND receipt.binding->>'publicationId'=active.publication_id
  AND receipt.receipt_bytes IS NOT DISTINCT FROM active.ack_receipt_bytes THEN 'matched' ELSE 'conflicting' END;
 IF selected_phase='before_ack' AND (checkpoint IS DISTINCT FROM active.prior_bytes OR active.phase<>'before_ack')
  OR selected_phase='ack_unresolved' AND (checkpoint NOT IN (active.prior_bytes,active.target_bytes) OR active.phase NOT IN ('before_ack','ack_unresolved'))
  OR selected_phase='ack_unresolved' AND ((checkpoint=active.prior_bytes AND outcome<>'missing')
   OR (checkpoint=active.target_bytes AND outcome<>'matched')) THEN
  RAISE EXCEPTION 'phase-specific feed checkpoint/receipt correspondence required' USING ERRCODE='55000';
 END IF;
 UPDATE truss.runtime_feed_source_custody SET phase=selected_phase WHERE custody_id=custody;
 RETURN convert_to(jsonb_build_object('phase',selected_phase,'checkpointBase64',replace(encode(checkpoint,'base64'),chr(10),''),
  'receiptOutcome',outcome,'consumerId',active.consumer_id,'registrationId',active.registration_id::text,
  'installationId',active.installation_id,'sourceEpoch',active.source_epoch,'releaseId',active.release_id,
  'releaseSha256',active.release_sha256,'priorBase64',replace(encode(active.prior_bytes,'base64'),chr(10),''),
  'nextBase64',replace(encode(active.target_bytes,'base64'),chr(10),''),'feedSha256',active.feed_sha256)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.renew_feed_source_custody(uuid,bytea,bytea,bytea,text,text,text,integer,integer,text) FROM PUBLIC;

CREATE FUNCTION truss.acknowledge_feed_under_source_custody(custody uuid,request_original bytea,
 destination_registration bytea,ack_scope bytea,selected_consumer text,prior bytea,target bytea,
 feed_sha text,destination text,request_sha text,publication text,receipt_bytes bytea,
 expected_release text,expected_digest text,selected_lock_key_a integer,selected_lock_key_b integer,selected_token text)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE active truss.runtime_feed_source_custody%ROWTYPE; result bytea;
BEGIN
 SELECT * INTO STRICT active FROM truss.runtime_feed_source_custody WHERE custody_id=custody FOR UPDATE;
 IF active.backend_pid IS DISTINCT FROM pg_backend_pid()
  OR active.lock_key_a IS DISTINCT FROM selected_lock_key_a OR active.lock_key_b IS DISTINCT FROM selected_lock_key_b
  OR sha256(convert_to(selected_token,'UTF8')) IS DISTINCT FROM active.internal_token_sha256
  OR NOT truss.runtime_feed_custody_lock_active(active.backend_pid,active.lock_key_a,active.lock_key_b)
  OR coalesce(pg_current_xact_id_if_assigned()=active.opened_xid,false)
  OR active.consumer_id IS DISTINCT FROM selected_consumer
  OR active.release_id IS DISTINCT FROM expected_release OR active.release_sha256 IS DISTINCT FROM expected_digest
  OR active.request_bytes IS DISTINCT FROM request_original
  OR active.destination_registration_bytes IS DISTINCT FROM destination_registration
  OR active.ack_scope_bytes IS DISTINCT FROM ack_scope
  OR active.prior_bytes IS DISTINCT FROM prior OR active.target_bytes IS DISTINCT FROM target
  OR active.feed_sha256 IS DISTINCT FROM feed_sha OR active.destination_id IS DISTINCT FROM destination
  OR active.request_sha256 IS DISTINCT FROM request_sha OR active.publication_id IS DISTINCT FROM publication
  OR active.phase<>'before_ack' THEN
  RAISE EXCEPTION 'exact source custody ACK scope required' USING ERRCODE='55P03';
 END IF;
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 PERFORM pg_catalog.set_config('truss.feed_source_custody_token',active.internal_token,true);
 BEGIN
  result:=truss.acknowledge_feed_with_receipt(selected_consumer,prior,target,feed_sha,destination,request_sha,
   publication,receipt_bytes,expected_release,expected_digest);
  PERFORM pg_catalog.set_config('truss.feed_source_custody_token','',true);
 EXCEPTION WHEN OTHERS THEN
  PERFORM pg_catalog.set_config('truss.feed_source_custody_token','',true);
  RAISE;
 END;
 UPDATE truss.runtime_feed_source_custody SET phase='ack_unresolved',ack_xid=pg_current_xact_id(),
  ack_receipt_bytes=receipt_bytes WHERE custody_id=custody;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.acknowledge_feed_under_source_custody(uuid,bytea,bytea,bytea,text,bytea,bytea,text,text,text,text,bytea,text,text,integer,integer,text) FROM PUBLIC;

CREATE FUNCTION truss.reconcile_feed_ack_under_source_custody(custody uuid,request_original bytea,
 destination_registration bytea,ack_scope bytea,selected_consumer text,prior bytea,target bytea,
 feed_sha text,destination text,request_sha text,publication text,receipt_bytes bytea,
 expected_release text,expected_digest text,selected_lock_key_a integer,selected_lock_key_b integer,selected_token text)
RETURNS bytea LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE active truss.runtime_feed_source_custody%ROWTYPE; result bytea;
BEGIN
 SELECT * INTO STRICT active FROM truss.runtime_feed_source_custody WHERE custody_id=custody;
 IF active.backend_pid IS DISTINCT FROM pg_backend_pid()
  OR active.lock_key_a IS DISTINCT FROM selected_lock_key_a OR active.lock_key_b IS DISTINCT FROM selected_lock_key_b
  OR sha256(convert_to(selected_token,'UTF8')) IS DISTINCT FROM active.internal_token_sha256
  OR NOT truss.runtime_feed_custody_lock_active(active.backend_pid,active.lock_key_a,active.lock_key_b)
  OR coalesce(pg_current_xact_id_if_assigned()=active.opened_xid,false)
  OR active.consumer_id IS DISTINCT FROM selected_consumer
  OR active.release_id IS DISTINCT FROM expected_release OR active.release_sha256 IS DISTINCT FROM expected_digest
  OR active.request_bytes IS DISTINCT FROM request_original
  OR active.destination_registration_bytes IS DISTINCT FROM destination_registration
  OR active.ack_scope_bytes IS DISTINCT FROM ack_scope
  OR active.prior_bytes IS DISTINCT FROM prior OR active.target_bytes IS DISTINCT FROM target
  OR active.feed_sha256 IS DISTINCT FROM feed_sha OR active.destination_id IS DISTINCT FROM destination
  OR active.request_sha256 IS DISTINCT FROM request_sha OR active.publication_id IS DISTINCT FROM publication
  OR active.phase NOT IN ('before_ack','ack_unresolved') THEN
  RAISE EXCEPTION 'exact source custody reconciliation scope required' USING ERRCODE='55P03';
 END IF;
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 result:=truss.reconcile_feed_ack(selected_consumer,prior,target,feed_sha,destination,request_sha,
  publication,receipt_bytes,expected_release,expected_digest);
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.reconcile_feed_ack_under_source_custody(uuid,bytea,bytea,bytea,text,bytea,bytea,text,text,text,text,bytea,text,text,integer,integer,text) FROM PUBLIC;

CREATE FUNCTION truss.close_feed_source_custody(custody uuid,request_original bytea,
 destination_registration bytea,ack_scope bytea,committed boolean,expected_release text,expected_digest text,
 selected_lock_key_a integer,selected_lock_key_b integer,selected_token text)
RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE active truss.runtime_feed_source_custody%ROWTYPE; current_checkpoint bytea; observed bytea; initial_xid xid8;
BEGIN
 initial_xid:=pg_current_xact_id_if_assigned();
 SELECT * INTO STRICT active FROM truss.runtime_feed_source_custody WHERE custody_id=custody FOR UPDATE;
 IF active.backend_pid IS DISTINCT FROM pg_backend_pid()
  OR active.lock_key_a IS DISTINCT FROM selected_lock_key_a OR active.lock_key_b IS DISTINCT FROM selected_lock_key_b
  OR sha256(convert_to(selected_token,'UTF8')) IS DISTINCT FROM active.internal_token_sha256
  OR NOT truss.runtime_feed_custody_lock_active(active.backend_pid,active.lock_key_a,active.lock_key_b)
  OR coalesce(pg_current_xact_id_if_assigned()=active.opened_xid,false)
  OR active.release_id IS DISTINCT FROM expected_release OR active.release_sha256 IS DISTINCT FROM expected_digest
  OR active.request_bytes IS DISTINCT FROM request_original
  OR active.destination_registration_bytes IS DISTINCT FROM destination_registration
  OR active.ack_scope_bytes IS DISTINCT FROM ack_scope THEN
  RAISE EXCEPTION 'original feed source custody authority required' USING ERRCODE='55P03';
 END IF;
 PERFORM truss.runtime_feed_authorize(active.consumer_id,expected_release,expected_digest);
 observed:=truss.reread_feed(active.consumer_id,active.prior_bytes,active.target_bytes,active.feed_sha256,
  active.maximum_facts,active.maximum_bytes,expected_release,expected_digest);
 IF decode((convert_from(observed,'UTF8')::jsonb)->>'payloadBase64','base64') IS DISTINCT FROM active.payload_bytes THEN
  RAISE EXCEPTION 'original feed page changed before custody close' USING ERRCODE='55000'; END IF;
 SELECT checkpoint_bytes INTO STRICT current_checkpoint FROM truss.runtime_feed_consumer
  WHERE consumer_id=active.consumer_id AND registration_id=active.registration_id;
 IF committed THEN
  IF current_checkpoint IS DISTINCT FROM active.target_bytes OR active.phase<>'ack_unresolved'
   OR active.ack_xid IS NULL OR initial_xid IS NOT DISTINCT FROM active.ack_xid THEN
   RAISE EXCEPTION 'committed custody close requires a fresh transaction after exact ACK' USING ERRCODE='55000'; END IF;
  IF NOT EXISTS(SELECT 1 FROM truss.runtime_feed_ack_receipt r WHERE r.registration_id=active.registration_id
   AND r.prior_bytes=active.prior_bytes AND r.target_bytes=active.target_bytes
   AND r.binding->>'feedSha256'=active.feed_sha256 AND r.binding->>'destinationId'=active.destination_id
   AND r.binding->>'requestSha256'=active.request_sha256 AND r.binding->>'publicationId'=active.publication_id
   AND r.receipt_bytes=active.ack_receipt_bytes) THEN
   RAISE EXCEPTION 'exact committed ACK receipt required at custody close' USING ERRCODE='55000'; END IF;
 ELSE
  IF current_checkpoint IS DISTINCT FROM active.prior_bytes OR active.phase<>'before_ack' THEN
   RAISE EXCEPTION 'no-publication feed custody close requires exact original checkpoint' USING ERRCODE='55000'; END IF;
 END IF;
 DELETE FROM truss.runtime_feed_source_custody WHERE custody_id=custody;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.close_feed_source_custody(uuid,bytea,bytea,bytea,boolean,text,text,integer,integer,text) FROM PUBLIC;
