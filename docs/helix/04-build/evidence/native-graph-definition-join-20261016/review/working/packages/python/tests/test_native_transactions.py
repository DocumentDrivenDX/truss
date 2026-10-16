"""Native lifecycle and private adopted-executor composition evidence."""
import unittest
from truss._native_pg8000 import NativeBoundaryRefusal
from truss._native_transactions import NativeTransactions
from truss._host_execution import HostExecutor
from truss.execution import Ok, Error
from test_native_pg8000 import NativeBoundaryFixture


class NativeTransactionTests(NativeBoundaryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.transactions = NativeTransactions(self.boundary)

    def test_repeated_begin_and_chained_end_generations(self):
        t = self.transactions
        t.begin(isolation='repeatable_read')
        first = t._state.generation
        self.assertEqual(first.identity, '1')
        t.begin(isolation='serializable')
        self.assertIs(t._state.generation, first)
        t.rollback(chain=True)
        second = t._state.generation
        self.assertEqual(second.identity, '2')
        self.assertTrue(first.ended)
        self.assertIsNot(second, first)
        t.commit(chain=True)
        self.assertTrue(second.ended)
        third = t._state.generation
        self.assertEqual(third.identity, '3')
        t.rollback()
        self.assertTrue(third.ended)
        self.assertIsNone(t._state.generation)

    def test_shadowing_rollback_and_release_use_original_stack(self):
        t = self.transactions
        t.begin()
        a = t.savepoint('MixedCase')
        b = t.savepoint('MixedCase')
        with self.assertRaises(NativeBoundaryRefusal): t.rollback_to(a)
        t.rollback_to(b)
        c = t.savepoint('child')
        t.release(b)
        with self.assertRaises(NativeBoundaryRefusal): t.release(c)
        t.rollback_to(a)
        t.release(a)
        t.rollback()
        with self.assertRaises(NativeBoundaryRefusal): t.release(a)

    def test_identifier_and_capacity_refuse_before_submission(self):
        t = self.transactions
        t.begin()
        previous = self.boundary.last_call
        for name in ('a'*64, 'é', 'a";COMMIT', '', 4):
            with self.assertRaises(NativeBoundaryRefusal): t.savepoint(name)
            self.assertIs(self.boundary.last_call, previous)
        t._limit = 1
        t.savepoint('one')
        previous = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): t.savepoint('two')
        self.assertIs(self.boundary.last_call, previous)
        t.rollback()

    def test_actual_profile_nonallocating_xid_and_scope(self):
        t = self.transactions
        t.begin(isolation='repeatable_read', access_mode='read_only')
        token = self.boundary.acquire_operation()
        p = t.port(token)
        observed = p.observe()
        self.assertEqual(observed.isolation, 'repeatable_read')
        self.assertEqual(observed.access_mode, 'read_only')
        self.assertIsNone(p.xid)
        self.assertEqual((p.person, p.role), ('postgres', 'postgres'))
        self.boundary.release_operation(token)
        with self.assertRaises(NativeBoundaryRefusal): p.observe()
        t.rollback()

    def test_real_private_executor_adoption_and_failed_savepoint_cleanup(self):
        from pg8000.exceptions import DatabaseError
        t = self.transactions
        t.begin(isolation='repeatable_read')
        token = self.boundary.acquire_operation()
        p = t.port(token)
        e = HostExecutor()
        adopted = e.adopt_transaction(p, isolation='repeatable_read', access_mode='read_write')
        self.assertIsInstance(adopted, Ok)
        h = adopted.value
        a = e.savepoint(h).value
        self.boundary.run('CREATE TEMP TABLE host_work(value text)', token=token)
        self.boundary.run("INSERT INTO host_work VALUES ('prior')", token=token)
        b = e.savepoint(h).value
        with self.assertRaises(DatabaseError): self.boundary.run('SELECT 1/0', token=token)
        self.assertIsInstance(e.rollback_to_savepoint(h, b), Ok)
        self.assertEqual(self.boundary.run('SELECT value FROM host_work', token=token), [['prior']])
        self.assertIsInstance(e.release_savepoint(h, b), Ok)
        self.assertIsInstance(e.release_savepoint(h, a), Ok)
        self.assertIsInstance(e.adopt_transaction(p, isolation='repeatable_read', access_mode='read_write'), Error)
        self.boundary.release_operation(token)
        t.rollback()

    def test_host_release_invalidates_executor_savepoint_before_control(self):
        t = self.transactions
        t.begin()
        token = self.boundary.acquire_operation()
        p = t.port(token)
        e = HostExecutor()
        h = e.adopt_transaction(p, isolation='read_committed', access_mode='read_write').value
        a = e.savepoint(h).value
        b = e.savepoint(h).value
        self.boundary.release_operation(token)
        t.release(p._savepoints[a._key])
        token = self.boundary.acquire_operation()
        p.bind_operation(token)
        result = e.rollback_to_savepoint(h, b)
        self.assertEqual(result.error.code, 'invalid_transaction')
        self.assertFalse(any(event.payload == b'ROLLBACK\0' for event in self.boundary.last_call.events))
        self.assertIsInstance(e.savepoint(h), Ok)
        self.boundary.release_operation(token)
        t.rollback()

    def test_confirmed_end_allows_new_adoption_preserving_original_custody(self):
        t = self.transactions
        e = HostExecutor()
        t.begin()
        token = self.boundary.acquire_operation()
        p = t.port(token)
        h = e.adopt_transaction(p, isolation='read_committed', access_mode='read_write').value
        custody = e._original_custody(h)
        self.boundary.release_operation(token)
        t.commit()
        t.begin()
        token = self.boundary.acquire_operation()
        q = t.port(token)
        new = e.adopt_transaction(q, isolation='read_committed', access_mode='read_write')
        self.assertIsInstance(new, Ok)
        self.assertEqual(p._tracker._identity, q._tracker._identity)
        self.assertNotEqual(h, new.value)
        p.bind_operation(token)
        self.assertEqual(e.savepoint(h).error.code, 'invalid_transaction')
        self.assertIs(e._original_custody(h), custody)
        self.assertIsInstance(e.savepoint(new.value), Ok)
        self.boundary.release_operation(token)
        t.rollback()

    def test_unasserted_multistatement_lifecycle_quarantines_after_effects(self):
        t = self.transactions
        t.begin()
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('COMMIT; BEGIN')
        self.assertTrue(self.boundary._quarantined)
        self.assertEqual(self.boundary.last_call.final_status, b'T')
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.acquire_operation()

    def test_failed_commit_records_actual_rollback_and_retires_generation(self):
        from pg8000.exceptions import DatabaseError, InterfaceError
        t = self.transactions
        t.begin()
        original = t._state.generation
        with self.assertRaises(DatabaseError): self.boundary.run('SELECT 1/0')
        with self.assertRaises(InterfaceError): t.commit()
        self.assertTrue(original.ended)
        self.assertIsNone(t._state.generation)
        self.assertIn(b'ROLLBACK\0', [e.payload for e in self.boundary.last_call.events if e.code == b'C'])
        t.begin()
        self.assertIsNot(original, t._state.generation)
        t.rollback()

    def test_deferred_commit_error_ends_original_generation(self):
        from pg8000.exceptions import DatabaseError
        t = self.transactions
        t.begin()
        original = t._state.generation
        self.boundary.run('CREATE TEMP TABLE deferred_probe(value int UNIQUE DEFERRABLE INITIALLY DEFERRED)')
        self.boundary.run('INSERT INTO deferred_probe VALUES (1), (1)')
        with self.assertRaises(DatabaseError): t.commit()
        self.assertEqual(self.boundary.last_call.final_status, b'I')
        self.assertTrue(original.ended)
        self.assertIsNone(t._state.generation)
        t.begin()
        t.rollback()

    def test_host_shadowing_cannot_redirect_original_executor_handle(self):
        t = self.transactions
        t.begin()
        token = self.boundary.acquire_operation()
        p = t.port(token)
        e = HostExecutor()
        h = e.adopt_transaction(p, isolation='read_committed', access_mode='read_write').value
        a = e.savepoint(h).value
        self.boundary.release_operation(token)
        shadow = t.savepoint(a._key)
        token = self.boundary.acquire_operation()
        p.bind_operation(token)
        self.assertEqual(e.rollback_to_savepoint(h, a).error.code, 'invalid_transaction')
        self.boundary.release_operation(token)
        t.release(shadow)
        token = self.boundary.acquire_operation()
        p.bind_operation(token)
        self.assertIsInstance(e.rollback_to_savepoint(h, a), Ok)
        self.boundary.release_operation(token)
        t.rollback()

    def test_ended_port_cannot_be_readopted_as_new_generation(self):
        t = self.transactions
        e = HostExecutor()
        t.begin()
        token = self.boundary.acquire_operation()
        old = t.port(token)
        self.assertIsInstance(e.adopt_transaction(old, isolation='read_committed', access_mode='read_write'), Ok)
        self.boundary.release_operation(token)
        t.commit()
        t.begin()
        token = self.boundary.acquire_operation()
        old.bind_operation(token)
        previous = self.boundary.last_call
        self.assertEqual(old.observe().state, 'idle')
        self.assertIs(self.boundary.last_call, previous)
        self.assertIsInstance(e.adopt_transaction(old, isolation='read_committed', access_mode='read_write'), Error)
        current = t.port(token)
        self.assertIsInstance(e.adopt_transaction(current, isolation='read_committed', access_mode='read_write'), Ok)
        self.assertIsInstance(e.adopt_transaction(current, isolation='read_committed', access_mode='read_write'), Error)
        self.boundary.release_operation(token)
        t.rollback()

    def test_actual_observation_cannot_resolve_host_shadow_functions(self):
        t = self.transactions
        t.begin()
        self.boundary.run('CREATE SCHEMA shadow_native_probe')
        self.boundary.run("CREATE FUNCTION shadow_native_probe.current_setting(text) RETURNS text LANGUAGE sql AS $$SELECT 'forged'::text$$")
        self.boundary.run("CREATE FUNCTION shadow_native_probe.pg_current_xact_id_if_assigned() RETURNS xid8 LANGUAGE sql AS $$SELECT '999'::xid8$$")
        self.boundary.run('SET LOCAL search_path=shadow_native_probe,pg_catalog')
        self.assertEqual(self.boundary.run("SELECT current_setting('transaction_isolation')"), [['forged']])
        self.boundary.run('CREATE DOMAIN shadow_native_probe.text AS pg_catalog.int4')
        token = self.boundary.acquire_operation()
        p = t.port(token)
        observed = p.observe()
        self.assertEqual(observed.isolation, 'read_committed')
        self.assertEqual(observed.access_mode, 'read_write')
        self.assertNotEqual(p.xid, '999')
        self.boundary.release_operation(token)
        t.rollback()

    def test_original_control_survives_post_native_publication_failure(self):
        from unittest.mock import patch
        t = self.transactions
        t.begin()
        original_after = t._after
        def failed(control, call):
            if control is not None and control.kind == 'savepoint':
                raise MemoryError('Injected post-native lifecycle publication failure')
            return original_after(control, call)
        with patch.object(t, '_after', side_effect=failed):
            with self.assertRaises(MemoryError): t.savepoint('retained_original')
        call = self.boundary.last_call
        self.assertTrue(call.capture_complete)
        self.assertEqual(call.original_control.savepoint.name, 'retained_original')
        self.assertIs(call.original_control.expected.generation, t._state.generation)
        self.assertIs(self.boundary._active_control, call.original_control)
        self.assertTrue(self.boundary._quarantined)
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.acquire_operation()

    def test_monotone_epoch_exhaustion_refuses_before_native_control(self):
        t = self.transactions
        t._next_epoch = 18446744073709551615
        t.begin()
        original = t._state.generation
        self.assertEqual(original.identity, '18446744073709551615')
        t.begin()
        self.assertIs(t._state.generation, original)
        previous = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): t.rollback(chain=True)
        with self.assertRaises(NativeBoundaryRefusal): t.commit(chain=True)
        self.assertIs(self.boundary.last_call, previous)
        self.assertIs(t._state.generation, original)
        self.assertEqual(self.connection._transaction_status, b'T')
        t.rollback()
        previous = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): t.begin()
        self.assertIs(self.boundary.last_call, previous)
        self.assertEqual(self.connection._transaction_status, b'I')
