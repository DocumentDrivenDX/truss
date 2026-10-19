# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic native-to-generated Key adapter checks; requires generated commerce models."""
import copy
from types import SimpleNamespace
import unittest
from commerce import OrderLineKey
from truss.access import _typed_rows
from truss.query import QueryRows, QueryRelatedKeys
from umf_access.related_keys import key_descriptor, make_related_result_model


def fixture():
    key=key_descriptor(OrderLineKey);source=OrderLineKey.UMF_SOURCE
    identity={'documentId':source.document_id,'revision':'original-owner-revision'}
    relation={'module':'commerce','id':'original-relation','direction':'inverse'}
    pins=[{**identity,'sha256':source.document_sha256,'umfVersion':source.core_version}]
    decoder={'profile':'truss-related-keys/0.1','bound':2,'relationship':relation,'key':key,
        'target':{**identity,'module':key['module'],'element':key['record']},'modelPins':pins,
        'representation':{'kind':'relatedKeys','bound':2,
            'relationship':{**identity,'module':relation['module'],'relationship':relation['id']},
            'key':{'id':key['key'],'fields':[{**identity,**c['field']} for c in key['components']],
                'types':[{'family':c['carrier'],'facets':{},'nullable':False} for c in key['components']]}}}
    decoder['representation']['key']['types'][1]['facets']={'integerWidth':{'bits':64,'signed':True}}
    model=make_related_result_model('NativeRelatedLines',OrderLineKey,OrderLineKey,'lines',decoder,OrderLineKey)
    program={'outputs':[{'name':'lines','carrier':'related-keys','nullable':False,'decoder':decoder}],
        'artifact':{'modelPins':pins,'columns':[{'outputName':'lines','position':3,'nullable':False,'representation':decoder['representation']}]}}
    return SimpleNamespace(result=model),program


class RelatedKeyAdapterTests(unittest.TestCase):
    def test_exact_generated_keys_preserve_parallel_occurrences(self):
        entry,program=fixture();large=7
        carrier=QueryRelatedKeys((('a',large),('a',large)),True)
        native=QueryRows(('line_order_id','line_number','lines'),(('root',1,carrier),),1)
        result=_typed_rows(entry,program,native)
        self.assertEqual(result[0].lines.items,(OrderLineKey(line_order_id='a',line_number=large),)*2)
        self.assertIs(type(result[0].lines.items[0]),OrderLineKey)
        self.assertTrue(result[0].lines.truncated)
        self.assertIs(native.rows[0][2],carrier)

    def test_empty_result_still_checks_original_correspondence(self):
        entry,program=fixture();native=QueryRows(('line_order_id','line_number','lines'),(),1)
        self.assertEqual(_typed_rows(entry,program,native),[])
        changed=copy.deepcopy(program);changed['artifact']['modelPins'][0]['sha256']='0'*64
        # Keep the output decoder untouched: a different compiler source must refuse.
        changed['outputs']=copy.deepcopy(program['outputs'])
        with self.assertRaises(ValueError):_typed_rows(entry,changed,native)

    def test_wrong_order_and_inexact_components_refuse(self):
        entry,program=fixture()
        for items in ((('b',1),('a',1)),(('a',True),),(('a',1.0),)):
            native=QueryRows(('line_order_id','line_number','lines'),(('root',1,QueryRelatedKeys(items,False)),),1)
            with self.subTest(items=items),self.assertRaises(ValueError):_typed_rows(entry,program,native)


if __name__=='__main__':unittest.main()
