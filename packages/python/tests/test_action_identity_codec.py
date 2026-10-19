# SPDX-License-Identifier: MIT OR Apache-2.0
"""Independent original Bun reference oracle, including native UTF-16 cases."""
import json
from pathlib import Path
import unittest
from truss._action_identity_codec import (encode_action_family, encode_action_role,
    encode_action_store_identity, encode_action_tenant_identity, encode_action_namespace_epoch)


class ActionIdentityCodecTests(unittest.TestCase):
    def test_original_reference_oracle(self):
        rows = json.loads(Path(__file__).with_name('fixtures').joinpath('action-family-codec.json').read_text())
        self.assertEqual(len(rows), 8)
        for row in rows:
            with self.subTest(module=repr(row['module']), action=repr(row['action'])):
                self.assertEqual(encode_action_family(row['module'], row['action']).hex(), row['familyHex'])
                self.assertEqual(encode_action_role(row['action']).hex(), row['roleHex'])
                for encoder in (encode_action_store_identity,encode_action_tenant_identity,encode_action_namespace_epoch):
                    self.assertEqual(encoder(row['action']).hex(), row['roleHex'])

    def test_original_utf16_bounds_and_exact_identity(self):
        for invalid in ('', 'a'*257, '\U0001f680'*129, None, 1, b'sales'):
            with self.subTest(value=repr(invalid)):
                with self.assertRaises(ValueError):
                    encode_action_family(invalid, 'set-name')
                with self.assertRaises(ValueError):
                    encode_action_role(invalid)
        self.assertNotEqual(encode_action_family('sales','set-name'), encode_action_family('Sales','set-name'))
        self.assertNotEqual(encode_action_role('é'), encode_action_role('e\u0301'))
        self.assertEqual(encode_action_role('\ud83d\ude80'), encode_action_role('\U0001f680'))
