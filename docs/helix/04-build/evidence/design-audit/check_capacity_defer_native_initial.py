"""Native original tuple recognition before named deferral; administrative registration fixture."""
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
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/capacity-reservation-source.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/capacity-accounting-source.owner-export.sql', 'packages/postgresql/native/issued-operation-admission/operation-admission.sql', 'docs/helix/02-design/contracts/row-home-capacity-initialization-v0.1.proposal.sql', 'docs/helix/02-design/contracts/bindings/truss-row-touch-retention-resource-v0.1.proposal.json', 'packages/postgresql/native/capacity-reservation/accounting.sql', 'docs/helix/04-build/evidence/design-audit/custody-codec-source.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/custody-size-source.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/capacity-inventory-source.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/capacity-observation-source.owner-export.sql', 'packages/postgresql/native/capacity-reservation/observation.sql','docs/helix/04-build/evidence/design-audit/capacity-commit-source.owner-export.sql','packages/postgresql/native/capacity-reservation/commit-check.sql','docs/helix/04-build/evidence/design-audit/capacity-cache-source.owner-export.sql','packages/postgresql/native/capacity-reservation/commit-cache.sql','docs/helix/04-build/evidence/design-audit/capacity-defer-source.owner-export.sql','packages/postgresql/native/capacity-reservation/defer-check.sql']
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
  for p in paths[7:11]:c.run(frozen[p].decode())
  c.run(frozen[paths[12]].decode())
  c.run(frozen[paths[14]].decode())
  c.run(frozen[paths[16]].decode())
  c.run("""CREATE TABLE truss.schedule_probe_calls(writer_xid xid8 NOT NULL);
CREATE FUNCTION truss.cache_audit_probe() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF NEW.verified_generation IS NOT NULL AND OLD.verified_generation IS DISTINCT FROM NEW.verified_generation THEN
 INSERT INTO truss.schedule_probe_calls VALUES(NEW.writer_xid); END IF; RETURN NULL; END $$;
CREATE TRIGGER cache_audit_probe AFTER UPDATE ON truss.capacity_check_memo FOR EACH ROW EXECUTE FUNCTION truss.cache_audit_probe();
CREATE SCHEMA host_probe;
CREATE TABLE host_probe.value(id integer PRIMARY KEY,value integer NOT NULL);
INSERT INTO host_probe.value VALUES(1,7);
CREATE FUNCTION host_probe.check_value() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.value<0 THEN RAISE EXCEPTION 'host fixture refusal' USING ERRCODE='23514'; END IF;RETURN NULL;END $$;
CREATE CONSTRAINT TRIGGER host_guard AFTER UPDATE ON host_probe.value DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION host_probe.check_value();""")
  c.run('BEGIN');xid=c.run('SELECT pg_current_xact_id()::text')[0][0]
  c.run('CREATE TEMP TABLE caller_sentinel(value int)');c.run('INSERT INTO caller_sentinel VALUES (7)')
  plan=b'original administrative accounting fixture'
  def context(ordinal):
   return c.run("SELECT convert_to(jsonb_build_object('interfaceVersion','truss-native-operation-context/0.2','xid',pg_current_xact_id()::text,'ordinal',CAST(:ordinal AS text),'sessionUser',session_user::text,'actingUser',current_user::text,'actorRoleOid',(SELECT oid::text FROM pg_roles WHERE rolname=current_user),'sessionRoleOid',(SELECT oid::text FROM pg_roles WHERE rolname=session_user),'database',current_database(),'backendPid',pg_backend_pid()::text)::text,'UTF8')",ordinal=str(ordinal))[0][0]
  def ledger():
   row=c.run('SELECT retained_rows,retained_custody_bytes,reserved_rows,reserved_custody_bytes,reservation_writer_xid::text,reservation_operation_ordinal::text,encode(reservation_context_bytes,\'hex\'),encode(reservation_plan_bytes,\'hex\'),reservation_initial_rows,reservation_initial_custody_bytes FROM truss.row_home_capacity')[0]
   return row
  def reserve(ordinal,ctx):
   c.run('SELECT truss.capacity_reserve_original(:ordinal,:context,:plan,4,8192,:layout,:resource)',ordinal=ordinal,context=ctx,plan=plan,layout=frozen[paths[0]],resource=frozen[paths[5]])
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
  ctx=context(0);reserve(0,ctx);admit(0)
  def finalize(ordinal):
   c.run("UPDATE truss.row_home_operation SET phase='application_finalized',readiness_generation=0,sealed_generation=0,application_generation=0,application_result_bytes=decode('abcd','hex') WHERE original_writer_xid=pg_current_xact_id_if_assigned() AND operation_ordinal=:n",n=ordinal)
  finalize(0);c.run('SELECT truss.capacity_release_original(:c,:p)',c=ctx,p=plan)
  first=ledger();c.run('SET CONSTRAINTS truss.capacity_cache_check IMMEDIATE')
  expect('early-closed-A-one-verification',[[1]],c.run('SELECT count(*) FROM truss.schedule_probe_calls'))
  c.run('SET CONSTRAINTS host_probe.host_guard IMMEDIATE')
  # Actual reservation UPDATE reaches its deferred constraint immediately, before
  # original registry admission. Fail and contain; ordinal1 remains consumed.
  ctx1=context(1)
  refusal('immediate-mode-blocks-next-native-reservation','55000','SELECT truss.capacity_reserve_original(1,:context,:plan,4,8192,:layout,:resource)',context=ctx1,plan=plan,layout=frozen[paths[0]],resource=frozen[paths[5]])
  expect('failed-next-reservation-preserves-A',first,ledger())
  expect('failed-next-reservation-restores-cache',[[xid,4,4]],c.run('SELECT writer_xid::text,dirty_generation,verified_generation FROM truss.capacity_check_memo'))
  expect('failed-next-reservation-keeps-only-original-A',[[0]],c.run('SELECT operation_ordinal FROM truss.row_home_operation'))
  # Reassert only this installed-owned constraint, before actual capacity effects.
  binding=c.run("SELECT k.oid,t.oid,p.oid,p.proowner,convert_to(pg_get_functiondef(p.oid),'UTF8') FROM pg_constraint k JOIN pg_trigger t ON t.tgconstraint=k.oid JOIN pg_proc p ON p.oid=t.tgfoid WHERE k.connamespace='truss'::regnamespace AND k.conname='capacity_cache_check'")[0]
  defer_sql='SELECT truss.capacity_defer_check_original(CAST(:c AS oid),CAST(:t AS oid),CAST(:p AS oid),CAST(:o AS oid),:b)'
  def args(values=binding):return dict(zip(['c','t','p','o','b'],values))
  wrong=binding.copy();wrong[4]=b'wrong original body'
  refusal('wrong-original-body','55000',defer_sql,**args(wrong))
  wrong=binding.copy();wrong[3]+=1
  refusal('wrong-original-owner','55000',defer_sql,**args(wrong))
  def catalog_fault(name,mutation):
   c.run('SAVEPOINT catalog_fault');c.run(mutation)
   try:c.run(defer_sql,**args())
   except pg8000.exceptions.DatabaseError as e:expect(name,'55000',e.args[0]['C'])
   else:raise ValueError('Expected original catalog refusal')
   c.run('ROLLBACK TO SAVEPOINT catalog_fault');c.run('RELEASE SAVEPOINT catalog_fault')
  catalog_fault('duplicate-qualified-constraint-name',"CREATE TABLE truss.name_collision(value int); CREATE CONSTRAINT TRIGGER capacity_cache_check AFTER UPDATE ON truss.name_collision DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION host_probe.check_value()")
  catalog_fault('disabled-original-trigger','ALTER TABLE truss.capacity_check_memo DISABLE TRIGGER capacity_cache_check')
  catalog_fault('original-routine-security-drift','ALTER FUNCTION truss.capacity_cache_check_original() SECURITY DEFINER')
  catalog_fault('original-routine-public-execute-drift','GRANT EXECUTE ON FUNCTION truss.capacity_cache_check_original() TO PUBLIC')
  catalog_fault('native-replica-mode-refusal',"SET LOCAL session_replication_role='replica'")
  c.run(defer_sql,**args())
  expect('recognized-private-deferral-success',[[1]],c.run('SELECT 1'))

  c.run('SAVEPOINT host_guard_check')
  try:c.run('UPDATE host_probe.value SET value=-1 WHERE id=1')
  except pg8000.exceptions.DatabaseError as e:expect('named-truss-deferral-preserves-host-immediate-guard','23514',e.args[0]['C'])
  else:raise ValueError('Host constraint mode unexpectedly changed')
  c.run('ROLLBACK TO SAVEPOINT host_guard_check');c.run('RELEASE SAVEPOINT host_guard_check')
  expect('host-value-preserved',[[7]],c.run('SELECT value FROM host_probe.value'))
  ctx2=context(2);reserve(2,ctx2);admit(2);finalize(2)
  c.run('SELECT truss.capacity_release_original(:c,:p)',c=ctx2,p=plan)
  c.run('SET CONSTRAINTS truss.capacity_cache_check IMMEDIATE')
  expect('later-B-one-additional-verification',[[2]],c.run('SELECT count(*) FROM truss.schedule_probe_calls'))
  expect('two-operations-generation-eight-proof',[[xid,8,8]],c.run('SELECT writer_xid::text,dirty_generation,verified_generation FROM truss.capacity_check_memo'))
  expect('two-original-finalized-members-before-commit',[[0,'application_finalized'],[2,'application_finalized']],c.run('SELECT operation_ordinal,phase FROM truss.row_home_operation ORDER BY operation_ordinal'))
  c.run('COMMIT')
  expect('independent-committed-A-and-B',[[0,'application_finalized'],[2,'application_finalized']],foreign.run('SELECT operation_ordinal,phase FROM truss.row_home_operation ORDER BY operation_ordinal'))
  expect('independent-complete-closeout-rows',[[2]],foreign.run('SELECT retained_rows FROM truss.row_home_capacity'))
  expect('host-guard-remains-original-committed-value',[[7]],foreign.run('SELECT value FROM host_probe.value'))
  expect('independent-committed-cache-generation',[[xid,8,8]],foreign.run('SELECT writer_xid::text,dirty_generation,verified_generation FROM truss.capacity_check_memo'))
  # Equal ledger images still invalidate within a new original actual transaction.
  c.run('BEGIN');new_xid=c.run('SELECT pg_current_xact_id()::text')[0][0]
  c.run('UPDATE truss.row_home_capacity SET retained_rows=retained_rows')
  expect('new-epoch-equal-image-invalidates',[[new_xid,1,None]],c.run('SELECT writer_xid::text,dirty_generation,verified_generation FROM truss.capacity_check_memo'))
  c.run('COMMIT')
  expect('new-epoch-original-proof',[[new_xid,1,1]],foreign.run('SELECT writer_xid::text,dirty_generation,verified_generation FROM truss.capacity_check_memo'))
  expect('equal-image-one-more-verification',[[3]],foreign.run('SELECT count(*) FROM truss.schedule_probe_calls'))
  # Generation exhaustion is fault-injected only in this administrative scope.
  c.run('BEGIN');active_xid=c.run('SELECT pg_current_xact_id()::text')[0][0]
  c.run('SAVEPOINT exhausted')
  c.run('UPDATE truss.capacity_check_memo SET writer_xid=pg_current_xact_id_if_assigned(),dirty_generation=9223372036854775807,verified_generation=NULL')
  before=ledger()
  try:c.run('UPDATE truss.row_home_capacity SET retained_rows=retained_rows')
  except pg8000.exceptions.DatabaseError as e:expect('generation-max-refuses-before-wrap','54000',e.args[0]['C'])
  else:raise ValueError('Expected exhausted generation refusal')
  c.run('ROLLBACK TO SAVEPOINT exhausted');c.run('ROLLBACK')
  expect('exhaustion-rollback-preserves-original-ledger',before,ledger())
  expect('exhaustion-rollback-preserves-prior-proof',[[new_xid,1,1]],c.run('SELECT writer_xid::text,dirty_generation,verified_generation FROM truss.capacity_check_memo'))
 finally:
  for c in connections:c.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()):raise ValueError('Original source drift')
receipt={'scope':'Native tuple/name/body/owner/attribute recognition and original guarded named deferral with actual capacity operations; administrative original registration fixture, not complete installed authority','serverVersion':version,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installerReady':False,'nativeFullReservationQualified':False,'acceptanceCasesPromoted':[],'limitations':['Original tuple captured from isolated administrative installation; complete authenticated registry/profile/dependency/DDL closure still required','Verification audit counts actual cache proof writes; no complete callback/native-work/copy budget qualification','Manual ordinal0/1-burn/2 fixture is not original host issuer factory','Administrative phase updates are not protected finalization or ordinary graph/security acceptance','Exact original native constraint identity/name collision/role/DDL dependency and all seven-body installation remain required']}
with output.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'installerReady':False}))
