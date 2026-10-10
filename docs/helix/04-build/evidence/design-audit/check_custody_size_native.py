"""Independent complete-row size oracle/native comparison; no authority or inventory proof."""
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
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','docs/helix/04-build/evidence/design-audit/custody-codec-source.owner-export.sql','docs/helix/04-build/evidence/design-audit/custody-size-source.owner-export.sql','packages/postgresql/native/capacity-reservation/custody-codec.sql','packages/postgresql/native/capacity-reservation/custody-size.sql']
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
with tempfile.TemporaryDirectory(prefix='truss-custody-codec-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop');connections=[]
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  c=pg8000.native.Connection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=5);connections.append(c)
  version=c.run('SHOW server_version')[0][0]
  if not version.startswith('16.15'):raise ValueError('Native version mismatch')
  for p in paths[:3]:c.run(frozen[p].decode())
  blob=b'\0\xff\xc3\xa9';op=['18446744073709551615','9223372036854775807','mutation','admitted','0',None,None,None]+[blob]*7+[None]
  c.run("INSERT INTO truss.row_home_operation VALUES ('18446744073709551615'::xid8,9223372036854775807,'mutation','admitted',0,NULL,NULL,NULL,:b,:b,:b,:b,:b,:b,:b,NULL)",b=blob)
  operation_cells=[v.encode() if type(v) is str else v for v in op]
  actual=c.run('SELECT truss.custody_operation_original(o) FROM truss.row_home_operation o')[0][0]
  expect('complete-operation-size',len(frame('operation',operation_cells)),c.run('SELECT truss.custody_operation_size_original(o) FROM truss.row_home_operation o')[0][0])
  touch=['18446744073709551615','object','-9223372036854775808','2147483647','-2147483648','1','9223372036854775807',None]+[blob]*4
  c.run("INSERT INTO truss.row_home_touch VALUES ('18446744073709551615'::xid8,'object',-9223372036854775808,2147483647,-2147483648,1,9223372036854775807,NULL,:b,:b,:b,:b)",b=blob)
  touch_cells=[v.encode() if type(v) is str else v for v in touch]
  actual=c.run('SELECT truss.custody_touch_original(t) FROM truss.row_home_touch t')[0][0]
  expect('complete-touch-size',len(frame('touch',touch_cells)),c.run('SELECT truss.custody_touch_size_original(t) FROM truss.row_home_touch t')[0][0])
  cells=[None,b'']+[blob]*14
  actual=c.run("SELECT truss.custody_frame_original('operation',:cells)",cells=cells)[0][0]
  expect('null-versus-empty-and-nonutf8',frame('operation',cells).hex(),actual.hex())
  zero=[None]*16;overhead=len(frame('operation',zero));payload=8388608-overhead
  expected=frame('operation',[b'x'*payload]+[None]*15)
  row=c.run("SELECT octet_length(f),encode(sha256(f),'hex') FROM (SELECT truss.custody_frame_original('operation',ARRAY[convert_to(repeat('x',:n),'UTF8')]||array_fill(NULL::bytea,ARRAY[15])) f) q",n=payload)[0]
  expect('exact8MiB-native-framing',[8388608,hashlib.sha256(expected).hexdigest()],row)
  def refusal(name,code,sql,**args):
   c.run('BEGIN');c.run('SAVEPOINT refusal')
   try:c.run(sql,**args)
   except pg8000.exceptions.DatabaseError as e:expect(name,code,e.args[0]['C'])
   else:raise ValueError('Expected native refusal: '+name)
   c.run('ROLLBACK TO SAVEPOINT refusal');c.run('ROLLBACK')
  refusal('one-over8MiB','54000',"SELECT truss.custody_frame_original('operation',ARRAY[convert_to(repeat('x',:n),'UTF8')]||array_fill(NULL::bytea,ARRAY[15]))",n=payload+1)
  refusal('missing-cell','22023',"SELECT truss.custody_frame_original('operation',array_fill(NULL::bytea,ARRAY[15]))")
  refusal('multidimensional-cells','22023',"SELECT truss.custody_frame_original('operation',array_fill(NULL::bytea,ARRAY[4,4]))")
  refusal('foreign-array-origin','22023',"SELECT truss.custody_frame_original('operation',array_fill(NULL::bytea,ARRAY[16],ARRAY[0]))")
  refusal('unknown-kind','22023',"SELECT truss.custody_frame_original('unknown',array_fill(NULL::bytea,ARRAY[16]))")
  refusal('absent-operation-row','22023','SELECT truss.custody_operation_original(NULL::truss.row_home_operation)')
  refusal('absent-touch-row','22023','SELECT truss.custody_touch_original(NULL::truss.row_home_touch)')
  expect('length-only-exact8MiB',8388608,c.run("SELECT truss.custody_size_original('operation',ARRAY[CAST(:n AS integer)]||array_fill(NULL::integer,ARRAY[15]))",n=payload)[0][0])
  refusal('length-only-one-over','54000',"SELECT truss.custody_size_original('operation',ARRAY[CAST(:n AS integer)]||array_fill(NULL::integer,ARRAY[15]))",n=payload+1)
  refusal('negative-length','22023',"SELECT truss.custody_size_original('operation',ARRAY[-1]||array_fill(NULL::integer,ARRAY[15]))")
  refusal('max-int-length-no-overflow','54000',"SELECT truss.custody_size_original('operation',ARRAY[2147483647]||array_fill(NULL::integer,ARRAY[15]))")
  refusal('missing-length','22023',"SELECT truss.custody_size_original('operation',array_fill(NULL::integer,ARRAY[15]))")
  refusal('multidimensional-lengths','22023',"SELECT truss.custody_size_original('operation',array_fill(NULL::integer,ARRAY[4,4]))")
  refusal('foreign-length-origin','22023',"SELECT truss.custody_size_original('operation',array_fill(NULL::integer,ARRAY[16],ARRAY[0]))")
  # Build large bytes natively; return only complete size. Oracle includes every
  # other original cell, not just the new carrier's length.
  oldsize=len(frame('operation',operation_cells));large=8388608-oldsize+len(blob)
  c.run("UPDATE truss.row_home_operation SET original_input_bytes=convert_to(repeat('x',:n),'UTF8')",n=large)
  expect('actual-stored-row-exact8MiB-size',8388608,c.run('SELECT truss.custody_operation_size_original(o) FROM truss.row_home_operation o')[0][0])
  c.run("UPDATE truss.row_home_operation SET original_input_bytes=original_input_bytes||decode('00','hex')")
  refusal('actual-stored-row-one-over','54000','SELECT truss.custody_operation_size_original(o) FROM truss.row_home_operation o')
  c.run('CREATE ROLE custody_size_ordinary')
  c.run('GRANT USAGE ON SCHEMA truss TO custody_size_ordinary')
  signatures=['truss.custody_size_original(text,integer[])','truss.custody_operation_size_original(truss.row_home_operation)','truss.custody_touch_size_original(truss.row_home_touch)']
  for signature in signatures:expect('private-execute-'+signature,False,c.run("SELECT has_function_privilege('custody_size_ordinary',:s,'EXECUTE')",s=signature)[0][0])
  c.run('ALTER TABLE truss.row_home_operation ADD COLUMN unexpected_original bytea')
  refusal('unmapped-native-column','55000','SELECT truss.custody_operation_size_original(o) FROM truss.row_home_operation o')
 finally:
  for c in connections:c.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()):raise ValueError('Original source drift')
receipt={'scope':'Native complete fixed-row byte sizing against independent Python oracle; synthetic administrative rows, not accepted semantic data or complete inventory/account proof','serverVersion':version,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installerReady':False,'nativeFullReservationQualified':False,'acceptanceCasesPromoted':[],'limitations':['No full original source/security/issuer/event/retained inventory or physical storage overhead proof','Framing bytes include all native cell representations and explicit overhead; not tuple/index/WAL size','8MiB tests observe only internal length/hash or length-only scalar, not qualified8MiB driver transport','No complete native argument allocation/repeated-copy/work/cancellation budget qualification','Administrative negative IDs/opaque carriers are codec images, not admitted graph values']}
with output.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'installerReady':False}))
