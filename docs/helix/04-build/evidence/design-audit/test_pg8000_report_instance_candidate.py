import unittest
from pg8000_report_instance_candidate import ReportFrameFile, ReportConnection

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
    def test_complete_report_row_does_not_admit_after_late_failure(self):
        from types import SimpleNamespace
        from pg8000.exceptions import DatabaseError
        from check_report_response_boundary import build
        _, source = build(4194304)
        # Independently specified text/OID25/format0 descriptor and error.
        descriptor = bytes.fromhex('0001') + b'carrier\0' + bytes.fromhex(
            '00000000000000000019ffff000000000000')
        def frame(kind, body):
            return kind + (len(body) + 4).to_bytes(4, 'big') + body
        row = bytes.fromhex('000100400000') + source
        error = b'SERROR\0VERROR\0CXX000\0Mcontrolled late error\0\0'
        for tail, exception, status in [
            (frame(b'E', error) + bytes.fromhex('5a0000000549'), DatabaseError, b'I'),
            (b'', ValueError, b'T'),
        ]:
            transport = BulkTransport(frame(b'T', descriptor) + frame(b'D', row) + tail)
            file = ReportFrameFile(transport)
            connection = ReportConnection.__new__(ReportConnection)
            connection._sock = file
            connection._transaction_status = b'T'
            connection._client_encoding = 'utf8'
            connection.message_types = {
                b'T': connection.handle_ROW_DESCRIPTION,
                b'D': connection.handle_DATA_ROW,
                b'E': connection.handle_ERROR_RESPONSE,
                b'Z': connection.handle_READY_FOR_QUERY,
            }
            context = SimpleNamespace(columns=None, rows=None, error=None)
            admitted = []
            with self.assertRaises(exception):
                connection.handle_messages(context)
                admitted.append(context.rows[0][0])
            self.assertEqual(admitted, [])
            self.assertEqual(context.rows, [(source,)])  # Provisional only.
            self.assertEqual(connection._transaction_status, status)
            self.assertTrue(file.closed)
            reads = list(transport.requests)
            with self.assertRaises(ValueError): file.read(5)
            with self.assertRaises(ValueError): file.write(b'Q')
            self.assertEqual(transport.requests, reads)

    def test_one_over_refuses_without_body_ingress(self):
        t = BulkTransport(bytes.fromhex('440040000b') + b'untouched')
        f = ReportFrameFile(t)
        with self.assertRaises(ValueError): f.read(5)
        self.assertTrue(f.closed)
        self.assertEqual(t.requests,[5])
        self.assertEqual(t.data,b'untouched')

if __name__ == '__main__': unittest.main()
