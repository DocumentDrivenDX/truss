import struct
import unittest
import hashlib
import json
from pathlib import Path
from python_pg_frame_candidate import row_description, data_row, MAX_FRAME


def frame(kind, body):
    return kind + struct.pack('!i', len(body) + 4) + body


class FrameTests(unittest.TestCase):
    def test_saved_native_frames_and_original_source_correspondence(self):
        here = Path(__file__).resolve().parent
        receipt = json.loads((here / 'python-pg-frame-native.json').read_bytes())
        self.assertEqual(receipt['status'], 'passed_read_only_native_frame_candidate')
        for name in ['python_pg_frame_candidate.py', 'check_python_pg_frame_native.py']:
            self.assertEqual(hashlib.sha256((here / name).read_bytes()).hexdigest(),
                             receipt['sourceSha256'][name])
        frames = [bytes.fromhex(value) for value in receipt['framesHex']]
        self.assertEqual([value[:1] for value in frames],
                         [b'Z', b'C', b'T', b'D', b'C', b'C', b'Z'])
        columns = row_description(frames[2])
        self.assertEqual([(c.name, c.type_oid, c.format) for c in columns],
                         [(b'n', 25, 0), (b'empty', 25, 0), (b'exact', 1700, 0),
                          (b'unicode', 25, 0), (b'server', 25, 0)])
        self.assertEqual(data_row(frames[3], 5),
                         (None, b'', b'9007199254740993.0000000000000000001',
                          'é𐀀'.encode('utf8'), b'170009'))
        self.assertEqual([value[5:] for value in frames if value[:1] == b'C'],
                         [b'BEGIN\0', b'SELECT 1\0', b'ROLLBACK\0'])
        self.assertEqual([value for value in frames if value[:1] == b'Z'],
                         [b'Z\0\0\0\5I'] * 2)

    def test_ordered_metadata_signed_fields_and_unsigned_oids(self):
        # Independent literal network-order witnesses: name, table, attribute,
        # type, size, modifier, format. No encoder from the candidate is used.
        source = bytes.fromhex(
            '540000002e0002610000000000000000000019ffffffffffff0000'
            '6200ffffffff0002ffffffff0008ffffffff0001')
        columns = row_description(source)
        self.assertEqual([(c.name, c.table_oid, c.attribute, c.type_oid,
                           c.type_size, c.modifier, c.format) for c in columns],
                         [(b'a', 0, 0, 25, -1, -1, 0),
                          (b'b', 4294967295, 2, 4294967295, 8, -1, 1)])
        # Pinned pg8000 1.31.5 core.py selects the signed "ihihih" format.
        # Its metadata representation cannot substitute for original raw OIDs.
        self.assertEqual(struct.unpack('!ihihih', source[-18:]),
                         (-1, 2, -1, 8, -1, 1))

    def test_null_empty_and_exact_undecoded_cells(self):
        source = bytes.fromhex('44000000140003ffffffff0000000000000002ff00')
        self.assertEqual(data_row(source, 3), (None, b'', b'\xff\0'))
        text = b'9007199254740993.0000000000000000001'
        self.assertEqual(data_row(frame(b'D', b'\0\1' + struct.pack('!i', len(text)) + text), 1), (text,))

    def test_complete_frame_and_field_refusals(self):
        good = frame(b'D', b'\0\1\0\0\0\0')
        for source in [good[:-1], good + b'X', b'T' + good[1:],
                       frame(b'D', b'\0\1\xff\xff\xff\xfe'),
                       frame(b'D', b'\0\1\0\0\0\x02X'),
                       frame(b'D', b'\0\1\0\0\0\0X')]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                data_row(source, 1)
        with self.assertRaises(ValueError):
            data_row(good, 2)
        with self.assertRaises(ValueError):
            data_row(good, True)

    def test_description_refusals_and_duplicate_names_preserved(self):
        metadata = struct.pack('!IhIhih', 0, 0, 25, -1, -1, 0)
        self.assertEqual([c.name for c in row_description(frame(b'T', b'\0\2' + (b'x\0' + metadata) * 2))], [b'x', b'x'])
        for body in [b'\0\1name', b'\0\1\xff\0' + metadata,
                     b'\0\1x\0' + metadata[:-1] + b'\2',
                     b'\0\0X', b'\x10\x01']:
            with self.subTest(body=body), self.assertRaises(ValueError):
                row_description(frame(b'T', body))

    def test_capacity_immutable_input_and_zero_columns(self):
        self.assertEqual(data_row(frame(b'D', b'\0\0'), 0), ())
        self.assertEqual(row_description(frame(b'T', b'\0\0')), ())
        with self.assertRaises(ValueError):
            data_row(bytearray(frame(b'D', b'\0\0')), 0)
        with self.assertRaises(ValueError):
            data_row(b'D' * (MAX_FRAME + 1), 0)

    def test_complete_valid_frame_exact_and_one_over_capacity(self):
        self.assertEqual(MAX_FRAME, 1048576)  # Independent candidate fixture limit.
        # Type byte + length + count + cell length occupy eleven bytes.
        payload = b'a' * (1048576 - 11)
        exact = frame(b'D', b'\0\1' + struct.pack('!i', len(payload)) + payload)
        self.assertEqual(len(exact), 1048576)
        self.assertEqual(data_row(exact, 1), (payload,))
        larger = payload + b'a'
        over = frame(b'D', b'\0\1' + struct.pack('!i', len(larger)) + larger)
        self.assertEqual(len(over), 1048577)
        with self.assertRaisesRegex(ValueError, 'capacity'):
            data_row(over, 1)


if __name__ == '__main__':
    unittest.main()
