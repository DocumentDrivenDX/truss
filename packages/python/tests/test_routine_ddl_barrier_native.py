# SPDX-License-Identifier: MIT OR Apache-2.0
"""Selected native routine-DDL writer participation, never complete source admission."""
import gzip,json,hashlib,os,unittest
from pathlib import Path
from test_native_pg8000 import NativeBoundaryFixture
from pg8000.exceptions import DatabaseError
ROOT=Path(__file__).resolve().parents[3]
BARRIER=(ROOT/'packages/postgresql/native/source-epoch-routine-ddl-barrier.sql').read_text()
FUNCTION=BARRIER.split('REVOKE ALL',1)[0].replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION',1)
READ="SELECT * FROM truss.runtime_lock_fenced_fresh_source_epoch('fixture',:prior,'target')"
CHANGE='CREATE OR REPLACE FUNCTION truss.ddl_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 444 $$'
TAGS=['CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION','CREATE PROCEDURE','ALTER PROCEDURE','DROP PROCEDURE']

class RoutineDdlBarrierNativeTests(NativeBoundaryFixture,unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  super().setUpClass();cls.admin=cls.Connection(**cls.kwargs);cls.admin.run('CREATE DATABASE routine_ddl_barrier_component');cls.kwargs={**cls.kwargs,'database':'routine_ddl_barrier_component'}
  c=cls.Connection(**cls.kwargs)
  try:
   c.run((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text())
   for n in ('source-epoch-immutability','source-epoch-lock','source-epoch-issue','source-epoch-fresh-lock','source-epoch-read-fence','source-epoch-fenced-fresh-lock','operation-admission'):c.run((ROOT/f'packages/postgresql/native/{n}.sql').read_text())
   c.run("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0','fixture','fixture',sha256(decode('01','hex')),'fixture',sha256(decode('02','hex')),'fixture','truss',now(),now()::text)")
   cls.epoch=c.run("SELECT truss.runtime_issue_source_epoch('fixture',NULL,'target',decode('01','hex'),decode('02','hex'))")[0][0]
   c.run("CREATE FUNCTION truss.ddl_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 333 $$; CREATE PROCEDURE truss.ddl_procedure() LANGUAGE sql AS $$ SELECT 1 $$; CREATE SEQUENCE truss.ddl_first_effect")
   c.run("CREATE FUNCTION truss.ddl_effect_probe() RETURNS event_trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM nextval('truss.ddl_first_effect'); END $$; CREATE EVENT TRIGGER zz_ddl_effect_probe ON ddl_command_start WHEN TAG IN ('CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION','CREATE PROCEDURE','ALTER PROCEDURE','DROP PROCEDURE') EXECUTE FUNCTION truss.ddl_effect_probe(); ALTER EVENT TRIGGER zz_ddl_effect_probe ENABLE ALWAYS")
   c.run("CREATE ROLE ddl_barrier_ordinary LOGIN NOSUPERUSER NOBYPASSRLS; GRANT USAGE ON SCHEMA truss TO ddl_barrier_ordinary; CREATE ROLE ddl_barrier_definer NOLOGIN; GRANT CREATE ON SCHEMA truss TO ddl_barrier_definer; CREATE FUNCTION truss.ddl_definer_probe() RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$ BEGIN EXECUTE 'CREATE FUNCTION truss.definer_added() RETURNS integer LANGUAGE sql AS $b$ SELECT 1 $b$'; END $$; ALTER FUNCTION truss.ddl_definer_probe() OWNER TO ddl_barrier_definer")
   c.run(BARRIER)
  finally:c.close()
 @classmethod
 def tearDownClass(cls):
  cls.admin.run('DROP DATABASE routine_ddl_barrier_component');cls.admin.run('DROP ROLE ddl_barrier_ordinary; DROP ROLE ddl_barrier_definer');cls.admin.close();super().tearDownClass()
 def setUp(self):
  self.c=self.Connection(**self.kwargs);self.w=self.Connection(**self.kwargs);self.c.run('BEGIN');self.w.run("SET lock_timeout='150ms'; SET statement_timeout='3s'")
 def tearDown(self):
  self.c.run('ROLLBACK');self.w.run('ROLLBACK')
  try:
   self.w.run(FUNCTION)
   self.assertEqual(self.w.run("SELECT prosrc FROM pg_proc WHERE oid='truss.runtime_fence_routine_ddl_writer()'::regprocedure"),[[FUNCTION.split('AS $$',1)[1].split('$$;',1)[0]]])
   self.assertEqual(self.w.run("SELECT evtevent,evtenabled,evttags,evtfoid::regprocedure::text FROM pg_event_trigger WHERE evtname='truss_routine_ddl_writer_barrier'"),[['ddl_command_start','A',TAGS,'truss.runtime_fence_routine_ddl_writer()']])
   self.assertEqual(self.w.run('SELECT truss.ddl_subject()'),[[333]])
   self.w.run('BEGIN');self.w.run(READ,prior=self.epoch)
   self.refuse(self.w,CHANGE,'55000','selected epoch cut excludes routine DDL')
   self.w.run('ROLLBACK')
  finally:self.c.close();self.w.close()
 def acquire(self):
  native=self.c.run("SELECT pg_current_xact_id()::text,(SELECT oid::text FROM pg_database WHERE datname=current_database()),pg_backend_pid()::text,session_user::text,current_user::text")[0]
  result=self.c.run(READ,prior=self.epoch)
  self.assertEqual(result,[['fixture',self.epoch,'target','01','02',hashlib.sha256(b'\x02').hexdigest(),*native,'transaction_epoch_state_fence_only']])
  return result
 def shares(self,c):return c.run("SELECT count(*)::int FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)")[0][0]
 def modes(self,c):return c.run("SELECT count(*)::int FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='RowExclusiveLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)")[0][0]
 def called(self):return self.w.run('SELECT last_value,is_called FROM truss.ddl_first_effect')
 def refuse(self,c,sql,code,message=None,**args):
  c.run('SAVEPOINT refusal')
  try:
   with self.assertRaises(DatabaseError) as caught:c.run(sql,**args)
   self.assertEqual(caught.exception.args[0]['C'],code)
   if message:self.assertEqual(caught.exception.args[0]['M'],message)
  finally:c.run('ROLLBACK TO refusal');c.run('RELEASE refusal')
 def census(self,label):
  raw=self.c.run((ROOT/'packages/postgresql/native/security-query-source-census-pg16.sql').read_text())[0][0]
  self.assertIs(type(raw),str);data=raw.encode();self.assertLessEqual(len(data),16777216)
  path=os.environ.get('TRUSS_ROUTINE_DDL_EVIDENCE')
  if path:(Path(path)/(self._testMethodName+'-'+label+'.census.txt.gz')).write_bytes(gzip.compress(data,mtime=0))
  digest=hashlib.sha256(data).hexdigest();print(json.dumps({'test':self._testMethodName,'census':label,'sha256':digest,'octets':len(data)}));return digest
 def test_closed_hook_inventory(self):
  row=self.c.run("SELECT evtevent,evtenabled,evttags,evtfoid::regprocedure::text FROM pg_event_trigger WHERE evtname='truss_routine_ddl_writer_barrier'")[0]
  self.assertEqual(row,['ddl_command_start','A',TAGS,'truss.runtime_fence_routine_ddl_writer()'])
  self.assertEqual(self.c.run("SELECT prosecdef,provolatile,proconfig,EXISTS(SELECT 1 FROM aclexplode(coalesce(proacl,acldefault('f',proowner))) a WHERE a.grantee=0 AND a.privilege_type='EXECUTE') FROM pg_proc WHERE oid='truss.runtime_fence_routine_ddl_writer()'::regprocedure"),[[False,'v',['search_path=pg_catalog, pg_temp'],False]])
 def test_pending_writer_commit_and_abort(self):
  for end in ('ROLLBACK','COMMIT'):
   self.w.run('BEGIN');self.w.run(CHANGE);self.assertEqual(self.modes(self.w),2)
   self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[333]])
   self.refuse(self.c,READ,'55P03',prior=self.epoch)
   self.w.run(end);self.acquire();self.assertEqual(self.shares(self.c),2)
   self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[444 if end=='COMMIT' else 333]])
   self.assertEqual(self.c.run('SELECT source_epoch FROM truss.source_epoch_current'),[[self.epoch]])
   self.c.run('ROLLBACK; BEGIN')
  self.w.run('CREATE OR REPLACE FUNCTION truss.ddl_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 333 $$')
 def test_selected_ddl_changes_source_not_epoch(self):
  before=self.census('before');self.c.run('ROLLBACK');self.w.run(CHANGE);self.c.run('BEGIN');self.acquire()
  self.assertNotEqual(before,self.census('after'));self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[444]])
  self.assertEqual(self.c.run('SELECT source_epoch FROM truss.source_epoch_current'),[[self.epoch]])
  self.c.run('ROLLBACK');self.w.run('CREATE OR REPLACE FUNCTION truss.ddl_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 333 $$')
 def test_same_backend_six_tags_refuse_before_effect(self):
  self.acquire();before=self.called()
  commands=[CHANGE,'ALTER FUNCTION truss.ddl_subject() IMMUTABLE','DROP FUNCTION truss.ddl_subject()', 'CREATE PROCEDURE truss.new_procedure() LANGUAGE sql AS $$ SELECT 1 $$','ALTER PROCEDURE truss.ddl_procedure() SET search_path=pg_catalog','DROP PROCEDURE truss.ddl_procedure()']
  for sql in commands:self.refuse(self.c,sql,'55000','selected epoch cut excludes routine DDL')
  self.assertEqual(self.called(),before);self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[333]])
 def test_reader_first_external_writer_refuses_before_effect(self):
  self.acquire();before=self.called();self.w.run('BEGIN');self.refuse(self.w,CHANGE,'55P03');self.assertEqual(self.called(),before)
 def test_two_participating_writers_serialize_before_effect(self):
  self.c.run(CHANGE);self.assertEqual(self.modes(self.c),2);before=self.called();self.w.run('BEGIN');self.refuse(self.w,CHANGE,'55P03','could not obtain lock on row in relation "installation_marker"');self.assertEqual(self.called(),before)
 def test_original_privilege_and_definer_refusal(self):
  ordinary=self.Connection(**{**self.kwargs,'user':'ddl_barrier_ordinary'})
  try:
   ordinary.run('BEGIN');self.refuse(ordinary,CHANGE,'42501');self.refuse(ordinary,"SELECT truss.runtime_fence_routine_ddl_writer()",'42501');ordinary.run('ROLLBACK')
  finally:ordinary.close()
  self.refuse(self.c,'SELECT truss.ddl_definer_probe()','55000','original invoker routine DDL boundary required')
 def test_writer_lock_savepoint_lifetime(self):
  self.w.run('BEGIN; SAVEPOINT original');self.w.run(CHANGE);self.w.run('RELEASE original; SAVEPOINT later; ROLLBACK TO later');self.assertEqual(self.modes(self.w),2)
  self.refuse(self.c,READ,'55P03',prior=self.epoch);self.w.run('ROLLBACK');self.acquire()
 def test_omitted_table_modes_allow_pending_commit_source_change(self):
  marker=' LOCK TABLE truss.source_epoch_current, truss.source_epoch_registry IN ROW EXCLUSIVE MODE NOWAIT;';self.assertEqual(FUNCTION.count(marker),1)
  self.w.run(FUNCTION.replace(marker,' -- Deliberate omitted writer table modes.'))
  self.w.run('BEGIN');self.w.run(CHANGE);self.assertEqual(self.modes(self.w),0);self.acquire();before=self.census('pending')
  self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[333]])
  self.w.run('COMMIT');self.assertEqual(self.shares(self.c),2);self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[444]])
  self.assertNotEqual(before,self.census('committed'));self.assertEqual(self.c.run('SELECT source_epoch FROM truss.source_epoch_current'),[[self.epoch]])
  self.c.run('ROLLBACK');self.w.run('CREATE OR REPLACE FUNCTION truss.ddl_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 333 $$')
 def test_omitted_own_share_guard_allows_same_backend_source_change(self):
  marker=' IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l';self.assertEqual(FUNCTION.count(marker),1)
  self.w.run(FUNCTION.replace(marker,' IF FALSE AND EXISTS(SELECT 1 FROM pg_catalog.pg_locks l'))
  self.acquire();before=self.called();self.c.run(CHANGE);self.assertEqual(self.shares(self.c),2);self.assertNotEqual(self.called(),before)
  self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[444]]);self.assertEqual(self.c.run('SELECT source_epoch FROM truss.source_epoch_current'),[[self.epoch]])
 def test_shared_role_change_is_explicitly_outside_barrier(self):
  self.acquire();before=self.census('before-role');self.w.run('ALTER ROLE ddl_barrier_ordinary BYPASSRLS')
  self.assertNotEqual(before,self.census('after-role'));self.assertEqual(self.shares(self.c),2)
  self.assertEqual(self.c.run('SELECT source_epoch FROM truss.source_epoch_current'),[[self.epoch]])
  self.w.run('ALTER ROLE ddl_barrier_ordinary NOBYPASSRLS')

 def test_old_snapshot_refuses_before_acquisition(self):
  for isolation in ('REPEATABLE READ','SERIALIZABLE'):
   self.c.run('ROLLBACK; BEGIN ISOLATION LEVEL '+isolation);self.c.run('SELECT source_epoch FROM truss.source_epoch_current')
   self.refuse(self.c,READ,'55000','fenced epoch requires native read committed read write',prior=self.epoch)
   self.assertEqual(self.shares(self.c),0)
 def test_replica_mode_still_fences_same_backend(self):
  self.c.run('SET LOCAL session_replication_role=replica');self.acquire();before=self.called()
  self.refuse(self.c,CHANGE,'55000','selected epoch cut excludes routine DDL');self.assertEqual(self.called(),before)
 def test_privileged_hook_disable_is_explicitly_outside_barrier(self):
  self.w.run('ALTER EVENT TRIGGER truss_routine_ddl_writer_barrier DISABLE')
  try:
   self.acquire();self.w.run(CHANGE);self.assertEqual(self.shares(self.c),2)
   self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[444]])
   self.assertEqual(self.c.run('SELECT source_epoch FROM truss.source_epoch_current'),[[self.epoch]])
  finally:
   self.c.run('ROLLBACK');self.w.run('ALTER EVENT TRIGGER truss_routine_ddl_writer_barrier ENABLE ALWAYS')
   self.w.run('CREATE OR REPLACE FUNCTION truss.ddl_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 333 $$')

 def test_omitted_marker_lock_allows_distinct_concurrent_ddl_effects(self):
  marker=' PERFORM 1 FROM truss.installation_marker m WHERE m.singleton_id=1 FOR UPDATE NOWAIT;'
  self.assertEqual(FUNCTION.count(marker),1);self.w.run(FUNCTION.replace(marker,' PERFORM 1; -- Deliberate omitted marker row exclusion.'))
  self.c.run(CHANGE);self.assertEqual(self.modes(self.c),2);before=self.called();self.w.run('BEGIN')
  self.w.run('CREATE FUNCTION truss.second_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$')
  self.assertEqual(self.modes(self.w),2);self.assertNotEqual(self.called(),before)
  self.assertEqual(self.w.run('SELECT truss.second_subject()'),[[1]])

 def admit(self):
  native=self.c.run('SELECT pg_current_xact_id()::text')[0][0]
  result=self.c.run("SELECT * FROM truss.runtime_admit_operation('mutation',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'))")
  self.assertEqual(result[0][:2],[native,'0'])
  context=json.loads(bytes.fromhex(result[0][2]));self.assertEqual(context['xid'],native)
  self.assertEqual(self.c.run('SELECT original_writer_xid::text,operation_ordinal::text,phase FROM truss.row_home_operation'),[[native,'0','admitted']])
  return native
 def test_original_operation_refuses_ddl_without_epoch_shares(self):
  self.admit();self.assertEqual(self.shares(self.c),0);self.assertEqual(self.modes(self.c),0);before=self.called()
  self.refuse(self.c,CHANGE,'55000','routine DDL cannot follow an original operation')
  self.assertEqual(self.modes(self.c),0);self.assertEqual(self.called(),before)
  self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[333]])
 def test_rollback_across_original_admission_releases_ddl_refusal(self):
  self.c.run('SAVEPOINT before_admission');native=self.admit();self.c.run('SAVEPOINT later; ROLLBACK TO later; RELEASE later')
  self.refuse(self.c,CHANGE,'55000','routine DDL cannot follow an original operation')
  self.c.run('ROLLBACK TO before_admission; RELEASE before_admission')
  self.assertEqual(self.c.run('SELECT pg_current_xact_id()::text'),[[native]])
  self.assertEqual(self.c.run('SELECT count(*)::int FROM truss.row_home_operation'),[[0]])
  self.c.run(CHANGE);self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[444]])
 def test_omitted_operation_guard_allows_source_change_behind_admission(self):
  marker=' IF EXISTS(SELECT 1 FROM truss.row_home_operation o';self.assertEqual(FUNCTION.count(marker),1)
  self.w.run(FUNCTION.replace(marker,' IF FALSE AND EXISTS(SELECT 1 FROM truss.row_home_operation o'))
  self.admit();before=self.called();self.assertEqual(self.shares(self.c),0);self.c.run(CHANGE)
  self.assertNotEqual(self.called(),before);self.assertEqual(self.c.run('SELECT truss.ddl_subject()'),[[444]])
  self.assertEqual(self.c.run('SELECT phase FROM truss.row_home_operation'),[['admitted']])
