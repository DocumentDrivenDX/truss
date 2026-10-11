"""Direct socket primitive ledger tests; synthetic basis is not native qualification."""
import socket
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from time import monotonic
import test_native_ingress_deadline as ingress
from truss._native_outbound import NativeOutbound
from truss._native_pg8000 import NativeCall, NativeBoundaryRefusal
from truss._native_result_custody import NativeTextLimits

class OutboundTests(unittest.TestCase):
    setUp=ingress.IngressDeadlineTests.setUp
    guard=ingress.IngressDeadlineTests.guard
    def writer(self,limits=None):
        guard=self.guard()
        self.boundary._revision=1;self.boundary._calling=False
        self.boundary.last_call=NativeCall((),False,True,b'T',revision=1)
        self.call=SimpleNamespace(native_call=None)
        self.session=SimpleNamespace(calls=(self.call,),cleanup_calls=())
        self.gate.session=self.session;self.gate._cleanup_mode=lambda:False
        self.writer_guard=guard
        writer=NativeOutbound(self.gate,guard,limits or NativeTextLimits())
        self.boundary._operation_ledger=self.session
        self.boundary._revision=2;self.boundary._calling=True
        self.boundary._active_resource=('execute',object())
        return writer
    def test_exact_bytes_order_and_frozen_record(self):
        writer=self.writer();source=b'BC'
        self.assertEqual(writer.write(b'A\0'),2);self.assertEqual(writer.write(source),2)
        self.assertIs(writer.ordinary[1].data,source)
        writer.flush()
        self.assertEqual(self.peer.recv(4),b'A\0BC')
        self.assertEqual(tuple(w.data for w in writer.barrier.writes),(b'A\0',b'BC'))
        self.assertTrue(all(w.native_returned and w.settled for w in writer.barrier.writes))
        self.assertIsNone(self.sock.gettimeout())
    def test_mutable_bytes_refused_before_retention_or_send(self):
        writer=self.writer()
        with self.assertRaises(NativeBoundaryRefusal):writer.write(bytearray(b'BC'))
        self.assertEqual(writer.ordinary_count,0)
        self.assertIsNone(writer.barrier)
        self.peer.settimeout(0.005)
        with self.assertRaises(TimeoutError):self.peer.recv(1)
    def test_actual_backpressure_timeout_retains_unknown_prefix(self):
        writer=self.writer();self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,4096)
        started=monotonic()
        with self.assertRaises(TimeoutError):writer.write(b'x'*1048576)
        self.assertLess(monotonic()-started,1)
        self.assertIsInstance(self.writer_guard.failure,TimeoutError)
        entry=writer.ordinary[0]
        self.assertFalse(entry.native_returned);self.assertFalse(entry.settled)
        self.assertIsNone(writer.barrier);self.assertTrue(self.boundary._quarantined)
        self.assertIsNone(self.sock.gettimeout())
        self.peer.settimeout(0.1);prefix=self.peer.recv(4096)
        self.assertTrue(prefix);self.assertEqual(prefix,b'x'*len(prefix))
    def test_send_return_survives_timeout_restoration_failure(self):
        writer=self.writer();original=socket.socket.settimeout;calls=[]
        def setter(sock,value):
            if sock is self.sock:
                calls.append(value)
                if len(calls)==2:raise OSError('Restoration failure')
            return original(sock,value)
        with patch.object(socket.socket,'settimeout',setter):
            with self.assertRaises(OSError):writer.write(b'exact')
        entry=writer.ordinary[0]
        self.assertTrue(entry.native_returned);self.assertFalse(entry.settled)
        self.assertEqual(self.peer.recv(5),b'exact');self.assertIsNone(writer.barrier)
        self.assertTrue(self.boundary._quarantined)
    def test_record_capacity_refuses_before_second_send(self):
        writer=self.writer(NativeTextLimits(outbound_records=1))
        writer.write(b'x')
        with self.assertRaises(NativeBoundaryRefusal):writer.write(b'y')
        self.assertEqual(self.peer.recv(1),b'x')
        self.peer.settimeout(0.005)
        with self.assertRaises(TimeoutError):self.peer.recv(1)
        self.assertEqual(writer.ordinary_count,1);self.assertTrue(self.boundary._quarantined)
    def test_native_error_ready_does_not_establish_empty_baseline(self):
        writer=self.writer();self.boundary._calling=False;self.boundary._revision=3
        self.boundary.last_call=NativeCall((),True,True,b'T',revision=3)
        with self.assertRaises(NativeBoundaryRefusal):NativeOutbound(self.gate,self.writer_guard,NativeTextLimits())
    def test_foreign_revision_cannot_establish_empty_baseline(self):
        writer=self.writer();self.boundary._calling=False
        with self.assertRaises(NativeBoundaryRefusal):NativeOutbound(self.gate,self.writer_guard,NativeTextLimits())
