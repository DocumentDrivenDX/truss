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
        self.assertEqual(json.loads(prepared.report_evidence_bytes)['ownerObservations']['sourceFormat'],'truss-catalog-source-reference/0.1')
