# SPDX-License-Identifier: MIT OR Apache-2.0
"""Load original UMF pack ontologies through the public Python API.

Set TRUSS_UMF_DOMAIN_PACK_ROOT to an UMF checkout. These checks cover native
catalog acceptance and committed catalog/source readback, not dataset loading.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest
import psycopg
from truss import (Ok,CatalogDocument,ModuleAccessGrant,adopt_psycopg_host,
                   create_reference_assembly,CatalogRuntimeConfiguration)
from truss.reader_catalog import AcceptedDocument,ReaderCatalog
from test_catalog_runtime_native import PublicCatalogRuntimeTests

ROOT=os.environ.get('TRUSS_UMF_DOMAIN_PACK_ROOT')

@unittest.skipUnless(ROOT,'Set TRUSS_UMF_DOMAIN_PACK_ROOT to the original UMF checkout')
class DomainPackCatalogTests(PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

    def load_original(self,path):
        self.install()
        raw=path.read_bytes();source=json.loads(raw);digest=sha256(raw).hexdigest()
        connection,host,assembly,tx=self.consumer()
        prepared=assembly.prepare_catalog((CatalogDocument(source['id'],digest,raw),),
            source_version=source['umf'],bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='original-domain-pack')
        self.assertIsInstance(accepted,Ok,repr(accepted))
        host.detach();connection.commit()
        self.admin.execute('BEGIN')
        admin_host=adopt_psycopg_host(self.admin);self.addCleanup(admin_host.detach)
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        admin_tx=admin_host.adopt_transaction().value
        for role in ('pack_reader','pack_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        grants=tuple(ModuleAccessGrant(source['id'],module['id'],'pack_reader','pack_writer') for module in source['modules'])
        configured=admin_assembly.configure_module_access_in_transaction(admin_tx,grants)
        self.assertIsInstance(configured,Ok,repr(configured))
        admin_host.detach();self.admin.commit()
        self.admin.execute('GRANT pack_reader TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection,host,assembly,tx=self.consumer()
        document=assembly.accepted_document_in_transaction(tx,document_id=source['id'])
        self.assertIsInstance(document,Ok,repr(document))
        self.assertIsInstance(document.value,AcceptedDocument,repr(document.value))
        self.assertEqual(document.value.content,raw)
        self.assertEqual(document.value.sha256,digest)
        view=assembly.reader_catalog_in_transaction(tx,maximum_bytes=16777216)
        self.assertIsInstance(view,Ok,repr(view))
        self.assertIsInstance(view.value,ReaderCatalog,repr(view.value))
        expected={e['id'] for m in source['modules'] for e in m['elements'] if e['kind']=='record'}
        found={t['recordId'] for module in view.value.modules for t in module['types'] if t['kind']=='record'}
        self.assertEqual(found,expected)
        expected_fields={(m['id'],e['id']):e.get('scalarType') for m in source['modules'] for e in m['elements'] if e['kind']=='field'}
        found_fields={(m['moduleId'],p['fieldId']):p['scalarType'] for m in view.value.modules for p in m['properties']}
        self.assertEqual(found_fields,expected_fields)
        expected_relationships={(m['id'],r['id']) for m in source['modules'] for r in m.get('relationships',())}
        found_relationships={(m['moduleId'],r['authoredId']) for m in view.value.modules for r in m['relationships']}
        self.assertEqual(found_relationships,expected_relationships)
        host.detach();connection.rollback()

if ROOT:
    for pack in sorted((Path(ROOT)/'spec/domain-packs').glob('*/pack.json')):
        metadata=json.loads(pack.read_text())
        for schema in metadata.get('schemas',[]):
            if schema.get('format')!='umf':continue
            path=pack.parent/schema['reference']
            def check(self,path=path):self.load_original(path)
            setattr(DomainPackCatalogTests,'test_'+pack.parent.name.replace('-','_')+'_'+schema['id'].replace('-','_'),check)
