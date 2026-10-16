"""Persistent private adoption signal; original native custody remains authoritative."""
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Thread
from unittest.mock import patch
import test_host_control_custody as custody
from truss import _native_adoption as claims
from truss._native_operation import NativeOperationRunner
from truss._native_cancellation import NativeCancellation
from truss.execution import Ok,Error

class AdoptionCancellationTests(custody.NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        super().setUp();self.connection._usock.settimeout(2)
        self.boundary.run('CREATE TEMP TABLE adoption_cancel_fixture(value text PRIMARY KEY)')
        self.executor=custody.HostExecutor();self.tracker=custody.NativeTransactions(self.boundary)
        self.service=custody.NativeArbitration(self.executor)
        self.producer=custody.HostControlCustody(self.executor)
        self.session=custody.NativeHostSession(self.executor,self.tracker,self.service,control_producer=self.producer)
        self.assertIsInstance(self.session.observe_host_resource_baseline(),Ok)
        self.assertIsInstance(self.session.begin(),Ok)
        self.signal=self.executor.cancellation()
    def adopt(self):return self.session.adopt_transaction(cancellation=self.signal)
    def runner(self):
        r=NativeOperationRunner(self.service)
        return r,r.register('SELECT :value::pg_catalog.text','SELECT')
    def test_pre_cancelled_adoption_runs_no_sql(self):
        self.signal.request();before=self.boundary.last_call
        result=self.adopt()
        self.assertEqual(result.error.code,'cancelled')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.tracker._state.generation.adoption)
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_cancel_between_shows_retains_partial_original_cancelled_claim(self):
        original=self.boundary._call
        def call(*args,**kwargs):
            value=original(*args,**kwargs)
            if any(e.code==b'C' and e.payload==b'SHOW\0' for e in self.boundary.last_call.events):self.signal.request()
            return value
        with patch.object(self.boundary,'_call',side_effect=call):result=self.adopt()
        self.assertEqual(result.error.code,'cancelled')
        claim=self.tracker._state.generation.adoption.current
        self.assertEqual(claim.phase,'cancelled')
        self.assertEqual(len(claim.claim.capture.profile_checks),1)
        self.assertIsNone(claim.claim.capture.native)
        self.assertIsNone(claim.native_observation)
        before=self.boundary.last_call
        self.assertEqual(self.session.adopt_transaction().error.code,'invalid_transaction')
        self.assertIs(self.boundary.last_call,before)
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_cancel_before_handle_publication_returns_original_cancelled(self):
        original=claims.capture_original
        def captured(*args):
            value=original(*args);self.signal.request();return value
        with patch.object(claims,'capture_original',side_effect=captured):result=self.adopt()
        self.assertEqual(result.error.code,'cancelled')
        root=self.tracker._state.generation.adoption
        self.assertEqual(root.current.phase,'cancelled')
        self.assertIsNotNone(root.current.native_observation)
        self.assertEqual(self.executor._transactions,{})
    def test_handle_publication_wins_preserving_ok_with_latched_context(self):
        original=claims._publish_root
        def publish(generation,root):
            value=original(generation,root)
            if root.current is not None and root.current.phase=='published':self.signal.request()
            return value
        with patch.object(claims,'_publish_root',side_effect=publish):result=self.adopt()
        self.assertIsInstance(result,Ok)
        r,s=self.runner();before=self.boundary.last_call
        self.assertEqual(r.execute(result.value,s,{'value':'blocked'}).error.code,'cancelled')
        self.assertIs(self.boundary.last_call,before)
    def test_active_cancel_contains_but_does_not_reopen_context(self):
        tx=self.adopt().value;r,s=self.runner()
        self.boundary.run("INSERT INTO adoption_cancel_fixture VALUES('before')")
        sql='SELECT :value::pg_catalog.text FROM pg_catalog.pg_sleep(1.5)'
        with patch.dict(r.QUALIFIED_STATEMENTS,{sql:'SELECT'}):slow=r.register(sql,'SELECT')
        submitted=Event();original=NativeCancellation._submitted
        def ready(child):original(child);submitted.set()
        with patch.object(NativeCancellation,'_submitted',ready):
            with ThreadPoolExecutor(max_workers=1) as worker:
                future=worker.submit(r.execute,tx,slow,{'value':'slow'})
                self.assertTrue(submitted.wait(2));self.signal.request();result=future.result(timeout=4)
        self.assertEqual(result.error.code,'cancelled')
        self.assertEqual(self.tracker._state.status,b'T')
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(self.boundary.run('SELECT value FROM adoption_cancel_fixture'),[['before']])
        before=self.boundary.last_call
        self.assertEqual(r.execute(tx,s,{'value':'blocked'}).error.code,'cancelled')
        self.assertEqual(self.session.savepoint(tx).error.code,'cancelled')
        attempt=self.service.registry.prepare(r._assembly,tx)
        self.assertEqual(attempt.reason,'cancelled')
        self.assertIs(self.boundary.last_call,before)
        self.assertEqual(self.session.commit().value.state,'committed')
    def test_late_request_preserves_success_and_exact_savepoint_cleanup(self):
        tx=self.adopt().value;sp=self.session.savepoint(tx).value;r,s=self.runner()
        result=r.execute(tx,s,{'value':'ok'})
        self.assertIsInstance(result,Ok)
        self.assertEqual(self.signal.request(),'latched')
        before=self.boundary.last_call
        self.assertEqual(r.execute(tx,s,{'value':'blocked'}).error.code,'cancelled')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsInstance(self.session.rollback_to_savepoint(tx,sp),Ok)
        self.assertIsInstance(self.session.release_savepoint(tx,sp),Ok)
        self.assertEqual(result.value,(('ok',),))
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_cancelled_terminal_lost_reply_retains_original_outcome(self):
        original=self.boundary._call;publish=claims._publish_root
        def call(*args,**kwargs):
            value=original(*args,**kwargs);self.signal.request();return value
        def lost(generation,root):
            publish(generation,root)
            if root.current is not None and root.current.phase=='cancelled':raise OSError('Lost reply')
        with patch.object(self.boundary,'_call',side_effect=call),patch.object(claims,'_publish_root',side_effect=lost):result=self.adopt()
        self.assertEqual(result.error.code,'cancelled')
        self.assertIs(result,self.tracker._state.generation.adoption.current.claim.cancelled)
    def test_profile_refund_wins_before_late_request(self):
        publish=claims._publish_root
        def root(generation,value):
            publish(generation,value)
            if value.current is None and value.retained:self.signal.request()
        with patch.object(claims,'_publish_root',side_effect=root):
            result=self.session.adopt_transaction(isolation='serializable',cancellation=self.signal)
        self.assertEqual(result.error.code,'invalid_transaction')
        self.assertEqual(self.tracker._state.generation.adoption.retained[-1].phase,'profile_refused')
        self.assertIsInstance(self.session.adopt_transaction(),Ok)
    def test_foreign_signal_refuses_without_sql(self):
        signal=custody.HostExecutor().cancellation();before=self.boundary.last_call
        self.assertEqual(self.session.adopt_transaction(cancellation=signal).error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.tracker._state.generation.adoption)
    def test_cancelled_context_foreign_cleanup_refuses_without_observation(self):
        tx=self.adopt().value;self.signal.request();before=self.boundary.last_call
        self.assertEqual(self.session.rollback_to_savepoint(tx,object()).error.code,'invalid_transaction')
        self.assertEqual(self.session.release_savepoint(tx,object()).error.code,'invalid_transaction')
        self.assertIs(self.boundary.last_call,before)
    def test_dispatch_failure_remains_unusable_and_retains_native_custody(self):
        tx=self.adopt().value;r,s=self.runner();submitted=Event()
        sql='SELECT :value::pg_catalog.text FROM pg_catalog.pg_sleep(1.5)'
        with patch.dict(r.QUALIFIED_STATEMENTS,{sql:'SELECT'}):slow=r.register(sql,'SELECT')
        original=NativeCancellation._submitted
        def ready(child):original(child);submitted.set()
        with patch.object(NativeCancellation,'_submitted',ready),patch.object(NativeCancellation,'_send',side_effect=OSError('Dispatch unavailable')):
            with ThreadPoolExecutor(max_workers=1) as worker:
                future=worker.submit(r.execute,tx,slow,{'value':'slow'})
                self.assertTrue(submitted.wait(2));self.signal.request();result=future.result(timeout=4)
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(self.boundary._quarantined)
        self.assertIsNotNone(self.boundary._operation)
        before=self.boundary.last_call
        self.assertEqual(self.session.savepoint(tx).error.code,'transaction_unusable')
        self.assertEqual(r.execute(tx,s,{'value':'blocked'}).error.code,'transaction_unusable')
        self.assertIs(self.boundary.last_call,before)

    def test_savepoint_request_after_observation_submits_no_savepoint(self):
        tx=self.adopt().value;port=self.executor._original_custody(tx).port
        observe=port.observe
        def requested():
            result=observe();self.signal.request();return result
        with patch.object(port,'observe',side_effect=requested):result=self.session.savepoint(tx)
        self.assertEqual(result.error.code,'cancelled')
        self.assertEqual(self.tracker._state.savepoints,())
        self.assertTrue(self.executor._original_custody(tx).usable)
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_lost_acquisition_reply_reconciles_after_context_latch(self):
        tx=self.adopt().value;r,s=self.runner()
        attempt=self.service.registry.prepare(r._assembly,tx).attempt
        token=self.boundary.acquire_operation()
        self.executor._original_custody(tx).port.bind_operation(token)
        original=self.service.registry._publish
        def lost(root):
            original(root);raise MemoryError('Lost acquired reply')
        with patch.object(self.service.registry,'_publish',side_effect=lost):
            with self.assertRaises(MemoryError):self.service.bind(attempt)
        self.signal.request();before=self.boundary.last_call
        binding=self.service._bindings[-1]
        session=self.service.bind(attempt)
        self.assertIs(session,binding.session)
        self.assertIs(session,self.boundary._operation_ledger)
        self.assertIs(self.boundary.last_call,before)
        self.assertIs(self.service.bind(attempt),session)
    def test_request_after_preexecute_check_contains_unsent_refusal(self):
        tx=self.adopt().value;r,s=self.runner();original=NativeCancellation._is_requested
        def checked(child):
            value=original(child);self.signal.request();return value
        with patch.object(NativeCancellation,'_is_requested',checked):
            result=r.execute(tx,s,{'value':'unsent'})
        self.assertEqual(result.error.code,'cancelled')
        self.assertEqual(self.tracker._state.status,b'T')
        self.assertIsNone(self.boundary._operation)
        self.assertFalse(self.boundary._quarantined)
        self.assertTrue(self.executor._original_custody(tx).usable)

    def test_savepoint_admission_wins_before_late_request(self):
        tx=self.adopt().value;original=self.executor._admit_savepoint
        def admitted(*args):
            value=original(*args);self.signal.request();return value
        with patch.object(self.executor,'_admit_savepoint',side_effect=admitted):
            result=self.session.savepoint(tx)
        self.assertIsInstance(result,Ok)
        self.assertIs(self.executor._savepoint_publications[-1].admission,self.executor._original_custody(tx))
        self.assertTrue(self.signal.requested())
        self.assertIsInstance(self.session.rollback_to_savepoint(tx,result.value),Ok)
        self.assertIsInstance(self.session.release_savepoint(tx,result.value),Ok)
    def test_unsupported_cancel_channel_does_not_downgrade(self):
        tx=self.adopt().value;r,s=self.runner();self.connection._usock.settimeout(None)
        before=self.boundary.last_call
        self.assertEqual(r.execute(tx,s,{'value':'blocked'}).error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
    def test_original_cancelled_generation_cannot_be_readopted_by_other_executor(self):
        tx=self.adopt().value;self.signal.request();before=self.boundary.last_call
        other=custody.HostExecutor()
        result=other.adopt_transaction(self.executor._original_custody(tx).port,isolation='read_committed',access_mode='read_write')
        self.assertEqual(result.error.code,'invalid_transaction')
        self.assertIs(self.boundary.last_call,before)
    def test_request_in_execute_preflight_preserves_admitted_resource(self):
        from truss._native_pg8000 import _Prepared
        tx=self.adopt().value;r,s=self.runner();original=_Prepared._open
        entered=Event();threads=[];request=NativeCancellation.request
        def forwarded(child):
            entered.set();return request(child)
        def preflight(prepared):
            original(prepared)
            thread=Thread(target=self.signal.request);threads.append(thread);thread.start()
            self.assertTrue(entered.wait(1))
        with patch.object(_Prepared,'_open',preflight),patch.object(NativeCancellation,'request',forwarded):
            result=r.execute(tx,s,{'value':'admitted'})
        for thread in threads:
            thread.join(timeout=3);self.assertFalse(thread.is_alive())
        if isinstance(result,Error):self.assertEqual(result.error.code,'cancelled')
        else:self.assertEqual(result.value,(('admitted',),))
        self.assertFalse(self.boundary._quarantined)
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(self.tracker._state.status,b'T')
        self.assertEqual(self.boundary.run('SELECT count(*) FROM pg_catalog.pg_prepared_statements'),[[0]])

    def test_request_after_binding_retains_unproved_setup_custody(self):
        tx=self.adopt().value;r,s=self.runner();original=NativeCancellation._attach
        def attached(child,session):
            original(child,session);self.signal.request()
        before=self.boundary.last_call
        with patch.object(NativeCancellation,'_attach',attached):
            result=r.execute(tx,s,{'value':'unsent'})
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertIs(self.boundary.last_call,before)
        self.assertTrue(self.boundary._quarantined)
        self.assertIsNotNone(self.boundary._operation)
        self.assertIsNotNone(self.boundary._operation_ledger)
        self.assertFalse(self.executor._original_custody(tx).usable)
        self.assertEqual(r.execute(tx,s,{'value':'blocked'}).error.code,'transaction_unusable')
        self.assertIs(self.boundary.last_call,before)

    def test_confirmed_end_and_replacement_precede_cancelled_old_handle(self):
        for ending in ('commit','rollback'):
            with self.subTest(ending=ending):
                if self.tracker._state.status==b'I':
                    self.assertIsInstance(self.session.begin(),Ok)
                    self.signal=self.executor.cancellation()
                tx=self.adopt().value
                r=getattr(self.service,'_completion_producer',None) or NativeOperationRunner(self.service)
                statement=r.register('SELECT :value::pg_catalog.text','SELECT')
                self.signal.request();self.assertIsInstance(getattr(self.session,ending)(),Ok)
                for replacement in (False,True):
                    if replacement:self.assertIsInstance(self.session.begin(),Ok)
                    before=self.boundary.last_call
                    self.assertEqual(r.execute(tx,statement,{'value':'old'}).error.code,'invalid_transaction')
                    self.assertEqual(self.session.savepoint(tx).error.code,'invalid_transaction')
                    self.assertEqual(self.executor.savepoint(tx).error.code,'invalid_transaction')
                    self.assertEqual(self.service.registry.prepare(r._assembly,tx).reason,'invalid_transaction')
                    self.assertIs(self.boundary.last_call,before)
                self.assertIsInstance(self.session.rollback(),Ok)

    def test_disposal_precedes_cancelled_admission_without_erasing_custody(self):
        tx=self.adopt().value;r,s=self.runner();original=self.executor._original_custody(tx)
        self.signal.request();self.executor.dispose();before=self.boundary.last_call
        self.assertEqual(r.execute(tx,s,{'value':'old'}).error.code,'invalid_transaction')
        self.assertEqual(self.session.savepoint(tx).error.code,'invalid_transaction')
        self.assertEqual(self.executor.savepoint(tx).error.code,'invalid_transaction')
        self.assertIs(self.executor._original_custody(tx),original)
        self.assertTrue(self.signal.requested())
        self.assertIs(self.boundary.last_call,before)

class AdoptionSignalTests(unittest.TestCase):
    def test_request_forwards_outside_context_lock_and_detach_is_exact(self):
        from truss._adoption_cancellation import AdoptionCancellation
        owner=object();custodian=object();signal=AdoptionCancellation(owner)
        self.assertTrue(signal.bind(owner,custodian))
        calls=[]
        class Child:
            def request(child):
                with ThreadPoolExecutor(max_workers=1) as worker:
                    self.assertTrue(worker.submit(signal.requested).result(timeout=1))
                calls.append(child);return 'forwarded'
        first=Child();second=Child()
        self.assertTrue(signal.attach(custodian,first))
        self.assertFalse(signal.attach(custodian,second))
        self.assertEqual(signal.request(),'forwarded')
        self.assertFalse(signal.detach(custodian,second))
        self.assertTrue(signal.detach(custodian,first))
        self.assertEqual(signal.request(),'latched')
        self.assertTrue(signal.attach(custodian,second))
        self.assertEqual(calls,[first,second])
        self.assertTrue(signal.detach(custodian,second))
        self.assertTrue(signal.requested())
        self.assertFalse(signal.bind(owner,object()))
