"""Real native/arbitration composition; successful release stays unqualified."""
import unittest
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._host_execution import HostExecutor
from truss._native_transactions import NativeTransactions
from truss._native_pg8000 import NativeBoundaryRefusal
from truss._native_arbitration import NativeArbitration, NativeOperationSession
from truss._operation_arbitration import Prepared, Unresolved, Refused
from truss.execution import Ok

class NativeArbitrationTests(NativeBoundaryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.t = NativeTransactions(self.boundary)
        self.t.begin()
        self.token = self.boundary.acquire_operation()
        self.port = self.t.port(self.token)
        self.executor = HostExecutor()
        adopted = self.executor.adopt_transaction(self.port, isolation='read_committed', access_mode='read_write')
        self.assertIsInstance(adopted, Ok)
        self.transaction = adopted.value
        self.service = NativeArbitration(self.executor)
        self.assembly = object()
        self.assertEqual(self.service.registry.register(self.assembly), 'registered')
        prepared = self.service.registry.prepare(self.assembly, self.transaction)
        self.assertIsInstance(prepared, Prepared)
        self.attempt = prepared.attempt

    def test_real_prepared_execution_retains_original_calls_in_one_lease(self):
        session = self.service.bind(self.attempt)
        self.assertIsInstance(session, NativeOperationSession)
        self.assertIs(self.service.bind(self.attempt), session)
        p = self.boundary.prepare('SELECT :value::text', token=self.token)
        self.assertEqual(p.run(token=self.token, value='exact'), [['exact']])
        p.close(token=self.token)
        self.assertEqual(len(session.calls), 3)
        for entry, kind in zip(session.calls, ('prepare', 'execute', 'close')):
            self.assertIs(entry.native_call.original_resource[1], p._resource)
            self.assertEqual(entry.resource[0], kind)
            self.assertEqual(entry.revision, entry.native_call.revision)
            self.assertTrue(entry.native_call.capture_complete)
        self.assertIs(session.context.custody, self.executor._original_custody(self.transaction))
        self.assertIs(session.generation, self.port._generation)
        self.assertIsInstance(self.service.release(session), Unresolved)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.release_operation(self.token)
        self.assertIs(self.boundary._operation, self.token)
        self.assertIs(self.boundary._operation_ledger, session)

    def test_foreign_bytes_and_empty_inventory_cannot_release(self):
        session = self.service.bind(self.attempt)
        self.assertEqual(session.calls, ())
        self.assertIsInstance(self.service.registry.release(session.context.lease, b'foreign'), Unresolved)
        # Retry cannot replace the exact original unknown evidence.
        self.assertIsInstance(self.service.release(session), Unresolved)
        self.assertIs(self.boundary._operation_ledger, session)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.release_operation(self.token)

    def test_original_call_reserved_before_transport_failure(self):
        session = self.service.bind(self.attempt)
        original = self.connection.run
        self.connection.run = lambda *a, **k: (_ for _ in ()).throw(OSError('transport lost'))
        try:
            with self.assertRaises(OSError): self.boundary.run('SELECT 1', token=self.token)
        finally:
            self.connection.run = original
        self.assertEqual(len(session.calls), 1)
        self.assertIs(session.calls[0].native_call, self.boundary.last_call)
        self.assertFalse(session.calls[0].native_call.capture_complete)
        self.assertIsInstance(self.service.release(session), Unresolved)

    def test_call_limit_refuses_before_native_submission(self):
        self.service._call_limit = 1
        session = self.service.bind(self.attempt)
        self.assertEqual(self.boundary.run('SELECT 1', token=self.token), [[1]])
        call = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 2', token=self.token)
        self.assertIs(self.boundary.last_call, call)
        self.assertEqual(len(session.calls), 1)
        self.assertFalse(self.boundary._quarantined)

    def test_binding_lost_reply_reconciles_same_retained_session(self):
        original = self.service._publish_binding
        def lost(boundary, session):
            original(boundary, session)
            raise MemoryError('lost binding reply')
        with patch.object(self.service, '_publish_binding', side_effect=lost):
            with self.assertRaises(MemoryError): self.service.bind(self.attempt)
        session = self.service._sessions[0]
        self.assertIs(self.service.bind(self.attempt), session)
        self.assertIs(self.boundary._native_arbitration_sessions[0], session)
        self.assertIs(self.boundary._operation_ledger, session)

    def test_binding_prepublication_failure_reuses_original_session(self):
        with patch.object(self.service, '_publish_binding', side_effect=MemoryError('before publication')):
            with self.assertRaises(MemoryError): self.service.bind(self.attempt)
        session = self.service._sessions[0]
        self.assertIsNone(self.boundary._operation_ledger)
        self.assertIs(self.boundary._pending_operation_ledger, self.service._bindings[0])
        self.assertIs(self.service._bindings[0].session, session)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.release_operation(self.token)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.acquire_operation()
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 1', token=self.token)
        self.assertIs(self.service.bind(self.attempt), session)
        self.assertEqual(len(self.service._sessions), 1)
        self.assertIs(self.boundary._operation_ledger, session)

    def test_foreign_attempt_refuses_without_guard_or_sql_change(self):
        call = self.boundary.last_call
        self.assertIsInstance(self.service.bind(object()), Refused)
        self.assertIs(self.boundary.last_call, call)
        self.assertIsNone(self.boundary._operation_ledger)

    def test_call_limit_prepare_refusal_does_not_reserve_or_quarantine(self):
        self.service._call_limit = 1
        session = self.service.bind(self.attempt)
        self.boundary.run('SELECT 1', token=self.token)
        call = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.prepare('SELECT 2', token=self.token)
        self.assertEqual(self.boundary._resources, ())
        self.assertEqual(len(session.calls), 1)
        self.assertIs(self.boundary.last_call, call)
        self.assertFalse(self.boundary._quarantined)

    def test_call_limit_close_refusal_preserves_original_live_resource(self):
        self.service._call_limit = 1
        session = self.service.bind(self.attempt)
        p = self.boundary.prepare('SELECT 1', token=self.token)
        call = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): p.close(token=self.token)
        self.assertEqual(p._resource.phase, 'live')
        self.assertIsNone(p._resource.close_attempt)
        self.assertIsNone(p._resource.close_call)
        self.assertEqual(len(session.calls), 1)
        self.assertIs(self.boundary.last_call, call)
        self.assertFalse(self.boundary._quarantined)

    def test_disposal_closes_submission_without_erasing_original_session(self):
        session = self.service.bind(self.attempt)
        self.executor.dispose()
        call = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 1', token=self.token)
        self.assertIs(call, self.boundary.last_call)
        self.assertEqual(session.calls, ())
        self.assertIs(self.boundary._operation_ledger, session)
        self.assertIsInstance(self.service.release(session), Unresolved)

    def test_two_boundaries_share_service_retention_under_concurrent_bind(self):
        from threading import Event, Thread
        from truss._native_pg8000 import NativeBoundary
        other = self.Connection(**self.kwargs)
        try:
            other.run('SELECT 1')
            boundary = NativeBoundary(other)
            tracker = NativeTransactions(boundary)
            tracker.begin()
            token = boundary.acquire_operation()
            adopted = self.executor.adopt_transaction(tracker.port(token), isolation='read_committed', access_mode='read_write')
            self.assertIsInstance(adopted, Ok)
            prepared = self.service.registry.prepare(self.assembly, adopted.value)
            self.assertIsInstance(prepared, Prepared)
            entered, proceed, second_started = Event(), Event(), Event()
            original = self.service._publish_binding
            results, errors = [], []
            def paused(b, session):
                if b is self.boundary:
                    entered.set()
                    if not proceed.wait(5): raise RuntimeError('synchronization timeout')
                original(b, session)
            def worker(attempt, second=False):
                if second: second_started.set()
                try: results.append(self.service.bind(attempt))
                except BaseException as error: errors.append(error)
            with patch.object(self.service, '_publish_binding', side_effect=paused):
                first = Thread(target=worker, args=(self.attempt,))
                second = Thread(target=worker, args=(prepared.attempt, True))
                first.start()
                try:
                    self.assertTrue(entered.wait(5))
                    second.start()
                    self.assertTrue(second_started.wait(5))
                finally:
                    proceed.set()
                    first.join(5)
                    second.join(5)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(len(results), 2)
            self.assertEqual(len(self.service._sessions), 2)
            self.assertIn(self.boundary._operation_ledger, self.service._sessions)
            self.assertIn(boundary._operation_ledger, self.service._sessions)
            self.assertIs(self.service.bind(self.attempt), self.boundary._operation_ledger)
            self.assertIs(self.service.bind(prepared.attempt), boundary._operation_ledger)
        finally:
            other.close()

    def test_confirmed_end_retains_original_lease_and_rejects_stale_context(self):
        from dataclasses import replace
        session = self.service.bind(self.attempt)
        self.t.commit(token=self.token)
        self.assertTrue(session.generation.ended)
        self.assertEqual(len(session.calls), 1)
        self.assertIs(session.calls[0].native_call, self.boundary.last_call)
        self.assertIsNone(self.service._verify(session.locator, replace(session.context, generation='2')))
        self.assertIsInstance(self.service.release(session), Unresolved)
        call = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): self.t.begin(token=self.token)
        self.assertIs(self.boundary.last_call, call)
        self.assertIs(self.boundary._operation_ledger, session)

    def test_lost_acquire_reply_keeps_pending_guard_before_session_exists(self):
        original = self.service.registry._publish
        def lost(root):
            original(root)
            raise MemoryError('lost acquire reply')
        with patch.object(self.service.registry, '_publish', side_effect=lost):
            with self.assertRaises(MemoryError): self.service.bind(self.attempt)
        binding = self.service._bindings[0]
        self.assertIsNone(binding.session)
        self.assertIs(self.boundary._pending_operation_ledger, binding)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.release_operation(self.token)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.acquire_operation()
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 1', token=self.token)
        session = self.service.bind(self.attempt)
        self.assertIs(binding.session, session)
        self.assertIs(session.context, self.service.registry._root.entries[self.attempt].completion_context)

    def test_session_allocation_failure_keeps_acquired_original_guard(self):
        with patch.object(self.service, '_make_session', side_effect=MemoryError('allocation lost')):
            with self.assertRaises(MemoryError): self.service.bind(self.attempt)
        binding = self.service._bindings[0]
        self.assertIsNone(binding.session)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.release_operation(self.token)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 1', token=self.token)
        session = self.service.bind(self.attempt)
        self.assertIs(binding.session, session)
        self.assertEqual(len(self.service._bindings), 1)

    def test_completion_attempt_freezes_new_calls_without_releasing_custody(self):
        session = self.service.bind(self.attempt)
        p = self.boundary.prepare('SELECT 1', token=self.token)
        self.assertIsInstance(self.service.release(session), Unresolved)
        call = self.boundary.last_call
        for action in (lambda: self.boundary.run('SELECT 2', token=self.token),
                       lambda: self.boundary.prepare('SELECT 3', token=self.token),
                       lambda: p.run(token=self.token), lambda: p.close(token=self.token)):
            with self.assertRaises(NativeBoundaryRefusal): action()
            self.assertIs(self.boundary.last_call, call)
        self.assertTrue(session.admission_closed)
        self.assertEqual(p._resource.phase, 'live')
        self.assertEqual(len(session.calls), 1)
        self.assertIs(self.boundary._operation, self.token)

    def test_abandoned_unacquired_attempt_does_not_strand_native_guard(self):
        self.assertEqual(self.service.registry.abandon_prepared(self.attempt), 'abandoned')
        self.assertIsInstance(self.service.bind(self.attempt), Refused)
        self.assertIsNone(self.service.registry._root.entries[self.attempt].lease)
        self.assertIsNone(self.boundary._pending_operation_ledger)
        self.assertIsNone(self.boundary._operation_ledger)
        self.boundary.release_operation(self.token)
        self.assertIsNone(self.boundary._operation)

    def test_closed_prepared_assembly_does_not_strand_native_guard(self):
        self.service.registry.close_admission(self.assembly)
        self.assertIsInstance(self.service.bind(self.attempt), Refused)
        self.assertIsNone(self.service.registry._root.entries[self.attempt].lease)
        self.assertIsNone(self.boundary._pending_operation_ledger)
        self.boundary.release_operation(self.token)

    def test_abandon_between_reservation_and_acquire_clears_only_unacquired_claim(self):
        original = self.service.registry.acquire
        def abandon_then_acquire(attempt):
            self.assertIsNotNone(self.boundary._pending_operation_ledger)
            self.assertEqual(self.service.registry.abandon_prepared(attempt), 'abandoned')
            return original(attempt)
        with patch.object(self.service.registry, 'acquire', side_effect=abandon_then_acquire):
            self.assertIsInstance(self.service.bind(self.attempt), Refused)
        self.assertIsNone(self.service.registry._root.entries[self.attempt].lease)
        self.assertIsNone(self.boundary._pending_operation_ledger)
        self.boundary.release_operation(self.token)
