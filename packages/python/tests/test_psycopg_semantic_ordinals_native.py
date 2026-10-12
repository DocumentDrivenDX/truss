"""Actual guarded semantic ordinals; no catalog acceptance qualification."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import psycopg
from truss import Ok, Error, adopt_psycopg_host
from truss._operation_ordinal import OperationOrdinalIssuer
import truss.psycopg_host as host_module

class SemanticOrdinalTests(unittest.TestCase):
    @classmethod
    def run_pg(cls, name, *args):
        subprocess.run([str(cls.pgbin/name), *args], check=True,
                       capture_output=True, text=True, timeout=60)

    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='truss-role-', dir='/tmp'))
        cls.data = cls.root/'data'
        cls.socket = cls.root/'socket'
        cls.pgbin = Path(os.environ['TRUSS_CENSUS_POSTGRES_BIN'])
        cls.database = 'postgres'
        cls.start_attempted = False
        cls.addClassCleanup(cls.cleanup_owned_server)
        cls.socket.mkdir()
        cls.run_pg('initdb', '-D', str(cls.data), '-U', 'postgres', '--auth=trust', '--encoding=UTF8')
        cls.start_attempted = True
        cls.run_pg('pg_ctl', '-D', str(cls.data), '-l', str(cls.root/'server.log'), '-w',
                   '-o', f"-h '' -k {cls.socket}", 'start')
        with psycopg.connect(host=str(cls.socket), user='postgres', dbname=cls.database) as conn:
            actual = conn.execute('SHOW server_version_num').fetchone()[0]
            if actual != '180006':
                raise RuntimeError(f'Expected PostgreSQL 180006, got {actual}')

    @classmethod
    def cleanup_owned_server(cls):
        if cls.start_attempted:
            try:
                cls.run_pg('pg_ctl', '-D', str(cls.data), '-w', '-m', 'immediate', 'stop')
            except Exception as error:
                raise RuntimeError(f'Shutdown unconfirmed; retained {cls.root}') from error
        shutil.rmtree(cls.root)

    def setUp(self):
        self.connection = psycopg.connect(host=str(self.socket), user='postgres',
            dbname=self.database, autocommit=True, options='-c statement_timeout=3000')
        self.addCleanup(self.connection.close)
        self.host = adopt_psycopg_host(self.connection)
        self.addCleanup(lambda: self.host.detach())
        self.connection.execute('BEGIN')
        self.tx = self.host.adopt_transaction().value
        self.connection.execute("CREATE TEMP TABLE caller_work(value text); INSERT INTO caller_work VALUES('kept')")

    def run_semantic(self, statement='SELECT 1'):
        def execute(cursor, observed, ordinal):
            cursor.execute(statement, prepare=False)
            cursor.fetchall()
            return ordinal
        return self.host._run_semantic_operation(self.tx, execute)

    def test_success_rollback_and_inspection_do_not_reuse(self):
        self.assertEqual(self.run_semantic(), Ok('0'))
        self.assertIsInstance(self.run_semantic('SELECT 1/0'), Error)
        attempt = self.host._custody.last_attempt
        self.assertEqual(attempt.ordinal_reservation.result.ordinal, '1')
        self.assertEqual(self.host._run_operation(self.tx, lambda c,o: 'inspection'), Ok('inspection'))
        self.assertEqual(self.run_semantic(), Ok('2'))
        self.assertEqual(self.connection.execute('TABLE caller_work').fetchall(), [('kept',)])

    def test_detach_and_readonly_change_keep_same_transaction_counter(self):
        self.assertEqual(self.run_semantic(), Ok('0'))
        self.host.detach()
        self.connection.execute('SET TRANSACTION READ ONLY')
        self.host = adopt_psycopg_host(self.connection)
        self.tx = self.host.adopt_transaction(access_mode='read_only').value
        self.assertEqual(self.run_semantic(), Ok('1'))
        self.connection.rollback()
        self.connection.execute('BEGIN')
        self.tx = self.host.adopt_transaction().value
        self.assertEqual(self.run_semantic(), Ok('0'))

    def test_failed_savepoint_consumes_before_first_sql(self):
        execute = host_module._GuardedCursor.execute
        def refuse(cursor, query, *args, **kwargs):
            text = query if isinstance(query,str) else query.as_string(self.connection)
            if text.startswith('SAVEPOINT '):
                return execute(cursor, 'SAVEPOINT', *args, **kwargs)
            return execute(cursor,query,*args,**kwargs)
        with patch.object(host_module._GuardedCursor, 'execute', refuse):
            self.assertIsInstance(self.run_semantic(), Error)
        self.assertEqual(self.host._custody.last_attempt.ordinal_reservation.result.ordinal, '0')
        issuer = next(iter(self.host._custody.semantic_issuers.values()))[1]
        self.assertEqual(issuer._next,1)
        self.assertTrue(self.host._custody.quarantined)

    def test_lost_reservation_publication_retains_consumed_ordinal(self):
        publish = OperationOrdinalIssuer._publish_state
        def lost(issuer, state):
            publish(issuer,state)
            raise ValueError('injected lost reservation reply')
        with patch.object(OperationOrdinalIssuer,'_publish_state',lost):
            self.assertIsInstance(self.run_semantic(), Error)
        self.assertEqual(self.host._custody.last_attempt.ordinal_reservation.result.ordinal,'0')
        self.assertEqual(self.run_semantic(), Ok('1'))

    def test_attempt_cap_refuses_without_callback_or_savepoint(self):
        self.assertEqual(self.run_semantic(), Ok('0'))
        issuer = next(iter(self.host._custody.semantic_issuers.values()))[1]
        self.assertEqual(issuer._maximum,255)
        # Set the counter at its production boundary, without 255 irrelevant SQL calls.
        issuer._state = (256, issuer._state[1])
        with patch.object(host_module._GuardedCursor,'execute',side_effect=AssertionError('No SQL expected')):
            result = self.host._run_semantic_operation(self.tx,lambda *args:self.fail('No callback expected'))
        self.assertIsInstance(result, Error)
        self.assertFalse(self.host._custody.quarantined)
        self.assertEqual(self.host._run_operation(self.tx,lambda c,o:'usable'),Ok('usable'))
        self.assertEqual(self.connection.execute('TABLE caller_work').fetchall(), [('kept',)])

    def test_transaction_cap_preserves_caller_usability(self):
        self.host._custody.semantic_issuers.update({(str(i),'test'):None for i in range(256)})
        with patch.object(host_module._GuardedCursor,'execute',side_effect=AssertionError('No SQL expected')):
            result = self.host._run_semantic_operation(self.tx,lambda *args:self.fail('No callback expected'))
        self.assertIsInstance(result,Error)
        self.assertFalse(self.host._custody.quarantined)
        self.assertEqual(self.host._run_operation(self.tx,lambda c,o:'usable'),Ok('usable'))
        self.assertEqual(self.connection.execute('TABLE caller_work').fetchall(), [('kept',)])

if __name__ == '__main__': unittest.main(verbosity=2)
