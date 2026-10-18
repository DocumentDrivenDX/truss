"""The exact Pizza, Northwind and catalog schemas that previously failed registration."""
import gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
from truss import CatalogDocument,Ok,prepare_acceptance
from truss.preparation import prepare_core08_acceptance
from truss.catalog_preparation import _configuration
from truss.catalog_results import CatalogRegistration
import test_catalog_runtime_native as base
corpus=json.loads(gzip.decompress((Path(__file__).with_name('fixtures')/'hohfeld/originals.json.gz').read_bytes()))
class EmbedderSchemaTests(base.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[_name]=None

def registration_case(document):
    def run(self):
        raw=document['sourceText'].encode();self.assertEqual(hashlib.sha256(raw).hexdigest(),document['sha256'])
        source=json.loads(raw);documents=(CatalogDocument(source['id'],document['sha256'],raw),)
        self.install();connection,host,assembly,tx=self.consumer()
        with patch('subprocess.Popen',side_effect=AssertionError('No external process during preparation')):
            prepared=assembly.prepare_catalog(documents)
            for alias in (prepare_acceptance,prepare_core08_acceptance):
                compatible=alias(documents,json.dumps(_configuration(source['umf'])).encode())
                self.assertEqual(compatible.input(),prepared.input())
                self.assertEqual(compatible.report_evidence_bytes,prepared.report_evidence_bytes)
                self.assertEqual(compatible.documents[0].document.content,raw)
        self.assertLess(len(prepared.report_evidence_bytes),16384)
        request='embedder-'+document['sample'];accepted=assembly.accept_in_transaction(tx,prepared,request_key=request)
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(accepted.value,CatalogRegistration)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        replay=assembly.accept_in_transaction(tx,prepared,request_key=request)
        self.assertIsInstance(replay,Ok,repr(replay));self.assertTrue(replay.value.replayed)
        self.assertEqual(replay.value.report_bytes,accepted.value.report_bytes)
        # Native schema_doc is the custody authority; compare its exact original text.
        archived=self.admin.execute('SELECT document FROM truss.schema_doc WHERE doc_id=%s',(source['id'],)).fetchone()[0]
        self.assertEqual(archived.encode(),raw)
        host.detach();connection.commit()
    return run
for document in corpus['documents']:setattr(EmbedderSchemaTests,'test_'+document['sample'],registration_case(document))
