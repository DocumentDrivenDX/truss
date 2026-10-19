# SPDX-License-Identifier: MIT OR Apache-2.0
"""Exact numeric-bearing owner evidence; semantic wire remains numeric-free."""
import unittest
from decimal import Decimal, InvalidOperation, localcontext
import json
from truss._owner_evidence_json import decode_owner_evidence_json, same_owner_evidence
from truss._acceptance_json import decode_acceptance_json


class OwnerEvidenceJsonTests(unittest.TestCase):
    def test_exact_numbers_and_distinct_carriers(self):
        raw=b'{"big":9007199254740993,"decimal":0.10000000000000000000001,"tiny":1e-400,"integer":1,"boolean":true}'
        value=decode_owner_evidence_json(raw)
        self.assertEqual(value['big'],9007199254740993)
        self.assertEqual(value['decimal'].as_tuple(),Decimal('0.10000000000000000000001').as_tuple())
        self.assertEqual(value['tiny'].as_tuple(),Decimal('1e-400').as_tuple())
        self.assertFalse(same_owner_evidence(value['integer'],value['boolean']))
        self.assertFalse(same_owner_evidence(1,Decimal('1')))
        self.assertFalse(same_owner_evidence(Decimal('1.0'),Decimal('1.00')))
        self.assertTrue(same_owner_evidence(value,decode_owner_evidence_json(raw)))
        self.assertEqual(raw,b'{"big":9007199254740993,"decimal":0.10000000000000000000001,"tiny":1e-400,"integer":1,"boolean":true}')

    def test_invalid_encoding_duplicates_nonfinite_and_limits_refuse(self):
        cases=(b'{"a":1,"a":2}',b'{"\\u0061":1,"a":2}',b'NaN',b'Infinity',
               b'-Infinity',b'"\\ud800"',b'{"\\udfff":null}',b'"\xff"',
               b'\xef\xbb\xbf{}',b'['*130+b'null'+b']'*130,
               b'['+b','.join([b'null']*4097)+b']',b'1'*513,
               b' '*8_388_609)
        for raw in cases:
            with self.subTest(prefix=raw[:30]), self.assertRaises(ValueError):
                decode_owner_evidence_json(raw)

    def test_extreme_exponent_refuses_independently_of_decimal_traps(self):
        raw=b'1e'+b'9'*100
        for trap in (True,False):
            with localcontext() as context:
                context.traps[InvalidOperation]=trap
                with self.assertRaises(ValueError):decode_owner_evidence_json(raw)

    def test_truss_semantic_wire_still_refuses_numbers(self):
        with self.assertRaises(ValueError):decode_acceptance_json(b'{"min":1}')

    def test_full_and_embedded_evidence_type_substitution_refuses(self):
        full=decode_owner_evidence_json(b'{"result":{"min":1,"value":0.1000000000000000001}}')
        same=decode_owner_evidence_json(b'{"result":{"min":1,"value":0.1000000000000000001}}')
        boolean=decode_owner_evidence_json(b'{"result":{"min":true,"value":0.1000000000000000001}}')
        rounded=decode_owner_evidence_json(b'{"result":{"min":1,"value":0.1}}')
        self.assertTrue(same_owner_evidence(full,same))
        self.assertFalse(same_owner_evidence(full,boolean))
        self.assertFalse(same_owner_evidence(full,rounded))

if __name__=='__main__':unittest.main()
