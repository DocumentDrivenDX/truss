"""Basic source preparation for declaration-only scalar Fields; no native claim."""
import json
import os
from pathlib import Path
import unittest
from truss import CatalogDocument
from truss.preparation import prepare_core08_acceptance
from truss.catalog_preparation import _configuration
from truss._catalog_report_semantics import canonical_numeric_free
from truss._catalog_source_reference import DECLARATIVE08_PROFILE, RECURSIVE08_PROFILE
from truss._catalog_support import evaluate_catalog_support


class DeclarativeCatalogTests(unittest.TestCase):
    def test_exact_owner_model_keeps_standalone_scalar_without_storage_declaration(self):
        root=Path(__file__).resolve().parents[3]
        content=(root/'docs/helix/04-build/evidence/named-current-native-refusal-20261015/original-core.json').read_bytes()
        for pin,state in ((RECURSIVE08_PROFILE,'unavailable'),(DECLARATIVE08_PROFILE,'inventoried')):
            with self.subTest(profile=pin['version']):
                config=_configuration('0.8.0');config['supportProfile']=dict(pin)
                prepared=prepare_core08_acceptance((CatalogDocument('domain','named-query-core-r1',content),),canonical_numeric_free(config),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                inventory=evaluate_catalog_support(prepared)['closedSourceInventory']
                self.assertEqual(inventory['state'],state)
                self.assertEqual(prepared.documents[0].document.content,content)
                self.assertNotIn('clear',[field['fieldId'] for doc in json.loads(prepared.declarations_bytes) for record in doc['records'] for field in record['fields']])
                if state=='inventoried':
                    self.assertTrue(inventory['assertionOccurrenceCoverageComplete'])
                    self.assertTrue(all(entry['enforcement']=='none' for entry in inventory['entries']))
                    self.assertFalse(inventory['acceptedReportQualified'])
