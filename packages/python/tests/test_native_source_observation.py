# SPDX-License-Identifier: MIT OR Apache-2.0
"""Supplied native row controls; no actual source/caller/authority claim."""
import json,unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from truss._owner_evidence_json import decode_owner_evidence_json
from truss._native_source_observation import (capture_native_source_observation_with_cursor,_exact_assessment,_uint,_signed,_boolean,_bounded,CATALOGS,ASSESSMENT)

class Cursor:
    def __init__(self,raw):self.raw=raw;self.queries=[];self.description=[SimpleNamespace(type_code=25)]
    def execute(self,query,params=(),**kwargs):
        self.queries.append((query,params));self.rows=self.raw if 'prop_def' in query else []
    def fetchmany(self,n):return self.rows[:n]

class NativeSourceObservationTests(unittest.TestCase):
    def request(self):return b'{"modules":[{"pin":{"documentId":"d","revision":"r","umfVersion":"0.10.0","sha256":"x"}}],"unknown":{"escaped":"\\u0061","n":1.2300}}'
    def exact(self,rows):
        cursor=Cursor(rows)
        with patch('truss._native_source_observation.capture_accepted_catalog',return_value=b'{"legacy":"retained"}') as original:
            exact,legacy=_exact_assessment(cursor,self.request(),('i','release','digest','42'),'1')
        original.assert_called_once_with(cursor,self.request(),existing_source_cut=True)
        self.assertEqual(len(cursor.queries),len(CATALOGS));self.assertEqual(legacy,b'{"legacy":"retained"}')
        return exact
    def test_fractional_legacy_counterexample_and_exact_native_fragment(self):
        row='{"facets":{"unknown":1.2345678901234567890000},"prop_id":9007199254740993}'
        legacy=json.dumps(json.loads(row),separators=(',',':')).encode()
        self.assertNotEqual(decode_owner_evidence_json(legacy)['facets']['unknown'].as_tuple(),Decimal('1.2345678901234567890000').as_tuple())
        exact=self.exact([(row,)]);self.assertIn(row.encode(),exact)
        value=decode_owner_evidence_json(exact);self.assertEqual(value['version'],ASSESSMENT)
        self.assertEqual(value['inventory']['properties'][0]['facets']['unknown'].as_tuple(),Decimal('1.2345678901234567890000').as_tuple())
        self.assertEqual(value['inventory']['properties'][0]['prop_id'],9007199254740993)
        self.assertFalse(value['securityReady'])
    def test_unknown_row_content_and_escapes_retained_without_serializer(self):
        raw=' {"opaque":["\\u0061",{"n":1.2300}],"prop_id":1} '
        self.assertIn(raw.encode(),self.exact([(raw,)]))
    def test_malformed_duplicate_nonfinite_or_nonobject_native_rows_refuse(self):
        for raw in ('{','{"n":1,"n":2}','{"n":NaN}','{"n":"\\ud800"}','[]','null'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):self.exact([(raw,)])
    def test_capacity_overflow_refuses_no_partial(self):
        for rows in ([('{}',)]*4097,[(json.dumps({'x':'x'*4_000_000}),)],[(json.dumps({'x':[0]*4097}),)],[(('{"x":'+('1'*513)+'}'),)]):
            with self.assertRaises(ValueError):self.exact(rows)
    def test_identity_and_flag_forms_are_closed(self):
        for raw in ('0','01','+1','1.0','4294967296',True,None,'١'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):_uint(raw)
        self.assertEqual(_uint('4294967295'),'4294967295');self.assertEqual(_uint('0',zero=True),'0')
        for raw in ('true','false'):self.assertIs(type(_boolean(raw)),bool)
        for raw in ('TRUE','0',True,None):
            with self.assertRaises(ValueError):_boolean(raw)
        self.assertEqual(_signed('-2147483648'),-2147483648)
        for raw in ('-0','+1','01','2147483648',True):
            with self.assertRaises(ValueError):_signed(raw)
    def test_release_is_bounded_and_scanned_before_verifier_or_return(self):
        for raw in (b'{"releaseId":"x","releaseId":"y"}',b'{"opaque":"'+b'x'*4_000_001+b'"}'):
            cursor=SimpleNamespace(_deadline=SimpleNamespace(check=lambda:None),execute=lambda *args,**kwargs:None)
            package=SimpleNamespace(joinpath=lambda path:SimpleNamespace(read_bytes=lambda:raw))
            with patch('truss._native_source_observation._text_rows',side_effect=[[('180006','read committed','off')],[('public',)]]),patch('truss._native_source_observation.verify_held_accepted_catalog_source_cut'),patch('truss._native_source_observation.files',return_value=package),patch('truss._native_source_observation._release',side_effect=AssertionError('Manifest must be scanned before release use')):
                with self.assertRaises(ValueError):capture_native_source_observation_with_cursor(cursor,b'{"modules":[{"documentJson":"{}"}]}')
    def test_output_inherits_exact_owner_capacity(self):
        for raw in (b'{"a":1,"a":2}',b'{"x":'+b'1'*513+b'}',b' '*4_000_001):
            with self.assertRaises(ValueError):_bounded(raw)

if __name__=='__main__':unittest.main()
