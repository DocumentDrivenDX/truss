"""Original consumer model preparation through the public source-only entrypoint."""
import hashlib,json,os,unittest
from pathlib import Path
from unittest.mock import patch
from truss import CatalogDocument,PreparedAcceptance,prepare_catalog

class CatalogPreparationPublicTests(unittest.TestCase):
    def test_prepare_original_commerce_without_database(self):
        raw=(Path(__file__).parent/'fixtures/commerce-original-umf08.json').read_bytes()
        document=CatalogDocument(json.loads(raw)['id'],hashlib.sha256(raw).hexdigest(),raw)
        with patch('psycopg.connect',side_effect=AssertionError('Preparation must not connect')):
            prepared=prepare_catalog((document,),source_version='0.8.0',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(prepared,PreparedAcceptance)
        self.assertEqual(prepared.documents[0].document.content,raw)
        summary=json.loads(prepared.report_evidence_bytes)
        self.assertEqual(summary['interfaceVersion'],'truss-registration-preparation/2.0')
        self.assertEqual(set(summary),{'interfaceVersion','documents'})
        self.assertTrue(summary['documents'][0]['validation']['valid'])
        self.assertEqual(summary['documents'][0]['contentSha256'],hashlib.sha256(raw).hexdigest())

    def test_large_original_document_does_not_generate_inspection_transcripts(self):
        from test_preparation import document
        from truss._catalog_support import evaluate_catalog_support
        from truss._catalog_report_semantics import compose_original_catalog_report_semantics
        source=json.loads(document('large').content)
        source['vocabularies']={'vendor':{'version':'1.0.0'}}
        source['extensions']={'vendor':{'text':'x'*500000}}
        raw=json.dumps(source).encode()
        prepared=prepare_catalog((CatalogDocument('large','r1',raw),),
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertEqual(prepared.documents[0].document.content,raw)
        self.assertLess(len(prepared.report_evidence_bytes),4096)
        support=evaluate_catalog_support(prepared)
        self.assertEqual(support['closedSourceInventory']['state'],'supported')
        semantic=compose_original_catalog_report_semantics(prepared,support)
        self.assertEqual(semantic['sourceFormat'],'truss-registration-summary/2.0')
        self.assertNotIn('assertionEntries',semantic)

    def test_source_selects_its_profile_and_explicit_mismatch_refuses(self):
        from test_preparation import document
        from truss import PreparationRejected
        from truss.catalog_preparation import _configuration
        for version in ('0.7.0','0.8.0'):
            source=json.loads(document('selected').content);source['umf']=version
            original=CatalogDocument('selected','r1',json.dumps(source).encode())
            prepared=prepare_catalog((original,))
            self.assertEqual(prepared.input()['supportProfile'],_configuration(version)['supportProfile'])
            self.assertEqual(prepared.documents[0].document.content,original.content)
            self.assertIsNone(prepared.documents[0].observation()['transition'])
            other='0.8.0' if version=='0.7.0' else '0.7.0'
            with self.assertRaises(PreparationRejected) as rejected:prepare_catalog((original,),source_version=other)
            self.assertEqual(rejected.exception.reason,'unsupported_profile')
