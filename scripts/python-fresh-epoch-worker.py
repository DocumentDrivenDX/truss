"""Native original epoch projection component; no protected admission."""
import json,sys,threading,time,hashlib,struct,copy
from pathlib import Path
config=json.loads(sys.stdin.read());sys.path.insert(0,config['capturedModules'])
from pg8000.native import Connection
from truss._native_pg8000 import NativeBoundary,NativeBoundaryRefusal
from truss._native_transactions import NativeTransactions
from truss._host_execution import HostExecutor
from truss._native_arbitration import NativeArbitration
from truss._operation_arbitration import Prepared
from truss.execution import Ok
from truss._native_fresh_epoch_capture import NativeFreshEpochCapture,FRESH_EPOCH_LIMITS
folder=Path(config['evidence']);observations=[];threads=[];connections=[]
def connect(user='postgres'):
 c=Connection(user=user,database='postgres',unix_sock=config['unixSocket'],ssl_context=False,timeout=8);connections.append(c);return c
def same(expected,observed):
 if type(expected) is not type(observed):return False
 if type(expected) in (tuple,list):return len(expected)==len(observed) and all(same(a,b) for a,b in zip(expected,observed))
 if type(expected) is dict:return expected.keys()==observed.keys() and all(same(expected[k],observed[k]) for k in expected)
 return expected==observed
def check(name,expected,observed):
 observations.append({'id':name,'expected':copy.deepcopy(expected),'observed':copy.deepcopy(observed)})
 if not same(expected,observed):raise AssertionError(name)
def error_detail(call):
 try:call();return {'code':'unexpected-success','message':''}
 except Exception as error:
  native=error.args[0] if error.args and type(error.args[0]) is dict else {}
  return {'code':native.get('C','unknown'),'message':native.get('M',str(error))}
