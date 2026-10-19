# SPDX-License-Identifier: MIT OR Apache-2.0
"""Logical frame limits and transport faults; no allocation accounting."""
import struct
import unittest
from truss._bounded_receive import BoundedReceiver

FRAME = b'Z' + struct.pack('!i', 5) + b'T'

class Transport:
    def __init__(self, data, observe=lambda: None):
        self.data, self.observe, self.calls = data, observe, 0
    def recv_into(self, view):
        self.calls += 1
        self.observe()
        n = min(len(view), len(self.data), 2)
        view[:n] = self.data[:n]
        self.data = self.data[n:]
        return n

class BoundedReceiveTests(unittest.TestCase):
    def receiver(self, data=FRAME, **options):
        transport = Transport(data)
        limits = dict(frame_bytes=6, total_bytes=12, messages=2, reads=8)
        limits.update(options)
        return transport, BoundedReceiver(transport, **limits)
    def test_partial_reads_preserve_exact_parts(self):
        transport, receiver = self.receiver()
        self.assertEqual(receiver.receive_parts(), (FRAME[:5], FRAME[5:]))
        self.assertEqual(transport.calls, 4)
    def test_malformed_and_oversized_frames_fail_permanently(self):
        for size in (3, 6, -1):
            transport, receiver = self.receiver(b'Z' + struct.pack('!i', size))
            with self.assertRaises(ValueError): receiver.receive()
            calls = transport.calls
            with self.assertRaises(ValueError): receiver.receive()
            self.assertEqual(transport.calls, calls)
    def test_wire_message_and_read_limits(self):
        for options in (dict(total_bytes=5), dict(reads=2)):
            _, receiver = self.receiver(**options)
            with self.assertRaises(ValueError): receiver.receive()
        transport, receiver = self.receiver(FRAME * 2, messages=1)
        self.assertEqual(receiver.receive(), FRAME)
        calls = transport.calls
        with self.assertRaises(ValueError): receiver.receive()
        self.assertEqual(transport.calls, calls)
    def test_truncated_transport_and_reentrancy(self):
        _, receiver = self.receiver(FRAME[:-1])
        with self.assertRaises(ValueError): receiver.receive()
        transport, receiver = self.receiver()
        def observe():
            with self.assertRaises(ValueError): receiver.receive()
        transport.observe = observe
        self.assertEqual(receiver.receive(), FRAME)
    def test_independent_cleanup_lane(self):
        _, ordinary = self.receiver(messages=1)
        _, cleanup = self.receiver(messages=1)
        ordinary.receive()
        with self.assertRaises(ValueError): ordinary.receive()
        self.assertEqual(cleanup.receive(), FRAME)
