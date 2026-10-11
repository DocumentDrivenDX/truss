"""Original scheduling clocks and native savepoint containment, not I/O bounds."""
import unittest
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._host_execution import HostExecutor
from truss._native_transactions import NativeTransactions
from truss._native_arbitration import NativeArbitration
from truss._native_deadline import NativeOperationDeadline, NativeDeadlineExpired
from truss._native_result_custody import NativeTextLimits
from truss._native_operation import NativeOperationRunner
from truss.execution import Ok

class DeadlineClockTests(unittest.TestCase):
    def test_exact_allowances(self):
        for value in (0,-1,True,1.5):
            with self.assertRaises(ValueError): NativeOperationDeadline(value,5)
            with self.assertRaises(ValueError): NativeOperationDeadline(30,value)
    def test_fixed_ordinary_and_single_settlement_phase(self):
        now=[0]
        with patch('truss._native_deadline.monotonic_ns',side_effect=lambda:now[0]):
            deadline=NativeOperationDeadline(30,5)
            now[0]=29999999; deadline.check()
            now[0]=30000000
            with self.assertRaises(NativeDeadlineExpired): deadline.check()
            deadline.begin_settlement(); self.assertEqual(deadline.settlement_cutoff_ns,35000000)
            now[0]=34000000; deadline.begin_settlement()
            self.assertEqual(deadline.settlement_cutoff_ns,35000000)
            now[0]=35000000
            with self.assertRaises(NativeDeadlineExpired): deadline.begin_settlement()
            self.assertEqual(deadline.settlement_cutoff_ns,35000000)

