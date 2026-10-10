import unittest
from dataclasses import replace
from truss.execution import TransactionObservation, ExecutionFailure, Ok, Error
from truss._host_execution import HostExecutor

class Port:
    def __init__(self):
        self.current = TransactionObservation('native-connection', 'native-transaction', 'repeatable_read', 'read_write', 'active')
        self.commands = []
        self.failure = False
    def observe(self): return self.current
    def control(self, sql):
        self.commands.append(sql)
        if self.failure: raise OSError('lost completion')
        if sql.startswith('ROLLBACK TO'): self.current = replace(self.current, state='active')

class HostExecutionTests(unittest.TestCase):
    def adopt(self, executor, port):
        r=executor.adopt_transaction(port,isolation='repeatable_read',access_mode='read_write')
        self.assertIsInstance(r,Ok);return r.value
    def test_actual_profile_and_duplicate_adoption_refuse_without_control(self):
        e=HostExecutor();p=Port()
        self.assertIsInstance(e.adopt_transaction(p,isolation='serializable',access_mode='read_write'),Error)
        h=self.adopt(e,p)
        self.assertEqual(h.ownership,'caller')
        self.assertIsInstance(e.adopt_transaction(p,isolation='repeatable_read',access_mode='read_write'),Error)
        self.assertEqual(p.commands,[])
    def test_savepoint_rollback_failed_transaction_and_nested_invalidation(self):
        e=HostExecutor();p=Port();h=self.adopt(e,p)
        a=e.savepoint(h).value;b=e.savepoint(h).value
        p.current=replace(p.current,state='failed')
        self.assertIsInstance(e.rollback_to_savepoint(h,a),Ok)
        self.assertIsInstance(e.release_savepoint(h,b),Error)
        self.assertIsInstance(e.release_savepoint(h,a),Ok)
        self.assertIsInstance(e.release_savepoint(h,a),Error)
        self.assertTrue(all(s.startswith(('SAVEPOINT ','ROLLBACK TO SAVEPOINT ','RELEASE SAVEPOINT ')) for s in p.commands))
    def test_foreign_handles_and_original_transaction_replacement(self):
        e=HostExecutor();p=Port();h=self.adopt(e,p);other=HostExecutor()
        self.assertIsInstance(other.savepoint(h),Error)
        p.current=replace(p.current,transaction_identity='next-transaction')
        self.assertEqual(e.savepoint(h).error.code,'invalid_transaction')
        self.assertEqual(p.commands,[])
    def test_uncertain_control_quarantines_without_cleanup_or_retry(self):
        e=HostExecutor();p=Port();h=self.adopt(e,p);p.failure=True
        self.assertIsInstance(e.savepoint(h),Error)
        self.assertIsInstance(e.savepoint(h),Error)
        self.assertEqual(len(p.commands),1)
        self.assertIsInstance(e.adopt_transaction(p,isolation='repeatable_read',access_mode='read_write'),Error)
        self.assertEqual(e.savepoint(h).error.code,'transaction_unusable')
        e.dispose();self.assertEqual(len(p.commands),1)
        self.assertIs(e._transactions[h._key].port,p)
        self.assertFalse(e._transactions[h._key].usable)
    def test_observation_loss_is_unusable_not_foreign_handle(self):
        e=HostExecutor();p=Port();h=self.adopt(e,p)
        def lost(): raise OSError('native observation lost')
        p.observe=lost
        self.assertEqual(e.savepoint(h).error.code,'transaction_unusable')
        self.assertEqual(p.commands,[])

    def test_original_custody_lookup_is_inert_and_survives_quarantine(self):
        e=HostExecutor();p=Port();h=self.adopt(e,p)
        original=e._original_custody(h)
        def forbidden(): raise AssertionError('Preparation performed native observation')
        p.observe=forbidden
        self.assertIs(e._original_custody(h),original)
        self.assertIsNone(HostExecutor()._original_custody(h))
        original.usable=False;e.dispose()
        self.assertIs(e._original_custody(h),original)
        self.assertEqual(p.commands,[])
        self.assertIsInstance(e.savepoint(h),Error)

    def test_disposal_never_ends_host_transaction(self):
        e=HostExecutor();p=Port();h=self.adopt(e,p);e.dispose()
        self.assertIsInstance(e.savepoint(h),Error);self.assertEqual(p.commands,[])
    def test_execution_failure_retry_scope_is_exact(self):
        with self.assertRaises(ValueError):ExecutionFailure('retry','retry')
        with self.assertRaises(ValueError):ExecutionFailure('invalid_transaction','bad','whole_transaction')
        self.assertEqual(ExecutionFailure('retry','retry','whole_transaction').retry_scope,'whole_transaction')
        with self.assertRaises(TypeError):Ok(1,status='error')
        with self.assertRaises(TypeError):Error(ExecutionFailure('cancelled','cancelled'),status='ok')
