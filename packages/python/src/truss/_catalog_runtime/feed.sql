-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Caller-owned complete transaction feed; no downstream durability attestation.
CREATE SEQUENCE truss.runtime_feed_reservation_seq;
CREATE TABLE truss.runtime_feed_reservation (
 reservation_id bigint PRIMARY KEY DEFAULT nextval('truss.runtime_feed_reservation_seq'),
 writer_xid xid8 NOT NULL, kind text NOT NULL CHECK(kind IN ('object_key','edge_key')),
 original_row jsonb NOT NULL);
CREATE INDEX runtime_feed_reservation_writer ON truss.runtime_feed_reservation(writer_xid,reservation_id);
CREATE TRIGGER runtime_feed_reservation_immutable BEFORE UPDATE OR DELETE ON truss.runtime_feed_reservation
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();

CREATE FUNCTION truss.runtime_feed_current_configuration() RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;
BEGIN
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 RETURN jsonb_build_object('releaseId',installation.release_id,'releaseSha256',installation.release_sha256,
  'layoutProfile',installation.layout_profile,'preparationConfiguration',installation.preparation_configuration,
  'settings',(SELECT jsonb_object_agg(key,value) FROM truss.setting));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_current_configuration() FROM PUBLIC;

CREATE FUNCTION truss.runtime_feed_retain_configuration(writer xid8,configuration jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE retained jsonb;
BEGIN
 SELECT t.configuration INTO retained FROM truss.runtime_feed_transaction_configuration t WHERE t.writer_xid=writer;
 IF FOUND THEN
  IF retained IS DISTINCT FROM configuration THEN RAISE EXCEPTION 'stable feed writer configuration required' USING ERRCODE='55000';END IF;
 ELSE
  INSERT INTO truss.runtime_feed_transaction_configuration VALUES(writer,configuration);
  SELECT t.configuration INTO retained FROM truss.runtime_feed_transaction_configuration t WHERE t.writer_xid=writer;
  IF NOT FOUND OR retained IS DISTINCT FROM configuration THEN RAISE EXCEPTION 'original feed writer configuration required' USING ERRCODE='55000';END IF;
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_retain_configuration(xid8,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_feed_capture_configuration_statement() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE row_count bigint; configuration jsonb; writer xid8:=pg_current_xact_id();
BEGIN
 IF TG_TABLE_NAME='journal' THEN
  SELECT count(*) INTO row_count FROM inserted_rows;
  IF row_count>0 AND EXISTS(SELECT 1 FROM inserted_rows WHERE xid IS DISTINCT FROM writer) THEN
   RAISE EXCEPTION 'current feed fact writer required' USING ERRCODE='55000';END IF;
 ELSE
  SELECT count(*) INTO row_count FROM inserted_rows;
  IF row_count>0 AND EXISTS(SELECT 1 FROM inserted_rows WHERE writer_xid IS DISTINCT FROM writer) THEN
   RAISE EXCEPTION 'current feed fact writer required' USING ERRCODE='55000';END IF;
 END IF;
 IF row_count>0 THEN
  configuration:=truss.runtime_feed_current_configuration();
  PERFORM truss.runtime_feed_retain_configuration(writer,configuration);
 END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_capture_configuration_statement() FROM PUBLIC;

CREATE FUNCTION truss.runtime_feed_capture_object_reservations() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE row_count bigint; inserted_count bigint;
BEGIN
 SELECT count(*) INTO row_count FROM inserted_rows;
 IF row_count=0 THEN
  RETURN NULL;
 END IF;
 WITH parsed AS MATERIALIZED (
  SELECT r.storage_row_id,(convert_from(r.original_reservation_bytes,'UTF8')::jsonb->>'xid')::xid8 AS writer_xid,to_jsonb(r) AS original_row
  FROM inserted_rows r ORDER BY r.storage_row_id)
 INSERT INTO truss.runtime_feed_reservation(writer_xid,kind,original_row)
 SELECT writer_xid,'object_key',original_row FROM parsed WHERE writer_xid=pg_current_xact_id() ORDER BY storage_row_id;
 GET DIAGNOSTICS inserted_count=ROW_COUNT;
 IF inserted_count IS DISTINCT FROM row_count THEN RAISE EXCEPTION 'original reservation writer required' USING ERRCODE='55000';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_capture_object_reservations() FROM PUBLIC;

CREATE FUNCTION truss.runtime_feed_capture_edge_reservations() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE row_count bigint; inserted_count bigint; writer xid8:=pg_current_xact_id();
BEGIN
 SELECT count(*) INTO row_count FROM inserted_rows;
 IF row_count=0 THEN
  RETURN NULL;
 END IF;
 INSERT INTO truss.runtime_feed_reservation(writer_xid,kind,original_row)
 SELECT writer,'edge_key',to_jsonb(r) FROM inserted_rows r ORDER BY r.at,r.type_id,r.key_num,r.k,r.entity_id;
 GET DIAGNOSTICS inserted_count=ROW_COUNT;
 IF inserted_count IS DISTINCT FROM row_count THEN RAISE EXCEPTION 'complete edge reservation feed required' USING ERRCODE='55000';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_capture_edge_reservations() FROM PUBLIC;

CREATE TRIGGER runtime_feed_object_reservation AFTER INSERT ON truss.object_key_reservation_bucket
 REFERENCING NEW TABLE AS inserted_rows FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_feed_capture_object_reservations();
ALTER TABLE truss.object_key_reservation_bucket ENABLE ALWAYS TRIGGER runtime_feed_object_reservation;
CREATE TRIGGER runtime_feed_edge_reservation AFTER INSERT ON truss.key_tombstone
 REFERENCING NEW TABLE AS inserted_rows FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_feed_capture_edge_reservations();
ALTER TABLE truss.key_tombstone ENABLE ALWAYS TRIGGER runtime_feed_edge_reservation;

CREATE TABLE truss.runtime_feed_configuration (singleton boolean PRIMARY KEY CHECK(singleton),original_settings jsonb NOT NULL);
INSERT INTO truss.runtime_feed_configuration SELECT true,jsonb_object_agg(key,value) FROM truss.setting;
CREATE TRIGGER runtime_feed_configuration_immutable BEFORE UPDATE OR DELETE ON truss.runtime_feed_configuration
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();

CREATE TABLE truss.runtime_feed_consumer (
 consumer_id text PRIMARY KEY CHECK(octet_length(consumer_id) BETWEEN 1 AND 4096),
 registration_id uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),reader_oid oid NOT NULL,
 checkpoint_bytes bytea NOT NULL,last_prior bytea,last_target bytea,last_payload_sha256 text,
 CHECK((last_prior IS NULL)=(last_target IS NULL)),CHECK((last_target IS NULL)=(last_payload_sha256 IS NULL)));

CREATE FUNCTION truss.runtime_feed_authorize(selected_consumer text,expected_release text,expected_digest text) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE person oid;consumer truss.runtime_feed_consumer%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;owner record;
BEGIN
 person:=truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest
 OR pg_is_in_recovery() THEN RAISE EXCEPTION 'selected authority feed profile required' USING ERRCODE='0A000';END IF;
 SELECT * INTO consumer FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer;
 IF NOT FOUND OR NOT EXISTS(WITH RECURSIVE memberships(role_oid) AS (
  SELECT person UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
  SELECT 1 FROM memberships WHERE role_oid=consumer.reader_oid) THEN
  RAISE EXCEPTION 'authorized feed consumer required' USING ERRCODE='42501';END IF;
 -- This is a complete database feed, not a role-filtered change stream.
 -- Every module in every disclosed historical document must be readable.
 FOR owner IN SELECT DISTINCT d.doc_id,m.value->>'id' AS module_id FROM truss.schema_doc d
  CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m LOOP
  IF NOT truss.runtime_can_read(owner.doc_id,owner.module_id) THEN
   RAISE EXCEPTION 'complete source authority required' USING ERRCODE='42501';END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_authorize(text,text,text) FROM PUBLIC;

-- Parallel-layout transaction configuration capture; historical intervals are never backfilled.
CREATE TABLE truss.runtime_feed_transaction_configuration (
 writer_xid xid8 PRIMARY KEY, configuration jsonb NOT NULL CHECK(jsonb_typeof(configuration)='object'));
CREATE TRIGGER runtime_feed_transaction_configuration_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.runtime_feed_transaction_configuration
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
ALTER TABLE truss.runtime_feed_transaction_configuration ENABLE ALWAYS TRIGGER runtime_feed_transaction_configuration_immutable;
CREATE FUNCTION truss.runtime_capture_feed_configuration() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE writer xid8;installation truss.catalog_runtime_installation%ROWTYPE;configuration jsonb;retained jsonb;
BEGIN
 -- Installed carriers expose their writer directly. Do not serialize the full
 -- journal event merely to extract its xid; extension carriers retain the
 -- original named-field path.
 IF TG_ARGV[0]='xid' THEN writer:=NEW.xid;
 ELSIF TG_ARGV[0]='writer_xid' THEN writer:=NEW.writer_xid;
 ELSE writer:=(to_jsonb(NEW)->>TG_ARGV[0])::xid8;
 END IF;
 IF writer IS DISTINCT FROM pg_current_xact_id() THEN RAISE EXCEPTION 'current feed fact writer required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 configuration:=jsonb_build_object('releaseId',installation.release_id,'releaseSha256',installation.release_sha256,
  'layoutProfile',installation.layout_profile,'preparationConfiguration',installation.preparation_configuration,
  'settings',(SELECT jsonb_object_agg(key,value) FROM truss.setting));
 SELECT t.configuration INTO retained FROM truss.runtime_feed_transaction_configuration t WHERE t.writer_xid=writer;
 IF FOUND THEN
  IF retained IS DISTINCT FROM configuration THEN RAISE EXCEPTION 'stable feed writer configuration required' USING ERRCODE='55000';END IF;
 ELSE
  INSERT INTO truss.runtime_feed_transaction_configuration VALUES(writer,configuration);
  SELECT t.configuration INTO retained FROM truss.runtime_feed_transaction_configuration t WHERE t.writer_xid=writer;
  IF NOT FOUND OR retained IS DISTINCT FROM configuration THEN RAISE EXCEPTION 'original feed writer configuration required' USING ERRCODE='55000';END IF;
 END IF;
 RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_capture_feed_configuration() FROM PUBLIC;
CREATE TRIGGER runtime_capture_feed_configuration AFTER INSERT ON truss.catalog_registration_request FOR EACH ROW EXECUTE FUNCTION truss.runtime_capture_feed_configuration('writer_xid');
CREATE TRIGGER runtime_capture_feed_configuration AFTER INSERT ON truss.runtime_import_source FOR EACH ROW EXECUTE FUNCTION truss.runtime_capture_feed_configuration('writer_xid');
CREATE TRIGGER runtime_capture_feed_configuration AFTER INSERT ON truss.journal
 REFERENCING NEW TABLE AS inserted_rows FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_feed_capture_configuration_statement();
CREATE TRIGGER runtime_capture_feed_configuration AFTER INSERT ON truss.runtime_feed_reservation
 REFERENCING NEW TABLE AS inserted_rows FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_feed_capture_configuration_statement();
ALTER TABLE truss.journal ENABLE ALWAYS TRIGGER runtime_capture_feed_configuration;
ALTER TABLE truss.catalog_registration_request ENABLE ALWAYS TRIGGER runtime_capture_feed_configuration;
ALTER TABLE truss.runtime_import_source ENABLE ALWAYS TRIGGER runtime_capture_feed_configuration;
ALTER TABLE truss.runtime_feed_reservation ENABLE ALWAYS TRIGGER runtime_capture_feed_configuration;
-- End parallel-layout transaction configuration capture.

CREATE FUNCTION truss.runtime_feed_cursor(selected_consumer text,next_xid text) RETURNS bytea
LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT convert_to(jsonb_build_object('profile','truss-caller-asserted-feed/0.1',
  'installationId',i.installation_id::text,'sourceEpoch',i.source_epoch::text,
  'consumerId',c.consumer_id,'registrationId',c.registration_id::text,'nextXid',next_xid)::text,'UTF8')
 FROM truss.runtime_feed_consumer c CROSS JOIN truss.runtime_current_installation() i WHERE c.consumer_id=selected_consumer;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_cursor(text,text) FROM PUBLIC;

CREATE FUNCTION truss.runtime_feed_revision(selected_revision int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' AS $$
DECLARE original_report bytea;expected_hash bytea;result jsonb;
BEGIN
 IF selected_revision>0 THEN
  SELECT r.report_bytes,q.report_sha256 INTO STRICT original_report,expected_hash
   FROM truss.catalog_acceptance_report r JOIN truss.catalog_registration_request q ON q.revision=r.rev WHERE r.rev=selected_revision;
  IF sha256(original_report) IS DISTINCT FROM expected_hash THEN RAISE EXCEPTION 'original accepted report required' USING ERRCODE='55000';END IF;
 END IF;
 SELECT jsonb_build_object('revision',r.rev::text,'record',to_jsonb(r),'documents',
  (SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.ord),'[]') FROM truss.schema_doc d WHERE d.rev=r.rev),
  'reportBytesBase64',CASE WHEN original_report IS NOT NULL THEN replace(encode(original_report,'base64'),chr(10),'') END,
  'reportSha256',encode(expected_hash,'hex')) INTO STRICT result FROM truss.schema_rev r WHERE r.rev=selected_revision;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_revision(int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_feed_page(selected_consumer text,prior_bytes bytea,frontier numeric,maximum_facts int,maximum_bytes int) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE prior jsonb;lower_xid numeric;writer xid8;next_xid numeric;changes jsonb;sources jsonb;reservations jsonb;
 revisions jsonb;prerequisites jsonb;maximum_revision int;payload bytea;result bytea;next_cursor bytea;count_facts bigint;
BEGIN
 IF maximum_facts IS NULL OR maximum_facts NOT BETWEEN 1 AND 65536 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216
 OR prior_bytes IS NULL OR octet_length(prior_bytes) NOT BETWEEN 1 AND 16384 THEN RAISE EXCEPTION 'bounded feed request required' USING ERRCODE='22023';END IF;
 IF (convert_from(prior_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'exact feed cursor required' USING ERRCODE='22023';END IF;
 prior:=convert_from(prior_bytes,'UTF8')::jsonb;
 IF jsonb_typeof(prior->'nextXid') IS DISTINCT FROM 'string' OR prior->>'nextXid' !~ '^(0|[1-9][0-9]{0,19})$' THEN RAISE EXCEPTION 'exact feed position required' USING ERRCODE='22023';END IF;
 lower_xid:=(prior->>'nextXid')::numeric;
 IF prior_bytes IS DISTINCT FROM truss.runtime_feed_cursor(selected_consumer,lower_xid::text) OR lower_xid>frontier THEN
  RAISE EXCEPTION 'current source cursor required' USING ERRCODE='55000';END IF;
 SELECT x INTO writer FROM (
  SELECT xid AS x FROM truss.journal WHERE xid>=lower_xid::text::xid8 AND xid<frontier::text::xid8
  UNION SELECT writer_xid FROM truss.catalog_registration_request WHERE writer_xid>=lower_xid::text::xid8 AND writer_xid<frontier::text::xid8
  UNION SELECT writer_xid FROM truss.runtime_import_source WHERE writer_xid>=lower_xid::text::xid8 AND writer_xid<frontier::text::xid8
  UNION SELECT writer_xid FROM truss.runtime_feed_reservation WHERE writer_xid>=lower_xid::text::xid8 AND writer_xid<frontier::text::xid8 ) required ORDER BY x LIMIT 1;
 next_xid:=CASE WHEN writer IS NULL THEN frontier ELSE writer::text::numeric+1 END;
 count_facts:=(SELECT count(*) FROM truss.journal WHERE xid=writer)+(SELECT count(*) FROM truss.runtime_import_source WHERE writer_xid=writer)
  +(SELECT count(*) FROM truss.runtime_feed_reservation WHERE writer_xid=writer)+(SELECT count(*) FROM truss.catalog_registration_request WHERE writer_xid=writer);
 IF count_facts>maximum_facts THEN RAISE EXCEPTION 'whole feed transaction exceeds fact limit' USING ERRCODE='54000';END IF;
 SELECT coalesce(jsonb_agg(to_jsonb(j) ORDER BY j.seq),'[]') INTO changes FROM truss.journal j WHERE xid=writer;
 SELECT coalesce(jsonb_agg(to_jsonb(s) ORDER BY l.entity_kind,l.entity_id),'[]') INTO sources
  FROM truss.runtime_import_source l JOIN truss.record_source s USING(entity_kind,entity_id) WHERE l.writer_xid=writer;
 SELECT coalesce(jsonb_agg(jsonb_build_object('kind',kind,'row',original_row) ORDER BY reservation_id),'[]') INTO reservations FROM truss.runtime_feed_reservation WHERE writer_xid=writer;
 SELECT coalesce(jsonb_agg(truss.runtime_feed_revision(r.rev) ORDER BY r.rev),'[]') INTO revisions
  FROM truss.schema_rev r JOIN truss.catalog_registration_request q ON q.revision=r.rev WHERE q.writer_xid=writer;
 SELECT max(rev) INTO maximum_revision FROM (
  SELECT rev FROM truss.journal WHERE xid=writer UNION SELECT revision FROM truss.catalog_registration_request WHERE writer_xid=writer) dependencies;
 -- Earlier xids may observe a catalog revision produced by a later xid.
 -- Attach the real retained prerequisites; this does not advance their writer.
 SELECT coalesce(jsonb_agg(truss.runtime_feed_revision(r.rev) ORDER BY r.rev),'[]') INTO prerequisites
  FROM truss.schema_rev r WHERE r.rev<=maximum_revision;
 count_facts:=count_facts+jsonb_array_length(prerequisites);
 IF count_facts>maximum_facts THEN RAISE EXCEPTION 'whole feed prerequisites exceed fact limit' USING ERRCODE='54000';END IF;
 next_cursor:=truss.runtime_feed_cursor(selected_consumer,next_xid::text);
 payload:=convert_to(jsonb_build_object('interfaceVersion','truss-native-feed/0.1','prior',prior,'next',convert_from(next_cursor,'UTF8')::jsonb,
  'writerXid',writer::text,'configuration',coalesce((SELECT t.configuration FROM truss.runtime_feed_transaction_configuration t WHERE t.writer_xid=writer),jsonb_build_object('releaseId',(SELECT release_id FROM truss.catalog_runtime_installation),
   'releaseSha256',(SELECT release_sha256 FROM truss.catalog_runtime_installation),
   'layoutProfile',(SELECT layout_profile FROM truss.catalog_runtime_installation),
   'preparationConfiguration',(SELECT preparation_configuration FROM truss.catalog_runtime_installation),'settings',(SELECT original_settings FROM truss.runtime_feed_configuration))),
  'catalogPrerequisites',prerequisites,'revisions',revisions,'changes',changes,'sources',sources,'reservations',reservations)::text,'UTF8');
 IF octet_length(payload)>maximum_bytes THEN RAISE EXCEPTION 'whole feed transaction exceeds byte limit' USING ERRCODE='54000';END IF;
 result:=convert_to(jsonb_build_object('outcome',CASE WHEN writer IS NULL THEN 'empty_interval' ELSE 'transaction' END,
  'consumerId',selected_consumer,'registrationId',prior->>'registrationId','writerXid',writer::text,'safeWatermarkXid',frontier::text,
  'priorBase64',replace(encode(prior_bytes,'base64'),chr(10),''),'nextBase64',replace(encode(next_cursor,'base64'),chr(10),''),
  'payloadBase64',replace(encode(payload,'base64'),chr(10),''),'sha256',encode(sha256(payload),'hex'))::text,'UTF8');
 IF octet_length(result)>maximum_bytes THEN RAISE EXCEPTION 'whole feed envelope exceeds byte limit' USING ERRCODE='54000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_feed_page(text,bytea,numeric,int,int) FROM PUBLIC;

CREATE FUNCTION truss.read_feed(selected_consumer text,maximum_facts int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE prior bytea;frontier numeric;result bytea;captured_revision int;
BEGIN
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 captured_revision:=(SELECT rev FROM truss.schema_head WHERE id=1);
 -- No xid assignment or row locks in read-only polling.
 frontier:=pg_snapshot_xmin(pg_current_snapshot())::text::numeric;
 SELECT checkpoint_bytes INTO STRICT prior FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer;
 result:=truss.runtime_feed_page(selected_consumer,prior,frontier,maximum_facts,maximum_bytes);
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 IF captured_revision IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1)
 OR prior IS DISTINCT FROM (SELECT checkpoint_bytes FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer) THEN
  RAISE EXCEPTION 'feed context changed' USING ERRCODE='55P03';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.read_feed(text,int,int,text,text) FROM PUBLIC;

CREATE FUNCTION truss.acknowledge_feed(selected_consumer text,expected_prior bytea,target bytea,payload_sha256 text,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE consumer truss.runtime_feed_consumer%ROWTYPE;result jsonb;frontier numeric;target_json jsonb;
BEGIN
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 SELECT * INTO STRICT consumer FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer FOR UPDATE NOWAIT;
 IF consumer.checkpoint_bytes=target AND consumer.last_prior=expected_prior AND consumer.last_target=target AND consumer.last_payload_sha256=payload_sha256 THEN
  RETURN convert_to(jsonb_build_object('outcome','equal','checkpointBase64',replace(encode(target,'base64'),chr(10),''))::text,'UTF8');END IF;
 IF consumer.checkpoint_bytes IS DISTINCT FROM expected_prior THEN RAISE EXCEPTION 'feed checkpoint conflict' USING ERRCODE='P1001';END IF;
 IF target IS NULL OR octet_length(target) NOT BETWEEN 1 AND 16384 OR payload_sha256 IS NULL OR payload_sha256 !~ '^[0-9a-f]{64}$'
 OR (convert_from(target,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'exact delivered boundary required' USING ERRCODE='22023';END IF;
 target_json:=convert_from(target,'UTF8')::jsonb;
 IF jsonb_typeof(target_json->'nextXid') IS DISTINCT FROM 'string' OR target_json->>'nextXid' !~ '^(0|[1-9][0-9]{0,19})$' THEN RAISE EXCEPTION 'exact delivered position required' USING ERRCODE='22023';END IF;
 frontier:=(target_json->>'nextXid')::numeric;
 IF frontier>pg_snapshot_xmin(pg_current_snapshot())::text::numeric THEN RAISE EXCEPTION 'committed interval required' USING ERRCODE='55000';END IF;
 result:=convert_from(truss.runtime_feed_page(selected_consumer,expected_prior,frontier,65536,16777216),'UTF8')::jsonb;
 IF decode(result->>'nextBase64','base64') IS DISTINCT FROM target OR result->>'sha256' IS DISTINCT FROM payload_sha256 THEN
  RAISE EXCEPTION 'complete delivered interval required' USING ERRCODE='55000';END IF;
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 IF target=expected_prior THEN
  RETURN convert_to(jsonb_build_object('outcome','equal','checkpointBase64',replace(encode(target,'base64'),chr(10),''))::text,'UTF8');END IF;
 UPDATE truss.runtime_feed_consumer SET checkpoint_bytes=target,last_prior=expected_prior,last_target=target,last_payload_sha256=payload_sha256 WHERE consumer_id=selected_consumer;
 RETURN convert_to(jsonb_build_object('outcome','advanced','checkpointBase64',replace(encode(target,'base64'),chr(10),''))::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.acknowledge_feed(text,bytea,bytea,text,text,text) FROM PUBLIC;

-- Reproduce a retained delivery after acknowledgement without moving its checkpoint.
CREATE FUNCTION truss.reread_feed(selected_consumer text,expected_prior bytea,target bytea,payload_sha256 text,
 maximum_facts int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE target_json jsonb;frontier numeric;result bytea;envelope jsonb;captured_revision int;
BEGIN
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 captured_revision:=(SELECT rev FROM truss.schema_head WHERE id=1);
 IF target IS NULL OR octet_length(target) NOT BETWEEN 1 AND 16384 OR payload_sha256 IS NULL OR payload_sha256 !~ '^[0-9a-f]{64}$'
 OR (convert_from(target,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
  RAISE EXCEPTION 'exact delivered boundary required' USING ERRCODE='22023';END IF;
 target_json:=convert_from(target,'UTF8')::jsonb;
 IF jsonb_typeof(target_json->'nextXid') IS DISTINCT FROM 'string' OR target_json->>'nextXid' !~ '^(0|[1-9][0-9]{0,19})$' THEN
  RAISE EXCEPTION 'exact delivered position required' USING ERRCODE='22023';END IF;
 frontier:=(target_json->>'nextXid')::numeric;
 IF frontier>pg_snapshot_xmin(pg_current_snapshot())::text::numeric THEN
  RAISE EXCEPTION 'committed interval required' USING ERRCODE='55000';END IF;
 result:=truss.runtime_feed_page(selected_consumer,expected_prior,frontier,maximum_facts,maximum_bytes);
 envelope:=convert_from(result,'UTF8')::jsonb;
 IF decode(envelope->>'nextBase64','base64') IS DISTINCT FROM target OR envelope->>'sha256' IS DISTINCT FROM payload_sha256 THEN
  RAISE EXCEPTION 'original complete retained interval required' USING ERRCODE='55000';END IF;
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 IF captured_revision IS DISTINCT FROM (SELECT rev FROM truss.schema_head WHERE id=1) THEN
  RAISE EXCEPTION 'feed context changed' USING ERRCODE='55P03';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.reread_feed(text,bytea,bytea,text,int,int,text,text) FROM PUBLIC;


CREATE FUNCTION truss.feed_reached(selected_consumer text,original_position bytea,maximum_evidence_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE proof jsonb;checkpoint bytea;registration uuid;position jsonb;locator jsonb;next_xid numeric;writer_xid numeric;included boolean;
BEGIN
 -- READ ONLY alone does not prove that an earlier local ACK has committed.
 IF current_setting('transaction_read_only')<>'on' OR pg_current_xact_id_if_assigned() IS NOT NULL THEN RAISE EXCEPTION 'unassigned read-only feed comparison required' USING ERRCODE='0A000';END IF;
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 proof:=convert_from(truss.reached(original_position,maximum_evidence_bytes,expected_release,expected_digest),'UTF8')::jsonb;
 IF proof->>'outcome'<>'available' THEN RETURN convert_to(proof::text,'UTF8');END IF;
 SELECT checkpoint_bytes,registration_id INTO STRICT checkpoint,registration FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer;
 IF octet_length(checkpoint) NOT BETWEEN 1 AND 16384 OR (convert_from(checkpoint,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN RAISE EXCEPTION 'original checkpoint required' USING ERRCODE='55000';END IF;
 position:=convert_from(checkpoint,'UTF8')::jsonb;locator:=convert_from(original_position,'UTF8')::jsonb;
 IF jsonb_typeof(position->'nextXid') IS DISTINCT FROM 'string' OR position->>'nextXid' !~ '^(0|[1-9][0-9]{0,19})$' THEN RAISE EXCEPTION 'canonical checkpoint position required' USING ERRCODE='55000';END IF;
 next_xid:=(position->>'nextXid')::numeric;writer_xid:=(locator->>'writerXid')::numeric;
 IF next_xid>18446744073709551615 OR checkpoint IS DISTINCT FROM truss.runtime_feed_cursor(selected_consumer,next_xid::text)
  OR position->>'registrationId' IS DISTINCT FROM registration::text THEN RAISE EXCEPTION 'current registered checkpoint required' USING ERRCODE='55000';END IF;
 included:=next_xid>writer_xid;
 -- Changed registration/checkpoint, missing evidence, or revoked authority refuses.
 proof:=convert_from(truss.reached(original_position,maximum_evidence_bytes,expected_release,expected_digest),'UTF8')::jsonb;
 IF proof->>'outcome'<>'available' THEN RETURN convert_to(proof::text,'UTF8');END IF;
 PERFORM truss.runtime_feed_authorize(selected_consumer,expected_release,expected_digest);
 IF NOT EXISTS(SELECT 1 FROM truss.runtime_feed_consumer c WHERE c.consumer_id=selected_consumer AND c.registration_id=registration AND c.checkpoint_bytes=checkpoint)
  OR pg_current_xact_id_if_assigned() IS NOT NULL THEN RAISE EXCEPTION 'unchanged committed checkpoint required' USING ERRCODE='55P03';END IF;
 RETURN convert_to(jsonb_build_object('outcome','available','included',included,'comparisonProfile','{"identity":"truss-feed-receipt-visibility","version":"0.1","sha256":"576c7cdc116552fd72448c627e3cc313734ffb87865b268bd73e628784aafd25"}'::jsonb)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.feed_reached(text,bytea,int,text,text) FROM PUBLIC;
