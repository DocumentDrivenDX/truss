import json
import unittest
from pathlib import Path
from truss._umf_key_tuples import KeyTupleRequest, encode_string_key_tuples
from test_catalog_relational_support import relational_document


class OriginalUmfKeyTupleTests(unittest.TestCase):
    def source(self,identity='key-document'):
        value=relational_document();value['id']=identity
        return json.dumps(value).encode()

    def encode(self,requests,source=None):
        return encode_string_key_tuples(self.source() if source is None else source,requests,bun_executable='/opt/homebrew/bin/bun')

    def test_composite_component_order_and_ambiguous_concatenations(self):
        requests=tuple(KeyTupleRequest('m','A','a-primary',values) for values in (('ab','c'),('a','bc'),('c','ab')))
        results=self.encode(requests)
        self.assertEqual(len({result.tuple_bytes for result in results}),3)
        for result in results:
            receipt=json.loads(result.original_receipt_bytes)
            self.assertEqual(receipt['values'],[{'string':value} for value in result.request.values])
            self.assertEqual(receipt['keyPath'],'/modules/0/elements/0/keys/1')
            self.assertEqual(receipt['version'],'2.0.0')

    def test_empty_strings_unicode_and_qualified_namespace(self):
        request=KeyTupleRequest('m','A','a-primary',('','é'))
        a=self.encode((request,),self.source('a'))[0]
        b=self.encode((request,),self.source('b'))[0]
        self.assertEqual(a.tuple_bytes,b.tuple_bytes)
        self.assertNotEqual(a.document_sha256,b.document_sha256)
        decomposed=self.encode((KeyTupleRequest('m','A','a-primary',('','e\u0301')),))[0]
        self.assertNotEqual(a.tuple_bytes,decomposed.tuple_bytes)

    def test_invalid_key_or_missing_component_refuses_entire_batch(self):
        valid=KeyTupleRequest('m','A','a-primary',('a','b'))
        for invalid in (KeyTupleRequest('m','A','absent',('a','b')),KeyTupleRequest('m','A','a-primary',('a',))):
            with self.assertRaises(ValueError):self.encode((valid,invalid))

    def test_owner_parser_refuses_duplicate_source_and_aggregate_overflow(self):
        source=self.source().replace(b'"umf": "0.7.0"',b'"umf":"0.7.0","umf":"0.7.0"')
        with self.assertRaises(ValueError):self.encode((KeyTupleRequest('m','A','a-primary',('a','b')),),source)
        values=('x'*600000,'y'*600000)
        with self.assertRaises(ValueError):self.encode((KeyTupleRequest('m','A','a-primary',values),))

    def test_original_umf_string_byte_vectors(self):
        corpus=json.loads((Path(__file__).parent/'fixtures/umf-string-key-vectors.json').read_bytes())
        for vector in corpus['vectors']:
            with self.subTest(vector=vector['id']):
                request=KeyTupleRequest('m','A','z-alt',tuple(value['string'] for value in vector['values']))
                self.assertEqual(self.encode((request,))[0].tuple_bytes.hex(),vector['expectedHex'])

    def test_wrong_document_stale_source_and_boolean_substitution_refuse(self):
        from unittest.mock import patch
        from subprocess import CompletedProcess
        request=KeyTupleRequest('m','A','a-primary',('a','b'))
        original=self.encode((request,))[0]
        receipt=json.loads(original.original_receipt_bytes)
        for mutation in ('wrong-document','stale-source','boolean-substitution'):
            current=json.loads(self.source())
            candidate=json.loads(original.original_receipt_bytes)
            if mutation=='wrong-document':current['id']='other'
            elif mutation=='stale-source':current['modules'][0]['elements'][0]['keys'][0]['name']='changed'
            else:candidate['source']['modules'][0]['relationships'][0]['directed']=1
            response=json.dumps({'status':'encoded','receiptTexts':[json.dumps(candidate)]}).encode()
            captures=[CompletedProcess([],0,b'1.4.2\n',b''),CompletedProcess([],0,response,b'')]
            with self.subTest(mutation=mutation),patch('truss._umf_key_tuples._capture',side_effect=captures),self.assertRaises(ValueError):
                self.encode((request,),json.dumps(current).encode())

    def test_owner_numeric_normalization_and_full_supported_batch(self):
        source=self.source().replace(b'"min": 0',b'"min": 0.0')
        request=KeyTupleRequest('m','A','a-primary',('a','b'))
        normalized=self.encode((request,),source)[0]
        self.assertEqual(json.loads(normalized.original_receipt_bytes)['source']['modules'][0]['relationships'][0]['sourceMultiplicity']['min'],0)
        batch=self.encode((request,)*512)
        self.assertEqual(len(batch),512)
        self.assertTrue(all(result.tuple_bytes==batch[0].tuple_bytes for result in batch))



    def test_core08_original_owner_receipt_and_legacy_byte_vectors(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/security-mapping-request.json').read_bytes())
        source=fixture['modules'][0]['documentJson'].encode()
        for text in ('','é','e\u0301','a\0b'):
            current=self.encode((KeyTupleRequest('m','Staff','pk',(text,)),),source)[0]
            legacy=self.encode((KeyTupleRequest('m','A','z-alt',(text,)),))[0]
            self.assertEqual(current.tuple_bytes,legacy.tuple_bytes)
            self.assertEqual(json.loads(current.original_receipt_bytes)['version'],'3.0.0')
            self.assertEqual(json.loads(current.original_receipt_bytes)['source']['umf'],'0.8.0')

    def test_core08_compound_key_and_missing_component_refusal(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/security-mapping-request.json').read_bytes());source=json.loads(fixture['modules'][0]['documentJson'])
        staff=next(e for e in source['modules'][0]['elements'] if e['id']=='Staff')
        staff['members'].append({'module':'m','element':'staffCode'});staff['keys'][0]['fields'].append({'module':'m','element':'staffCode'})
        source['modules'][0]['elements'].append({'id':'staffCode','kind':'field','name':'staffCode','scalarType':'string','nullability':'required','cardinality':'one','extensions':{}})
        original=json.dumps(source).encode()
        outputs=self.encode(tuple(KeyTupleRequest('m','Staff','pk',v) for v in (('ab','c'),('a','bc'),('c','ab'))),original)
        self.assertEqual(len({r.tuple_bytes for r in outputs}),3)
        with self.assertRaises(ValueError):self.encode((KeyTupleRequest('m','Staff','pk',('only',)),),original)

if __name__=='__main__':unittest.main()
