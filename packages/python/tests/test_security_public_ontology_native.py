# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual public graph ontology fixture; candidate lowering, not admitted security."""
import json,os,subprocess
from pathlib import Path
import psycopg
from truss import Ok
from truss.contracts import TextValue,BooleanValue
from truss.groups import CreateObject,CreateEdge,AuthoredValue,RootlessOwnership,AliasObjectReference,NullOrderKey,GroupSuccess,RequestNone
import test_group_create_native as groups
RECORDS={'Client':{'code':'string'},'Project':{'code':'string'},'Staff':{'code':'string','login':'string'},'Resource':{'code':'string','secret':'string'},'Assignment':{'code':'string','active':'boolean'}}
LINKS={'staff_assignment':('Staff','Assignment'),'assignment_project':('Assignment','Project'),'resource_project':('Resource','Project'),'project_client':('Project','Client')}
class PublicOntologySecurityTests(groups.PublicCreateGroupTests):
 for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
 def setUp(self):
  self._security_connections=[]
  super().setUp()
 def _track_owned_connection(self,connection):
  self._security_connections.append(connection)
  self.addCleanup(connection.close)
 def _close_owned_connections(self):
  for connection in reversed(self._security_connections):
   if not connection.closed:connection.close()
 def test_native_statement_data_writer_guard_coordinates_raw_and_graph_homes(self):
  from truss import adopt_psycopg_host
  from truss._security_home_installation import bootstrap_security_homes_in_transaction
  connection,seed_host,assembly,seed_tx=self.ready();seed_input,seed_request=self.input(assembly,seed_tx);self.apply(assembly,seed_tx,seed_input,seed_request);seed_host.detach();connection.commit()
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  identity=self.installation.installation_id.encode();profile=b'native-data-writer-spike/0.2'
  self.assertIsInstance(bootstrap_security_homes_in_transaction(self.host,tx,installation_identity=identity,authored_profile=profile,max_retained=8),Ok)
  self.admin.execute('CREATE SCHEMA relational_fixture;CREATE TABLE relational_fixture.assignment(id int PRIMARY KEY,active boolean NOT NULL);INSERT INTO relational_fixture.assignment VALUES(1,true)')
  source=(Path(__file__).resolve().parents[3]/'packages/postgresql/native/security-data-writer-guard-pg18.sql').read_text()
  self.admin.execute(psycopg.sql.SQL('SET LOCAL ROLE {}').format(psycopg.sql.Identifier(self.installation.owner_role)));self.admin.execute(source);self.admin.execute('RESET ROLE')
  homes=[('truss','object'),('truss','edge'),('relational_fixture','assignment')];home_oids=[]
  for schema,table in homes:
   oid=self.admin.execute('SELECT pg_catalog.to_regclass(%s)::oid',(schema+'.'+table,)).fetchone()[0];home_oids.append(oid)
   for when,name in [('BEFORE','aa_security_data_gate'),('AFTER','zz_security_data_advance')]:
    self.admin.execute(psycopg.sql.SQL('CREATE TRIGGER {} {} INSERT OR UPDATE OR DELETE OR TRUNCATE ON {}.{} FOR EACH STATEMENT EXECUTE FUNCTION truss.security_data_writer_guard({},{},{})').format(psycopg.sql.Identifier(name),psycopg.sql.SQL(when),psycopg.sql.Identifier(schema),psycopg.sql.Identifier(table),psycopg.sql.Literal(identity.hex()),psycopg.sql.Literal(profile.hex()),psycopg.sql.Literal(str(oid))))
    self.admin.execute(psycopg.sql.SQL('ALTER TABLE {}.{} ENABLE ALWAYS TRIGGER {}').format(psycopg.sql.Identifier(schema),psycopg.sql.Identifier(table),psycopg.sql.Identifier(name)))
  self.admin.execute('GRANT USAGE ON SCHEMA relational_fixture TO consumer;GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE ON relational_fixture.assignment TO consumer')
  self.host.detach();self.admin.commit()
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as writer:
   writer.execute('BEGIN');writer.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=1')
   self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=1').fetchone(),(True,))
   writer.rollback();self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(1,))
   writer.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=1')
   self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(2,))
   self.admin.execute('INSERT INTO truss.policy_publication_claim VALUES(%s,%s,%s,2,false)',(b'original-active',identity,profile))
   for statement in ['UPDATE relational_fixture.assignment SET active=true','INSERT INTO relational_fixture.assignment VALUES(2,true)','DELETE FROM relational_fixture.assignment','TRUNCATE relational_fixture.assignment']:
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):writer.execute(statement)
    self.assertEqual(self.admin.execute('TABLE relational_fixture.assignment').fetchall(),[(1,False)])
    self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(2,))
   self.admin.execute('UPDATE truss.policy_publication_claim SET settled=true')
   writer.execute('UPDATE relational_fixture.assignment SET active=true');self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(3,))
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):writer.execute('ALTER TABLE relational_fixture.assignment DISABLE TRIGGER aa_security_data_gate')
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):writer.execute("SET session_replication_role='replica'")
  for statement,generation in [('UPDATE truss.object SET props=props',4),('DELETE FROM truss.edge WHERE false',5)]:
   self.admin.execute(statement);self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(generation,))
  # Each zero-row trigger event conservatively advances too.
  self.admin.execute('BEGIN');self.admin.execute('UPDATE truss.object SET props=props');self.admin.execute('ROLLBACK')
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(5,))
  import threading,time
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR SHARE')
  self.admin.execute('INSERT INTO truss.policy_publication_claim VALUES(%s,%s,%s,5,false)',(b'pending-native-original',identity,profile))
  pending=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(pending);pid=pending.info.backend_pid;outcomes=[]
  def update_after_guard():
   try:pending.execute('UPDATE relational_fixture.assignment SET active=false');outcomes.append('incorrect success')
   except psycopg.Error as error:outcomes.append(error.sqlstate)
  task=threading.Thread(target=update_after_guard);task.start();deadline=time.monotonic()+5;blocked=False
  try:
   while time.monotonic()<deadline:
    if self.admin.info.backend_pid in self.admin.execute('SELECT pg_catalog.pg_blocking_pids(%s)',(pid,)).fetchone()[0]:blocked=True;break
    time.sleep(.01)
   self.assertTrue(blocked);self.assertTrue(task.is_alive());self.admin.commit()
  finally:
   self.admin.rollback();task.join(11)
  self.assertFalse(task.is_alive());self.assertEqual(outcomes,['42501'])
  self.assertEqual(self.admin.execute('TABLE relational_fixture.assignment').fetchall(),[(1,True)]);self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(5,))
  with psycopg.connect(**params,autocommit=True) as old_snapshot:
   old_snapshot.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):old_snapshot.execute('UPDATE relational_fixture.assignment SET active=false')
   old_snapshot.rollback()
  self.admin.execute('UPDATE truss.policy_publication_claim SET settled=true')
  with psycopg.connect(**params,autocommit=True) as composite:
   composite.execute('INSERT INTO relational_fixture.assignment VALUES(2,false) ON CONFLICT(id) DO UPDATE SET active=excluded.active')
   self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(7,))
   composite.execute('MERGE INTO relational_fixture.assignment t USING (VALUES(2,true),(3,false)) s(id,active) ON t.id=s.id WHEN MATCHED AND s.active THEN UPDATE SET active=s.active WHEN MATCHED THEN DELETE WHEN NOT MATCHED THEN INSERT VALUES(s.id,s.active)')
   self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(10,))
  self.admin.execute(psycopg.sql.SQL("CREATE FUNCTION relational_fixture.late_claim() RETURNS trigger LANGUAGE plpgsql AS $body$ BEGIN INSERT INTO truss.policy_publication_claim VALUES({}, {}, {}, 10, false); RETURN NULL; END $body$").format(psycopg.sql.Literal(b'late-after-effect'),psycopg.sql.Literal(identity),psycopg.sql.Literal(profile)))
  self.admin.execute('CREATE TRIGGER mm_late_claim AFTER UPDATE ON relational_fixture.assignment FOR EACH STATEMENT EXECUTE FUNCTION relational_fixture.late_claim()')
  with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.admin.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=1')
  self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=1').fetchone(),(True,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'late-after-effect',)).fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(10,))
  self.admin.execute('DROP TRIGGER mm_late_claim ON relational_fixture.assignment')
  self.admin.execute('UPDATE truss.policy_generation_guard SET generation=9223372036854775806')
  with psycopg.connect(**params,autocommit=True) as overflow:
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):overflow.execute('INSERT INTO relational_fixture.assignment VALUES(4,false) ON CONFLICT(id) DO UPDATE SET active=excluded.active')
  self.assertEqual(self.admin.execute('SELECT count(*) FROM relational_fixture.assignment WHERE id=4').fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(9223372036854775806,))
  # A statement trigger cannot refresh the already-selected outer DML snapshot.
  self.admin.execute('UPDATE truss.policy_generation_guard SET generation=10')
  self.admin.execute('UPDATE relational_fixture.assignment SET active=true')
  stale=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(stale)
  from truss._security_data_writer import write_data_in_transaction
  def race(prelock):
   self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute('SELECT generation FROM truss.policy_generation_guard FOR UPDATE');self.admin.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=1')
   expected=self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone()[0]
   results=[]
   def conditional_write():
    try:
     stale.execute('BEGIN')
     if prelock:
      coordinated=adopt_psycopg_host(stale,statement_timeout_ms=10000,operation_timeout_ms=30000);coordinated_tx=coordinated.adopt_transaction().value
      def effect(cursor):
       cursor.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=2 AND EXISTS(SELECT 1 FROM relational_fixture.assignment WHERE id=1 AND active)');results.append(cursor.rowcount)
      try:
       outcome=write_data_in_transaction(coordinated,coordinated_tx,installation_identity=identity,authored_profile=profile,expected_generation=expected,expected_event_count=1,home_oids=tuple(home_oids),action=effect)
       if not isinstance(outcome,Ok):results.append(str(coordinated._custody.last_attempt.error))
      finally:coordinated.detach()
     else:
      result=stale.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=2 AND EXISTS(SELECT 1 FROM relational_fixture.assignment WHERE id=1 AND active)');results.append(result.rowcount)
     stale.commit()
    except BaseException as error:results.append(type(error).__name__);stale.rollback()
   worker=threading.Thread(target=conditional_write);worker.start();deadline=time.monotonic()+5;waiting=False
   try:
    while time.monotonic()<deadline:
     if self.admin.info.backend_pid in self.admin.execute('SELECT pg_catalog.pg_blocking_pids(%s)',(stale.info.backend_pid,)).fetchone()[0]:waiting=True;break
     time.sleep(.01)
    self.assertTrue(waiting);self.admin.commit()
   finally:self.admin.rollback();worker.join(11)
   self.assertFalse(worker.is_alive());return results
  self.assertEqual(race(False),[1])
  self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=1').fetchone(),(False,))
  self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=2').fetchone(),(False,))
  self.admin.execute('UPDATE relational_fixture.assignment SET active=true')
  # Test-only administrative prelock: no ordinary credential admission is implied.
  stale.close();stale=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(stale)
  self.assertEqual(race(True),[0])
  self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=2').fetchone(),(True,))
  from truss import Error
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  current=self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone()[0]
  self.admin.execute("CREATE TEMP TABLE data_writer_prior_work(value text);INSERT INTO data_writer_prior_work VALUES('kept')")
  effects=[]
  def coordinated(action,count=1,selected=profile):return write_data_in_transaction(self.host,tx,installation_identity=identity,authored_profile=selected,expected_generation=current,expected_event_count=count,home_oids=tuple(home_oids),action=action)
  for epoch_drift in ['ALTER TABLE truss.policy_generation_guard DROP COLUMN routine_source_generation','ALTER TABLE truss.policy_generation_guard ALTER COLUMN routine_source_generation TYPE integer']:
   self.admin.execute('SAVEPOINT source_epoch_fixture');self.admin.execute(epoch_drift)
   try:self.assertIsInstance(coordinated(lambda cursor:effects.append('unexpected')),Error);self.assertEqual(effects,[])
   finally:self.admin.execute('ROLLBACK TO SAVEPOINT source_epoch_fixture;RELEASE SAVEPOINT source_epoch_fixture')
   self.assertEqual(self.admin.execute('TABLE data_writer_prior_work').fetchall(),[('kept',)])
  def upsert(cursor):cursor.execute('INSERT INTO relational_fixture.assignment VALUES(4,true) ON CONFLICT(id) DO UPDATE SET active=excluded.active')
  for mutate,restore in [('ALTER TABLE relational_fixture.assignment DISABLE TRIGGER aa_security_data_gate','ALTER TABLE relational_fixture.assignment ENABLE ALWAYS TRIGGER aa_security_data_gate'),('ALTER FUNCTION truss.security_data_writer_guard() STABLE','ALTER FUNCTION truss.security_data_writer_guard() VOLATILE'),('GRANT EXECUTE ON FUNCTION truss.security_data_writer_guard() TO consumer','REVOKE EXECUTE ON FUNCTION truss.security_data_writer_guard() FROM consumer')]:
   self.admin.execute(mutate);self.assertIsInstance(coordinated(lambda cursor:effects.append('unexpected')),Error);self.assertEqual(effects,[]);self.admin.execute(restore)
  replace_source='CREATE OR REPLACE FUNCTION'+source.split('CREATE FUNCTION',1)[1]
  self.admin.execute(replace_source.replace('RETURN NULL;','RETURN NULL; -- fixture source drift'))
  self.assertIsInstance(coordinated(lambda cursor:effects.append('unexpected')),Error);self.assertEqual(effects,[]);self.admin.execute(replace_source)
  def rebind_after(selected):
   self.admin.execute('DROP TRIGGER zz_security_data_advance ON relational_fixture.assignment')
   self.admin.execute(psycopg.sql.SQL('CREATE TRIGGER zz_security_data_advance AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON relational_fixture.assignment FOR EACH STATEMENT EXECUTE FUNCTION truss.security_data_writer_guard({},{},{})').format(psycopg.sql.Literal(identity.hex()),psycopg.sql.Literal(selected.hex()),psycopg.sql.Literal(str(home_oids[2]))))
   self.admin.execute('ALTER TABLE relational_fixture.assignment ENABLE ALWAYS TRIGGER zz_security_data_advance')
  rebind_after(b'foreign-original-profile');self.assertIsInstance(coordinated(lambda cursor:effects.append('unexpected')),Error);self.assertEqual(effects,[]);rebind_after(profile)
  from psycopg.adapt import Loader
  from psycopg.pq import Format
  array_loads=[]
  class ForgedConfigArrayLoader(Loader):
   format=Format.TEXT
   def load(self,data):array_loads.append('used');return ['search_path=pg_catalog, pg_temp']
  original_loader=self.admin.adapters.get_loader(1009,Format.TEXT)
  self.admin.adapters.register_loader(1009,ForgedConfigArrayLoader)
  try:
   self.admin.execute('ALTER FUNCTION truss.security_data_writer_guard() SET search_path=hostile,pg_catalog')
   self.assertIsInstance(coordinated(lambda cursor:effects.append('unexpected')),Error);self.assertEqual(effects,[]);self.assertEqual(array_loads,[])
  finally:
   self.admin.adapters.register_loader(1009,original_loader);self.admin.execute('ALTER FUNCTION truss.security_data_writer_guard() SET search_path=pg_catalog,pg_temp')
  self.admin.execute(psycopg.sql.SQL('CREATE TRIGGER mm_security_extra BEFORE UPDATE ON relational_fixture.assignment FOR EACH STATEMENT EXECUTE FUNCTION truss.security_data_writer_guard({},{},{})').format(psycopg.sql.Literal('0'*131093),psycopg.sql.Literal(profile.hex()),psycopg.sql.Literal(str(home_oids[2]))))
  self.assertIsInstance(coordinated(lambda cursor:effects.append('unexpected')),Error);self.assertEqual(effects,[])
  self.admin.execute('DROP TRIGGER mm_security_extra ON relational_fixture.assignment')
  def late_metadata_drift(cursor):
   cursor.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=2');cursor.execute('ALTER FUNCTION truss.security_data_writer_guard() STABLE')
  self.assertIsInstance(coordinated(late_metadata_drift),Error)
  self.assertEqual(self.admin.execute("SELECT provolatile::text FROM pg_catalog.pg_proc WHERE oid='truss.security_data_writer_guard()'::regprocedure").fetchone(),('v',))
  self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=2').fetchone(),(True,))
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(current,))

  self.assertIsInstance(coordinated(lambda cursor:effects.append('unexpected'),selected=b'wrong-profile'),Error);self.assertEqual(effects,[])
  self.assertIsInstance(coordinated(upsert,count=True),Error)
  self.assertIsInstance(coordinated(lambda cursor:None),Error)
  self.assertIsInstance(coordinated(upsert,count=1),Error)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM relational_fixture.assignment WHERE id=4').fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(current,))
  def deferred(cursor):
   def later():yield 1
   return later()
  self.assertIsInstance(coordinated(deferred),Error)
  import inspect
  original_path=self.admin.execute('SHOW search_path').fetchone()
  def native_failure(cursor):
   cursor.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=2');cursor.execute('SELECT 1/0')
  failed=coordinated(native_failure);self.assertIsInstance(failed,Error);self.assertEqual(failed.error.sql_state,'22012')
  deferred_handles=[];cleanup=[]
  def started_deferred(cursor):
   def later():
    try:
     cursor.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=2');yield None
    finally:
     cursor.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=3');cleanup.append('closed');raise KeyboardInterrupt('fixture cleanup failure')
   handle=later();next(handle);deferred_handles.append(handle);return handle
  with self.assertRaisesRegex(KeyboardInterrupt,'fixture cleanup failure'):coordinated(started_deferred,count=2)
  self.assertEqual(self.host._custody.last_attempt.phase,'contained');self.assertIsNone(self.host._custody.last_attempt.cleanup_error)
  self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=3').fetchone(),(True,))
  self.assertEqual(cleanup,['closed']);self.assertEqual(inspect.getgeneratorstate(deferred_handles[0]),'GEN_CLOSED')
  async def later_coroutine():effects.append('unexpected coroutine body')
  def returned_coroutine(cursor):
   cursor.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=2');handle=later_coroutine();deferred_handles.append(handle);return handle
  self.assertIsInstance(coordinated(returned_coroutine),Error);self.assertEqual(inspect.getcoroutinestate(deferred_handles[1]),'CORO_CLOSED');self.assertEqual(effects,[])
  def declared_generator(cursor):
   effects.append('unexpected generator body');yield None
  async def declared_coroutine(cursor):effects.append('unexpected coroutine body')
  async def declared_async_generator(cursor):
   effects.append('unexpected async generator body');yield None
  prior_attempt=self.host._custody.last_attempt
  for callback in [declared_generator,declared_coroutine,declared_async_generator]:
   self.assertIsInstance(coordinated(callback),Error);self.assertIs(self.host._custody.last_attempt,prior_attempt)
  self.assertEqual(effects,[])
  self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=2').fetchone(),(True,))
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(current,))
  self.assertEqual(self.admin.execute('TABLE data_writer_prior_work').fetchall(),[('kept',)])
  self.assertEqual(self.admin.execute('SHOW search_path').fetchone(),original_path)
  self.admin.execute('INSERT INTO truss.policy_publication_claim VALUES(%s,%s,%s,%s,false)',(b'coordinated-unsettled',identity,profile,current))
  self.assertIsInstance(coordinated(lambda cursor:effects.append('unexpected')),Error);self.assertEqual(effects,[])
  self.admin.execute('UPDATE truss.policy_publication_claim SET settled=true WHERE operation_identity_bytes=%s',(b'coordinated-unsettled',))
  success=coordinated(upsert,count=2);self.assertIsInstance(success,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(success.value.generation,current+2);self.assertFalse(success.value.security_ready)
  self.assertEqual(self.admin.execute('TABLE data_writer_prior_work').fetchall(),[('kept',)])
  self.host.detach();self.admin.rollback()
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(current,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM relational_fixture.assignment WHERE id=4').fetchone(),(0,))
  # Native counterexample: endpoint checks alone do not hold routine DDL lifetime.
  import hashlib
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=2000') as ddl:
   aba=[]
   def routine_aba(cursor):
    try:
     ddl.execute(replace_source.replace('RETURN NULL;','RETURN NULL; -- concurrent ABA fixture'))
     body=ddl.execute("SELECT prosrc FROM pg_catalog.pg_proc WHERE oid='truss.security_data_writer_guard()'::regprocedure").fetchone()[0]
     changed=hashlib.sha256(body.encode()).hexdigest();self.assertNotEqual(changed,'8c3c1418af9cd20ee7c85cee8babdc74cc0e16f7391b1c91074994cc9e54c1c1');aba.append(changed)
     cursor.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=2')
    finally:ddl.execute(replace_source)
   observed=coordinated(routine_aba);self.assertIsInstance(observed,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(len(aba),1)
   self.assertEqual(observed.value.generation,current+1);self.assertFalse(observed.value.security_ready)
  self.host.detach();self.admin.rollback()
  self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=2').fetchone(),(True,))
  from truss._security_authority_change import change_authority_in_transaction
  coordinated_ddl=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(coordinated_ddl)
  ddl_outcomes=[];ddl_callbacks=[];ddl_worker=None
  def ddl_authority_change():
   ddl_host=None
   try:
    coordinated_ddl.execute('BEGIN');ddl_host=adopt_psycopg_host(coordinated_ddl,statement_timeout_ms=10000,operation_timeout_ms=30000);ddl_tx=ddl_host.adopt_transaction().value
    def change_source(cursor):
     ddl_callbacks.append('entered');cursor.execute(replace_source.replace('RETURN NULL;','RETURN NULL; -- coordinated source change'));cursor.execute(replace_source)
    changed=change_authority_in_transaction(ddl_host,ddl_tx,installation_identity=identity,authored_profile=profile,expected_generation=current+1,action=change_source)
    if isinstance(changed,Ok):ddl_outcomes.append((changed.value.generation,changed.value.security_ready));ddl_host.detach();ddl_host=None;coordinated_ddl.commit()
    else:ddl_outcomes.append(str(ddl_host._custody.last_attempt.error))
   except BaseException as error:ddl_outcomes.append(type(error).__name__)
   finally:
    if ddl_host is not None:ddl_host.detach()
    coordinated_ddl.rollback()
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  def guarded_data(cursor):
   nonlocal ddl_worker
   ddl_worker=threading.Thread(target=ddl_authority_change);ddl_worker.start();deadline=time.monotonic()+5;blocked=False
   while time.monotonic()<deadline:
    cursor.execute('SELECT pg_catalog.pg_blocking_pids(%s)',(coordinated_ddl.info.backend_pid,))
    if self.admin.info.backend_pid in cursor.fetchone()[0]:blocked=True;break
    time.sleep(.01)
   self.assertTrue(blocked);self.assertEqual(ddl_outcomes,[]);self.assertEqual(ddl_callbacks,[]);self.assertTrue(ddl_worker.is_alive())
   cursor.execute('UPDATE relational_fixture.assignment SET active=false WHERE id=2')
  try:
   guarded=coordinated(guarded_data);self.assertIsInstance(guarded,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(guarded.value.generation,current+1)
   self.host.detach();self.admin.commit()
  finally:
   self.admin.rollback()
   if ddl_worker is not None:ddl_worker.join(11)
  self.assertFalse(ddl_worker.is_alive());self.assertEqual(ddl_outcomes,[(current+2,False)]);self.assertEqual(ddl_callbacks,['entered'])
  # Same-transaction guard reacquisition does not establish inactive-only DDL.
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  reentrant_sources=[]
  def reentrant_source_change(cursor):
   cursor.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE')
   self.assertEqual(cursor.fetchone(),(current,))
   cursor.execute(replace_source.replace('RETURN NULL;','RETURN NULL; -- reentrant ABA fixture'))
   cursor.execute("SELECT prosrc FROM pg_catalog.pg_proc WHERE oid='truss.security_data_writer_guard()'::regprocedure")
   changed=hashlib.sha256(cursor.fetchone()[0].encode()).hexdigest();self.assertNotEqual(changed,'8c3c1418af9cd20ee7c85cee8babdc74cc0e16f7391b1c91074994cc9e54c1c1');reentrant_sources.append(changed)
   cursor.execute('UPDATE relational_fixture.assignment SET active=true WHERE id=2')
   cursor.execute(replace_source)
  current+=2
  reentrant=coordinated(reentrant_source_change);self.assertIsInstance(reentrant,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(reentrant.value.generation,current+1);self.assertEqual(len(reentrant_sources),1);self.assertFalse(reentrant.value.security_ready)
  self.host.detach();self.admin.rollback()
  self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=2').fetchone(),(False,))
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(current,))
  from truss._security_data_writer import write_data_with_routine_hooks_in_transaction
  hook_owner_oid=self.admin.execute('SELECT oid FROM pg_catalog.pg_roles WHERE rolname=current_user').fetchone()[0]
  strict_effects=[]
  def strict_coordinated(action,count=1,owner=hook_owner_oid):return write_data_with_routine_hooks_in_transaction(self.host,tx,installation_identity=identity,authored_profile=profile,expected_generation=current,expected_event_count=count,home_oids=tuple(home_oids),hook_owner_oid=owner,action=action)
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  self.assertIsInstance(strict_coordinated(lambda cursor:strict_effects.append('unexpected')),Error);self.assertEqual(strict_effects,[])
  self.host.detach();self.admin.rollback()
  # Native selected routine DDL participation; hooks installed by fixture superuser.
  ddl_source=(Path(__file__).resolve().parents[3]/'packages/postgresql/native/security-routine-ddl-guard-pg18.sql').read_text()
  function_source,hook_source=ddl_source.split('CREATE EVENT TRIGGER',1)
  self.admin.execute(psycopg.sql.SQL('SET ROLE {}').format(psycopg.sql.Identifier(self.installation.owner_role)))
  try:self.admin.execute(function_source)
  finally:self.admin.execute('RESET ROLE')
  self.admin.execute('CREATE ROLE hook_binding_other SUPERUSER NOLOGIN');self.addCleanup(self.admin.execute,'DROP ROLE IF EXISTS hook_binding_other')
  other_superuser_oid=self.admin.execute("SELECT oid FROM pg_catalog.pg_roles WHERE rolname='hook_binding_other'").fetchone()[0]
  self.admin.execute("CREATE FUNCTION truss.hook_binding_noop() RETURNS event_trigger LANGUAGE plpgsql AS $$ BEGIN RETURN; END $$")
  self.admin.execute('CREATE EVENT TRIGGER'+hook_source)
  try:
   self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
   for hook_mutation in ['ALTER EVENT TRIGGER truss_security_routine_ddl_start DISABLE','ALTER EVENT TRIGGER truss_security_routine_ddl_end ENABLE','DROP EVENT TRIGGER truss_security_routine_ddl_end','SET LOCAL event_triggers=off','ALTER EVENT TRIGGER truss_security_routine_ddl_start OWNER TO hook_binding_other',"DROP EVENT TRIGGER truss_security_routine_ddl_end;CREATE EVENT TRIGGER truss_security_routine_ddl_end ON ddl_command_end WHEN TAG IN ('CREATE FUNCTION','ALTER FUNCTION') EXECUTE FUNCTION truss.security_routine_ddl_guard();ALTER EVENT TRIGGER truss_security_routine_ddl_end ENABLE ALWAYS","DROP EVENT TRIGGER truss_security_routine_ddl_end;CREATE EVENT TRIGGER truss_security_routine_ddl_end ON ddl_command_end WHEN TAG IN ('CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION') EXECUTE FUNCTION truss.hook_binding_noop();ALTER EVENT TRIGGER truss_security_routine_ddl_end ENABLE ALWAYS","CREATE EVENT TRIGGER extra_source_guard ON ddl_command_start WHEN TAG IN ('CREATE FUNCTION') EXECUTE FUNCTION truss.security_routine_ddl_guard()"]:
    self.admin.execute('SAVEPOINT hook_metadata_fixture');self.admin.execute(hook_mutation)
    try:self.assertIsInstance(strict_coordinated(lambda cursor:strict_effects.append('unexpected')),Error);self.assertEqual(strict_effects,[])
    finally:self.admin.execute('ROLLBACK TO SAVEPOINT hook_metadata_fixture;RELEASE SAVEPOINT hook_metadata_fixture')
   for wrong_owner in [True,0,4294967296,other_superuser_oid,self.admin.execute("SELECT oid FROM pg_catalog.pg_roles WHERE rolname='consumer'").fetchone()[0]]:
    self.assertIsInstance(strict_coordinated(lambda cursor:strict_effects.append('unexpected'),owner=wrong_owner),Error);self.assertEqual(strict_effects,[])
   def late_hook_drift(cursor):
    cursor.execute('UPDATE relational_fixture.assignment SET active=true WHERE id=2')
    cursor.execute('ALTER EVENT TRIGGER truss_security_routine_ddl_start DISABLE')
   self.assertIsInstance(strict_coordinated(late_hook_drift),Error)
   late_guc_events=[]
   def late_event_guc_drift(cursor):
    late_guc_events.append('entered');cursor.execute('UPDATE relational_fixture.assignment SET active=true WHERE id=2');cursor.execute('SET LOCAL event_triggers=off');late_guc_events.append('off')
   self.assertIsInstance(strict_coordinated(late_event_guc_drift),Error)
   self.assertEqual(late_guc_events,['entered','off']);self.assertIn('active native event triggers',str(self.host._custody.last_attempt.error))
   self.assertEqual(self.admin.execute('SHOW event_triggers').fetchone(),('on',))
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current,0))
   self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=2').fetchone(),(False,))
   self.assertEqual(self.admin.execute("SELECT evtenabled FROM pg_catalog.pg_event_trigger WHERE evtname='truss_security_routine_ddl_start'").fetchone(),('A',))
   self.host.detach();self.admin.rollback()
   # All selected tags participate once; rolled-back DDL restores generation.
   self.admin.execute('CREATE FUNCTION relational_fixture.ddl_probe() RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$')
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current+1,1))
   self.admin.execute('ALTER FUNCTION relational_fixture.ddl_probe() IMMUTABLE')
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current+2,2))
   self.admin.execute('DROP FUNCTION relational_fixture.ddl_probe()');current+=3
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current,3))
   for ceiling_column in ['generation','routine_source_generation']:
    self.admin.execute('BEGIN');self.admin.execute(psycopg.sql.SQL('UPDATE truss.policy_generation_guard SET {}=9223372036854775807').format(psycopg.sql.Identifier(ceiling_column)))
    try:
     with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.admin.execute('ALTER FUNCTION truss.security_data_writer_guard() STRICT')
    finally:self.admin.rollback()
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current,3))
   self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
   ddl_seen=[]
   def tracked_aba(cursor):
    cursor.execute(replace_source.replace('RETURN NULL;','RETURN NULL; -- native tracked ABA'))
    cursor.execute('SELECT generation FROM truss.policy_generation_guard');ddl_seen.append(cursor.fetchone()[0])
    cursor.execute('UPDATE relational_fixture.assignment SET active=true WHERE id=2')
    cursor.execute(replace_source)
    cursor.execute('SELECT generation FROM truss.policy_generation_guard');ddl_seen.append(cursor.fetchone()[0])
   self.assertIsInstance(strict_coordinated(tracked_aba),Error);self.assertEqual(ddl_seen,[current+1,current+3])
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current,3))
   self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=2').fetchone(),(False,))
   # A deliberately wrong data-event declaration can absorb DDL advances.
   # The separate source epoch rejects it despite a matching total delta.
   wrong_inventory=strict_coordinated(tracked_aba,count=3);self.assertIsInstance(wrong_inventory,Error)
   self.assertIn('routine source epoch changed',str(self.host._custody.last_attempt.error))
   self.assertEqual(ddl_seen,[current+1,current+3,current+1,current+3])
   self.host.detach();self.admin.rollback()
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current,3))
   self.assertEqual(self.admin.execute('SELECT active FROM relational_fixture.assignment WHERE id=2').fetchone(),(False,))
   self.admin.execute('INSERT INTO truss.policy_publication_claim VALUES(%s,%s,%s,%s,false)',(b'routine-ddl-pending',identity,profile,current))
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.admin.execute(replace_source.replace('RETURN NULL;','RETURN NULL; -- blocked routine DDL'))
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current,3))
   self.admin.execute('UPDATE truss.policy_publication_claim SET settled=true WHERE operation_identity_bytes=%s',(b'routine-ddl-pending',))
   native_ddl=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(native_ddl)
   native_outcomes=[];native_worker=None
   def competing_routine_ddl():
    try:
     native_ddl.execute(replace_source.replace('RETURN NULL;','RETURN NULL; -- native serialized routine'))
     native_ddl.execute(replace_source);native_outcomes.append('changed-and-restored')
    except BaseException as error:native_outcomes.append(type(error).__name__)
   self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
   def native_guarded_data(cursor):
    nonlocal native_worker
    native_worker=threading.Thread(target=competing_routine_ddl);native_worker.start();deadline=time.monotonic()+5;blocked=False
    while time.monotonic()<deadline:
     cursor.execute('SELECT pg_catalog.pg_blocking_pids(%s)',(native_ddl.info.backend_pid,))
     if self.admin.info.backend_pid in cursor.fetchone()[0]:blocked=True;break
     time.sleep(.01)
    self.assertTrue(blocked);self.assertEqual(native_outcomes,[]);self.assertTrue(native_worker.is_alive())
    cursor.execute('UPDATE relational_fixture.assignment SET active=true WHERE id=2')
   try:
    serialized=strict_coordinated(native_guarded_data);self.assertIsInstance(serialized,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(serialized.value.generation,current+1)
    self.assertEqual(self.admin.execute('SELECT routine_source_generation FROM truss.policy_generation_guard').fetchone(),(3,))
    self.host.detach();self.admin.commit()
   finally:
    self.admin.rollback()
    if native_worker is not None:native_worker.join(11)
   self.assertFalse(native_worker.is_alive());self.assertEqual(native_outcomes,['changed-and-restored']);current+=3
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current,5))
   # Fresh claim check after a native wait, not merely an immediate claim check.
   waited_outcomes=[];waited_worker=None
   def waited_routine_ddl():
    try:native_ddl.execute(replace_source.replace('RETURN NULL;','RETURN NULL; -- post-wait refusal'));waited_outcomes.append('unexpected-success')
    except psycopg.Error as error:waited_outcomes.append(error.sqlstate)
    except BaseException as error:waited_outcomes.append(type(error).__name__)
   self.admin.execute('BEGIN');self.admin.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR SHARE')
   try:
    waited_worker=threading.Thread(target=waited_routine_ddl);waited_worker.start();deadline=time.monotonic()+5;blocked=False
    while time.monotonic()<deadline:
     if self.admin.info.backend_pid in self.admin.execute('SELECT pg_catalog.pg_blocking_pids(%s)',(native_ddl.info.backend_pid,)).fetchone()[0]:blocked=True;break
     time.sleep(.01)
    self.assertTrue(blocked);self.assertEqual(waited_outcomes,[])
    self.admin.execute('INSERT INTO truss.policy_publication_claim VALUES(%s,%s,%s,%s,false)',(b'routine-ddl-wait',identity,profile,current));self.admin.commit()
   finally:
    self.admin.rollback()
    if waited_worker is not None:waited_worker.join(11)
   self.assertFalse(waited_worker.is_alive());self.assertEqual(waited_outcomes,['42501'])
   self.assertEqual(self.admin.execute('SELECT generation,routine_source_generation FROM truss.policy_generation_guard').fetchone(),(current,5))
   self.admin.execute('UPDATE truss.policy_publication_claim SET settled=true WHERE operation_identity_bytes=%s',(b'routine-ddl-wait',))
   body=self.admin.execute("SELECT prosrc FROM pg_catalog.pg_proc WHERE oid='truss.security_data_writer_guard()'::regprocedure").fetchone()[0]
   self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),'8c3c1418af9cd20ee7c85cee8babdc74cc0e16f7391b1c91074994cc9e54c1c1')
  finally:
   self.admin.rollback()
   self.admin.execute('DROP EVENT TRIGGER IF EXISTS truss_security_routine_ddl_start;DROP EVENT TRIGGER IF EXISTS truss_security_routine_ddl_end')
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as ordinary:
   ordinary.execute('BEGIN');ordinary_host=adopt_psycopg_host(ordinary,statement_timeout_ms=10000,operation_timeout_ms=30000);ordinary_adoption=ordinary_host.adopt_transaction();self.assertIsInstance(ordinary_adoption,Ok);ordinary_tx=ordinary_adoption.value
   refused=write_data_in_transaction(ordinary_host,ordinary_tx,installation_identity=identity,authored_profile=profile,expected_generation=current,expected_event_count=1,home_oids=tuple(home_oids),action=lambda cursor:effects.append('unexpected'))
   self.assertIsInstance(refused,Error);self.assertEqual(effects,[]);ordinary_host.detach();ordinary.rollback()
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.data-writer.json').write_text(json.dumps({'observations':['ordinary raw writer guard and data effects commit atomically','outer rollback preserves data and generation','all four DML/TRUNCATE families refuse outstanding claim before effects','settled tombstone permits subsequent update','ordinary trigger disabling/replica bypass denied','graph object and zero-row edge events advance conservatively','graph rollback preserves generation','original native guard wait drains pending registrant; fresh post-wait claim check refuses','repeatable-read writer scope refuses before effects','UPSERT advances two events and MERGE three including zero-row events','late intervening claim rolls back data and claim','composite overflow refuses and rolls back all events','counterexample: trigger guard wait retains stale outer DML predicate','actual private coordinated writer acquires original guard before DML, observes committed revocation and affects zero rows','wrong profile and pending claim refuse callback','no generation or wrong composite event count rolls back effects, preserves prior caller work','deferred returned callback refuses','exact two-event UPSERT returns pending commit; outer rollback preserves original data/generation','ordinary consumer coordinator access refuses before callback','native post-effect division failure rolls back data/generation','started generator cleanup writes and KeyboardInterrupt are contained, generator closed','returned coroutine is closed without executing body; prior DML rolls back','declared generator/coroutine/async-generator callbacks refuse before invocation','failure preserves prior caller work and search path','original selected function/body/ACL/always-trigger metadata checked before callback','disabled trigger, routine attribute/body, extra execute grant and wrong trigger profile refuse before callback','post-effect metadata drift refuses and rolls back data/generation/DDL','forged array loader cannot hide actual function configuration drift; no array loads','oversized extra trigger stays in cardinality check and refuses before callback','counterexample: competing uncoordinated routine DDL changes and restores source during guarded callback; endpoint checks accept pending operation','actual authority-change routine DDL waits on original writer PID until commit, then advances generation','counterexample: same transaction reacquires guard and changes/restores routine source during active callback; endpoint checks accept pending operation','native selected CREATE/ALTER/DROP FUNCTION hooks each advance general and source epochs once; either ceiling refuses before DDL','missing or mistyped source epoch refuses actual writer before callback and preserves prior caller work','native selected DDL change/restore advances two generations; actual data writer refuses unexpected delta and rolls back DML/source/generation','separate routine source epoch refuses wrong data-event declaration that absorbs DDL advances; data/source/generation roll back','native unsettled claim refuses selected source DDL before effects','native competing routine DDL waits on original writer PID until commit, then change/restore advances twice','native selected DDL observed waiting on original guard SHARE holder refuses freshly committed unsettled claim with42501 and unchanged source/generation','explicit hook-bound writer requires original owner/function/body and two exact always-on hooks before and after callback','missing/disabled/origin-only/dropped/extra hooks and invalid/unprivileged hook owner refuse before callback','late hook disabling after DML rolls back effects/epochs and restores always-on hook metadata','event_triggers off refuses before callback; measured late-off callback enters and refuses after effects with exact active-setting cause and rollback','incomplete tags, wrong routine binding and alternate superuser owner refuse before callback'],'scope':'Native physical statement coordination only, original installer-bound bytes/OIDs and trusted native function/trigger ownership. No logical write permissions, all key/catalog/role/source writer closure, fresh protected query/old-new snapshot, final sink or backend admission.'},indent=2)+'\n')
 def test_private_publication_registration_identity_capacity_and_rollback(self):
  from truss import Error,adopt_psycopg_host
  from truss._security_home_installation import bootstrap_security_homes_in_transaction
  from truss._security_publication_registration import register_publication_in_transaction
  self.install();self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  identity=self.installation.installation_id.encode();profile=b'publication-registration-fixture/0.1'
  self.assertIsInstance(bootstrap_security_homes_in_transaction(self.host,tx,installation_identity=identity,authored_profile=profile,max_retained=2),Ok)
  self.admin.execute("CREATE TEMP TABLE registration_prior_work(value text);INSERT INTO registration_prior_work VALUES('kept')")
  def register(token,selected=profile):return register_publication_in_transaction(self.host,tx,operation_identity=token,installation_identity=identity,authored_profile=selected,expected_generation=1)
  self.assertIsInstance(register(b'foreign',b'wrong-profile'),Error)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(0,))
  original=register(b'original-one');self.assertIsInstance(original,Ok,str(self.host._custody.last_attempt.error));self.assertFalse(original.value.publication_allowed)
  duplicate=register(b'original-one');self.assertIsInstance(duplicate,Error);self.assertEqual(duplicate.error.sql_state,'23505')
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(1,))
  self.assertIsInstance(register(b'original-two'),Ok)
  self.admin.execute('UPDATE truss.policy_publication_claim SET settled=true')
  self.assertIsInstance(register(b'original-overflow'),Error)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(2,))
  self.assertEqual(self.admin.execute('TABLE registration_prior_work').fetchall(),[('kept',)])
  self.host.detach();self.admin.rollback()
  self.assertIsNone(self.admin.execute("SELECT pg_catalog.to_regclass('truss.policy_publication_claim')").fetchone()[0])
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.registration.json').write_text(json.dumps({'observations':['wrong original profile refuses without insertion','original registration returns pending commit and no release grant','duplicate original identity23505 retains first claim','second original identity takes last slot','settled tombstones retain capacity and exhaustion refuses','caller prior work survives refusals','outer rollback removes staged homes and claims'],'scope':'Private trusted-administrator registration only; no authentic operation issuer, original sink/recovery or admitted policy.'},indent=2)+'\n')
 def test_private_authority_change_claim_gate_and_atomic_effects(self):
  from truss import Error,adopt_psycopg_host
  from truss._security_home_installation import bootstrap_security_homes_in_transaction
  from truss._security_authority_change import change_authority_in_transaction
  self.install();self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  identity=self.installation.installation_id.encode();profile=b'authority-change-fixture/0.1'
  self.assertIsInstance(bootstrap_security_homes_in_transaction(self.host,tx,installation_identity=identity,authored_profile=profile,max_retained=6),Ok)
  self.admin.execute("CREATE TEMP TABLE authority_action_work(value text);INSERT INTO authority_action_work VALUES('kept')")
  self.admin.execute('INSERT INTO truss.policy_publication_claim VALUES(%s,%s,%s,1,false)',(b'original-operation',identity,profile))
  calls=[]
  def effect(cursor):calls.append('effect');cursor.execute("INSERT INTO authority_action_work VALUES('changed')")
  def change(action=effect):return change_authority_in_transaction(self.host,tx,installation_identity=identity,authored_profile=profile,expected_generation=1,action=action)
  self.assertIsInstance(change(),Error);self.assertEqual(calls,[])
  self.admin.execute('UPDATE truss.policy_publication_claim SET settled=true')
  def failed(cursor):effect(cursor);raise RuntimeError('failed physical action')
  self.assertIsInstance(change(failed),Error)
  self.assertEqual(self.admin.execute('TABLE authority_action_work').fetchall(),[('kept',)])
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(1,))
  def late_claim(cursor):effect(cursor);cursor.execute('INSERT INTO truss.policy_publication_claim VALUES(%s,%s,%s,1,false)',(b'late-original',identity,profile))
  self.assertIsInstance(change(late_claim),Error)
  self.assertEqual(self.admin.execute('TABLE authority_action_work').fetchall(),[('kept',)])
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(1,))
  changed=change();self.assertIsInstance(changed,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(changed.value.generation,2);self.assertFalse(changed.value.security_ready)
  self.assertEqual(self.admin.execute('TABLE authority_action_work').fetchall(),[('kept',),('changed',)])
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(2,))
  before=list(calls);self.assertIsInstance(change(),Error);self.assertEqual(calls,before)
  self.host.detach();self.admin.rollback()
  self.assertIsNone(self.admin.execute("SELECT pg_catalog.to_regclass('truss.policy_generation_guard')").fetchone()[0])
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.authority.json').write_text(json.dumps({'observations':['unsettled original claim blocks before physical callback','settled tombstone permits advancement','physical action error rolls back effects and generation','late unsettled claim rolls back callback effects and inserted claim','complete action and exact native generation2 stage together','stale original generation refuses before callback','outer caller rollback removes staged installation homes'],'scope':'Private native authority effect coordination under trusted administrator. Physical temp-table effect only; no logical action permission, original policy issuer, complete participant closure or security-ready profile.'},indent=2)+'\n')
 def test_private_authority_change_refuses_deferred_and_ordinary_actor(self):
  from truss import Error,adopt_psycopg_host
  from truss._security_home_installation import bootstrap_security_homes_in_transaction
  from truss._security_authority_change import change_authority_in_transaction
  self.install();self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  identity=self.installation.installation_id.encode();profile=b'authority-deferred-fixture/0.1'
  self.assertIsInstance(bootstrap_security_homes_in_transaction(self.host,tx,installation_identity=identity,authored_profile=profile,max_retained=6),Ok)
  self.admin.execute("CREATE TEMP TABLE authority_deferred_work(value text);INSERT INTO authority_deferred_work VALUES('kept')")
  bodies=[];deferred=[]
  async def declared_async(cursor):bodies.append('must not execute')
  def declared_generator(cursor):
   bodies.append('must not execute');yield None
  for action in [declared_async,declared_generator]:
   refused=change_authority_in_transaction(self.host,tx,installation_identity=identity,authored_profile=profile,expected_generation=1,action=action)
   self.assertIsInstance(refused,Error)
  for kind in ['generator','coroutine']:
   def action(cursor):
    cursor.execute("INSERT INTO authority_deferred_work VALUES('staged')")
    def cold():bodies.append('must not execute');yield None
    async def cold_async():bodies.append('must not execute')
    value=cold() if kind=='generator' else cold_async();deferred.append(value);return value
   refused=change_authority_in_transaction(self.host,tx,installation_identity=identity,authored_profile=profile,expected_generation=1,action=action)
   self.assertIsInstance(refused,Error)
   self.assertEqual(self.admin.execute('TABLE authority_deferred_work').fetchall(),[('kept',)])
   self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(1,))
  self.assertEqual(bodies,[]);self.assertIsNone(deferred[0].gi_frame);self.assertIsNone(deferred[1].cr_frame)
  self.host.detach();self.admin.commit()
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer';calls=[]
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as ordinary:
   ordinary.execute('BEGIN');ordinary_host=adopt_psycopg_host(ordinary,statement_timeout_ms=10000,operation_timeout_ms=10000)
   try:
    ordinary_adoption=ordinary_host.adopt_transaction();self.assertIsInstance(ordinary_adoption,Ok);ordinary_tx=ordinary_adoption.value
    ordinary.execute("CREATE TEMP TABLE authority_ordinary_work(value text);INSERT INTO authority_ordinary_work VALUES('kept')")
    denied=change_authority_in_transaction(ordinary_host,ordinary_tx,installation_identity=identity,authored_profile=profile,expected_generation=1,action=lambda cursor:calls.append('must not execute'))
    self.assertIsInstance(denied,Error);self.assertEqual(denied.error.sql_state,'42501');self.assertEqual(calls,[])
    self.assertEqual(ordinary.execute('TABLE authority_ordinary_work').fetchall(),[('kept',)])
   finally:ordinary_host.detach();ordinary.rollback()
  self.assertEqual(self.admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(1,))
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.authority-boundary.json').write_text(json.dumps({'observations':['declared async/generator actions refuse without body execution','returned cold generator/coroutine actions close and roll back staged physical effects','original generation1 and caller work retained','actual ordinary native consumer receives42501 before callback','ordinary caller transaction work survives refusal'],'scope':'Private native administrative/deferred boundary only; no logical action permission, authenticated issuer/source or full backend security admission.'},indent=2)+'\n')
 def test_supported_source_census_observes_bootstrap_and_body_drift(self):
  from truss import Error,adopt_psycopg_host
  from truss._security_home_installation import bootstrap_security_homes_in_transaction
  from truss._psycopg_source_census import observe_source_census_in_transaction
  import gzip,hashlib
  self.install();self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);tx=self.host.adopt_transaction().value
  self.admin.execute("CREATE TEMP TABLE source_census_work(value text);INSERT INTO source_census_work VALUES('kept')")
  self.assertIsInstance(bootstrap_security_homes_in_transaction(self.host,tx,installation_identity=self.installation.installation_id.encode(),authored_profile=b'source-census-fixture/0.1',max_retained=6),Ok)
  self.admin.execute("CREATE FUNCTION truss.census_fixture_probe() RETURNS int LANGUAGE sql AS 'SELECT 1'")
  self.admin.execute("CREATE FUNCTION truss.census_fixture_event() RETURNS event_trigger LANGUAGE plpgsql AS $$ BEGIN RETURN; END $$;CREATE EVENT TRIGGER census_fixture_event ON ddl_command_start WHEN TAG IN ('CREATE FUNCTION','ALTER FUNCTION') EXECUTE FUNCTION truss.census_fixture_event()")
  def capture():
   result=observe_source_census_in_transaction(self.host,tx)
   self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertFalse(result.value.admitted)
   return result.value.original_image
  self.admin.execute("CREATE SCHEMA census_hostile;CREATE FUNCTION census_hostile.multiply(int,int) RETURNS int LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'hostile operator invoked';END $$;CREATE OPERATOR census_hostile.* (FUNCTION=census_hostile.multiply,LEFTARG=int,RIGHTARG=int)")
  self.addCleanup(self.admin.execute,'DROP SCHEMA IF EXISTS census_hostile CASCADE')
  self.admin.execute('SET LOCAL search_path=census_hostile,pg_catalog,pg_temp')
  original_path=self.admin.execute("SELECT pg_catalog.current_setting('search_path')").fetchone()[0]
  self.admin.execute('SAVEPOINT hostile_operator_probe')
  with self.assertRaises(psycopg.errors.RaiseException):self.admin.execute('SELECT 2*3')
  self.admin.execute('ROLLBACK TO hostile_operator_probe')
  original=capture();parsed=json.loads(original)
  self.assertEqual(self.admin.execute("SELECT pg_catalog.current_setting('search_path')").fetchone()[0],original_path)
  self.assertEqual(parsed['serverVersion'],'180006')
  names={json.loads(row)['relname'] for row in parsed['sections']['pg_class']}
  self.assertTrue({'policy_generation_guard','policy_publication_claim','policy_publication_capacity'}<=names)
  def bodies(image):return [json.loads(row)['prosrc'] for row in json.loads(image)['sections']['pg_proc'] if json.loads(row)['proname']=='census_fixture_probe']
  self.assertEqual(bodies(original),['SELECT 1'])
  self.admin.execute('SAVEPOINT event_hook_mutation');self.admin.execute('ALTER EVENT TRIGGER census_fixture_event DISABLE')
  disabled_hook=capture();self.assertNotEqual(disabled_hook,original)
  def hook(image):return [json.loads(row) for row in json.loads(image)['sections']['pg_event_trigger'] if json.loads(row)['evtname']=='census_fixture_event']
  self.assertEqual(len(hook(original)),1);self.assertEqual(hook(original)[0]['evtenabled'],'O');self.assertEqual(hook(disabled_hook)[0]['evtenabled'],'D')
  expected=json.loads(self.admin.execute("SELECT pg_catalog.to_jsonb(r)::text FROM pg_catalog.pg_event_trigger r WHERE evtname='census_fixture_event'").fetchone()[0])
  self.assertEqual(hook(disabled_hook),[expected]);self.assertEqual(set(expected['evttags']),{'CREATE FUNCTION','ALTER FUNCTION'})
  for name,rows in json.loads(original)['sections'].items():
   if name!='pg_event_trigger':self.assertEqual(json.loads(disabled_hook)['sections'][name],rows)
  self.admin.execute('ROLLBACK TO event_hook_mutation');self.assertEqual(capture(),original)
  self.admin.execute('SAVEPOINT source_mutation');self.admin.execute("CREATE OR REPLACE FUNCTION truss.census_fixture_probe() RETURNS int LANGUAGE sql AS 'SELECT 2'")
  changed=capture();self.assertNotEqual(changed,original);self.assertEqual(bodies(changed),['SELECT 2'])
  self.admin.execute('ROLLBACK TO source_mutation');restored=capture();self.assertEqual(restored,original)
  self.admin.execute('CREATE FOREIGN DATA WRAPPER source_census_fixture')
  refused=observe_source_census_in_transaction(self.host,tx);self.assertIsInstance(refused,Error)
  self.assertEqual(self.admin.execute('TABLE source_census_work').fetchall(),[('kept',)])
  self.admin.execute('ROLLBACK TO source_mutation');self.assertEqual(capture(),original)
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):
   target=Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.census.json')
   target.write_text(json.dumps({'originalBytes':len(original),'originalSha256':hashlib.sha256(original).hexdigest(),'changedSha256':hashlib.sha256(changed).hexdigest(),'restoredSha256':hashlib.sha256(restored).hexdigest(),'guardHomesObserved':True,'hostileOperatorNotInvoked':True,'callerSearchPathRestored':True,'originalBody':'SELECT 1','changedBody':'SELECT 2','foreignWrapperRefused':True,'eventHookEnabledDriftObserved':True,'eventHookOtherSectionsUnchanged':True,'eventHookExactNativeMetadata':True,'callerWork':'kept','scope':'Actual PostgreSQL18.6 source response via stock supported psycopg, private host scope. Not authenticated producer/source writer, held authority/data cut or admitted policy.'},indent=2)+'\n')
   Path(str(target)+'.original.gz').write_bytes(gzip.compress(original,mtime=0));Path(str(target)+'.changed.gz').write_bytes(gzip.compress(changed,mtime=0))
 def test_private_bootstrap_refuses_suppressed_native_seed(self):
  from truss import Error,adopt_psycopg_host
  from truss._security_home_installation import bootstrap_security_homes_in_transaction
  self.install()
  self.admin.execute("CREATE SCHEMA bootstrap_fault_fixture;CREATE FUNCTION bootstrap_fault_fixture.skip_seed() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL;END $$")
  self.admin.execute("CREATE FUNCTION bootstrap_fault_fixture.attach_fault() RETURNS event_trigger LANGUAGE plpgsql AS $$ DECLARE command record;BEGIN FOR command IN SELECT * FROM pg_catalog.pg_event_trigger_ddl_commands() LOOP IF command.object_identity='truss.policy_generation_guard' THEN EXECUTE 'CREATE TRIGGER skip_seed BEFORE INSERT ON truss.policy_generation_guard FOR EACH ROW EXECUTE FUNCTION bootstrap_fault_fixture.skip_seed()';END IF;END LOOP;END $$")
  self.admin.execute("CREATE EVENT TRIGGER bootstrap_seed_fault ON ddl_command_end WHEN TAG IN ('CREATE TABLE') EXECUTE FUNCTION bootstrap_fault_fixture.attach_fault()")
  self.addCleanup(self.admin.execute,'DROP SCHEMA bootstrap_fault_fixture CASCADE')
  self.addCleanup(self.admin.execute,'DROP EVENT TRIGGER bootstrap_seed_fault')
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);tx=self.host.adopt_transaction().value
  self.admin.execute("CREATE TEMP TABLE bootstrap_fault_work(value text);INSERT INTO bootstrap_fault_work VALUES('kept')")
  result=bootstrap_security_homes_in_transaction(self.host,tx,installation_identity=self.installation.installation_id.encode(),authored_profile=b'suppressed-seed-fixture/0.1',max_retained=6)
  self.assertIsInstance(result,Error)
  for home in ['policy_generation_guard','policy_publication_claim','policy_publication_capacity']:
   self.assertIsNone(self.admin.execute('SELECT pg_catalog.to_regclass(%s)',('truss.'+home,)).fetchone()[0])
  self.assertEqual(self.admin.execute('TABLE bootstrap_fault_work').fetchall(),[('kept',)])
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.seed.json').write_text(json.dumps({'observations':['actual native event hook attaches BEFORE INSERT suppression','bootstrap refuses without pending success','all three homes roll back','original caller work preserved'],'scope':'Native suppressed-seed containment; excluded administrator injects fixture fault. Not full event-hook census or security profile admission.'},indent=2)+'\n')
 def test_private_security_home_operation_preserves_transaction_and_refuses_repair(self):
  from truss import Error,adopt_psycopg_host
  from truss._security_home_installation import bootstrap_security_homes_in_transaction
  self.install()
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);tx=self.host.adopt_transaction().value
  identity=self.installation.installation_id.encode();profile=b'private-bootstrap-native/0.1'
  self.admin.execute("CREATE TEMP TABLE bootstrap_caller_work(value text);INSERT INTO bootstrap_caller_work VALUES('kept')")
  def bootstrap(original=identity):return bootstrap_security_homes_in_transaction(self.host,tx,installation_identity=original,authored_profile=profile,max_retained=6)
  self.assertIsInstance(bootstrap(b'foreign'),Error)
  self.assertIsNone(self.admin.execute("SELECT pg_catalog.to_regclass('truss.policy_generation_guard')").fetchone()[0])
  self.admin.execute('ALTER DEFAULT PRIVILEGES GRANT SELECT ON TABLES TO consumer')
  self.assertIsInstance(bootstrap(),Error)
  self.assertIsNone(self.admin.execute("SELECT pg_catalog.to_regclass('truss.policy_generation_guard')").fetchone()[0])
  self.assertEqual(self.admin.execute('TABLE bootstrap_caller_work').fetchall(),[('kept',)])
  self.admin.execute('ALTER DEFAULT PRIVILEGES REVOKE SELECT ON TABLES FROM consumer')
  from psycopg.types.string import BytesDumper
  from psycopg.adapt import Dumper
  class ChangedBytes(BytesDumper):
   def dump(self,value):return super().dump(value+b'-changed')
  class ChangedCapacity(Dumper):
   oid=23
   def dump(self,value):return str(9 if value==6 else value).encode()
  self.admin.adapters.register_dumper(bytes,ChangedBytes)
  self.admin.adapters.register_dumper(int,ChangedCapacity)
  installed=bootstrap();self.assertIsInstance(installed,Ok,str(self.host._custody.last_attempt.error));self.assertFalse(installed.value.security_ready)
  self.assertEqual(self.admin.execute('SELECT %s::bytea,%s::int',(b'caller',6)).fetchone(),(b'caller-changed',9))
  self.assertEqual(self.admin.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard').fetchall(),[(identity,profile,1)])
  self.assertEqual(self.admin.execute('SELECT installation_identity_bytes,policy_profile_bytes,max_retained FROM truss.policy_publication_capacity').fetchall(),[(identity,profile,6)])
  self.assertIsInstance(bootstrap(),Error)
  self.assertEqual(self.admin.execute('TABLE bootstrap_caller_work').fetchall(),[('kept',)])
  self.host.detach();self.admin.rollback()
  self.assertIsNone(self.admin.execute("SELECT pg_catalog.to_regclass('truss.policy_generation_guard')").fetchone()[0])
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);tx=self.host.adopt_transaction().value
  committed=bootstrap();self.assertIsInstance(committed,Ok,str(self.host._custody.last_attempt.error));self.host.detach();self.admin.commit()
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(0,))
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as ordinary:
   for home in ['policy_generation_guard','policy_publication_claim','policy_publication_capacity']:
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):ordinary.execute(psycopg.sql.SQL('TABLE truss.{}').format(psycopg.sql.Identifier(home)))
   ordinary.execute("SET statement_timeout='10000'");ordinary.execute('BEGIN');ordinary_host=adopt_psycopg_host(ordinary,statement_timeout_ms=10000,operation_timeout_ms=10000)
   try:
    ordinary_adoption=ordinary_host.adopt_transaction();self.assertIsInstance(ordinary_adoption,Ok);ordinary_tx=ordinary_adoption.value
    denied=bootstrap_security_homes_in_transaction(ordinary_host,ordinary_tx,installation_identity=identity,authored_profile=profile,max_retained=6)
    self.assertIsInstance(denied,Error)
    self.assertEqual(ordinary.execute('SELECT 1').fetchone(),(1,))
   finally:ordinary_host.detach();ordinary.rollback()
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.operation.json').write_text(json.dumps({'observations':['foreign original identity refused','hostile default ACL refused with full home rollback','prior caller work preserved','exact original guard and capacity seeded despite caller custom bytes/int adapters; caller adapters preserved','existing homes refused without repair','outer rollback removes homes','original caller commit persists homes','ordinary native consumer denied all three homes and private bootstrap; transaction remains usable'],'scope':'Private installation operation only; no security-ready profile, policy activation, authority issuer, complete participant/native source qualification or backend acceptance.'},indent=2)+'\n')
 def test_fresh_installer_seals_candidate_homes_and_refuses_inherited_acl(self):
  from unittest.mock import patch
  from truss import Error
  import truss.catalog_runtime as runtime
  contracts=Path(__file__).resolve().parents[3]/'docs/helix/02-design/contracts'
  sources=[(contracts/name).read_text() for name in ['installation-policy-guard-v0.1.proposal.sql','installation-publication-claim-v0.2.tombstone.proposal.sql','installation-publication-capacity-profile-v0.1.proposal.sql']]
  manifest,digest,original=runtime._release()
  self.admin.execute("CREATE TEMP TABLE caller_bootstrap_work(value text);INSERT INTO caller_bootstrap_work VALUES('kept')")
  observations=[]
  for mode in ['default-table-grant','direct-column-grant']:
   if mode=='default-table-grant':self.admin.execute('ALTER DEFAULT PRIVILEGES GRANT SELECT ON TABLES TO consumer')
   extra=sources+(['GRANT SELECT(generation) ON truss.policy_generation_guard TO consumer'] if mode=='direct-column-grant' else [])
   with patch('truss.catalog_runtime._release',return_value=(manifest,digest,tuple(original)+tuple(extra))):
    refused=self.assembly.install_in_transaction(self.tx,owner_role='security_bootstrap_owner',registrar_role='security_bootstrap_client')
   self.assertIsInstance(refused,Error)
   self.assertIsNone(self.admin.execute("SELECT pg_catalog.to_regnamespace('truss')").fetchone()[0])
   self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_catalog.pg_roles WHERE rolname IN ('security_bootstrap_owner','security_bootstrap_client')").fetchone(),(0,))
   self.assertEqual(self.admin.execute('TABLE caller_bootstrap_work').fetchall(),[('kept',)])
   observations.append({'id':'production-installer-refuses-'+mode,'observed':{'namespace':None,'createdRoles':0,'callerWork':'kept'}})
   if mode=='default-table-grant':self.admin.execute('ALTER DEFAULT PRIVILEGES REVOKE SELECT ON TABLES FROM consumer')
  # The release source injection is test-only, not an adopted release manifest.
  with patch('truss.catalog_runtime._release',return_value=(manifest,digest,tuple(original)+tuple(sources))):self.install()
  homes=['policy_generation_guard','policy_publication_claim','policy_publication_capacity']
  owners=self.admin.execute("SELECT c.relname,r.rolname FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_roles r ON r.oid=c.relowner WHERE n.nspname='truss' AND c.relname=ANY(%s) ORDER BY c.relname",(homes,)).fetchall()
  self.assertEqual(owners,sorted((home,self.installation.owner_role) for home in homes))
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as ordinary:
   for home in homes:
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):ordinary.execute(psycopg.sql.SQL('TABLE truss.{}').format(psycopg.sql.Identifier(home)))
    self.assertFalse(ordinary.execute("SELECT pg_catalog.has_any_column_privilege(current_user,%s,'SELECT,INSERT,UPDATE,REFERENCES')",('truss.'+home,)).fetchone()[0])
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):ordinary.execute(psycopg.sql.SQL('SET ROLE {}').format(psycopg.sql.Identifier(self.installation.owner_role)))
  observations.append({'id':'production-fresh-installer-seals-proposed-security-homes','observed':owners,'ordinaryRead':'42501','ordinaryColumnPrivileges':False,'ownerAdoption':'42501'})
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.installer.json').write_text(json.dumps({'observations':observations,'scope':'Existing production fresh-install savepoint and privilege sealing primitive with explicit test-only source injection. Original release manifest is unchanged; security homes/profile are not adopted or activated. No complete issuer/source/caller/bootstrap qualification or acceptance-case promotion.'},indent=2)+'\n')
 def test_candidate_security_bootstrap_atomicity_and_owner_isolation(self):
  self.install();self.host.detach();self.admin.commit()
  contracts=Path(__file__).resolve().parents[3]/'docs/helix/02-design/contracts'
  homes=[('policy_generation_guard','installation-policy-guard-v0.1.proposal.sql'),('policy_publication_claim','installation-publication-claim-v0.2.tombstone.proposal.sql'),('policy_publication_capacity','installation-publication-capacity-profile-v0.1.proposal.sql')]
  installation=self.admin.execute('SELECT installation_id::text FROM truss.catalog_runtime_installation').fetchone()[0].encode()
  profile=b'bootstrap-ownership-fixture/0.1';observations=[]
  # Every partial prefix must disappear with its original failed transaction.
  for prefix in range(1,len(homes)+1):
   self.admin.execute('BEGIN')
   for home,source in homes[:prefix]:self.admin.execute((contracts/source).read_text())
   with self.assertRaises(psycopg.errors.DivisionByZero):self.admin.execute('SELECT 1/0')
   self.admin.rollback()
   absent=[self.admin.execute('SELECT pg_catalog.to_regclass(%s)',('truss.'+home,)).fetchone()[0] for home,_ in homes]
   self.assertEqual(absent,[None]*3)
   observations.append({'id':'failed-bootstrap-prefix-'+str(prefix),'observed':absent})
  self.admin.execute('BEGIN')
  for home,source in homes:
   self.admin.execute((contracts/source).read_text())
   self.admin.execute(psycopg.sql.SQL('ALTER TABLE truss.{} OWNER TO {}').format(psycopg.sql.Identifier(home),psycopg.sql.Identifier(self.installation.owner_role)))
   self.admin.execute(psycopg.sql.SQL('REVOKE ALL ON truss.{} FROM PUBLIC').format(psycopg.sql.Identifier(home)))
  self.admin.execute('INSERT INTO truss.policy_generation_guard VALUES(1,%s,%s,1)',(installation,profile))
  self.admin.execute('INSERT INTO truss.policy_publication_capacity VALUES(1,%s,%s,6)',(installation,profile))
  self.admin.commit()
  ownership=self.admin.execute("SELECT c.relname,r.rolname FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_roles r ON r.oid=c.relowner WHERE n.nspname='truss' AND c.relname=ANY(%s) ORDER BY c.relname",([home for home,_ in homes],)).fetchall()
  self.assertEqual(ownership,sorted((home,self.installation.owner_role) for home,_ in homes))
  observations.append({'id':'candidate-security-homes-original-installation-owner','observed':ownership})
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as ordinary:
   for home,_ in homes:
    for privilege in ['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']:
     allowed=ordinary.execute('SELECT pg_catalog.has_table_privilege(current_user,%s,%s)',('truss.'+home,privilege)).fetchone()[0]
     self.assertFalse(allowed)
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):ordinary.execute(psycopg.sql.SQL('TABLE truss.{}').format(psycopg.sql.Identifier(home)))
    observations.append({'id':'ordinary-consumer-security-home-denied-'+home,'observed':'42501','privilegesAbsent':['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']})
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.bootstrap.json').write_text(json.dumps({'observations':observations,'scope':'Candidate DDL under explicit trusted fixture administrator, atomic rollback and existing installation-owner isolation only. No public runtime adoption, authenticated profile issuer, complete native source census or production bootstrap admission.'},indent=2)+'\n')
 def test_owned_connections_close_before_schema_teardown(self):
  import time
  self.install();self.host.detach();self.admin.commit()
  self.admin.execute('CREATE SCHEMA ontology_fixture;CREATE TABLE ontology_fixture.cleanup_probe(value text)')
  owned=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(owned);pid=owned.execute('SELECT pg_backend_pid()').fetchone()[0];owned.execute('BEGIN');owned.execute('TABLE ontology_fixture.cleanup_probe').fetchall()
  locks=self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=%s AND relation='ontology_fixture.cleanup_probe'::regclass",(pid,)).fetchone()[0];self.assertGreater(locks,0)
  self._close_owned_connections();self.assertTrue(owned.closed)
  remaining=1;wait_until=time.monotonic()+5
  while time.monotonic()<wait_until:
   remaining=self.admin.execute('SELECT count(*) FROM pg_stat_activity WHERE pid=%s',(pid,)).fetchone()[0]
   if remaining==0:break
   time.sleep(.02)
  self.assertEqual(remaining,0);self.admin.execute("SET lock_timeout='250ms'");self.admin.execute('DROP SCHEMA ontology_fixture CASCADE');self.admin.execute("SET lock_timeout='0'")
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']+'.cleanup.json').write_text(json.dumps({'observations':[{'id':'owned-fixture-transaction-holds-native-schema-lock','observed':locks},{'id':'owned-fixture-close-precedes-schema-drop','observed':{'closed':owned.closed,'remainingBackend':remaining}}],'scope':'Explicit owned fixture connection only; not production caller transaction recovery or unknown-outcome cleanup.'},indent=2)+'\n')
 def tearDown(self):
  self._close_owned_connections()
  self.admin.rollback();self.admin.execute('DROP SCHEMA IF EXISTS relational_fixture CASCADE;DROP SCHEMA IF EXISTS ontology_fixture CASCADE')
  super().tearDown()
 def consumer(self):
  # Larger atomic ontology seed; retain an explicit finite native deadline.
  from truss import adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
  connection=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=60000')
  self.addCleanup(connection.close);connection.execute('BEGIN');host=adopt_psycopg_host(connection,statement_timeout_ms=60000,operation_timeout_ms=60000);self.addCleanup(host.detach);self.consumer_connections.append((connection,host))
  assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
  return connection,host,assembly,host.adopt_transaction().value
 def model(self,document):
  if document['id']!='adoc':return # The ontology belongs to adoc; retain zdoc baseline.
  m=document['modules'][0];m['elements']=[];m['relationships']=[]
  for name,fields in RECORDS.items():
   m['elements'].append({'id':name,'kind':'record','members':[{'module':'m','element':name+'-'+f} for f in fields],'keys':[{'id':'pk','name':'primary','primary':True,'fields':[{'module':'m','element':name+'-code'}]}],'extensions':{}})
   for field,scalar in fields.items():m['elements'].append({'id':name+'-'+field,'name':name+'-'+field,'kind':'field','scalarType':scalar,'nullability':'required','cardinality':'one','extensions':{}})
  for name,(source,target) in LINKS.items():m['relationships'].append({'id':name,'name':name,'source':[{'module':'m','element':source}],'target':[{'module':'m','element':target,'key':'pk'}],'sourceMultiplicity':{'min':0,'max':100},'targetMultiplicity':{'min':0,'max':100},'targetLifecycle':'independent','directed':True})
 def test_public_created_membership_graph(self):
  c,h,a,t=self.ready(self.model);ops=[]
  def node(record,code,**extras):
   values={'code':code,**extras};ops.append(CreateObject(type_definition_pin=self.types[('adoc',record)].definition_pin,values=tuple(AuthoredValue(name=record+'-'+f,value=BooleanValue(value=v) if isinstance(v,bool) else TextValue(kind='string',text=v)) for f,v in values.items()),ownership=RootlessOwnership(),alias=code))
  node('Client','C');node('Project','A');node('Project','B')
  for login in ['alice','bob','outsider']:node('Staff','staff-'+login,login=login)
  for code in ['RA','RB','RAB','RO']:node('Resource',code,secret='raw-'+code)
  for code,active in [('AA',True),('AB',False),('BB',True)]:node('Assignment',code,active=active)
  connections={'staff_assignment':[('staff-alice','AA'),('staff-alice','AB'),('staff-bob','BB')],'assignment_project':[('AA','A'),('AB','B'),('BB','B')],'resource_project':[('RA','A'),('RB','B'),('RAB','A'),('RAB','B')],'project_client':[('A','C'),('B','C')]}
  for link,pairs in connections.items():
   pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id=link).value.definition_pin
   for i,(source,target) in enumerate(pairs):ops.append(CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias=source),target=AliasObjectReference(alias=target),values=(),order_key=NullOrderKey(),alias=link+str(i)))
  inp,_=self.input(a,t,tuple(ops));result=a.apply_in_transaction(t,inp,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun');self.assertIsInstance(result,Ok,str(a._host._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess);h.detach();c.commit()
  packet={'records':{},'links':{}}
  for record,fields in RECORDS.items():
   type_id=self.types[('adoc',record)].type_id;props={name:str(pid) for name,pid in self.admin.execute('SELECT name,prop_id FROM truss.prop_def WHERE type_id=%s',(int(type_id),))}
   packet['records'][record]={'typeId':type_id,'fields':{f:{'id':props[record+'-'+f],'scalar':scalar} for f,scalar in fields.items()}}
  for link,(source,target) in LINKS.items():packet['links'][link]={'id':str(self.admin.execute("SELECT rel_type_id FROM truss.rel_def WHERE document_id='adoc' AND module='m' AND rel_id=%s",(link,)).fetchone()[0]),'source':source,'target':target}
  produced=subprocess.run(['/opt/homebrew/bin/bun',str(Path(__file__).resolve().parents[3]/'tests/fixtures/security-public-ontology.ts')],input=json.dumps(packet),text=True,capture_output=True,timeout=30);self.assertEqual(produced.returncode,0,produced.stderr);sql=json.loads(produced.stdout);observations=[]
  version=self.admin.execute('SHOW server_version_num').fetchone()[0];self.assertEqual(version,'180006');observations.append({'id':'native-version','observed':version})
  self.admin.execute('CREATE SCHEMA ontology_fixture')
  for name,source in sql['objects'].items():
   valid=self.admin.execute(source['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'complete-object-source-'+name,'observed':valid});self.admin.execute('CREATE VIEW ontology_fixture.'+name.lower()+' AS '+source['sql'])
  for name,source in sql['edges'].items():
   valid=self.admin.execute(source['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'complete-edge-endpoints-'+name,'observed':valid});self.admin.execute('CREATE VIEW ontology_fixture.'+name+' AS '+source['sql'])
  self.admin.execute('CREATE VIEW ontology_fixture.assignments AS SELECT a.code,a.active,s.source_code AS staff_code,p.target_code AS project_code FROM ontology_fixture.assignment a LEFT JOIN ontology_fixture.staff_assignment s ON s.target_code=a.code LEFT JOIN ontology_fixture.assignment_project p ON p.source_code=a.code')
  rows=self.admin.execute('SELECT code,active,staff_code,project_code FROM ontology_fixture.assignments ORDER BY code').fetchall();self.assertEqual(rows,[('AA',True,'staff-alice','A'),('AB',False,'staff-alice','B'),('BB',True,'staff-bob','B')]);observations.append({'id':'actual-assignment-business-key-facts','observed':[list(r) for r in rows]})
  self.admin.execute('CREATE ROLE ontology_facts NOLOGIN NOINHERIT NOSUPERUSER NOBYPASSRLS;GRANT USAGE ON SCHEMA truss,ontology_fixture TO ontology_facts;GRANT SELECT(id,type_id,props) ON truss.object TO ontology_facts;GRANT SELECT(id,rel_type_id,source_id,source_type,target_id,target_type) ON truss.edge TO ontology_facts')
  self.addCleanup(self.admin.execute,'DROP OWNED BY ontology_facts;DROP ROLE ontology_facts')
  for name in [*RECORDS,*LINKS,'assignments']:self.admin.execute('ALTER VIEW ontology_fixture.'+name.lower()+' OWNER TO ontology_facts')
  self.admin.execute('CREATE FUNCTION ontology_fixture.decision_bound(text,text) RETURNS text LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=on AS $$ '+sql['fold']['sql']+' $$;REVOKE ALL ON FUNCTION ontology_fixture.decision_bound(text,text) FROM PUBLIC;GRANT CREATE ON SCHEMA ontology_fixture TO ontology_facts;ALTER FUNCTION ontology_fixture.decision_bound(text,text) OWNER TO ontology_facts')
  self.admin.execute("CREATE FUNCTION ontology_fixture.eligible_bound(text,text) RETURNS bool LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET row_security=on AS $$ DECLARE decision text;BEGIN decision:=ontology_fixture.decision_bound($1,$2);IF decision IS NULL OR decision NOT IN ('permit','deny') THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;RETURN decision='permit';END $$;REVOKE ALL ON FUNCTION ontology_fixture.eligible_bound(text,text) FROM PUBLIC;ALTER FUNCTION ontology_fixture.eligible_bound(text,text) OWNER TO ontology_facts")
  self.admin.execute("CREATE FUNCTION ontology_fixture.eligible(text) RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=on AS $$ DECLARE subject_count bigint;subject_key text;BEGIN IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'security authority profile unavailable' USING ERRCODE='0A000';END IF;SELECT count(*),min(code) INTO subject_count,subject_key FROM ontology_fixture.staff WHERE login OPERATOR(pg_catalog.=) SESSION_USER::pg_catalog.text;IF subject_count<>1 THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;RETURN ontology_fixture.eligible_bound($1,subject_key);END $$;REVOKE ALL ON FUNCTION ontology_fixture.eligible(text) FROM PUBLIC;ALTER FUNCTION ontology_fixture.eligible(text) OWNER TO ontology_facts;REVOKE CREATE ON SCHEMA ontology_fixture FROM ontology_facts")
  self.admin.execute('ALTER TABLE truss.object ENABLE ROW LEVEL SECURITY;ALTER TABLE truss.object FORCE ROW LEVEL SECURITY;CREATE POLICY complete_private_facts ON truss.object FOR SELECT TO ontology_facts USING(true)')
  resource=packet['records']['Resource'];key=resource['fields']['code']['id']
  for login in ['alice','bob','outsider']:
   self.admin.execute('CREATE ROLE '+login+' LOGIN NOSUPERUSER NOBYPASSRLS;GRANT USAGE ON SCHEMA truss,ontology_fixture TO '+login+';GRANT SELECT(id,type_id,props) ON truss.object TO '+login+';GRANT EXECUTE ON FUNCTION ontology_fixture.eligible(text) TO '+login)
   self.addCleanup(self.admin.execute,'DROP OWNED BY '+login+';DROP ROLE '+login)
  self.admin.execute("CREATE POLICY resource_membership ON truss.object FOR SELECT TO alice,bob,outsider USING(type_id="+resource['typeId']+" AND ontology_fixture.eligible(props->'"+key+"'->>'text'))")
  expected={'alice':['RA','RAB'],'bob':['RAB','RB'],'outsider':[]}
  for login,wanted in expected.items():
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    identity=reader.execute('SELECT session_user,current_user').fetchone();self.assertEqual(identity,(login,login));observations.append({'id':'original-native-caller-'+login,'observed':list(identity)})
    actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,wanted);observations.append({'id':'membership-resource-oracle-'+login,'expected':wanted,'observed':actual})
    count=reader.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(count,len(wanted));observations.append({'id':'membership-count-'+login,'observed':count})
    flags=reader.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone();self.assertEqual(flags,(False,False));observations.append({'id':'ordinary-native-flags-'+login,'observed':list(flags)})
    private_count=reader.execute('SELECT count(*) FROM truss.object WHERE type_id=%s',(int(packet['records']['Assignment']['typeId']),)).fetchone()[0];self.assertEqual(private_count,0);observations.append({'id':'hidden-assignment-object-count-'+login,'observed':private_count})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SELECT * FROM truss.edge')
    observations.append({'id':'private-native-edge-table-denied-'+login,'observed':'42501'})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute("SELECT ontology_fixture.eligible_bound('RB','staff-bob')")
    observations.append({'id':'caller-supplied-subject-binding-denied-'+login,'observed':'42501'})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SET ROLE ontology_facts')
    observations.append({'id':'private-fact-owner-adoption-denied-'+login,'observed':'42501'})
    storage_substitution=reader.execute('SELECT id FROM truss.object WHERE ontology_fixture.eligible(id::text)').fetchall();self.assertEqual(storage_substitution,[]);observations.append({'id':'storage-id-is-not-business-key-'+login,'observed':storage_substitution})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SELECT * FROM ontology_fixture.assignments')
    observations.append({'id':'private-assignment-view-denied-'+login,'observed':'42501'})
  aliases={entry.alias:entry.identity for entry in result.value.response.semantic.aliases};assignment=packet['records']['Assignment'];active_id=assignment['fields']['active']['id']
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AA'].id),int(assignment['typeId'])))
  for login,wanted in [('alice',[]),('bob',['RAB','RB'])]:
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,wanted);observations.append({'id':'fresh-statement-after-committed-assignment-change-'+login,'expected':wanted,'observed':actual})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':True}),int(aliases['AA'].id),int(assignment['typeId'])))
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
  with psycopg.connect(**params,autocommit=True) as reader:
   actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);observations.append({'id':'restored-assignment-original-visibility','observed':actual})
  # A malformed hidden assignment must not look like a complete empty result.
  self.admin.execute('UPDATE truss.object SET props=props-%s WHERE id=%s AND type_id=%s',(active_id,int(aliases['AB'].id),int(assignment['typeId'])))
  valid=self.admin.execute(sql['objects']['Assignment']['validitySql']).fetchone()[0];self.assertEqual(valid,'false');observations.append({'id':'hidden-assignment-required-field-preflight-invalid','observed':valid})
  decision=self.admin.execute("SELECT ontology_fixture.decision_bound('RB','staff-bob')").fetchone()[0];self.assertEqual(decision,'indeterminate');observations.append({'id':'unrelated-valid-permit-cannot-hide-incomplete-facts','observed':decision})
  for login in ['alice','bob','outsider']:
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    for operation,query in [('list','SELECT id FROM truss.object'),('count','SELECT count(*) FROM truss.object')]:
     with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as failure:reader.execute(query).fetchall()
     self.assertEqual(failure.exception.sqlstate,'55000');self.assertEqual(failure.exception.diag.message_primary,'security facts unavailable');observations.append({'id':'incomplete-private-facts-refuse-'+operation+'-'+login,'observed':{'sqlState':'55000','message':'security facts unavailable'}})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AB'].id),int(assignment['typeId'])))
  valid=self.admin.execute(sql['objects']['Assignment']['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'complete-assignment-facts-restored','observed':valid})
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='bob'
  with psycopg.connect(**params,autocommit=True) as reader:
   actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RAB','RB']);observations.append({'id':'restored-facts-original-bob-visibility','observed':actual})
  # An endpoint object exists, but a required business key cannot be decoded.
  project=packet['records']['Project'];project_key=project['fields']['code']['id']
  self.admin.execute('UPDATE truss.object SET props=props-%s WHERE id=%s AND type_id=%s',(project_key,int(aliases['B'].id),int(project['typeId'])))
  rows=self.admin.execute('SELECT occurrence_id,source_code,target_code FROM ontology_fixture.resource_project ORDER BY occurrence_id').fetchall();self.assertEqual(len(rows),4);self.assertEqual(sum(row[2] is None for row in rows),2);observations.append({'id':'malformed-project-key-preserves-original-edge-population','edgeCount':len(rows),'nullTargetKeys':2})
  decision=self.admin.execute("SELECT ontology_fixture.decision_bound('RA','staff-alice')").fetchone()[0];self.assertEqual(decision,'indeterminate');observations.append({'id':'valid-other-project-does-not-hide-null-endpoint-key','observed':decision})
  for login in ['alice','bob','outsider']:
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as failure:reader.execute('SELECT count(*) FROM truss.object').fetchall()
    self.assertEqual(failure.exception.sqlstate,'55000');observations.append({'id':'incomplete-endpoint-key-refuses-count-'+login,'observed':'55000'})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(project_key,json.dumps({'kind':'string','text':'B'}),int(aliases['B'].id),int(project['typeId'])))
  decision=self.admin.execute("SELECT ontology_fixture.decision_bound('RA','staff-alice')").fetchone()[0];self.assertEqual(decision,'permit');observations.append({'id':'restored-project-key-restores-original-decision','observed':decision})
  # Ownerless data must not short-circuit a missing intrinsic subject binding.
  for resource_key,subject_key in [('RO',None),(None,'staff-alice')]:
   decision=self.admin.execute('SELECT ontology_fixture.decision_bound(%s,%s)',(resource_key,subject_key)).fetchone()[0];self.assertEqual(decision,'indeterminate');observations.append({'id':'missing-intrinsic-key-indeterminate-'+('subject' if subject_key is None else 'resource'),'observed':decision})
  staff=packet['records']['Staff'];login_id=staff['fields']['login']['id']
  self.admin.execute('UPDATE truss.object SET props=props-%s WHERE id=%s AND type_id=%s',(login_id,int(aliases['staff-alice'].id),int(staff['typeId'])))
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
  with psycopg.connect(**params,autocommit=True) as reader:
   with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as failure:reader.execute("SELECT ontology_fixture.eligible('RO')").fetchall()
   self.assertEqual(failure.exception.sqlstate,'55000');observations.append({'id':'missing-original-caller-binding-refuses-even-ownerless-resource','observed':'55000'})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(login_id,json.dumps({'kind':'string','text':'alice'}),int(aliases['staff-alice'].id),int(staff['typeId'])))
  with psycopg.connect(**params,autocommit=True) as reader:
   result=reader.execute("SELECT ontology_fixture.eligible('RO'),ontology_fixture.eligible('RA')").fetchone();self.assertEqual(result,(False,True));observations.append({'id':'restored-caller-binding-distinguishes-denial-and-permit','observed':list(result)})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(login_id,json.dumps({'kind':'string','text':'alice'}),int(aliases['staff-outsider'].id),int(staff['typeId'])))
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
  with psycopg.connect(**params,autocommit=True) as reader:
   for operation,query in [('ownerless',"SELECT ontology_fixture.eligible('RO')"),('count','SELECT count(*) FROM truss.object')]:
    with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as failure:reader.execute(query).fetchall()
    self.assertEqual(failure.exception.sqlstate,'55000');self.assertEqual(failure.exception.diag.message_primary,'security facts unavailable');observations.append({'id':'ambiguous-original-caller-refuses-'+operation,'observed':{'sqlState':'55000','message':'security facts unavailable'}})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(login_id,json.dumps({'kind':'string','text':'outsider'}),int(aliases['staff-outsider'].id),int(staff['typeId'])))
  with psycopg.connect(**params,autocommit=True) as reader:
   actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);observations.append({'id':'unique-original-caller-mapping-restores-visibility','observed':actual})
  params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
  with psycopg.connect(**params,autocommit=True) as old_snapshot:
   old_snapshot.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
   old_snapshot.execute('SELECT count(*) FROM pg_class').fetchone() # Establish original snapshot before change.
   isolation=old_snapshot.execute('SHOW transaction_isolation').fetchone()[0];self.assertEqual(isolation,'repeatable read');observations.append({'id':'old-authority-snapshot-established-before-change','observed':isolation})
   self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AA'].id),int(assignment['typeId'])))
   with self.assertRaises(psycopg.errors.FeatureNotSupported) as failure:old_snapshot.execute('SELECT count(*) FROM truss.object').fetchall()
   self.assertEqual(failure.exception.sqlstate,'0A000');self.assertEqual(failure.exception.diag.message_primary,'security authority profile unavailable');observations.append({'id':'first-protected-read-under-old-snapshot-refuses','observed':{'sqlState':'0A000','message':'security authority profile unavailable'}})
   old_snapshot.rollback()
  with psycopg.connect(**params,autocommit=True) as fresh:
   actual=[r[0] for r in fresh.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,[]);observations.append({'id':'fresh-read-after-committed-authority-change-denies','observed':actual})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':True}),int(aliases['AA'].id),int(assignment['typeId'])))
  with psycopg.connect(**params,autocommit=True) as fresh:
   actual=[r[0] for r in fresh.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);observations.append({'id':'restored-authority-fresh-read-original-vector','observed':actual})
  # Actual graph assignment writer waits through the fixture's buffered release.
  import threading,time
  writer=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(writer)
  writer_pid=writer.execute('SELECT pg_backend_pid()').fetchone()[0];errors=[]
  def revoke_assignment():
   try:writer.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AA'].id),int(assignment['typeId'])))
   except Exception as exc:errors.append(type(exc).__name__)
  self.admin.execute('BEGIN');self.admin.execute('LOCK TABLE truss.object,truss.edge,truss.type_def,truss.prop_def,truss.rel_def,truss.rel_endpoint IN SHARE MODE')
  thread=threading.Thread(target=revoke_assignment);thread.start()
  try:
   deadline=time.monotonic()+5;waiting=None
   while time.monotonic()<deadline:
    waiting=self.admin.execute("SELECT mode,granted FROM pg_locks WHERE pid=%s AND relation='truss.object'::regclass AND mode='RowExclusiveLock'",(writer_pid,)).fetchone()
    if waiting==('RowExclusiveLock',False):break
    time.sleep(.01)
   self.assertEqual(waiting,('RowExclusiveLock',False));observations.append({'id':'graph-assignment-revoker-native-wait','writerPid':writer_pid,'observed':list(waiting)})
   with psycopg.connect(**params,autocommit=True) as guarded_reader:
    buffered=[r[0] for r in guarded_reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(buffered,['RA','RAB'])
   self.assertTrue(thread.is_alive());observations.append({'id':'buffered-graph-read-released-before-revoker-commit','observed':buffered,'boundary':'fixture records final buffered return before releasing native source locks'})
  finally:self.admin.rollback();thread.join(12)
  self.assertFalse(thread.is_alive());self.assertEqual(errors,[]);observations.append({'id':'graph-assignment-revoker-completes-after-release','observed':'committed'})
  with psycopg.connect(**params,autocommit=True) as fresh:
   actual=[r[0] for r in fresh.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,[]);observations.append({'id':'new-read-after-drained-graph-change-denies','observed':actual})
  self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':True}),int(aliases['AA'].id),int(assignment['typeId'])))
  # Source-table exclusion cannot fence native role authority changes.
  control=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=5000');self._track_owned_connection(control)
  self.admin.execute('BEGIN');self.admin.execute('LOCK TABLE truss.object,truss.edge,truss.type_def,truss.prop_def,truss.rel_def,truss.rel_endpoint IN SHARE MODE')
  try:
   control.execute('ALTER ROLE alice BYPASSRLS')
   held=self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND mode='ShareLock' AND granted AND relation IN ('truss.object'::regclass,'truss.edge'::regclass,'truss.type_def'::regclass,'truss.prop_def'::regclass,'truss.rel_def'::regclass,'truss.rel_endpoint'::regclass)").fetchone()[0];self.assertEqual(held,6);observations.append({'id':'native-role-change-commits-while-six-source-locks-held','observed':held})
   with psycopg.connect(**params,autocommit=True) as changed_reader:
    flags=changed_reader.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone();self.assertEqual(flags,(False,True));observations.append({'id':'changed-original-caller-bypass-attribute','observed':list(flags)})
    count=changed_reader.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(count,13);observations.append({'id':'bypass-authority-defeats-source-lock-only-profile','observed':count,'qualification':'deliberate disposable authority-widening counterexample'})
  finally:
   control.execute('ALTER ROLE alice NOBYPASSRLS');self.admin.rollback()
  with psycopg.connect(**params,autocommit=True) as restored_reader:
   actual=[r[0] for r in restored_reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);observations.append({'id':'restored-native-caller-authority-original-vector','observed':actual})
  # Exercise the existing installation-wide authority guard's original SQL.
  contracts=Path(__file__).resolve().parents[3]/'docs/helix/02-design/contracts'
  from truss import adopt_psycopg_host
  from truss._security_home_installation import bootstrap_security_homes_in_transaction
  installation_bytes=self.admin.execute('SELECT installation_id::text FROM truss.catalog_runtime_installation').fetchone()[0].encode();profile_bytes=b'ontology-authority-guard-fixture/0.1'
  self.admin.execute('BEGIN');bootstrap_host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
  try:
   bootstrap_tx=bootstrap_host.adopt_transaction().value
   bootstrapped=bootstrap_security_homes_in_transaction(bootstrap_host,bootstrap_tx,installation_identity=installation_bytes,authored_profile=profile_bytes,max_retained=6)
   self.assertIsInstance(bootstrapped,Ok,str(bootstrap_host._custody.last_attempt.error));self.assertFalse(bootstrapped.value.security_ready)
  finally:bootstrap_host.detach()
  self.admin.commit()
  observations.append({'id':'ontology-lifecycle-uses-private-bootstrap-homes','observed':{'installationHex':installation_bytes.hex(),'profileHex':profile_bytes.hex(),'maxRetained':6,'securityReady':False},'qualification':'implemented bootstrap custody and sealed homes; candidate source/issuer/participant admission remains unqualified'})
  acquire=(contracts/'installation-policy-guard-acquire-v0.1.proposal.sql').read_text()
  advance=(contracts/'installation-policy-generation-advance-v0.1.proposal.sql').read_text()
  for ordinal in [1,2,3]:advance=advance.replace('$'+str(ordinal),'%s')
  authority_writer=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(authority_writer)
  authority_pid=authority_writer.execute('SELECT pg_backend_pid()').fetchone()[0];authority_errors=[];advanced=[]
  observations.append({'id':'native-role-change-uses-private-authority-operation','observed':{'expectedGeneration':1,'nextGeneration':2,'securityReady':False},'qualification':'original direct trusted fixture administrator; permission, full participant and source parity not admitted'})
  def controlled_role_change():
   try:
    from truss._security_authority_change import change_authority_in_transaction
    authority_writer.execute('BEGIN');writer_host=adopt_psycopg_host(authority_writer,statement_timeout_ms=10000,operation_timeout_ms=30000)
    try:
     writer_tx=writer_host.adopt_transaction().value
     def physical_role_change(cursor):cursor.execute('ALTER ROLE alice BYPASSRLS')
     changed=change_authority_in_transaction(writer_host,writer_tx,installation_identity=installation_bytes,authored_profile=profile_bytes,expected_generation=1,action=physical_role_change)
     if not isinstance(changed,Ok) or changed.value.generation!=2:raise ValueError('Original implemented authority change refused')
    finally:writer_host.detach()
    rows=authority_writer.execute("SELECT singleton::text,pg_catalog.encode(installation_identity_bytes,'hex'),pg_catalog.encode(policy_profile_bytes,'hex'),generation::text FROM truss.policy_generation_guard").fetchall()
    if rows!=[('1',installation_bytes.hex(),profile_bytes.hex(),'2')]:raise ValueError('Original stored generation advance refused')
    advanced.extend(rows);authority_writer.execute('COMMIT')
   except Exception as exc:authority_errors.append(type(exc).__name__);authority_writer.rollback()
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE').fetchone();guard_cursor=self.admin.execute(acquire);captured=guard_cursor.fetchall();self.assertEqual(captured,[('1',installation_bytes.hex(),profile_bytes.hex(),'1')]);observations.append({'id':'original-proposed-guard-acquisition','observed':[list(row) for row in captured]})
  decoder_packet={'columns':[{'name':column.name,'typeOid':str(column.type_code)} for column in guard_cursor.description],'rows':[list(row) for row in captured],'expected':{'installationIdentityHex':installation_bytes.hex(),'policyProfileHex':profile_bytes.hex()}}
  decoder=subprocess.run(['/opt/homebrew/bin/bun',str(Path(__file__).resolve().parents[3]/'tests/fixtures/security-authority-guard-decode.ts')],input=json.dumps(decoder_packet),text=True,capture_output=True,timeout=30);self.assertEqual(decoder.returncode,0,decoder.stderr);decoded=json.loads(decoder.stdout);self.assertEqual(decoded['generation'],'1');observations.append({'id':'actual-native-guard-descriptors-and-row-decoded','input':decoder_packet,'observed':decoded,'qualification':'local decoding, not a lease'})
  holder_pid=self.admin.execute('SELECT pg_backend_pid()').fetchone()[0];authority_thread=threading.Thread(target=controlled_role_change);authority_thread.start()
  try:
   deadline=time.monotonic()+5;blockers=[]
   while time.monotonic()<deadline:
    blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(authority_pid,)).fetchone()[0]
    if holder_pid in blockers:break
    time.sleep(.01)
   self.assertIn(holder_pid,blockers);observations.append({'id':'participating-native-role-changer-waits-on-authority-guard','blockerPid':holder_pid,'observed':blockers})
   with psycopg.connect(**params,autocommit=True) as admitted_fixture_reader:
    actual=[r[0] for r in admitted_fixture_reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,['RA','RAB']);self.assertTrue(authority_thread.is_alive());observations.append({'id':'guarded-buffered-result-before-authority-change','observed':actual})
  finally:self.admin.rollback();authority_thread.join(12)
  self.assertFalse(authority_thread.is_alive());self.assertEqual(authority_errors,[]);self.assertEqual(advanced,[('1',installation_bytes.hex(),profile_bytes.hex(),'2')]);observations.append({'id':'controlled-role-effect-and-generation-advance-commit','observed':[list(row) for row in advanced]})
  fresh_guard=self.admin.execute(acquire).fetchall();self.assertEqual(fresh_guard,[('1',installation_bytes.hex(),profile_bytes.hex(),'2')]);observations.append({'id':'next-authority-observation-sees-new-generation','observed':[list(row) for row in fresh_guard]})
  flags=self.admin.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname='alice'").fetchone();self.assertEqual(flags,(False,True));observations.append({'id':'new-generation-requires-original-caller-bypass-exclusion','observed':list(flags),'qualification':'new generation is not authorization'})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('ALTER ROLE alice NOBYPASSRLS');restored_generation=authority_writer.execute(advance,(installation_bytes,profile_bytes,2)).fetchall();self.assertEqual(restored_generation,[('1',installation_bytes.hex(),profile_bytes.hex(),'3')]);authority_writer.execute('COMMIT');observations.append({'id':'controlled-restoration-preserves-generation-continuity','observed':[list(row) for row in restored_generation]})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('ALTER ROLE alice BYPASSRLS')
  stale=authority_writer.execute(advance,(installation_bytes,profile_bytes,2)).fetchall();self.assertEqual(stale,[]);observations.append({'id':'stale-expected-generation-refuses-advance','observed':stale});authority_writer.rollback()
  flags=self.admin.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname='alice'").fetchone();generation=self.admin.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone()[0];self.assertEqual(flags,(False,False));self.assertEqual(generation,'3');observations.append({'id':'failed-controlled-delta-rolls-back-role-and-generation','observed':{'flags':list(flags),'generation':generation}})
  for invalid_identity,invalid_profile,kind in [(b'foreign-installation',profile_bytes,'installation'),(installation_bytes,b'foreign-profile','profile')]:
   authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone()
   rows=authority_writer.execute(advance,(invalid_identity,invalid_profile,3)).fetchall();self.assertEqual(rows,[]);authority_writer.rollback();observations.append({'id':'foreign-authority-'+kind+'-refuses-generation-advance','observed':rows})
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as ordinary:
   with self.assertRaises(psycopg.errors.InsufficientPrivilege) as failure:ordinary.execute('UPDATE truss.policy_generation_guard SET generation=1')
   self.assertEqual(failure.exception.sqlstate,'42501');observations.append({'id':'ordinary-authority-generation-reset-denied','observed':'42501'})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('UPDATE truss.policy_generation_guard SET generation=9223372036854775807 WHERE singleton=1');authority_writer.execute('ALTER ROLE alice BYPASSRLS')
  exhausted=authority_writer.execute(advance,(installation_bytes,profile_bytes,9223372036854775807)).fetchall();self.assertEqual(exhausted,[]);observations.append({'id':'authority-generation-maximum-refuses-instead-of-wrap','observed':exhausted})
  maximum=authority_writer.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone()[0];self.assertEqual(maximum,'9223372036854775807');observations.append({'id':'maximum-generation-remains-exact-before-rollback','observed':maximum});authority_writer.rollback()
  flags=self.admin.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname='alice'").fetchone();generation=self.admin.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone()[0];self.assertEqual(flags,(False,False));self.assertEqual(generation,'3');observations.append({'id':'exhausted-authority-delta-rolls-back-role-and-generation','observed':{'flags':list(flags),'generation':generation}})
  # Losing the original coordinator cannot authorize its buffered result.
  coordinator=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(coordinator)
  coordinator_pid=coordinator.execute('SELECT pg_backend_pid()').fetchone()[0];coordinator.execute('BEGIN');coordinator.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE').fetchone();held_generation=coordinator.execute(acquire).fetchall();self.assertEqual(held_generation,[('1',installation_bytes.hex(),profile_bytes.hex(),'3')])
  data_reader=psycopg.connect(**params,autocommit=True);self._track_owned_connection(data_reader);data_reader.execute('BEGIN');data_reader.execute("CREATE TEMP TABLE prior_data_work(value text);INSERT INTO prior_data_work VALUES('kept')")
  pending_buffer=[r[0] for r in data_reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))]
  self.assertEqual(pending_buffer,['RA','RAB']);lost_errors=[];lost_advance=[]
  def change_after_coordinator_loss():
   try:
    authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':False}),int(aliases['AA'].id),int(assignment['typeId'])))
    rows=authority_writer.execute(advance,(installation_bytes,profile_bytes,3)).fetchall()
    if rows!=[('1',installation_bytes.hex(),profile_bytes.hex(),'4')]:raise ValueError('Original generation advance refused')
    lost_advance.extend(rows);authority_writer.execute('COMMIT')
   except Exception as exc:lost_errors.append(type(exc).__name__);authority_writer.rollback()
  loss_thread=threading.Thread(target=change_after_coordinator_loss);loss_thread.start()
  try:
   deadline=time.monotonic()+5;blockers=[]
   while time.monotonic()<deadline:
    blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(authority_pid,)).fetchone()[0]
    if coordinator_pid in blockers:break
    time.sleep(.01)
   self.assertIn(coordinator_pid,blockers);observations.append({'id':'authority-writer-waits-on-original-coordinator','observed':blockers,'coordinatorPid':coordinator_pid})
   successful_probe=coordinator.execute('SELECT 1').fetchone();self.assertEqual(successful_probe,(1,));observations.append({'id':'coordinator-positive-probe-before-native-loss','observed':list(successful_probe),'qualification':'positive probe alone does not cover subsequent release'})
   stale_buffer=list(pending_buffer)
   terminated=self.admin.execute('SELECT pg_terminate_backend(%s)',(coordinator_pid,)).fetchone()[0];self.assertIs(terminated,True);observations.append({'id':'owned-original-coordinator-terminated','observed':True})
   with self.assertRaises(psycopg.OperationalError) as loss:coordinator.execute('SELECT 1')
   observations.append({'id':'original-coordinator-native-liveness-probe-fails','observed':{'kind':type(loss.exception).__name__,'sqlState':loss.exception.sqlstate}})
  finally:
   coordinator.close();loss_thread.join(12)
  self.assertFalse(loss_thread.is_alive());self.assertEqual(lost_errors,[]);self.assertEqual(lost_advance,[('1',installation_bytes.hex(),profile_bytes.hex(),'4')]);observations.append({'id':'authority-change-commits-after-native-coordinator-loss','observed':[list(row) for row in lost_advance]})
  self.assertEqual(data_reader.info.transaction_status,psycopg.pq.TransactionStatus.INTRANS);prior=data_reader.execute('TABLE prior_data_work').fetchall();self.assertEqual(prior,[('kept',)]);observations.append({'id':'coordinator-loss-preserves-original-data-transaction-work','observed':[list(row) for row in prior]});data_reader.rollback()
  pending_buffer=[];observations.append({'id':'lost-coordinator-buffer-withheld-by-fixture','observed':pending_buffer,'qualification':'explicit fixture release arbitration, not a production lease'})
  with psycopg.connect(**params,autocommit=True) as fresh:
   actual=[r[0] for r in fresh.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,[]);observations.append({'id':'new-read-after-coordinator-loss-observes-revocation','observed':actual})
   self.assertEqual(stale_buffer,['RA','RAB']);self.assertNotEqual(stale_buffer,actual);observations.append({'id':'positive-liveness-probe-retains-stale-buffer-counterexample','observed':{'bufferBeforeLoss':stale_buffer,'freshAfterRevocation':actual},'qualification':'would leak if published using only the earlier positive probe; actual fixture withheld it'})
  # Same logical Record/Relationship condition over independent raw tables.
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();authority_writer.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':True}),int(aliases['AA'].id),int(assignment['typeId'])));rows=authority_writer.execute(advance,(installation_bytes,profile_bytes,4)).fetchall();self.assertEqual(rows,[('1',installation_bytes.hex(),profile_bytes.hex(),'5')]);authority_writer.execute('COMMIT')
  # Durable outstanding publication survives native coordinator death.
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(0,))
  def claim_sql(name,count):
   source=(contracts/name).read_text()
   for ordinal in range(1,count+1):source=source.replace('$'+str(ordinal),'%s')
   return source
  register=claim_sql('installation-publication-claim-register-v0.2.tombstone.proposal.sql',4)
  settle=claim_sql('installation-publication-claim-settle-v0.2.tombstone.proposal.sql',4)
  claim_advance=claim_sql('installation-policy-generation-advance-v0.3.tombstone.proposal.sql',3)
  operation_bytes=b'fixture-original-publication-1'
  claim_coordinator=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(claim_coordinator)
  claim_pid=claim_coordinator.execute('SELECT pg_backend_pid()').fetchone()[0]
  claim_coordinator.execute('BEGIN');claim_coordinator.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');claim_coordinator.execute(acquire).fetchall()
  registered=claim_coordinator.execute(register,(operation_bytes,installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(registered,[(operation_bytes.hex(),)]);claim_coordinator.execute('COMMIT')
  observations.append({'id':'durable-publication-claim-commit-confirmed','observed':registered})
  self.assertIs(self.admin.execute('SELECT pg_terminate_backend(%s)',(claim_pid,)).fetchone()[0],True)
  outstanding=self.admin.execute("SELECT pg_catalog.encode(operation_identity_bytes,'hex'),generation::text FROM truss.policy_publication_claim").fetchall();self.assertEqual(outstanding,[(operation_bytes.hex(),'5')]);observations.append({'id':'publication-claim-survives-native-coordinator-loss','observed':outstanding})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone()
  blocked=authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(blocked,[]);authority_writer.execute('ROLLBACK');observations.append({'id':'outstanding-publication-refuses-participating-authority-advance','observed':blocked})
  for wrong in [(b'foreign-operation',installation_bytes,profile_bytes,5),(operation_bytes,b'foreign-installation',profile_bytes,5),(operation_bytes,installation_bytes,b'foreign-profile',5),(operation_bytes,installation_bytes,profile_bytes,4)]:
   self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();deleted=self.admin.execute(settle,wrong).fetchall();self.assertEqual(deleted,[]);self.admin.execute('ROLLBACK')
  observations.append({'id':'publication-claim-original-settlement-mismatch-refuses','observed':'four mismatches preserve original claim'})
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as ordinary:
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):ordinary.execute('DELETE FROM truss.policy_publication_claim')
  observations.append({'id':'ordinary-publication-claim-reset-refuses','observed':'42501'})
  second_operation=b'fixture-original-publication-2'
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();second_registered=self.admin.execute(register,(second_operation,installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(second_registered,[(second_operation.hex(),)]);self.admin.execute('COMMIT');observations.append({'id':'overlapping-publication-claims-independently-register','observed':second_registered})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall()
  with self.assertRaises(psycopg.errors.UniqueViolation) as duplicate:self.admin.execute(register,(second_operation,installation_bytes,profile_bytes,5)).fetchall()
  self.assertEqual(duplicate.exception.sqlstate,'23505');self.admin.execute('ROLLBACK');observations.append({'id':'duplicate-original-publication-claim-refuses-replacement','observed':'23505'})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();stale_registered=self.admin.execute(register,(b'stale-publication',installation_bytes,profile_bytes,4)).fetchall();self.assertEqual(stale_registered,[]);self.admin.execute('ROLLBACK');observations.append({'id':'stale-publication-generation-cannot-register','observed':stale_registered})
  # Fixture establishes withheld completion; no production sink/issuer proof.
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();deleted=self.admin.execute(settle,(operation_bytes,installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(deleted,[(operation_bytes.hex(),)]);self.admin.execute('COMMIT');observations.append({'id':'original-publication-claim-settles-after-fixture-withholding','observed':deleted,'qualification':'fixture completion premise only'})
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();still_blocked=authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(still_blocked,[]);authority_writer.execute('ROLLBACK');observations.append({'id':'settling-one-publication-preserves-other-operation-exclusion','observed':still_blocked})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(second_operation,installation_bytes,profile_bytes,5)).fetchall(),[(second_operation.hex(),)]);self.admin.execute('ROLLBACK')
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim WHERE NOT settled').fetchone(),(1,));observations.append({'id':'rolled-back-publication-settlement-retains-claim','observed':1})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(second_operation,installation_bytes,profile_bytes,5)).fetchall(),[(second_operation.hex(),)]);self.admin.execute('COMMIT')
  authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();advanced=authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(advanced,[('1',installation_bytes.hex(),profile_bytes.hex(),'6')]);authority_writer.execute('ROLLBACK');observations.append({'id':'settled-publication-allows-participating-advance','observed':advanced,'qualification':'rolled back to preserve generation5; no production authority-delta proof'})
  retained=self.admin.execute("SELECT pg_catalog.encode(operation_identity_bytes,'hex'),generation::text,settled FROM truss.policy_publication_claim ORDER BY operation_identity_bytes").fetchall();self.assertEqual(retained,[(operation_bytes.hex(),'5',True),(second_operation.hex(),'5',True)]);observations.append({'id':'settled-publication-identities-retain-native-tombstones','observed':retained})
  for replay in [operation_bytes,second_operation]:
   self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall()
   with self.assertRaises(psycopg.errors.UniqueViolation) as duplicate:self.admin.execute(register,(replay,installation_bytes,profile_bytes,5)).fetchall()
   self.assertEqual(duplicate.exception.sqlstate,'23505');self.admin.execute('ROLLBACK')
  observations.append({'id':'settled-original-operation-token-replay-refuses','observed':'two23505 refusals; no replacement claims'})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();repeated_settlement=self.admin.execute(settle,(operation_bytes,installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(repeated_settlement,[]);self.admin.execute('ROLLBACK');observations.append({'id':'settled-original-operation-cannot-settle-twice','observed':repeated_settlement})
  # A pending registration SHARE scope drains before writer's fresh claim check.
  pending_operation=b'fixture-pending-publication'
  pending_owner=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(pending_owner)
  pending_pid=pending_owner.execute('SELECT pg_backend_pid()').fetchone()[0]
  pending_owner.execute('BEGIN');pending_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');pending_owner.execute(acquire).fetchall();self.assertEqual(pending_owner.execute(register,(pending_operation,installation_bytes,profile_bytes,5)).fetchall(),[(pending_operation.hex(),)])
  pending_errors=[];pending_advances=[]
  def advance_after_pending_registration():
   try:
    authority_writer.execute('BEGIN');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();pending_advances.extend(authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,5)).fetchall());authority_writer.execute('ROLLBACK')
   except BaseException as error:pending_errors.append(type(error).__name__);authority_writer.execute('ROLLBACK')
  pending_thread=threading.Thread(target=advance_after_pending_registration);pending_thread.start()
  try:
   blockers=[];wait_until=time.monotonic()+8
   while time.monotonic()<wait_until:
    blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(authority_pid,)).fetchone()[0]
    if pending_pid in blockers:break
    time.sleep(.02)
   self.assertIn(pending_pid,blockers);observations.append({'id':'authority-writer-drains-pending-publication-registration','observed':blockers})
   pending_owner.execute('COMMIT')
  finally:
   pending_owner.rollback();pending_thread.join(12)
  self.assertFalse(pending_thread.is_alive());self.assertEqual(pending_errors,[]);self.assertEqual(pending_advances,[]);observations.append({'id':'fresh-post-drain-authority-check-sees-committed-claim','observed':pending_advances})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(pending_operation,installation_bytes,profile_bytes,5)).fetchall(),[(pending_operation.hex(),)]);self.admin.execute('COMMIT')
  # Capacity source: retained tombstones count; serialization precedes fresh count.
  capacity_lock=(contracts/'installation-publication-claim-capacity-lock-v0.1.proposal.sql').read_text()
  capacity_register=(contracts/'installation-publication-claim-register-v0.3.capacity.proposal.sql').read_text()
  for ordinal in range(1,6):capacity_register=capacity_register.replace('$'+str(ordinal),'%(p'+str(ordinal)+')s')
  def capacity_execute(connection,parameters):return connection.execute(capacity_register,{'p'+str(i):value for i,value in enumerate(parameters,1)})
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(3,))
  for cap,token in [(3,b'full-registry'),(0,b'zero-capacity'),(-1,b'negative-capacity'),(1048577,b'oversized-capacity'),(4,b'x'*2049)]:
   self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.admin.execute(capacity_lock);refused=capacity_execute(self.admin,(token,installation_bytes,profile_bytes,5,cap)).fetchall();self.assertEqual(refused,[]);self.admin.execute('ROLLBACK')
  observations.append({'id':'publication-capacity-and-token-bounds-refuse-before-registration','observed':'five zero-row refusals; retained tombstones preserved'})
  capacity_owner=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(capacity_owner);capacity_pid=capacity_owner.execute('SELECT pg_backend_pid()').fetchone()[0]
  capacity_waiter=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(capacity_waiter);capacity_waiter_pid=capacity_waiter.execute('SELECT pg_backend_pid()').fetchone()[0]
  capacity_owner.execute('BEGIN');capacity_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');capacity_owner.execute(acquire).fetchall();capacity_owner.execute(capacity_lock);last_registered=capacity_execute(capacity_owner,(b'last-capacity-slot',installation_bytes,profile_bytes,5,4)).fetchall();self.assertEqual(last_registered,[(b'last-capacity-slot'.hex(),)])
  capacity_errors=[];capacity_rows=[]
  def register_after_capacity_drain():
   try:
    capacity_waiter.execute('BEGIN');capacity_waiter.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');capacity_waiter.execute(acquire).fetchall();capacity_waiter.execute(capacity_lock);capacity_rows.extend(capacity_execute(capacity_waiter,(b'racing-capacity-slot',installation_bytes,profile_bytes,5,4)).fetchall());capacity_waiter.execute('ROLLBACK')
   except BaseException as error:capacity_errors.append(type(error).__name__);capacity_waiter.execute('ROLLBACK')
  capacity_thread=threading.Thread(target=register_after_capacity_drain);capacity_thread.start()
  try:
   blockers=[];wait_until=time.monotonic()+8
   while time.monotonic()<wait_until:
    blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(capacity_waiter_pid,)).fetchone()[0]
    if capacity_pid in blockers:break
    time.sleep(.02)
   self.assertIn(capacity_pid,blockers);observations.append({'id':'publication-capacity-registrants-native-serialization','observed':blockers});capacity_owner.execute('COMMIT')
  finally:capacity_owner.rollback();capacity_thread.join(12)
  self.assertFalse(capacity_thread.is_alive());self.assertEqual(capacity_errors,[]);self.assertEqual(capacity_rows,[]);self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(4,));observations.append({'id':'fresh-capacity-check-refuses-racing-last-slot','observed':{'rows':capacity_rows,'retained':4}})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(b'last-capacity-slot',installation_bytes,profile_bytes,5)).fetchall(),[(b'last-capacity-slot'.hex(),)]);self.admin.execute('COMMIT')
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.admin.execute(capacity_lock);self.assertEqual(capacity_execute(self.admin,(b'after-capacity-settlement',installation_bytes,profile_bytes,5,4)).fetchall(),[]);self.admin.execute('ROLLBACK');observations.append({'id':'settlement-cannot-reopen-retained-token-capacity','observed':'zero rows after settled fourth identity'})
  # Failed capacity acquisition rolls back only its savepoint, not caller work.
  for interruption in ['timeout','cancel']:
   capacity_owner.execute('BEGIN');capacity_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');capacity_owner.execute(acquire).fetchall();capacity_owner.execute(capacity_lock)
   interrupted=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(interrupted);interrupted_pid=interrupted.execute('SELECT pg_backend_pid()').fetchone()[0]
   interrupted.execute('BEGIN');interrupted.execute('CREATE TEMP TABLE prior_capacity_work(value text)');interrupted.execute("INSERT INTO prior_capacity_work VALUES('kept')");interrupted.execute('SAVEPOINT capacity_attempt');interrupted.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');interrupted.execute(acquire).fetchall()
   interruption_states=[];interruption_thread=None
   try:
    if interruption=='timeout':
     interrupted.execute("SET LOCAL lock_timeout='150ms'")
     with self.assertRaises(psycopg.errors.LockNotAvailable) as error:interrupted.execute(capacity_lock)
     interruption_states.append(error.exception.sqlstate)
    else:
     def wait_for_capacity_lock():
      try:interrupted.execute(capacity_lock);interruption_states.append('unexpected-success')
      except psycopg.Error as error:interruption_states.append(error.sqlstate)
     interruption_thread=threading.Thread(target=wait_for_capacity_lock);interruption_thread.start();blockers=[];wait_until=time.monotonic()+8
     while time.monotonic()<wait_until:
      blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(interrupted_pid,)).fetchone()[0]
      if capacity_pid in blockers:break
      time.sleep(.02)
     self.assertIn(capacity_pid,blockers);self.assertIs(self.admin.execute('SELECT pg_cancel_backend(%s)',(interrupted_pid,)).fetchone()[0],True);interruption_thread.join(12);self.assertFalse(interruption_thread.is_alive())
    self.assertEqual(interruption_states,['55P03' if interruption=='timeout' else '57014']);self.assertEqual(interrupted.info.transaction_status,psycopg.pq.TransactionStatus.INERROR);observations.append({'id':'publication-capacity-'+interruption+'-native-refusal','observed':interruption_states})
    interrupted.execute('ROLLBACK TO SAVEPOINT capacity_attempt');self.assertEqual(interrupted.info.transaction_status,psycopg.pq.TransactionStatus.INTRANS);self.assertEqual(interrupted.execute('TABLE prior_capacity_work').fetchall(),[('kept',)])
    locks=self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=%s AND relation IN ('truss.schema_head'::regclass,'truss.policy_generation_guard'::regclass,'truss.policy_publication_claim'::regclass)",(interrupted_pid,)).fetchone()[0];self.assertEqual(locks,0);self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(4,));observations.append({'id':'publication-capacity-'+interruption+'-savepoint-preserves-prior-work','observed':{'partialLocks':locks,'retainedClaims':4,'priorWork':'kept'}})
   finally:
    capacity_owner.rollback()
    if interruption_thread is not None:interruption_thread.join(12)
    interrupted.rollback();interrupted.close()
  # Source capacity from original protected native profile, not a fifth argument.
  self.assertEqual(self.admin.execute('SELECT installation_identity_bytes,policy_profile_bytes,max_retained FROM truss.policy_publication_capacity').fetchall(),[(installation_bytes,profile_bytes,6)])
  profile_register=(contracts/'installation-publication-claim-register-v0.4.profile.proposal.sql').read_text()
  for ordinal in range(1,5):profile_register=profile_register.replace('$'+str(ordinal),'%(p'+str(ordinal)+')s')
  def profile_execute(connection,parameters):return connection.execute(profile_register,{'p'+str(i):value for i,value in enumerate(parameters,1)})
  for mutation in ["DELETE FROM truss.policy_publication_capacity","UPDATE truss.policy_publication_capacity SET installation_identity_bytes='foreign'::bytea","UPDATE truss.policy_publication_capacity SET policy_profile_bytes='foreign'::bytea","UPDATE truss.policy_publication_capacity SET max_retained=4"]:
   self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();self.admin.execute(mutation);self.admin.execute(capacity_lock);refused=profile_execute(self.admin,(b'profile-bound-operation',installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(refused,[]);self.admin.execute('ROLLBACK')
  observations.append({'id':'native-capacity-profile-missing-mismatched-full-refuses','observed':'four zero-row refusals; fixture mutations rolled back'})
  with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as ordinary:
   with self.assertRaises(psycopg.errors.InsufficientPrivilege) as failure:ordinary.execute('UPDATE truss.policy_publication_capacity SET max_retained=100')
   self.assertEqual(failure.exception.sqlstate,'42501')
  observations.append({'id':'ordinary-native-capacity-profile-change-refuses','observed':'42501'})
  from security_commit_loss_proxy import CommitResponseDropProxy
  commit_proxy=CommitResponseDropProxy(psycopg.conninfo.conninfo_to_dict(self.info.connection_uri));self.addCleanup(commit_proxy.close)
  uncertain_owner=psycopg.connect(self.info.connection_uri,host='127.0.0.1',port=commit_proxy.port,sslmode='disable',gssencmode='disable',autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(uncertain_owner)
  from truss._security_publication_registration import register_publication_in_transaction
  uncertain_owner.execute('BEGIN');registration_host=adopt_psycopg_host(uncertain_owner,statement_timeout_ms=10000,operation_timeout_ms=30000)
  try:
   registration_tx=registration_host.adopt_transaction().value
   registered=register_publication_in_transaction(registration_host,registration_tx,operation_identity=b'original-commit-ack-loss',installation_identity=installation_bytes,authored_profile=profile_bytes,expected_generation=5)
   self.assertIsInstance(registered,Ok,str(registration_host._custody.last_attempt.error));self.assertFalse(registered.value.publication_allowed)
  finally:registration_host.detach()
  observations.append({'id':'original-commit-loss-uses-private-registration-operation','observed':{'generation':5,'publicationAllowed':False},'qualification':'pending original caller commit; no authenticated operation issuer or release grant'})
  commit_proxy.armed.set()
  with self.assertRaises(psycopg.OperationalError) as ack_loss:uncertain_owner.execute('COMMIT')
  self.assertIsNone(ack_loss.exception.sqlstate);self.assertTrue(commit_proxy.dropped.wait(2));commit_proxy.close();self.assertEqual(commit_proxy.errors,[]);observations.append({'id':'original-registration-native-commit-response-dropped','observed':{'nativeCommand':'COMMIT','sqlState':ack_loss.exception.sqlstate},'qualification':'stock driver transport failure; no manufactured native SQLSTATE'})
  observe_claim=claim_sql('installation-publication-claim-observe-v0.1.proposal.sql',1)
  def decode_native_claim(token,settled=None):
   cursor=self.admin.execute(observe_claim,(token,));native_rows=cursor.fetchall()
   native_packet={'columns':[{'name':c.name,'typeOid':str(c.type_code)} for c in cursor.description],'rows':[list(row) for row in native_rows],'expected':{'operationIdentityHex':token.hex(),'installationIdentityHex':installation_bytes.hex(),'policyProfileHex':profile_bytes.hex(),'generation':'5'}}
   runner=str(Path(__file__).resolve().parents[3]/'tests/fixtures/security-publication-claim-decode.ts')
   decoded=subprocess.run(['/opt/homebrew/bin/bun',runner],input=json.dumps(native_packet),text=True,capture_output=True,timeout=30);self.assertEqual(decoded.returncode,0,decoded.stderr);value=json.loads(decoded.stdout)
   self.assertEqual(value,{'state':'not-observed'} if settled is None else {'state':'observed',**native_packet['expected'],'settled':settled})
   wrong=json.loads(json.dumps(native_packet));wrong['expected']['operationIdentityHex']='ff'
   if settled is not None:self.assertNotEqual(subprocess.run(['/opt/homebrew/bin/bun',runner],input=json.dumps(wrong),text=True,capture_output=True,timeout=30).returncode,0)
   return native_packet,value
  # No re-insertion/disclosure: drain original registrants and freshly reconcile.
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone()
  reconciled=self.admin.execute("SELECT pg_catalog.encode(installation_identity_bytes,'hex'),pg_catalog.encode(policy_profile_bytes,'hex'),generation::text,settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s",(b'original-commit-ack-loss',)).fetchall();self.assertEqual(reconciled,[(installation_bytes.hex(),profile_bytes.hex(),'5',False)]);native_packet,claim_decoded=decode_native_claim(b'original-commit-ack-loss',False);absent_packet,absent_decoded=decode_native_claim(b'never-registered-original');self.admin.execute('COMMIT');observations.append({'id':'lost-registration-ack-reconciles-exact-original-durable-claim','observed':reconciled});observations.append({'id':'native-original-claim-recovery-carriers-decode','input':native_packet,'observed':claim_decoded});observations.append({'id':'native-missing-original-claim-is-only-not-observed','input':absent_packet,'observed':absent_decoded})
  # Fixture ledger dispatched no data query; conclusively withheld, then settle.
  settlement_proxy=CommitResponseDropProxy(psycopg.conninfo.conninfo_to_dict(self.info.connection_uri));self.addCleanup(settlement_proxy.close)
  settlement_owner=psycopg.connect(self.info.connection_uri,host='127.0.0.1',port=settlement_proxy.port,sslmode='disable',gssencmode='disable',autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(settlement_owner)
  from truss.execution import Error
  from truss._security_publication_settlement import settle_publication_in_transaction
  settlement_owner.execute('BEGIN');settlement_host=adopt_psycopg_host(settlement_owner,statement_timeout_ms=10000,operation_timeout_ms=30000)
  try:
   adopted_settlement=settlement_host.adopt_transaction();self.assertIsInstance(adopted_settlement,Ok);settlement_tx=adopted_settlement.value
   settlement_owner.execute('CREATE TEMP TABLE settlement_prior_work(value int)');settlement_owner.execute('INSERT INTO settlement_prior_work VALUES(17)')
   for token,install,profile,generation in [(b'missing-original',installation_bytes,profile_bytes,5),(b'original-commit-ack-loss',installation_bytes,b'wrong-profile',5),(b'original-commit-ack-loss',installation_bytes,profile_bytes,4),(b'original-commit-ack-loss',b'wrong-installation',profile_bytes,5)]:
    refused=settle_publication_in_transaction(settlement_host,settlement_tx,operation_identity=token,installation_identity=install,authored_profile=profile,expected_generation=generation)
    self.assertIsInstance(refused,Error);self.assertEqual(settlement_owner.execute('SELECT value FROM settlement_prior_work').fetchall(),[(17,)])
    self.assertEqual(settlement_owner.execute('SELECT settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'original-commit-ack-loss',)).fetchone(),(False,))
   settled=settle_publication_in_transaction(settlement_host,settlement_tx,operation_identity=b'original-commit-ack-loss',installation_identity=installation_bytes,authored_profile=profile_bytes,expected_generation=5)
   self.assertIsInstance(settled,Ok,str(settlement_host._custody.last_attempt.error));self.assertFalse(settled.value.publication_allowed)
   repeated_private=settle_publication_in_transaction(settlement_host,settlement_tx,operation_identity=b'original-commit-ack-loss',installation_identity=installation_bytes,authored_profile=profile_bytes,expected_generation=5)
   self.assertIsInstance(repeated_private,Error);self.assertEqual(settlement_owner.execute('SELECT value FROM settlement_prior_work').fetchall(),[(17,)]);self.assertEqual(settlement_owner.execute('SELECT settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'original-commit-ack-loss',)).fetchone(),(True,))
  finally:settlement_host.detach()
  observations.append({'id':'original-settlement-commit-loss-uses-private-operation','observed':{'generation':5,'publicationAllowed':False},'qualification':'fixture conclusively withheld; completion/issuer authentication remains a premise'})
  settlement_proxy.armed.set()
  with self.assertRaises(psycopg.OperationalError) as settlement_loss:settlement_owner.execute('COMMIT')
  self.assertIsNone(settlement_loss.exception.sqlstate);self.assertTrue(settlement_proxy.dropped.wait(2));settlement_proxy.close();self.assertEqual(settlement_proxy.errors,[]);observations.append({'id':'original-settlement-native-commit-response-dropped','observed':{'sqlState':settlement_loss.exception.sqlstate,'replacementOperation':False},'qualification':'fixture no-data-query completion premise; not production sink proof'})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();settled_packet,settled_decoded=decode_native_claim(b'original-commit-ack-loss',True);self.admin.execute('COMMIT');observations.append({'id':'native-original-settled-claim-recovery-carriers-decode','input':settled_packet,'observed':settled_decoded})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();repeated=self.admin.execute(settle,(b'original-commit-ack-loss',installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(repeated,[]);self.admin.execute('ROLLBACK');observations.append({'id':'lost-settlement-ack-reconciled-original-cannot-settle-twice','observed':repeated,'qualification':'negative control after original reconciliation, not automatic retry'})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.admin.execute(capacity_lock)
  with self.assertRaises(psycopg.errors.UniqueViolation) as replay:profile_execute(self.admin,(b'original-commit-ack-loss',installation_bytes,profile_bytes,5)).fetchall()
  self.assertEqual(replay.exception.sqlstate,'23505');self.admin.execute('ROLLBACK');observations.append({'id':'lost-registration-ack-never-replaced-original-token','observed':'original settled tombstone refuses23505'})
  publication_owner=psycopg.connect(self.info.connection_uri,autocommit=True);self._track_owned_connection(publication_owner);publication_pid=publication_owner.execute('SELECT pg_backend_pid()').fetchone()[0]
  for failure_mode in ['explicit_rollback','native_failure']:
   recovery_thread=None;recovery_rows=[];recovery_errors=[]
   publication_owner.execute('BEGIN');publication_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');publication_owner.execute(acquire).fetchall();publication_owner.execute(capacity_lock)
   try:
    pending_registration=profile_execute(publication_owner,(b'profile-bound-operation',installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(pending_registration,[(b'profile-bound-operation'.hex(),)])
    self.assertEqual(publication_owner.execute('SELECT settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'profile-bound-operation',)).fetchone(),(False,));self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'profile-bound-operation',)).fetchone(),(0,))
    if failure_mode=='explicit_rollback':
     recovery_reader=psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=10000');self._track_owned_connection(recovery_reader);recovery_pid=recovery_reader.execute('SELECT pg_backend_pid()').fetchone()[0]
     def recover_after_original_drain():
      try:
       recovery_reader.execute('BEGIN');recovery_reader.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');recovery_reader.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone();recovery_rows.extend(recovery_reader.execute(observe_claim,(b'profile-bound-operation',)).fetchall());recovery_reader.execute('COMMIT')
      except BaseException as error:recovery_errors.append(type(error).__name__);recovery_reader.rollback()
     recovery_thread=threading.Thread(target=recover_after_original_drain);recovery_thread.start();blockers=[];wait_until=time.monotonic()+8
     while time.monotonic()<wait_until:
      blockers=self.admin.execute('SELECT pg_blocking_pids(%s)',(recovery_pid,)).fetchone()[0]
      if publication_pid in blockers:break
      time.sleep(.02)
     self.assertIn(publication_pid,blockers);observations.append({'id':'original-claim-recovery-drains-invisible-pending-registration','observed':{'blockers':blockers,'unguardedVisibleRows':0}})
    if failure_mode=='native_failure':
     with self.assertRaises(psycopg.errors.DivisionByZero) as error:publication_owner.execute('SELECT 1/0')
     self.assertEqual(error.exception.sqlstate,'22012');self.assertEqual(publication_owner.info.transaction_status,psycopg.pq.TransactionStatus.INERROR)
   finally:
    publication_owner.rollback()
    if recovery_thread is not None:recovery_thread.join(12)
   if recovery_thread is not None:
    self.assertFalse(recovery_thread.is_alive());self.assertEqual(recovery_errors,[]);self.assertEqual(recovery_rows,[]);observations.append({'id':'fresh-original-claim-recovery-after-drained-rollback-is-not-observed','observed':recovery_rows,'qualification':'native absence after known rollback; decoder still supplies no issuer/abort proof'})
   self.assertEqual(publication_owner.info.transaction_status,psycopg.pq.TransactionStatus.IDLE);self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'profile-bound-operation',)).fetchone(),(0,));self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.policy_publication_claim').fetchone(),(5,));observations.append({'id':'profile-registration-'+failure_mode+'-preserves-capacity-and-original-token','observed':{'retained':5,'originalTokenRows':0,'commit':'not-published'},'qualification':'confirmed rollback only; no unknown-commit retry'})
  publication_owner.execute('BEGIN');publication_owner.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');publication_owner.execute(acquire).fetchall();publication_owner.execute(capacity_lock);profile_registered=profile_execute(publication_owner,(b'profile-bound-operation',installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(profile_registered,[(b'profile-bound-operation'.hex(),)]);publication_owner.execute('COMMIT');observations.append({'id':'native-profile-capacity-registers-original-next-slot','observed':profile_registered})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.admin.execute(capacity_lock);refused=profile_execute(self.admin,(b'profile-bound-overflow',installation_bytes,profile_bytes,5)).fetchall();self.assertEqual(refused,[]);self.admin.execute('ROLLBACK');observations.append({'id':'native-profile-capacity-exhaustion-refuses','observed':refused})
  read_params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);read_params['user']='alice'
  def protected_codes():
   with psycopg.connect(**read_params,autocommit=True) as reader:return [r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))]
  real_buffer=protected_codes();self.assertEqual(real_buffer,['RA','RAB']);observations.append({'id':'durable-registered-operation-buffers-real-protected-read','observed':list(real_buffer)})
  self.assertIs(self.admin.execute('SELECT pg_terminate_backend(%s)',(publication_pid,)).fetchone()[0],True)
  with self.assertRaises(psycopg.OperationalError):publication_owner.execute('SELECT 1')
  self.assertEqual(self.admin.execute('SELECT settled FROM truss.policy_publication_claim WHERE operation_identity_bytes=%s',(b'profile-bound-operation',)).fetchone(),(False,));observations.append({'id':'real-protected-buffer-original-coordinator-loss-retains-claim','observed':'unsettled'})
  def participating_assignment_change(active,expected_generation,fault=None):
   authority_writer.execute('BEGIN')
   try:
    authority_writer.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');authority_writer.execute('SELECT generation FROM truss.policy_generation_guard WHERE singleton=1 FOR UPDATE').fetchone()
    if authority_writer.execute('SELECT EXISTS(SELECT 1 FROM truss.policy_publication_claim WHERE NOT settled)').fetchone()[0]:authority_writer.execute('ROLLBACK');return 'refused'
    authority_writer.execute('UPDATE truss.object SET props=jsonb_set(props,ARRAY[%s],%s::jsonb) WHERE id=%s AND type_id=%s',(active_id,json.dumps({'kind':'boolean','value':active}),int(aliases['AA'].id),int(assignment['typeId'])))
    if fault=='after_effects':
     self.assertEqual(authority_writer.execute('SELECT props->%s FROM truss.object WHERE id=%s AND type_id=%s',(active_id,int(aliases['AA'].id),int(assignment['typeId']))).fetchone(),({'kind':'boolean','value':False},));authority_writer.execute('SELECT 1/0')
    advanced=authority_writer.execute(claim_advance,(installation_bytes,profile_bytes,expected_generation)).fetchall();self.assertEqual(advanced,[('1',installation_bytes.hex(),profile_bytes.hex(),str(expected_generation+1))])
    if fault=='after_generation':
     self.assertEqual(authority_writer.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone(),(str(expected_generation+1),));authority_writer.execute('SELECT 1/0')
    authority_writer.execute('COMMIT');return advanced
   except BaseException:authority_writer.rollback();raise
  self.assertEqual(participating_assignment_change(False,5),'refused');self.assertEqual(protected_codes(),['RA','RAB']);self.assertEqual(self.admin.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone(),('5',));observations.append({'id':'durable-real-read-refuses-assignment-revocation-before-effects','observed':{'generation':'5','freshCodes':['RA','RAB']}})
  # Explicit fixture withholding is the completion premise, not a production sink.
  real_buffer=[];observations.append({'id':'durable-real-read-withholds-buffer-before-original-settlement','observed':real_buffer,'qualification':'fixture completion only'})
  self.admin.execute('BEGIN');self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE');self.admin.execute(acquire).fetchall();self.assertEqual(self.admin.execute(settle,(b'profile-bound-operation',installation_bytes,profile_bytes,5)).fetchall(),[(b'profile-bound-operation'.hex(),)]);self.admin.execute('COMMIT')
  for fault in ['after_effects','after_generation']:
   with self.assertRaises(psycopg.errors.DivisionByZero) as failure:participating_assignment_change(False,5,fault=fault)
   self.assertEqual(failure.exception.sqlstate,'22012');self.assertEqual(authority_writer.info.transaction_status,psycopg.pq.TransactionStatus.IDLE)
   self.assertEqual(self.admin.execute('SELECT props->%s FROM truss.object WHERE id=%s AND type_id=%s',(active_id,int(aliases['AA'].id),int(assignment['typeId']))).fetchone(),({'kind':'boolean','value':True},));self.assertEqual(self.admin.execute('SELECT generation::text FROM truss.policy_generation_guard WHERE singleton=1').fetchone(),('5',));self.assertEqual(protected_codes(),['RA','RAB']);observations.append({'id':'durable-assignment-'+fault+'-native-failure-rolls-back-effect-and-generation','observed':{'sqlState':'22012','generation':'5','active':True,'freshCodes':['RA','RAB']}})
  committed=participating_assignment_change(False,5);self.assertEqual(committed,[('1',installation_bytes.hex(),profile_bytes.hex(),'6')]);observations.append({'id':'durable-real-read-settlement-permits-committed-assignment-revocation','observed':committed})
  fresh_codes=protected_codes();self.assertEqual(fresh_codes,[]);observations.append({'id':'durable-real-read-fresh-admission-after-revocation-denies','observed':fresh_codes})
  restored=participating_assignment_change(True,6);self.assertEqual(restored,[('1',installation_bytes.hex(),profile_bytes.hex(),'7')]);self.assertEqual(protected_codes(),['RA','RAB']);observations.append({'id':'durable-real-read-controlled-restoration-advances-generation','observed':restored})
  self.admin.execute('CREATE SCHEMA relational_fixture;CREATE TABLE relational_fixture.client(code text PRIMARY KEY);CREATE TABLE relational_fixture.project(code text PRIMARY KEY);CREATE TABLE relational_fixture.staff(code text PRIMARY KEY,login text NOT NULL);CREATE TABLE relational_fixture.resource(code text PRIMARY KEY,secret text NOT NULL);CREATE TABLE relational_fixture.assignment(code text PRIMARY KEY,active boolean NOT NULL)')
  for table,codes in [('client',['C']),('project',['A','B']),('resource',['RA','RB','RAB','RO'])]:
   for code in codes:
    if table=='resource':self.admin.execute('INSERT INTO relational_fixture.resource VALUES(%s,%s)',(code,'raw-'+code))
    else:self.admin.execute('INSERT INTO relational_fixture.'+table+' VALUES(%s)',(code,))
  for login in ['alice','bob','outsider']:self.admin.execute('INSERT INTO relational_fixture.staff VALUES(%s,%s)',('staff-'+login,login))
  for code,active in [('AA',True),('AB',False),('BB',True)]:self.admin.execute('INSERT INTO relational_fixture.assignment VALUES(%s,%s)',(code,active))
  for link,(source,target) in LINKS.items():
   self.admin.execute('CREATE TABLE relational_fixture.'+link+'(occurrence_id text PRIMARY KEY,source_code text NOT NULL REFERENCES relational_fixture.'+source.lower()+'(code),target_code text NOT NULL REFERENCES relational_fixture.'+target.lower()+'(code))')
   for index,(left,right) in enumerate(connections[link]):self.admin.execute('INSERT INTO relational_fixture.'+link+' VALUES(%s,%s,%s)',('raw-'+link+str(index),left,right))
  self.admin.execute('GRANT USAGE ON SCHEMA relational_fixture TO ontology_facts;GRANT SELECT ON ALL TABLES IN SCHEMA relational_fixture TO ontology_facts;GRANT CREATE ON SCHEMA relational_fixture TO ontology_facts')
  self.admin.execute('CREATE FUNCTION relational_fixture.decision_bound(text,text) RETURNS text LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ '+sql['flatFold']['sql']+' $$;REVOKE ALL ON FUNCTION relational_fixture.decision_bound(text,text) FROM PUBLIC;ALTER FUNCTION relational_fixture.decision_bound(text,text) OWNER TO ontology_facts')
  self.admin.execute("CREATE FUNCTION relational_fixture.eligible(text) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ DECLARE n bigint;subject_key text;decision text;BEGIN IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'security authority profile unavailable' USING ERRCODE='0A000';END IF;SELECT count(*),min(code) INTO n,subject_key FROM relational_fixture.staff WHERE login=SESSION_USER::text;IF n<>1 THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;decision:=relational_fixture.decision_bound($1,subject_key);IF decision IS NULL OR decision NOT IN ('permit','deny') THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;RETURN decision='permit';END $$;REVOKE ALL ON FUNCTION relational_fixture.eligible(text) FROM PUBLIC;ALTER FUNCTION relational_fixture.eligible(text) OWNER TO ontology_facts;REVOKE CREATE ON SCHEMA relational_fixture FROM ontology_facts")
  self.admin.execute('ALTER TABLE relational_fixture.resource ENABLE ROW LEVEL SECURITY;ALTER TABLE relational_fixture.resource FORCE ROW LEVEL SECURITY;CREATE POLICY resource_membership ON relational_fixture.resource TO alice,bob,outsider USING(relational_fixture.eligible(code))')
  for login in ['alice','bob','outsider']:
   self.admin.execute('GRANT USAGE ON SCHEMA relational_fixture TO '+login+';GRANT SELECT ON relational_fixture.resource TO '+login+';GRANT EXECUTE ON FUNCTION relational_fixture.eligible(text) TO '+login)
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    flat=[r[0] for r in reader.execute('SELECT code FROM relational_fixture.resource ORDER BY code')];graph=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(flat,expected[login]);self.assertEqual(graph,expected[login]);observations.append({'id':'same-policy-raw-and-graph-oracle-'+login,'expected':expected[login],'raw':flat,'graph':graph})
    raw_count=reader.execute('SELECT count(*) FROM relational_fixture.resource').fetchone()[0];graph_count=reader.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(raw_count,len(expected[login]));self.assertEqual(graph_count,len(expected[login]));observations.append({'id':'same-policy-native-count-'+login,'raw':raw_count,'graph':graph_count})
    for selected in ['RA','RB','RO']:
     wanted=[selected] if selected in expected[login] else []
     raw_lookup=[row[0] for row in reader.execute('SELECT code FROM relational_fixture.resource WHERE code=%s',(selected,))];graph_lookup=[row[0] for row in reader.execute("SELECT props->%s->>'text' FROM truss.object WHERE props->%s->>'text'=%s",(key,key,selected))];self.assertEqual(raw_lookup,wanted);self.assertEqual(graph_lookup,wanted);observations.append({'id':'same-policy-native-key-lookup-'+login+'-'+selected,'raw':raw_lookup,'graph':graph_lookup})
    for offset in [0,1,2]:
     wanted=expected[login][offset:offset+1]
     raw_page=[row[0] for row in reader.execute('SELECT code FROM relational_fixture.resource ORDER BY code LIMIT 1 OFFSET %s',(offset,))];graph_page=[row[0] for row in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text' LIMIT 1 OFFSET %s",(key,key,offset))];self.assertEqual(raw_page,wanted);self.assertEqual(graph_page,wanted);observations.append({'id':'same-policy-native-sorted-page-'+login+'-'+str(offset),'raw':raw_page,'graph':graph_page})
    raw_pairs=reader.execute('SELECT count(*) FROM relational_fixture.resource a CROSS JOIN relational_fixture.resource b').fetchone()[0];graph_pairs=reader.execute('SELECT count(*) FROM truss.object a CROSS JOIN truss.object b').fetchone()[0];self.assertEqual(raw_pairs,len(expected[login])**2);self.assertEqual(graph_pairs,len(expected[login])**2);observations.append({'id':'same-policy-native-self-join-count-'+login,'raw':raw_pairs,'graph':graph_pairs})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SELECT * FROM relational_fixture.assignment')
    observations.append({'id':'raw-private-assignment-table-denied-'+login,'observed':'42501'})
  # Activate constant-transformed field disclosure; no raw bag/column grants.
  for namespace,disclosure in [('ontology_fixture',sql['graphDisclosure']),('relational_fixture',sql['flatDisclosure'])]:
   self.admin.execute('GRANT CREATE ON SCHEMA '+namespace+' TO ontology_facts')
   self.admin.execute('CREATE FUNCTION '+namespace+'.disclosure_bound(text,text) RETURNS TABLE(decision text,disclosure jsonb) LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ '+disclosure['sql']+' $$;REVOKE ALL ON FUNCTION '+namespace+'.disclosure_bound(text,text) FROM PUBLIC;ALTER FUNCTION '+namespace+'.disclosure_bound(text,text) OWNER TO ontology_facts')
   body="DECLARE n bigint;subject_key text;r record;d record;mask jsonb;BEGIN IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'security authority profile unavailable' USING ERRCODE='0A000';END IF;SELECT count(*),min(s.code) INTO n,subject_key FROM "+namespace+".staff s WHERE s.login=SESSION_USER::text;IF n<>1 THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;FOR r IN SELECT q.code FROM "+namespace+".resource q LOOP SELECT * INTO STRICT d FROM "+namespace+".disclosure_bound(r.code,subject_key);IF d.decision='deny' THEN CONTINUE;END IF;IF d.decision IS DISTINCT FROM 'permit' THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;SELECT entry->'disposition' INTO STRICT mask FROM jsonb_array_elements(d.disclosure) entry WHERE entry->'field'=jsonb_build_object('documentId','adoc','moduleId','m','elementId','Resource-secret');IF mask#>>'{transformed,transform}' IS DISTINCT FROM 'constant' OR mask#>>'{transformed,version}' IS DISTINCT FROM '0.1.0' OR mask#>>'{transformed,literal,string}' IS NULL THEN RAISE EXCEPTION 'security disclosure unavailable' USING ERRCODE='55000';END IF;RETURN QUERY SELECT r.code::text,mask#>>'{transformed,literal,string}',mask;END LOOP;END"
   self.admin.execute('CREATE FUNCTION '+namespace+'.masked_resources() RETURNS TABLE(code text,secret text,disposition jsonb) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ '+body+' $$;REVOKE ALL ON FUNCTION '+namespace+'.masked_resources() FROM PUBLIC;ALTER FUNCTION '+namespace+'.masked_resources() OWNER TO ontology_facts;REVOKE CREATE ON SCHEMA '+namespace+' FROM ontology_facts')
  self.admin.execute('CREATE POLICY complete_private_resource_disclosure ON relational_fixture.resource FOR SELECT TO ontology_facts USING(true)')
  for login in ['alice','bob','outsider']:
   self.admin.execute('REVOKE SELECT(props) ON truss.object FROM '+login+';REVOKE SELECT ON relational_fixture.resource FROM '+login+';GRANT SELECT(code) ON relational_fixture.resource TO '+login+';GRANT EXECUTE ON FUNCTION ontology_fixture.masked_resources(),relational_fixture.masked_resources() TO '+login)
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    for namespace in ['ontology_fixture','relational_fixture']:
     rows=reader.execute('SELECT code,secret,disposition FROM '+namespace+'.masked_resources() ORDER BY code').fetchall();self.assertEqual([row[0] for row in rows],expected[login]);self.assertTrue(all(row[1]=='MASKED' and row[2]['transformed']['literal']['string']=='MASKED' for row in rows));observations.append({'id':'native-constant-disclosure-'+namespace+'-'+login,'observed':[[row[0],row[1],row[2]] for row in rows]})
     raw_filter=reader.execute('SELECT count(*) FROM '+namespace+".masked_resources() WHERE secret='raw-RA'").fetchone()[0];self.assertEqual(raw_filter,0);observations.append({'id':'query-uses-disclosed-value-'+namespace+'-'+login,'observed':raw_filter})
    for statement in ['SELECT props FROM truss.object','SELECT secret FROM relational_fixture.resource']:
     with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute(statement)
    observations.append({'id':'raw-field-and-bag-denied-after-mask-activation-'+login,'observed':'42501'})
  original_graph=self.admin.execute('SELECT secret FROM ontology_fixture.resource WHERE code=%s',('RA',)).fetchone()[0];original_raw=self.admin.execute('SELECT secret FROM relational_fixture.resource WHERE code=%s',('RA',)).fetchone()[0];self.assertEqual((original_graph,original_raw),('raw-RA','raw-RA'));observations.append({'id':'read-transform-preserves-canonical-values','observed':[original_graph,original_raw]})
  # Withholding has metadata and no public secret column/value carrier.
  for namespace,disclosure in [('ontology_fixture',sql['graphWithheld']),('relational_fixture',sql['flatWithheld'])]:
   self.admin.execute('GRANT CREATE ON SCHEMA '+namespace+' TO ontology_facts;CREATE FUNCTION '+namespace+'.withheld_bound(text,text) RETURNS TABLE(decision text,disclosure jsonb) LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ '+disclosure['sql']+' $$;REVOKE ALL ON FUNCTION '+namespace+'.withheld_bound(text,text) FROM PUBLIC;ALTER FUNCTION '+namespace+'.withheld_bound(text,text) OWNER TO ontology_facts')
   body="DECLARE n bigint;subject_key text;r record;d record;state jsonb;BEGIN IF current_setting('transaction_isolation')<>'read committed' THEN RAISE EXCEPTION 'security authority profile unavailable' USING ERRCODE='0A000';END IF;SELECT count(*),min(s.code) INTO n,subject_key FROM "+namespace+".staff s WHERE s.login=SESSION_USER::text;IF n<>1 THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;FOR r IN SELECT q.code FROM "+namespace+".resource q LOOP SELECT * INTO STRICT d FROM "+namespace+".withheld_bound(r.code,subject_key);IF d.decision='deny' THEN CONTINUE;END IF;IF d.decision IS DISTINCT FROM 'permit' THEN RAISE EXCEPTION 'security facts unavailable' USING ERRCODE='55000';END IF;SELECT entry->'disposition' INTO STRICT state FROM jsonb_array_elements(d.disclosure) entry WHERE entry->'field'=jsonb_build_object('documentId','adoc','moduleId','m','elementId','Resource-secret');IF state IS DISTINCT FROM '\"withheld\"'::jsonb THEN RAISE EXCEPTION 'security disclosure unavailable' USING ERRCODE='55000';END IF;RETURN QUERY SELECT r.code::text,jsonb_build_object('field',jsonb_build_object('documentId','adoc','moduleId','m','elementId','Resource-secret'),'disposition',state);END LOOP;END"
   self.admin.execute('CREATE FUNCTION '+namespace+'.withheld_resources() RETURNS TABLE(code text,disposition jsonb) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ '+body+' $$;REVOKE ALL ON FUNCTION '+namespace+'.withheld_resources() FROM PUBLIC;ALTER FUNCTION '+namespace+'.withheld_resources() OWNER TO ontology_facts;REVOKE CREATE ON SCHEMA '+namespace+' FROM ontology_facts')
  for login in ['alice','bob','outsider']:
   self.admin.execute('REVOKE EXECUTE ON FUNCTION ontology_fixture.masked_resources(),relational_fixture.masked_resources() FROM '+login+';GRANT EXECUTE ON FUNCTION ontology_fixture.withheld_resources(),relational_fixture.withheld_resources() TO '+login)
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    for namespace in ['ontology_fixture','relational_fixture']:
     rows=reader.execute('SELECT code,disposition FROM '+namespace+'.withheld_resources() ORDER BY code').fetchall();self.assertEqual([row[0] for row in rows],expected[login]);self.assertTrue(all(row[1]=={'field':{'documentId':'adoc','moduleId':'m','elementId':'Resource-secret'},'disposition':'withheld'} for row in rows));observations.append({'id':'native-withheld-disposition-'+namespace+'-'+login,'observed':[list(row) for row in rows]})
     with self.assertRaises(psycopg.errors.UndefinedColumn):reader.execute('SELECT secret FROM '+namespace+'.withheld_resources()')
     observations.append({'id':'withheld-property-operator-has-no-value-carrier-'+namespace+'-'+login,'observed':'42703'})
     with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SELECT * FROM '+namespace+'.masked_resources()')
     observations.append({'id':'prior-transform-endpoint-revoked-'+namespace+'-'+login,'observed':'42501'})
  # Conflicting candidate never publishes over the protected withholding surface.
  for namespace,candidate in [('ontology_fixture',sql['graphConflict']),('relational_fixture',sql['flatConflict'])]:
   original=self.admin.execute("SELECT pg_get_functiondef(oid),proacl::text,proowner::text FROM pg_proc WHERE oid=%s::regprocedure",(namespace+'.withheld_resources()',)).fetchone()
   self.admin.execute('BEGIN')
   try:
    self.admin.execute('CREATE FUNCTION '+namespace+'.conflicting_candidate(text,text) RETURNS TABLE(decision text,disclosure jsonb) LANGUAGE SQL SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$ '+candidate['sql']+' $$;REVOKE ALL ON FUNCTION '+namespace+'.conflicting_candidate(text,text) FROM PUBLIC')
    candidate_result=self.admin.execute('SELECT * FROM '+namespace+'.conflicting_candidate(%s,%s)',('RA','staff-alice')).fetchone();self.assertEqual(candidate_result,('conflict',[]));observations.append({'id':'incompatible-native-masks-refuse-before-publication-'+namespace,'observed':list(candidate_result)})
   finally:self.admin.rollback()
   current=self.admin.execute("SELECT pg_get_functiondef(oid),proacl::text,proowner::text FROM pg_proc WHERE oid=%s::regprocedure",(namespace+'.withheld_resources()',)).fetchone();self.assertEqual(current,original);observations.append({'id':'conflict-refusal-preserves-prior-body-acl-owner-'+namespace,'observed':'exact-original'})
   exists=self.admin.execute('SELECT to_regprocedure(%s)',(namespace+'.conflicting_candidate(text,text)',)).fetchone()[0];self.assertIsNone(exists);observations.append({'id':'conflicting-candidate-rollback-leaves-no-routine-'+namespace,'observed':None})
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='alice'
   with psycopg.connect(**params,autocommit=True) as reader:
    rows=reader.execute('SELECT code,disposition FROM '+namespace+'.withheld_resources() ORDER BY code').fetchall();self.assertEqual([row[0] for row in rows],['RA','RAB']);self.assertTrue(all(row[1]['disposition']=='withheld' for row in rows));observations.append({'id':'prior-withholding-still-executes-after-conflict-refusal-'+namespace,'observed':[list(row) for row in rows]})
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']).write_text(json.dumps({'packet':packet,'sql':sql,'observations':observations,'publicCreatedIdentities':{alias:{'id':identity.id,'typeId':identity.type_id} for alias,identity in aliases.items()},'scope':'Actual public-created objects/edges, typed native joins to business keys and candidate typed Record/opaque Relationship membership lowering under ordinary native RLS. Private views are real graph projections, not seeded flat tables. Not complete source enrollment, held authority or released public API/security compiler admission.'},indent=2)+'\n')
if __name__=='__main__':
 import unittest;unittest.main()
