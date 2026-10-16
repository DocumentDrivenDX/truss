"""Original selected host simple-call flush witness; not a public SQL profile."""
import unittest
from dataclasses import replace
from unittest.mock import patch
import test_host_control_deadline as deadline
from truss.execution import Ok
from truss._native_pg8000 import HostSimpleWitness
from truss._native_outbound import confirmed_host_simple_basis

class HostSimpleRecoveryTests(deadline.custody.NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.boundary.run('SELECT 1')
        c=deadline.custody
        self.executor=c.HostExecutor();self.tracker=c.NativeTransactions(self.boundary)
        self.service=c.NativeArbitration(self.executor)
        self.producer=c.HostControlCustody(self.executor)
        self.session=c.NativeHostSession(self.executor,self.tracker,self.service,control_producer=self.producer)
    baseline=deadline.HostControlDeadlineTests.baseline
    def test_duplicate_error_rollback_to_preserves_earlier_host_write(self):
        self.boundary.run('CREATE TEMP TABLE simple_recovery(value int PRIMARY KEY)')
        self.baseline();self.session.begin();tx=self.session.adopt_transaction().value
        self.boundary.run('INSERT INTO simple_recovery VALUES(1)')
        sp=self.session.savepoint(tx).value
        with self.assertRaises(Exception):self.boundary.run('INSERT INTO simple_recovery VALUES(1)')
        before=self.boundary.last_call
        self.assertTrue(before.capture_complete);self.assertTrue(before.driver_raised)
        self.assertTrue(confirmed_host_simple_basis(self.boundary))
        self.assertIsInstance(self.session.rollback_to_savepoint(tx,sp),Ok)
        self.assertIsInstance(self.session.release_savepoint(tx,sp),Ok)
        self.assertEqual(self.boundary.run('SELECT value FROM simple_recovery'),[[1]])
        self.assertEqual(self.session.commit().value.state,'committed')
    def test_explicit_stream_none_and_ignored_types_are_simple(self):
        class Poison:
            def __iter__(self):raise AssertionError('Ignored types traversed')
        for params in ({'stream':None},{'types':Poison()},{'stream':None,'types':Poison()}):
            self.baseline();self.session.begin()
            with self.assertRaises(Exception):self.boundary.run('SELECT 1/0',**params)
            self.assertTrue(confirmed_host_simple_basis(self.boundary))
            self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_real_parameterized_parse_error_refuses_without_flush(self):
        self.baseline();self.session.begin()
        with self.assertRaises(Exception):self.boundary.run('SELECT :value::definitely_missing_type',value='x')
        before=self.boundary.last_call
        self.assertTrue(before.capture_complete);self.assertTrue(before.driver_raised)
        self.assertTrue(any(e.code==b'E' for e in before.events))
        self.assertIsNone(before.original_simple)
        self.assertFalse(confirmed_host_simple_basis(self.boundary))
        self.assertEqual(self.session.rollback().error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
        # Original host alias cleanup is outside the admitted recovery profile.
    def test_missing_and_foreign_witness_refuse_without_sql(self):
        self.baseline();self.session.begin()
        with self.assertRaises(Exception):self.boundary.run('SELECT 1/0')
        before=self.boundary.last_call;original=self.boundary._host_simple_witness
        for witness in (None,HostSimpleWitness(object(),before.revision),
                        HostSimpleWitness(self.boundary,before.revision+1)):
            self.boundary._host_simple_witness=witness
            self.assertEqual(self.session.rollback().error.code,'execution_obligation')
            self.assertIs(self.boundary.last_call,before)
            self.assertIsNone(self.boundary._operation)
        self.boundary._host_simple_witness=original
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_replaced_call_cannot_borrow_original_descriptor(self):
        self.baseline();self.session.begin()
        with self.assertRaises(Exception):self.boundary.run('SELECT 1/0')
        before=self.boundary.last_call
        for candidate in (replace(before),replace(before,revision=before.revision+1)):
            self.boundary.last_call=candidate
            self.assertEqual(self.session.rollback().error.code,'execution_obligation')
        self.boundary.last_call=before
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_non_none_stream_gets_no_simple_witness(self):
        self.baseline();self.session.begin()
        with self.assertRaises(Exception):self.boundary.run('SELECT 1/0',stream=object())
        before=self.boundary.last_call
        self.assertTrue(before.capture_complete)
        self.assertIsNone(before.original_simple)
        self.assertFalse(confirmed_host_simple_basis(self.boundary))
        self.assertEqual(self.session.rollback().error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
    def test_callback_cannot_claim_simple_path_with_boolean(self):
        self.baseline();self.session.begin()
        with self.assertRaises(Exception):
            self.boundary._call(lambda:self.connection.run('SELECT :value::definitely_missing_type',value='x'),host_simple=True)
        before=self.boundary.last_call
        self.assertTrue(before.capture_complete)
        self.assertIsNone(before.original_simple)
        self.assertEqual(self.session.rollback().error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
    def test_nominal_packet_owns_invocation_instead_of_callback(self):
        from truss._native_pg8000 import _HostSimpleInvocation
        self.baseline();self.session.begin()
        called=[]
        with self.assertRaises(Exception):
            self.boundary._call(lambda:called.append(True),host_simple=_HostSimpleInvocation('SELECT 1/0'))
        self.assertEqual(called,[])
        self.assertTrue(confirmed_host_simple_basis(self.boundary))
        self.assertEqual(self.session.rollback().value.state,'rolled_back')
    def test_real_describe_error_after_parse_keeps_queued_bind_unflushed(self):
        from pg8000.core import CoreConnection
        import pg8000.core as core
        self.baseline();self.session.begin();flushes=[];writes=[]
        original_flush=core._flush;original_write=core._write
        def flush(stream):
            flushes.append(len(writes));return original_flush(stream)
        def write(stream,data):
            writes.append(data);return original_write(stream,data)
        def describe(name):
            # Fault fixture: send a genuine missing-statement Describe after
            # successful original Parse; original Bind still queues behind it.
            return CoreConnection.send_DESCRIBE_STATEMENT(self.connection,b'missing_describe_fixture\0')
        with patch.object(self.connection,'send_DESCRIBE_STATEMENT',side_effect=describe),patch.object(core,'_flush',side_effect=flush),patch.object(core,'_write',side_effect=write):
            with self.assertRaises(Exception):self.boundary.run('SELECT :value::text',value='x')
        before=self.boundary.last_call
        self.assertTrue(before.capture_complete)
        codes=tuple(e.code for e in before.events)
        self.assertIn(b'1',codes);self.assertEqual(codes.count(b'Z'),2)
        self.assertLess(codes.index(b'Z'),codes.index(b'E'))
        self.assertEqual(len(flushes),2)
        self.assertTrue(any(data[:1]==b'B' for data in writes[flushes[-1]:]))
        self.assertIsNone(before.original_simple)
        self.assertEqual(self.session.rollback().error.code,'execution_obligation')
        self.assertIs(self.boundary.last_call,before)
