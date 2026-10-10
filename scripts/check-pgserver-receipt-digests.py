"""Populated receipt byte/digest component; fixtures are not admitted migration artifacts."""
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
values=[b'\x00\xff\x00',bytes(range(256)),'é'.encode(),'e\u0301'.encode(),b'{"exact":"9007199254740993","scale":"1.2300"}\r\n']
expected=[];statements=[]
for index,value in enumerate(values):
    attempt=b'binary-fixture-'+str(index).encode()
    request=value;receipt=value[::-1]
    statement="INSERT INTO truss.layout_migration_receipt(installation_id,original_source_epoch,original_target_incarnation,original_attempt_identity_bytes,receipt_profile_bytes,original_request_bytes,original_receipt_bytes) VALUES ('guard-fixture','guard-fixture-epoch','guard-fixture-incarnation',decode('%s','hex'),convert_to('binary-fixture-profile','UTF8'),decode('%s','hex'),decode('%s','hex'));"
    statements.append(statement%(attempt.hex(),request.hex(),receipt.hex()))
    expected.append([attempt.hex(),request.hex(),receipt.hex(),hashlib.sha256(attempt).hexdigest(),hashlib.sha256(request).hexdigest(),hashlib.sha256(receipt).hexdigest()])
expected.sort()
probe="""
DO $$ BEGIN
 BEGIN
  INSERT INTO truss.layout_migration_receipt(original_attempt_sha256) VALUES (decode('00','hex'));
  RAISE EXCEPTION 'explicit generated digest unexpectedly accepted';
 EXCEPTION WHEN SQLSTATE '428C9' THEN NULL;
 END;
 IF (SELECT count(*) FROM truss.layout_migration_receipt)<>6 THEN
  RAISE EXCEPTION 'unexpected receipt fixture effects';
 END IF;
END $$;
SELECT json_agg(json_build_array(encode(original_attempt_identity_bytes,'hex'),encode(original_request_bytes,'hex'),encode(original_receipt_bytes,'hex'),encode(original_attempt_sha256,'hex'),encode(original_request_sha256,'hex'),encode(original_receipt_sha256,'hex')) ORDER BY encode(original_attempt_identity_bytes,'hex')) FROM truss.layout_migration_receipt WHERE original_attempt_identity_bytes<>convert_to('fixture-attempt','UTF8');
ROLLBACK;
"""
assert importlib.metadata.version('pgserver')=='0.1.4'
psql=Path(str(importlib.resources.files('pgserver')))/'pginstall/bin/psql'
with tempfile.TemporaryDirectory(prefix='truss-receipt-digests-') as directory:
    server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
    def query(sql):
        return subprocess.check_output([str(psql),server.get_uri(),'-X','-q','-A','-t','-v','ON_ERROR_STOP=1'],input=sql,text=True,timeout=60).strip()
    try:
        version=query('SHOW server_version;');assert version=='16.2'
        observed=json.loads(query('BEGIN;\n'+b';\n'.join(originals).decode()+';\n'+'\n'.join(statements)+'\n'+probe))
        assert observed==expected
        assert expected[2][1]!=expected[3][1] and expected[2][4]!=expected[3][4]
        assert query("SELECT to_regnamespace('truss') IS NULL;")=='t'
    finally:server.cleanup()
receipt=dict(scope='Five populated administrative byte/digest fixture cases and explicit generated-column refusal; not original receipt/migration producer qualification',serverVersion=version,expected=expected,observed=observed,explicitGeneratedValueSqlstate='428C9',receiptRowsAfterRefusal=6,rollbackRemovedNamespace=True,sources={p:hashlib.sha256(b).hexdigest() for p,b in zip(paths,originals)},producerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limitations=['Synthetic nonempty binary payloads are not admitted request/receipt encodings','No protected producer/current-person authority, migration execution or installed readiness','Digest routes never substitute for full original byte equality','Other generated homes remain separately unqualified'])
(root/'docs/helix/04-build/evidence/design-audit/pgserver-receipt-digest-component.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(serverVersion=version,cases=len(values),digestComparisons=15,explicitGeneratedRefusal=True,rollbackRemovedNamespace=True)))
