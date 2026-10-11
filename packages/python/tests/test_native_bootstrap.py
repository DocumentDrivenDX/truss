"""Fresh original construction without uncaptured setup SQL or fabricated idle."""
import unittest
import importlib.util
from unittest.mock import patch
from dataclasses import replace
import test_host_control_custody as custody
if importlib.util.find_spec("pg8000"):
    from truss._native_bootstrap import NativeConnectionFactory, BootstrapFailure
from truss._native_pg8000 import NativeBoundary, NativeBoundaryRefusal
from truss._native_operation import NativeOperationRunner
if importlib.util.find_spec("pg8000"):
    from truss._startup_custody import attach_startup, startup_outbound_basis
from truss.execution import Ok

class NativeBootstrapTests(custody.NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):self.factory=NativeConnectionFactory()
    def tearDown(self):
        for record in self.factory._records:
            if record.exposed:
                record.connection._sock=record.stream
                record.connection.close()
            elif not record.closed:record.close_owned(recovery=True)
    def connect(self,**kwargs):
        options=dict(user='postgres',database='postgres',unix_sock=self.kwargs['unix_sock']);options.update(kwargs)
        return self.factory.connect(**options)
    def test_original_show_precedes_tracker_and_complete_host_workflow(self):
        boundary=self.connect();record=self.factory._records[-1]
        self.assertEqual(record.witness.phase,'consumed')
        self.assertEqual(boundary._revision,1)
        self.assertIsNone(boundary._transaction_tracker)
        self.assertEqual(boundary.last_call.final_status,b'I')
        self.assertEqual(tuple(e.payload for e in boundary.last_call.events if e.code==b'C'),(b'SHOW\0',))
        self.assertIs(record.completion[0],boundary.last_call)
        self.assertTrue(record.ledger.result_custody.detached)
        self.assertIsNone(boundary._operation)
        self.assertIsNone(boundary._operation_ledger)
        from pg8000.core import CoreConnection
        self.assertIs(record.connection.close.__func__,CoreConnection.close)
        executor=custody.HostExecutor();tracker=custody.NativeTransactions(boundary)
        service=custody.NativeArbitration(executor);producer=custody.HostControlCustody(executor)
        session=custody.NativeHostSession(executor,tracker,service,control_producer=producer)
        self.assertIsInstance(session.observe_host_resource_baseline(),Ok)
        self.assertIsInstance(session.begin(),Ok)
        tx=session.adopt_transaction().value
        runner=NativeOperationRunner(service);statement=runner.register('SELECT :value::pg_catalog.text','SELECT')
        self.assertEqual(runner.execute(tx,statement,{'value':'exact'}).value,(('exact',),))
        self.assertEqual(session.commit().value.state,'committed')
        self.assertFalse(record.close_attempted)
        from truss._startup_custody import StartupRefusal
        with self.assertRaises(StartupRefusal):record.close_owned()
    def test_existing_connection_cannot_claim_fresh_witness(self):
        connection=self.Connection(**self.kwargs)
        try:
            with self.assertRaises(NativeBoundaryRefusal):NativeBoundary(connection)
            with self.assertRaises(NativeBoundaryRefusal):NativeBoundary(connection,startup=object())
            self.assertIsNone(connection._transaction_status)
            self.assertFalse(hasattr(connection,'_truss_native_boundary'))
        finally:connection.close()
    def test_copied_replayed_and_foreign_witness_refuse(self):
        boundary=self.connect();witness=self.factory._records[-1].witness
        self.assertFalse(startup_outbound_basis(boundary))
        for candidate in (witness,replace(witness),object()):
            with self.assertRaises(ValueError):attach_startup(candidate,boundary._connection,object())
        other=self.Connection(**self.kwargs)
        try:
            with self.assertRaises(NativeBoundaryRefusal):NativeBoundary(other,startup=witness)
            self.assertIsNone(other._transaction_status)
        finally:other.close()
    def test_changed_constructor_refuses_without_creating_connection(self):
        from pg8000.core import CoreConnection
        with patch.object(CoreConnection,'__init__',side_effect=AssertionError('Must not invoke changed source')):
            with self.assertRaises(NativeBoundaryRefusal):self.connect()
        self.assertEqual(self.factory._records,())
    def test_closed_options_refuse_before_creation(self):
        for kwargs in ({'timeout':None},{'timeout':True},{'timeout':0},{'timeout':float('inf')},{'timeout':3}):
            with self.subTest(kwargs=kwargs),self.assertRaises(NativeBoundaryRefusal):self.connect(**kwargs)
        self.assertEqual(self.factory._records,())
    def test_lost_publication_retains_one_show_and_closes_unexposed_connection(self):
        with patch.object(self.factory,'_publish',side_effect=MemoryError('Publication unavailable')):
            with self.assertRaises(BootstrapFailure) as error:self.connect()
        record=error.exception.record
        self.assertEqual(len(record.ledger.calls),1)
        self.assertEqual(record.witness.boundary._revision,1)
        self.assertTrue(record.closed)
        self.assertFalse(record.exposed)
        self.assertEqual(record.witness.phase,'consumed')
        self.assertIsNotNone(record.completion)
    def test_one_use_witness_cannot_submit_second_show(self):
        boundary=self.connect();record=self.factory._records[-1]
        before=boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):record.ledger.simple_query('SHOW transaction_read_only')
        self.assertIs(boundary.last_call,before)
        self.assertEqual(len(record.ledger.calls),1)
    def test_arbitrary_nominal_issuer_cannot_attach_existing_writer(self):
        from truss._startup_custody import StartupProducer, StartupWitness, StartupRefusal
        connection=self.Connection(**self.kwargs)
        try:
            with self.assertRaises(StartupRefusal):StartupProducer(object())
            forged=object.__new__(StartupProducer)
            forged.factory=object();forged._witnesses=()
            witness=StartupWitness(forged,object(),connection,phase='created')
            forged._witnesses=(witness,)
            with self.assertRaises(NativeBoundaryRefusal):NativeBoundary(connection,startup=witness)
            self.assertIsNone(connection._transaction_status)
            self.assertFalse(hasattr(connection,'_truss_native_boundary'))
        finally:connection.close()
    def test_native_constructor_error_invokes_private_owned_cleanup_hook(self):
        with self.assertRaises(BootstrapFailure) as error:self.connect(database='missing_bootstrap_database')
        record=error.exception.record
        self.assertTrue(record.close_attempted)
        self.assertTrue(record.closed)
        self.assertIsNotNone(record.stream)
        self.assertIsNotNone(record.socket)
        self.assertFalse(record.constructor_completed)
        self.assertIsNone(record.ledger)
        self.assertEqual(record.witness.phase,'creating')
    def test_first_show_frame_budget_failure_retains_consumed_witness(self):
        from truss._native_result_custody import NativeTextLimits
        with self.assertRaises(BootstrapFailure) as error:self.connect(limits=NativeTextLimits(frame_bytes=4,contexts=8))
        record=error.exception.record
        self.assertTrue(record.closed)
        self.assertEqual(record.witness.phase,'attached')
        self.assertEqual(len(record.ledger.calls),0)
        self.assertIsNone(record.ledger.result_custody)
        self.assertIsNone(record.completion)
        self.assertFalse(record.exposed)
    def test_invalid_unicode_and_startup_option_injection_refuse_before_creation(self):
        for options in ({'database':'postgres\0application_name\0unapproved'},
                        {'user':'postgres\0options\0unapproved'},
                        {'unix_sock':self.kwargs['unix_sock']+'\0'},
                        {'user':'\ud800'},{'database':'\udfff'}, {'unix_sock':'relative'}):
            with self.subTest(options=options),self.assertRaises(NativeBoundaryRefusal):self.connect(**options)
        self.assertEqual(self.factory._records,())
    def test_selected_show_producer_mutation_refuses_before_creation(self):
        from pg8000.core import CoreConnection
        for name in ('send_QUERY','_send_message','handle_messages','handle_COMMAND_COMPLETE','handle_DATA_ROW'):
            with self.subTest(name=name),patch.object(CoreConnection,name,side_effect=AssertionError('Changed source')):
                with self.assertRaises(NativeBoundaryRefusal):self.connect()
        self.assertEqual(self.factory._records,())
    def test_lost_exposure_reply_recovers_original_boundary_without_second_show(self):
        original=self.factory._publish
        def publish(*args):original(*args);raise MemoryError('Lost exposure reply')
        with patch.object(self.factory,'_publish',publish):
            with self.assertRaises(BootstrapFailure) as error:self.connect()
        record=error.exception.record
        self.assertTrue(record.exposed);self.assertFalse(record.close_attempted)
        boundary=self.factory.recover(record);before=boundary.last_call
        self.assertIs(self.factory.recover(record),boundary)
        self.assertIs(boundary.last_call,before)
        self.assertEqual(len(record.ledger.calls),1)
        with self.assertRaises(NativeBoundaryRefusal):self.factory.recover(replace(record))

    def test_shutdown_before_effect_retains_buffer_without_flush(self):
        import truss._startup_custody as startup
        def publication(record,boundary):
            record.stream.write(b'Q\x00\x00\x00\x0dSELECT 1\x00')
            raise MemoryError('Unexposed queued writer')
        with patch.object(self.factory,'_publish',publication),patch.object(startup,'_SHUTDOWN',side_effect=OSError('Before effect')):
            with self.assertRaises(BootstrapFailure) as error:self.connect()
        record=error.exception.record
        self.assertFalse(record.closed)
        self.assertFalse(record.stream.closed)
        self.assertIn('stream_retained_after_unconfirmed_shutdown',record.cleanup_failures)
        self.assertEqual(len(record.ledger.calls),1)
        import struct
        pid=struct.unpack('!ii',record.connection._backend_key_data)[0]
        observer=self.Connection(**self.kwargs)
        try:
            self.assertEqual(observer.run('SELECT query FROM pg_catalog.pg_stat_activity WHERE pid=:pid',pid=pid),[['SHOW transaction_isolation']])
        finally:observer.close()
        record.close_owned(recovery=True)
        self.assertTrue(record.closed)
    def test_cleanup_interrupt_retains_original_handles_for_explicit_recovery(self):
        import truss._startup_custody as startup
        def publication(record,boundary):raise MemoryError('Unexposed')
        with patch.object(self.factory,'_publish',publication),patch.object(startup,'_SHUTDOWN',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.connect()
        record=self.factory._records[-1]
        self.assertTrue(record.close_attempted)
        self.assertFalse(record.closed)
        self.assertFalse(record.stream.closed)
        self.assertNotEqual(record.socket.fileno(),-1)
        self.assertIn('KeyboardInterrupt',record.cleanup_failures)
        record.close_owned(recovery=True)
        self.assertTrue(record.closed)
    def test_context_symbol_replacement_refuses_before_creation(self):
        from pg8000 import core
        with patch.object(core,'Context',object):
            with self.assertRaises(NativeBoundaryRefusal):self.connect()
        self.assertEqual(self.factory._records,())
    def test_expired_original_deadline_refuses_before_retaining_constructor(self):
        from truss._native_deadline import NativeOperationDeadline, NativeDeadlineExpired
        deadline=NativeOperationDeadline(1,1);deadline.ordinary_cutoff_ns=0
        with self.assertRaises(NativeDeadlineExpired):
            self.factory._producer.create(user='postgres',database='postgres',unix_sock=self.kwargs['unix_sock'],timeout=2,deadline=deadline)
        self.assertEqual(self.factory._records,())
    def test_explicit_cleanup_recovery_has_finite_attempt_allowance(self):
        import truss._startup_custody as startup
        with patch.object(self.factory,'_publish',side_effect=MemoryError),patch.object(startup,'_SHUTDOWN',side_effect=OSError):
            with self.assertRaises(BootstrapFailure) as error:self.connect()
            record=error.exception.record
            for _ in range(2):record.close_owned(recovery=True)
            self.assertEqual(record.cleanup_attempts,3)
            self.assertLessEqual(len(record.cleanup_failures),9)
        record.close_owned(recovery=True)
        self.assertTrue(record.closed)
        with self.assertRaises(startup.StartupRefusal):record.close_owned(recovery=True)
        self.assertEqual(record.cleanup_attempts,4)
