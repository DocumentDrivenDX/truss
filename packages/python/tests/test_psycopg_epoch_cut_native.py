# SPDX-License-Identifier: MIT OR Apache-2.0
"""Supported psycopg epoch-cut composition; administrative fixture, no backend admission."""
from pathlib import Path
import psycopg
from truss.execution import Ok, Error
from truss._psycopg_epoch_cut import _EpochComparison, _run_fenced_epoch_operation
import test_psycopg_host_native as host_tests
import unittest
import os,json,subprocess

ROOT=Path(__file__).resolve().parents[3]

class PsycopgEpochCutNativeTests(unittest.TestCase):
    run_pg=classmethod(host_tests.PsycopgHostNativeTests.run_pg.__func__)
    @classmethod
    def setUpClass(cls):
        host_tests.PsycopgHostNativeTests.setUpClass.__func__(cls)
        with psycopg.connect(host=str(cls.socket),user='postgres',dbname=cls.database,autocommit=True) as c:
            c.execute((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text())
            for n in ('source-epoch-immutability','source-epoch-lock','source-epoch-issue','source-epoch-fresh-lock','source-epoch-read-fence','source-epoch-fenced-fresh-lock'):
                c.execute((ROOT/f'packages/postgresql/native/{n}.sql').read_text())
            c.execute("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0','fixture','fixture',sha256(decode('01','hex')),'fixture',sha256(decode('02','hex')),'fixture','truss',now(),now()::text)")
            cls.epoch=c.execute("SELECT truss.runtime_issue_source_epoch('fixture',NULL,'target',decode('01','hex'),decode('02','hex'))").fetchone()[0]
            c.execute('CREATE FUNCTION truss.psy_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 333 $$')
            c.execute((ROOT/'packages/postgresql/native/source-epoch-routine-ddl-barrier.sql').read_text())
    @classmethod
    def tearDownClass(cls):
        if cls.worker_fixture is not None:
            cls.worker_fixture.cleanup();cls.worker_fixture=None
            return
        try:
            stopped=subprocess.run([str(cls.pgbin/'pg_ctl'),'-D',str(cls.data),'-w','-m','immediate','stop'],capture_output=True,text=True,timeout=60)
            status=subprocess.run([str(cls.pgbin/'pg_ctl'),'-D',str(cls.data),'status'],capture_output=True,text=True,timeout=60)
            receipt={'stopExitCode':stopped.returncode,'statusExitCode':status.returncode,'socketAbsent':not (cls.socket/'.s.PGSQL.5432').exists()}
            target=os.environ.get('TRUSS_PSYCOPG_EPOCH_EVIDENCE')
            if target:
                (Path(target)/'cleanup.json').write_text(json.dumps(receipt,indent=2)+'\n')
                (Path(target)/('cleanup-'+cls.__name__+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
            if receipt!={'stopExitCode':0,'statusExitCode':3,'socketAbsent':True}:raise RuntimeError('Owned fixture cleanup failed')
        finally:cls.directory.cleanup()
    def setUp(self):
        self.selected_profile=host_tests.PsycopgProfile()
        host_tests.PsycopgHostNativeTests.setUp(self)
    tearDown=host_tests.PsycopgHostNativeTests.tearDown
    begin=host_tests.PsycopgHostNativeTests.begin
    def comparison(self):return _EpochComparison('fixture',self.epoch,'target',b'\x01',b'\x02')
    def shares(self):return self.connection.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)").fetchone()[0]
    def run_cut(self,t,callback,comparison=None):return _run_fenced_epoch_operation(self.host,t,comparison or self.comparison(),callback)
    def test_census_comparison_precedes_callback_under_native_epoch_fence(self):
        from truss._psycopg_source_census import observe_source_census_in_transaction
        from truss._psycopg_census_cut import _run_census_compared_epoch_operation
        t=self.begin();original=observe_source_census_in_transaction(self.host,t)
        self.assertIsInstance(original,Ok,str(self.host._custody.last_attempt.error));calls=[]
        def callback(cursor):
            cursor.execute("SELECT count(*)::text FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)")
            self.assertEqual(cursor.fetchone(),('2',));calls.append('original callback')
            cursor.execute('SELECT truss.psy_subject()');return cursor.fetchone()[0]
        result=_run_census_compared_epoch_operation(self.host,t,self.comparison(),original.value.original_image,callback)
        self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(result.value,333);self.assertEqual(calls,['original callback'])

    def test_census_drift_refuses_before_callback_and_preserves_caller_work(self):
        from truss._psycopg_source_census import observe_source_census_in_transaction
        from truss._psycopg_census_cut import _run_census_compared_epoch_operation
        t=self.begin();self.connection.execute("CREATE TEMP TABLE census_prior_work(value text);INSERT INTO census_prior_work VALUES('kept')")
        original=observe_source_census_in_transaction(self.host,t);self.assertIsInstance(original,Ok)
        self.connection.execute("CREATE OR REPLACE FUNCTION truss.psy_subject() RETURNS integer LANGUAGE sql AS 'SELECT 334'")
        calls=[]
        result=_run_census_compared_epoch_operation(self.host,t,self.comparison(),original.value.original_image,lambda cursor:calls.append('must not execute'))
        self.assertIsInstance(result,Error);self.assertEqual(calls,[]);self.assertEqual(self.shares(),0)
        self.assertEqual(self.connection.execute('TABLE census_prior_work').fetchall(),[('kept',)])
        self.assertEqual(self.connection.execute('SELECT truss.psy_subject()').fetchone(),(334,))

    def test_census_compared_callback_cannot_escape_as_deferred_work(self):
        from truss._psycopg_source_census import observe_source_census_in_transaction
        from truss._psycopg_census_cut import _run_census_compared_epoch_operation
        t=self.begin();self.connection.execute("CREATE TEMP TABLE census_deferred_work(value text);INSERT INTO census_deferred_work VALUES('kept')")
        original=observe_source_census_in_transaction(self.host,t);self.assertIsInstance(original,Ok)
        bodies=[];deferred=[]
        def callback(cursor):
            def cold():
                bodies.append('must not run');yield cursor.execute('SELECT truss.psy_subject()')
            value=cold();deferred.append(value);return value
        result=_run_census_compared_epoch_operation(self.host,t,self.comparison(),original.value.original_image,callback)
        self.assertIsInstance(result,Error);self.assertEqual(bodies,[]);self.assertEqual(len(deferred),1);self.assertIsNone(deferred[0].gi_frame)
        self.assertEqual(self.shares(),0);self.assertEqual(self.connection.execute('TABLE census_deferred_work').fetchall(),[('kept',)])

    def test_callback_has_native_cut_and_external_writer_refuses(self):
        t=self.begin()
        def callback(cursor):
            cursor.execute("SELECT count(*)::text FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)")
            self.assertEqual(cursor.fetchone(),('2',))
            with psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database,autocommit=True) as writer:
                with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute('CREATE OR REPLACE FUNCTION truss.psy_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 444 $$')
            cursor.execute('SELECT truss.psy_subject()::text');return cursor.fetchone()[0]
        self.assertEqual(self.run_cut(t,callback),Ok('333'));self.assertEqual(self.shares(),2)
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(),('3s',))
    def test_same_writer_ddl_refuses_and_cut_is_rolled_back(self):
        t=self.begin()
        result=self.run_cut(t,lambda c:c.execute('CREATE OR REPLACE FUNCTION truss.psy_subject() RETURNS integer LANGUAGE sql AS $$ SELECT 444 $$'))
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000');self.assertEqual(self.shares(),0)
        self.assertEqual(self.connection.execute('SELECT truss.psy_subject()').fetchone(),(333,))
    def test_foreign_epoch_oid_refuses_before_custom_row_loader(self):
        from psycopg.adapt import Loader
        loaded=[];called=[]
        class ForeignNameLoader(Loader):
            def load(self,data):loaded.append(True);return 'fixture'
        self.connection.adapters.register_loader(19,ForeignNameLoader)
        t=self.begin()
        self.connection.execute('DROP FUNCTION truss.runtime_lock_fenced_fresh_source_epoch(text,text,text)')
        self.connection.execute("""CREATE FUNCTION truss.runtime_lock_fenced_fresh_source_epoch(text,text,text)
            RETURNS TABLE(installation_id name,source_epoch text,target_incarnation text,profile_hex text,
            evidence_hex text,evidence_sha256 text,actual_writer_xid text,actual_database_oid text,
            actual_backend_pid text,original_actor text,effective_actor text,cut_scope text)
            LANGUAGE sql AS $$ SELECT 'fixture'::name,'foreign'::text,'target'::text,'01'::text,'02'::text,
            'foreign'::text,'foreign'::text,'foreign'::text,'foreign'::text,'foreign'::text,'foreign'::text,
            'transaction_epoch_state_fence_only'::text $$""")
        result=self.run_cut(t,lambda c:called.append(True))
        self.assertIsInstance(result,Error);self.assertEqual(loaded,[]);self.assertEqual(called,[])

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
    def test_unqualified_host_profile_refuses_before_native_work(self):
        from unittest.mock import patch
        from truss.psycopg_host import PsycopgHost,PsycopgProfile
        t=self.begin();called=[]
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))
        with patch.object(PsycopgHost,'profile',property(lambda host:PsycopgProfile(server=160015))):
            with self.assertRaises(ValueError):self.run_cut(t,lambda c:called.append(True))
        self.assertEqual(called,[])
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))
