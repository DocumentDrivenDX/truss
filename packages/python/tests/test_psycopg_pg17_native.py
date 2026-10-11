"""Explicit PG17.11 tuple; no installer or ordinary authority qualification."""
from truss import PsycopgProfile,adopt_psycopg_host,Ok,Error
from test_psycopg_host_native import PsycopgHostNativeTests
from test_catalog_prerequisites_psycopg_native import PrerequisitePsycopgNativeTests

class Pg17AdoptionTests(PsycopgHostNativeTests):
    selected_profile=PsycopgProfile(server=170011)

    @classmethod
    def setUpClass(cls):
        PrerequisitePsycopgNativeTests.setUpClass.__func__(cls)

    @classmethod
    def cleanup_fixture(cls):
        import os
        from pathlib import Path
        parent=os.environ.get('TRUSS_PREREQUISITE_EVIDENCE_DIR')
        try:
            if parent:
                target=Path(parent)/'adoption';target.mkdir(exist_ok=True)
                os.environ['TRUSS_PREREQUISITE_EVIDENCE_DIR']=str(target)
            PrerequisitePsycopgNativeTests.cleanup_fixture.__func__(cls)
        finally:
            if parent:os.environ['TRUSS_PREREQUISITE_EVIDENCE_DIR']=parent

    @classmethod
    def tearDownClass(cls):
        pass # Registered original fixture cleanup also covers setup failure.

    def test_selected_profile_retained(self):
        self.assertIs(self.host.profile,self.selected_profile)
        self.assertEqual(self.connection.info.server_version,170011)

    def test_wrong_profile_refuses_before_attachment(self):
        self.host.detach()
        for profile in (PsycopgProfile(server=160015),PsycopgProfile(server=170010),PsycopgProfile(libpq=170011,server=170011),None):
            with self.subTest(profile=profile),self.assertRaises(ValueError):adopt_psycopg_host(self.connection,profile=profile)
        self.host=adopt_psycopg_host(self.connection,profile=self.selected_profile)

    def test_transaction_timeout_terminates_and_quarantines(self):
        self.host.detach()
        self.host=adopt_psycopg_host(self.connection,profile=self.selected_profile,statement_timeout_ms=3000)
        self.connection.execute("SET transaction_timeout='1000ms'")
        transaction=self.begin()
        self.assertEqual(self.scalar(transaction,'SHOW transaction_timeout'),Ok('1s'))
        result=self.scalar(transaction,'SELECT pg_sleep(2)')
        self.assertIsInstance(result,Error)
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertEqual(result.error.sql_state,'25P04')
        self.assertEqual(self.host._custody.last_attempt.error.sqlstate,'25P04')
        self.assertTrue(self.connection.closed or self.connection.broken)
        self.assertTrue(self.host._custody.quarantined)
        self.assertIsNotNone(self.host._custody.last_attempt.error)
        self.assertIsInstance(self.host._run_operation(transaction,lambda cursor,observed:self.fail('Quarantined callback ran')),Error)
        with self.assertRaises(ValueError):adopt_psycopg_host(self.connection,profile=self.selected_profile)

class Pg17PrerequisiteTests(PrerequisitePsycopgNativeTests):
    selected_profile=PsycopgProfile(server=170011)

import unittest
class Pg17FixtureFailureTests(unittest.TestCase):
    def exercise(self,after_setup):
        import os,tempfile,json
        from pathlib import Path
        parent=os.environ.get('TRUSS_PREREQUISITE_EVIDENCE_DIR')
        directory=Path(parent)/('post-setup-failure' if after_setup else 'uncertain-start') if parent else Path(tempfile.mkdtemp(prefix='truss-fixture-failure-',dir='/private/tmp'))
        directory.mkdir(exist_ok=True)
        class Broken(PrerequisitePsycopgNativeTests):
            @classmethod
            def run_pg(cls,name,*args):
                PrerequisitePsycopgNativeTests.run_pg.__func__(cls,name,*args)
                if not after_setup and name=='pg_ctl' and args[-1]=='start':raise RuntimeError('injected uncertain startup')
            @classmethod
            def setUpClass(cls):
                super().setUpClass()
                if after_setup:raise RuntimeError('injected post-start setup failure')
        try:
            os.environ['TRUSS_PREREQUISITE_EVIDENCE_DIR']=str(directory)
            try:
                with self.assertRaisesRegex(RuntimeError,'injected'):Broken.setUpClass()
            finally:
                Broken.doClassCleanups()
            self.assertEqual(Broken.tearDown_exceptions,[])
            receipt=json.loads((directory/'cleanup.json').read_text())
            self.assertEqual((receipt['stop'],receipt['status'],receipt['socket_absent']),(0,3,True))
            self.assertFalse(Broken.root.exists())
        finally:
            if parent:os.environ['TRUSS_PREREQUISITE_EVIDENCE_DIR']=parent
            else:os.environ.pop('TRUSS_PREREQUISITE_EVIDENCE_DIR',None)
    def test_uncertain_started_fixture_is_stopped(self):self.exercise(False)
    def test_post_start_setup_failure_is_stopped(self):self.exercise(True)
