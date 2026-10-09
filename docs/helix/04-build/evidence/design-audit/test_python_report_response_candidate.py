import unittest
from check_report_response_boundary import build, CONTRACTS, check
from python_report_response_candidate import ReportResponseCandidate
from python_report_wire_candidate import ReportWireCandidate


class ResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.response = ReportResponseCandidate(CONTRACTS)
        cls.legacy = ReportWireCandidate(CONTRACTS)

    def test_complete_frame_to_original_response_schema(self):
        import struct
        from python_report_frame_candidate import report_cell
        _, source = build(4194304)
        frame = b'D' + struct.pack('!iHi', len(source) + 10, 1, len(source)) + source
        cell = report_cell(frame)
        result = self.response.prepare(cell)
        self.assertEqual(result.original.source_bytes, source)
        self.assertEqual(len(result.original.value.entries), 19)
        with self.assertRaises(ValueError):
            self.response.prepare_native(cell)

    def test_frozen_complete_boundary_and_one_over(self):
        check()  # Independent original fixture/schema/hash verification.
        report, source = build(4194304)
        result = self.response.prepare(source)
        self.assertEqual(result.original.source_bytes, source)
        self.assertEqual(len(result.original.value.entries), 19)
        self.assertEqual(result.scope, 'response_schema_bytes_only_without_account_admission')
        with self.assertRaises(ValueError):
            self.response.prepare(build(4194305)[1])
        with self.assertRaises(ValueError):
            self.legacy.prepare(source)
        with self.assertRaisesRegex(ValueError, 'profile remains unadmitted'):
            self.response.prepare_native(source)

    def test_schema_and_numeric_refusal_remain_distinct_from_capacity(self):
        for source, message in [(b'{}', 'schema refused'),
                                (b'{"rev":9007199254740993}', 'numeric node')]:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, message):
                self.response.prepare(source)
        for source in [b'{"rev":"1","rev":"2"}', b'{"x":"\\ud800"}']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.response.prepare(source)

    def test_malformed_response_errors_are_instance_free(self):
        marker = b'private-original-instance-'
        for source, reason in [(b'{"x":"' + marker + b'a'*100000 + b'"', 'grammar'),
                               (b'{"x":"' + marker + b'\xff"}', 'unicode')]:
            with self.subTest(source_length=len(source)), self.assertRaises(ValueError) as rejected:
                self.response.prepare(source)
            error = rejected.exception
            self.assertEqual(error.reason, reason)
            self.assertNotIn(marker.decode(), str(error))
            self.assertFalse(hasattr(error, 'doc'))
            self.assertFalse(hasattr(error, 'object'))
            self.assertIsNone(error.__cause__)
            self.assertIsNone(error.__context__)

    def test_retained_response_cannot_change_with_caller_buffer(self):
        source = bytearray(build(4194304)[1])
        result = self.response.prepare(source)
        before = result.original.source_bytes
        source[:] = b'changed'
        self.assertEqual(result.original.source_bytes, before)
        self.assertNotEqual(result.original.source_bytes, bytes(source))


if __name__ == '__main__':
    unittest.main()
