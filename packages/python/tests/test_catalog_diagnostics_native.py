"""Original version-specific warnings remain retained and uninterpreted."""
import base64,json,hashlib,os
from decimal import Decimal
from truss import Ok,AcceptedDocument,QueryRows
from truss.contracts import TextValue
from truss.groups import CreateObject,RootlessOwnership,GroupSuccess
import test_numeric_facets_native as base

class CatalogDiagnosticTests(base.NumericFacetTests):
    for _name in tuple(n for n in dir(base.NumericFacetTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.7.0'
    def fields(self,source):
        super().fields(source);source['umf']=self.source_version
        source['vocabularies']={'urn:truss:test:opaque':{'version':'0.1.0'}}
        source['extensions']={'urn:truss:test:opaque':{'opaque':{'future':['uninterpreted','content']}}}
    def test_warn_accept_exact_source_report_write_read_and_query(self):
        c,h,a,t=self.ready(self.fields)
        original=next(d.content for d in self.documents if d.document_id=='adoc')
        source=a.accepted_document_in_transaction(t,document_id='adoc').value;self.assertIsInstance(source,AcceptedDocument);self.assertEqual(source.content,original);self.assertEqual(source.sha256,hashlib.sha256(original).hexdigest())
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        report=a.report_in_transaction(t).value.original_bytes;decoded=json.loads(report)['source']
        self.assertEqual({d['completeness'] for d in decoded['documentInterpretations']},{'partial'})
        diagnostics=[json.loads(base64.b64decode(d['diagnostic']['bytesBase64'])) for d in decoded['diagnostics']]
        prepared=a.prepare_catalog(self.documents,source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertEqual(decoded['diagnostics'],json.loads(prepared.report_evidence_bytes)['validation']['diagnostics']);self.assertTrue(any(d['diagnostic']['code']=='UNKNOWN_EXTENSION' for d in diagnostics))
        self.assertEqual(len(decoded['extensions']),2)
        created=self.apply(a,t,*self.input(a,t,(CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.values(),ownership=RootlessOwnership()),)))
        self.assertIsInstance(created,GroupSuccess);h.detach();c.commit();c,h,a,t=self.consumer()
        value=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(created.response.semantic.results[0].identity.id)).value.object
        self.assertEqual(dict(value.values)['quantity'],TextValue(kind='integer',text='9007199254740993'))
        query=a.query_in_transaction(t,sql='SELECT a.quantity,a.amount FROM "A" a',document_ids=('adoc',));self.assertIsInstance(query.value,QueryRows,repr(query));self.assertEqual(query.value.rows,((9007199254740993,Decimal('1.2300')),))
        self.assertEqual(a.report_in_transaction(t).value.original_bytes,report);h.detach();c.rollback()

class CatalogDiagnostic08Tests(CatalogDiagnosticTests):
    source_version='0.8.0'
