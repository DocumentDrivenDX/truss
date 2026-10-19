# SPDX-License-Identifier: MIT OR Apache-2.0
"""One tiny public workflow over the unchanged consumer commerce UMF0.8 model."""
import base64, hashlib, json, os
from decimal import Decimal
from pathlib import Path
import psycopg
from truss import (Ok, CatalogDocument, CatalogRegistration, resolve_catalog_report_source, prepare_catalog, AcceptedDocument, ModuleAccessGrant,
    adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration, ObjectFound, QueryRows, FeedPage)
from truss.contracts import MapValue, TextValue
from truss.groups import (CreateObject, CreateEdge, AuthoredValue, RootlessOwnership, AliasObjectReference,
    NullOrderKey, GroupSuccess, CommittedReceiptReplay)
import test_group_create_native as base

class CommerceSourceTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    def test_original_document_register_create_link_query_replay_feed(self):
        raw=(Path(__file__).parent/'fixtures/commerce-original-umf08.json').read_bytes()
        source=json.loads(raw);doc=source['id'];digest=hashlib.sha256(raw).hexdigest()
        document=CatalogDocument(doc,digest,raw);self.documents=(document,)
        prepared=prepare_catalog(self.documents,source_version='0.8.0',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.install();c,h,a,t=self.consumer()
        accepted=a.accept_in_transaction(t,prepared,request_key='original-commerce')
        self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(h._custody.last_attempt.error))
        self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted))
        report=json.loads(accepted.value.report_bytes)
        self.assertEqual(report['interfaceVersion'],'truss-catalog-registration-report/0.6')
        self.assertEqual(report['source']['sourceFormat'],'truss-registration-summary/2.0')
        self.assertNotIn('assertionEntries',report['source'])
        retained=report['acceptedInput']['documents'][0]
        artifact=retained['artifact']
        reference={'identity':artifact['identity'],'sha256':artifact['sha256'],
            'reference':{'interfaceVersion':'truss-catalog-source-reference/0.1',
                'documentId':doc,'contentSha256':digest,'documentRevision':digest,'basis':'original'}}
        self.assertNotIn('bytesBase64',artifact)
        with self.assertRaisesRegex(ValueError,'accepted_document_in_transaction'):
            resolve_catalog_report_source(accepted.value.report_bytes,reference)
        h.detach();c.commit()
        for role in ('group_reader','group_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN');ah=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        aa=create_reference_assembly(CatalogRuntimeConfiguration(),ah).value;at=ah.adopt_transaction().value
        self.assertIsInstance(aa.configure_module_access_in_transaction(at,(ModuleAccessGrant(doc,'domain','group_reader','group_writer'),)),Ok)
        self.assertIsInstance(aa.register_feed_consumer_in_transaction(at,consumer_id='commerce',reader_role='group_reader'),Ok)
        ah.detach();self.admin.commit();self.admin.execute('GRANT group_writer,group_reader TO consumer WITH SET FALSE')
        self.admin.execute('REVOKE '+self.installation.registrar_role+' FROM consumer')
        c,h,a,t=self.consumer()
        got=a.accepted_document_in_transaction(t,document_id=doc).value
        self.assertIsInstance(got,AcceptedDocument);self.assertEqual((got.content,got.sha256),(raw,digest))
        def create(record,alias,values):
            pin=a.get_type_reference_in_transaction(t,document_id=doc,module_id='domain',record_id=record).value.definition_pin
            return CreateObject(type_definition_pin=pin,alias=alias,ownership=RootlessOwnership(),values=tuple(AuthoredValue(name=n,value=TextValue(kind=k,text=v)) for n,k,v in values))
        maximum='9999999999999999.99'
        supplier=create('suppliers','supplier',(('id','string','s1'),('name','string','Supplier')))
        product=create('products','product',(('id','string','p1'),('supplier_id','string','s1'),('sku','string','SKU-1'),('unit_price','decimal',maximum)))
        pin=a.get_relationship_reference_in_transaction(t,document_id=doc,module_id='domain',relationship_id='products.supplier_id').value.definition_pin
        link=CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias='product'),target=AliasObjectReference(alias='supplier'),values=(),order_key=NullOrderKey())
        context=a.group_context_in_transaction(t).value;semantic=context.input((supplier,product,link),MapValue(entries=()));request=context.request('commerce-create')
        result=self.apply(a,t,semantic,request);self.assertIsInstance(result,GroupSuccess,repr(result));identity=result.response.semantic.results[1].identity
        h.detach();c.commit();c,h,a,t=self.consumer()
        found=a.lookup_key_in_transaction(t,document_id=doc,module_id='domain',record_id='products',key_id='identity',values=(TextValue(kind='string',text='p1'),),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(found.value,ObjectFound,repr(found));self.assertEqual(found.value.object.identity.id,identity.id)
        self.assertEqual(dict(found.value.object.values)['unit_price'],TextValue(kind='decimal',text=maximum))
        query=a.query_in_transaction(t,sql='SELECT p.unit_price FROM "products" p WHERE p.unit_price=:price',document_ids=(doc,),parameters={'price':Decimal(maximum)})
        self.assertIsInstance(query.value,QueryRows,repr(query));self.assertEqual(query.value.rows,((Decimal(maximum),),))
        replay=self.apply(a,t,semantic,request);self.assertIsInstance(replay.response,CommittedReceiptReplay)
        self.assertEqual(replay.response.semantic.results[1].identity.id,identity.id);h.detach();c.commit()
        def decimals(value):
            if isinstance(value,dict):
                if value.get('kind')=='decimal':yield value['text']
                if value.get('component')=='event' and isinstance(value.get('bytesBase64'),str):
                    raw=base64.b64decode(value['bytesBase64'],validate=True)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(),value['bytesSha256']);yield from decimals(json.loads(raw))
                for v in value.values():yield from decimals(v)
            elif isinstance(value,list):
                for v in value:yield from decimals(v)
        tokens=[]
        for _ in range(6):
            c,h,a,t=self.consumer();page=a.read_feed_in_transaction(t,consumer_id='commerce').value
            self.assertIsInstance(page,FeedPage,repr(page));tokens.extend(decimals(json.loads(page.content)['changes']))
            self.assertIsInstance(a.acknowledge_feed_in_transaction(t,page),Ok);h.detach();c.commit()
            if maximum in tokens:break
        self.assertIn(maximum,tokens)
