# SPDX-License-Identifier: MIT OR Apache-2.0
"""Trusted SDK dispatch input; no native facade or accepted-result claim."""
import dataclasses
import json
import unittest
from unittest.mock import patch
from test_catalog_support import selected
from truss._catalog_candidate import encode_fresh_catalog_dispatch_parameters as encode
from truss._catalog_candidate import FRESH_CATALOG_DISPATCH_SQL

class FreshCatalogDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared = selected()

    def test_original_byte_tuple_and_closed_source_inventory(self):
        p = self.prepared
        origin = b' {"x-action":"consumer.register","note":"caf\\u00e9"} \n'
        parameters = encode(p,'9007199254740993',origin)
        self.assertEqual(len(parameters),6)
        self.assertEqual(parameters[0],'9007199254740993')
        for actual, original in zip(parameters[3:],
                (p.archive_documents_bytes,p.declarations_bytes,origin),strict=True):
            self.assertIs(actual,original)
        self.assertIs(parameters[1],p.input_bytes)
        candidate = json.loads(parameters[2])
        self.assertEqual(bytes.fromhex(candidate['declarationsUtf8Hex']),p.declarations_bytes)
        self.assertEqual(bytes.fromhex(candidate['reportEvidenceUtf8Hex']),p.report_evidence_bytes)
        sources = {bytes.fromhex(m['keyUtf8Hex']).decode() for m in candidate['hostSources']['members']}
        self.assertEqual(sources,{'umf','diagnostics','documentInterpretations','losses',
            'extensions','transformRegistrations','assertionEntries'})
        self.assertEqual(FRESH_CATALOG_DISPATCH_SQL.count('%s'),6)
        self.assertNotIn(origin.decode(),FRESH_CATALOG_DISPATCH_SQL)

    def test_exact_int8_ordinal_domain(self):
        for ordinal in ('0','9223372036854775807'):
            self.assertEqual(encode(self.prepared,ordinal,b'{}')[0],ordinal)
        for ordinal in (True,0,0.0,'','-1','+1','01','1.0',' 1','١','9223372036854775808'):
            with self.subTest(ordinal=ordinal),self.assertRaises(ValueError):
                encode(self.prepared,ordinal,b'{}')

    def test_origin_grammar_duplicates_and_bounds(self):
        for raw in (bytearray(b'{}'),b'',b'[]',b'null',b'{"a":true,"a":false}',
                    b'{"a":1}',b'{"a":"\xff"}',b' ' * 131073):
            with self.subTest(raw=repr(raw)[:80]),self.assertRaises(ValueError):
                encode(self.prepared,'0',raw)

    def test_copied_or_changed_preparation_refuses(self):
        p = self.prepared
        for field in ('input_bytes','archive_documents_bytes','declarations_bytes','report_evidence_bytes'):
            with self.subTest(field=field),self.assertRaises(ValueError):
                encode(dataclasses.replace(p,**{field:b'{}'}),'0',b'{}')
        with self.assertRaises(ValueError): encode(dataclasses.replace(p),'0',b'{}')

    def test_source_omission_refuses_before_dispatch(self):
        with patch('truss._catalog_candidate.compose_original_catalog_report_semantics',
                   return_value={'state':'unavailable'}):
            with self.assertRaises(ValueError): encode(self.prepared,'0',b'{}')

    def test_mutation_during_producer_is_detected(self):
        p = selected()
        from truss._catalog_candidate import encode_original_catalog_candidate
        def mutate(prepared):
            result = encode_original_catalog_candidate(prepared)
            object.__setattr__(prepared,'input_bytes',b'{}')
            return result
        with patch('truss._catalog_candidate.encode_original_catalog_candidate',side_effect=mutate):
            with self.assertRaises(ValueError): encode(p,'0',b'{}')

if __name__ == '__main__': unittest.main(verbosity=2)
