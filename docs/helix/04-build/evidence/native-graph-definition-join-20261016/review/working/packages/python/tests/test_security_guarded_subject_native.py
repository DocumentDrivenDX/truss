"""Restricted native caller plus qualified caller/executor fact guards."""
import json,sys,os
from pathlib import Path
from unittest.mock import patch
from psycopg import sql
from truss import Ok,Error
from truss._psycopg_fact_cut import _FactRelationComparison
import test_security_catalog_subject_native as native
ROOT=Path(__file__).resolve().parents[3]
subject=native.subject

class GuardedSubjectTests(native.NativeCatalogSubjectTests):
 for name in tuple(n for n in dir(native.NativeCatalogSubjectTests) if n.startswith('test_')):locals()[name]=None
 def guarded_setup(self,disabled=None):
  mapping,c,h,t,selection,inspector=self.setup_subject()
  source=(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text()
  self.admin.execute(source)
  self.admin.execute(sql.SQL('ALTER FUNCTION truss.runtime_fence_authorization_fact_write() OWNER TO {}').format(sql.Identifier(self.installation.owner_role)))
  relations=[]
  for name in ('object','catalog_subject_map'):
   self.admin.execute(sql.SQL('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON {} FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write()').format(sql.Identifier('truss',name)))
   self.admin.execute(sql.SQL('ALTER TABLE {} ENABLE ALWAYS TRIGGER fact_write_fence').format(sql.Identifier('truss',name)))
   oid,owner=self.admin.execute('SELECT oid,relowner FROM pg_class WHERE oid=%s::regclass',('truss.'+name,)).fetchone()
   relations.append(_FactRelationComparison('truss',name,oid,owner,source.split('AS $$',1)[1].split('$$;',1)[0]))
  if disabled:self.admin.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER fact_write_fence').format(sql.Identifier('truss',disabled)))
  self.host.detach();self.admin.commit();self.admin.execute('BEGIN');self.host=native.catalog.adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  return mapping,c,h,t,selection,inspector,tuple(relations)
 def test_complete_guarded_chain_without_raw_caller_privileges(self):
  """@covers US-056-AC2; @covers US-056-AC9; component prerequisites only."""
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  for table in ('truss.object','truss.catalog_subject_map'):
   for privilege in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE'):
    self.assertEqual(c.execute('SELECT pg_catalog.has_table_privilege(%s,%s)',(table,privilege)).fetchone(),(False,))
  original_encoder=subject.encode_literal_key_tuple;original_read=subject.run_owned_catalog_resource_read;encoded=[];delegated=[]
  def encode(*args,**kwargs):
   for relation in relations:
    self.assertEqual(self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND relation=%s AND mode='ShareLock' AND granted)",(c.info.backend_pid,relation.oid)).fetchone(),(True,))
   encoded.append(True);return original_encoder(*args,**kwargs)
  def execute(*args,**kwargs):
   self.assertEqual(len(kwargs['fact_relations']),1);self.assertEqual(kwargs['fact_relations'][0].name,'object')
   delegated.append(True);return original_read(*args,**kwargs)
  with patch.object(subject,'encode_literal_key_tuple',encode),patch.object(subject,'run_owned_catalog_resource_read',execute):
   result=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertEqual(encoded,[True,True]);self.assertEqual(delegated,[True])
  self.assertEqual([r['key'] for r in result.value['rows']],[[{'string':'r1'}]])
  self.assertEqual(result.value['rows'][0]['output'][0]['disposition'],'withheld')
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/'decision.json').write_text(json.dumps(result.value,indent=2)+'\n')
 def assert_disabled_guard(self,disabled):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup(disabled)
  with patch.object(subject,'encode_literal_key_tuple') as encoder,patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);attempt=h._custody.last_attempt
  self.assertEqual(str(attempt.error),'Exact installed ALWAYS fact guard required');self.assertEqual(attempt.phase,'contained');self.assertIsNone(attempt.cleanup_error)
 def test_disabled_object_guard_refuses_before_codec_and_executor(self):
  self.assert_disabled_guard('object')
 def test_disabled_subject_map_guard_refuses_before_codec_and_executor(self):
  self.assert_disabled_guard('catalog_subject_map')
 def test_missing_mandatory_cut_never_calls_inspector_or_hosts(self):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  with patch.object(type(h),'_run_operation') as operation,patch.object(subject,'_prepare_subject_operation') as prepare:
   with self.assertRaisesRegex(ValueError,'Mandatory native caller fact cuts required'):
    subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,None)
   operation.assert_not_called();prepare.assert_not_called()

 def test_invalid_column_carriers_refuse_before_inspector_and_hosts(self):
  from dataclasses import replace,dataclass
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  @dataclass
  class ForeignColumn:
   name:str='foreign'
  for columns in ([],iter(()),(ForeignColumn(),),(None,)*1601):
   invalid=(replace(relations[0],columns=columns),relations[1])
   with patch.object(type(h),'_run_operation') as operation,patch.object(subject,'_prepare_subject_operation') as prepare:
    with self.assertRaisesRegex(ValueError,'Exact bounded caller fact column comparisons required'):
     subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,invalid)
    operation.assert_not_called();prepare.assert_not_called()

 def test_caller_cut_blocks_all_delegated_executor_writes(self):
  """@covers US-056-AC2; @covers US-056-AC9; two-host component."""
  import psycopg
  import security_catalog_read as read
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  original_read=subject.run_owned_catalog_resource_read
  original_run=read.subprocess.run;states=[]
  def evaluate(*args,**kwargs):
   for command in ('UPDATE truss.object SET props=props','DELETE FROM truss.object','INSERT INTO truss.object SELECT * FROM truss.object','TRUNCATE truss.object CASCADE'):
    self.admin.execute('SAVEPOINT composed_writer')
    self.admin.execute("SET LOCAL lock_timeout='100ms'")
    try:
     with self.assertRaises(psycopg.errors.LockNotAvailable) as caught:self.admin.execute(command)
     self.assertEqual(caught.exception.diag.message_primary,'canceling statement due to lock timeout')
     states.append(caught.exception.sqlstate)
    finally:
     self.admin.execute('ROLLBACK TO composed_writer');self.admin.execute('RELEASE composed_writer')
   self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(10,))
   return original_run(*args,**kwargs)
  def delegated(*args,**kwargs):
   with patch.object(read.subprocess,'run',evaluate):
    value=original_read(*args,**kwargs)
   if not isinstance(value,Ok):raise AssertionError(str(self.host._custody.last_attempt.error))
   return value
  with patch.object(subject,'run_owned_catalog_resource_read',delegated):
   result=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertEqual(states,['55P03']*4)
  self.assertEqual([r['key'] for r in result.value['rows']],[[{'string':'r1'}]])
  self.assertEqual(result.value['rows'][0]['output'][0]['disposition'],'withheld')

 def test_fresh_read_after_public_assignment_revocation(self):
  """@covers US-057-AC3; actual public writer and fresh component read."""
  import psycopg
  from truss import adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration,CatalogDocument
  from truss.groups import UpdateObject,StoredObjectReference,AuthoredValue,RequestNone,GroupSuccess
  from truss.contracts import BooleanValue,MapValue
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  first=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
  self.assertIsInstance(first,Ok,str(h._custody.last_attempt.error))
  self.assertEqual([r['key'] for r in first.value['rows']],[[{'string':'r1'}]])
  h.detach();c.commit();self.host.detach();self.admin.commit()
  self.admin.execute('CREATE ROLE assignment_revoker LOGIN;GRANT catalog_fact_writer TO assignment_revoker WITH SET FALSE')
  self.addCleanup(self.admin.execute,'DROP OWNED BY assignment_revoker;DROP ROLE assignment_revoker')
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='assignment_revoker'
  writer=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000');self.addCleanup(writer.close)
  self.assertEqual(writer.execute('SELECT session_user,current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone(),('assignment_revoker','assignment_revoker',False,False))
  writer.execute('BEGIN');wh=adopt_psycopg_host(writer);self.addCleanup(wh.detach)
  wt=wh.adopt_transaction().value;assembly=create_reference_assembly(CatalogRuntimeConfiguration(),wh).value
  found=assembly.lookup_key_in_transaction(wt,document_id='domain',module_id='m',record_id='Assignment',key_id='pk',values=('a1',),bun_executable='/opt/homebrew/bin/bun')
  self.assertIsInstance(found,Ok,str(wh._custody.last_attempt.error))
  operation=UpdateObject(target=StoredObjectReference(identity=found.value.object.identity),set=(AuthoredValue(name='active',value=BooleanValue(value=False)),),unset=(),expected_version='1')
  context=assembly.group_context_in_transaction(wt).value
  source=json.loads(mapping.original_request)
  documents=tuple(CatalogDocument(m['pin']['documentId'],m['pin']['revision'],m['documentJson'].encode()) for m in source['modules'])
  changed=assembly.apply_in_transaction(wt,context.input((operation,),MapValue(entries=())),RequestNone(),documents=documents,bun_executable='/opt/homebrew/bin/bun')
  self.assertIsInstance(changed,Ok,str(wh._custody.last_attempt.error));self.assertIsInstance(changed.value,GroupSuccess)
  wh.detach();writer.commit()
  self.assertEqual(writer.info.transaction_status,psycopg.pq.TransactionStatus.IDLE)
  inventory=json.loads(mapping.accepted_catalog_assessment)['inventory']
  active=next(p['prop_id'] for p in inventory['properties'] if p['element']=='active')
  self.assertEqual(self.admin.execute("SELECT props->%s->>'value' FROM truss.object WHERE id=%s",(str(active),int(found.value.object.identity.id))).fetchone(),('false',))
  writer.close()
  c.execute('BEGIN');h=adopt_psycopg_host(c);self.addCleanup(h.detach);t=h.adopt_transaction().value
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  fresh=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
  self.assertIsInstance(fresh,Ok,str(h._custody.last_attempt.error));self.assertEqual(fresh.value['rows'],[])
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/'revocation-decisions.json').write_text(json.dumps({'before':first.value,'afterCommittedPublicUpdate':fresh.value,'writer':'assignment_revoker','authentication':'owned local fixture authentication; not production credential qualification'},indent=2)+'\n')

 def test_public_revoker_waits_for_caller_transaction_settlement(self):
  """@covers US-057-AC3; @covers US-057-AC2; public writer drain component."""
  import psycopg,threading,time
  from truss import adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration,CatalogDocument
  from truss.groups import UpdateObject,StoredObjectReference,AuthoredValue,RequestNone,GroupSuccess
  from truss.contracts import BooleanValue,MapValue
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  first=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
  self.assertIsInstance(first,Ok,str(h._custody.last_attempt.error))
  self.assertEqual([r['key'] for r in first.value['rows']],[[{'string':'r1'}]])
  self.host.detach();self.admin.commit()
  self.admin.execute('CREATE ROLE assignment_revoker LOGIN;GRANT catalog_fact_writer TO assignment_revoker WITH SET FALSE')
  self.addCleanup(self.admin.execute,'DROP OWNED BY assignment_revoker;DROP ROLE assignment_revoker')
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='assignment_revoker'
  writer=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000');self.addCleanup(writer.close)
  self.assertEqual(writer.execute('SELECT session_user,current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone(),('assignment_revoker','assignment_revoker',False,False))
  writer.execute('BEGIN');wh=adopt_psycopg_host(writer);self.addCleanup(wh.detach)
  wt=wh.adopt_transaction().value;assembly=create_reference_assembly(CatalogRuntimeConfiguration(),wh).value
  found=assembly.lookup_key_in_transaction(wt,document_id='domain',module_id='m',record_id='Assignment',key_id='pk',values=('a1',),bun_executable='/opt/homebrew/bin/bun')
  self.assertIsInstance(found,Ok,str(wh._custody.last_attempt.error))
  operation=UpdateObject(target=StoredObjectReference(identity=found.value.object.identity),set=(AuthoredValue(name='active',value=BooleanValue(value=False)),),unset=(),expected_version='1')
  context=assembly.group_context_in_transaction(wt).value
  source=json.loads(mapping.original_request)
  documents=tuple(CatalogDocument(m['pin']['documentId'],m['pin']['revision'],m['documentJson'].encode()) for m in source['modules'])
  outcomes=[];errors=[];blocking=[]
  def revoke():
   try:
    changed=assembly.apply_in_transaction(wt,context.input((operation,),MapValue(entries=())),RequestNone(),documents=documents,bun_executable='/opt/homebrew/bin/bun')
    self.assertIsInstance(changed,Ok,str(wh._custody.last_attempt.error));self.assertIsInstance(changed.value,GroupSuccess)
    wh.detach();writer.commit()
    self.assertEqual(writer.info.transaction_status,psycopg.pq.TransactionStatus.IDLE)
    outcomes.append('public-update-committed')
   except BaseException as error:
    errors.append(error);wh.detach();writer.rollback()
  worker=threading.Thread(target=revoke,daemon=True);pid=writer.info.backend_pid;holder=c.info.backend_pid
  worker.start()
  try:
   deadline=time.monotonic()+5
   while True:
    row=self.admin.execute("SELECT pg_catalog.pg_blocking_pids(%s),EXISTS(SELECT 1 FROM pg_catalog.pg_locks WHERE pid=%s AND relation='truss.object'::regclass AND NOT granted)",(pid,pid)).fetchone()
    if holder in row[0] and row[1]:blocking.append({'writerPid':pid,'callerPid':holder,'blockers':row[0],'ungrantedObjectLock':row[1]});break
    if errors:raise errors[0]
    if time.monotonic()>deadline:raise AssertionError('Public writer did not wait on original caller object cut')
    time.sleep(.01)
   self.assertEqual(outcomes,[])
  finally:
   h.detach();c.commit();worker.join(12)
   if worker.is_alive():writer.cancel();worker.join(2)
  self.assertFalse(worker.is_alive(),'Public writer did not drain after caller settlement')
  if errors:raise errors[0]
  self.assertEqual(outcomes,['public-update-committed'])
  inventory=json.loads(mapping.accepted_catalog_assessment)['inventory']
  active=next(p['prop_id'] for p in inventory['properties'] if p['element']=='active')
  self.assertEqual(self.admin.execute("SELECT props->%s->>'value' FROM truss.object WHERE id=%s",(str(active),int(found.value.object.identity.id))).fetchone(),('false',))
  writer.close()
  c.execute('BEGIN');h=adopt_psycopg_host(c);self.addCleanup(h.detach);t=h.adopt_transaction().value
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  fresh=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
  self.assertIsInstance(fresh,Ok,str(h._custody.last_attempt.error));self.assertEqual(fresh.value['rows'],[])
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/'drain-decisions.json').write_text(json.dumps({'before':first.value,'afterCommittedPublicUpdate':fresh.value,'writer':'assignment_revoker','blocking':blocking,'outcomes':outcomes,'authentication':'owned local fixture authentication; not production credential qualification'},indent=2)+'\n')

 def test_guarded_publication_after_native_completion_under_caller_lease(self):
  import psycopg
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup();delivered=[]
  def publish(packet):
   self.assertIs(type(packet),bytes);self.assertEqual(h._custody.last_attempt.phase,'released')
   self.assertFalse(h._custody.lease.acquire(blocking=False))
   nested=[];refused=h._run_operation(t,lambda *a:nested.append(True))
   self.assertIsInstance(refused,Error);self.assertEqual(nested,[])
   for r in relations:
    self.assertEqual(self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND relation=%s AND mode='ShareLock' AND granted)",(c.info.backend_pid,r.oid)).fetchone(),(True,))
   with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=100ms') as writer:
    with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute('UPDATE truss.object SET props=props')
   delivered.append(packet)
  result=subject.publish_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,publish)
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertEqual(delivered,[result.value])
  decision=json.loads(result.value);self.assertEqual([r['key'] for r in decision['rows']],[[{'string':'r1'}]])
  self.assertEqual(decision['rows'][0]['output'][0]['disposition'],'withheld')
  self.assertEqual(h._custody.last_attempt.phase,'published');self.assertIsNone(h._custody.pending)
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/'published-decision.json').write_bytes(result.value)
 def test_late_host_observation_failure_never_publishes(self):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup();delivered=[]
  original=type(h)._observe
  def observe(host,cursor):
   if host is h and host._custody.last_attempt.phase=='command_returned':raise ValueError('injected final publication observation failure')
   return original(host,cursor)
  with patch.object(type(h),'_observe',observe):
   result=subject.publish_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,delivered.append)
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(h._custody.last_attempt.error),'injected final publication observation failure')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)
 def test_uncertain_receiver_delivery_quarantines_without_retry(self):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup();delivered=[]
  def publish(packet):delivered.append(packet);raise RuntimeError('injected uncertain receiver delivery')
  result=subject.publish_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,publish)
  self.assertIsInstance(result,Error);self.assertEqual(len(delivered),1)
  self.assertEqual(result.error.code,'transaction_unusable');self.assertEqual(result.error.retry_scope,'none')
  self.assertTrue(h._custody.quarantined);self.assertEqual(str(h._custody.last_attempt.error),'injected uncertain receiver delivery')
  retry=subject.publish_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,publish)
  self.assertIsInstance(retry,Error);self.assertEqual(len(delivered),1)

 def test_deferred_publishers_refuse_before_inspector_and_hosts(self):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  async def asynchronous(packet):pass
  def generator(packet):yield packet
  class AsyncCallable:
   async def __call__(self,packet):pass
  for sink in (asynchronous,generator,AsyncCallable()):
   with patch.object(type(h),'_run_operation') as operation,patch.object(subject,'_prepare_subject_operation') as prepare:
    with self.assertRaisesRegex(ValueError,'Original synchronous private publisher required'):
     subject.publish_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,sink)
    operation.assert_not_called();prepare.assert_not_called()
 def test_non_none_receiver_completion_never_claims_published(self):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup();delivered=[]
  def sink(packet):delivered.append(packet);return True
  result=subject.publish_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,sink)
  self.assertIsInstance(result,Error);self.assertEqual(len(delivered),1);self.assertTrue(h._custody.quarantined)
  self.assertEqual(result.error.retry_scope,'none');self.assertEqual(h._custody.last_attempt.phase,'released')
  self.assertEqual(str(h._custody.last_attempt.error),'Exact synchronous publisher completion required')

 def _assert_receiver_drain(self,fail_receiver):
  """@covers US-057-AC2; selected synchronous publication drain component."""
  import psycopg,threading,time
  from truss import adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration,CatalogDocument
  from truss.groups import UpdateObject,StoredObjectReference,AuthoredValue,RequestNone,GroupSuccess
  from truss.contracts import BooleanValue,MapValue
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  self.host.detach();self.admin.commit()
  self.admin.execute('CREATE ROLE assignment_revoker LOGIN;GRANT catalog_fact_writer TO assignment_revoker WITH SET FALSE')
  self.addCleanup(self.admin.execute,'DROP OWNED BY assignment_revoker;DROP ROLE assignment_revoker')
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='assignment_revoker'
  writer=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000');self.addCleanup(writer.close)
  self.assertEqual(writer.execute('SELECT session_user,current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone(),('assignment_revoker','assignment_revoker',False,False))
  writer.execute('BEGIN');wh=adopt_psycopg_host(writer,statement_timeout_ms=10000,operation_timeout_ms=20000);self.addCleanup(wh.detach)
  wt=wh.adopt_transaction().value;assembly=create_reference_assembly(CatalogRuntimeConfiguration(),wh).value
  found=assembly.lookup_key_in_transaction(wt,document_id='domain',module_id='m',record_id='Assignment',key_id='pk',values=('a1',),bun_executable='/opt/homebrew/bin/bun')
  self.assertIsInstance(found,Ok,str(wh._custody.last_attempt.error))
  operation=UpdateObject(target=StoredObjectReference(identity=found.value.object.identity),set=(AuthoredValue(name='active',value=BooleanValue(value=False)),),unset=(),expected_version='1')
  context=assembly.group_context_in_transaction(wt).value;source=json.loads(mapping.original_request)
  documents=tuple(CatalogDocument(m['pin']['documentId'],m['pin']['revision'],m['documentJson'].encode()) for m in source['modules'])
  outcomes=[];errors=[];blocking=[];delivered=[]
  def revoke():
   try:
    changed=assembly.apply_in_transaction(wt,context.input((operation,),MapValue(entries=())),RequestNone(),documents=documents,bun_executable='/opt/homebrew/bin/bun')
    self.assertIsInstance(changed,Ok,str(wh._custody.last_attempt.error));self.assertIsInstance(changed.value,GroupSuccess)
    wh.detach();writer.commit();self.assertEqual(writer.info.transaction_status,psycopg.pq.TransactionStatus.IDLE)
    outcomes.append('public-update-committed')
   except BaseException as error:errors.append(error);wh.detach();writer.rollback()
  worker=threading.Thread(target=revoke,daemon=True);pid=writer.info.backend_pid;holder=c.info.backend_pid
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  def publish(packet):
   self.assertEqual(h._custody.last_attempt.phase,'released');self.assertIs(type(packet),bytes)
   worker.start();deadline=time.monotonic()+5
   while True:
    row=self.admin.execute("SELECT pg_catalog.pg_blocking_pids(%s),EXISTS(SELECT 1 FROM pg_catalog.pg_locks WHERE pid=%s AND relation='truss.object'::regclass AND NOT granted)",(pid,pid)).fetchone()
    if holder in row[0] and row[1]:blocking.append({'phase':'receiver','blockers':row[0],'writerPid':pid,'callerPid':holder,'ungrantedObjectLock':row[1]});break
    if errors:raise errors[0]
    if time.monotonic()>deadline:raise AssertionError('Public revoker did not block before receiver completion')
    time.sleep(.01)
   self.assertEqual(outcomes,[]);delivered.append(packet)
   if fail_receiver:raise RuntimeError('injected receiver delivery uncertainty during revocation')
  try:
   result=subject.publish_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,publish)
   if fail_receiver:
    self.assertIsInstance(result,Error);self.assertEqual(result.error.retry_scope,'none');self.assertTrue(h._custody.quarantined)
    self.assertEqual(str(h._custody.last_attempt.error),'injected receiver delivery uncertainty during revocation')
    self.assertEqual(len(delivered),1)
   else:
    self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertEqual(delivered,[result.value])
   decision=json.loads(delivered[0]);self.assertEqual([r['key'] for r in decision['rows']],[[{'string':'r1'}]])
   self.assertEqual(decision['rows'][0]['output'][0]['disposition'],'withheld')
   self.host.detach();self.admin.commit()
   blockers=self.admin.execute('SELECT pg_catalog.pg_blocking_pids(%s)',(pid,)).fetchone()[0]
   self.assertEqual(blockers,[holder]);self.assertEqual(outcomes,[])
   blocking.append({'phase':'receiver-uncertain-executor-settled' if fail_receiver else 'receiver-complete-executor-settled','blockers':blockers})
  finally:
   h.detach()
   if fail_receiver:c.rollback()
   else:c.commit()
   self.host.detach();self.admin.commit()
   if worker.ident is not None:
    worker.join(12)
    if worker.is_alive():writer.cancel();worker.join(2)
  self.assertFalse(worker.is_alive())
  if errors:raise errors[0]
  self.assertEqual(outcomes,['public-update-committed'])
  inventory=json.loads(mapping.accepted_catalog_assessment)['inventory'];active=next(p['prop_id'] for p in inventory['properties'] if p['element']=='active')
  self.assertEqual(self.admin.execute("SELECT props->%s->>'value' FROM truss.object WHERE id=%s",(str(active),int(found.value.object.identity.id))).fetchone(),('false',))
  writer.close()
  if fail_receiver:c,h,a,t=self.consumer()
  else:
   c.execute('BEGIN');h=adopt_psycopg_host(c);self.addCleanup(h.detach);t=h.adopt_transaction().value
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  fresh=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
  self.assertIsInstance(fresh,Ok,str(h._custody.last_attempt.error));self.assertEqual(fresh.value['rows'],[])
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/('receiver-uncertain-drain.json' if fail_receiver else 'receiver-drain.json')).write_text(json.dumps({'receiverDelivery':'uncertain' if fail_receiver else 'completed','callerSettlement':'rollback' if fail_receiver else 'commit','packetObservedByReceiver':decision,'afterCommittedRevocation':fresh.value,'blocking':blocking,'outcomes':outcomes},indent=2)+'\n')

 def test_public_revoker_waits_through_receiver_and_caller_settlement(self):
  self._assert_receiver_drain(False)
 def test_uncertain_receiver_keeps_revoker_blocked_until_caller_rollback(self):
  self._assert_receiver_drain(True)

 def _assert_stale_snapshot_refusal(self,isolation):
  import psycopg
  from truss import adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration,CatalogDocument
  from truss.groups import UpdateObject,StoredObjectReference,AuthoredValue,RequestNone,GroupSuccess
  from truss.contracts import BooleanValue,MapValue
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  self.host.detach();self.admin.commit();h.detach();c.rollback()
  c.execute('BEGIN ISOLATION LEVEL '+{'repeatable_read':'REPEATABLE READ','serializable':'SERIALIZABLE'}[isolation])
  h=adopt_psycopg_host(c);self.addCleanup(h.detach)
  adopted=h.adopt_transaction(isolation=isolation);self.assertIsInstance(adopted,Ok);t=adopted.value
  snapshot=c.execute('SELECT pg_catalog.pg_current_snapshot()::pg_catalog.text').fetchone()[0]
  self.admin.execute('CREATE ROLE assignment_revoker LOGIN;GRANT catalog_fact_writer TO assignment_revoker WITH SET FALSE')
  self.addCleanup(self.admin.execute,'DROP OWNED BY assignment_revoker;DROP ROLE assignment_revoker')
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='assignment_revoker'
  writer=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000');self.addCleanup(writer.close)
  self.assertEqual(writer.execute('SELECT session_user,current_user,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone(),('assignment_revoker','assignment_revoker',False,False))
  writer.execute('BEGIN');wh=adopt_psycopg_host(writer);self.addCleanup(wh.detach)
  wt=wh.adopt_transaction().value;assembly=create_reference_assembly(CatalogRuntimeConfiguration(),wh).value
  found=assembly.lookup_key_in_transaction(wt,document_id='domain',module_id='m',record_id='Assignment',key_id='pk',values=('a1',),bun_executable='/opt/homebrew/bin/bun')
  self.assertIsInstance(found,Ok,str(wh._custody.last_attempt.error))
  xid=writer.execute('SELECT pg_catalog.pg_current_xact_id()::pg_catalog.text').fetchone()[0]
  operation=UpdateObject(target=StoredObjectReference(identity=found.value.object.identity),set=(AuthoredValue(name='active',value=BooleanValue(value=False)),),unset=(),expected_version='1')
  context=assembly.group_context_in_transaction(wt).value;source=json.loads(mapping.original_request)
  documents=tuple(CatalogDocument(m['pin']['documentId'],m['pin']['revision'],m['documentJson'].encode()) for m in source['modules'])
  changed=assembly.apply_in_transaction(wt,context.input((operation,),MapValue(entries=())),RequestNone(),documents=documents,bun_executable='/opt/homebrew/bin/bun')
  self.assertIsInstance(changed,Ok,str(wh._custody.last_attempt.error));self.assertIsInstance(changed.value,GroupSuccess)
  wh.detach();writer.commit();self.assertEqual(writer.info.transaction_status,psycopg.pq.TransactionStatus.IDLE)
  self.assertEqual(c.execute('SELECT pg_catalog.pg_visible_in_snapshot(%s::pg_catalog.xid8,%s::pg_catalog.pg_snapshot)',(xid,snapshot)).fetchone(),(False,))
  self.assertEqual(self.admin.execute('SELECT pg_catalog.pg_visible_in_snapshot(%s::pg_catalog.xid8,pg_catalog.pg_current_snapshot())',(xid,)).fetchone(),(True,))
  inventory=json.loads(mapping.accepted_catalog_assessment)['inventory'];active=next(p['prop_id'] for p in inventory['properties'] if p['element']=='active')
  self.assertEqual(self.admin.execute("SELECT props->%s->>'value' FROM truss.object WHERE id=%s",(str(active),int(found.value.object.identity.id))).fetchone(),('false',))
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value;delivered=[]
  with patch.object(subject,'encode_literal_key_tuple') as encoder,patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.publish_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,delivered.append)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(h._custody.last_attempt.error),'Original selected subject transaction profile required')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)
  for r in relations:self.assertEqual(self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND relation=%s AND mode='ShareLock' AND granted)",(c.info.backend_pid,r.oid)).fetchone(),(False,))
  h.detach();c.rollback();self.host.detach();self.admin.commit()
  c.execute('BEGIN');h=adopt_psycopg_host(c);self.addCleanup(h.detach);t=h.adopt_transaction().value
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  fresh=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
  self.assertIsInstance(fresh,Ok,str(h._custody.last_attempt.error));self.assertEqual(fresh.value['rows'],[])
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/(isolation+'.json')).write_text(json.dumps({'isolation':isolation,'originalSnapshot':snapshot,'committedRevokerXid':xid,'visibleInOriginalSnapshot':False,'visibleInFreshSnapshot':True,'stalePublication':'refused-before-codec-evaluator-and-sink','freshDecision':fresh.value},indent=2)+'\n')
 def test_repeatable_read_snapshot_before_revocation_refuses_publication(self):
  self._assert_stale_snapshot_refusal('repeatable_read')
 def test_serializable_snapshot_before_revocation_refuses_publication(self):
  self._assert_stale_snapshot_refusal('serializable')
