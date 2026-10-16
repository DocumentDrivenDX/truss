"""Actual socket/BufferedRWPair deadline restoration and original failure custody."""
import socket
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from truss._native_deadline import NativeOperationDeadline, NativeDeadlineExpired
from truss._native_ingress_deadline import NativeIngressDeadline

class IngressDeadlineTests(unittest.TestCase):
    def setUp(self):
        self.sock,self.peer=socket.socketpair()
        self.stream=self.sock.makefile('rwb')
        self.addCleanup(self.peer.close);self.addCleanup(self.sock.close);self.addCleanup(self.stream.close)
        self.now=[0]
        self.clock=patch('truss._native_deadline.monotonic_ns',side_effect=lambda:self.now[0])
        self.clock.start();self.addCleanup(self.clock.stop)
        self.deadline=NativeOperationDeadline(30,5)
        self.con=SimpleNamespace(_sock=self.stream,_usock=self.sock)
        self.boundary=SimpleNamespace(_connection=self.con,_original_stream=self.stream,_original_socket=self.sock,_quarantined=False)
        self.gate=SimpleNamespace(boundary=self.boundary,original_sock=self.stream,failed=False)
    def guard(self,timeout=None):
        self.sock.settimeout(timeout)
        guard=NativeIngressDeadline(self.gate,self.deadline)
        self.con._sock=self.gate
        return guard
    def test_success_restores_original_none_timeout(self):
        guard=self.guard();self.peer.sendall(b'abc')
        target=bytearray(3)
        self.assertEqual(guard.receive(self.stream,target),3)
        self.assertEqual(target,b'abc');self.assertIsNone(self.sock.gettimeout())
        self.assertFalse(self.gate.failed)
    def test_stricter_host_timeout_wins_and_is_restored(self):
        guard=self.guard(0.005);original=socket.socket.settimeout; observed=[]
        def setter(sock,value):
            if sock is self.sock:observed.append(value)
            return original(sock,value)
        with patch.object(socket.socket,'settimeout',setter):
            with self.assertRaises(TimeoutError):guard.receive(self.stream,bytearray(1))
        self.assertEqual(observed,[0.005,0.005])
        self.assertEqual(self.sock.gettimeout(),0.005)
        self.assertTrue(self.gate.failed);self.assertTrue(self.boundary._quarantined)
    def test_partial_setter_reply_loss_still_restores_baseline(self):
        guard=self.guard(0.5);original=socket.socket.settimeout; calls=[]
        def setter(sock,value):
            result=original(sock,value)
            if sock is self.sock:
                calls.append(value)
                if len(calls)==1:raise OSError('Lost setter reply')
            return result
        with patch.object(socket.socket,'settimeout',setter):
            with self.assertRaises(OSError):guard.receive(self.stream,bytearray(1))
        self.assertEqual(calls,[0.03,0.5]);self.assertEqual(self.sock.gettimeout(),0.5)
        self.assertTrue(self.gate.failed);self.assertTrue(self.boundary._quarantined)
    def test_restoration_failure_quarantines_successful_bytes(self):
        guard=self.guard();self.peer.sendall(b'x');original=socket.socket.settimeout;calls=[]
        def setter(sock,value):
            if sock is self.sock:
                calls.append(value)
                if len(calls)==2:raise OSError('Restoration unavailable')
            return original(sock,value)
        with patch.object(socket.socket,'settimeout',setter):
            with self.assertRaises(OSError):guard.receive(self.stream,bytearray(1))
        self.assertIsNotNone(guard.restoration_failure)
        self.assertTrue(self.gate.failed);self.assertTrue(self.boundary._quarantined)
    def test_buffered_only_read_cannot_ignore_expired_clock(self):
        guard=self.guard();self.peer.sendall(b'abcdef')
        self.assertEqual(guard.receive(self.stream,bytearray(1)),1)
        self.now[0]=30000000
        with self.assertRaises(NativeDeadlineExpired):guard.receive(self.stream,bytearray(1))
        self.assertIsNone(self.sock.gettimeout());self.assertTrue(self.gate.failed)
    def test_changed_timeout_refuses_without_overwriting_host_mutation(self):
        guard=self.guard();self.sock.settimeout(0.5)
        with self.assertRaises(RuntimeError):guard.receive(self.stream,bytearray(1))
        self.assertEqual(self.sock.gettimeout(),0.5);self.assertTrue(self.gate.failed)
    def test_baseexception_during_setter_restores_timeout(self):
        guard=self.guard();original=socket.socket.settimeout;calls=[]
        def setter(sock,value):
            result=original(sock,value)
            if sock is self.sock:
                calls.append(value)
                if len(calls)==1:raise KeyboardInterrupt()
            return result
        with patch.object(socket.socket,'settimeout',setter):
            with self.assertRaises(KeyboardInterrupt):guard.receive(self.stream,bytearray(1))
        self.assertIsNone(self.sock.gettimeout());self.assertTrue(self.boundary._quarantined)

    def test_settlement_phase_uses_same_original_remaining_clock(self):
        guard=self.guard();self.now[0]=30000000;self.deadline.begin_settlement()
        self.peer.sendall(b'x');original=socket.socket.settimeout;values=[]
        def setter(sock,value):
            if sock is self.sock:values.append(value)
            return original(sock,value)
        with patch.object(socket.socket,'settimeout',setter):
            self.assertEqual(guard.receive(self.stream,bytearray(1)),1)
        self.assertEqual(values,[0.005,None])
        self.assertEqual(self.deadline.settlement_cutoff_ns,35000000)
    def test_post_read_expiry_restores_timeout_before_refusal(self):
        guard=self.guard(0.5);self.peer.sendall(b'x')
        with patch('truss._native_deadline.monotonic_ns',side_effect=[0,30000000]):
            with self.assertRaises(NativeDeadlineExpired):guard.receive(self.stream,bytearray(1))
        self.assertEqual(self.sock.gettimeout(),0.5);self.assertTrue(self.gate.failed)
    def test_failed_original_ingress_cannot_retry(self):
        guard=self.guard(0.001)
        with self.assertRaises(TimeoutError):guard.receive(self.stream,bytearray(1))
        original_failure=guard.failure
        with patch.object(socket.socket,'settimeout',side_effect=AssertionError('No retry setter')):
            with self.assertRaises(RuntimeError):guard.receive(self.stream,bytearray(1))
        self.assertIs(guard.failure,original_failure)
    def test_foreign_stream_or_socket_is_not_selected(self):
        from truss._native_pg8000 import NativeBoundaryRefusal
        self.con._sock=object()
        with self.assertRaises(NativeBoundaryRefusal):NativeIngressDeadline(self.gate,self.deadline)
        self.con._sock=self.stream;self.con._usock=object()
        with self.assertRaises(NativeBoundaryRefusal):NativeIngressDeadline(self.gate,self.deadline)
