"""Original native registry read -> private Python correspondence, administrative fixture only."""
import hashlib, importlib.metadata, json, socket, sys, tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import pg8000.core, pgserver
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'packages/python/src'));sys.path.insert(0,str(ROOT/'packages/python/tests'))
from truss._accounted_receive import AccountedReceiver
from truss._resource_account import BytePermitAccount
from truss._operation_registry import COLUMNS
from truss._row_operation_address import encode_row_operation_address
from truss._row_operation_custody import decode_row_operation_custody
from truss._row_registry_correspondence import check_registry_correspondence
from pg8000_accounted_instance_candidate import AccountedSocket
from pg8000_original_control_candidate import OriginalControlConnection
from test_row_registry_correspondence import fixture
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):raise SystemExit('Fresh receipt basename required')
out=HERE/sys.argv[1]
if out.exists():raise SystemExit('Receipt exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':raise SystemExit('Pinned runtime required')
if hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest()!='cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26':raise SystemExit('Pinned driver source required')
paths=['docs/helix/02-design/contracts/row-home-operation-v0.1.proposal.sql','docs/helix/02-design/contracts/row-operation-registry-observation-v0.1.proposal.sql']
paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'packages/python/src/truss').glob('*.py'))]
paths += ['packages/python/tests/'+p for p in ['test_row_registry_correspondence.py','test_row_operation_context.py','test_row_operation_custody.py','test_row_group_custody.py']]
paths += ['docs/helix/04-build/evidence/design-audit/'+p for p in ['pg8000_original_control_candidate.py','pg8000_instance_candidate.py','pg8000_accounted_instance_candidate.py','python_pg_receive_candidate.py','python_pg_frame_candidate.py']]
frozen={p:(ROOT/p).read_bytes() for p in paths}
query=frozen[paths[1]].decode();registry_sql=query[query.index('SELECT\n'):]
checks=[];captures=[];connection=None;supplied=None
with tempfile.TemporaryDirectory(prefix='truss-registry-correspondence-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
 try:
  uri=urlparse(server.get_uri());options=parse_qs(uri.query);host=options.get('host',[uri.hostname])[0];port=int(options.get('port',[uri.port or 5432])[0])
  transport=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);transport.settimeout(10);transport.connect(str(Path(host)/f'.s.PGSQL.{port}'))
  producer=object();account=BytePermitAccount(producer,134217728,268435456,16384)
  supplied=AccountedSocket(transport,account,producer)
  supplied.file.receiver=AccountedReceiver(transport,account,producer,frame_bytes=1048576,total_bytes=33554432,messages=1024,reads=100000)
  supplied.file.remaining_writes=1024;supplied.file.remaining_send_bytes=16777216
  connection=OriginalControlConnection(user='postgres',database='postgres',sock=supplied,ssl_context=False,startup_params={'client_encoding':'UTF8'})
  version=connection.parameter_statuses['server_version']
  if version!='16.15':raise ValueError('Native version mismatch')
  def cells(result):return [[None if v is None else v.decode('ascii') for v in row] for row in result.rows]
  result=connection.execute_simple('SELECT pg_catalog.pg_current_xact_id_if_assigned()::text')
  if cells(result)!=[[None]]:raise ValueError('Observation assigned xid')
  checks.append({'id':'unassigned-xid-remains-null'})
  connection.execute_simple('CREATE SCHEMA truss')
  connection.execute_simple(frozen[paths[0]].decode())
  connection.execute_simple('BEGIN')
  xid=cells(connection.execute_simple('SELECT pg_catalog.pg_current_xact_id()::text'))[0][0]
  body,rows=fixture()
  for entry in body['operations']:
   ordinal=json.loads(entry['operationIdentity'])[3]
   entry['operationIdentity']=entry['nativeGroupCustodyIdentity']=encode_row_operation_address('fixture',xid,ordinal).decode()
  for row in rows:
   row[0]=xid
   context=json.loads(bytes.fromhex(row[8]));context['originalWriterXid']=xid;row[8]=json.dumps(context).encode().hex()
   group=json.loads(bytes.fromhex(row[14]));group['operationIdentity']=encode_row_operation_address('fixture',xid,row[1]).decode();row[14]=json.dumps(group).encode().hex()
  manifest=decode_row_operation_custody(json.dumps(body,indent=2).encode())
  def insert(row):
   values=[]
   for i,v in enumerate(row):
    if v is None:values.append('NULL')
    elif i>=8:values.append("decode('"+v+"','hex')")
    else:values.append("'"+v+"'")
   connection.execute_simple('INSERT INTO truss.row_home_operation VALUES ('+','.join(values)+')')
  for row in rows:insert(row)
  foreign=rows[0].copy();foreign[0]=str(int(xid)+1);insert(foreign)
  def capture():
   start=len(connection.original_controls);result=connection.execute_simple(registry_sql)
   names=tuple(c.name.decode('ascii') for c in result.columns)
   descriptor=[{'name':c.name.decode('ascii'),'typeOid':c.type_oid,'format':c.format} for c in result.columns]
   if names!=COLUMNS or any(c.type_oid!=25 or c.format!=0 for c in result.columns):raise ValueError('Original descriptor mismatch')
   if connection._ready_status!=b'T' or result.row_count!=3:raise ValueError('Original completion mismatch')
   frames=connection.original_controls[start:]
   if not any(f==b'C\0\0\0\x0dSELECT 3\0' for f in frames):raise ValueError('Original command frame missing')
   raw=cells(result)
   captures.append({'descriptor':descriptor,'rows':raw,'commandReadyFramesHex':[f.hex() for f in frames]})
   return check_registry_correspondence(manifest,'fixture',xid,raw,10,100000)
  match=capture()
  if sorted(r.cells[1] for r in match.cohort)!=['11','20','7'] or [r.cells[1] for r in match.contributors]!=['7','11']:raise ValueError('Complete native cohort mismatch')
  if {r.cells[1]:r.cells for r in match.cohort}!={r[1]:tuple(r) for r in rows}:raise ValueError('Original native cells changed')
  checks.append({'id':'native-exact-three-operation-cohort','contributorOrdinals':['7','11'],'retainedNoncontributorOrdinal':'20','foreignXidExcluded':foreign[0],'exactOriginalCells':True})
  for column in range(9,14):
   connection.execute_simple('SAVEPOINT original_substitution')
   name=COLUMNS[column].removesuffix('_hex')
   connection.execute_simple("UPDATE truss.row_home_operation SET "+name+"=decode('ff','hex') WHERE original_writer_xid=pg_current_xact_id_if_assigned() AND operation_ordinal=7")
   try:capture()
   except ValueError as error:
    if str(error) not in ('Original registry contributor artifact mismatch','Original registry context/group mismatch'):raise
    checks.append({'id':'native-substitution-'+name,'refused':True,'nativeTransactionStatus':connection._ready_status.decode()})
   else:raise ValueError('Expected original byte mismatch refusal')
   connection.execute_simple('ROLLBACK TO SAVEPOINT original_substitution');connection.execute_simple('RELEASE SAVEPOINT original_substitution')
  restored=capture()
  if {r.cells[1]:r.cells for r in restored.cohort}!={r[1]:tuple(r) for r in rows}:raise ValueError('Original cells not restored')
  checks.append({'id':'same-xid-and-original-cells-after-confirmed-restoration','writerXid':xid})
  connection.execute_simple('ROLLBACK')
  if connection._ready_status!=b'I':raise ValueError('Original rollback completion missing')
  if cells(connection.execute_simple('SELECT pg_catalog.pg_current_xact_id_if_assigned()::text'))!=[[None]]:raise ValueError('Rollback observation assigned xid')
  checks.append({'id':'confirmed-original-rollback-no-assigned-xid'})
 finally:
  if connection is not None:connection.close()
  if supplied is not None:supplied.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=raw for p,raw in frozen.items()):raise ValueError('Source drift')
receipt={'scope':'original PostgreSQL16.15 registry query and raw text descriptor/cells/control completion composed with Python correspondence; manually populated administrative fixture','serverVersion':version,'observations':checks,'originalCaptures':captures,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'protectedAdmissionReady':False,'acceptanceCasesPromoted':[],'limitations':['Fixture owner manually inserts full proposed carriers and phase labels; no protected producer or semantic readiness','Actual source table and complete current-xid query, not installed marker/role/ACL/dependency closure','No original native scope/security/family semantics or complete touch contributor coverage','Logical receive limits and byte permits do not qualify Python heap/native parser work/deadline','No seven semantic bodies, public API, published wheel or full settlement qualification']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'captures':len(captures),'protectedAdmissionReady':False}))
