"""Original prepared-resource facts; no public/resource-profile claim."""
import unittest
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._native_pg8000 import NativeBoundary, NativeBoundaryRefusal, _Prepared

class NativeResourceTests(NativeBoundaryFixture, unittest.TestCase):
    def test_creation_and_close_require_original_acknowledgements(self):
        p = self.boundary.prepare('SELECT :value::text')
        r = p._resource
        self.assertIs(self.boundary._resources[0], p)
        self.assertEqual(r.name, p._original.name_bin)
        self.assertTrue(r.native_created)
        self.assertEqual(r.phase, 'live')
        self.assertIs(r.create_call.original_resource[1], r)
        self.assertEqual(p.run(value='exact'), [['exact']])
        p.close()
        self.assertTrue(r.native_closed)
        self.assertEqual(r.phase, 'closed')
        self.assertIs(r.close_call.original_resource[1], r)
        call = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): p.close()
        self.assertIs(call, self.boundary.last_call)

    def test_parse_complete_followed_by_describe_error_retains_creation(self):
        original = self.connection.send_DESCRIBE_STATEMENT
        self.connection.send_DESCRIBE_STATEMENT = lambda name: original(b'missing_truss_statement\0')
        with self.assertRaises(Exception): self.boundary.prepare('SELECT 1')
        p = self.boundary._resources[0]
        self.assertIsNone(p._original)
        self.assertTrue(p._resource.native_created)
        self.assertIsNotNone(p._resource.name)
        self.assertEqual(p._resource.phase, 'unknown')
        self.assertTrue(p._resource.create_call.capture_complete)
        self.assertTrue(p._resource.create_call.driver_raised)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 2')

    def test_close_complete_before_bookkeeping_failure_retains_closed_fact(self):
        p = self.boundary.prepare('SELECT 1')
        class BrokenSet(set):
            def remove(self, name): raise MemoryError('lost driver bookkeeping')
        self.connection._statement_nums = BrokenSet(self.connection._statement_nums)
        with self.assertRaises(MemoryError): p.close()
        self.assertTrue(p._resource.native_closed)
        self.assertFalse(p._closed)
        self.assertEqual(p._resource.phase, 'unknown')
        self.assertFalse(p._resource.close_call.capture_complete)
        self.assertIs(p._resource.close_call, self.boundary.last_call)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.acquire_operation()

    def test_lost_wrapper_publication_preserves_exact_native_resource(self):
        with patch.object(_Prepared, '_publish_live', side_effect=MemoryError('lost publication')):
            with self.assertRaises(MemoryError): self.boundary.prepare('SELECT 1')
        p = self.boundary._resources[0]
        self.assertTrue(p._resource.native_created)
        self.assertEqual(p._resource.name, p._original.name_bin)
        self.assertTrue(p._resource.create_call.capture_complete)
        self.assertEqual(p._resource.phase, 'unknown')
        with self.assertRaises(NativeBoundaryRefusal): p.run()

    def test_missing_prepare_completion_retains_name_before_submission(self):
        original = self.connection.send_PARSE
        def lost(name, *args, **kwargs):
            original(name, *args, **kwargs)
            raise OSError('uncertain prepare send')
        self.connection.send_PARSE = lost
        with self.assertRaises(OSError): self.boundary.prepare('SELECT 1')
        p = self.boundary._resources[0]
        self.assertIsNotNone(p._resource.name)
        self.assertFalse(p._resource.native_created)
        self.assertEqual(p._resource.phase, 'unknown')
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 2')

    def test_exact_retained_count_refuses_before_sql_even_after_close(self):
        self.boundary._prepared_limit = 1
        p = self.boundary.prepare('SELECT 1')
        p.close()
        call = self.boundary.last_call
        names = set(self.connection._statement_nums)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.prepare('SELECT 2')
        self.assertIs(self.boundary.last_call, call)
        self.assertEqual(self.connection._statement_nums, names)
        self.assertEqual(len(self.boundary._resources), 1)

    def test_lost_caller_handle_stays_owned_by_original_boundary(self):
        import gc, weakref
        p = self.boundary.prepare('SELECT 1')
        ref = weakref.ref(p)
        del p
        gc.collect()
        self.assertIsNotNone(ref())
        self.assertIs(self.boundary._resources[0], ref())
        self.assertTrue(ref()._resource.native_created)

    def test_missing_close_complete_never_claims_closed_from_ready(self):
        p = self.boundary.prepare('SELECT 1')
        p._original.close = lambda: self.connection.run('SELECT 1')
        p.close()
        self.assertFalse(p._resource.native_closed)
        self.assertFalse(p._closed)
        self.assertEqual(p._resource.phase, 'unknown')
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 2')

    def test_refused_competing_close_cannot_quarantine_original_close(self):
        from threading import Event, Thread
        p = self.boundary.prepare('SELECT 1')
        entered, proceed = Event(), Event()
        original = p._original.close
        errors = []
        def paused():
            entered.set()
            if not proceed.wait(5): raise RuntimeError('synchronization timeout')
            return original()
        p._original.close = paused
        def worker():
            try: p.close()
            except BaseException as error: errors.append(error)
        thread = Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(entered.wait(5))
            with self.assertRaises(NativeBoundaryRefusal): p.close()
            self.assertEqual(p._resource.phase, 'closing')
            self.assertFalse(self.boundary._quarantined)
        finally:
            proceed.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(p._resource.phase, 'closed')
        self.assertTrue(p._resource.native_closed)
        self.assertEqual(self.boundary.run('SELECT 2'), [[2]])
