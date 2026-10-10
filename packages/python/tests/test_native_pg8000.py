"""Private native-call evidence; no public adoption or protected admission."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlparse, parse_qs
from truss import LocalPostgres
from truss._native_pg8000 import NativeBoundary, NativeBoundaryRefusal


@unittest.skipUnless(importlib.util.find_spec('pg8000'), 'Optional pinned native driver absent')
class NativeBoundaryFixture:
    @classmethod
    def setUpClass(cls):
        from pg8000.native import Connection
        cls.directory = tempfile.TemporaryDirectory(prefix='truss-native-boundary-')
        cls.runtime = LocalPostgres(Path(cls.directory.name) / 'data').__enter__()
        uri = urlparse(cls.runtime.info.connection_uri)
        params = parse_qs(uri.query)
        host = params.get('host', [uri.hostname])[0]
        port = int(params.get('port', [uri.port or 5432])[0])
        cls.kwargs = dict(user='postgres', database='postgres', port=port, ssl_context=False)
        cls.kwargs['unix_sock' if host.startswith('/') else 'host'] = str(Path(host) / f'.s.PGSQL.{port}') if host.startswith('/') else host
        cls.Connection = Connection

    @classmethod
    def tearDownClass(cls):
        cls.runtime.close()
        cls.directory.cleanup()

    def setUp(self):
        self.connection = self.Connection(**self.kwargs)
        self.connection.run('SELECT 1')  # Original driver resets startup status to None.
        self.boundary = NativeBoundary(self.connection)

    def tearDown(self):
        # Test teardown deliberately uses the original host alias after evidence
        # collection; it is not supported cooperative-wrapper operation.
        self.connection.close()


class NativeBoundaryTests(NativeBoundaryFixture, unittest.TestCase):
    def test_extended_call_keeps_all_ready_cycles(self):
        self.assertEqual(self.boundary.run('SELECT :value::text', value='exact'), [['exact']])
        call = self.boundary.last_call
        self.assertTrue(call.capture_complete)
        self.assertFalse(call.driver_raised)
        self.assertGreaterEqual(sum(e.code == b'Z' for e in call.events), 2)
        self.assertEqual(call.events[-1].code, b'Z')

    def test_prepared_and_host_calls_share_operation_guard(self):
        prepared = self.boundary.prepare('SELECT :value::text')
        token = self.boundary.acquire_operation()
        original = self.boundary.last_call
        for action in (lambda: self.boundary.run('SELECT 1'), prepared.run, prepared.close,
                       self.boundary.close, self.boundary.acquire_operation):
            with self.assertRaises(NativeBoundaryRefusal): action()
            self.assertIs(self.boundary.last_call, original)
        self.assertEqual(prepared.run(token=token, value='guarded'), [['guarded']])
        prepared.close(token=token)
        self.boundary.release_operation(token)
        with self.assertRaises(NativeBoundaryRefusal): prepared.run(value='closed')
        self.assertEqual(self.boundary.run('SELECT 2'), [[2]])

    def test_original_error_and_rollback_survive_driver_exception(self):
        from pg8000.exceptions import DatabaseError, InterfaceError
        self.boundary.run('BEGIN')
        with self.assertRaises(DatabaseError): self.boundary.run('SELECT 1/0')
        failure = self.boundary.last_call
        self.assertTrue(failure.driver_raised)
        self.assertTrue(failure.capture_complete)
        self.assertTrue(any(e.code == b'E' for e in failure.events))
        self.assertEqual(failure.final_status, b'E')
        with self.assertRaises(InterfaceError): self.boundary.run('COMMIT')
        completion = self.boundary.last_call
        self.assertTrue(completion.driver_raised)
        self.assertTrue(completion.capture_complete)
        self.assertIn(b'ROLLBACK\0', [e.payload for e in completion.events if e.code == b'C'])
        self.assertEqual(completion.final_status, b'I')

    def test_attach_requires_idle_and_single_original_owner(self):
        with self.assertRaises(NativeBoundaryRefusal): NativeBoundary(self.connection)
        other = self.Connection(**self.kwargs)
        try:
            other.run('BEGIN')
            with self.assertRaises(NativeBoundaryRefusal): NativeBoundary(other)
        finally: other.close()

    def test_raw_alias_events_quarantine_without_claiming_pre_effect_refusal(self):
        self.connection.run('SELECT 1')
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 2')
        self.assertIsNone(self.boundary.last_call)

    def test_capture_overflow_is_retained_incomplete_and_quarantined(self):
        other = self.Connection(**self.kwargs)
        try:
            other.run('SELECT 1')
            boundary = NativeBoundary(other, event_bytes=1)
            self.assertEqual(boundary.run('SELECT 1'), [[1]])
            self.assertFalse(boundary.last_call.capture_complete)
            self.assertLessEqual(sum(len(e.payload)+1 for e in boundary.last_call.events), 1)
            with self.assertRaises(NativeBoundaryRefusal): boundary.acquire_operation()
        finally: other.close()

    def test_missing_completion_keeps_original_operation_quarantined(self):
        token = self.boundary.acquire_operation()
        original = self.connection.run
        def lost(*args, **kwargs): raise OSError('Injected transport loss before completion')
        self.connection.run = lost
        try:
            with self.assertRaises(OSError): self.boundary.run('SELECT 1', token=token)
        finally: self.connection.run = original
        self.assertFalse(self.boundary.last_call.capture_complete)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.release_operation(token)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 2', token=token)

    def test_competing_call_refuses_before_original_driver_invocation(self):
        from threading import Event, Thread
        entered, proceed = Event(), Event()
        original = self.connection.run
        calls, errors = [], []
        def paused(sql, **params):
            calls.append(sql)
            entered.set()
            if not proceed.wait(5): raise RuntimeError('Test synchronization timeout')
            return original(sql, **params)
        self.connection.run = paused
        def worker():
            try: self.boundary.run('SELECT 1')
            except BaseException as error: errors.append(error)
        thread = Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(entered.wait(5))
            with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 2')
            with self.assertRaises(NativeBoundaryRefusal): self.boundary.acquire_operation()
            self.assertEqual(calls, ['SELECT 1'])
        finally:
            proceed.set()
            thread.join(5)
            self.connection.run = original
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertTrue(self.boundary.last_call.capture_complete)

    def test_transport_loss_after_prior_ready_is_not_settled(self):
        for stage in ('send_BIND', 'send_EXECUTE'):
            other = self.Connection(**self.kwargs)
            try:
                other.run('SELECT 1')
                boundary = NativeBoundary(other)
                original = getattr(other, stage)
                def lost(*args, **kwargs):
                    original(*args, **kwargs)
                    raise OSError('Injected transport uncertainty after submission')
                setattr(other, stage, lost)
                with self.assertRaises(OSError): boundary.run('SELECT :value::text', value='x')
                call = boundary.last_call
                self.assertTrue(any(e.code == b'Z' for e in call.events))
                self.assertFalse(call.capture_complete)
                with self.assertRaises(NativeBoundaryRefusal): boundary.run('SELECT 2')
            finally: other.close()

    def test_closed_prepared_validation_is_inside_call_admission(self):
        prepared = self.boundary.prepare('SELECT 1')
        prepared.close()
        original = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): prepared.run()
        self.assertIs(self.boundary.last_call, original)
        self.assertEqual(self.boundary.run('SELECT 2'), [[2]])

    def test_close_vs_run_cannot_submit_after_native_close(self):
        from threading import Event, Thread
        prepared = self.boundary.prepare('SELECT 1')
        native_closed, publish = Event(), Event()
        original_close = prepared._original.close
        errors = []
        def pause_after_native_close():
            result = original_close()
            native_closed.set()
            if not publish.wait(5): raise RuntimeError('Test synchronization timeout')
            return result
        prepared._original.close = pause_after_native_close
        def worker():
            try: prepared.close()
            except BaseException as error: errors.append(error)
        thread = Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(native_closed.wait(5))
            with self.assertRaises(NativeBoundaryRefusal): prepared.run()
        finally:
            publish.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        completion = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): prepared.run()
        self.assertIs(self.boundary.last_call, completion)
        self.assertEqual(self.boundary.run('SELECT 2'), [[2]])
