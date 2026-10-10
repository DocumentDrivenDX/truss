#!/usr/bin/env python3
"""Reproduce epoch-context allocator reuse; not installed epoch authority."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import subprocess
import tempfile
import pgserver
root=Path(__file__).resolve().parents[1]
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','packages/postgresql/native/source-epoch-lock.sql','packages/postgresql/native/operation-epoch-context-admission.sql','docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql']
originals=[(root/p).read_bytes() for p in paths]
assert importlib.metadata.version('pgserver')=='0.1.4'
psql=Path(str(importlib.resources.files('pgserver')))/'pginstall/bin/psql'
call="SELECT json_build_object('writerXid',writer_xid,'ordinal',ordinal,'context',convert_from(decode(context_hex,'hex'),'UTF8')::jsonb) FROM truss.runtime_admit_operation_with_epoch_context('mutation',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'),convert_to('original asserted fixture','UTF8'),convert_to('original capture profile fixture','UTF8'),'guard-fixture','guard-fixture-epoch','guard-fixture-incarnation');"
with tempfile.TemporaryDirectory(prefix='truss-operation-ordinal-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
 def query(sql):
  return subprocess.check_output([str(psql),server.get_uri(),'-X','-q','-A','-t','-v','ON_ERROR_STOP=1'],input=sql,text=True,timeout=60).strip()
 try:
  version=query('SHOW server_version;')
  result=query('BEGIN;\n'+b';\n'.join(originals[:3]).decode()+ ';\n'+originals[3].decode().split('INSERT INTO truss.row_home_operation')[0]+"INSERT INTO truss.source_epoch_current VALUES (1,'guard-fixture','guard-fixture-epoch');"+';\nSAVEPOINT operation_probe;\n'+call+'\nROLLBACK TO SAVEPOINT operation_probe;\n'+call+'\nROLLBACK;')
  observations=[json.loads(line) for line in result.splitlines()]
  assert len(observations)==2 and observations[0]['writerXid']==observations[1]['writerXid']
  assert [o['ordinal'] for o in observations]==['0','0'], 'Private counter behavior changed; review the frontier'
  for observation in observations:
   context=observation['context']
   assert context['interfaceVersion']=='truss-native-operation-context/0.4'
   assert context['xid']==observation['writerXid'] and context['ordinal']==observation['ordinal']
   assert bytes.fromhex(context['assertedOriginUtf8Hex'])==b'original asserted fixture'
   assert bytes.fromhex(context['assertedOriginCaptureProfileHex'])==b'original capture profile fixture'
   assert context['installationId']=='guard-fixture' and context['sourceEpoch']=='guard-fixture-epoch' and context['targetIncarnation']=='guard-fixture-incarnation'
   assert bytes.fromhex(context['sourceEpochProfileHex'])==b'fixture-profile'
   assert bytes.fromhex(context['sourceEpochEvidenceHex'])==b'fixture-evidence'
  assert query("SELECT to_regnamespace('truss') IS NULL;")=='t'
 finally:
  server.cleanup()
receipt={'scope':'Native reproduction of private epoch-context admission ordinal conflict and administrative fixture byte capture only; no supported executor/issuer, original artifact admission or protected mutation qualification',
 'pgserver':'0.1.4','serverVersion':version,'observations':observations,'sameNativeTopLevelTransaction':True,
 'fixtureAssertedBytesPreserved':True,'originalOriginAdmissionQualified':False,'installedEpochAuthorityQualified':False,'fixtureEpochBytesPreserved':True,'savepointRollbackReissuedOrdinal':True,'contractConformant':False,'requiredBehavior':'Consume the original executor issuer ordinal, preserve issuer nonrewind across savepoint rollback and verify original custody; never allocate from surviving registry rows',
 'rollbackRemovedNamespace':True,'sources':[{'path':p,'sha256':hashlib.sha256(b).hexdigest()} for p,b in zip(paths,originals)],
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(root/'docs/helix/04-build/evidence/design-audit/pgserver-epoch-operation-ordinal-frontier.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'serverVersion':version,'ordinals':[o['ordinal'] for o in observations],'contractConformant':False,'rollbackRemovedNamespace':True}))
