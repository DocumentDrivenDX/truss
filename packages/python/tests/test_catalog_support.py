# SPDX-License-Identifier: MIT OR Apache-2.0
"""Current UMF 0.10 preparation and selected storage-support outcomes."""
import copy
import json
import unittest

from truss import CatalogDocument, PreparationRejected
from truss._catalog_support import DATE10_PROFILE, evaluate_catalog_support
from test_catalog_relational_support import relational_document, relational_prepared
from test_preparation import prepare
from truss.catalog_preparation import _configuration


def selected(value=None):
    source=copy.deepcopy(relational_document() if value is None else value)
    source['id']='support'
    return prepare((CatalogDocument('support','r1',json.dumps(source).encode()),))


class CatalogSupportTests(unittest.TestCase):
    def test_current_source_uses_one_exact_support_profile_and_summary(self):
        prepared=selected()
        self.assertEqual(prepared.input()['supportProfile'],DATE10_PROFILE)
        evidence=json.loads(prepared.report_evidence_bytes)
        self.assertEqual(evidence['interfaceVersion'],'truss-registration-preparation/2.0')
        self.assertTrue(all(item['validation']['valid'] for item in evidence['documents']))
        self.assertNotIn('ownerObservations',evidence)
        support=evaluate_catalog_support(prepared)
        self.assertEqual(support['state'],'evaluated')
        self.assertEqual(support['profile'],DATE10_PROFILE)
        self.assertEqual(support['closedSourceInventory']['state'],'supported')
        self.assertNotIn('entries',support['closedSourceInventory'])

    def test_semantic_metadata_and_unknown_extensions_remain_in_original_source(self):
        source=relational_document();source['id']='support'
        source['vocabularies']={'example.identity':{'version':'99.0.0'},
            'vendor.example':{'version':'1.0.0'}}
        field=next(e for e in source['modules'][0]['elements'] if e['id']=='A-label')
        field['semanticTypes']=[{'vocabulary':'example.identity','version':'1.0.0','term':'external-id'}]
        field['extensions']={'vendor.example':{'opaque':['retain',None,{'text':'雪'}]}}
        prepared=selected(source)
        observed=prepared.documents[0].source()
        self.assertEqual(observed['modules'][0]['elements'][-4]['semanticTypes'],field['semanticTypes'])
        self.assertEqual(observed['modules'][0]['elements'][-4]['extensions'],field['extensions'])
        self.assertEqual(prepared.documents[0].document.content,json.dumps(source).encode())

    def test_unknown_native_scalar_is_storage_unavailable(self):
        source=relational_document();source['id']='support'
        field=next(e for e in source['modules'][0]['elements'] if e['id']=='A-label')
        field['scalarType']='uuid'
        prepared=selected(source)
        support=evaluate_catalog_support(prepared)
        self.assertEqual(support['state'],'evaluated')
        self.assertEqual(support['closedSourceInventory'],
            {'state':'unavailable','reason':'unsupported_storage_definition'})

    def test_old_umf_version_is_rejected_as_input(self):
        source=relational_document();source['id']='legacy';source['umf']='0.7.0'
        with self.assertRaises(PreparationRejected) as raised:
            prepare((CatalogDocument('legacy','r1',json.dumps(source).encode()),))
        self.assertEqual(raised.exception.reason,'unsupported_profile')

    def test_profile_substitution_is_unavailable(self):
        config=copy.deepcopy(_configuration())
        config['supportProfile']={'identity':'truss-fresh-catalog-support','version':'0.1.0','sha256':'0'*64}
        source=relational_document();source['id']='support'
        prepared=prepare((CatalogDocument('support','r1',json.dumps(source).encode()),),config)
        self.assertEqual(evaluate_catalog_support(prepared),{'state':'unavailable','reason':'unregistered_support_policy'})


# Preserve the shared constructor imported by other current-format tests.
__all__=['selected','CatalogSupportTests']
