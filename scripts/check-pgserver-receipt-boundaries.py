"""Receipt byte-boundary component; fixtures are not admitted migration artifacts."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import subprocess
import tempfile
import pgserver
root=Path(__file__).resolve().parents[1]
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql','docs/helix/04-build/evidence/layout-migration-storage.owner-export.sql','packages/postgresql/native/operation-configuration-immutability.sql','packages/postgresql/native/layout-migration-receipt-immutability.sql','docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql']
originals=[(root/p).read_bytes() for p in paths]
probe="""
DO $$
DECLARE failure text; before_count bigint;
BEGIN
 SELECT count(*) INTO before_count FROM truss.layout_migration_receipt;
 FOREACH failure IN ARRAY ARRAY['empty-attempt','large-attempt','empty-profile','large-profile','empty-request','empty-receipt','aggregate-over'] LOOP
  BEGIN
   INSERT INTO truss.layout_migration_receipt(installation_id,original_source_epoch,original_target_incarnation,original_attempt_identity_bytes,receipt_profile_bytes,original_request_bytes,original_receipt_bytes)
   VALUES ('guard-fixture','guard-fixture-epoch','guard-fixture-incarnation',
    CASE failure WHEN 'empty-attempt' THEN decode('','hex') WHEN 'large-attempt' THEN decode(repeat('61',1025),'hex') ELSE convert_to('boundary-negative','UTF8') END,
    CASE failure WHEN 'empty-profile' THEN decode('','hex') WHEN 'large-profile' THEN decode(repeat('61',65537),'hex') ELSE convert_to('boundary-profile','UTF8') END,
    CASE failure WHEN 'empty-request' THEN decode('','hex') WHEN 'aggregate-over' THEN decode(repeat('61',8388609),'hex') ELSE decode('61','hex') END,
    CASE failure WHEN 'empty-receipt' THEN decode('','hex') WHEN 'aggregate-over' THEN decode(repeat('62',8388608),'hex') ELSE decode('62','hex') END);
   RAISE EXCEPTION 'receipt bound unexpectedly admitted: %',failure;
  EXCEPTION WHEN SQLSTATE '23514' THEN NULL;
  END;
  IF (SELECT count(*) FROM truss.layout_migration_receipt)<>before_count THEN
   RAISE EXCEPTION 'refused receipt inserted a row';
  END IF;
 END LOOP;
END $$;
INSERT INTO truss.layout_migration_receipt(installation_id,original_source_epoch,original_target_incarnation,original_attempt_identity_bytes,receipt_profile_bytes,original_request_bytes,original_receipt_bytes)
VALUES ('guard-fixture','guard-fixture-epoch','guard-fixture-incarnation',decode(repeat('61',1024),'hex'),decode(repeat('62',65536),'hex'),decode(repeat('61',8388608),'hex'),decode(repeat('62',8388608),'hex'));
SELECT json_build_array(octet_length(original_attempt_identity_bytes),octet_length(receipt_profile_bytes),octet_length(original_request_bytes),octet_length(original_receipt_bytes),encode(original_request_sha256,'hex'),encode(original_receipt_sha256,'hex'),(SELECT count(*) FROM truss.layout_migration_receipt)) FROM truss.layout_migration_receipt WHERE octet_length(original_attempt_identity_bytes)=1024;
ROLLBACK;
"""
expected=[1024,65536,8388608,8388608,hashlib.sha256(b'a'*8388608).hexdigest(),hashlib.sha256(b'b'*8388608).hexdigest(),2]
assert importlib.metadata.version('pgserver')=='0.1.4'
psql=Path(str(importlib.resources.files('pgserver')))/'pginstall/bin/psql'
with tempfile.TemporaryDirectory(prefix='truss-receipt-digests-') as directory:
    server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
    def query(sql):
        return subprocess.check_output([str(psql),server.get_uri(),'-X','-q','-A','-t','-v','ON_ERROR_STOP=1'],input=sql,text=True,timeout=60).strip()
    try:
        version=query('SHOW server_version;');assert version=='16.2'
        observed=json.loads(query('BEGIN;\n'+b';\n'.join(originals).decode()+';\n'+probe))
        assert observed==expected
        assert query("SELECT to_regnamespace('truss') IS NULL;")=='t'
    finally:server.cleanup()
receipt=dict(scope='Administrative receipt byte-boundary controls only; not original receipt/migration producer qualification',serverVersion=version,expected=expected,observed=observed,refusalSqlstate='23514',negativeControls=7,exactAggregateBytes=16777216,receiptRowsAfterSuccessfulBoundary=2,rollbackRemovedNamespace=True,sources={p:hashlib.sha256(b).hexdigest() for p,b in zip(paths,originals)},producerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limitations=['Synthetic nonempty binary payloads are not admitted request/receipt encodings','No protected producer/current-person authority, migration execution or installed readiness','Digest routes never substitute for full original byte equality','Other generated homes remain separately unqualified'])
(root/'docs/helix/04-build/evidence/design-audit/pgserver-receipt-boundary-component.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(serverVersion=version,negativeControls=7,exactAggregateBytes=16777216,rollbackRemovedNamespace=True)))
