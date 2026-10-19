# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original UMF domain packs through public catalog acceptance and commit/retry."""
import gzip
import hashlib
import json
import os
from pathlib import Path
from truss import CatalogDocument,Ok
from truss.catalog_results import CatalogRegistration
import test_catalog_runtime_native as base

fixture_dir=Path(__file__).with_name('fixtures')/'umf-domain-packs'
historical=json.loads(gzip.decompress((fixture_dir/'originals.json.gz').read_bytes()))
corpus=json.loads(gzip.decompress((fixture_dir/'successors-0.10.0.json.gz').read_bytes()))
historical_by_pack={document['pack']:document for document in historical['documents']}
assert len(historical_by_pack)==21
assert len(corpus['documents'])==len(historical_by_pack)
assert corpus['producer']['repository']=='DocumentDrivenDX/umf'
assert corpus['producer']['commit']=='4fc64adf30e2f49eae28162cf476ecd01ce505e3'

class DomainPackCatalogTests(base.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

def registration_case(document):
    def run(self):
        raw=document['sourceText'].encode('utf8')
        self.assertEqual(hashlib.sha256(raw).hexdigest(),document['sha256'])
        source=json.loads(raw)
        self.assertEqual(source['umf'],'0.10.0')
        original=historical_by_pack[document['pack']]
        self.assertEqual(document['historicalPath'],original['path'])
        self.assertEqual(document['historicalSha256'],original['sha256'])
        self.install()
        connection,host,assembly,tx=self.consumer()
        prepared=assembly.prepare_catalog((CatalogDocument(source['id'],document['sha256'],raw),),
            source_version='0.10.0',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
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
