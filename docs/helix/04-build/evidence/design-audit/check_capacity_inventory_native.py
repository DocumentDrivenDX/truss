"""Independent complete retained-inventory/native comparison; no authority or inventory proof."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import sys
import tempfile
from urllib.parse import urlparse,parse_qs
import pg8000.native
import pg8000.exceptions
import pgserver
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):raise SystemExit('Fresh receipt basename required')
output=HERE/sys.argv[1]
if output.exists():raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':raise SystemExit('Original runtime/driver required')
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','docs/helix/04-build/evidence/design-audit/custody-codec-source.owner-export.sql','docs/helix/04-build/evidence/design-audit/custody-size-source.owner-export.sql','docs/helix/04-build/evidence/design-audit/capacity-inventory-source.owner-export.sql','packages/postgresql/native/capacity-reservation/inventory.sql']
frozen={p:(ROOT/p).read_bytes() for p in paths};checks=[]
def expect(name,expected,actual):
 if expected!=actual:raise ValueError(name+': native/oracle mismatch')
 checks.append({'id':name,'expected':expected,'observed':actual})
def frame(kind,cells):
 out=('truss.custody.'+kind+'/0.1').encode()+b'\0'+struct.pack('>H',len(cells))
 for cell in cells:
  if cell is None:out+=b'\0'+struct.pack('>Q',0)
  else:out+=b'\1'+struct.pack('>Q',len(cell))+cell
 return out
with tempfile.TemporaryDirectory(prefix='truss-capacity-inventory-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop');connections=[]
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  c=pg8000.native.Connection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=5);connections.append(c)
  version=c.run('SHOW server_version')[0][0]
  if not version.startswith('16.15'):raise ValueError('Native version mismatch')
  for p in paths[:4]:c.run(frozen[p].decode())
  layout=b'admin layout fixture';resource=b'admin framed resource fixture';blob=b'\0\xff'
  c.run('INSERT INTO truss.row_home_capacity VALUES (1,0,0,0,0,:l,:r)',l=layout,r=resource)
  def verify():return c.run('SELECT * FROM truss.capacity_verify_inventory_original(:l,:r)',l=layout,r=resource)
  def refusal(name,code,sql,**args):
   c.run('BEGIN');c.run('SAVEPOINT refusal')
   try:c.run(sql,**args)
   except pg8000.exceptions.DatabaseError as e:expect(name,code,e.args[0]['C'])
   else:raise ValueError('Expected native refusal: '+name)
   c.run('ROLLBACK TO SAVEPOINT refusal');c.run('ROLLBACK')
  call='SELECT * FROM truss.capacity_verify_inventory_original(:l,:r)'
  expect('empty-complete-inventory',[[0,0]],verify())
  refusal('foreign-resource','55000',call,l=layout,r=b'foreign')
  operation=['1','0','mutation','application_finalized','0','0','0','0']
  operation_cells=[s.encode() for s in operation]+[blob]*8
  first=len(frame('operation',operation_cells))
  c.run("INSERT INTO truss.row_home_operation VALUES ('1'::xid8,0,'mutation','application_finalized',0,0,0,0,:b,:b,:b,:b,:b,:b,:b,:b)",b=blob)
  refusal('unaccounted-finalized-foreign-xid','55000',call,l=layout,r=resource)
  c.run('UPDATE truss.row_home_capacity SET retained_rows=1,retained_custody_bytes=:n',n=first)
  expect('finalized-foreign-xid-included',[[1,first]],verify())
  secondcells=[s.encode() for s in ['2','7','mutation','admitted','0']]+[None]*3+[blob]*7+[None]
  second=len(frame('operation',secondcells))
  c.run("INSERT INTO truss.row_home_operation VALUES ('2'::xid8,7,'mutation','admitted',0,NULL,NULL,NULL,:b,:b,:b,:b,:b,:b,:b,NULL)",b=blob)
  refusal('unfinished-foreign-xid-not-skipped','55000',call,l=layout,r=resource)
  touchcells=[s.encode() for s in ['3','object','1','1','1','1','1']]+[None]+[blob]*4
  third=len(frame('touch',touchcells))
  c.run("INSERT INTO truss.row_home_touch VALUES ('3'::xid8,'object',1,1,1,1,1,NULL,:b,:b,:b,:b)",b=blob)
  total=first+second+third
  c.run('UPDATE truss.row_home_capacity SET retained_rows=3,retained_custody_bytes=:n',n=total)
  expect('all-phases-all-xids-both-families',[[3,total]],verify())
  c.run('BEGIN');c.run('SAVEPOINT changed')
  c.run("UPDATE truss.row_home_operation SET original_input_bytes=original_input_bytes||decode('00','hex') WHERE original_writer_xid='1'::xid8")
  try:verify()
  except pg8000.exceptions.DatabaseError as e:expect('growth-byte-mismatch','55000',e.args[0]['C'])
  else:raise ValueError('Expected growth mismatch')
  c.run('ROLLBACK TO SAVEPOINT changed');expect('rollback-restores-full-parity',[[3,total]],verify());c.run('ROLLBACK')
  c.run('UPDATE truss.row_home_capacity SET retained_rows=2')
  refusal('row-count-mismatch','55000',call,l=layout,r=resource)
  c.run('UPDATE truss.row_home_capacity SET retained_rows=3')
  c.run('DELETE FROM truss.row_home_touch')
  refusal('removed-member-mismatch','55000',call,l=layout,r=resource)
  c.run('UPDATE truss.row_home_capacity SET retained_rows=2,retained_custody_bytes=:n',n=first+second)
  expect('administrative-cleanup-recount',[[2,first+second]],verify())
  c.run('ALTER TABLE truss.row_home_operation ENABLE ROW LEVEL SECURITY')
  refusal('rls-refused-even-superuser','55000',call,l=layout,r=resource)
  c.run('ALTER TABLE truss.row_home_operation DISABLE ROW LEVEL SECURITY')
  c.run('CREATE ROLE inventory_ordinary')
  expect('public-execute-revoked',False,c.run("SELECT has_function_privilege('inventory_ordinary','truss.capacity_verify_inventory_original(bytea,bytea)','EXECUTE')")[0][0])
  c.run('ALTER TABLE truss.row_home_touch ADD COLUMN unmapped bytea')
  refusal('unmapped-empty-family-column','55000',call,l=layout,r=resource)
 finally:
  for c in connections:c.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()):raise ValueError('Original source drift')
receipt={'scope':'Complete native operation/touch framed-size parity under administrative fixtures; not protected source/authority or installed resource qualification','serverVersion':version,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installerReady':False,'nativeFullReservationQualified':False,'acceptanceCasesPromoted':[],'limitations':['All protected writers must participate in original head/ledger exclusion; administrative bypass not contained','Original installed identities/dependencies/roles/resource-profile adoption remain external','Size parity is not byte-content, source meaning, issuer/security/finalizer authority','No native work/cancellation/full65536-row or512MiB qualification','Administrative markers and rows do not establish accepted profiles or public cleanup']}
with output.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'installerReady':False}))
