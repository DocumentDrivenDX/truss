import unittest
import hashlib
import json
from pathlib import Path
from python_pg_frame_candidate import row_description, data_row
from python_pg_receive_candidate import Receiver


class Transport:
    def __init__(self, source, fragment=None):
        self.source = source
        self.fragment = fragment
        self.requests = []

    def recv_into(self, target):
        self.requests.append(len(target))
        size = min(len(target), len(self.source), self.fragment or len(target))
        target[:size] = self.source[:size]
        self.source = self.source[size:]
        return size


def receiver(transport, **changes):
    limits = dict(frame_bytes=8, total_bytes=16, messages=2, reads=20)
    limits.update(changes)
    return Receiver(transport, **limits)


class ReceiveTests(unittest.TestCase):
    def test_saved_native_receive_source_and_exact_cells(self):
        here = Path(__file__).resolve().parent
        receipt = json.loads((here / 'python-pg-receive-native.json').read_bytes())
        self.assertEqual(receipt['status'], 'passed_read_only_native_receive_candidate')
        for name in ['python_pg_receive_candidate.py', 'python_pg_frame_candidate.py',
                     'check_python_pg_receive_native.py']:
            self.assertEqual(hashlib.sha256((here / name).read_bytes()).hexdigest(),
                             receipt['sourceSha256'][name])
        frames = [bytes.fromhex(value) for value in receipt['framesHex']]
        self.assertEqual([value[:1] for value in frames],
                         [b'Z', b'C', b'T', b'D', b'C', b'C', b'Z'])
        self.assertEqual([(c.name, c.type_oid, c.format)
                          for c in row_description(frames[2])],
                         [(b'n', 25, 0), (b'empty', 25, 0), (b'exact', 1700, 0),
                          (b'unicode', 25, 0), (b'server', 25, 0)])
        self.assertEqual(data_row(frames[3], 5),
                         (None, b'', b'9007199254740993.0000000000000000001',
                          'é𐀀'.encode('utf8'), b'170009'))
        self.assertEqual([value[5:] for value in frames if value[:1] == b'C'],
                         [b'BEGIN\0', b'SELECT 1\0', b'ROLLBACK\0'])

    def test_complete_literal_frames_and_fragmented_reads(self):
        # Independent protocol literals, no candidate encoder.
        first = bytes.fromhex('4400000007000000')
        second = bytes.fromhex('5a0000000549')
        transport = Transport(first + second, 1)
        candidate = receiver(transport)
        self.assertEqual(candidate.receive(), first)
        self.assertEqual(candidate.receive(), second)
        self.assertEqual(len(transport.requests), 14)
        self.assertEqual(candidate.remaining_bytes, 2)
        self.assertFalse(candidate.failed)

    def test_message_exhaustion_has_zero_next_header_reads(self):
        transport = Transport(bytes.fromhex('5a00000005495a0000000549'))
        candidate = receiver(transport, messages=1)
        self.assertEqual(candidate.receive(), bytes.fromhex('5a0000000549'))
        before = list(transport.requests)
        with self.assertRaisesRegex(ValueError, 'Message'):
            candidate.receive()
        self.assertEqual(transport.requests, before)
        self.assertEqual(transport.source, bytes.fromhex('5a0000000549'))

    def test_invalid_or_unaffordable_headers_have_zero_body_reads(self):
        for header, limits in [
            ('4400000008', {}),  # Otherwise valid nine-byte frame exceeds eight.
            ('44ffffffff', {}),
            ('4400000003', {}),
            ('4400000007', {'total_bytes': 7}),
        ]:
            with self.subTest(header=header, limits=limits):
                transport = Transport(bytes.fromhex(header) + b'abc')
                candidate = receiver(transport, **limits)
                with self.assertRaises(ValueError):
                    candidate.receive()
                self.assertEqual(transport.requests, [5])
                self.assertEqual(transport.source, b'abc')
                self.assertTrue(candidate.failed)

    def test_fragment_work_limit_precedes_next_read_and_failure_is_terminal(self):
        transport = Transport(bytes.fromhex('4400000007000000'), 1)
        candidate = receiver(transport, reads=5)
        with self.assertRaisesRegex(ValueError, 'Read work'):
            candidate.receive()
        self.assertEqual(len(transport.requests), 5)
        self.assertEqual(transport.source, b'\0\0\0')
        with self.assertRaisesRegex(ValueError, 'cannot be reused'):
            candidate.receive()
        self.assertEqual(len(transport.requests), 5)

    def test_partial_eof_and_transport_failure_do_not_refund_or_affect_sibling(self):
        sibling = receiver(Transport(bytes.fromhex('5a0000000549')))
        for source in [b'D\0', bytes.fromhex('4400000007') + b'a']:
            candidate = receiver(Transport(source))
            with self.assertRaises(ValueError):
                candidate.receive()
            self.assertTrue(candidate.failed)
            self.assertEqual(candidate.remaining_messages, 1)
        class Interrupted:
            def recv_into(self, target):
                raise KeyboardInterrupt()
        candidate = receiver(Interrupted())
        with self.assertRaises(KeyboardInterrupt):
            candidate.receive()
        self.assertTrue(candidate.failed)
        self.assertEqual(sibling.receive(), bytes.fromhex('5a0000000549'))

    def test_closed_limit_and_transport_count_admission(self):
        for name in ['frame_bytes', 'total_bytes', 'messages', 'reads']:
            for value in [True, 0, -1, 1.0]:
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    receiver(Transport(b''), **{name: value})
        for value in [True, 0, -1, 6, None]:
            class WrongCount:
                def recv_into(self, target):
                    return value
            candidate = receiver(WrongCount())
            with self.subTest(value=value), self.assertRaises(ValueError):
                candidate.receive()
            self.assertTrue(candidate.failed)


if __name__ == '__main__':
    unittest.main()
