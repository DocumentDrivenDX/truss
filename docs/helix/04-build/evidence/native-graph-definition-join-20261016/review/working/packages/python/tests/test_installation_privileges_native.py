"""Fresh native privilege protection, not a callable catalog installation."""
from pathlib import Path
import unittest
from unittest.mock import patch
import psycopg
from truss import Ok, Error, PsycopgProfile
import truss._installation_privileges as privileges
from truss._installation_privileges import InstallationRoles, protect_installation_in_transaction
from test_psycopg_host_native import PsycopgHostNativeTests

ROOT=Path(__file__).resolve().parents[3]

class InstallationPrivilegeTests(unittest.TestCase):
    run_pg=classmethod(PsycopgHostNativeTests.run_pg.__func__)
    setUpClass=classmethod(PsycopgHostNativeTests.setUpClass.__func__)
    tearDownClass=classmethod(PsycopgHostNativeTests.tearDownClass.__func__)
    tearDown=PsycopgHostNativeTests.tearDown
    begin=PsycopgHostNativeTests.begin
    selected_profile=PsycopgProfile(server=180006)
    def setUp(self):
        PsycopgHostNativeTests.setUp(self)
        self.tx=self.begin()
        self.connection.execute((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text(),prepare=False)
        self.connection.execute("CREATE TYPE truss.choice AS ENUM ('a','b'); CREATE DOMAIN truss.positive AS int CHECK(VALUE>0)",prepare=False)
        self.connection.execute("CREATE FUNCTION truss.private_probe() RETURNS int LANGUAGE sql AS 'SELECT 1'; CREATE FUNCTION truss.private_probe(value int) RETURNS int LANGUAGE sql AS 'SELECT value'",prepare=False)
        self.connection.execute("CREATE TABLE public.caller_sentinel(value text); INSERT INTO public.caller_sentinel VALUES ('kept')",prepare=False)
        self.roles=InstallationRoles('truss_test_owner','truss_test_client')
    def protect(self):
        return protect_installation_in_transaction(self.host,self.tx,self.roles)
    def test_protects_generated_layout_and_future_routines(self):
        result=self.protect();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.connection.execute('SET LOCAL ROLE truss_test_owner')
        self.connection.execute("CREATE FUNCTION truss.future_probe() RETURNS int LANGUAGE sql AS 'SELECT 2'",prepare=False)
        self.connection.execute('RESET ROLE')
        self.assertFalse(self.connection.execute("SELECT has_function_privilege('truss_test_client','truss.future_probe()','EXECUTE')").fetchone()[0])
        self.assertFalse(self.connection.execute("SELECT pg_has_role('truss_test_client','truss_test_owner','MEMBER')").fetchone()[0])
        self.connection.execute('CREATE ROLE truss_test_person LOGIN; GRANT truss_test_client TO truss_test_person',prepare=False)
        for statement in ['SELECT * FROM truss.schema_head', 'INSERT INTO truss.schema_head VALUES(1,0)',
                'TRUNCATE truss.schema_head', 'ALTER TABLE truss.schema_head DISABLE TRIGGER ALL',
                "CREATE OR REPLACE FUNCTION truss.private_probe() RETURNS int LANGUAGE sql AS 'SELECT 9'",
                'SELECT truss.private_probe()', 'SET ROLE truss_test_owner']:
            with self.subTest(statement=statement):
                self.connection.execute('SAVEPOINT denied')
                self.connection.execute('SET LOCAL SESSION AUTHORIZATION truss_test_person')
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.connection.execute(statement,prepare=False)
                self.connection.execute('ROLLBACK TO denied');self.connection.execute('RELEASE denied')
        self.assertEqual(self.connection.execute('SELECT value FROM public.caller_sentinel').fetchall(),[('kept',)])
    def test_public_column_grant_removed(self):
        self.connection.execute('GRANT SELECT(id) ON truss.schema_head TO PUBLIC')
        result=self.protect();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertFalse(self.connection.execute("SELECT has_column_privilege('truss_test_client','truss.schema_head','id','SELECT')").fetchone()[0])
    def test_late_failure_restores_roles_owners_and_caller_work(self):
        with patch('truss._installation_privileges._verify',side_effect=ValueError('injected late failure')) as verify:
            self.assertIsInstance(self.protect(),Error)
            verify.assert_called_once()
        self.assertEqual(self.connection.execute("SELECT count(*) FROM pg_roles WHERE rolname IN ('truss_test_owner','truss_test_client')").fetchone()[0],0)
        self.assertEqual(self.connection.execute("SELECT nspowner=(SELECT oid FROM pg_roles WHERE rolname=current_user) FROM pg_namespace WHERE nspname='truss'").fetchone()[0],True)
        self.assertEqual(self.connection.execute('SELECT value FROM public.caller_sentinel').fetchall(),[('kept',)])
    def test_collisions_third_party_grants_and_unsupported_objects_refuse(self):
        cases=('CREATE ROLE truss_test_owner',
               'CREATE ROLE third_party; GRANT SELECT ON truss.schema_head TO third_party',
               'CREATE VIEW truss.extra_view AS SELECT 1 AS value',
               'CREATE ROLE third_party; GRANT SELECT(id) ON truss.schema_head TO third_party',
               'ALTER EXTENSION plpgsql ADD TABLE truss.schema_head')
        for statement in cases:
            with self.subTest(statement=statement):
                self.connection.execute('SAVEPOINT preflight')
                self.connection.execute(statement,prepare=False)
                self.assertIsInstance(self.protect(),Error)
                self.assertEqual(self.connection.execute("SELECT count(*) FROM pg_roles WHERE rolname='truss_test_client'").fetchone()[0],0)
                self.connection.execute('ROLLBACK TO preflight');self.connection.execute('RELEASE preflight')

    def test_hostile_search_path_is_ignored_and_restored(self):
        self.connection.execute("CREATE SCHEMA evil; CREATE DOMAIN evil.aclitem AS text; CREATE DOMAIN evil.regclass AS text",prepare=False)
        self.connection.execute("CREATE FUNCTION evil.current_setting(text) RETURNS text LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'hostile function called'; END $$",prepare=False)
        self.connection.execute('SET LOCAL search_path TO evil, pg_catalog, public')
        before=self.connection.execute("SELECT pg_catalog.current_setting('search_path')").fetchone()[0]
        self.assertIsInstance(self.protect(),Ok,str(self.host._custody.last_attempt.error))
        self.assertEqual(self.connection.execute("SELECT pg_catalog.current_setting('search_path')").fetchone()[0],before)
    def test_restored_public_default_refuses_and_rolls_back(self):
        original=privileges._verify
        def restore_public(cursor,*args):
            cursor.execute('ALTER DEFAULT PRIVILEGES FOR ROLE truss_test_owner GRANT EXECUTE ON FUNCTIONS TO PUBLIC',prepare=False)
            return original(cursor,*args)
        with patch('truss._installation_privileges._verify',side_effect=restore_public) as verify:
            self.assertIsInstance(self.protect(),Error)
            verify.assert_called_once()
        self.assertEqual(self.connection.execute("SELECT count(*) FROM pg_roles WHERE rolname IN ('truss_test_owner','truss_test_client')").fetchone()[0],0)
        self.assertEqual(self.connection.execute('SELECT value FROM public.caller_sentinel').fetchall(),[('kept',)])

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(InstallationPrivilegeTests(name) for name in (
        'test_protects_generated_layout_and_future_routines','test_public_column_grant_removed',
        'test_late_failure_restores_roles_owners_and_caller_work',
        'test_collisions_third_party_grants_and_unsupported_objects_refuse',
        'test_hostile_search_path_is_ignored_and_restored',
        'test_restored_public_default_refuses_and_rolls_back'))
