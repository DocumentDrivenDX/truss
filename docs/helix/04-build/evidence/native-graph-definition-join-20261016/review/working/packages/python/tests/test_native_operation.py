"""Private selected text operation; never protected capability evidence."""
import unittest
from test_native_pg8000 import NativeBoundaryFixture
from truss._host_execution import HostExecutor
from truss._native_transactions import NativeTransactions
from truss._native_arbitration import NativeArbitration
from truss._native_operation import NativeOperationRunner
from truss.execution import Ok, Error

class NativeOperationTests(NativeBoundaryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.boundary.run('CREATE TEMP TABLE truss_operation_fixture(value text PRIMARY KEY)')
        self.t = NativeTransactions(self.boundary)
        self.t.begin()
        token = self.boundary.acquire_operation()
        self.executor = HostExecutor()
        self.port = self.t.port(token)
        adopted = self.executor.adopt_transaction(self.port, isolation='read_committed', access_mode='read_write')
        self.assertIsInstance(adopted, Ok)
        self.tx = adopted.value
        self.boundary.release_operation(token)
        self.service = NativeArbitration(self.executor)
        self.runner = NativeOperationRunner(self.service)

    def test_success_failure_success_preserves_host(self):
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        host = self.boundary.run("SELECT 'host-before'::text")
        context = self.connection._context
        generation = self.t._state.generation
        result = self.runner.execute(self.tx, statement, {'value': 'first'})
        self.assertIsInstance(result, Ok, repr(result))
        self.assertEqual(result.value, (('first',),))
        self.assertIs(self.connection._context, context)
        self.assertEqual(host, [['host-before']])
        self.assertIsNone(self.boundary._operation)
        self.boundary.run("INSERT INTO truss_operation_fixture VALUES('host-between')")
        failure = self.runner.execute(self.tx, statement, {'value': 'nul\0value'})
        self.assertIsInstance(failure, Error, repr(failure))
        self.assertEqual(failure.error.code, 'execution_obligation')
        self.assertIsNone(self.boundary._operation)
        self.assertIsInstance(self.runner.execute(self.tx, statement, {'value': 'last'}), Ok)
        self.assertIs(self.t._state.generation, generation)
        self.assertEqual(self.boundary.run('SELECT value FROM truss_operation_fixture ORDER BY value'), [['host-between']])

    def test_unicode_and_null_are_lossless(self):
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        for value in ('🙂 café 𐐀', '', None):
            result = self.runner.execute(self.tx, statement, {'value': value})
            self.assertIsInstance(result, Ok, repr(result))
            self.assertEqual(result.value, ((value,),))

    def test_busy_refusal_leaves_winner_unchanged(self):
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        token = self.boundary.acquire_operation()
        before = self.boundary.last_call
        result = self.runner.execute(self.tx, statement, {'value': 'refused'})
        self.assertIsInstance(result, Error)
        self.assertIs(self.boundary.last_call, before)
        self.assertIs(self.boundary._operation, token)
        self.assertFalse(self.boundary._quarantined)
        self.boundary.release_operation(token)
        self.assertIsInstance(self.runner.execute(self.tx, statement, {'value': 'works'}), Ok)

    def test_unqualified_sql_cannot_change_host_settings(self):
        with self.assertRaises(ValueError):
            self.runner.register("SELECT pg_catalog.set_config('statement_timeout','42s',false)::pg_catalog.text", 'SELECT')

    def test_preexisting_prepared_resource_is_preserved(self):
        host = self.boundary.prepare('SELECT :value::text')
        before = self.boundary.last_call
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        self.assertIsInstance(self.runner.execute(self.tx, statement, {'value': 'no'}), Error)
        self.assertIs(self.boundary.last_call, before)
        self.assertEqual(host.run(value='host'), [['host']])
        host.close()

    def test_ordinary_call_exhaustion_retains_cleanup_capacity(self):
        self.service._call_limit = 3
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        result = self.runner.execute(self.tx, statement, {'value': 'not executed'})
        self.assertIsInstance(result, Error, repr(result))
        self.assertEqual(result.error.code, 'execution_obligation')
        self.assertFalse(self.boundary._quarantined)
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(self.boundary.run("SELECT 'host-after'::text"), [['host-after']])

    def test_lost_handback_reply_and_stale_reconcile_do_not_clear_later_owner(self):
        from unittest.mock import patch
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        original = self.boundary._publish_ownership
        def lost(root):
            original(root)
            raise OSError('lost handback reply')
        with patch.object(self.boundary, '_publish_ownership', lost):
            result = self.runner.execute(self.tx, statement, {'value': 'first'})
        self.assertIsInstance(result, Ok, repr(result))
        run = self.runner._runs[-1]
        later = self.boundary.acquire_operation()
        self.assertIs(self.runner.reconcile(run), result)
        self.assertIs(self.boundary._operation, later)
        self.assertFalse(self.boundary._quarantined)
        self.boundary.release_operation(later)

    def test_lost_completion_publication_reply_reconciles_original(self):
        from unittest.mock import patch
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        original = self.runner._produce
        def lost(run, final):
            original(run, final)
            raise OSError('lost original completion reply')
        with patch.object(self.runner, '_produce', lost):
            result = self.runner.execute(self.tx, statement, {'value': 'original'})
        self.assertIsInstance(result, Error)
        self.assertFalse(self.boundary._quarantined)
        recovered = self.runner.reconcile(self.runner._runs[-1])
        self.assertIsInstance(recovered, Ok)
        self.assertEqual(recovered.value, (('original',),))
        self.assertIsNone(self.boundary._operation)

    def test_foreign_null_encoder_refuses_before_sql(self):
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        self.connection.py_types[type(None)] = lambda value: 'wrong'
        before = self.boundary.last_call
        self.assertIsInstance(self.runner.execute(self.tx, statement, {'value': None}), Error)
        self.assertIs(self.boundary.last_call, before)
        self.assertIsNone(self.boundary._operation)

    def test_native_text_error_is_contained(self):
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        self.assertIsInstance(self.runner.execute(self.tx, statement, {'value': 'before'}), Ok)
        result = self.runner.execute(self.tx, statement, {'value': 'nul\0value'})
        self.assertIsInstance(result, Error, repr(result))
        self.assertEqual(result.error.code, 'execution_obligation')
        self.assertFalse(self.boundary._quarantined)
        self.assertIsNone(self.boundary._operation)
        self.assertIsInstance(self.runner.execute(self.tx, statement, {'value': 'after'}), Ok)

    def test_oversized_native_cell_quarantines_and_retains_guard(self):
        from truss._native_result_custody import NativeTextLimits
        self.runner.limits = NativeTextLimits(cell_bytes=1)
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        result = self.runner.execute(self.tx, statement, {'value': 'oversized'})
        self.assertIsInstance(result, Error)
        self.assertEqual(result.error.code, 'transaction_unusable')
        self.assertTrue(self.boundary._quarantined)
        self.assertIsNotNone(self.boundary._operation)
        self.assertTrue(self.runner._runs[-1].gate.failed)

    def test_cleanup_failure_cannot_publish_completion(self):
        from unittest.mock import patch
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        with patch.object(self.runner, '_close_portal', side_effect=OSError('cleanup lost')):
            result = self.runner.execute(self.tx, statement, {'value': 'result'})
        self.assertIsInstance(result, Error)
        self.assertTrue(self.boundary._quarantined)
        self.assertIsNotNone(self.boundary._operation)
        self.assertIsNone(self.runner._runs[-1].completion)

    def test_disposal_does_not_interrupt_reserved_cleanup(self):
        from unittest.mock import patch
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        original = self.t.release
        def disposed(*args, **kwargs):
            self.executor.dispose()
            return original(*args, **kwargs)
        with patch.object(self.t, 'release', disposed):
            result = self.runner.execute(self.tx, statement, {'value': 'complete'})
        self.assertIsInstance(result, Ok, repr(result))
        self.assertIsNone(self.boundary._operation)
        self.assertFalse(self.boundary._quarantined)
        self.assertIsInstance(self.runner.execute(self.tx, statement, {'value': 'refused'}), Error)
        self.assertEqual(self.boundary.run("SELECT 'host'::text"), [['host']])

    def test_completed_gate_does_not_pin_historical_host_context(self):
        import gc, weakref
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        self.boundary.run("SELECT 'host-owned'::text")
        original = self.connection._context
        reference = weakref.ref(original)
        self.assertIsInstance(self.runner.execute(self.tx, statement, {'value': 'operation'}), Ok)
        self.assertIs(self.connection._context, original)
        self.assertIsNone(self.runner._runs[-1].gate.original_context)
        self.boundary.run("SELECT 'later-host'::text")
        del original
        gc.collect()
        self.assertIsNone(reference())

    def test_synthetic_port_refuses_selected_native_profile(self):
        from test_host_execution import Port
        port = Port()
        adopted = self.executor.adopt_transaction(port, isolation='repeatable_read', access_mode='read_write')
        self.assertIsInstance(adopted, Ok)
        statement = self.runner.register('SELECT :value::pg_catalog.text', 'SELECT')
        before = self.boundary.last_call
        result = self.runner.execute(adopted.value, statement, {'value': 'refused'})
        self.assertIsInstance(result, Error)
        self.assertEqual(port.commands, [])
        self.assertIs(self.boundary.last_call, before)
