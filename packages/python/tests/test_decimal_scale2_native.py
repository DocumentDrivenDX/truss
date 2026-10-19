# SPDX-License-Identifier: MIT OR Apache-2.0
"""Declared decimal18,2 through public catalog, mutation, key, query and feed APIs."""
import json,os,base64
from decimal import Decimal
from dataclasses import replace
from hashlib import sha256
from truss import Ok,ObjectFound,QueryRows,QueryPage,FeedPage,ModuleAccessGrant,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import TextValue,MapValue
from truss.groups import CreateObject,RootlessOwnership,GroupSuccess,GroupFailed,UpdateObject,StoredObjectReference,RequestNone,CommittedReceiptReplay
from truss.imports import ImportReported,ImportCreated
import test_numeric_facets_native as base

class DecimalScale2Tests(base.NumericFacetTests):
    test_public_accept_create_update_import_read_and_query=None
    def fields(self,source):
        super().fields(source)
        module=source['modules'][0]
        next(e for e in module['elements'] if e['id']=='amount')['facets']={'precision':18,'scale':2}
        record=next(e for e in module['elements'] if e['id']=='A')
        next(k for k in record['keys'] if k.get('primary'))['fields'].append({'module':'m','element':'amount'})
    def test_exact_original_source_maximum_write_import_key_query_replay_and_feed(self):
        bun=os.environ.get('TRUSS_BUN_EXECUTABLE','bun');maximum='9999999999999999.99'
        c,h,a,t=self.ready(self.fields)
        original=next(d for d in self.documents if d.document_id=='adoc')
        accepted=a.accepted_document_in_transaction(t,document_id='adoc');self.assertIsInstance(accepted,Ok,repr(accepted));self.assertEqual(accepted.value.content,original.content);self.assertEqual(accepted.value.sha256,sha256(original.content).hexdigest());self.assertEqual(accepted.value.document_revision,'r1')
        create=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.values(amount=maximum),ownership=RootlessOwnership(),alias='created')
        semantic,request=self.input(a,t,(create,));created=self.apply(a,t,semantic,request);self.assertIsInstance(created,GroupSuccess,repr(created));identity=created.response.semantic.results[0].identity
        self.assertEqual(dict(a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value.object.values)['amount'],TextValue(kind='decimal',text=maximum))
        lookup=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('value','one',TextValue(kind='decimal',text=maximum)),bun_executable=bun);self.assertIsInstance(lookup.value,ObjectFound,repr(lookup));self.assertEqual(lookup.value.object.id,int(identity.id))
        for token in ('10000000000000000.00','0.001'):
            invalid=replace(create,alias='invalid',values=self.values('invalid',amount=token));context=a.group_context_in_transaction(t).value
            refused=a.apply_in_transaction(t,context.input((invalid,),MapValue(entries=())),RequestNone(),documents=self.documents,bun_executable=bun);self.assertIsInstance(refused.value,GroupFailed,repr(refused))
        h.detach();c.commit();c,h,a,t=self.consumer()
        replay=self.apply(a,t,semantic,request);self.assertIsInstance(replay.response,CommittedReceiptReplay);self.assertEqual(replay.response.semantic.results[0].identity,identity)
        update=UpdateObject(target=StoredObjectReference(identity=identity),set=(base.AuthoredValue(name='amount',value=TextValue(kind='decimal',text=maximum+'00')),),unset=(),expected_version='1')
        context=a.group_context_in_transaction(t).value;changed=a.apply_in_transaction(t,context.input((update,),MapValue(entries=())),context.request('decimal2-update'),documents=self.documents,bun_executable=bun);self.assertIsInstance(changed.value,GroupSuccess,repr(changed))
        built=a.object_import_record_in_transaction(t,document_id='adoc',module_id='m',record_id='A',values=self.values('imported',amount='1.20'));self.assertIsInstance(built,Ok,repr(built));context=a.import_context_in_transaction(t).value
        imported=a.import_in_transaction(t,context.input((built.value,),load_id='decimal2-load',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=bun);self.assertIsInstance(imported,ImportReported,repr(imported));self.assertIsInstance(imported.report.outcomes[0],ImportCreated)
        h.detach();c.commit();c,h,a,t=self.consumer()
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id));self.assertEqual(dict(found.value.object.values)['amount'],TextValue(kind='decimal',text=maximum+'00'))
        sql='SELECT a.amount FROM "A" a WHERE a.amount=:amount'
        result=a.query_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'amount':Decimal(maximum)});self.assertIsInstance(result.value,QueryRows,repr(result));self.assertEqual(result.value.rows,((Decimal(maximum+'00'),),));self.assertEqual(str(result.value.rows[0][0]),maximum+'00')
        page=a.query_page_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'amount':Decimal(maximum)},limit=1);self.assertIsInstance(page.value,QueryPage,repr(page));self.assertEqual(page.value.rows,((Decimal(maximum+'00'),),))
        h.detach();c.rollback()
        self.admin.execute('BEGIN');ah=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);aa=create_reference_assembly(CatalogRuntimeConfiguration(),ah).value;at=ah.adopt_transaction().value
        self.assertIsInstance(aa.configure_module_access_in_transaction(at,(ModuleAccessGrant('zdoc','m','group_reader','group_writer'),)),Ok)
        self.assertIsInstance(aa.register_feed_consumer_in_transaction(at,consumer_id='decimal2',reader_role='group_reader'),Ok);ah.detach();self.admin.commit();self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        def cells(value):
            if isinstance(value,dict):
                if value.get('kind')=='decimal':yield value['text']
                if value.get('component')=='event' and type(value.get('bytesBase64')) is str:
                    original_event=base64.b64decode(value['bytesBase64'],validate=True)
                    self.assertEqual(sha256(original_event).hexdigest(),value['bytesSha256'])
                    yield from cells(json.loads(original_event))
                for v in value.values():yield from cells(v)
            elif isinstance(value,list):
                for v in value:yield from cells(v)
            elif isinstance(value,str):
                yield value
        tokens=[]
        for _ in range(8):
            c,h,a,t=self.consumer();feed=a.read_feed_in_transaction(t,consumer_id='decimal2');self.assertIsInstance(feed.value,FeedPage,repr(feed));tokens.extend(cells(json.loads(feed.value.content)['changes']))
            self.assertIsInstance(a.acknowledge_feed_in_transaction(t,feed.value),Ok);h.detach();c.commit()
            if maximum in tokens and maximum+'00' in tokens and '1.20' in tokens:break
        self.assertIn(maximum,tokens,repr(json.loads(feed.value.content))[:1800]);self.assertIn(maximum+'00',tokens);self.assertIn('1.20',tokens)

class DecimalScale208Tests(DecimalScale2Tests):
    def fields(self,source):
        source['umf']='0.8.0';super().fields(source)
