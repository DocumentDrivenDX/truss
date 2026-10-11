"""Fresh-process original Python source-census witness on an owned native fixture."""
import hashlib,json,struct,sys
from pathlib import Path
input=json.loads(sys.stdin.read());sys.path.insert(0,input['capturedModules'])
from pg8000.native import Connection
from truss._native_pg8000 import NativeBoundary,NativeBoundaryRefusal
from truss._native_transactions import NativeTransactions
from truss._host_execution import HostExecutor
from truss._native_arbitration import NativeArbitration
from truss._operation_arbitration import Prepared
from truss.execution import Ok
from truss._native_source_census import NativeSourceCensusCapture
observations=[];captures=[];folder=Path(input['evidence']);source=Path(input['source']).read_text()
sha=lambda b:hashlib.sha256(b).hexdigest()
def check(name,expected,observed):
 observations.append({'id':name,'expected':expected,'observed':observed})
 if expected!=observed:raise AssertionError(name)
def connect():return Connection(user='postgres',password=input['password'],host='127.0.0.1',port=input['port'],database='postgres',ssl_context=False,timeout=5)
admin=connect()
def capture(label,*,unavailable=False,lost=False):
 con=connect();gate=None
 try:
  con.run('SELECT 1');boundary=NativeBoundary(con);tracker=NativeTransactions(boundary)
  tracker.begin(isolation='repeatable_read',access_mode='read_only');token=boundary.acquire_operation()
  port=tracker.port(token);executor=HostExecutor();adopted=executor.adopt_transaction(port,isolation='repeatable_read',access_mode='read_only')
  check(label+':real-adoption',True,type(adopted) is Ok)
  service=NativeArbitration(executor);assembly=object();check(label+':registered','registered',service.registry.register(assembly))
  prepared=service.registry.prepare(assembly,adopted.value);check(label+':prepared',True,type(prepared) is Prepared)
  session=service.bind(prepared.attempt);gate=NativeSourceCensusCapture(session,source)
  if lost:
   original=gate._publish
   def lost_reply(observation):original(observation);raise MemoryError('Lost local census publication reply')
   gate._publish=lost_reply
  try:result=gate.capture()
  except (NativeBoundaryRefusal,MemoryError):result=None
  check(label+':closed-admission',True,session.admission_closed)
  if unavailable:
   check(label+':no-image',None,result);check(label+':no-retained-positive',None,gate.original_observation)
   check(label+':complete-native-null',True,gate.unavailable and gate.stage==3 and boundary.last_call.capture_complete)
  else:
   retained=gate.original_observation
   check(label+':retained-original',True,retained is not None)
   check(label+':exact-retained-call',True,retained.original_call is boundary.last_call and session.calls[-1].native_call is retained.original_call)
   check(label+':returned-or-lost-reply',True,(result is retained) if not lost else result is None)
   check(label+':complete-original-call',True,retained.original_call.capture_complete and retained.original_call.final_status==b'T')
   image=retained.original_image;parsed=json.loads(image)
   check(label+':qualified-engine','160015',parsed['serverVersion']);check(label+':40-sections',40,len(parsed['sections']))
   check(label+':original-request',True,retained.original_request==b'Q'+struct.pack('!I',len(gate.sql.encode())+5)+gate.sql.encode()+b'\0')
   (folder/(label+'.image.json')).write_bytes(image)
   captures.append({'label':label,'sha256':sha(image),'imageBytes':len(image),'chunks':gate.chunk_count,'account':gate.account.snapshot(gate),'rows':gate.rows_seen,'wireRemaining':gate.receiver._remaining_bytes})
  raw=b''.join(e.code+struct.pack('!I',len(e.payload)+4)+e.payload for e in gate.frames)
  (folder/(label+'.response.bin')).write_bytes(raw)
  entries=[w for w in gate.outbound.ordinary if w is not None] if gate.outbound else []
  (folder/(label+'.request.bin')).write_bytes(b''.join(w.data for w in entries))
  before=boundary.last_call
  try:gate.capture();replay='unexpected'
  except NativeBoundaryRefusal:replay='refused'
  check(label+':no-replay','refused',replay);check(label+':no-new-native-call',True,boundary.last_call is before)
  gate.detach();check(label+':original-ingress-restored',True,con._sock is boundary._original_stream and gate.detached)
  # Administrative fixture teardown closes the original connection. No complete
  # cooperative operation handback, accepted issuer or mutation is inferred.
  return None if gate.original_observation is None else gate.original_observation.original_image
 finally:
  if gate is not None and not gate.detached:con._sock=gate.original_sock
  con.close()
try:
 check('native-engine',[['160015']],admin.run("SELECT current_setting('server_version_num')::text"))
 admin.run("CREATE SCHEMA census_probe; CREATE TABLE census_probe.facts(value text); INSERT INTO census_probe.facts VALUES('original'); CREATE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 1::bigint';")
 unicode='A'*4095+'🙂é'+'B'*1000000
 admin.run("CREATE FUNCTION census_probe.unicode() RETURNS text LANGUAGE sql AS $body$ SELECT '"+unicode+"'::text $body$;")
 baseline=capture('baseline');check('baseline:greater-than-default-text-wire',True,len(baseline)>1048576)
 check('baseline:complete-native-Unicode',True,unicode.encode() in baseline)
 admin.run("UPDATE census_probe.facts SET value='changed';")
 data=capture('backing-data-update');check('backing-data:same-source',sha(baseline),sha(data))
 admin.run("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 333::bigint';")
 changed=capture('source-change');check('same-descriptor-body-change',True,sha(changed)!=sha(baseline))
 admin.run("CREATE OR REPLACE FUNCTION census_probe.value() RETURNS bigint LANGUAGE sql IMMUTABLE AS 'SELECT 1::bigint';")
 restored=capture('restored');check('exact-source-restoration',sha(baseline),sha(restored))
 withheld=capture('lost-publication',lost=True);check('lost-publication:retained-original-image',sha(baseline),sha(withheld))
 admin.run('CREATE FOREIGN DATA WRAPPER census_unqualified NO HANDLER;');capture('foreign-refusal',unavailable=True);admin.run('DROP FOREIGN DATA WRAPPER census_unqualified;')
 admin.run("CREATE FUNCTION census_probe.overflow() RETURNS text LANGUAGE sql AS $body$ SELECT '"+'Z'*17000000+"'::text $body$;")
 capture('overflow-refusal',unavailable=True);admin.run('DROP FUNCTION census_probe.overflow();')
 final=capture('final-restored');check('overflow:exact-source-restoration',sha(baseline),sha(final))
 (folder/'native.json').write_text(json.dumps({'status':'component-passed','observations':observations,'captures':captures,'scope':'Excluded PostgreSQL16.15 Docker installer and pg8000 original-operation capture only. Cooperative host/driver and retained payload bookkeeping premises. No installed pgserver port, authenticated provider/issuer, whole native observer interpretation, authority/execution held cut, graph profile, completed operation handback or backend acceptance.'},indent=2)+'\n')
 print(json.dumps({'status':'component-passed','observations':len(observations)}))
except BaseException as error:
 (folder/'native-failure.json').write_text(json.dumps({'status':'failed','observations':observations,'captures':captures,'error':str(error)},indent=2)+'\n');raise
finally:admin.close()