def error_code(call):return error_detail(call)['code']
query="SELECT * FROM truss.runtime_lock_fresh_source_epoch('component-test-installation',:epoch,:incarnation)"
admin=connect();reader=connect();writer=connect()
try:
 check('exact-engine',[['160015']],admin.run("SELECT current_setting('server_version_num')::text"))
 for name in ('layout','immutable','lock','issue','fresh'):
  admin.run(Path(config[name]).read_text())
 admin.run("INSERT INTO truss.installation_marker VALUES (1,'truss-bootstrap-marker/0.1.0','component-test-installation','component-only',decode(repeat('00',32),'hex'),'component',decode(repeat('00',32),'hex'),'owned-fixture','truss',now(),'component-clock-unqualified')")
 installed=admin.run("SELECT p.prosrc,p.prosecdef,p.provolatile,p.proconfig,p.proargtypes::text,p.proallargtypes::text,pg_catalog.pg_get_userbyid(p.proowner),l.lanname,EXISTS(SELECT 1 FROM pg_catalog.aclexplode(p.proacl) a WHERE a.grantee=0 AND a.privilege_type='EXECUTE') FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE p.oid='truss.runtime_lock_fresh_source_epoch(text,text,text)'::regprocedure")
 body=Path(config['fresh']).read_text().split('AS $$',1)[1].split('$$;',1)[0]
 check('independent-installed-source-profile',[[body,False,'v',['search_path=pg_catalog, pg_temp'],'25 25 25','{'+','.join(['25']*15)+'}','postgres','plpgsql',False]],installed)
 initial=admin.run("SELECT truss.runtime_issue_source_epoch('component-test-installation',NULL,'component-test-incarnation',decode('01','hex'),decode('0203','hex'))")[0][0]
 admin.run('CREATE ROLE fresh_epoch_ordinary LOGIN NOSUPERUSER NOBYPASSRLS; GRANT USAGE ON SCHEMA truss TO fresh_epoch_ordinary')
 ordinary=connect('fresh_epoch_ordinary')
 check('ungranted-ordinary-producer-refuses','42501',error_code(lambda:ordinary.run(query,epoch=initial,incarnation='component-test-incarnation')))
 reader.run('BEGIN ISOLATION LEVEL READ COMMITTED')
 native=reader.run("SELECT pg_current_xact_id()::text,(SELECT oid::text FROM pg_database WHERE datname=current_database()),pg_backend_pid()::text,session_user::text,current_user::text")[0]
 captured=reader.run(query,epoch=initial,incarnation='component-test-incarnation')
 expected=['component-test-installation',initial,'component-test-incarnation','01','0203',hashlib.sha256(bytes.fromhex('0203')).hexdigest(),*native,'transaction_source_epoch_lock_only']
 check('original-native-epoch-and-transaction-projection',[expected],captured)
 check('exact-ordered-text-columns',['installation_id','source_epoch','target_incarnation','profile_hex','evidence_hex','evidence_sha256','actual_writer_xid','actual_database_oid','actual_backend_pid','original_actor','effective_actor','cut_scope'],[c['name'] for c in reader.columns])
 writer.run("SET lock_timeout='150ms'")
 issue="SELECT truss.runtime_issue_source_epoch('component-test-installation',:prior,'component-test-incarnation',decode('01','hex'),decode('0405','hex'))"
 check('held-projection-blocks-participating-epoch-writer','55P03',error_code(lambda:writer.run(issue,prior=initial)))
 check('held-pointer-unchanged',[[initial]],admin.run('SELECT source_epoch FROM truss.source_epoch_current'))
 reader.run('COMMIT')
 successor=writer.run(issue,prior=initial)[0][0]
 check('release-permits-original-issuer',True,successor!=initial)
 # All bad calls run under a caller-owned savepoint; no epoch mutation follows.
 reader.run('BEGIN ISOLATION LEVEL READ COMMITTED')
 for label,epoch,incarnation in [('stale',initial,'component-test-incarnation'),('wrong-target',successor,'wrong'),('missing',None,'component-test-incarnation')]:
  reader.run('SAVEPOINT refusal')
  check(label+'-comparison-refuses','55000',error_code(lambda:reader.run(query,epoch=epoch,incarnation=incarnation)))
  reader.run('ROLLBACK TO SAVEPOINT refusal');reader.run('RELEASE SAVEPOINT refusal')
 check('refusals-leave-current-pointer',[[successor]],reader.run('SELECT source_epoch FROM truss.source_epoch_current'));reader.run('COMMIT')
 for level in ('REPEATABLE READ','SERIALIZABLE'):
  reader.run('BEGIN ISOLATION LEVEL '+level);reader.run('SELECT source_epoch FROM truss.source_epoch_current')
  check(level+'-inherited-snapshot-refuses',{'code':'55000','message':'fresh epoch requires native read committed read write'},error_detail(lambda:reader.run(query,epoch=successor,incarnation='component-test-incarnation')));reader.run('ROLLBACK')
 reader.run('BEGIN READ ONLY')
 check('read-only-lock-profile-refuses',{'code':'55000','message':'fresh epoch requires native read committed read write'},error_detail(lambda:reader.run(query,epoch=successor,incarnation='component-test-incarnation')));reader.run('ROLLBACK')
 # Pending original issuer update precedes reader acquisition. Native tuple/xid
 # wait must drain before the VOLATILE helper observes its committed registry.
 writer.run('BEGIN');pending=writer.run(issue,prior=successor)[0][0]
 reader.run('BEGIN ISOLATION LEVEL READ COMMITTED');wait_native=reader.run("SELECT pg_current_xact_id()::text,(SELECT oid::text FROM pg_database WHERE datname=current_database()),pg_backend_pid()::text,session_user::text,current_user::text")[0];pid=int(wait_native[2])
 result=[];errors=[]
 def acquire():
  try:result.extend(reader.run(query,epoch=pending,incarnation='component-test-incarnation'))
  except Exception as e:errors.append(str(e))
 thread=threading.Thread(target=acquire);threads.append(thread);thread.start();deadline=time.monotonic()+4
 while not admin.run('SELECT :writer=ANY(pg_blocking_pids(:reader))',writer=writer.run('SELECT pg_backend_pid()')[0][0],reader=pid)[0][0]:
  if time.monotonic()>deadline:raise TimeoutError('Exact epoch writer blocker not observed')
  time.sleep(.01)
 check('pending-issuer-blocks-reader',True,thread.is_alive());writer.run('COMMIT');thread.join(8)
 check('drain-settles-reader',False,thread.is_alive());check('drain-no-driver-error',[],errors)
 check('post-drain-original-committed-epoch',pending,result[0][1]);check('post-drain-evidence','0405',result[0][4])
 check('post-drain-complete-original-tuple',[['component-test-installation',pending,'component-test-incarnation','01','0405',hashlib.sha256(bytes.fromhex('0405')).hexdigest(),*wait_native,'transaction_source_epoch_lock_only']],result)
 reader.run('COMMIT')
 # Response identity is not a durable capability: autocommit already released.
 auto=reader.run(query,epoch=pending,incarnation='component-test-incarnation')
 check('autocommit-response-is-idle','49',reader._transaction_status.hex())
 after_auto=writer.run(issue,prior=pending)[0][0]
 check('autocommit-return-does-not-hold-epoch',True,after_auto!=pending)
 reader.run('BEGIN ISOLATION LEVEL READ COMMITTED');parent_xid=reader.run('SELECT pg_current_xact_id()::text')[0][0];reader.run('SAVEPOINT before_lock')
 saved=reader.run(query,epoch=after_auto,incarnation='component-test-incarnation')[0]
 check('savepoint-lock-original-parent-xid',parent_xid,saved[6])
 reader.run('ROLLBACK TO SAVEPOINT before_lock')
 check('savepoint-rollback-keeps-parent-xid',[[saved[6]]],reader.run('SELECT pg_current_xact_id()::text'))
 after_savepoint=writer.run(issue,prior=after_auto)[0][0]
 check('savepoint-rollback-releases-epoch-lock',True,after_savepoint!=after_auto)
 reader.run('RELEASE SAVEPOINT before_lock');reader.run('COMMIT')
 reader.run('BEGIN ISOLATION LEVEL READ COMMITTED')
 owned=reader.run(query,epoch=after_savepoint,incarnation='component-test-incarnation')[0]
 after_same=reader.run(issue,prior=after_savepoint)[0][0]
 check('same-parent-writer-can-change-epoch',True,after_same!=after_savepoint)
 check('same-parent-writer-xid-unchanged',[[owned[6]]],reader.run('SELECT pg_current_xact_id()::text'))
 reader.run('ROLLBACK');pending=after_savepoint
 # Native scope ancestry: RELEASE reparents; rollback to a later scope
 # preserves an earlier acquisition; recreated depth cannot restore a lock.
 reader.run('BEGIN ISOLATION LEVEL READ COMMITTED');parent_xid=reader.run('SELECT pg_current_xact_id()::text')[0][0]
 reader.run('SAVEPOINT original_parent');reader.run('SAVEPOINT original_child')
 released=reader.run(query,epoch=pending,incarnation='component-test-incarnation')[0]
 reader.run('RELEASE SAVEPOINT original_child')
 check('release-child-retains-parent-lock','55P03',error_code(lambda:writer.run(issue,prior=pending)))
 reader.run('ROLLBACK TO SAVEPOINT original_parent')
 check('rollback-parent-retains-original-xid',[[parent_xid]],reader.run('SELECT pg_current_xact_id()::text'))
 reader.run('SAVEPOINT original_child')
 successor=writer.run(issue,prior=pending)[0][0]
 check('same-name-depth-recreation-does-not-restore-lock',True,successor!=pending)
 check('released-original-row-is-historical',pending,released[1])
 reader.run('ROLLBACK');pending=successor
 reader.run('BEGIN ISOLATION LEVEL READ COMMITTED')
 earlier=reader.run(query,epoch=pending,incarnation='component-test-incarnation')[0]
 reader.run('SAVEPOINT later_scope');reader.run('ROLLBACK TO SAVEPOINT later_scope')
 check('rollback-after-acquisition-preserves-lock','55P03',error_code(lambda:writer.run(issue,prior=pending)))
 reader.run('RELEASE SAVEPOINT later_scope')
 check('release-later-scope-preserves-lock','55P03',error_code(lambda:writer.run(issue,prior=pending)))
 reader.run('ROLLBACK')
 successor=writer.run(issue,prior=pending)[0][0]
 check('outer-rollback-releases-original-acquisition',True,successor!=pending)
 check('rolled-back-original-row-is-historical',pending,earlier[1]);pending=successor
 # A definer wrapper cannot manufacture original invoker correspondence.
 admin.run("CREATE ROLE fresh_epoch_definer; GRANT USAGE ON SCHEMA truss TO fresh_epoch_definer; GRANT EXECUTE ON FUNCTION truss.runtime_lock_fresh_source_epoch(text,text,text) TO fresh_epoch_definer; CREATE FUNCTION truss.fresh_epoch_definer_probe() RETURNS text LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$ SELECT cut_scope FROM truss.runtime_lock_fresh_source_epoch('component-test-installation', '"+pending+"', 'component-test-incarnation') $$; ALTER FUNCTION truss.fresh_epoch_definer_probe() OWNER TO fresh_epoch_definer")
 check('definer-invoker-elevation-refuses',{'code':'55000','message':'original invoker fresh epoch boundary required'},error_detail(lambda:admin.run('SELECT truss.fresh_epoch_definer_probe()')))
 # Same installed helper through original operation/ingress/outbound custody.
 for label,lost in [('original-capture',False),('lost-local-reply',True),('maximum-native-evidence',False),('unqualified-self-issue',False),('lost-control-reply',False),('unqualified-native-error',False),('known-transport-close',False)]:
  if label=='maximum-native-evidence':
   pending=admin.run("SELECT truss.runtime_issue_source_epoch('component-test-installation',:prior,'component-test-incarnation',pg_catalog.decode(pg_catalog.repeat('01',65536),'hex'),pg_catalog.decode(pg_catalog.repeat('02',1048576),'hex'))",prior=pending)[0][0]
  con=connect();gate=None
  try:
   con.run('SELECT 1');boundary=NativeBoundary(con,event_bytes=FRESH_EPOCH_LIMITS.wire_bytes);tracker=NativeTransactions(boundary)
   tracker.begin(isolation='read_committed',access_mode='read_write');token=boundary.acquire_operation()
   original_parent=tracker.savepoint('acquisition_parent',token=token);original_child=tracker.savepoint('acquisition_child',token=token)
   port=tracker.port(token);executor=HostExecutor();adopted=executor.adopt_transaction(port,isolation='read_committed',access_mode='read_write')
   check(label+':original-adoption',True,type(adopted) is Ok)
   service=NativeArbitration(executor);assembly=object();check(label+':registered','registered',service.registry.register(assembly))
   prepared=service.registry.prepare(assembly,adopted.value);check(label+':original-attempt',True,type(prepared) is Prepared)
   session=service.bind(prepared.attempt);tracker._epoch_acquisitions.maximum=1;gate=NativeFreshEpochCapture(session,'component-test-installation',pending,'component-test-incarnation')
   if lost:
    publish=gate._publish
    def lose(observation):publish(observation);raise MemoryError('Lost local epoch reply')
    gate._publish=lose
   try:returned=gate.capture()
   except MemoryError:returned=None
   retained=gate.original_observation
   check(label+':closed-admission',True,session.admission_closed)
   check(label+':retained-native-result',True,retained is not None and retained.original_call is boundary.last_call and session.calls[-1].native_call is retained.original_call)
   check(label+':published-or-retained',True,(returned is retained) if not lost else returned is None)
   check(label+':response-only-scope','original_epoch_response_only',retained.scope)
   check(label+':original-epoch',pending,retained.original_row[1])
   if label=='maximum-native-evidence':
    check(label+':complete-profile-byte-limit',65536,len(bytes.fromhex(retained.original_row[3])))
    check(label+':complete-evidence-byte-limit',1048576,len(bytes.fromhex(retained.original_row[4])))
    check(label+':original-evidence-bytes',hashlib.sha256(b'\x02'*1048576).hexdigest(),retained.original_row[5])
   check(label+':original-outbound-q',True,b'Q'+struct.pack('!I',len(gate.sql.encode())+5)+gate.sql.encode()+b'\0'==retained.original_request)
   raw=b''.join(e.code+struct.pack('!I',len(e.payload)+4)+e.payload for e in retained.original_frames)
   frames=retained.original_frames
   check(label+':original-row-frame-count',1,sum(e.code==b'D' for e in frames))
   data=next(e.payload for e in frames if e.code==b'D');offset=2;decoded=[]
   for _ in range(struct.unpack_from('!H',data)[0]):
    size=struct.unpack_from('!i',data,offset)[0];offset+=4
    decoded.append(data[offset:offset+size].decode('utf8'));offset+=size
   check(label+':original-row-frame-reconstruction',retained.original_row,tuple(decoded))
   check(label+':original-row-frame-complete',len(data),offset)
   check(label+':original-response-frame-order',['T','D','C','Z'],[e.code.decode('ascii') for e in frames])
   (folder/(label+'.response.bin')).write_bytes(raw);(folder/(label+'.request.bin')).write_bytes(retained.original_request)
   (folder/(label+'.row.json')).write_text(json.dumps(retained.original_row)+'\n')
   prior=boundary.last_call
   try:gate.capture();refusal=False
   except NativeBoundaryRefusal as e:refusal=str(e)=='Retain original epoch observation; never replay'
   check(label+':replay-refuses',True,refusal)
   check(label+':replay-no-native-call',True,boundary.last_call is prior)
   check(label+':actual-epoch-lock-blocks-writer','55P03',error_code(lambda:writer.run(issue,prior=pending)))
   gate.detach();check(label+':retained-after-detach',True,gate.original_observation is retained and con._sock is boundary._original_stream)
   acquisition=gate.original_acquisition
   check(label+':original-acquisition-retained',True,acquisition is not None and acquisition.observation is retained and any(a is acquisition for a in tracker._epoch_acquisitions.records))
   check(label+':original-acquisition-live',True,acquisition.live())
   check(label+':acquisition-only-scope','original_acquisition_lifecycle_only',acquisition.scope)
   check(label+':copied-acquisition-refuses',False,copy.copy(acquisition).live())
   original_root=tracker._epoch_acquisitions;tracker._epoch_acquisitions=object()
   try:check(label+':replaced-root-refuses',False,acquisition.live())
   finally:tracker._epoch_acquisitions=original_root
   original_pending=boundary._pending_operation_ledger;boundary._pending_operation_ledger=object()
   try:check(label+':replaced-pending-session-refuses',False,acquisition.live())
   finally:boundary._pending_operation_ledger=original_pending
   original_records=tracker._epoch_acquisitions.records
   try:tracker._epoch_acquisitions.retain(gate,retained);capacity_refused=False
   except NativeBoundaryRefusal as error:capacity_refused=str(error)=='Original acquisition capacity exhausted'
   check(label+':capacity-exact-plus-one-refuses',True,capacity_refused)
   check(label+':capacity-refusal-keeps-original-root',True,tracker._epoch_acquisitions.records is original_records and gate.original_acquisition is acquisition)
   if label=='known-transport-close':
    original_generation=tracker._state.generation
    check(label+':acquisition-live-immediately-before-close',True,acquisition.live() and acquisition.valid)
    continue
   if label=='lost-control-reply':
    original_simple=boundary._run_simple
    def lose_control(command):original_simple(command);raise MemoryError('Lost original control reply')
    boundary._run_simple=lose_control
    try:
     try:tracker._control('release','RELEASE SAVEPOINT acquisition_child',token=token,savepoint=original_child,cleanup=session.cleanup_permit);lost=False
     except MemoryError:lost=True
    finally:boundary._run_simple=original_simple
    check(label+':original-control-reply-lost',True,lost)
    check(label+':original-incomplete-raised-completion-still-active',True,not boundary.last_call.capture_complete and boundary.last_call.driver_raised and boundary.last_call.final_status==b'T')
    check(label+':uncertain-control-invalidates',False,acquisition.live())
    check(label+':physical-lock-can-remain-held','55P03',error_code(lambda:writer.run(issue,prior=pending)))
    check(label+':uncertain-boundary-quarantined',True,boundary._quarantined)
    prior_call=boundary.last_call
    try:tracker._control('rollback','ROLLBACK',token=token,cleanup=session.cleanup_permit);retry_refused=False
    except NativeBoundaryRefusal:retry_refused=True
    check(label+':uncertain-native-retry-refuses',True,retry_refused and boundary.last_call is prior_call)
    check(label+':uncertainty-never-revives',False,acquisition.live());continue
   if label=='unqualified-native-error':
    original_before=tracker._epoch_acquisitions.before;before_invocation=[]
    def observe_failed_invalidation(control):original_before(control);before_invocation.append(acquisition.valid)
    tracker._epoch_acquisitions.before=observe_failed_invalidation
    check(label+':actual-native-error','22012',error_code(lambda:boundary.run('SELECT 1/0',token=token,cleanup=session.cleanup_permit)))
    check(label+':invalidated-before-failed-native-call',[False],before_invocation)
    check(label+':failed-call-does-not-revive',False,acquisition.live())
    tracker._control('rollback','ROLLBACK',token=token,cleanup=session.cleanup_permit)
    check(label+':failed-call-rollback-does-not-revive',False,acquisition.live());continue
   if label=='unqualified-self-issue':
    original_before=tracker._epoch_acquisitions.before;before_invocation=[]
    def observe_invalidation(control):
     original_before(control);before_invocation.append(acquisition.valid)
    tracker._epoch_acquisitions.before=observe_invalidation
    successor=boundary.run(issue,token=token,cleanup=session.cleanup_permit,prior=pending)[0][0]
    check(label+':invalidated-before-native-invocation',[False],before_invocation)
    check(label+':native-self-issuer-changes-epoch',True,successor!=pending)
    check(label+':self-issuer-original-xid',[[retained.original_row[6]]],boundary.run('SELECT pg_current_xact_id()::text',token=token,cleanup=session.cleanup_permit))
    check(label+':unqualified-call-irreversible-invalidation',False,acquisition.live())
    check(label+':unqualified-call-reason','unqualified-ordinary-call',acquisition.reason)
    tracker._control('rollback','ROLLBACK',token=token,cleanup=session.cleanup_permit)
    check(label+':rollback-cannot-revive-acquisition',False,acquisition.live())
    continue
   tracker._control('release','RELEASE SAVEPOINT acquisition_child',token=token,savepoint=original_child,cleanup=session.cleanup_permit)
   check(label+':release-reparents-original-acquisition',True,acquisition.live() and acquisition.scopes==(original_parent,))
   check(label+':native-reparented-lock-held','55P03',error_code(lambda:writer.run(issue,prior=pending)))
   later=tracker._control('savepoint','SAVEPOINT acquisition_later',token=token,savepoint='acquisition_later',cleanup=session.cleanup_permit)
   def paused_rollback(target,sql,expect_held):
    native_returned=threading.Event();resume=threading.Event();faults=[];original_simple=boundary._run_simple
    def pause_after_native(command):
     response=original_simple(command);native_returned.set()
     if not resume.wait(8):raise TimeoutError('Original native settlement pause expired')
     return response
    def rollback_original():
     try:tracker._control('rollback_to',sql,token=token,savepoint=target,cleanup=session.cleanup_permit)
     except BaseException as error:faults.append(str(error))
    boundary._run_simple=pause_after_native;thread=threading.Thread(target=rollback_original);threads.append(thread);thread.start()
    try:
     if not native_returned.wait(4):raise TimeoutError('Original rollback did not return natively')
     check(label+':'+target.name+':original-call-unsettled',True,boundary._calling)
     check(label+':'+target.name+':no-live-claim-during-settlement',False,acquisition.live())
     check(label+':'+target.name+':not-yet-invalidated',True,acquisition.valid)
     if expect_held:
      check(label+':'+target.name+':native-earlier-lock-still-held','55P03',error_code(lambda:writer.run(issue,prior=pending)))
      successor=None
     else:
      successor=writer.run(issue,prior=pending)[0][0]
      check(label+':'+target.name+':native-lock-released-before-settlement',True,successor!=pending)
    finally:
     resume.set();thread.join(8);boundary._run_simple=original_simple
    check(label+':'+target.name+':settlement-drained',False,thread.is_alive())
    check(label+':'+target.name+':settlement-errors',[],faults)
    return successor
   paused_rollback(later,'ROLLBACK TO SAVEPOINT acquisition_later',True)
   check(label+':rollback-later-keeps-acquisition',True,acquisition.live())
   successor=paused_rollback(original_parent,'ROLLBACK TO SAVEPOINT acquisition_parent',False)
   check(label+':rollback-across-invalidates-original-acquisition',False,acquisition.live())
   check(label+':rollback-original-scope-object-survives',True,tracker._live(original_parent))
   tracker._control('savepoint','SAVEPOINT acquisition_child',token=token,savepoint='acquisition_child',cleanup=session.cleanup_permit)
   check(label+':recreated-scope-cannot-revive-acquisition',False,acquisition.live())
   check(label+':native-rollback-releases-original-lock',True,successor!=pending);pending=successor
   check(label+':admission-still-closed',True,session.admission_closed)
  finally:
   if gate is not None and not gate.detached:con._sock=gate.original_sock
   connections.remove(con);con.close()
   if gate is not None and gate.original_acquisition is not None:
    check(label+':known-original-connection-close-refuses-live',False,gate.original_acquisition.live())
    if label=='known-transport-close':
     check(label+':close-keeps-stale-native-generation',True,tracker._state.generation is original_generation and tracker._state.status==b'T' and gate.original_acquisition.valid)
     successor=writer.run(issue,prior=pending)[0][0]
     check(label+':closed-original-connection-releases-physical-lock',True,successor!=pending);pending=successor
 if len({e['id'] for e in observations})!=len(observations) or any(not same(e['expected'],e['observed']) for e in observations):raise AssertionError('Final retained observations differ')
 (folder/'native.json').write_text(json.dumps({'status':'component-passed','observations':observations,'scope':'Original source-epoch SQL projection in owned PostgreSQL16.15, original issuer lineage, native RC/read-write gate, pending issuer drain and transaction-bound row lock. Installer-authored synthetic marker/profile/evidence are not admitted artifacts. Drain/lifetime schedules use materialized administrative pg8000 results. Seven separate original NativeCall captures qualify bounded selected ingress/outbound and retained-response custody, including native maximum65536-byte profile/1048576-byte evidence, lost local reply and original acquisition lifecycle tracking; an unqualified self-issuer call invalidates lifecycle state before invocation. The explicit8MiB boundary event journal is component-only and ordinary defaults are unchanged. No authenticated provider, full source/authority/data writer closure, complete protected business execution/final host disclosure, final handback or backend acceptance.'},indent=2)+'\n')
 print(json.dumps({'status':'component-passed','observations':len(observations)}))
except BaseException as e:
 (folder/'native-failure.json').write_text(json.dumps({'status':'failed','observations':observations,'error':str(e)},indent=2)+'\n');raise
finally:
 writer.close()
 for thread in threads:thread.join(8)
 for connection in reversed(connections):
  if connection is not writer:connection.close()
