"""Build a rollback-only native component probe from original source bytes."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
ddl = (root / 'docs/helix/04-build/evidence/layout-migration-storage.owner-export.sql').read_text()
guard = (root / 'docs/helix/04-build/evidence/layout-migration-immutability.owner-export.sql').read_text()
namespace = 'truss_migration_storage_probe'
body = """-- Synthetic parent and renamed disposable schema; no installation/commit qualification.
BEGIN;
CREATE SCHEMA truss_migration_storage_probe;
CREATE TABLE truss_migration_storage_probe.source_epoch_registry (
 installation_id text COLLATE pg_catalog."C", source_epoch text COLLATE pg_catalog."C",
 PRIMARY KEY (installation_id,source_epoch));
""" + ddl.replace('truss.', namespace + '.') + ';\n' + guard.replace('truss.', namespace + '.') + ';\n' + """
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
"""
path = root / 'docs/helix/04-build/evidence/layout-migration-storage.rollback-probe.sql'
if '--check' in sys.argv:
    if path.read_text() != body:
        raise SystemExit('stale migration storage probe')
else:
    path.write_text(body)
print('Migration storage probe source exact; native execution remains separate.')
