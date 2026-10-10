"""Actual private accounting procedures; administrative carrier fixtures, not engine admission."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
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
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':raise SystemExit('Original local runtime/driver required')
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','docs/helix/04-build/evidence/design-audit/capacity-reservation-source.owner-export.sql','packages/postgresql/native/capacity-reservation/accounting.sql','packages/postgresql/native/issued-operation-admission/operation-admission.sql','docs/helix/02-design/contracts/row-home-capacity-initialization-v0.1.proposal.sql','docs/helix/02-design/contracts/bindings/truss-row-touch-retention-resource-v0.1.proposal.json']
frozen={p:(ROOT/p).read_bytes() for p in paths};checks=[]
def expect(name,expected,actual):
 if expected!=actual:raise ValueError(name+': native mismatch')
 checks.append({'id':name,'expected':expected,'observed':actual})
with tempfile.TemporaryDirectory(prefix='truss-capacity-procedures-') as directory:
 server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop');connections=[]
 try:
  uri=urlparse(server.get_uri());opts=parse_qs(uri.query);host=opts.get('host',[uri.hostname])[0];port=int(opts.get('port',[uri.port or 5432])[0])
  def connect(user='postgres'):
   c=pg8000.native.Connection(user=user,database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=5);connections.append(c);return c
  c=connect();foreign=connect();version=c.run('SHOW server_version')[0][0]
  if not version.startswith('16.15'):raise ValueError('Native version mismatch')
  for p in paths[:4]:c.run(frozen[p].decode('utf8'))
  initialization=frozen[paths[4]].decode().replace('$1::bytea',':layout').replace('$2::bytea',':resource')
  c.run(initialization,layout=frozen[paths[0]],resource=frozen[paths[5]])
  c.run('BEGIN');xid=c.run('SELECT pg_current_xact_id()::text')[0][0]
  c.run('CREATE TEMP TABLE caller_sentinel(value int)');c.run('INSERT INTO caller_sentinel VALUES (7)')
  plan=b'original administrative accounting fixture'
  def context(ordinal):
   return c.run("SELECT convert_to(jsonb_build_object('interfaceVersion','truss-native-operation-context/0.2','xid',pg_current_xact_id()::text,'ordinal',CAST(:ordinal AS text),'sessionUser',session_user::text,'actingUser',current_user::text,'actorRoleOid',(SELECT oid::text FROM pg_roles WHERE rolname=current_user),'sessionRoleOid',(SELECT oid::text FROM pg_roles WHERE rolname=session_user),'database',current_database(),'backendPid',pg_backend_pid()::text)::text,'UTF8')",ordinal=str(ordinal))[0][0]
  def ledger():
   row=c.run('SELECT retained_rows,retained_custody_bytes,reserved_rows,reserved_custody_bytes,reservation_writer_xid::text,reservation_operation_ordinal::text,encode(reservation_context_bytes,\'hex\'),encode(reservation_plan_bytes,\'hex\'),reservation_initial_rows,reservation_initial_custody_bytes FROM truss.row_home_capacity')[0]
   return row
  def reserve(ordinal,ctx):
   c.run('SELECT truss.capacity_reserve_original(:ordinal,:context,:plan,2,4096,:layout,:resource)',ordinal=ordinal,context=ctx,plan=plan,layout=frozen[paths[0]],resource=frozen[paths[5]])
  def admit(ordinal):
   row=c.run("SELECT writer_xid,ordinal,context_hex FROM truss.runtime_admit_operation(:ordinal,'mutation',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'))",ordinal=ordinal)[0]
   expect('native-admission-'+str(ordinal),[xid,str(ordinal),context(ordinal).hex()],row)
  def transfer(ctx,rows=0,growth=0,removed=0):
   c.run('SELECT truss.capacity_transfer_original(:context,:plan,:rows,:growth,:removed)',context=ctx,plan=plan,rows=rows,growth=growth,removed=removed)
  def refusal(name,code,sql,**args):
   before=ledger();c.run('SAVEPOINT refusal')
   try:c.run(sql,**args)
   except pg8000.exceptions.DatabaseError as e:expect(name,code,e.args[0]['C'])
   else:raise ValueError('Expected native refusal: '+name)
   c.run('ROLLBACK TO SAVEPOINT refusal');c.run('RELEASE SAVEPOINT refusal');expect(name+'-ledger-unchanged',before,ledger())
  ctx=context(0);c.run('SAVEPOINT operation_a');reserve(0,ctx)
  expect('reserve-before-registry',[0,0,2,4096,xid,'0',ctx.hex(),plan.hex(),2,4096],ledger())
  expect('no-registry-prerequisite',[[0]],c.run('SELECT count(*) FROM truss.row_home_operation WHERE original_writer_xid=pg_current_xact_id_if_assigned()'))
  refusal('release-before-finalization','P0002','SELECT truss.capacity_release_original(:context,:plan)',context=ctx,plan=plan)
  admit(0);size=len(ctx)+6;transfer(ctx,1,size)
  expect('actual-carrier-transfer',[1,size,1,4096-size,xid,'0',ctx.hex(),plan.hex(),2,4096],ledger())
  refusal('negative-delta','22023','SELECT truss.capacity_transfer_original(:context,:plan,-1,0,0)',context=ctx,plan=plan)
  refusal('new-row-without-carrier-byte','22023','SELECT truss.capacity_transfer_original(:context,:plan,1,0,0)',context=ctx,plan=plan)
  refusal('growth-over-remaining','54000','SELECT truss.capacity_transfer_original(:context,:plan,0,4096,0)',context=ctx,plan=plan)
  refusal('foreign-plan','55000','SELECT truss.capacity_transfer_original(:context,:plan,0,0,0)',context=ctx,plan=b'foreign')
  refusal('unfinished-release','55000','SELECT truss.capacity_release_original(:context,:plan)',context=ctx,plan=plan)
  # This is an explicit administrative phase fixture, not a protected finalizer.
  transfer(ctx,0,2)
  c.run("UPDATE truss.row_home_operation SET phase='application_finalized',readiness_generation=effect_generation,sealed_generation=effect_generation,application_generation=effect_generation,application_result_bytes=decode('abcd','hex') WHERE original_writer_xid=pg_current_xact_id_if_assigned() AND operation_ordinal=0")
  c.run('SELECT truss.capacity_release_original(:context,:plan)',context=ctx,plan=plan)
  settled=[1,size+2,0,0,None,None,None,None,None,None];expect('release-only-unused',settled,ledger())
  c.run('SAVEPOINT operation_b');ctx_b=context(1);reserve(1,ctx_b);admit(1);transfer(ctx_b,1,len(ctx_b)+6)
  expect('b-retains-a',[2,size+2+len(ctx_b)+6],ledger()[:2])
  c.run('ROLLBACK TO SAVEPOINT operation_b');c.run('RELEASE SAVEPOINT operation_b');expect('b-rollback-preserves-a',settled,ledger())
  expect('only-a-registry-survives',[[0,'application_finalized']],c.run('SELECT operation_ordinal,phase FROM truss.row_home_operation WHERE original_writer_xid=pg_current_xact_id_if_assigned() ORDER BY operation_ordinal'))
  expect('caller-work-preserved',[[7]],c.run('SELECT value FROM caller_sentinel'))
  foreign.run('BEGIN');foreign.run('SELECT pg_current_xact_id()');foreign.run("SET LOCAL statement_timeout='1s'")
  try:foreign.run('SELECT truss.capacity_transfer_original(:context,:plan,0,0,0)',context=ctx,plan=plan)
  except pg8000.exceptions.DatabaseError as e:expect('foreign-transaction-refusal','55000',e.args[0]['C'])
  else:raise ValueError('Foreign transaction admitted')
  foreign.run('ROLLBACK');c.run('ROLLBACK')
  expect('host-rollback-restores-ledger',[0,0,0,0,None,None,None,None,None,None],ledger())
  expect('host-rollback-restores-registry',[[0]],c.run('SELECT count(*) FROM truss.row_home_operation'))
  c.run('BEGIN');c.run('SELECT pg_current_xact_id()')
  refusal('wrong-original-profile','55000','SELECT truss.capacity_reserve_original(0,:context,:plan,2,4096,:layout,:resource)',context=ctx,plan=plan,layout=b'wrong',resource=frozen[paths[5]])
  c.run('ROLLBACK')
  c.run('CREATE ROLE truss_capacity_probe LOGIN');c.run('GRANT USAGE ON SCHEMA truss TO truss_capacity_probe')
  signatures=['truss.capacity_reserve_original(bigint,bytea,bytea,bigint,bigint,bytea,bytea)','truss.capacity_transfer_original(bytea,bytea,bigint,bigint,bigint)','truss.capacity_release_original(bytea,bytea)']
  for signature in signatures:expect('ordinary-execute-denied-'+signature,[[False]],c.run("SELECT has_function_privilege('truss_capacity_probe',:signature,'EXECUTE')",signature=signature))
  probe=connect('truss_capacity_probe')
  try:probe.run('SELECT truss.capacity_release_original(:context,:plan)',context=ctx,plan=plan)
  except pg8000.exceptions.DatabaseError as e:expect('actual-ordinary-invocation-denied','42501',e.args[0]['C'])
  else:raise ValueError('Ordinary invocation admitted')

 finally:
  for c in connections:c.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()):raise ValueError('Original source drift')
receipt={'scope':'Actual private ledger reservation/transfer/release procedures with native registry byte correspondence and rollback; administrative synthetic carriers/phase fixture, not protected producer/finalizer', 'serverVersion':version,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installerReady':False,'nativeFullReservationQualified':False,'acceptanceCasesPromoted':[],'limitations':['No original semantic plan/security/account/complete inventory or native overhead qualification','Supplied deltas are not authenticated; protected event/finalizer must derive and validate them','Administrative application_finalized fixture proves helper preconditions only, not actual finalization','No ordinary-role graph mutation/R4/R5/feed/commit or guard closure','Host issuer nonreuse, deadlines/cancellation and unknown recovery are separate uncomposed evidence']}
with output.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'installerReady':False}))
