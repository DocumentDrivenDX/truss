"""Original composed-call recovery facts, not graph receipt/recovery evidence."""
import gc
import unittest
import weakref
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._host_execution import HostExecutor
from truss._native_transactions import NativeTransactions
from truss._native_arbitration import NativeArbitration
from truss._host_session import NativeHostSession
from truss._host_control_custody import HostControlCustody
from truss._host_call_recovery import _CallReference
from truss.execution import Ok,Error

class HostCallRecoveryTests(NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.executor=HostExecutor();self.tracker=NativeTransactions(self.boundary)
        self.service=NativeArbitration(self.executor)
        self.producer=HostControlCustody(self.executor)
        self.session=NativeHostSession(self.executor,self.tracker,self.service,control_producer=self.producer)
        self.recovery=self.session.recovery

    def begin(self):
        self.assertIsInstance(self.session.observe_host_resource_baseline(),Ok)
        self.assertIsInstance(self.session.begin(),Ok)

    def observe(self,reference=None):
        result=self.recovery.observe(reference or self.session.last_call_reference)
        self.assertIsInstance(result,Ok,repr(result))
        return result.value

    def test_original_facts_survive_later_generation(self):
        self.begin();self.session.adopt_transaction();self.session.commit()
        reference=self.session.last_call_reference
        original=self.observe(reference)
        self.session.begin();self.session.adopt_transaction();self.session.rollback()
        self.assertEqual(self.observe(reference),original)
        self.assertEqual((original.custody,original.outcome.settlement),('released','committed'))
        self.assertIsNone(self.boundary._operation)

    def test_forged_foreign_and_subclass_references_refuse(self):
        self.begin();original=self.session.last_call_reference
        class Foreign(_CallReference):pass
        for reference in (object(),_CallReference(original._issuer,original._ordinal),Foreign(original._issuer,original._ordinal)):
            self.assertEqual(self.recovery.observe(reference).error.code,'invalid_transaction')
        other=HostExecutor()
        self.assertEqual(other._host_call_recovery.observe(original).error.code,'invalid_transaction')
        self.assertEqual(self.observe(original).custody,'released')

    def test_owner_custody_survives_facade_collection_and_disposal(self):
        self.begin();self.session.adopt_transaction();self.session.commit()
        reference=self.session.last_call_reference
        original=self.observe(reference)
        facade=weakref.ref(self.session)
        self.session=None;gc.collect();self.executor.dispose()
        self.assertIsNone(facade())
        self.assertIn(reference,self.recovery.references(self.boundary))
        self.assertEqual(self.recovery.observe(reference).value,original)

    def test_disposed_refusals_do_not_consume_host_rollback_capacity(self):
        self.begin()
        facade=NativeHostSession(self.executor,self.tracker,self.service,retained_calls=2,control_producer=self.producer)
        self.executor.dispose()
        before=self.boundary.last_call
        for _ in range(5):
            self.assertEqual(facade.observe_host_resource_baseline().error.code,'invalid_transaction')
            self.assertEqual(facade.adopt_transaction().error.code,'invalid_transaction')
        self.assertEqual(facade._calls,())
        self.assertIs(self.boundary.last_call,before)
        self.assertEqual(facade.rollback().value.state,'rolled_back')

    def test_disposal_linearizes_before_original_ordinary_reservation(self):
        self.begin()
        entered=Event();resume=Event();reserve=self.recovery.reserve
        def delayed(boundary,record):
            entered.set();self.assertTrue(resume.wait(5))
            return reserve(boundary,record)
        before=self.boundary.last_call
        with patch.object(self.recovery,'reserve',side_effect=delayed):
            with ThreadPoolExecutor(max_workers=1) as worker:
                future=worker.submit(self.session.adopt_transaction)
                self.assertTrue(entered.wait(5));self.executor.dispose();resume.set()
                result=future.result(timeout=5)
        self.assertEqual(result.error.code,'invalid_transaction')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(self.session.rollback().value.state,'rolled_back')

    def test_acquisition_window_is_conservative(self):
        self.session.observe_host_resource_baseline()
        acquired=Event();resume=Event();acquire=self.boundary.acquire_operation
        def paused(**kwargs):
            result=acquire(**kwargs);acquired.set();self.assertTrue(resume.wait(5));return result
        with patch.object(self.boundary,'acquire_operation',side_effect=paused):
            with ThreadPoolExecutor(max_workers=1) as worker:
                future=worker.submit(self.session.begin)
                self.assertTrue(acquired.wait(5))
                observation=self.observe()
                self.assertEqual((observation.phase,observation.custody),('acquiring','unresolved'))
                resume.set();self.assertIsInstance(future.result(timeout=5),Ok)
        self.assertEqual(self.observe().custody,'released')
        self.session.rollback()

    def test_ready_and_completion_do_not_prove_unpublished_handback(self):
        self.begin();entered=Event();resume=Event();handback=self.producer.handback
        def paused(ledger):
            entered.set();self.assertTrue(resume.wait(5));return handback(ledger)
        with patch.object(self.producer,'handback',side_effect=paused):
            with ThreadPoolExecutor(max_workers=1) as worker:
                future=worker.submit(self.session.commit)
                self.assertTrue(entered.wait(5))
                observation=self.observe()
                self.assertTrue(observation.native_complete)
                self.assertEqual(observation.outcome.settlement,'committed')
                self.assertEqual((observation.custody,observation.outcome.handback),('held','unresolved'))
                resume.set();self.assertEqual(future.result(timeout=5).value.state,'committed')
        self.assertEqual(self.observe().outcome.handback,'released')

    def test_summary_and_snapshot_allocation_faults_do_not_erase_native_commit(self):
        import truss._host_call_recovery as module
        self.begin()
        with patch.object(module,'CallOutcome',side_effect=MemoryError),patch.object(module,'CallObservation',side_effect=MemoryError):
            result=self.session.commit()
            self.assertEqual(result.value.state,'committed')
            self.assertEqual(self.recovery.observe(self.session.last_call_reference).error.code,'execution_obligation')
        self.assertEqual(self.observe().outcome.settlement,'committed')
        self.assertEqual(self.observe().custody,'released')

    def test_snapshot_publication_failure_retains_original_released_outcome(self):
        self.begin();publisher=self.recovery._publish_snapshot
        def fail(entry,facts):
            if facts.phase=='settled':raise MemoryError('Original diagnostic publication failed')
            return publisher(entry,facts)
        with patch.object(self.recovery,'_publish_snapshot',side_effect=fail):
            with self.assertRaises(MemoryError):self.session.commit()
        reference=self.recovery.references(self.boundary)[-1]
        observation=self.observe(reference)
        self.assertEqual((observation.custody,observation.outcome.settlement),('released','committed'))
        self.assertIsNone(self.boundary._operation)

    def test_acquisition_publication_failure_retains_unresolved_without_sql(self):
        publisher=self.recovery._publish_snapshot
        def fail(entry,facts):
            if facts.phase in ('in_flight','unresolved'):raise MemoryError('Original fact publication failed')
            return publisher(entry,facts)
        before=self.boundary.last_call
        with patch.object(self.recovery,'_publish_snapshot',side_effect=fail):
            with self.assertRaises(MemoryError):self.session.observe_host_resource_baseline()
        observation=self.observe(self.recovery.references(self.boundary)[-1])
        self.assertEqual((observation.phase,observation.custody),('unresolved','unresolved'))
        self.assertEqual(observation.outcome.code,'transaction_unusable')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNotNone(self.boundary._operation)

    def test_unknown_commit_is_retained_without_resubmission(self):
        self.begin();attach=self.producer.attach;original=self.connection.send_QUERY
        def intercepted(boundary,record):
            ledger=attach(boundary,record)
            def fail(sql):raise OSError('Original native send failed')
            self.connection.send_QUERY=fail
            return ledger
        try:
            with patch.object(self.producer,'attach',side_effect=intercepted):result=self.session.commit()
            self.assertEqual(result.error.code,'commit_unknown')
            before=self.boundary.last_call
            observation=self.observe()
            self.assertEqual((observation.outcome.code,observation.custody),('commit_unknown','unresolved'))
            self.assertFalse(observation.native_complete)
            self.assertIs(self.boundary.last_call,before)
        finally:self.connection.send_QUERY=original

    def test_refusal_lost_handback_does_not_capture_later_host_call(self):
        release=self.boundary.release_operation
        def lose(token,**options):
            release(token,**options)
            self.boundary.run("SELECT 'later'::pg_catalog.text")
            raise MemoryError('Lost release reply after later host work')
        with patch.object(self.boundary,'release_operation',side_effect=lose):result=self.session.begin()
        self.assertEqual(result.error.code,'execution_obligation')
        observation=self.observe()
        self.assertIsNone(observation.native_revision)
        self.assertIsNone(observation.native_complete)
        self.assertEqual(observation.custody,'released')

    def test_known_commit_with_unresolved_handback_is_inspectable(self):
        self.begin();publisher=self.boundary._publish_ownership
        def fail(root):
            publisher(root)
            pending=self.boundary._host_control_pending
            if pending is not None and root is pending.original_root:
                raise MemoryError('Restoration reply failed before release')
        with patch.object(self.boundary,'_publish_ownership',side_effect=fail):result=self.session.commit()
        self.assertEqual((result.value.state,result.value.handback),('committed','quarantined'))
        observation=self.observe()
        self.assertEqual((observation.outcome.settlement,observation.custody),('committed','unresolved'))
        self.assertEqual(observation.outcome.handback,'unresolved')
        self.assertIsNotNone(self.boundary._operation)

    def test_baseexception_lost_return_preserves_published_commit(self):
        self.begin();publisher=self.recovery._publish_snapshot
        def fail(entry,facts):
            if facts.phase=='settled':raise KeyboardInterrupt()
            return publisher(entry,facts)
        with patch.object(self.recovery,'_publish_snapshot',side_effect=fail):
            with self.assertRaises(KeyboardInterrupt):self.session.commit()
        observation=self.observe(self.recovery.references(self.boundary)[-1])
        self.assertEqual((observation.custody,observation.outcome.settlement),('released','committed'))

    def test_failed_acquisition_retains_effect_free_refusal(self):
        token=self.boundary.acquire_operation()
        before=self.boundary.last_call
        result=self.session.begin()
        observation=self.observe()
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertEqual((observation.phase,observation.custody),('refused','not_acquired'))
        self.assertEqual(observation.outcome.code,result.error.code)
        self.assertIs(self.boundary._operation,token)
        self.assertIs(self.boundary.last_call,before)
        self.boundary.release_operation(token)

    def test_observation_does_not_wait_for_boundary_lock(self):
        self.begin();reference=self.session.last_call_reference;before=self.boundary.last_call
        self.boundary._lock.acquire()
        try:result=self.recovery.observe(reference)
        finally:self.boundary._lock.release()
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
        self.assertEqual(self.observe(reference).custody,'released')

    def test_disposal_preserves_already_admitted_completion(self):
        self.begin();entered=Event();resume=Event();handback=self.producer.handback
        def paused(ledger):
            entered.set();self.assertTrue(resume.wait(5));return handback(ledger)
        with patch.object(self.producer,'handback',side_effect=paused):
            with ThreadPoolExecutor(max_workers=1) as worker:
                future=worker.submit(self.session.commit)
                self.assertTrue(entered.wait(5));self.executor.dispose();resume.set()
                self.assertEqual(future.result(timeout=5).value.state,'committed')
        self.assertEqual(self.observe().custody,'released')
        before=self.boundary.last_call
        self.assertEqual(self.session.adopt_transaction().error.code,'invalid_transaction')
        self.assertIs(self.boundary.last_call,before)
