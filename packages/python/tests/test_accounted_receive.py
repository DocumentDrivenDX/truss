"""Independent payload arithmetic and ingress faults; no native qualification."""
import unittest
from truss._accounted_receive import AccountedReceiver
from truss._resource_account import BytePermitAccount


FRAME = b'Z\x00\x00\x00\x05T'


class Transport:
    def __init__(self, data, observe=lambda: None):
        self.data = data
        self.observe = observe
        self.calls = 0

    def recv_into(self, view):
        self.calls += 1
        self.observe()
        count = min(len(view), len(self.data), 2)
        view[:count] = self.data[:count]
        self.data = self.data[count:]
        return count


class AccountedReceiveTests(unittest.TestCase):
    def setup_receiver(self, data=FRAME, capacity=69, cumulative=100, reads=10):
        producer = object()
        account = BytePermitAccount(producer, capacity, cumulative, 30)
        observed = []
        transport = Transport(data, lambda: observed.append(account.snapshot(producer)))
        receiver = AccountedReceiver(transport, account, producer,
            frame_bytes=32, total_bytes=100, messages=3, reads=reads)
        return producer, account, transport, receiver, observed

    def test_reservation_precedes_ingress_and_payload_copies_stay_charged(self):
        producer, account, transport, receiver, observed = self.setup_receiver()
        self.assertEqual(receiver.receive(), FRAME)
        # 69 reserved before read; header5 then frame6 then immutable frame6.
        self.assertEqual(observed, [(5,64,5,False)] * 3 + [(11,58,11,False)])
        self.assertEqual(account.snapshot(producer), (17,0,17,False))
        self.assertEqual(transport.calls, 4)

    def test_shared_capacity_denial_reads_nothing_and_retains_prior_custody(self):
        producer, account, transport, receiver, _ = self.setup_receiver(data=FRAME*2)
        self.assertEqual(receiver.receive(), FRAME)
        second = AccountedReceiver(transport, account, producer,
            frame_bytes=32, total_bytes=100, messages=3, reads=10)
        with self.assertRaises(ValueError): second.receive()
        self.assertEqual(transport.calls, 4)
        self.assertEqual(account.snapshot(producer), (17,0,17,True))
        with self.assertRaises(ValueError): receiver.receive()
        self.assertEqual(transport.calls, 4)

    def test_pre_read_cumulative_refusal_is_irreversible(self):
        producer, account, transport, receiver, _ = self.setup_receiver(cumulative=68)
        for _ in range(2):
            with self.assertRaises(ValueError): receiver.receive()
        self.assertEqual(transport.calls, 0)
        self.assertEqual(account.snapshot(producer), (0,0,0,True))

    def test_failed_partial_ingress_retains_reservation_and_allocations(self):
        for data, reads, expected, calls in [
            (FRAME[:3],10,(5,64,5,True),3),
            (FRAME[:5],10,(11,58,11,True),4),
            (FRAME,1,(5,64,5,True),1),
            (b'Z\x00\x00\x00\x03',10,(5,64,5,True),3),
        ]:
            with self.subTest(data=data, reads=reads):
                producer, account, transport, receiver, _ = self.setup_receiver(data=data,reads=reads)
                with self.assertRaises(ValueError): receiver.receive()
                self.assertEqual(account.snapshot(producer), expected)
                with self.assertRaises(ValueError): receiver.receive()
                self.assertEqual(transport.calls, calls)

    def test_foreign_producer_and_reentry_cannot_start_another_read(self):
        producer, account, transport, receiver, _ = self.setup_receiver()
        with self.assertRaises(ValueError):
            AccountedReceiver(transport,account,object(),frame_bytes=32,total_bytes=100,messages=1,reads=10)
        def observe():
            with self.assertRaises(ValueError): receiver.receive()
        transport.observe = observe
        self.assertEqual(receiver.receive(), FRAME)
        self.assertEqual(transport.calls, 4)
        self.assertEqual(account.snapshot(producer), (17,0,17,False))
