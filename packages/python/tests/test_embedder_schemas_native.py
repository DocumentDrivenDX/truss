# SPDX-License-Identifier: MIT OR Apache-2.0
"""Frozen unnamed originals refuse; explicit named revisions register exactly."""
import gzip,hashlib,json
from pathlib import Path
from unittest.mock import patch
from truss import CatalogDocument,Ok,prepare_acceptance,PreparationRejected
from embedder_fixture_sources import named_revision
from truss.preparation import prepare_core10_acceptance
from truss.catalog_preparation import _configuration
from truss.catalog_results import CatalogRegistration
import test_catalog_runtime_native as base
corpus=json.loads(gzip.decompress((Path(__file__).with_name('fixtures')/'hohfeld/originals.json.gz').read_bytes()))
class EmbedderSchemaTests(base.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[_name]=None

def registration_case(document):
    def run(self):
        raw=document['sourceText'].encode();self.assertEqual(hashlib.sha256(raw).hexdigest(),document['sha256'])
        source=json.loads(raw);originals=(CatalogDocument(source['id'],document['sha256'],raw),)
        self.install();connection,host,assembly,tx=self.consumer()
        with patch('subprocess.Popen',side_effect=AssertionError('No external process during preparation')):
            revised,missing=named_revision(document)
            self.assertTrue(missing)
            with self.assertRaises(PreparationRejected) as caught:assembly.prepare_catalog(originals)
            diagnostics=[json.loads(d) for d in caught.exception.diagnostics]
            self.assertEqual(caught.exception.reason,'invalid_document')
            self.assertEqual({(d['moduleId'],d['elementId']) for d in diagnostics},set(missing))
            self.assertTrue(all(d['code']=='TRUSS-NAME-MISSING' for d in diagnostics))
            self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
            documents=(revised,);raw=revised.content
            prepared=assembly.prepare_catalog(documents)
            for alias in (prepare_acceptance,prepare_core10_acceptance):
                compatible=alias(documents,json.dumps(_configuration()).encode())
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
