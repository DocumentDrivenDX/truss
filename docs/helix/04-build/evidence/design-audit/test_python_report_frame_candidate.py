import struct
import unittest
from python_report_frame_candidate import report_cell, MAX_REPORT_FRAME
from python_pg_frame_candidate import data_row


class ReportFrameTests(unittest.TestCase):
    def test_full_capacity_exact_bytes_and_legacy_refusal(self):
        payload = b'a' * 4194304
        source = b'D' + struct.pack('!iHi', 4194314, 1, 4194304) + payload
        self.assertEqual(len(source), MAX_REPORT_FRAME)
        self.assertEqual(report_cell(source), payload)
        with self.assertRaisesRegex(ValueError, 'capacity'):
            data_row(source, 1)
        with self.assertRaisesRegex(ValueError, 'capacity'):
            report_cell(b'D' + struct.pack('!iHi', 4194315, 1, 4194305) + payload + b'a')

    def test_independent_literals_and_complete_frame_refusals(self):
        source = bytes.fromhex('440000000a000100000000')
        self.assertEqual(report_cell(source), b'')
        for bad in [source[:-1], source + b'x', b'T' + source[1:],
                    bytes.fromhex('440000000a0000ffffffff'),
                    bytes.fromhex('440000000a0001ffffffff'),
                    bytes.fromhex('440000000a0001fffffffe'),
                    bytes.fromhex('440000000a000200000000'),
                    bytes.fromhex('44ffffffff000100000000')]:
            with self.subTest(source=bad), self.assertRaises(ValueError):
                report_cell(bad)
        with self.assertRaises(ValueError):
            report_cell(bytearray(source))

    def test_cell_syntax_does_not_claim_json_unicode_or_commit_admission(self):
        payload = b'not JSON\x00\xff'
        source = b'D' + struct.pack('!iHi', len(payload) + 10, 1, len(payload)) + payload
        self.assertEqual(report_cell(source), payload)


if __name__ == '__main__':
    unittest.main()
