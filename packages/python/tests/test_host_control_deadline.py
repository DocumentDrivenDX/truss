"""Original bounded control transport; actual deferred native commit stall."""
import unittest
from unittest.mock import patch
from time import monotonic
import test_host_control_custody as custody
from truss.execution import Ok
from truss._native_result_custody import NativeTextLimits

class HostControlDeadlineTests(custody.NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.boundary.run('SELECT 1')
        self.executor=custody.HostExecutor();self.tracker=custody.NativeTransactions(self.boundary)
        self.service=custody.NativeArbitration(self.executor)
        self.producer=custody.HostControlCustody(self.executor)
        self.session=custody.NativeHostSession(self.executor,self.tracker,self.service,control_producer=self.producer)
    baseline=custody.HostControlCustodyTests.baseline
    # Run inherited native control composition against the deadline-enabled gate.
    def clock(self,now):
        return patch('truss._native_deadline.monotonic_ns',side_effect=lambda:now[0])
    def test_actual_deferred_commit_stall_retains_original_unknown(self):
        self.baseline();self.session.begin()
        self.boundary.run("CREATE TEMP TABLE deadline_control_fixture(value int)")
        self.boundary.run("CREATE FUNCTION pg_temp.deadline_control_delay() RETURNS trigger LANGUAGE plpgsql AS 'BEGIN PERFORM pg_catalog.pg_sleep(2); RETURN NEW; END'")
        self.boundary.run("CREATE CONSTRAINT TRIGGER deadline_control_trigger AFTER INSERT ON deadline_control_fixture DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION pg_temp.deadline_control_delay()")
        self.boundary.run("INSERT INTO deadline_control_fixture VALUES(1)")
        self.producer.limits=NativeTextLimits(contexts=8,rows=8,columns=5,ordinary_ms=100)
        start=monotonic();result=self.session.commit();elapsed=monotonic()-start
        self.assertEqual(result.error.code,'commit_unknown')
        self.assertGreaterEqual(elapsed,0.08);self.assertLess(elapsed,1.5)
        ledger=self.producer._ledgers[-1]
        self.assertIsInstance(ledger.result_custody.ingress_deadline.failure,TimeoutError)
        self.assertFalse(ledger.calls[-1].native_call.capture_complete)
        self.assertIs(self.boundary._operation,ledger.token)
        self.assertTrue(self.boundary._quarantined)
        self.assertIsNone(self.connection._usock.gettimeout())
    def test_preacquisition_expiry_refuses_without_sql(self):
        now=[0];before=self.boundary.last_call
        original_reserve=self.session.recovery.reserve
        def reserve(*args):
            value=original_reserve(*args);now[0]=30000000000;return value
        with self.clock(now),patch.object(self.session.recovery,'reserve',side_effect=reserve):
            result=self.session.observe_host_resource_baseline()
        self.assertEqual(result.error.code,'cancelled')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        self.assertFalse(self.boundary._quarantined)
    def test_expired_adoption_publication_keeps_original_claim_and_guard(self):
        self.baseline();self.session.begin();now=[0]
        original=self.executor.adopt_transaction
        def adopt(*args,**kwargs):
            value=original(*args,**kwargs);now[0]=30000000000;return value
        with self.clock(now),patch.object(self.executor,'adopt_transaction',side_effect=adopt):
            result=self.session.adopt_transaction()
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertIsNotNone(self.boundary._operation)
        self.assertTrue(self.session._closed)
        self.assertEqual(self.tracker._state.generation.adoption.current.phase,'published')
    def test_successful_idle_baseline_and_end_share_sealed_clock(self):
        self.baseline();self.session.begin();self.session.rollback()
        for ledger in self.producer._ledgers:
            self.assertIs(ledger.completion.deadline_basis,ledger.deadline.accepted_basis)
            self.assertIsNotNone(ledger.result_custody.outbound.barrier)
    def test_detachment_expiry_preserves_known_rollback_with_unconfirmed_handback(self):
        from truss._native_result_custody import NativeResultCustody
        self.baseline();self.session.begin();now=[0];original=NativeResultCustody.detach
        def detach(gate):
            value=original(gate);now[0]=30000000000;return value
        with self.clock(now),patch.object(NativeResultCustody,'detach',side_effect=detach):
            result=self.session.rollback()
        self.assertEqual(result.value.state,'rolled_back')
        self.assertEqual(result.value.handback,'quarantined')
        self.assertIsNotNone(self.boundary._operation)
        self.assertIsNone(self.producer._ledgers[-1].completion)
    def test_no_captured_call_refuses_without_implicit_setup(self):
        connection=self.Connection(**self.kwargs)
        try:
            connection.run('SELECT 1')
            from truss._native_pg8000 import NativeBoundary
            boundary=NativeBoundary(connection)
            tracker=custody.NativeTransactions(boundary)
            session=custody.NativeHostSession(self.executor,tracker,self.service,control_producer=self.producer)
            result=session.observe_host_resource_baseline()
            self.assertEqual(result.error.code,'execution_obligation')
            self.assertIsNone(boundary.last_call)
            self.assertIsNone(boundary._operation)
            self.assertFalse(boundary._quarantined)
        finally:connection.close()
    def test_unqualified_host_error_refuses_without_retry_or_implicit_flush(self):
        self.baseline();self.session.begin()
        with self.assertRaises(Exception):self.boundary.run('SELECT 1/0')
        before=self.boundary.last_call
        result=self.session.rollback()
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(self.tracker._state.status,b'E')
        # Explicit trusted host settlement remains outside the bounded control claim.
        self.tracker.rollback()
    def test_expired_acquired_scope_before_submit_retains_original_token(self):
        self.baseline();before=self.boundary.last_call;now=[0];original=self.producer.attach
        def attach(*args):
            value=original(*args);now[0]=30000000000;return value
        with self.clock(now),patch.object(self.producer,'attach',side_effect=attach):
            result=self.session.begin()
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertIs(self.boundary.last_call,before)
        ledger=self.producer._ledgers[-1]
        self.assertEqual(ledger.calls,())
        self.assertIs(self.boundary._operation,ledger.token)
        self.assertIsNone(self.tracker._state.generation)
        self.assertTrue(self.session._closed)
    def deferred_abort(self):
        self.boundary.run('CREATE TEMP TABLE deadline_deferred(value int UNIQUE DEFERRABLE INITIALLY DEFERRED)')
        self.baseline();self.session.begin()
        self.boundary.run('INSERT INTO deadline_deferred VALUES(1),(1)')
        result=self.session.commit()
        self.assertEqual(result.value.state,'rolled_back')
        self.assertEqual(result.value.sql_state,'23505')
        self.assertEqual(result.value.handback,'released')
    def test_completed_error_control_barrier_allows_next_begin(self):
        from truss._native_outbound import successful_outbound_basis,confirmed_control_outbound_basis
        self.deferred_abort()
        self.assertFalse(successful_outbound_basis(self.boundary))
        self.assertTrue(confirmed_control_outbound_basis(self.boundary))
        self.assertIsInstance(self.session.begin(),Ok)
        self.assertIsInstance(self.session.rollback(),Ok)
    def test_missing_original_error_barrier_refuses_without_sql(self):
        self.deferred_abort();before=self.boundary.last_call
        gate=self.producer._ledgers[-1].result_custody
        barrier=gate.outbound.barrier;gate.outbound.barrier=None
        result=self.session.begin()
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        gate.outbound.barrier=barrier
        self.assertIsInstance(self.session.begin(),Ok)
        self.session.rollback()
    def test_effect_free_idle_adoption_preserves_original_error_send_witness(self):
        self.deferred_abort();witness=self.boundary._control_outbound_witness
        before=self.boundary.last_call
        self.assertEqual(self.session.adopt_transaction().error.code,'invalid_transaction')
        self.assertIs(self.boundary.last_call,before)
        self.assertIs(self.boundary._control_outbound_witness,witness)
        self.assertEqual(self.producer._ledgers[-1].calls,())
        self.assertIsInstance(self.session.begin(),Ok)
        self.session.rollback()
