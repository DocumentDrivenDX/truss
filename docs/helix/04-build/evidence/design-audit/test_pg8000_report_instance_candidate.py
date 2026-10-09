import unittest
from pg8000_report_instance_candidate import ReportFrameFile

class BulkTransport:
    def __init__(self, data): self.data, self.requests = data, []
    def recv_into(self, target):
        self.requests.append(len(target))
        n = min(len(target),len(self.data))
        target[:n] = self.data[:n]
        self.data = self.data[n:]
        return n

class ReportFileTests(unittest.TestCase):
    def test_exact_capacity_frame_is_retained(self):
        body = bytes.fromhex('000100400000') + b'a' * 4194304
        t = BulkTransport(bytes.fromhex('440040000a') + body)
        f = ReportFrameFile(t)
        self.assertEqual(f.read(5),bytes.fromhex('440040000a'))
        self.assertEqual(f.read(len(body)),body)
        self.assertEqual(t.requests,[5,4194310])
    def test_one_over_refuses_without_body_ingress(self):
        t = BulkTransport(bytes.fromhex('440040000b') + b'untouched')
        f = ReportFrameFile(t)
        with self.assertRaises(ValueError): f.read(5)
        self.assertTrue(f.closed)
        self.assertEqual(t.requests,[5])
        self.assertEqual(t.data,b'untouched')

if __name__ == '__main__': unittest.main()
