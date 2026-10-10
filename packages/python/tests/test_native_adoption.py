"""Original native claim transitions; no full E06/resource qualification."""
import unittest
from unittest.mock import patch
from truss.execution import Ok, Error
from truss._host_execution import HostExecutor
from truss._native_transactions import NativeTransactions
from truss import _native_adoption as claims
from test_native_pg8000 import NativeBoundaryFixture


class NativeAdoptionTests(NativeBoundaryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.t = NativeTransactions(self.boundary)
        self.t.begin()
        self.token = self.boundary.acquire_operation()
        self.port = self.t.port(self.token)

    def adopt(self, executor, port=None, isolation='read_committed'):
        return executor.adopt_transaction(port or self.port, isolation=isolation, access_mode='read_write')

    def test_two_executors_share_original_claim_without_second_sql(self):
        a, b = HostExecutor(), HostExecutor()
        first = self.adopt(a)
        self.assertIsInstance(first, Ok)
        original = self.boundary.last_call
        second = self.adopt(b, self.t.port(self.token))
        self.assertIsInstance(second, Error)
        self.assertEqual(second.error.code, 'invalid_transaction')
        self.assertIs(self.boundary.last_call, original)
        self.assertIsInstance(a.savepoint(first.value), Ok)
        self.assertEqual(len(a._transactions), 1)
        self.assertEqual(b._transactions, {})

    def test_competing_claim_refuses_before_observation(self):
        from threading import Event, Thread
        entered, proceed = Event(), Event()
        original = self.port._observe_for_adoption
        result = []
        def paused(claim):
            entered.set()
            if not proceed.wait(5): raise RuntimeError('Test synchronization timeout')
            return original(claim)
        a, b = HostExecutor(), HostExecutor()
        with patch.object(self.port, '_observe_for_adoption', side_effect=paused):
            thread = Thread(target=lambda: result.append(self.adopt(a)))
            thread.start()
            try:
                self.assertTrue(entered.wait(5))
                previous = self.boundary.last_call
                self.assertIsInstance(self.adopt(b, self.t.port(self.token)), Error)
                self.assertIs(self.boundary.last_call, previous)
            finally:
                proceed.set()
                thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertIsInstance(result[0], Ok)

    def test_known_profile_mismatch_refunds_exact_claim_with_history(self):
        a, b = HostExecutor(), HostExecutor()
        self.assertEqual(self.adopt(a, isolation='serializable').error.code, 'invalid_transaction')
        root = self.t._state.generation.adoption
        self.assertIsNone(root.current)
        self.assertEqual(root.retained[0].phase, 'profile_refused')
        self.assertEqual(a._transactions, {})
        self.assertIsInstance(self.adopt(b), Ok)
        self.assertEqual(len(self.t._state.generation.adoption.retained), 1)

    def test_intervening_same_token_command_prevents_publication_and_refund(self):
        original = self.port._observe_for_adoption
        def changed(claim):
            observation = original(claim)
            self.boundary.run('SET LOCAL application_name=changed_revision', token=self.token)
            return observation
        a, b = HostExecutor(), HostExecutor()
        with patch.object(self.port, '_observe_for_adoption', side_effect=changed):
            result = self.adopt(a, isolation='serializable')
        self.assertEqual(result.error.code, 'transaction_unusable')
        root = self.t._state.generation.adoption
        self.assertEqual(root.current.phase, 'unresolved')
        self.assertIsNotNone(root.current.native_observation)
        self.assertLess(root.current.native_observation.revision, self.boundary._revision)
        previous = self.boundary.last_call
        self.assertIsInstance(self.adopt(b), Error)
        self.assertIs(self.boundary.last_call, previous)

    def test_observation_failure_retains_original_claim(self):
        a = HostExecutor()
        with patch.object(self.port, '_observe_for_adoption', side_effect=OSError('Injected observation loss')):
            self.assertEqual(self.adopt(a).error.code, 'transaction_unusable')
        root = self.t._state.generation.adoption
        self.assertEqual(root.current.phase, 'unresolved')
        self.assertIs(root.current.claim.executor, a)
        self.assertIs(root.current.claim.port, self.port)
        self.assertFalse(root.current.claim.custody.usable)
        a.dispose()
        self.assertIs(self.t._state.generation.adoption, root)
        self.assertIsInstance(self.adopt(HostExecutor()), Error)

    def test_before_and_after_executor_insertion_faults_keep_inert_custody(self):
        class FaultIndex(dict):
            def __init__(self, after): super().__init__(); self.after = after
            def __setitem__(self, key, value):
                if self.after: super().__setitem__(key, value)
                raise MemoryError('Injected executor insertion publication failure')
        # Independent original generation for each publication window.
        for after in (False, True):
            if self.t._state.generation.adoption is not None:
                self.boundary.release_operation(self.token)
                self.t.rollback()
                self.t.begin()
                self.token = self.boundary.acquire_operation()
                self.port = self.t.port(self.token)
            a = HostExecutor()
            a._transactions = FaultIndex(after)
            self.assertEqual(self.adopt(a).error.code, 'transaction_unusable')
            record = self.t._state.generation.adoption.current
            self.assertEqual(record.phase, 'unresolved')
            self.assertIsNotNone(record.native_observation)
            self.assertEqual(len(a._transactions), int(after))
            self.assertFalse(record.claim.custody.usable)
            self.assertIsInstance(a.savepoint(record.claim.custody.handle), Error)
            self.assertIsInstance(self.adopt(HostExecutor()), Error)

    def test_native_final_publication_fault_preserves_original_decision(self):
        original = claims._publish_root
        a = HostExecutor()
        def fail_after_publish(generation, root):
            original(generation, root)
            if root.current is not None and root.current.phase == 'published':
                raise MemoryError('Injected lost published adoption reply')
        with patch.object(claims, '_publish_root', side_effect=fail_after_publish):
            result = self.adopt(a)
            self.assertIsInstance(result, Ok)
        record = self.t._state.generation.adoption.current
        self.assertEqual(record.phase, 'published')
        self.assertIs(result, record.claim.success)
        self.assertIs(a._original_custody(record.claim.custody.handle), record.claim.custody)
        self.assertIsInstance(self.adopt(HostExecutor()), Error)

    def test_disposal_during_observation_never_refunds_claim(self):
        a = HostExecutor()
        original = self.port._observe_for_adoption
        def disposed(claim):
            value = original(claim)
            a.dispose()
            return value
        with patch.object(self.port, '_observe_for_adoption', side_effect=disposed):
            self.assertEqual(self.adopt(a).error.code, 'transaction_unusable')
        self.assertEqual(self.t._state.generation.adoption.current.phase, 'unresolved')
        self.assertIsInstance(self.adopt(HostExecutor()), Error)

    def test_confirmed_end_allows_another_executor_on_new_generation(self):
        a = HostExecutor()
        h = self.adopt(a).value
        original_generation = self.t._state.generation
        original_record = original_generation.adoption.current
        self.boundary.release_operation(self.token)
        self.t.commit()
        self.t.begin()
        self.token = self.boundary.acquire_operation()
        self.port = self.t.port(self.token)
        self.assertIsInstance(self.adopt(HostExecutor()), Ok)
        self.assertTrue(original_generation.ended)
        self.assertIs(original_generation.adoption.current, original_record)
        self.assertIs(a._original_custody(h), original_record.claim.custody)

    def test_refusal_history_capacity_is_conjunctive_before_observation(self):
        self.t._adoption_limit = 1
        self.assertIsInstance(self.adopt(HostExecutor(), isolation='serializable'), Error)
        original = self.boundary.last_call
        self.assertIsInstance(self.adopt(HostExecutor()), Error)
        self.assertIs(self.boundary.last_call, original)

    def test_lost_reservation_reply_retains_exact_original_claim_without_sql(self):
        original = claims._publish_root
        a = HostExecutor()
        previous = self.boundary.last_call
        def lost(generation, root):
            original(generation, root)
            if root.current is not None and root.current.phase == 'observing':
                raise MemoryError('Injected lost reservation reply')
        with patch.object(claims, '_publish_root', side_effect=lost):
            self.assertEqual(self.adopt(a).error.code, 'transaction_unusable')
        self.assertIs(self.boundary.last_call, previous)
        record = self.t._state.generation.adoption.current
        self.assertEqual(record.phase, 'unresolved')
        self.assertIs(record.claim.executor, a)
        self.assertFalse(record.claim.custody.usable)
        self.assertIsInstance(self.adopt(HostExecutor()), Error)

    def test_pre_final_publication_failure_cannot_admit_partial_index(self):
        original = claims._publish_root
        a = HostExecutor()
        def refused(generation, root):
            if root.current is not None and root.current.phase == 'published':
                raise MemoryError('Injected pre-final native publication failure')
            original(generation, root)
        with patch.object(claims, '_publish_root', side_effect=refused):
            self.assertEqual(self.adopt(a).error.code, 'transaction_unusable')
        record = self.t._state.generation.adoption.current
        self.assertEqual(record.phase, 'unresolved')
        self.assertIs(a._original_custody(record.claim.custody.handle), record.claim.custody)
        previous = self.boundary.last_call
        self.assertIsInstance(a.savepoint(record.claim.custody.handle), Error)
        self.assertIs(self.boundary.last_call, previous)
        self.assertIsInstance(self.adopt(HostExecutor()), Error)

    def test_fatal_observation_interruption_retains_original_claim(self):
        a = HostExecutor()
        with patch.object(self.port, '_observe_for_adoption', side_effect=KeyboardInterrupt('Injected cancellation')):
            with self.assertRaises(KeyboardInterrupt): self.adopt(a)
        record = self.t._state.generation.adoption.current
        self.assertEqual(record.phase, 'unresolved')
        self.assertFalse(record.claim.custody.usable)
        self.assertIsInstance(self.adopt(HostExecutor()), Error)

    def test_second_observation_cannot_erase_original_claim_evidence(self):
        original = self.port._observe_for_adoption
        records = []
        def twice(claim):
            value = original(claim)
            records.append(self.port._last_native_observation)
            self.port.observe()
            return value
        with patch.object(self.port, '_observe_for_adoption', side_effect=twice):
            self.assertEqual(self.adopt(HostExecutor()).error.code, 'transaction_unusable')
        record = self.t._state.generation.adoption.current
        self.assertEqual(record.phase, 'unresolved')
        self.assertIs(record.native_observation, records[0])
        self.assertIs(record.claim.capture.native, records[0])
        self.assertIsNot(record.native_observation, self.port._last_native_observation)
        self.assertLess(record.native_observation.revision, self.boundary._revision)
        self.assertEqual(record.native_observation.person, 'postgres')

    def test_lost_profile_refund_reply_preserves_terminal_original_refusal(self):
        original = claims._publish_root
        a = HostExecutor()
        def lost(generation, root):
            original(generation, root)
            if root.current is None and root.retained:
                raise MemoryError('Injected lost profile refusal reply')
        with patch.object(claims, '_publish_root', side_effect=lost):
            result = self.adopt(a, isolation='serializable')
        root = self.t._state.generation.adoption
        self.assertIsNone(root.current)
        self.assertIs(result, root.retained[0].claim.refusal)
        self.assertEqual(result.error.code, 'invalid_transaction')
        self.assertIsInstance(self.adopt(HostExecutor()), Ok)

    def test_unindexed_failed_custody_retained_after_generation_end_and_gc(self):
        import gc, weakref
        a = HostExecutor()
        with patch.object(self.port, '_observe_for_adoption', side_effect=OSError('Injected pre-index failure')):
            self.assertIsInstance(self.adopt(a), Error)
        generation_ref = weakref.ref(self.t._state.generation)
        port_ref = weakref.ref(self.port)
        self.port = None
        self.boundary.release_operation(self.token)
        self.t.rollback()
        self.t.begin()
        self.boundary.run('SELECT 1')
        gc.collect()
        self.assertIsNotNone(generation_ref())
        self.assertIsNotNone(port_ref())
        claim = a._native_claims[0]
        self.assertIs(claim.generation, generation_ref())
        self.assertIs(claim.port, port_ref())
        self.assertEqual(claim.generation.adoption.current.phase, 'unresolved')
        self.assertTrue(claim.generation.ended)
        self.assertEqual(a._transactions, {})

    def test_before_reservation_publication_fault_is_retained_without_sql(self):
        original = claims._publish_root
        a = HostExecutor()
        previous = self.boundary.last_call
        def lost(generation, root):
            if root.current is not None and root.current.phase == 'observing':
                raise MemoryError('Injected pre-reservation root failure')
            original(generation, root)
        with patch.object(claims, '_publish_root', side_effect=lost):
            self.assertEqual(self.adopt(a).error.code, 'transaction_unusable')
        self.assertIsNone(self.t._state.generation.adoption)
        self.assertIs(self.boundary.last_call, previous)
        self.assertIs(a._native_claims[0], self.t._adoption_custody[0])
        self.assertTrue(a._native_claims[0].capture.reservation_failed)
        self.assertIsInstance(self.adopt(HostExecutor()), Ok)

    def test_executor_retention_limit_refuses_before_original_observation(self):
        a = HostExecutor()
        a._native_claim_limit = 1
        self.assertIsInstance(self.adopt(a, isolation='serializable'), Error)
        previous = self.boundary.last_call
        self.assertIsInstance(self.adopt(a), Error)
        self.assertIs(self.boundary.last_call, previous)
        self.assertIsInstance(self.adopt(HostExecutor()), Ok)

    def test_unrelated_observer_cannot_consume_original_adoption_probe(self):
        original = self.port._observe_for_adoption
        unrelated = []
        def before_probe(claim):
            self.port.observe()
            unrelated.append(self.port._last_native_observation)
            self.assertIsNone(claim.capture.native)
            self.assertIsNone(claim.capture.probe_revision)
            return original(claim)
        a = HostExecutor()
        with patch.object(self.port, '_observe_for_adoption', side_effect=before_probe):
            result = self.adopt(a)
        self.assertIsInstance(result, Ok)
        record = self.t._state.generation.adoption.current
        self.assertIsNot(record.native_observation, unrelated[0])
        self.assertGreater(record.native_observation.revision, unrelated[0].revision)
        self.assertEqual(record.claim.capture.probe_revision, record.native_observation.revision)
