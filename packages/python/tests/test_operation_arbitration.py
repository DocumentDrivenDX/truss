import unittest
from threading import Event, Thread
from truss._host_execution import HostExecutor
from truss._operation_arbitration import OperationArbitration, ArbitrationLimits, CompletionDecision, Prepared, Admitted, Refused, Unresolved
from test_host_execution import Port

class OperationArbitrationTests(unittest.TestCase):
    def setup_registry(self, verify=None, limits=None):
        executor=HostExecutor();port=Port()
        handle=executor.adopt_transaction(port,isolation='repeatable_read',access_mode='read_write').value
        def completed(evidence,context):return CompletionDecision('caller_idle',context,True,True)
        registry=OperationArbitration(executor,verify or completed,limits=limits)
        a,b=object(),object();self.assertEqual(registry.register(a),'registered');self.assertEqual(registry.register(b),'registered')
        return registry,a,b,executor,port,handle
    def test_prepare_and_observe_are_inert_and_never_acquire(self):
        r,a,b,e,p,h=self.setup_registry()
        def forbidden():raise AssertionError('Native observation during preparation')
        p.observe=forbidden
        attempt=r.prepare(a,h).attempt
        self.assertIsInstance(r.observe(attempt),Unresolved)
        self.assertEqual(p.commands,[])
        first=r.acquire(attempt);self.assertIsInstance(first,Admitted)
        self.assertIs(r.acquire(attempt),first);self.assertIs(r.observe(attempt),first)
    def test_shared_transaction_busy_is_terminal_even_after_release(self):
        r,a,b,e,p,h=self.setup_registry();one=r.prepare(a,h).attempt;two=r.prepare(b,h).attempt
        lease=r.acquire(one).lease;busy=r.acquire(two)
        self.assertEqual(busy.reason,'busy');self.assertEqual(r.release(lease,b'original-complete'),'released')
        self.assertIs(r.acquire(two),busy);self.assertIsInstance(r.acquire(r.prepare(b,h).attempt),Admitted)
    def test_old_completion_cannot_release_new_owner(self):
        r,a,b,e,p,h=self.setup_registry();one=r.prepare(a,h).attempt;lease=r.acquire(one).lease
        self.assertEqual(r.release(lease,b'one'),'released');two=r.prepare(b,h).attempt;new=r.acquire(two).lease
        self.assertEqual(r.release(lease,b'one'),'released');self.assertIsInstance(r.release(lease,b'other'),Unresolved)
        self.assertEqual(r.acquire(r.prepare(a,h).attempt).reason,'busy')
        self.assertEqual(r.release(new,b'two'),'released');self.assertIsInstance(r.acquire(one),Refused)
    def test_uncertain_completion_retains_slot_and_custody_after_close(self):
        def unknown(*args):raise OSError('lost outcome')
        r,a,b,e,p,h=self.setup_registry(unknown);attempt=r.prepare(a,h).attempt;lease=r.acquire(attempt).lease
        result=r.release(lease,b'original');self.assertIsInstance(result,Unresolved)
        r.close_admission(a);self.assertEqual(r.release(lease,b'original'),result)
        self.assertEqual(r.acquire(r.prepare(b,h).attempt).reason,'busy')
    def test_close_abandons_prepared_only_and_preserves_other_assembly(self):
        r,a,b,e,p,h=self.setup_registry();one=r.prepare(a,h).attempt;two=r.prepare(b,h).attempt
        r.close_admission(a);self.assertIsInstance(r.acquire(one),Refused);self.assertEqual(r.abandon_prepared(one),'abandoned')
        self.assertIsInstance(r.acquire(two),Admitted);self.assertEqual(r.prepare(a,h).reason,'disposed')
    def test_verifier_runs_outside_lock_while_ownership_remains_held(self):
        entered,finish=Event(),Event()
        def verify(evidence,context):
            entered.set();self.assertTrue(finish.wait(2));return CompletionDecision('caller_idle',context,True,True)
        r,a,b,e,p,h=self.setup_registry(verify);lease=r.acquire(r.prepare(a,h).attempt).lease
        results=[];worker=Thread(target=lambda:results.append(r.release(lease,b'original')));worker.start()
        try:
            self.assertTrue(entered.wait(2));self.assertEqual(r.acquire(r.prepare(b,h).attempt).reason,'busy')
        finally:finish.set();worker.join(2)
        self.assertFalse(worker.is_alive());self.assertEqual(results,['released'])
    def test_unusable_caller_does_not_release_and_ended_invalidates_handles(self):
        r,a,b,e,p,h=self.setup_registry();lease=r.acquire(r.prepare(a,h).attempt).lease
        e._original_custody(h).usable=False;self.assertIsInstance(r.release(lease,b'original'),Unresolved)
        def ended(evidence,context):return CompletionDecision('transaction_ended',context,True,True)
        r,a,b,e,p,h=self.setup_registry(ended);lease=r.acquire(r.prepare(a,h).attempt).lease
        self.assertEqual(r.release(lease,b'end'),'released');self.assertEqual(e.savepoint(h).error.code,'invalid_transaction')
    def test_duplicate_registry_for_exact_executor_refuses(self):
        r,a,b,e,p,h=self.setup_registry()
        with self.assertRaises(ValueError):OperationArbitration(e,lambda *args:None)

    def test_prior_completion_context_cannot_release_later_lease(self):
        originals={}
        def verify(evidence,context):
            return CompletionDecision('caller_idle',originals.setdefault(evidence,context),True,True)
        r,a,b,e,p,h=self.setup_registry(verify)
        first=r.acquire(r.prepare(a,h).attempt).lease
        self.assertEqual(r.release(first,b'original'),'released')
        later=r.acquire(r.prepare(b,h).attempt).lease
        self.assertIsInstance(r.release(later,b'original'),Unresolved)
        self.assertEqual(r.acquire(r.prepare(a,h).attempt).reason,'busy')

    def test_before_and_after_root_publication_faults_keep_single_owner(self):
        for after in (False,True):
            r,a,b,e,p,h=self.setup_registry();attempt=r.prepare(a,h).attempt
            publish=r._publish
            def fault(root):
                if after:publish(root)
                raise MemoryError('publication fault')
            r._publish=fault
            with self.assertRaises(MemoryError):r.acquire(attempt)
            r._publish=publish
            original=r.observe(attempt)
            if after:
                self.assertIsInstance(original,Admitted)
                self.assertEqual(r.acquire(r.prepare(b,h).attempt).reason,'busy')
            else:
                self.assertIsInstance(original,Unresolved)
                self.assertIsInstance(r.acquire(attempt),Admitted)

    def test_explicit_reconciliation_after_verifier_recovery(self):
        available=[False]
        def verify(evidence,context):
            if not available[0]:raise OSError('temporarily unavailable')
            return CompletionDecision('caller_idle',context,True,True)
        r,a,b,e,p,h=self.setup_registry(verify);lease=r.acquire(r.prepare(a,h).attempt).lease
        self.assertIsInstance(r.release(lease,b'original'),Unresolved)
        available[0]=True
        self.assertEqual(r.release(lease,b'original'),'released')
        self.assertIsInstance(r.acquire(r.prepare(b,h).attempt),Admitted)

    def test_release_publication_faults_reconcile_without_stranding(self):
        for window in ('entered','closure'):
            r,a,b,e,p,h=self.setup_registry();attempt=r.prepare(a,h).attempt;lease=r.acquire(attempt).lease
            publish=r._publish;calls=[0]
            def fault(root):
                calls[0]+=1
                if window=='entered' and calls[0]==1:
                    publish(root);raise MemoryError('reply after entering verification')
                if window=='closure' and calls[0]==2:
                    raise MemoryError('before closure publication')
                publish(root)
            r._publish=fault
            with self.assertRaises(MemoryError):r.release(lease,b'original')
            r._publish=publish
            self.assertEqual(r.acquire(r.prepare(b,h).attempt).reason,'busy')
            self.assertEqual(r.release(lease,b'original'),'released')
            self.assertIsInstance(r.acquire(r.prepare(b,h).attempt),Admitted)

    def test_ended_commit_unknown_closes_slot_but_retains_original_recovery(self):
        def ended(evidence,context):return CompletionDecision('transaction_ended',context,True,True,('original-commit-recovery',))
        r,a,b,e,p,h=self.setup_registry(ended);attempt=r.prepare(a,h).attempt;lease=r.acquire(attempt).lease
        self.assertEqual(r.release(lease,b'original'),'released')
        self.assertIn('original-commit-recovery',r._root.entries[attempt].recovery)
        self.assertNotIn(h,r._root.active)
        self.assertEqual(e.savepoint(h).error.code,'invalid_transaction')

    def test_invalid_or_oversized_ended_recovery_is_not_dropped(self):
        for refs in [(42,), ('x'*129,), tuple(str(i) for i in range(33)), ('',), ('\ud800',)]:
            def verify(evidence,context):return CompletionDecision('transaction_ended',context,True,True,refs)
            r,a,b,e,p,h=self.setup_registry(verify);attempt=r.prepare(a,h).attempt;lease=r.acquire(attempt).lease
            self.assertIsInstance(r.release(lease,b'original'),Unresolved)
            self.assertIsNone(r._root.entries[attempt].verification.observed)
            self.assertEqual(r.acquire(r.prepare(b,h).attempt).reason,'busy')

    def test_recovery_budget_admission_precedes_retained_result(self):
        refs=('a'*128,'b'*128,'c'*128)
        def verify(evidence,context):return CompletionDecision('transaction_ended',context,True,True,refs)
        r,a,b,e,p,h=self.setup_registry(verify,ArbitrationLimits(metadata_bytes=500))
        attempt=r.prepare(a,h).attempt;lease=r.acquire(attempt).lease
        self.assertIsInstance(r.release(lease,b'original'),Unresolved)
        self.assertIsNone(r._root.entries[attempt].verification.observed)

    def test_resource_reservation_and_terminal_retention(self):
        limits=ArbitrationLimits(attempts=1,prepared=1,registry_bytes=69632)
        r,a,b,e,p,h=self.setup_registry(limits=limits);attempt=r.prepare(a,h).attempt
        self.assertEqual(r.prepare(b,h).reason,'resource');r.abandon_prepared(attempt)
        self.assertEqual(r.prepare(b,h).reason,'resource');self.assertEqual(r.acquire(attempt).reason,'invalid_transaction')
        with self.assertRaises(ValueError):ArbitrationLimits(attempts=True)
    def test_recovery_or_incomplete_ledger_prevents_release(self):
        for decision in [lambda c:CompletionDecision('caller_idle',c,False,True),
                         lambda c:CompletionDecision('caller_idle',c,True,True,('commit-unknown',)),
                         lambda c:CompletionDecision('caller_idle',object(),True,True)]:
            r,a,b,e,p,h=self.setup_registry(lambda evidence,c:decision(c));lease=r.acquire(r.prepare(a,h).attempt).lease
            self.assertIsInstance(r.release(lease,b'original'),Unresolved)
