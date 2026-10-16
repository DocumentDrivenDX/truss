"""Original UMF domain packs through public catalog acceptance and commit/retry."""
import gzip
import hashlib
import json
import os
from pathlib import Path
from truss import CatalogDocument,Ok
from truss.catalog_results import CatalogRegistration
import test_catalog_runtime_native as base

fixture=Path(__file__).with_name('fixtures')/'umf-domain-packs'/'originals.json.gz'
corpus=json.loads(gzip.decompress(fixture.read_bytes()))

class DomainPackCatalogTests(base.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

def registration_case(document):
    def run(self):
        raw=document['sourceText'].encode('utf8')
        self.assertEqual(hashlib.sha256(raw).hexdigest(),document['sha256'])
        source=json.loads(raw)
        self.install()
        connection,host,assembly,tx=self.consumer()
        prepared=assembly.prepare_catalog((CatalogDocument(source['id'],document['sha256'],raw),),
            source_version=source['umf'],bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        request_key='domain-pack-'+document['pack']
        accepted=assembly.accept_in_transaction(tx,prepared,request_key=request_key)
        self.assertIsInstance(accepted,Ok,repr(accepted))
        self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted))
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        replay=assembly.accept_in_transaction(tx,prepared,request_key=request_key)
        self.assertIsInstance(replay,Ok,repr(replay))
        self.assertIsInstance(replay.value,CatalogRegistration,repr(replay))
        self.assertTrue(replay.value.replayed)
        self.assertEqual(replay.value.report_bytes,accepted.value.report_bytes)
        host.detach();connection.commit()
    return run

for index,document in enumerate(corpus['documents']):
    setattr(DomainPackCatalogTests,'test_'+str(index).zfill(2)+'_'+document['pack'].replace('-','_'),registration_case(document))
