import base64
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import unittest
from truss._receipt_position import decode_receipt_position

ROOT = Path(__file__).resolve().parents[3]


def token(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


class ReceiptPositionTests(unittest.TestCase):
    def test_original_wire_vectors(self):
        vectors = json.loads((ROOT / 'docs/helix/04-build/evidence/receipt-position-locator-vectors.json').read_text())['vectors']
        for vector in vectors:
            with self.subTest(vector=vector['id']):
                result = decode_receipt_position(vector['token'])
                self.assertEqual(result.original_bytes.hex(), vector['utf8Hex'])
                self.assertEqual(result.writer_xid, vector['locator']['writerXid'])
                self.assertEqual(result.receipt_storage_row_id, vector['locator']['receiptStorageRowId'])
                self.assertEqual(result.position_profile.identity, vector['locator']['positionProfile']['identity'])
                with self.assertRaises(FrozenInstanceError):
                    result.writer_xid = '0'

    def test_canonicality_bounds_domains_and_closed_members(self):
        vector = json.loads((ROOT / 'docs/helix/04-build/evidence/receipt-position-locator-vectors.json').read_text())['vectors'][0]
        raw = bytes.fromhex(vector['utf8Hex'])
        invalid = [token(json.dumps(vector['locator'], ensure_ascii=False).encode()), token(raw.replace(b'"epoch"', b'"\\u0065poch"')), vector['token']+'=', 'A', 'a'*16385, token(b' '+raw), token(raw.replace(b'123', b'0123')), token(raw.replace(b'"123"', b'123')), token(raw.replace(b'"1"', b'"0"')), token(raw.replace(b'"123"', b'"18446744073709551616"')), token(raw.replace(b'"1"', b'"9223372036854775808"')), token(raw.replace(b'"installation"', b'"'+b'x'*1025+b'"')), token(raw.replace(b'"epoch"', b'"'+('é'*129).encode()+b'"')), token(raw.replace(b'"epoch"', b'"\\u0000"')), token(raw.replace(b'"epoch"', b'"\\ud800"')), token(raw[:-1]+b',"extra":true}'), token(raw[:-1]+b',"writerXid":"123"}')]
        for value in invalid:
            with self.subTest(token_length=len(value)):
                with self.assertRaises(ValueError):
                    decode_receipt_position(value)


if __name__ == '__main__':
    unittest.main()
