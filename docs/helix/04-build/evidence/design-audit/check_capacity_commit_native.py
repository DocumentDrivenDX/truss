"""Explicit native capacity closeout; not automatic or semantic commit enforcement."""
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
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/capacity-reservation-source.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/capacity-accounting-source.owner-export.sql', 'packages/postgresql/native/issued-operation-admission/operation-admission.sql', 'docs/helix/02-design/contracts/row-home-capacity-initialization-v0.1.proposal.sql', 'docs/helix/02-design/contracts/bindings/truss-row-touch-retention-resource-v0.1.proposal.json', 'packages/postgresql/native/capacity-reservation/accounting.sql', 'docs/helix/04-build/evidence/design-audit/custody-codec-source.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/custody-size-source.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/capacity-inventory-source.owner-export.sql', 'docs/helix/04-build/evidence/design-audit/capacity-observation-source.owner-export.sql', 'packages/postgresql/native/capacity-reservation/observation.sql','docs/helix/04-build/evidence/design-audit/capacity-commit-source.owner-export.sql','packages/postgresql/native/capacity-reservation/commit-check.sql']
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
  def size(kind,cells):return len(('truss.custody.'+kind+'/0.1').encode())+3+9*len(cells)+sum(0 if v is None else len(v if isinstance(v,bytes) else str(v).encode()) for v in cells)
  def counters():return c.run('SELECT retained_rows,retained_custody_bytes,reserved_rows,reserved_custody_bytes FROM truss.row_home_capacity')[0]
  def parity():return c.run('SELECT * FROM truss.capacity_verify_inventory_original(:l,:r)',l=frozen[paths[0]],r=frozen[paths[5]])
  ctx=context(0);c.run('SAVEPOINT operation_a');reserve(0,ctx);admit(0)
  op=[xid,'0','mutation','admitted','0',None,None,None,ctx]+[bytes([n]) for n in range(1,7)]+[None]
  operation_size=size('operation',op)
  expect('native-insert-derived-complete-size',[1,operation_size,3,8192-operation_size],counters())
  expect('insert-full-inventory-parity',[[1,operation_size]],parity())
  closeout='SELECT 1 FROM (SELECT truss.capacity_commit_check_original(:l,:r)) original_closeout'
  refusal('active-reservation-closeout','55000',closeout,l=frozen[paths[0]],r=frozen[paths[5]])
  blob=b'\x01';touch=[xid,'object','1','1','1','1','1',None]+[blob]*4;touch_size=size('touch',touch)
  c.run("INSERT INTO truss.row_home_touch VALUES (pg_current_xact_id_if_assigned(),'object',1,1,1,1,1,NULL,:b,:b,:b,:b)",b=blob)
  total=operation_size+touch_size;remaining=8192-total
  expect('native-touch-insert-derived-size',[2,total,2,remaining],counters())
  c.run("UPDATE truss.row_home_touch SET original_home_bytes=decode(repeat('01',20),'hex')")
  total+=19;remaining-=19
  expect('native-positive-growth-spent',[2,total,2,remaining],counters())
  c.run("UPDATE truss.row_home_touch SET original_home_bytes=decode('01','hex')")
  total-=19
  expect('native-shrink-without-refund',[2,total,2,remaining],counters())
  expect('post-shrink-full-parity',[[2,total]],parity())
  refusal('touch-identity-rewrite','55000','UPDATE truss.row_home_touch SET owner_id=2')
  refusal('touch-delete-refused','55000','DELETE FROM truss.row_home_touch')
  refusal('touch-truncate-refused','55000','TRUNCATE truss.row_home_touch')
  refusal('operation-context-rewrite','55000',"UPDATE truss.row_home_operation SET original_context_bytes=decode('01','hex')")
  refusal('operation-delete-refused','55000','DELETE FROM truss.row_home_operation')
  refusal('operation-truncate-refused','55000','TRUNCATE truss.row_home_operation CASCADE')
  refusal('row-growth-over-remaining','54000',"UPDATE truss.row_home_touch SET original_home_bytes=decode(repeat('01',8192),'hex')")
  refusal('constraint-after-observer-restores-ledger','23514',"UPDATE truss.row_home_touch SET dirty_generation=0,original_home_bytes=decode(repeat('01',4),'hex')")
  # Administrative phase update: derives capacity correctly but is not proof of
  # protected guard, semantic effect or finalizer authority.
  finalized=op.copy();finalized[3]='application_finalized';finalized[5:8]=['0']*3;finalized[-1]=b'\xab\xcd'
  final_size=size('operation',finalized);growth=final_size-operation_size
  c.run("UPDATE truss.row_home_operation SET phase='application_finalized',readiness_generation=0,sealed_generation=0,application_generation=0,application_result_bytes=decode('abcd','hex')")
  total+=growth;remaining-=growth
  expect('before-finalization-complete-delta',[2,total,2,remaining],counters())
  expect('finalized-full-parity',[[2,total]],parity())
  refusal('finalized-but-unreleased-closeout','55000',closeout,l=frozen[paths[0]],r=frozen[paths[5]])
  refusal('finalized-member-rewrite','55000',"UPDATE truss.row_home_operation SET application_result_bytes=decode('ab','hex')")
  c.run('SELECT truss.capacity_release_original(:c,:p)',c=ctx,p=plan)
  expect('release-retains-full-framed-totals',[2,total,0,0],counters())
  expect('released-closeout-success',[[1]],c.run(closeout,l=frozen[paths[0]],r=frozen[paths[5]]))
  refusal('touch-write-without-held-reservation','55000','UPDATE truss.row_home_touch SET dirty_generation=2')
  c.run('RELEASE SAVEPOINT operation_a');c.run('ROLLBACK')
  expect('host-rollback-restores-empty-ledger',[0,0,0,0],counters())
  expect('host-rollback-restores-empty-members',[[0,0]],parity())
  # A separate actual transaction commits administrative finalized A. Native
  # durability is observed from a distinct connection, not an in-process cache.
  c.run('BEGIN');xid=c.run('SELECT pg_current_xact_id()::text')[0][0]
  ctx=context(0);reserve(0,ctx);admit(0)
  finalized=[xid,'0','mutation','application_finalized','0','0','0','0',ctx]+[bytes([n]) for n in range(1,7)]+[b'\xab\xcd']
  committed_size=size('operation',finalized)
  c.run("UPDATE truss.row_home_operation SET phase='application_finalized',readiness_generation=0,sealed_generation=0,application_generation=0,application_result_bytes=decode('abcd','hex')")
  c.run('SELECT truss.capacity_release_original(:c,:p)',c=ctx,p=plan)
  c.run(closeout,l=frozen[paths[0]],r=frozen[paths[5]]);c.run('COMMIT')
  expect('separate-connection-committed-original-row',[[xid,'0','application_finalized','abcd']],foreign.run("SELECT original_writer_xid::text,operation_ordinal::text,phase,encode(application_result_bytes,'hex') FROM truss.row_home_operation"))
  expect('committed-counters-visible-separately',[[1,committed_size,0,0]],foreign.run('SELECT retained_rows,retained_custody_bytes,reserved_rows,reserved_custody_bytes FROM truss.row_home_capacity'))
  c.run('BEGIN')
  refusal('foreign-profile-closeout','55000',closeout,l=frozen[paths[0]],r=b'foreign')
  c.run('SAVEPOINT corrupt_counter');c.run('UPDATE truss.row_home_capacity SET retained_custody_bytes=retained_custody_bytes+1')
  try:c.run(closeout,l=frozen[paths[0]],r=frozen[paths[5]])
  except pg8000.exceptions.DatabaseError as e:expect('committed-byte-counter-corruption','55000',e.args[0]['C'])
  else:raise ValueError('Expected corrupt counter refusal')
  c.run('ROLLBACK TO SAVEPOINT corrupt_counter')
  expect('counter-rollback-preserves-committed-A',[[1,committed_size]],parity())
  # Fault injection: only the isolated administrative fixture bypasses an
  # observer to represent a preexisting orphan. The checker never repairs it.
  c.run('SAVEPOINT orphan');c.run('ALTER TABLE truss.row_home_operation DISABLE TRIGGER capacity_operation_insert')
  c.run("INSERT INTO truss.row_home_operation VALUES ('18446744073709551615'::xid8,8,'mutation','admitted',0,NULL,NULL,NULL,decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),decode('01','hex'),NULL)")
  orphan=size('operation',['18446744073709551615','8','mutation','admitted','0',None,None,None]+[b'\x01']*7+[None])
  c.run('UPDATE truss.row_home_capacity SET retained_rows=2,retained_custody_bytes=:n',n=committed_size+orphan)
  expect('orphan-has-size-parity',[[2,committed_size+orphan]],parity())
  try:c.run(closeout,l=frozen[paths[0]],r=frozen[paths[5]])
  except pg8000.exceptions.DatabaseError as e:expect('foreign-unfinished-orphan-closeout','55000',e.args[0]['C'])
  else:raise ValueError('Expected orphan closeout refusal')
  c.run('ROLLBACK TO SAVEPOINT orphan');c.run('ROLLBACK')
  expect('orphan-rollback-preserves-committed-A',[[1,committed_size]],parity())
  expect('repeat-closeout-keeps-committed-A',[[1]],c.run(closeout,l=frozen[paths[0]],r=frozen[paths[5]]))
 finally:
  for c in connections:c.close()
  server.cleanup()
if any((ROOT/p).read_bytes()!=v for p,v in frozen.items()):raise ValueError('Original source drift')
receipt={'scope':'Explicit native capacity closeout composed with event-derived framing and real commit/independent visibility; administrative semantic fixture, not protected engine authority','serverVersion':version,'observations':checks,'sourceSha256':{p:hashlib.sha256(v).hexdigest() for p,v in frozen.items()},'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installerReady':False,'nativeFullReservationQualified':False,'acceptanceCasesPromoted':[],'limitations':['Administrative phase transition is not protected finalizer or ordinary-role graph acceptance','Trigger identities/order/dependencies/ACL/security and framed resource-profile adoption remain uninstalled','Complete commit guards and all seven mandatory bodies remain required','No complete native work/cancellation/physical overhead qualification','Cleanup deliberately refuses; qualified deletion/retention path still required','Explicit function call only; no automatic deferred/commit-hook enforcement or all-cohort work qualification']}
with output.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(checks),'installerReady':False}))
