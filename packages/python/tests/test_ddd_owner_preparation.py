# SPDX-License-Identifier: MIT OR Apache-2.0
"""The selected UMF DDD owner validates original bytes separately from core."""
import hashlib
import json
import unittest

from truss import CatalogDocument, PreparationRejected, prepare_catalog


def ddd_document(*, valid=True):
    source={
        'umf':'0.10.0','id':'ddd-model','vocabularies':{'umf.ddd':{'version':'0.1.0'}},'extensions':{},
        'modules':[{'id':'sales','namespace':'sales','extensions':{'umf.ddd':{'kind':'bounded-context','terms':[]}},
            'elements':[
                {'id':'Item','kind':'record','members':[{'module':'sales','element':'label'}],
                    'extensions':{'umf.ddd':{'kind':'entity','fields':{
                        'label':{'type':{'kind':'scalar','name':'string'},'cardinality':'one'}},
                        'identity':{'fields':['missing' if not valid else 'label'],'scope':'context'}}}},
                {'id':'label','kind':'field','name':'label','scalarType':'string','nullability':'required','cardinality':'one','extensions':{}},
            ]}],
    }
    raw=json.dumps(source,separators=(',',':')).encode('utf8')
    return CatalogDocument('ddd-model','r1',raw)


class DddOwnerPreparationTests(unittest.TestCase):
    def test_original_umf_accepts_hallmark_optional_field_evolution(self):
        original=ddd_document()
        source=json.loads(original.content)
        record=source['modules'][0]['elements'][0]
        record['members'].append({'module':'sales','element':'note'})
        record['extensions']['umf.ddd']['fields']['note']={
            'type':{'kind':'scalar','name':'string'},'cardinality':'optional'}
        source['modules'][0]['elements'].append({'id':'note','kind':'field','name':'note','scalarType':'string',
            'nullability':'absent-allowed','cardinality':'one','extensions':{}})
        evolved=CatalogDocument('ddd-model','r2',json.dumps(source,separators=(',',':')).encode('utf8'))
        prepared=prepare_catalog((evolved,),source_version='0.10.0')
        observation=prepared.documents[0].observation()
        self.assertTrue(observation['sourceValidation']['valid'])
        self.assertTrue(observation['dddValidation']['valid'])
        self.assertEqual(observation['originalText'],evolved.content.decode('utf8'))

    def test_original_ddd_result_is_separate_and_profile_bound(self):
        original=ddd_document()
        prepared=prepare_catalog((original,),source_version='0.10.0')
        observation=prepared.documents[0].observation()
        self.assertEqual(observation['originalText'],original.content.decode('utf8'))
        self.assertTrue(observation['sourceValidation']['valid'])
        self.assertTrue(observation['dddValidation']['valid'])
        self.assertIn('diagnostics',observation['dddValidation'])
        self.assertEqual(observation['dddProfile']['identity'],'umf-ddd-document-validation')
        self.assertEqual(observation['dddProfile']['version'],prepared.provenance.owner_revision)
        self.assertEqual(observation['dddProfile']['sha256'],prepared.provenance.owner_bundle_sha256)
        evidence=json.loads(prepared.report_evidence_bytes)['documents'][0]
        self.assertIn('validation',evidence)
        self.assertIn('dddValidation',evidence)
        archived=json.loads(prepared.archive_documents_bytes)[0]
        self.assertEqual(archived['originalText'],original.content.decode('utf8'))
        self.assertIn('sourceValidation',archived['validation'])
        self.assertIn('dddValidation',archived['validation'])
        self.assertEqual(hashlib.sha256(original.content).hexdigest(),evidence['contentSha256'])

    def test_invalid_ddd_diagnostics_are_retained_separately(self):
        with self.assertRaises(PreparationRejected) as caught:
            prepare_catalog((ddd_document(valid=False),),source_version='0.10.0')
        self.assertEqual(caught.exception.reason,'invalid_document')
        diagnostic=json.loads(caught.exception.diagnostics[0])
        self.assertIn('validation',diagnostic)
        self.assertIn('dddValidation',diagnostic)
        self.assertFalse(diagnostic['dddValidation']['valid'])
        self.assertTrue(any(item['code']=='DDD_IDENTITY' for item in diagnostic['dddValidation']['diagnostics']))


if __name__=='__main__':
    unittest.main()
