-- Synthetic parent and renamed disposable schema; no installation/commit qualification.
BEGIN;
CREATE SCHEMA truss_migration_storage_probe;
CREATE TABLE truss_migration_storage_probe.source_epoch_registry (
 installation_id text COLLATE pg_catalog."C", source_epoch text COLLATE pg_catalog."C",
 PRIMARY KEY (installation_id,source_epoch));
CREATE SEQUENCE truss_migration_storage_probe.layout_migration_receipt_row_seq AS bigint MINVALUE 1 MAXVALUE 9223372036854775807 START 1 NO CYCLE; CREATE TABLE truss_migration_storage_probe.layout_migration_receipt (storage_row_id bigint PRIMARY KEY DEFAULT nextval('truss_migration_storage_probe.layout_migration_receipt_row_seq'), installation_id text NOT NULL COLLATE pg_catalog."C", original_source_epoch text NOT NULL COLLATE pg_catalog."C", original_target_incarnation text NOT NULL CHECK (octet_length(original_target_incarnation) BETWEEN 1 AND 1024) COLLATE pg_catalog."C", original_attempt_identity_bytes bytea NOT NULL CHECK (octet_length(original_attempt_identity_bytes) BETWEEN 1 AND 1024), receipt_profile_bytes bytea NOT NULL CHECK (octet_length(receipt_profile_bytes) BETWEEN 1 AND 65536), original_request_bytes bytea NOT NULL CHECK (octet_length(original_request_bytes) > 0), original_receipt_bytes bytea NOT NULL CHECK (octet_length(original_receipt_bytes) > 0), original_attempt_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(original_attempt_identity_bytes)) STORED, original_request_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(original_request_bytes)) STORED, original_receipt_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(original_receipt_bytes)) STORED, CHECK (storage_row_id > 0), CHECK ((octet_length(original_request_bytes)::bigint + octet_length(original_receipt_bytes)::bigint) <= 16777216), FOREIGN KEY (installation_id, original_source_epoch) REFERENCES truss_migration_storage_probe.source_epoch_registry (installation_id, source_epoch) ON DELETE RESTRICT); CREATE INDEX layout_migration_receipt_attempt_route ON truss_migration_storage_probe.layout_migration_receipt USING btree (installation_id, original_attempt_sha256, storage_row_id); REVOKE ALL ON truss_migration_storage_probe.layout_migration_receipt, truss_migration_storage_probe.layout_migration_receipt_row_seq FROM public;
CREATE FUNCTION truss_migration_storage_probe.runtime_immutable_layout_migration_receipt() RETURNS trigger LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
BEGIN
 IF TG_RELID<>'truss_migration_storage_probe.layout_migration_receipt'::regclass OR TG_NARGS<>0
  OR TG_WHEN<>'BEFORE' OR NOT ((TG_LEVEL='ROW' AND TG_OP IN ('UPDATE','DELETE'))
   OR (TG_LEVEL='STATEMENT' AND TG_OP='TRUNCATE')) THEN
  RAISE EXCEPTION 'unregistered migration receipt event' USING ERRCODE='55000';
 END IF;
 RAISE EXCEPTION 'original migration receipt is immutable; cleanup unavailable' USING ERRCODE='55000';
END;
$$; REVOKE ALL ON FUNCTION truss_migration_storage_probe.runtime_immutable_layout_migration_receipt() FROM public; CREATE TRIGGER runtime_layout_migration_receipt_immutable BEFORE DELETE OR UPDATE ON truss_migration_storage_probe.layout_migration_receipt FOR EACH ROW EXECUTE FUNCTION truss_migration_storage_probe.runtime_immutable_layout_migration_receipt(); ALTER TABLE truss_migration_storage_probe.layout_migration_receipt ENABLE ALWAYS TRIGGER runtime_layout_migration_receipt_immutable; CREATE TRIGGER runtime_layout_migration_receipt_no_truncate BEFORE TRUNCATE ON truss_migration_storage_probe.layout_migration_receipt EXECUTE FUNCTION truss_migration_storage_probe.runtime_immutable_layout_migration_receipt(); ALTER TABLE truss_migration_storage_probe.layout_migration_receipt ENABLE ALWAYS TRIGGER runtime_layout_migration_receipt_no_truncate;

INSERT INTO truss_migration_storage_probe.source_epoch_registry VALUES ('installation','source');
INSERT INTO truss_migration_storage_probe.layout_migration_receipt
 (installation_id,original_source_epoch,original_target_incarnation,original_attempt_identity_bytes,
 receipt_profile_bytes,original_request_bytes,original_receipt_bytes)
 VALUES ('installation','source','incarnation',decode('617474656d7074','hex'),decode('01','hex'),decode('0203','hex'),decode('0405','hex'));
