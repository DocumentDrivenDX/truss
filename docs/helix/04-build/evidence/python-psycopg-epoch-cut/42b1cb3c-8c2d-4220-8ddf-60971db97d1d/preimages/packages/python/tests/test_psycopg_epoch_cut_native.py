"""Supported psycopg epoch-cut composition; administrative fixture, no backend admission."""
from pathlib import Path
import psycopg
from truss.execution import Ok, Error
from truss._psycopg_epoch_cut import _EpochComparison, _run_fenced_epoch_operation
from test_psycopg_host_native import PsycopgHostNativeTests
import unittest
import os,json,subprocess

ROOT=Path(__file__).resolve().parents[3]

class PsycopgEpochCutNativeTests(unittest.TestCase):
    run_pg=classmethod(PsycopgHostNativeTests.run_pg.__func__)
    @classmethod
    def setUpClass(cls):
        PsycopgHostNativeTests.setUpClass.__func__(cls)
        with psycopg.connect(host=str(cls.socket),user='postgres',dbname='postgres',autocommit=True) as c:
            c.execute((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text())
            for n in ('source-epoch-immutability','source-epoch-lock','source-epoch-issue','source-epoch-fresh-lock','source-epoch-read-fence','source-epoch-fenced-fresh-lock'):
                c.execute((ROOT/f'packages/postgresql/native/{n}.sql').read_text())
            c.execute("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0','fixture','fixture',sha256(decode('01','hex')),'fixture',sha256(decode('02','hex')),'fixture','truss',now(),now()::text)")
            cls.epoch=c.execute("SELECT truss.runtime_issue_source_epoch('fixture',NULL,'target',decode('01','hex'),decode('02','hex'))").fetchone()[0]
            c.execute('CREATE FUNCTION truss.psy_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 333 $$')
            c.execute((ROOT/'packages/postgresql/native/source-epoch-routine-ddl-barrier.sql').read_text())
    @classmethod
    def tearDownClass(cls):
        try:
            stopped=subprocess.run([str(cls.pgbin/'pg_ctl'),'-D',str(cls.data),'-w','-m','immediate','stop'],capture_output=True,text=True,timeout=60)
            status=subprocess.run([str(cls.pgbin/'pg_ctl'),'-D',str(cls.data),'status'],capture_output=True,text=True,timeout=60)
            receipt={'stopExitCode':stopped.returncode,'statusExitCode':status.returncode,'socketAbsent':not (cls.socket/'.s.PGSQL.5432').exists()}
            target=os.environ.get('TRUSS_PSYCOPG_EPOCH_EVIDENCE')
            if target:(Path(target)/'cleanup.json').write_text(json.dumps(receipt,indent=2)+'\n')
            if receipt!={'stopExitCode':0,'statusExitCode':3,'socketAbsent':True}:raise RuntimeError('Owned fixture cleanup failed')
        finally:cls.directory.cleanup()
    setUp=PsycopgHostNativeTests.setUp
    tearDown=PsycopgHostNativeTests.tearDown
    begin=PsycopgHostNativeTests.begin
    def comparison(self):return _EpochComparison('fixture',self.epoch,'target',b'\x01',b'\x02')
    def shares(self):return self.connection.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)").fetchone()[0]
    def run_cut(self,t,callback,comparison=None):return _run_fenced_epoch_operation(self.host,t,comparison or self.comparison(),callback)
    def test_callback_has_native_cut_and_external_writer_refuses(self):
        t=self.begin()
        def callback(cursor):
            cursor.execute("SELECT count(*)::text FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)")
            self.assertEqual(cursor.fetchone(),('2',))
            with psycopg.connect(host=str(self.socket),user='postgres',dbname='postgres',autocommit=True) as writer:
                with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute('CREATE OR REPLACE FUNCTION truss.psy_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 444 $$')
            cursor.execute('SELECT truss.psy_subject()::text');return cursor.fetchone()[0]
        self.assertEqual(self.run_cut(t,callback),Ok('333'));self.assertEqual(self.shares(),2)
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(),('3s',))
    def test_same_writer_ddl_refuses_and_cut_is_rolled_back(self):
        t=self.begin()
        result=self.run_cut(t,lambda c:c.execute('CREATE OR REPLACE FUNCTION truss.psy_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 444 $$'))
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000');self.assertEqual(self.shares(),0)
        self.assertEqual(self.connection.execute('SELECT truss.psy_subject()').fetchone(),(333,))
    def test_wrong_profile_refuses_before_callback(self):
        t=self.begin();called=[]
        result=self.run_cut(t,lambda c:called.append(True),_EpochComparison('fixture',self.epoch,'target',b'wrong',b'\x02'))
        self.assertIsInstance(result,Error);self.assertEqual(called,[]);self.assertEqual(self.shares(),0)
    def test_callback_error_preserves_prior_host_work(self):
        t=self.begin();self.connection.execute("CREATE TEMP TABLE host_work(v text); INSERT INTO host_work VALUES('keep')")
        result=self.run_cut(t,lambda c:c.execute('SELECT 1/0'))
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'22012');self.assertEqual(self.shares(),0)
        self.assertEqual(self.connection.execute('TABLE host_work').fetchall(),[('keep',)])
    def test_outer_rollback_releases_cut_and_new_call_reacquires(self):
        t=self.begin();self.connection.execute('SAVEPOINT outer_scope')
        self.assertEqual(self.run_cut(t,lambda c:'first'),Ok('first'));self.assertEqual(self.shares(),2)
        xid=self.connection.execute('SELECT pg_current_xact_id()::text').fetchone()
        self.connection.execute('ROLLBACK TO outer_scope');self.assertEqual(self.shares(),0)
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id()::text').fetchone(),xid)
        self.assertEqual(self.run_cut(t,lambda c:'second'),Ok('second'));self.assertEqual(self.shares(),2)
    def test_readonly_refuses_before_callback(self):
        t=self.begin(readonly=True);called=[];result=self.run_cut(t,lambda c:called.append(True))
        self.assertIsInstance(result,Error);self.assertEqual(called,[]);self.assertEqual(self.shares(),0)
    def test_host_custom_string_codecs_do_not_substitute_comparison(self):
        from psycopg.adapt import Dumper,Loader
        class WrongString(Dumper):
            oid=25
            def dump(self,value):return b'wrong'
        class WrongText(Loader):
            def load(self,data):return 'wrong'
        self.connection.adapters.register_dumper(str,WrongString)
        self.connection.adapters.register_loader(25,WrongText)
        t=self.begin();self.assertEqual(self.run_cut(t,lambda c:'original'),Ok('original'));self.assertEqual(self.shares(),2)
    def test_recipe_snapshot_survives_later_carrier_mutation(self):
        from unittest.mock import patch
        from truss.psycopg_host import PsycopgHost
        t=self.begin();comparison=self.comparison();original=PsycopgHost._run_operation
        def mutate(host,transaction,callback):
            object.__setattr__(comparison,'epoch','substituted')
            object.__setattr__(comparison,'profile',b'wrong')
            return original(host,transaction,callback)
        with patch.object(PsycopgHost,'_run_operation',mutate):
            self.assertEqual(self.run_cut(t,lambda c:'original',comparison),Ok('original'))
        self.assertEqual(self.shares(),2);self.assertEqual(comparison.epoch,'substituted')
