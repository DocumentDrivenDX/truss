# SPDX-License-Identifier: MIT OR Apache-2.0
"""Canonical report bytes and current UMF 0.10 registration-summary projection."""
import copy
import json
import unittest
from hashlib import sha256
from pathlib import Path
from test_catalog_support import selected
from truss._catalog_support import DATE10_PROFILE, evaluate_catalog_support
from truss._catalog_report_semantics import (
    canonical_numeric_free, compose_catalog_report_semantics,
    compose_original_catalog_report_semantics,
)

ROOT=Path(__file__).resolve().parents[3]


class CatalogReportSemanticsTests(unittest.TestCase):
    def test_independent_canonical_bytes_and_domain_vectors(self):
        vectors=json.loads((ROOT/'docs/helix/02-design/contracts/bindings/canonical-byte-v0.1.vectors.json').read_text())['vectors']
        for vector in vectors:
            raw=bytes.fromhex(vector['canonicalUtf8Hex'])
            with self.subTest(name=vector['name']):
                self.assertEqual(canonical_numeric_free(json.loads(raw)),raw)
                self.assertEqual(sha256(b'truss-canonical/0.1.0\n'+vector['domain'].encode()+b'\n'+raw).hexdigest(),vector['sha256'])
        self.assertEqual(canonical_numeric_free({'\U00010000':'é','\ue000':'\n\t'}),b'{"\xee\x80\x80":"\\u000a\\u0009","\xf0\x90\x80\x80":"\xc3\xa9"}')
        self.assertNotEqual(canonical_numeric_free('é'),canonical_numeric_free('e\u0301'))

    def test_canonical_refuses_numbers_surrogates_and_capacity(self):
        for value in (1,1.0,'\ud800',{'\ud800':None},[None]*4097):
            with self.subTest(kind=type(value)),self.assertRaises(ValueError):canonical_numeric_free(value)

    def test_current_registration_summary_projection_has_no_claimed_execution(self):
        prepared=selected();support=evaluate_catalog_support(prepared)
        result=compose_original_catalog_report_semantics(prepared,support)
        self.assertEqual(result['state'],'source_fields_ready')
        self.assertEqual(result['sourceFormat'],'truss-registration-summary/2.0')
        self.assertEqual(result['documentValidations'],support['registrationSummary']['documents'])
        self.assertNotIn('assertionEntries',result)
        self.assertNotIn('catalogRevision',result)
        with_revision=compose_catalog_report_semantics(prepared,support,'1')
        self.assertEqual(with_revision['catalogRevision'],'1')
        for revision in ('0','01','-1','2147483648'):
            with self.subTest(revision=revision),self.assertRaises(ValueError):
                compose_catalog_report_semantics(prepared,support,revision)

    def test_profile_substitution_is_unavailable_without_replaying_owner_evidence(self):
        prepared=selected()
        altered=copy.deepcopy(prepared.input())
        altered['supportProfile']=dict(DATE10_PROFILE,sha256='0'*64)
        self.assertNotEqual(altered['supportProfile'],prepared.input()['supportProfile'])
        with self.assertRaises(ValueError):
            compose_original_catalog_report_semantics(prepared,{'state':'evaluated','profile':altered['supportProfile']})

if __name__=='__main__':unittest.main()
