"""Every unchanged stress schema through public preparation and native registration."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from performance_workloads import schema,workloads
from truss import CatalogDocument,Ok
from truss.catalog_results import CatalogRegistration
import test_catalog_runtime_native as base
class StressRegistrationTests(base.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[_name]=None

def registration_case(name,workload):
    def run(self):
        raw=json.dumps(schema(workload),separators=(',',':')).encode()
        self.install();connection,host,assembly,tx=self.consumer()
        prepared=assembly.prepare_catalog((CatalogDocument('perf-'+name,'matrix-v1',raw),))
        self.assertEqual(prepared.documents[0].document.content,raw)
        self.assertIsNone(prepared.documents[0].observation()['transition'])
        started=time.monotonic()
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='matrix-'+name)
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(host._custody.last_attempt.error))
        self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted))
        host.detach();connection.commit()
        # Source has one custody home. Receipts and pin indexes hold references.
        self.assertEqual(self.admin.execute('SELECT octet_length(document_bytes),octet_length(declaration_bytes) FROM truss.catalog_registration_request WHERE revision=1').fetchone(),(0,0))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.schema_change').fetchone(),(0,))
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_attribute WHERE attrelid='truss.runtime_definition_source'::regclass AND attname='fragment' AND NOT attisdropped").fetchone(),(0,))
        homes=('schema_doc','type_def','prop_def','key_def','rel_def','runtime_definition_source','catalog_registration_request','catalog_acceptance_report')
        sizes={home:self.admin.execute('SELECT pg_total_relation_size(%s::regclass)',('truss.'+home,)).fetchone()[0] for home in homes}
        print(json.dumps({'schema':name,'sourceBytes':len(raw),'registrationSeconds':time.monotonic()-started,'storageBytesIncludingIndexesAndToast':sizes}),flush=True)
    return run
for name,workload in workloads().items():setattr(StressRegistrationTests,'test_'+name.replace('-','_'),registration_case(name,workload))
