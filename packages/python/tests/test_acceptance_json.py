"""Shared original wire vectors plus independent boundary expectations."""
import hashlib
import json
from pathlib import Path
import unittest
from truss._acceptance_json import AcceptanceJsonError, decode_acceptance_json

ROOT = Path(__file__).resolve().parents[3]


class AcceptanceJsonTests(unittest.TestCase):
    def test_original_shared_vectors(self):
        corpus = json.loads((ROOT / 'docs/helix/03-test/acceptance-outer-json-expected.proposal.json').read_text())
        for case in corpus['cases']:
            with self.subTest(case=case['name']):
                original = bytes.fromhex(case['utf8Hex'])
                self.assertEqual(hashlib.sha256(original).hexdigest(), case['sourceSha256'])
                expected = case['expected']
                if expected['status'] == 'decoded':
                    self.assertEqual(decode_acceptance_json(original), expected['value'])
                else:
                    with self.assertRaises(AcceptanceJsonError) as raised:
                        decode_acceptance_json(original)
                    self.assertEqual(raised.exception.reason, expected['reason'])

    def refuse_resource(self, original):
        with self.assertRaises(AcceptanceJsonError) as raised:
            decode_acceptance_json(original)
        self.assertEqual(raised.exception.reason, 'resource')

    def test_depth_members_bytes_work_and_node_limits(self):
        decode_acceptance_json(b'[' * 129 + b']' * 129)
        self.refuse_resource(b'[' * 130 + b']' * 130)
        self.assertEqual(len(decode_acceptance_json(b'[' + b','.join([b'null'] * 4096) + b']')), 4096)
        self.refuse_resource(b'[' + b','.join([b'null'] * 4097) + b']')
        self.refuse_resource(bytes(1048577))
        keys = [json.dumps('key-' + str(i).zfill(5)) + ':null' for i in range(1000)]
        self.refuse_resource(('{' + ','.join(keys) + '}').encode())
        def nodes(last):
            return ('[' + ','.join('[' + ','.join(['null'] * (last if i == 24 else 3999)) + ']' for i in range(25)) + ']').encode()
        self.assertEqual(len(decode_acceptance_json(nodes(3998))), 25)
        self.refuse_resource(nodes(3999))

    def test_shared_capacity_input(self):
        fixture = json.loads((ROOT / 'docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').read_text())
        original = json.dumps(fixture['input'], ensure_ascii=False, separators=(',', ':')).encode()
        self.assertEqual(len(original), fixture['expected']['canonicalTreeBytes'])
        self.assertEqual(decode_acceptance_json(original), fixture['input'])


if __name__ == '__main__':
    unittest.main()
