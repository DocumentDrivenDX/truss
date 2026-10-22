# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original opaque source byte bounds, with real acceptance and exact readback."""
import json
import psycopg
from truss import Ok,CatalogDocument,CatalogRegistration
from truss.preparation import PreparationRejected
import test_group_create_native as fixtures

class CatalogDocumentBoundsTests(fixtures.PublicCreateGroupTests):
    for name in tuple(n for n in dir(fixtures.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None

    @staticmethod
    def sized(source,size):
        source['vocabularies']['x-large']={'version':'1.0.0'};source['extensions']['x-large']={'opaque':''}
        raw=json.dumps(source,separators=(',',':')).encode();source['extensions']['x-large']['opaque']='x'*(size-len(raw))
        result=json.dumps(source,separators=(',',':')).encode();assert len(result)==size;return result

    def test_500kib_original_document_accepts_and_reads_exact_bytes(self):
        c,h,a,t=self.ready(document_ids=('adoc',));source=json.loads(self.documents[0].content);raw=self.sized(source,500*1024)
        document=CatalogDocument('adoc','large-r2',raw);prepared=a.prepare_catalog((document,))
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        accepted=a.accept_in_transaction(t,prepared,request_key='large-original');self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted))
        observed=a.accepted_document_in_transaction(t,document_id='adoc');self.assertIsInstance(observed,Ok,repr(observed));self.assertEqual(observed.value.content,raw)

    def test_one_byte_above_document_budget_refuses_without_native_effects(self):
        c,h,a,t=self.ready(document_ids=('adoc',));raw=self.sized(json.loads(self.documents[0].content),4194305)
        with self.assertRaises(PreparationRejected) as raised:a.prepare_catalog((CatalogDocument('adoc','over-r2',raw),))
        self.assertEqual(raised.exception.reason,'resource')
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(1,))
