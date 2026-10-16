"""Composed private prepared-Execute cancellation; no public C02 claim."""
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
from test_native_pg8000 import NativeBoundaryFixture
from truss._host_execution import HostExecutor
from truss._native_transactions import NativeTransactions
from truss._native_arbitration import NativeArbitration
from truss._native_operation import NativeOperationRunner
from truss._native_cancellation import NativeCancellation
from truss._native_pg8000 import NativeBoundaryRefusal
from truss.execution import Ok, Error


class NativeCancellationTests(NativeBoundaryFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.connection._usock.settimeout(2)
        self.boundary.run('CREATE TEMP TABLE truss_operation_fixture(value text PRIMARY KEY)')
        self.t=NativeTransactions(self.boundary);self.t.begin()
        token=self.boundary.acquire_operation();self.executor=HostExecutor()
        self.port=self.t.port(token)
        self.tx=self.executor.adopt_transaction(self.port,isolation='read_committed',access_mode='read_write').value
        self.boundary.release_operation(token)
        self.service=NativeArbitration(self.executor);self.runner=NativeOperationRunner(self.service)

    def slow_statement(self):
        sql='SELECT :value::pg_catalog.text FROM pg_catalog.pg_sleep(1.5)'
        # Explicit native qualification fixture, never a shipped SQL registration.
        with patch.dict(self.runner.QUALIFIED_STATEMENTS,{sql:'SELECT'}):
            return self.runner.register(sql,'SELECT')

    def statement(self):
        return self.runner.register('SELECT :value::pg_catalog.text','SELECT')

    def test_pre_cancel_has_no_native_statement(self):
        handle=self.runner.cancellation();handle.request()
        before=self.boundary.last_call
        result=self.runner.execute(self.tx,self.statement(),{'value':'unused'},cancellation=handle)
        self.assertEqual(result.error.code,'cancelled')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)

    def test_active_native_cancel_contains_and_preserves_host(self):
        self.boundary.run("INSERT INTO truss_operation_fixture VALUES ('host-before')")
        handle=self.runner.cancellation();submitted=Event()
        original=handle._submitted
        def publish():original();submitted.set()
        with patch.object(handle,'_submitted',side_effect=publish):
            with ThreadPoolExecutor(max_workers=1) as worker:
                future=worker.submit(self.runner.execute,self.tx,self.slow_statement(),{'value':'slow'},cancellation=handle)
                self.assertTrue(submitted.wait(2));handle.request()
                result=future.result(timeout=4)
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.code,'cancelled')
        self.assertTrue(handle._entry.eof)
        self.assertTrue(handle._entry.native.capture_complete)
        self.assertEqual(handle._entry.native.final_status,b'E')
        self.assertIsNone(self.boundary._operation)
        self.assertIsNone(self.boundary._cancel_pending)
        self.assertEqual(self.boundary.run('SELECT value FROM truss_operation_fixture'),[['host-before']])
        self.assertIsInstance(self.runner.execute(self.tx,self.statement(),{'value':'after'}),Ok)

    def test_request_during_prepare_is_unsent_and_contained(self):
        handle=self.runner.cancellation();prepare=self.boundary.prepare
        def prepared(*args,**kwargs):
            result=prepare(*args,**kwargs);self.assertEqual(handle.request(),'latched');return result
        with patch.object(self.boundary,'prepare',side_effect=prepared):
            result=self.runner.execute(self.tx,self.statement(),{'value':'unused'},cancellation=handle)
        self.assertEqual(result.error.code,'cancelled')
        self.assertIsNone(handle._entry)
        self.assertIsNone(self.boundary._operation)
        self.assertIsInstance(self.runner.execute(self.tx,self.statement(),{'value':'after'}),Ok)

    def test_whole_call_completion_wins_late_request(self):
        handle=self.runner.cancellation();drained=handle._drained
        def complete(entry,native):
            drained(entry,native)
        with patch.object(handle,'_drained',side_effect=complete):
            result=self.runner.execute(self.tx,self.statement(),{'value':'known'},cancellation=handle)
        self.assertIsInstance(result,Ok,repr(result));native=handle._entry.native
        self.assertEqual(handle.request(),'settled')
        self.assertFalse(handle._entry.reserved)
        self.assertIs(handle._entry.native,native)

    def test_eof_barrier_blocks_handback_after_native_drain(self):
        handle=self.runner.cancellation();submitted=Event();sending=Event();resume=Event();settling=Event()
        original=handle._submitted;send=handle._send;settle=handle._settle
        def publish():original();submitted.set()
        def held(entry):sending.set();self.assertTrue(resume.wait(2));send(entry)
        def waiting():settling.set();settle()
        with patch.object(handle,'_submitted',side_effect=publish),patch.object(handle,'_send',side_effect=held),patch.object(handle,'_settle',side_effect=waiting):
            with ThreadPoolExecutor(max_workers=2) as worker:
                future=worker.submit(self.runner.execute,self.tx,self.slow_statement(),{'value':'complete'},cancellation=handle)
                self.assertTrue(submitted.wait(2));request=worker.submit(handle.request)
                self.assertTrue(sending.wait(1));self.assertTrue(settling.wait(2))
                self.assertFalse(self.boundary._calling)
                self.assertTrue(handle._entry.native.capture_complete)
                self.assertIs(self.boundary._cancel_pending,handle._entry)
                with self.assertRaises(NativeBoundaryRefusal):self.boundary.run('SELECT 1')
                with self.assertRaises(NativeBoundaryRefusal):self.boundary.release_operation(self.boundary._operation)
                resume.set();request.result(timeout=2);result=future.result(timeout=3)
        self.assertIsInstance(result,Ok,repr(result))
        self.assertIsNone(self.boundary._cancel_pending)

    def test_transport_failure_retains_native_success_and_quarantines(self):
        handle=self.runner.cancellation();original=handle._submitted
        def publish():
            original();handle.request()
        with patch.object(handle,'_submitted',side_effect=publish),patch.object(handle,'_send',side_effect=OSError('private')):
            result=self.runner.execute(self.tx,self.statement(),{'value':'known'},cancellation=handle)
        self.assertEqual(result.error.code,'transaction_unusable')
        entry=handle._entry
        self.assertTrue(entry.native.capture_complete)
        self.assertFalse(entry.native.driver_raised)
        self.assertTrue(entry.failed)
        self.assertIs(self.boundary._cancel_pending,entry)
        self.assertTrue(self.boundary._quarantined)
        with self.assertRaises(NativeBoundaryRefusal):self.boundary.run('SELECT 1')

    def test_foreign_and_reused_handles_refuse_before_native(self):
        before=self.boundary.last_call
        foreign=NativeCancellation(object())
        result=self.runner.execute(self.tx,self.statement(),{'value':'unused'},cancellation=foreign)
        self.assertEqual(result.error.code,'execution_obligation');self.assertIs(self.boundary.last_call,before)
        handle=self.runner.cancellation()
        self.assertIsInstance(self.runner.execute(self.tx,self.statement(),{'value':'first'},cancellation=handle),Ok)
        before=self.boundary.last_call
        result=self.runner.execute(self.tx,self.statement(),{'value':'again'},cancellation=handle)
        self.assertEqual(result.error.code,'execution_obligation');self.assertIs(self.boundary.last_call,before)

    def test_unbounded_main_socket_profile_is_effectfree_refusal(self):
        self.connection._usock.settimeout(None)
        handle=self.runner.cancellation();before=self.boundary.last_call
        result=self.runner.execute(self.tx,self.statement(),{'value':'unused'},cancellation=handle)
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertFalse(self.boundary._quarantined)
        self.assertIs(self.boundary.last_call,before)

    def test_latched_request_after_preexecute_check_dispatches_once(self):
        handle=self.runner.cancellation();check=handle._is_requested;calls=[];send=handle._send
        def latch():
            result=check();handle.request();return result
        def dispatch(entry):calls.append(entry);send(entry)
        with patch.object(handle,'_is_requested',side_effect=latch),patch.object(handle,'_send',side_effect=dispatch):
            result=self.runner.execute(self.tx,self.slow_statement(),{'value':'cancel'},cancellation=handle)
        self.assertEqual(result.error.code,'cancelled')
        self.assertEqual(calls,[handle._entry]);self.assertTrue(handle._entry.eof)

    def test_duplicate_requests_never_send_twice(self):
        handle=self.runner.cancellation();submitted=Event();sending=Event();resume=Event();calls=[]
        original=handle._submitted;send=handle._send
        def publish():original();submitted.set()
        def held(entry):calls.append(entry);sending.set();self.assertTrue(resume.wait(1));send(entry)
        with patch.object(handle,'_submitted',side_effect=publish),patch.object(handle,'_send',side_effect=held):
            with ThreadPoolExecutor(max_workers=2) as worker:
                future=worker.submit(self.runner.execute,self.tx,self.slow_statement(),{'value':'cancel'},cancellation=handle)
                self.assertTrue(submitted.wait(1));request=worker.submit(handle.request)
                self.assertTrue(sending.wait(1));self.assertEqual(handle.request(),'retained')
                resume.set();request.result(timeout=2);result=future.result(timeout=3)
        self.assertEqual(result.error.code,'cancelled');self.assertEqual(calls,[handle._entry])

    def test_disposal_retains_reserved_cancellation_cleanup(self):
        handle=self.runner.cancellation();submitted=Event();original=handle._submitted
        def publish():original();submitted.set()
        with patch.object(handle,'_submitted',side_effect=publish):
            with ThreadPoolExecutor(max_workers=1) as worker:
                future=worker.submit(self.runner.execute,self.tx,self.slow_statement(),{'value':'cancel'},cancellation=handle)
                self.assertTrue(submitted.wait(1));self.executor.dispose();handle.request()
                result=future.result(timeout=3)
        self.assertEqual(result.error.code,'cancelled')
        self.assertIsNone(self.boundary._operation)
        self.assertFalse(self.boundary._quarantined)
        self.assertIsInstance(self.runner.execute(self.tx,self.statement(),{'value':'later'}),Error)

    def test_same_handle_concurrent_claim_loser_does_not_quarantine_winner(self):
        handle=self.runner.cancellation();binding=Event();resume=Event();bind=handle._bind
        def held(*args):binding.set();self.assertTrue(resume.wait(1));return bind(*args)
        with patch.object(handle,'_bind',side_effect=held):
            with ThreadPoolExecutor(max_workers=1) as worker:
                future=worker.submit(self.runner.execute,self.tx,self.statement(),{'value':'first'},cancellation=handle)
                self.assertTrue(binding.wait(1));before=self.boundary.last_call
                loser=self.runner.execute(self.tx,self.statement(),{'value':'second'},cancellation=handle)
                self.assertEqual(loser.error.code,'execution_obligation')
                self.assertIs(self.boundary.last_call,before);self.assertFalse(self.boundary._quarantined)
                resume.set();self.assertIsInstance(future.result(timeout=3),Ok)

    def test_cancel_state_does_not_expose_key_in_repr(self):
        handle=self.runner.cancellation()
        self.assertIsInstance(self.runner.execute(self.tx,self.statement(),{'value':'known'},cancellation=handle),Ok)
        self.assertNotIn(repr(self.connection._backend_key_data),repr(handle))
        self.assertNotIn(repr(handle._packet),repr(handle._entry))

    def test_cancel_before_admission_after_binding_runs_no_sql(self):
        handle=self.runner.cancellation();bind=handle._bind
        def latched(*args):
            result=bind(*args);handle.request();return result
        before=self.boundary.last_call
        with patch.object(handle,'_bind',side_effect=latched):
            result=self.runner.execute(self.tx,self.statement(),{'value':'unused'},cancellation=handle)
        self.assertEqual(result.error.code,'cancelled')
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)
        self.assertTrue(handle._channel_closed)

    def test_auxiliary_socket_allocation_failure_does_not_poison_host(self):
        handle=self.runner.cancellation();before=self.boundary.last_call
        with patch('truss._native_cancellation._new_channel',side_effect=MemoryError) as factory:
            result=self.runner.execute(self.tx,self.statement(),{'value':'unused'},cancellation=handle)
        factory.assert_called_once()
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertFalse(self.boundary._quarantined)
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(self.boundary._operation)

    def test_unused_channel_closure_precedes_completion_handback(self):
        handle=self.runner.cancellation();bind=handle._bind
        class BrokenClose:
            def __init__(self,original):self.original=original
            def close(self):self.original.close();raise OSError('private close failure')
        def bound(*args):
            result=bind(*args);handle._channel=BrokenClose(handle._channel);return result
        with patch.object(handle,'_bind',side_effect=bound):
            result=self.runner.execute(self.tx,self.statement(),{'value':'known'},cancellation=handle)
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(handle._closure_failed)
        self.assertIsNotNone(self.boundary._operation)
        self.assertFalse(self.runner._runs[-1].gate.detached)
        self.assertIsNone(self.runner._runs[-1].completion)
        self.assertEqual(handle.request(),'unresolved')

    def test_missing_original_drain_retains_eof_barrier(self):
        from truss._native_result_custody import NativeResultCustody
        handle=self.runner.cancellation();submitted=handle._submitted;messages=NativeResultCustody._messages
        def request():submitted();handle.request()
        def lost(gate,context):
            if gate.boundary._active_cancellation is None:
                return messages(gate,context)
            try:return messages(gate,context)
            finally:raise OSError('original drain return lost')
        with patch.object(handle,'_submitted',side_effect=request),patch.object(NativeResultCustody,'_messages',lost):
            result=self.runner.execute(self.tx,self.slow_statement(),{'value':'unknown'},cancellation=handle)
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(handle._entry.eof)
        self.assertFalse(handle._entry.native.capture_complete)
        self.assertIs(self.boundary._cancel_pending,handle._entry)
        self.assertEqual(handle.request(),'unresolved')

    def test_transport_timeout_never_becomes_cancelled_success(self):
        handle=self.runner.cancellation();submitted=handle._submitted
        def request():submitted();handle.request()
        with patch.object(handle,'_submitted',side_effect=request),patch.object(handle,'_send',side_effect=TimeoutError):
            result=self.runner.execute(self.tx,self.statement(),{'value':'known'},cancellation=handle)
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(handle._entry.native.capture_complete)
        self.assertTrue(handle._entry.failed)
        self.assertIs(self.boundary._cancel_pending,handle._entry)

    def test_second_profile_refusal_closes_channel_before_release(self):
        handle=self.runner.cancellation();release=self.boundary.release_operation
        observations=[]
        def releasing(*args,**kwargs):
            observations.append(handle._channel_closed)
            return release(*args,**kwargs)
        with patch.object(self.runner,'_profile',side_effect=[True,False]),patch.object(self.boundary,'release_operation',side_effect=releasing):
            result=self.runner.execute(self.tx,self.statement(),{'value':'unused'},cancellation=handle)
        self.assertEqual(result.error.code,'execution_obligation')
        self.assertEqual(observations,[True]);self.assertIsNone(self.boundary._operation)
        self.assertFalse(self.boundary._quarantined)

    def test_eof_notification_loss_retains_original_completed_facts(self):
        handle=self.runner.cancellation();submitted=handle._submitted
        observed=[]
        def requesting():
            submitted()
            with patch.object(handle._entry.finished,'set',side_effect=MemoryError):
                try:handle.request()
                except MemoryError:observed.append('lost')
        with patch.object(handle,'_submitted',side_effect=requesting):
            result=self.runner.execute(self.tx,self.slow_statement(),{'value':'cancel'},cancellation=handle)
        self.assertEqual(observed,['lost']);self.assertEqual(result.error.code,'cancelled')
        self.assertTrue(handle._entry.eof);self.assertTrue(handle._channel_closed)
        self.assertFalse(handle._entry.finished.is_set())
        self.assertIsNone(self.boundary._cancel_pending);self.assertIsNone(self.boundary._operation)

    def test_original_socket_profile_timeout_is_preserved(self):
        handle=self.runner.cancellation();timeout=self.connection._usock.gettimeout()
        self.assertIsInstance(self.runner.execute(self.tx,self.statement(),{'value':'known'},cancellation=handle),Ok)
        self.assertEqual(self.connection._usock.gettimeout(),timeout)

    def test_unexpected_cancel_reply_retains_original_error(self):
        handle=self.runner.cancellation();bind=handle._bind;submitted=handle._submitted
        class UnexpectedReply:
            def __init__(self,original):self.original=original
            def settimeout(self,value):return self.original.settimeout(value)
            def connect(self,peer):return self.original.connect(peer)
            def sendall(self,packet):return self.original.sendall(packet)
            def recv(self,size):self.original.recv(size);return b'x'
            def close(self):return self.original.close()
        def bound(*args):
            result=bind(*args);handle._channel=UnexpectedReply(handle._channel);return result
        def requesting():submitted();handle.request()
        with patch.object(handle,'_bind',side_effect=bound),patch.object(handle,'_submitted',side_effect=requesting):
            result=self.runner.execute(self.tx,self.slow_statement(),{'value':'cancel'},cancellation=handle)
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertTrue(handle._entry.native.capture_complete)
        self.assertTrue(any(event.code==b'E' for event in handle._entry.native.events))
        self.assertTrue(handle._entry.failed);self.assertFalse(handle._entry.eof)
        self.assertIs(self.boundary._cancel_pending,handle._entry)

    def test_request_after_execute_send_before_sync_stays_latched(self):
        import socket
        self.boundary.run("INSERT INTO truss_operation_fixture VALUES('host-before')")
        handle=self.runner.cancellation();original=socket.socket.sendall;observed=[]
        def send(sock,data,*args,**kwargs):
            value=original(sock,data,*args,**kwargs)
            resource=self.boundary._active_resource
            if sock is self.connection._usock and resource is not None and resource[0]=='execute' and data[:1]==b'E':
                observed.append(handle.request())
                self.assertFalse(handle._entry.submitted)
                self.assertFalse(handle._entry.reserved)
            return value
        with patch.object(socket.socket,'sendall',send):
            result=self.runner.execute(self.tx,self.slow_statement(),{'value':'cancel'},cancellation=handle)
        self.assertTrue(observed);self.assertEqual(result.error.code,'cancelled')
        self.assertTrue(handle._entry.submitted);self.assertTrue(handle._entry.eof)
        self.assertIsNone(self.boundary._operation)
        self.assertEqual(self.boundary.run('SELECT value FROM truss_operation_fixture'),[['host-before']])
    def test_sync_send_failure_after_execute_is_unknown_not_unsent(self):
        import socket
        handle=self.runner.cancellation();original=socket.socket.sendall
        def send(sock,data,*args,**kwargs):
            resource=self.boundary._active_resource
            if sock is self.connection._usock and resource is not None and resource[0]=='execute':
                if data[:1]==b'E':
                    value=original(sock,data,*args,**kwargs);handle.request();return value
                if data==b'S\x00\x00\x00\x04':raise OSError('Sync send failed')
            return original(sock,data,*args,**kwargs)
        with patch.object(socket.socket,'sendall',send):
            result=self.runner.execute(self.tx,self.statement(),{'value':'unknown'},cancellation=handle)
        self.assertEqual(result.error.code,'transaction_unusable')
        self.assertFalse(handle._entry.submitted);self.assertFalse(handle._entry.reserved)
        self.assertTrue(self.boundary._quarantined);self.assertIsNotNone(self.boundary._operation)
        writer=self.runner._runs[-1].gate.outbound
        writes=[w for w in writer.ordinary if w is not None and w.call is handle._entry.call]
        self.assertTrue(any(w.data[:1]==b'E' and w.native_returned for w in writes))
        self.assertFalse(writes[-1].native_returned);self.assertFalse(handle._entry.native.capture_complete)
    def test_direct_submission_publication_loss_retains_sent_facts(self):
        handle=self.runner.cancellation()
        with patch.object(handle,'_submitted',side_effect=OSError('Submission publication lost')):
            result=self.runner.execute(self.tx,self.statement(),{'value':'sent'},cancellation=handle)
        self.assertEqual(result.error.code,'transaction_unusable')
        writer=self.runner._runs[-1].gate.outbound
        self.assertTrue(all(w.native_returned and w.settled for w in writer.barrier.writes))
        self.assertEqual(writer.barrier.writes[-1].data,b'S\x00\x00\x00\x04')
        self.assertFalse(handle._entry.submitted);self.assertTrue(self.boundary._quarantined)
