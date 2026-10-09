import unittest
from pg8000_instance_candidate import FrameFile

class Transport:
    def __init__(self, data):
        self.data = data
        self.reads = []
        self.writes = []
    def recv_into(self, target):
        self.reads.append(len(target))
        n = min(1, len(target), len(self.data))
        target[:n] = self.data[:n]
        self.data = self.data[n:]
        return n
    def sendall(self, data):
        self.writes.append(bytes(data))

class DriverFileTests(unittest.TestCase):
    def test_fragmented_original_header_body_and_zero_body(self):
        f = FrameFile(Transport(bytes.fromhex('5a00000005494900000004')))
        self.assertEqual(f.read(5), bytes.fromhex('5a00000005'))
        self.assertEqual(f.read(1), b'I')
        self.assertEqual(f.read(5), bytes.fromhex('4900000004'))
        self.assertEqual(f.read(0), b'')
        self.assertFalse(f.closed)
    def test_invalid_header_or_partial_body_closes_without_reuse(self):
        for data in [bytes.fromhex('44ffffffff'), bytes.fromhex('440000000700')]:
            t = Transport(data)
            f = FrameFile(t)
            with self.assertRaises(ValueError): f.read(5)
            before = list(t.reads)
            self.assertTrue(f.closed)
            with self.assertRaises(ValueError): f.read(5)
            self.assertEqual(t.reads, before)
    def test_full_report_header_refuses_before_any_body_read(self):
        # Four-MiB single-cell DataRow: original signed length 4,194,314.
        # A valid header is enough to prove the one-MiB driver seam mismatch.
        t = Transport(bytes.fromhex('440040000a') + b'untouched-body')
        f = FrameFile(t)
        with self.assertRaises(ValueError): f.read(5)
        self.assertTrue(f.closed)
        self.assertEqual(t.data, b'untouched-body')
        self.assertEqual(t.reads, [5,4,3,2,1])

    def test_body_request_mismatch_is_terminal_and_sibling_is_independent(self):
        f = FrameFile(Transport(bytes.fromhex('5a0000000549')))
        f.read(5)
        with self.assertRaises(ValueError): f.read(2)
        self.assertTrue(f.closed)
        sibling = FrameFile(Transport(bytes.fromhex('5a0000000549')))
        self.assertEqual(sibling.read(5), bytes.fromhex('5a00000005'))
        self.assertEqual(sibling.read(1), b'I')
    def test_send_budget_and_unknown_send_failure_prevent_further_writes(self):
        t = Transport(b'')
        f = FrameFile(t)
        f.remaining_send_bytes = 1
        with self.assertRaises(ValueError): f.write(b'ab')
        with self.assertRaises(ValueError): f.write(b'a')
        self.assertEqual(t.writes, [])
        class Interrupted(Transport):
            def sendall(self, data): raise OSError('Interrupted send')
        f = FrameFile(Interrupted(b''))
        with self.assertRaises(OSError): f.write(b'a')
        self.assertTrue(f.closed)
        self.assertEqual(f.remaining_send_bytes, 2097151)

if __name__ == '__main__': unittest.main()