# Reuse only fixture setup, not inherited test membership.
class NativeDeadlineTests(NativeBoundaryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.boundary.run('CREATE TEMP TABLE truss_operation_fixture(value text PRIMARY KEY)')
        self.t=NativeTransactions(self.boundary); self.t.begin()
        token=self.boundary.acquire_operation(); self.executor=HostExecutor()
        self.port=self.t.port(token)
        self.tx=self.executor.adopt_transaction(self.port,isolation='read_committed',access_mode='read_write').value
        self.boundary.release_operation(token)
        self.service=NativeArbitration(self.executor); self.runner=NativeOperationRunner(self.service)
    def clock(self,now):
        return patch('truss._native_deadline.monotonic_ns',side_effect=lambda:now[0])
    def statement(self): return self.runner.register('SELECT :value::pg_catalog.text','SELECT')
    def test_preacquisition_expiry_is_no_sql(self):
        before=self.boundary.last_call; original=self.runner._profile; now=[0]
        def profile(boundary):
            result=original(boundary); now[0]=30000000000; return result
        with self.clock(now),patch.object(self.runner,'_profile',side_effect=profile):
            result=self.runner.execute(self.tx,self.statement(),{'value':'unused'})
        self.assertEqual(result.error.code,'cancelled')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        self.assertFalse(self.boundary._quarantined)
    def test_expired_prepared_call_contains_prior_host_work(self):
        self.boundary.run("INSERT INTO truss_operation_fixture VALUES('host-before')")
        now=[0]; original=self.boundary.prepare
        def prepare(*args,**kwargs):
            value=original(*args,**kwargs); now[0]=30000000000; return value
        with self.clock(now),patch.object(self.boundary,'prepare',side_effect=prepare):
            result=self.runner.execute(self.tx,self.statement(),{'value':'unsent'})
        self.assertEqual(result.error.code,'cancelled')
        self.assertIsNone(self.boundary._operation)
        self.assertFalse(self.boundary._quarantined)
        self.assertEqual(self.boundary.run('SELECT value FROM truss_operation_fixture'),[['host-before']])
        self.assertIsInstance(self.runner.execute(self.tx,self.statement(),{'value':'again'}),Ok)
    def test_post_result_expiry_rolls_back_original_scope(self):
        from truss._native_result_custody import NativeResultCustody
        now=[0]; original=NativeResultCustody.transfer
        def transfer(gate,rows):
            value=original(gate,rows); now[0]=30000000000; return value
        with self.clock(now),patch.object(NativeResultCustody,'transfer',transfer):
            result=self.runner.execute(self.tx,self.statement(),{'value':'not-published'})
        self.assertEqual(result.error.code,'cancelled')
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(self.t._state.savepoints,())
    def test_settlement_expiry_retains_unusable_original_scope(self):
        now=[0]; original=self.boundary.prepare; rollback=self.t.rollback_to
        def prepare(*args,**kwargs):
            value=original(*args,**kwargs); now[0]=30000000000; return value
        def expire(*args,**kwargs):
            now[0]=35000000000; return rollback(*args,**kwargs)
        with self.clock(now),patch.object(self.boundary,'prepare',side_effect=prepare),patch.object(self.t,'rollback_to',side_effect=expire):
            result=self.runner.execute(self.tx,self.statement(),{'value':'unsent'})
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(self.boundary._quarantined)
        self.assertIsNotNone(self.boundary._operation)
        self.assertEqual(len(self.t._state.savepoints),1)
    def test_successful_release_expiry_does_not_invent_rollback(self):
        now=[0]; original=self.t.release; rollback=self.t.rollback_to
        def release(*args,**kwargs):
            value=original(*args,**kwargs); now[0]=30000000000; return value
        with self.clock(now),patch.object(self.t,'release',side_effect=release),patch.object(self.t,'rollback_to',wraps=rollback) as called:
            result=self.runner.execute(self.tx,self.statement(),{'value':'settled'})
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(self.boundary._quarantined)
        self.assertEqual(self.t._state.savepoints,())
        called.assert_not_called()

    def test_expiry_after_mutating_preflight_does_not_poison_prepared_resource(self):
        now=[0]; original=self.boundary._call
        def call(invoke,token=None,**kwargs):
            resource=kwargs.get('resource')
            if resource is not None and resource[0]=='prepare':
                preflight=kwargs['preflight']
                def expire():
                    preflight(); now[0]=30000000000
                kwargs['preflight']=expire
            return original(invoke,token,**kwargs)
        with self.clock(now),patch.object(self.boundary,'_call',side_effect=call):
            result=self.runner.execute(self.tx,self.statement(),{'value':'unsent'})
        self.assertEqual(result.error.code,'cancelled')
        self.assertFalse(self.boundary._quarantined)
        self.assertIsNone(self.boundary._operation)
        self.assertTrue(all(p._resource.phase=='closed' for p in self.runner._runs[-1].gate.inventory()))
    def test_expiry_before_savepoint_does_not_invent_containment(self):
        now=[0]; original=self.runner._state
        def state(*args,**kwargs):
            value=original(*args,**kwargs); now[0]=30000000000; return value
        with self.clock(now),patch.object(self.runner,'_state',side_effect=state),patch.object(self.t,'rollback_to',wraps=self.t.rollback_to) as called:
            result=self.runner.execute(self.tx,self.statement(),{'value':'unused'})
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(self.boundary._quarantined)
        self.assertIsNone(self.runner._runs[-1].savepoint)
        called.assert_not_called()
    def test_lost_completed_reply_reconciles_after_clock_expiry_without_sql(self):
        now=[0]; original=self.runner._produce
        def lost(*args,**kwargs):
            original(*args,**kwargs); now[0]=40000000000; raise OSError('lost reply')
        with self.clock(now),patch.object(self.runner,'_produce',side_effect=lost):
            result=self.runner.execute(self.tx,self.statement(),{'value':'complete'})
            self.assertEqual(result.error.code,'transaction_unusable')
            run=self.runner._runs[-1]; before=self.boundary.last_call
            reconciled=self.runner.reconcile(run)
        self.assertIsInstance(reconciled,Ok)
        self.assertEqual(reconciled.value,(('complete',),))
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(run.completion.deadline_basis[3],0)

    def test_real_elapsed_native_call_settles_then_contains(self):
        # Explicit native timing fixture, never a shipped SQL registration.
        from time import monotonic
        sql='SELECT :value::pg_catalog.text FROM pg_catalog.pg_sleep(0.35)'
        self.runner.limits=NativeTextLimits(ordinary_ms=200)
        self.boundary.run("INSERT INTO truss_operation_fixture VALUES('host-before')")
        with patch.dict(self.runner.QUALIFIED_STATEMENTS,{sql:'SELECT'}):
            statement=self.runner.register(sql,'SELECT')
        started=monotonic()
        result=self.runner.execute(self.tx,statement,{'value':'settled-but-expired'})
        self.assertGreaterEqual(monotonic()-started,0.2)
        self.assertEqual(result.error.code,'cancelled')
        self.assertFalse(self.boundary._quarantined)
        self.assertIsNone(self.boundary._operation)
        run=self.runner._runs[-1]
        calls=[c.native_call for c in run.session.calls if c.resource is not None and c.resource[0]=='execute']
        self.assertEqual(len(calls),1)
        self.assertTrue(calls[0].capture_complete)
        self.assertTrue(any(e.code==b'C' for e in calls[0].events))
        self.assertEqual(self.boundary.run('SELECT value FROM truss_operation_fixture'),[['host-before']])

    def test_success_restoration_entry_expiry_keeps_unresolved_savepoint(self):
        from truss._native_result_custody import NativeResultCustody
        now=[0]; transferred=[False]; checks=[0]
        transfer=NativeResultCustody.transfer; check=NativeOperationDeadline.check
        def capture(gate,rows):
            value=transfer(gate,rows); transferred[0]=True; return value
        def expire(deadline):
            if transferred[0]:
                checks[0]+=1
                if checks[0]==2: now[0]=30000000000
            return check(deadline)
        with self.clock(now),patch.object(NativeResultCustody,'transfer',capture),patch.object(NativeOperationDeadline,'check',expire),patch.object(self.t,'rollback_to',wraps=self.t.rollback_to) as called:
            result=self.runner.execute(self.tx,self.statement(),{'value':'not-published'})
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(self.boundary._quarantined)
        self.assertEqual(len(self.t._state.savepoints),1)
        self.assertIsNone(self.runner._runs[-1].deadline.settlement_cutoff_ns)
        self.assertIsNone(self.runner._runs[-1].completion)
        called.assert_not_called()
