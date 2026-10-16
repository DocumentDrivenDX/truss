"""Original native epoch-state fence; no complete source/authority admission."""
import unittest,threading,time
from pathlib import Path
from test_native_pg8000 import NativeBoundaryFixture
ROOT=Path(__file__).resolve().parents[3]
ISSUE="SELECT truss.runtime_issue_source_epoch('fixture',:prior,'target',decode('01','hex'),decode('02','hex'))"
READ="SELECT * FROM truss.runtime_lock_fenced_fresh_source_epoch('fixture',:prior,'target')"

class EpochStateFenceNativeTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass();cls.admin=cls.Connection(**cls.kwargs)
        cls.admin.run('CREATE DATABASE epoch_state_fence_component')
        cls.kwargs={**cls.kwargs,'database':'epoch_state_fence_component'}
        c=cls.Connection(**cls.kwargs)
        try:
            c.run((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text())
            for name in ('source-epoch-immutability','source-epoch-lock','source-epoch-issue',
                         'source-epoch-fresh-lock','source-epoch-read-fence','source-epoch-fenced-fresh-lock'):
                c.run((ROOT/f'packages/postgresql/native/{name}.sql').read_text())
            c.run("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0','fixture','fixture',sha256(decode('01','hex')),'fixture',sha256(decode('02','hex')),'fixture','truss',now(),now()::text)")
            cls.initial=c.run(ISSUE,prior=None)[0][0]
        finally:c.close()
    @classmethod
    def tearDownClass(cls):
        cls.admin.run('DROP DATABASE epoch_state_fence_component');cls.admin.close();super().tearDownClass()
    def setUp(self):
        self.c=self.Connection(**self.kwargs);self.w=self.Connection(**self.kwargs)
        self.c.run('BEGIN');self.w.run("SET lock_timeout='150ms'")
        self.registry_count=self.c.run('SELECT count(*) FROM truss.source_epoch_registry')
    def tearDown(self):
        self.c.run('ROLLBACK');self.w.run('ROLLBACK');self.c.close();self.w.close()
    def acquire(self,prior=None):return self.c.run(READ,prior=prior or self.initial)
    def refusal(self,sql,code='55000',message='selected epoch cut excludes same-backend writes',**params):
        from pg8000.exceptions import DatabaseError
        self.c.run('SAVEPOINT refusal')
        try:
            with self.assertRaises(DatabaseError) as caught:self.c.run(sql,**params)
            self.assertEqual(caught.exception.args[0]['C'],code)
            if message:self.assertEqual(caught.exception.args[0]['M'],message)
        finally:self.c.run('ROLLBACK TO refusal');self.c.run('RELEASE refusal')
    def test_original_tuple_and_both_actual_locks(self):
        result=self.acquire()[0]
        self.assertEqual(result[:5],['fixture',self.initial,'target','01','02'])
        self.assertEqual(result[-1],'transaction_epoch_state_fence_only')
        self.assertEqual(self.c.run("SELECT c.relname FROM pg_locks l JOIN pg_class c ON c.oid=l.relation WHERE l.pid=pg_backend_pid() AND l.mode='ShareLock' AND l.granted AND c.relname IN ('source_epoch_current','source_epoch_registry') ORDER BY c.relname"),[['source_epoch_current'],['source_epoch_registry']])
    def test_issuer_refuses_before_registry_first_effect(self):
        self.c.run("CREATE TEMP SEQUENCE epoch_first_effect; CREATE FUNCTION truss.epoch_first_effect() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM nextval('pg_temp.epoch_first_effect'); RETURN NEW; END $$; CREATE TRIGGER epoch_first_effect BEFORE INSERT ON truss.source_epoch_registry FOR EACH ROW EXECUTE FUNCTION truss.epoch_first_effect()")
        # A later trigger cannot substitute for the entry guard: without that
        # guard, this independent marker lock would produce 55P03 first.
        self.w.run('BEGIN');self.w.run('SELECT installation_id FROM truss.installation_marker FOR UPDATE')
        self.c.run("SET LOCAL lock_timeout='150ms'")
        self.acquire();self.refusal(ISSUE,prior=self.initial)
        self.assertEqual(self.c.run('SELECT is_called FROM pg_temp.epoch_first_effect'),[[False]])
        self.assertEqual(self.c.run('SELECT source_epoch FROM truss.source_epoch_current'),[[self.initial]])
        self.assertEqual(self.c.run('SELECT count(*) FROM truss.source_epoch_registry'),self.registry_count)
    def test_all_statement_events_on_both_tables_are_fenced(self):
        self.acquire()
        for table in ('source_epoch_current','source_epoch_registry'):
            columns='installation_id,source_epoch,target_incarnation,predecessor_epoch,transition_reason,profile_bytes,evidence_bytes'
            insertion=f'INSERT INTO truss.{table}({columns}) SELECT {columns} FROM truss.{table} WHERE false' if table=='source_epoch_registry' else f'INSERT INTO truss.{table} SELECT * FROM truss.{table} WHERE false'
            for sql in (insertion,
                        f'UPDATE truss.{table} SET source_epoch=source_epoch WHERE false',
                        f'DELETE FROM truss.{table} WHERE false',f'TRUNCATE truss.{table} CASCADE'):
                with self.subTest(sql=sql):self.refusal(sql)
    def test_writer_first_then_reader_rejects_all_later_writes(self):
        successor=self.c.run(ISSUE,prior=self.initial)[0][0]
        self.acquire(successor);self.refusal(ISSUE,prior=successor)
        self.refusal('UPDATE truss.source_epoch_current SET source_epoch=source_epoch')
        self.assertEqual(self.c.run('SELECT source_epoch FROM truss.source_epoch_current'),[[successor]])
    def test_pending_writer_commit_and_abort_require_new_reader_attempt(self):
        from pg8000.exceptions import DatabaseError
        for end in ('ROLLBACK','COMMIT'):
            with self.subTest(end=end):
                self.w.run('BEGIN');new=self.w.run(ISSUE,prior=self.initial)[0][0]
                self.assertEqual(self.w.run("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass) AND mode='RowExclusiveLock' AND granted"),[[2]])
                self.refusal(READ,code='55P03',message=None,prior=self.initial)
                self.assertEqual(self.c.run("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass) AND mode='ShareLock' AND granted"),[[0]])
                self.w.run(end)
                if end=='COMMIT':
                    self.refusal(READ,message='current source epoch correspondence required',prior=self.initial)
                    self.assertEqual(self.acquire(new)[0][1],new)
                    # Keep the actual committed successor, not an administrative
                    # pointer restore masquerading as original epoch issuance.
                    self.c.run('ROLLBACK')
                    type(self).initial=new
                    self.c.run('BEGIN')
                else:self.assertEqual(self.acquire()[0][1],self.initial);self.c.run('ROLLBACK');self.c.run('BEGIN')
    def test_reader_first_excludes_external_issuer_until_release(self):
        from pg8000.exceptions import DatabaseError
        self.acquire()
        with self.assertRaises(DatabaseError) as caught:self.w.run(ISSUE,prior=self.initial)
        self.assertEqual(caught.exception.args[0]['C'],'55P03')
        self.c.run('ROLLBACK');self.w.run('BEGIN')
        self.assertNotEqual(self.w.run(ISSUE,prior=self.initial)[0][0],self.initial)
        self.w.run('ROLLBACK');self.c.run('BEGIN')
    def test_writer_modes_precede_marker_row_wait(self):
        r=self.Connection(**self.kwargs);thread=None;result=[];errors=[]
        try:
            self.c.run('SELECT installation_id FROM truss.installation_marker FOR UPDATE')
            marker_pid=self.c.run('SELECT pg_backend_pid()')[0][0]
            self.w.run("SET lock_timeout='3s'; BEGIN")
            writer_pid=self.w.run('SELECT pg_backend_pid()')[0][0]
            def issue():
                try:result.extend(self.w.run(ISSUE,prior=self.initial))
                except Exception as error:errors.append(str(error))
            thread=threading.Thread(target=issue);thread.start();deadline=time.monotonic()+2
            while not r.run('SELECT :marker=ANY(pg_blocking_pids(:writer))',marker=marker_pid,writer=writer_pid)[0][0]:
                if time.monotonic()>deadline:raise TimeoutError('Original marker row blocker not observed')
                time.sleep(.01)
            locks=r.run("SELECT count(*) FROM pg_locks WHERE pid=:writer AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass) AND mode='RowExclusiveLock' AND granted",writer=writer_pid)[0][0]
            r.run('BEGIN');r.run('SAVEPOINT reader_attempt')
            try:
                r.run(READ,prior=self.initial);code='success'
            except Exception as error:
                code=error.args[0].get('C') if error.args and type(error.args[0]) is dict else 'unknown'
            finally:r.run('ROLLBACK TO reader_attempt');r.run('RELEASE reader_attempt')
            r.run('ROLLBACK');self.c.run('ROLLBACK');thread.join(5)
            self.assertFalse(thread.is_alive());self.assertEqual(errors,[]);self.assertEqual(len(result),1)
            self.assertEqual((locks,code),(2,'55P03'))
        finally:
            r.run('ROLLBACK');r.close();self.c.run('ROLLBACK')
            if thread is not None:thread.join(5)
            if thread is not None and thread.is_alive():raise RuntimeError('Original writer thread did not terminate')
            self.w.run('ROLLBACK');self.c.run('BEGIN')
    def test_acquisition_rollback_release_and_later_rollback(self):
        xid=self.c.run('SELECT pg_current_xact_id()::text')
        self.c.run('SAVEPOINT acquisition');self.acquire();self.c.run('ROLLBACK TO acquisition');self.c.run('RELEASE acquisition')
        self.assertEqual(self.c.run('SELECT pg_current_xact_id()::text'),xid)
        successor=self.c.run(ISSUE,prior=self.initial)[0][0]
        self.c.run('SAVEPOINT acquisition');self.acquire(successor);self.c.run('RELEASE acquisition')
        self.c.run('SAVEPOINT later');self.c.run('ROLLBACK TO later');self.c.run('RELEASE later')
        self.refusal(ISSUE,prior=successor)
    def test_replica_and_ungranted_ordinary_role(self):
        self.c.run('CREATE ROLE epoch_fence_ordinary NOLOGIN; GRANT USAGE ON SCHEMA truss TO epoch_fence_ordinary')
        self.c.run('SET LOCAL ROLE epoch_fence_ordinary')
        self.refusal(READ,code='42501',message=None,prior=self.initial)
        self.c.run('RESET ROLE')
        self.c.run('GRANT SELECT ON truss.source_epoch_current,truss.source_epoch_registry TO epoch_fence_ordinary; GRANT EXECUTE ON FUNCTION truss.runtime_lock_fenced_fresh_source_epoch(text,text,text) TO epoch_fence_ordinary')
        self.c.run('SET LOCAL ROLE epoch_fence_ordinary')
        self.assertEqual(self.c.run('SELECT source_epoch FROM truss.source_epoch_current'),[[self.initial]])
        self.refusal(READ,code='42501',message='permission denied for table source_epoch_current',prior=self.initial)
        self.refusal('UPDATE truss.source_epoch_current SET source_epoch=source_epoch',code='42501',message=None)
        self.c.run('RESET ROLE');self.acquire();self.c.run('SET LOCAL session_replication_role=replica')
        self.refusal('DELETE FROM truss.source_epoch_current WHERE false')
    def test_stronger_isolation_and_read_only_refuse(self):
        self.c.run('ROLLBACK')
        for level in ('REPEATABLE READ','SERIALIZABLE','READ COMMITTED READ ONLY'):
            self.c.run('BEGIN ISOLATION LEVEL '+level)
            self.refusal(READ,message='fenced epoch requires native read committed read write',prior=self.initial)
            self.c.run('ROLLBACK')
        self.c.run('BEGIN')
