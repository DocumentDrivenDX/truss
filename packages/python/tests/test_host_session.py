"""Private complete-call scopes over original native lifetime custody."""
import unittest
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._host_execution import HostExecutor
from truss._native_transactions import NativeTransactions
from truss._native_arbitration import NativeArbitration
from truss._host_session import NativeHostSession
from truss.execution import Ok,Error

class HostSessionTests(NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.boundary.run('CREATE TEMP TABLE session_fixture(value int UNIQUE DEFERRABLE INITIALLY DEFERRED)')
        self.executor=HostExecutor();self.tracker=NativeTransactions(self.boundary)
        self.service=NativeArbitration(self.executor)
        self.session=NativeHostSession(self.executor,self.tracker,self.service)
    def adopt(self):
        self.assertIsInstance(self.session.begin(),Ok)
        result=self.session.adopt_transaction();self.assertIsInstance(result,Ok)
        return result.value
    def test_host_work_savepoint_rollback_and_commit(self):
        tx=self.adopt();self.boundary.run('INSERT INTO session_fixture VALUES(1)')
        sp=self.session.savepoint(tx).value
        self.boundary.run('INSERT INTO session_fixture VALUES(2)')
        self.assertIsInstance(self.session.rollback_to_savepoint(tx,sp),Ok)
        self.assertIsInstance(self.session.release_savepoint(tx,sp),Ok)
        self.assertEqual(self.session.commit().value.state,'committed')
        self.assertEqual(self.boundary.run('SELECT value FROM session_fixture'),[[1]])
        self.assertIsNone(self.boundary._operation)
        self.assertIsInstance(self.session.savepoint(tx),Error)
    def test_failed_transaction_commit_is_rollback(self):
        self.adopt();self.boundary.run('INSERT INTO session_fixture VALUES(1)')
        with self.assertRaises(Exception):self.boundary.run('SELECT 1/0')
        self.assertEqual(self.session.commit().value.state,'rolled_back')
        self.assertEqual(self.boundary.run('SELECT count(*) FROM session_fixture'),[[0]])
    def test_deferred_commit_failure_is_known_rollback(self):
        self.adopt();self.boundary.run('INSERT INTO session_fixture VALUES(1),(1)')
        result=self.session.commit()
        self.assertIsInstance(result,Ok);self.assertEqual(result.value.state,'rolled_back')
        self.assertEqual(result.value.sql_state,'23505')
        self.assertIsNone(self.boundary._operation)
    def test_complete_native_error_can_rollback_to_original_savepoint(self):
        tx=self.adopt();sp=self.session.savepoint(tx).value
        with self.assertRaises(Exception):self.boundary.run('SELECT 1/0')
        self.assertIsInstance(self.session.rollback_to_savepoint(tx,sp),Ok)
        self.assertIsInstance(self.session.release_savepoint(tx,sp),Ok)
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_same_domain_facade_and_busy_do_not_retry(self):
        tx=self.adopt();other=NativeHostSession(self.executor,self.tracker,self.service)
        self.assertEqual(other.adopt_transaction().error.code,'invalid_transaction')
        token=self.boundary.acquire_operation();before=self.boundary.last_call
        self.assertIsInstance(other.savepoint(tx),Error)
        self.assertIs(self.boundary.last_call,before)
        self.boundary.release_operation(token)
        self.assertIsInstance(other.savepoint(tx),Ok)
    def test_disposal_preserves_host_settlement(self):
        tx=self.adopt();self.boundary.run('INSERT INTO session_fixture VALUES(1)')
        self.session.dispose();self.assertIsInstance(self.session.savepoint(tx),Error)
        self.assertEqual(self.tracker._state.status,b'T')
        self.assertEqual(self.session.commit().value.state,'committed')
    def test_after_executor_publication_reply_loss_reconciles_without_replay(self):
        tx=self.adopt();publish=self.executor._publish_savepoint_map
        def lost(candidate):publish(candidate);raise RuntimeError('reply lost')
        with patch.object(self.executor,'_publish_savepoint_map',side_effect=lost):
            result=self.session.savepoint(tx)
        self.assertIsInstance(result,Ok)
        self.assertEqual(len(self.tracker._state.savepoints),1)
        self.assertIsNone(self.boundary._operation)
        self.assertIsInstance(self.session.release_savepoint(tx,result.value),Ok)
    def test_before_executor_publication_retains_original_guard(self):
        tx=self.adopt()
        with patch.object(self.executor,'_publish_savepoint_map',side_effect=MemoryError('allocation')):
            result=self.session.savepoint(tx)
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertIsNotNone(self.boundary._operation)
        self.assertEqual(len(self.tracker._state.savepoints),1)
        self.assertEqual(self.executor._savepoint_publications[-1].phase,'unresolved')
        before=self.boundary.last_call;self.assertIsInstance(self.session.rollback(),Error)
        self.assertIs(self.boundary.last_call,before)
    def test_port_base_exception_after_native_effect_retains_custody(self):
        tx=self.adopt();port=self.executor._original_custody(tx).port
        with patch.object(port,'_publish_savepoint_map',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.session.savepoint(tx)
        self.assertIsNotNone(self.boundary._operation)
        self.assertIsNotNone(port._pending_savepoint)
        self.assertEqual(port._last_control.phase,'unresolved')
        self.assertIsNotNone(port._last_control.native_call.original_control)
        self.assertEqual(self.session._calls[-1].phase,'unresolved')
    def test_rollback_and_release_publication_allocation_failures(self):
        for method in ('rollback_to_savepoint','release_savepoint'):
            # Independent cases use independently attached original connections.
            with self.subTest(method=method):
                connection=self.Connection(**self.kwargs);connection.run('SELECT 1')
                from truss._native_pg8000 import NativeBoundary
                b=NativeBoundary(connection);e=HostExecutor();t=NativeTransactions(b);a=NativeArbitration(e);s=NativeHostSession(e,t,a)
                try:
                    s.begin();tx=s.adopt_transaction().value;sp=s.savepoint(tx).value
                    with patch.object(e,'_publish_savepoint_map',side_effect=MemoryError):
                        result=getattr(s,method)(tx,sp)
                    self.assertEqual(result.error.code,'transaction_unusable')
                    self.assertIsNotNone(b._operation)
                    self.assertEqual(e._savepoint_publications[-1].phase,'unresolved')
                finally:connection.close()
    def test_capacity_refuses_before_acquiring_or_sql(self):
        tx=self.adopt();session=NativeHostSession(self.executor,self.tracker,self.service,retained_calls=1)
        session.savepoint(tx);before=self.boundary.last_call
        self.assertEqual(session.savepoint(tx).error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
    def test_sent_commit_without_ready_is_unknown_and_never_retried(self):
        self.adopt()
        with patch.object(self.connection,'handle_messages',side_effect=OSError('lost ready')):
            result=self.session.commit()
        self.assertEqual(result.error.code,'commit_unknown')
        self.assertIsNotNone(self.boundary._operation)
        before=self.boundary.last_call;self.assertIsInstance(self.session.commit(),Error)
        self.assertIs(self.boundary.last_call,before)
    def test_lost_native_guard_release_reply_reconciles_without_second_control(self):
        tx=self.adopt();release=self.boundary.release_operation
        def lost(token,**kwargs):release(token,**kwargs);raise RuntimeError('lost release reply')
        with patch.object(self.boundary,'release_operation',side_effect=lost):
            result=self.session.savepoint(tx)
        self.assertIsInstance(result,Ok)
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(len(self.tracker._state.savepoints),1)
    def test_disposal_during_original_publication_never_ends_host(self):
        tx=self.adopt();publish=self.executor._publish_savepoint_map
        def disposed(candidate):self.session.dispose();publish(candidate)
        with patch.object(self.executor,'_publish_savepoint_map',side_effect=disposed):
            result=self.session.savepoint(tx)
        self.assertIsInstance(result,Ok)
        self.assertEqual(self.tracker._state.status,b'T')
        self.assertIsInstance(self.session.savepoint(tx),Error)
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_sequential_original_generations_and_foreign_handles(self):
        original=self.adopt();self.session.commit()
        newer=self.adopt()
        self.assertIsNot(original,newer)
        self.assertIsInstance(self.session.savepoint(original),Error)
        self.assertIsInstance(self.session.savepoint(newer),Ok)
        foreign=HostExecutor()
        service=NativeArbitration(foreign)
        other=NativeHostSession(foreign,self.tracker,service)
        self.assertIsInstance(other.savepoint(newer),Error)
        self.assertEqual(other.adopt_transaction().error.code,'invalid_transaction')
    def test_wrong_shared_composition_rejected_inertly(self):
        before=self.boundary.last_call
        with self.assertRaises(ValueError):NativeHostSession(HostExecutor(),self.tracker,self.service)
        self.assertIs(self.boundary.last_call,before)
    def test_known_commit_survives_handback_failure(self):
        self.adopt();self.boundary.run('INSERT INTO session_fixture VALUES(1)')
        with patch.object(self.boundary,'release_operation',side_effect=MemoryError):
            result=self.session.commit()
        self.assertIsInstance(result,Ok)
        self.assertEqual(result.value.state,'committed')
        self.assertEqual(result.value.handback,'quarantined')
        self.assertIsNotNone(self.boundary._operation)
        self.assertTrue(self.session._closed)
    def test_two_boundaries_share_original_executor_publication_serialization(self):
        from threading import Event,Thread
        from truss._native_pg8000 import NativeBoundary
        first=self.adopt()
        connection=self.Connection(**self.kwargs);connection.run('SELECT 1')
        boundary=NativeBoundary(connection);tracker=NativeTransactions(boundary)
        other=NativeHostSession(self.executor,tracker,self.service)
        entered=Event();proceed=Event();result=[];publish=self.executor._publish_savepoint_map
        try:
            other.begin();second=other.adopt_transaction().value
            def paused(candidate):
                entered.set()
                if not proceed.wait(5):raise RuntimeError('test synchronization timeout')
                publish(candidate)
            with patch.object(self.executor,'_publish_savepoint_map',side_effect=paused):
                thread=Thread(target=lambda:result.append(self.session.savepoint(first)))
                thread.start()
                try:
                    self.assertTrue(entered.wait(5));before=boundary.last_call
                    refused=other.savepoint(second)
                    self.assertEqual(refused.error.code,'execution_obligation')
                    self.assertIs(boundary.last_call,before)
                finally:proceed.set();thread.join(5)
            self.assertFalse(thread.is_alive());self.assertIsInstance(result[0],Ok)
            later=other.savepoint(second);self.assertIsInstance(later,Ok)
            self.assertIn(result[0].value._key,self.executor._savepoints)
            self.assertIn(later.value._key,self.executor._savepoints)
            self.assertIsInstance(self.session.release_savepoint(first,result[0].value),Ok)
            self.assertIsInstance(other.release_savepoint(second,later.value),Ok)
        finally:connection.close()
    def test_native_capacity_refusal_preserves_prior_savepoint_and_cleanup(self):
        self.tracker._limit=1
        tx=self.adopt();sp=self.session.savepoint(tx).value
        result=self.session.savepoint(tx)
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertIsNone(self.boundary._operation)
        self.assertTrue(self.executor._original_custody(tx).usable)
        self.assertIsInstance(self.session.release_savepoint(tx,sp),Ok)
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_original_acquisition_reply_loss_retains_preallocated_token(self):
        self.adopt();acquire=self.boundary.acquire_operation
        def lost(**kwargs):acquire(**kwargs);raise MemoryError('lost acquisition reply')
        with patch.object(self.boundary,'acquire_operation',side_effect=lost):
            result=self.session.commit()
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(self.session._closed)
        self.assertIs(self.session._calls[-1].token,self.boundary._operation)
        self.assertEqual(self.session._calls[-1].phase,'unresolved')
    def test_acquisition_failure_before_publication_remains_effect_free(self):
        self.adopt();before=self.boundary.last_call
        with patch.object(self.boundary,'acquire_operation',side_effect=MemoryError):
            result=self.session.commit()
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertFalse(self.session._closed)
        self.assertIsNone(self.boundary._operation)
        self.assertIs(self.boundary.last_call,before)
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_same_executor_synthetic_port_is_not_native_session_authority(self):
        from test_host_execution import Port
        adopted=self.executor.adopt_transaction(Port(),isolation='repeatable_read',access_mode='read_write')
        self.assertIsInstance(adopted,Ok);before=self.boundary.last_call
        self.assertEqual(self.session.savepoint(adopted.value).error.code,'invalid_transaction')
        self.assertIs(self.boundary.last_call,before)
    def test_handback_then_later_host_call_cannot_replace_original_receipt(self):
        self.adopt();release=self.boundary.release_operation
        def lost(token,**kwargs):
            release(token,**kwargs)
            self.boundary.run("SELECT 'later-host-call'::text")
            raise RuntimeError('lost original release reply')
        with patch.object(self.boundary,'release_operation',side_effect=lost):
            result=self.session.commit()
        self.assertEqual(result.value.state,'committed')
        record=self.session._calls[-1]
        self.assertTrue(record.release.published)
        self.assertIsNot(record.original,self.boundary.last_call)
        self.assertEqual(tuple(e.payload.rstrip(b'\0') for e in record.original.events if e.code==b'C'),(b'COMMIT',))
        self.assertEqual(record.phase,'settled')
    def test_later_facade_control_cannot_replace_original_port_receipt(self):
        tx=self.adopt();other=NativeHostSession(self.executor,self.tracker,self.service)
        port=self.executor._original_custody(tx).port
        release=self.boundary.release_operation;later=[]
        def lost(token,**kwargs):
            release(token,**kwargs)
            if not later:
                later.append(None)
                later[0]=other.savepoint(tx)
                raise RuntimeError('lost original reply')
        with patch.object(self.boundary,'release_operation',side_effect=lost):
            result=self.session.savepoint(tx)
        self.assertIsInstance(result,Ok);self.assertIsInstance(later[0],Ok)
        record=self.session._calls[-1]
        self.assertIsNot(record.port_control,port._last_control)
        self.assertEqual(record.port_control.native_call.original_control.savepoint.name,result.value._key)
        self.assertEqual(port._last_control.native_call.original_control.savepoint.name,later[0].value._key)
    def test_known_commit_preallocated_result_survives_post_native_allocation_fault(self):
        self.adopt()
        with patch.object(self.session,'_settlement_result',side_effect=MemoryError):
            result=self.session.commit()
        self.assertIsInstance(result,Ok)
        self.assertEqual(result.value.state,'committed')
        self.assertEqual(result.value.handback,'quarantined')
        self.assertIsNotNone(self.boundary._operation)
    def test_settlement_result_constructor_is_not_called_after_native_commit(self):
        self.adopt()
        import truss._host_session as module
        original=module.HostControlResult
        def allocate(*args,**kwargs):
            if self.boundary.last_call and any(e.code==b'C' and e.payload==b'COMMIT\0' for e in self.boundary.last_call.events):
                raise MemoryError('post-native result allocation')
            return original(*args,**kwargs)
        with patch.object(module,'HostControlResult',side_effect=allocate):
            result=self.session.commit()
        self.assertIsInstance(result,Ok);self.assertEqual(result.value.state,'committed')
        self.assertIsNone(self.boundary._operation)
    def test_known_deferred_abort_survives_result_selection_fault(self):
        self.adopt();self.boundary.run('INSERT INTO session_fixture VALUES(1),(1)')
        with patch.object(self.session,'_settlement_result',side_effect=MemoryError):
            result=self.session.commit()
        self.assertIsInstance(result,Ok)
        self.assertEqual(result.value.state,'rolled_back')
        self.assertEqual(result.value.sql_state,'23505')
        self.assertEqual(result.value.handback,'quarantined')
        self.assertIsNotNone(self.boundary._operation)

    def test_acknowledged_commit_before_lost_ready_persists(self):
        self._acknowledged_end_before_lost_ready('commit','committed',1)

    def test_acknowledged_rollback_before_lost_ready_discards(self):
        self._acknowledged_end_before_lost_ready('rollback','rolled_back',0)

    def _acknowledged_end_before_lost_ready(self,kind,state,count):
        from uuid import uuid4
        table='scope_ack_'+uuid4().hex
        self.boundary.run('CREATE TABLE '+table+' (value int)')
        self.adopt();generation=self.tracker._state.generation
        self.boundary.run('INSERT INTO '+table+' VALUES(1)')
        original=self.connection.message_types[b'C']
        def lose_ready(data,context):
            original(data,context)
            if data==kind.upper().encode()+b'\0':raise OSError('lost Ready after native acknowledgment')
        self.connection.message_types[b'C']=lose_ready
        observer=self.Connection(**self.kwargs)
        try:
            result=getattr(self.session,kind)()
            self.assertIsInstance(result,Ok)
            self.assertEqual((result.value.state,result.value.handback),(state,'quarantined'))
            self.assertFalse(self.boundary.last_call.capture_complete)
            self.assertIs(self.tracker._state.generation,generation)
            self.assertIs(self.boundary._operation,self.session._calls[-1].token)
            self.assertEqual(observer.run('SELECT count(*) FROM '+table),[[count]])
            call=self.boundary.last_call
            self.assertIsInstance(self.session.rollback(),Error)
            self.assertIs(self.boundary.last_call,call)
        finally:
            self.connection.message_types[b'C']=original
            observer.run('DROP TABLE '+table);observer.close()
