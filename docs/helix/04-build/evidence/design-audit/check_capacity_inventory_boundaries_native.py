"""Independent complete retained-inventory/native comparison; no authority or inventory proof."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import sys
import tempfile
import time
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
measurements=[]
with tempfile.TemporaryDirectory(prefix='truss-inventory-boundaries-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop');connections=[]
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  c=pg8000.native.Connection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=60);connections.append(c)
  version=c.run('SHOW server_version')[0][0]
  if not version.startswith('16.15'):raise ValueError('Native version mismatch')
  for p in paths[:4]:c.run(frozen[p].decode())
  c.run("SET statement_timeout='45s'");c.run("SET lock_timeout='5s'")
  layout=b'admin layout fixture';resource=b'admin framed resource fixture'
  c.run('INSERT INTO truss.row_home_capacity VALUES (1,0,0,0,0,:l,:r)',l=layout,r=resource)
  call='SELECT * FROM truss.capacity_verify_inventory_original(:l,:r)'
  def measure(name,expected,code=None):
   start=time.monotonic()
   try:actual=c.run(call,l=layout,r=resource)
   except pg8000.exceptions.DatabaseError as e:
    if code is None:raise
    expect(name,code,e.args[0]['C'])
   else:
    if code is not None:raise ValueError('Expected native boundary refusal')
    expect(name,expected,actual)
   measurements.append({'id':name,'elapsedSeconds':time.monotonic()-start,'statementTimeoutSeconds':45,'lockTimeoutSeconds':5})
  def cells(ordinal):return [s.encode() for s in ['1',str(ordinal),'mutation','application_finalized','0','0','0','0']]+[b'\x01']*8
  smallsum=sum(len(frame('operation',cells(i))) for i in range(65536))
  c.run("INSERT INTO truss.row_home_operation SELECT '1'::xid8,i,'mutation','application_finalized',0,0,0,0,decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex') FROM generate_series(0,65535) i")
  c.run('UPDATE truss.row_home_capacity SET retained_rows=65536,retained_custody_bytes=:n',n=smallsum)
  measure('exact65536-operation-rows',[[65536,smallsum]])
  c.run('BEGIN');c.run('SAVEPOINT over_rows')
  c.run("INSERT INTO truss.row_home_operation VALUES ('1'::xid8,65536,'mutation','application_finalized',0,0,0,0,decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))")
  measure('one-over65536-operation-rows',None,'54000')
  c.run('ROLLBACK TO SAVEPOINT over_rows');c.run('ROLLBACK')
  # Administrative fixture reset only; original protected cleanup is not installed.
  c.run('DELETE FROM truss.row_home_operation')
  def touchcells(owner):return [s.encode() for s in ['1','object',str(owner),'1','1','1','1']]+[None]+[b'\x01']*4
  touchsum=sum(len(frame('touch',touchcells(i))) for i in range(1,65537))
  c.run("INSERT INTO truss.row_home_touch SELECT '1'::xid8,'object',i,1,1,1,1,NULL,decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex') FROM generate_series(1,65536) i")
  c.run('UPDATE truss.row_home_capacity SET retained_rows=65536,retained_custody_bytes=:n',n=touchsum)
  measure('exact65536-touch-rows',[[65536,touchsum]])
  c.run('BEGIN');c.run('SAVEPOINT over_touch')
  c.run("INSERT INTO truss.row_home_touch VALUES ('1'::xid8,'object',65537,1,1,1,1,NULL,decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))")
  measure('one-over65536-touch-rows',None,'54000')
  c.run('ROLLBACK TO SAVEPOINT over_touch');c.run('ROLLBACK')
  c.run('DELETE FROM truss.row_home_touch WHERE owner_id>32768')
  c.run("INSERT INTO truss.row_home_operation SELECT '1'::xid8,i,'mutation','application_finalized',0,0,0,0,decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex') FROM generate_series(0,32767) i")
  mixed=sum(len(frame('operation',cells(i))) for i in range(32768))+sum(len(frame('touch',touchcells(i))) for i in range(1,32769))
  c.run('UPDATE truss.row_home_capacity SET retained_rows=65536,retained_custody_bytes=:n',n=mixed)
  measure('exact65536-mixed-families',[[65536,mixed]])
  c.run('BEGIN');c.run('SAVEPOINT over_mixed')
  c.run("INSERT INTO truss.row_home_touch VALUES ('1'::xid8,'object',32769,1,1,1,1,NULL,decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))")
  measure('one-over65536-mixed-families',None,'54000')
  c.run('ROLLBACK TO SAVEPOINT over_mixed');c.run('ROLLBACK')
  c.run('DELETE FROM truss.row_home_operation');c.run('DELETE FROM truss.row_home_touch')
  # A complete8MiB operation frame has fixed overhead plus ordinal UTF8 length.
  # Replace only original_input_bytes; do not allocate512MiB in the Python oracle.
  template=cells(0);template[1]=b'';template[10]=b''
  overhead=len(frame('operation',template));cap=8388608
  c.run("INSERT INTO truss.row_home_operation SELECT '1'::xid8,i,'mutation','application_finalized',0,0,0,0,decode('01','hex'),decode('01','hex'),convert_to(repeat('x',CAST(:cap AS integer)-CAST(:overhead AS integer)-octet_length(i::text)),'UTF8'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex') FROM generate_series(0,63) i",cap=cap,overhead=overhead)
  c.run('UPDATE truss.row_home_capacity SET retained_rows=64,retained_custody_bytes=536870912')
  measure('exact512MiB-complete-framed-bytes',[[64,536870912]])
  # Replace one complete operation with one complete touch at the same8MiB.
  touchtemplate=touchcells(1);touchtemplate[2]=b'';touchtemplate[9]=b''
  touchoverhead=len(frame('touch',touchtemplate))
  c.run('DELETE FROM truss.row_home_operation WHERE operation_ordinal=63')
  c.run("INSERT INTO truss.row_home_touch VALUES ('1'::xid8,'object',1,1,1,1,1,NULL,decode('01','hex'),convert_to(repeat('x',CAST(:n AS integer)),'UTF8'),decode('01','hex'),decode('01','hex'))",n=cap-touchoverhead-1)
  measure('exact512MiB-mixed-complete-frames',[[64,536870912]])
  c.run('BEGIN');c.run('SAVEPOINT over_bytes')
  c.run("INSERT INTO truss.row_home_operation VALUES ('1'::xid8,64,'mutation','application_finalized',0,0,0,0,decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))")
  small=len(frame('operation',cells(64)))
  c.run("UPDATE truss.row_home_operation SET original_input_bytes=substring(original_input_bytes FROM 1 FOR octet_length(original_input_bytes)-CAST(:n AS integer)) WHERE operation_ordinal=0",n=small-1)
  c.run('UPDATE truss.row_home_capacity SET retained_rows=65')
  measure('exact-one-byte-over512MiB-across65-rows',None,'54000')
  c.run('ROLLBACK TO SAVEPOINT over_bytes');c.run('ROLLBACK')
  measure('over-byte-rollback-restores-exact512MiB',[[64,536870912]])
  c.run('DELETE FROM truss.row_home_operation');c.run('DELETE FROM truss.row_home_touch')
  c.run("INSERT INTO truss.row_home_touch SELECT '1'::xid8,'object',i,1,1,1,1,NULL,decode('01','hex'),convert_to(repeat('x',CAST(:cap AS integer)-CAST(:overhead AS integer)-octet_length(i::text)),'UTF8'),decode('01','hex'),decode('01','hex') FROM generate_series(1,64) i",cap=cap,overhead=touchoverhead)
  measure('exact512MiB-touch-complete-frames',[[64,536870912]])
  c.run('BEGIN');c.run('SAVEPOINT over_touch_bytes')
  small=len(frame('touch',touchcells(65)))
  c.run("UPDATE truss.row_home_touch SET original_home_bytes=substring(original_home_bytes FROM 1 FOR octet_length(original_home_bytes)-CAST(:n AS integer)) WHERE owner_id=1",n=small-1)
  c.run("INSERT INTO truss.row_home_touch VALUES ('1'::xid8,'object',65,1,1,1,1,NULL,decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'))")
  c.run('UPDATE truss.row_home_capacity SET retained_rows=65')
  measure('exact-one-byte-over512MiB-touch-frames',None,'54000')
  c.run('ROLLBACK TO SAVEPOINT over_touch_bytes');c.run('ROLLBACK')
  measure('over-touch-byte-rollback-restores512MiB',[[64,536870912]])
 finally:
  for c in connections:c.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()):raise ValueError('Original source drift')
receipt={'scope':'Actual declared row and framed-byte boundary execution for original native inventory component; administrative compressible fixtures, not installed authority/performance qualification','serverVersion':version,'observations':checks,'measurements':measurements,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installerReady':False,'nativeFullReservationQualified':False,'acceptanceCasesPromoted':[],'limitations':['Compressible native payloads qualify framed logical bytes, not512MiB physical storage or native detoasting/copy budgets','Single run timings are descriptive, not benchmark/native-work-account qualification','No ordinary-role security/issuer/finalizer/deferred-cohort or cancellation qualification','Administrative source population/reset is not protected mutation or cleanup','Declared framed bounds cover operation, touch and mixed populations; semantic/native work profiles remain separate']}
with output.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'measurements':measurements,'installerReady':False}))