DO $$
DECLARE mode text; statement text;
BEGIN
 IF (SELECT count(*) FROM pg_attribute WHERE attrelid='truss_migration_storage_probe.layout_migration_receipt'::regclass AND attnum>0 AND NOT attisdropped)<>11 THEN RAISE EXCEPTION 'columns'; END IF;
 IF (SELECT count(*) FROM pg_constraint WHERE conrelid='truss_migration_storage_probe.layout_migration_receipt'::regclass AND contype='f')<>1 THEN RAISE EXCEPTION 'foreign keys'; END IF;
 IF (SELECT count(*) FROM pg_attribute WHERE attrelid='truss_migration_storage_probe.layout_migration_receipt'::regclass AND attgenerated='s')<>3 THEN RAISE EXCEPTION 'generated hashes'; END IF;
 IF has_table_privilege('public','truss_migration_storage_probe.layout_migration_receipt','INSERT') THEN RAISE EXCEPTION 'PUBLIC INSERT'; END IF;
 IF EXISTS (SELECT FROM truss_migration_storage_probe.layout_migration_receipt WHERE original_attempt_sha256<>sha256(original_attempt_identity_bytes) OR original_request_sha256<>sha256(original_request_bytes) OR original_receipt_sha256<>sha256(original_receipt_bytes)) THEN RAISE EXCEPTION 'hash mismatch'; END IF;
 IF (SELECT count(*) FROM pg_trigger WHERE tgrelid='truss_migration_storage_probe.layout_migration_receipt'::regclass AND NOT tgisinternal AND tgenabled='A')<>2 THEN RAISE EXCEPTION 'always guards'; END IF;
 FOREACH mode IN ARRAY ARRAY['origin','replica'] LOOP
  PERFORM set_config('session_replication_role',mode,true);
  FOREACH statement IN ARRAY ARRAY[
   'UPDATE truss_migration_storage_probe.layout_migration_receipt SET original_receipt_bytes=decode(''ff'',''hex'')',
   'UPDATE truss_migration_storage_probe.layout_migration_receipt SET original_request_bytes=decode(''ff'',''hex'')',
   'UPDATE truss_migration_storage_probe.layout_migration_receipt SET original_attempt_identity_bytes=decode(''ff'',''hex'')',
   'DELETE FROM truss_migration_storage_probe.layout_migration_receipt',
   'TRUNCATE truss_migration_storage_probe.layout_migration_receipt'] LOOP
   BEGIN
    EXECUTE statement;
    RAISE EXCEPTION 'mutation did not refuse: % / %',mode,statement USING ERRCODE='P0001';
   EXCEPTION WHEN SQLSTATE '55000' THEN NULL;
   END;
  END LOOP;
 END LOOP;
 PERFORM set_config('session_replication_role','origin',true);
 IF (SELECT count(*) FROM truss_migration_storage_probe.layout_migration_receipt)<>1 OR EXISTS (SELECT FROM truss_migration_storage_probe.layout_migration_receipt WHERE original_request_bytes<>decode('0203','hex') OR original_receipt_bytes<>decode('0405','hex') OR original_attempt_identity_bytes<>decode('617474656d7074','hex')) THEN RAISE EXCEPTION 'original bytes changed'; END IF;
 BEGIN
  DELETE FROM truss_migration_storage_probe.source_epoch_registry;
  RAISE EXCEPTION 'parent deletion did not refuse';
 EXCEPTION WHEN foreign_key_violation THEN NULL;
 END;
END;
$$;
SAVEPOINT original_pending_receipt;
INSERT INTO truss_migration_storage_probe.layout_migration_receipt
 (installation_id,original_source_epoch,original_target_incarnation,original_attempt_identity_bytes,
 receipt_profile_bytes,original_request_bytes,original_receipt_bytes)
 VALUES ('installation','source','incarnation',decode('617474656d7074','hex'),decode('01','hex'),decode('0203','hex'),decode('0405','hex'));
DO $$ BEGIN
 IF (SELECT count(*) FROM truss_migration_storage_probe.layout_migration_receipt)<>2 THEN RAISE EXCEPTION 'nonunique route unexpectedly deduplicated'; END IF;
END $$;
ROLLBACK TO SAVEPOINT original_pending_receipt;
DO $$ BEGIN
 IF (SELECT count(*) FROM truss_migration_storage_probe.layout_migration_receipt)<>1 THEN RAISE EXCEPTION 'pending rollback failed'; END IF;
END $$;
ROLLBACK;
SELECT to_regclass('truss_migration_storage_probe.layout_migration_receipt') IS NULL AS rollback_removed_home;
