"""Real supported-API transaction adoption; no installed graph capabilities."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import psycopg
from psycopg import pq
from truss.execution import Ok, Error, TransactionHandle
from truss.psycopg_host import adopt_psycopg_host, PsycopgProfile


def postgres_bin_for_profile(profile):
    if profile.server != 180006:
        raise ValueError('Native tests require PostgreSQL18.6')
    variable = 'TRUSS_CENSUS_POSTGRES_BIN'
    return Path(os.environ[variable])


class PsycopgHostNativeTests(unittest.TestCase):
    selected_profile = PsycopgProfile()
    @classmethod
    def setUpClass(cls):
        cls.worker_fixture = None
        cls.database = 'postgres'
        if os.environ.get('TRUSS_NATIVE_WORKER') and not getattr(cls, 'isolated_lifecycle', False):
            from native_fixture import configure_shared_psycopg_fixture
            configure_shared_psycopg_fixture(cls)
            return
        cls.directory = tempfile.TemporaryDirectory(prefix='truss-psy-', dir='/private/tmp')
        cls.root = Path(cls.directory.name)
        cls.data = cls.root/'data'
        cls.socket = cls.root/'socket'; cls.socket.mkdir()
        cls.pgbin = postgres_bin_for_profile(getattr(cls, 'selected_profile', PsycopgProfile()))
        cls.run_pg('initdb', '-D', str(cls.data), '-U', 'postgres', '--auth=trust', '--encoding=UTF8')
        cls.run_pg('pg_ctl', '-D', str(cls.data), '-l', str(cls.root/'server.log'), '-w',
                   '-o', f"-h '' -k {cls.socket}", 'start')

    @classmethod
    def run_pg(cls, name, *args):
        result = subprocess.run([str(cls.pgbin/name), *args], capture_output=True, text=True, timeout=60)
        if result.returncode: raise RuntimeError(result.stderr[-1000:])

    @classmethod
    def tearDownClass(cls):
        if cls.worker_fixture is not None:
            cls.worker_fixture.cleanup()
            cls.worker_fixture = None
            return
        try: cls.run_pg('pg_ctl', '-D', str(cls.data), '-w', '-m', 'immediate', 'stop')
        finally: cls.directory.cleanup()

    def setUp(self):
        self.connection = psycopg.connect(host=str(self.socket), user='postgres', dbname=self.database,
                                         autocommit=True, options='-c statement_timeout=3000')
        self.addCleanup(self.connection.close)
        self.host = adopt_psycopg_host(self.connection, profile=self.selected_profile, statement_timeout_ms=1000)

        self.addCleanup(self.host.detach)

    def tearDown(self):
        self.host.detach()
        if not self.connection.closed:
            self.connection.rollback(); self.connection.close()

    def begin(self, *, readonly=False):
        self.connection.execute('BEGIN READ ONLY' if readonly else 'BEGIN')
        result = self.host.adopt_transaction(access_mode='read_only' if readonly else 'read_write')
        self.assertIsInstance(result, Ok)
        return result.value

    def scalar(self, transaction, query):
        def execute(cursor, observed):
            cursor.execute(query, prepare=False)
            return cursor.fetchone()[0]
        return self.host._run_operation(transaction, execute)

    def test_idle_refusal_does_not_begin(self):
        self.assertEqual(self.connection.info.transaction_status, pq.TransactionStatus.IDLE)
        self.assertIsInstance(self.host.adopt_transaction(), Error)
        self.assertEqual(self.connection.info.transaction_status, pq.TransactionStatus.IDLE)

    def test_active_readonly_identity_does_not_assign_xid(self):
        transaction = self.begin(readonly=True)
        self.assertEqual(transaction.ownership, 'caller')
        self.assertEqual(self.scalar(transaction, 'SELECT pg_current_xact_id_if_assigned()::text'), Ok(None))
        self.assertEqual(self.scalar(transaction, 'SELECT 1::text'), Ok('1'))
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(), ('3s',))
        self.assertEqual(self.connection.info.transaction_status, pq.TransactionStatus.INTRANS)

    def test_permanent_xid_can_first_be_assigned_by_write(self):
        transaction = self.begin()
        self.assertEqual(self.scalar(transaction, 'SELECT pg_current_xact_id_if_assigned()::text'), Ok(None))
        result = self.scalar(transaction, 'SELECT pg_current_xact_id()::text')
        self.assertIsInstance(result, Ok)
        self.assertEqual(self.scalar(transaction, 'SELECT pg_current_xact_id_if_assigned()::text'), result)

    def test_operation_error_preserves_prior_host_work_and_timeout(self):
        self.connection.execute('BEGIN')
        self.connection.execute("CREATE TEMP TABLE host_work(value text); INSERT INTO host_work VALUES('keep')")
        transaction = self.host.adopt_transaction().value
        result = self.scalar(transaction, 'SELECT 1/0')
        self.assertIsInstance(result, Error); self.assertEqual(result.error.sql_state, '22012')
        self.assertEqual(self.connection.execute('TABLE host_work').fetchall(), [('keep',)])
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(), ('3s',))
        self.assertEqual(self.scalar(transaction, 'SELECT 2::text'), Ok('2'))

    def test_duplicate_and_foreign_handles_refuse(self):
        transaction = self.begin()
        self.assertIsInstance(self.host.adopt_transaction(), Error)
        impostor = TransactionHandle(transaction._issuer, transaction._key, transaction.isolation, transaction.access_mode)
        self.assertIsInstance(self.scalar(impostor, 'SELECT 1'), Error)
        with self.assertRaises(ValueError): adopt_psycopg_host(self.connection,profile=self.selected_profile)
        self.assertEqual(self.scalar(transaction, 'SELECT 1::text'), Ok('1'))

    def test_host_completion_stales_handle_without_claiming_commit(self):
        transaction = self.begin()
        self.connection.rollback(); self.connection.execute('BEGIN')
        self.assertIsInstance(self.scalar(transaction, 'SELECT 1'), Error)
        replacement = self.host.adopt_transaction()
        self.assertIsInstance(replacement, Ok)
        self.assertIsNot(replacement.value, transaction)

    def test_failed_host_transaction_is_not_repaired_by_adoption(self):
        self.connection.execute('BEGIN')
        with self.assertRaises(psycopg.errors.DivisionByZero): self.connection.execute('SELECT 1/0')
        self.assertIsInstance(self.host.adopt_transaction(), Error)
        self.assertEqual(self.connection.info.transaction_status, pq.TransactionStatus.INERROR)

    def test_custom_host_text_loader_does_not_change_observer(self):
        from psycopg.adapt import Loader
        class WrongText(Loader):
            def load(self, data): return 'substituted'
        self.connection.adapters.register_loader(25, WrongText)
        transaction = self.begin()
        self.assertEqual(self.scalar(transaction, 'SELECT 123::text'), Ok('123'))

    def test_dispose_leaves_outer_transaction_and_connection_owned_by_host(self):
        transaction = self.begin()
        self.assertTrue(self.host.dispose())
        self.assertFalse(self.connection.closed)
        self.assertEqual(self.connection.info.transaction_status, pq.TransactionStatus.INTRANS)
        self.assertIsInstance(self.scalar(transaction, 'SELECT 1'), Error)
        self.connection.rollback()

    def test_nonblocking_operation_lease(self):
        transaction = self.begin()
        self.host._custody.lease.acquire()
        try:
            result = self.scalar(transaction, 'SELECT 1')
            self.assertIsInstance(result, Error)
            self.assertEqual(result.error.code, 'execution_obligation')
        finally: self.host._custody.lease.release()
        self.assertEqual(self.scalar(transaction, 'SELECT 1::text'), Ok('1'))

    def test_timeout_refuses_once_and_confirmed_rollback_allows_reuse(self):
        transaction = self.begin()
        self.host._timeout = 25
        result = self.scalar(transaction, 'SELECT pg_sleep(1)')
        self.assertIsInstance(result, Error); self.assertEqual(result.error.sql_state, '57014')
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(), ('3s',))
        self.assertEqual(self.scalar(transaction, 'SELECT 1::text'), Ok('1'))

    def test_uncertain_release_completion_quarantines_across_detach(self):
        transaction = self.begin()
        cursor_factory = self.host._cursor
        class LostRelease:
            def __init__(self, cursor): self.cursor = cursor
            def __getattr__(self, name): return getattr(self.cursor, name)
            def execute(self, query, *args, **kwargs):
                result = self.cursor.execute(query, *args, **kwargs)
                if self.cursor.statusmessage == 'RELEASE': raise RuntimeError('injected lost release reply')
                return result
        self.host._cursor = lambda: LostRelease(cursor_factory())
        result = self.scalar(transaction, 'SELECT 1::text')
        self.assertIsInstance(result, Error)
        self.assertFalse(self.host.detach())
        self.connection.rollback()
        with self.assertRaises(ValueError): adopt_psycopg_host(self.connection,profile=self.selected_profile)

    def test_interrupt_after_write_is_contained_and_primary_preserved(self):
        self.connection.execute('BEGIN')
        self.connection.execute("CREATE TEMP TABLE interrupt_work(value text); INSERT INTO interrupt_work VALUES('keep')")
        transaction = self.host.adopt_transaction().value
        primary = KeyboardInterrupt('injected after write')
        def interrupt(cursor, observed):
            cursor.execute("INSERT INTO interrupt_work VALUES('must disappear')")
            raise primary
        with self.assertRaises(KeyboardInterrupt) as caught:
            self.host._run_operation(transaction, interrupt)
        self.assertIs(caught.exception, primary)
        self.assertEqual(self.connection.execute('TABLE interrupt_work').fetchall(), [('keep',)])
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(), ('3s',))
        self.assertIs(self.host._custody.last_attempt.error, primary)
        self.assertEqual(self.host._custody.last_attempt.phase, 'contained')
        self.assertEqual(self.scalar(transaction, 'SELECT 1::text'), Ok('1'))

    def test_connection_and_profile_are_readonly(self):
        with self.assertRaises(AttributeError): self.host.connection = object()
        with self.assertRaises(AttributeError): self.host.profile = object()
        self.assertIs(self.host.connection, self.connection)

    def test_observer_and_timeout_do_not_use_custom_host_string_dumper(self):
        from psycopg.adapt import Dumper
        class WrongString(Dumper):
            oid = 25
            def dump(self, value): return b'wrong'
        self.connection.adapters.register_dumper(str, WrongString)
        transaction = self.begin()
        self.assertEqual(self.scalar(transaction, 'SELECT 1::text'), Ok('1'))
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(), ('3s',))

    def test_custody_capacity_refuses_before_native_work(self):
        self.connection.execute('BEGIN')
        self.host._transactions = {str(i): None for i in range(256)}
        result = self.host.adopt_transaction()
        self.assertIsInstance(result, Error); self.assertEqual(result.error.code, 'execution_obligation')
        self.host._transactions = {}
        self.assertEqual(self.connection.info.transaction_status, pq.TransactionStatus.INTRANS)

    def test_entire_attempt_deadline_covers_initial_observation(self):
        self.connection.execute("SET statement_timeout=3000; BEGIN")
        self.host._deadline_ms = 40
        observe = self.host._observe
        count = [0]
        def slow_first(cursor):
            count[0] += 1
            if count[0] == 1: cursor.execute('SELECT pg_sleep(1)')
            return observe(cursor)
        self.host._observe = slow_first
        result = self.host.adopt_transaction()
        self.assertIsInstance(result, Error); self.assertEqual(result.error.code, 'cancelled')
        self.assertEqual(self.connection.execute('SHOW statement_timeout').fetchone(), ('3s',))
        self.assertEqual(self.connection.info.transaction_status, pq.TransactionStatus.INTRANS)

    def test_busy_disposal_closes_admission_immediately(self):
        transaction = self.begin()
        self.host._custody.lease.acquire()
        try: self.assertFalse(self.host.dispose())
        finally: self.host._custody.lease.release()
        self.assertIsInstance(self.scalar(transaction, 'SELECT 1'), Error)
        self.assertFalse(self.connection.closed)
        self.assertEqual(self.connection.info.transaction_status, pq.TransactionStatus.INTRANS)

    def test_fallible_setup_does_not_leak_lease(self):
        from unittest.mock import patch
        self.connection.execute('BEGIN')
        with patch('truss.psycopg_host.uuid4', side_effect=MemoryError('injected allocation failure')):
            with self.assertRaises(MemoryError): self.host.adopt_transaction()
        self.assertTrue(self.host._custody.lease.acquire(blocking=False))
        self.host._custody.lease.release()

    def test_cleanup_setup_failure_preserves_primary_and_quarantines(self):
        from unittest.mock import patch
        from truss import psycopg_host
        transaction = self.begin()
        primary = KeyboardInterrupt('original interruption')
        original = psycopg_host._Deadline
        calls = [0]
        def deadline(*args):
            calls[0] += 1
            if calls[0] == 2: raise MemoryError('cleanup setup failure')
            return original(*args)
        def interrupt(cursor, observed): raise primary
        with patch('truss.psycopg_host._Deadline', side_effect=deadline):
            with self.assertRaises(KeyboardInterrupt) as caught: self.host._run_operation(transaction, interrupt)
        self.assertIs(caught.exception, primary)
        self.assertTrue(self.host._custody.quarantined)
        self.assertIsInstance(self.host._custody.last_attempt.cleanup_error, MemoryError)
        self.assertTrue(self.host._custody.lease.acquire(blocking=False))
        self.host._custody.lease.release()

    def test_serialization_failure_requires_new_host_transaction(self):
        transaction = self.begin()
        result = self.scalar(transaction, "DO $$ BEGIN RAISE EXCEPTION 'retry' USING ERRCODE='40001'; END $$")
        self.assertEqual(result.error.retry_scope, 'whole_transaction')
        self.assertIsInstance(self.host.adopt_transaction(), Error)
        self.assertIsInstance(self.scalar(transaction, 'SELECT 1'), Error)
        self.connection.rollback()
        replacement = self.begin()
        self.assertEqual(self.scalar(replacement, 'SELECT 1::text'), Ok('1'))

    def test_expiry_between_savepoint_and_observer_prevents_submission(self):
        from unittest.mock import patch
        from truss import psycopg_host
        self.connection.execute('BEGIN')
        original = self.host._cursor
        queries = []
        class ExpireAfterSavepoint:
            def __init__(self, cursor): self.cursor = cursor
            def __getattr__(self, name): return getattr(self.cursor, name)
            def execute(self, query, **kwargs):
                queries.append(query)
                result = self.cursor.execute(query, **kwargs)
                if self.cursor.statusmessage == 'SAVEPOINT':
                    deadlines[0].end = 0
                return result
        deadlines = []
        deadline_type = psycopg_host._Deadline
        def create(*args):
            result = deadline_type(*args); deadlines.append(result); return result
        self.host._cursor = lambda: ExpireAfterSavepoint(original())
        with patch('truss.psycopg_host._Deadline', side_effect=create):
            result = self.host.adopt_transaction()
        self.assertEqual(result.error.code, 'cancelled')
        self.assertEqual(sum(query == psycopg_host._IDENTITY_SQL for query in queries), 1)
        self.assertEqual(self.connection.info.transaction_status, pq.TransactionStatus.INTRANS)

    def test_monotonic_deadline_detects_delayed_timer(self):
        from truss.psycopg_host import _Deadline
        deadline = _Deadline(self.connection, 60000)
        try:
            deadline.end = 0
            self.assertFalse(deadline.expired.is_set())
            with self.assertRaises(TimeoutError): deadline.check()
        finally: self.assertTrue(deadline.finish())

    def test_success_path_join_interrupt_remains_primary_and_stops_once(self):
        from unittest.mock import patch
        from truss.psycopg_host import _Deadline
        transaction = self.begin()
        original = _Deadline.finish
        primary = KeyboardInterrupt('join interrupted')
        calls = []
        def finish(deadline):
            calls.append(deadline)
            original(deadline)
            raise primary
        with patch.object(_Deadline, 'finish', finish):
            with self.assertRaises(KeyboardInterrupt) as caught:
                self.scalar(transaction, 'SELECT 1::text')
        self.assertIs(caught.exception, primary)
        self.assertEqual(len(calls), 1)
        self.assertTrue(self.host._custody.quarantined)
        self.assertEqual(self.host._custody.last_attempt.phase, 'released')

    def test_success_path_join_failure_never_returns_success(self):
        from unittest.mock import patch
        from truss.psycopg_host import _Deadline
        transaction = self.begin()
        original = _Deadline.finish
        calls = []
        def finish(deadline):
            calls.append(deadline)
            original(deadline)
            raise RuntimeError('join failed')
        with patch.object(_Deadline, 'finish', finish):
            result = self.scalar(transaction, 'SELECT 1::text')
        self.assertIsInstance(result, Error)
        self.assertEqual(result.error.code, 'transaction_unusable')
        self.assertEqual(len(calls), 1)
        self.assertTrue(self.host._custody.quarantined)

    def test_unbounded_or_excessive_host_timeout_refuses_preserving_prior_work(self):
        for timeout in (0, 60001):
            with self.subTest(timeout=timeout):
                self.connection.execute('BEGIN')
                self.connection.execute("CREATE TEMP TABLE timeout_prior(value text); INSERT INTO timeout_prior VALUES('keep')")
                self.connection.execute(f'SET LOCAL statement_timeout={timeout}')
                calls = []
                result = self.host._attempt(lambda *args: calls.append(args))
                self.assertIsInstance(result, Error)
                self.assertEqual(calls, [])
                self.assertIsInstance(self.host.adopt_transaction(), Error)
                self.assertEqual(self.connection.execute('TABLE timeout_prior').fetchall(), [('keep',)])
                self.assertEqual(self.connection.execute("SELECT setting FROM pg_settings WHERE name='statement_timeout'").fetchone(), (str(timeout),))
                self.connection.rollback()
