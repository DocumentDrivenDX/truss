"""Basic real-data non-key numeric refinement acceptance/refusal workflow."""
import json,os
from decimal import Decimal
from truss import CatalogDocument,CatalogAcceptanceRefused,CatalogRegistration,ObjectFound,Ok,QueryRows
from truss.contracts import TextValue
from truss.groups import AuthoredValue,CreateObject,RootlessOwnership,UpdateObject,StoredObjectReference,GroupSuccess,CommittedReceiptReplay
import test_group_create_native as create_tests

class FacetEvolutionTests(create_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(create_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None
    source_version='0.7.0'
    def fields(self,source):
        source['umf']=self.source_version
        module=source['modules'][0];record=next(v for v in module['elements'] if v['id']=='A');record['name']='A'
        for name,family in (('quantity','integer'),('amount','decimal')):
            module['elements'].append({'id':name,'name':name,'kind':'field','scalarType':family,'nullability':'required','cardinality':'one','extensions':{}})
            record['members'].append({'module':'m','element':name})
    def values(self,label,quantity,amount):
        return self.create(label=label,value=label).values+(AuthoredValue(name='quantity',value=TextValue(kind='integer',text=quantity)),AuthoredValue(name='amount',value=TextValue(kind='decimal',text=amount)))
    def test_nonkey_refinement_counts_acceptance_and_widening(self):
        connection,host,assembly,tx=self.ready(self.fields)
        operations=tuple(CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.values(label,q,d),ownership=RootlessOwnership(),alias=label) for label,q,d in (('valid','9007199254740993','1.23000'),('invalid','9223372036854775808','1.23001')))
        input,request=self.input(assembly,tx,operations);created=self.apply(assembly,tx,input,request);self.assertIsInstance(created,GroupSuccess)
        original_input,original_request=input,request
        valid,invalid=(r.identity for r in created.response.semantic.results);host.detach();connection.commit()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE')
        connection,host,assembly,tx=self.consumer()
        original_report=assembly.report_in_transaction(tx).value.original_bytes
        original=json.loads(next(d.content for d in self.documents if d.document_id=='adoc'))
        narrowed=json.loads(json.dumps(original))
        for field in narrowed['modules'][0]['elements']:
            if field['id']=='quantity':field['facets']={'integerWidth':{'bits':64,'signed':True}}
            if field['id']=='amount':field['facets']={'precision':18,'scale':4}
        prepared=assembly.prepare_catalog((CatalogDocument('adoc','r2',json.dumps(narrowed).encode()),),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        before=self.admin.execute('SELECT rev FROM truss.schema_head').fetchone()[0]
        refused=assembly.accept_in_transaction(tx,prepared,request_key='narrow-refused')
        self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,CatalogAcceptanceRefused)
        self.assertEqual({(v.field_id,v.rule,v.affected_object_count) for v in refused.value.violations},{('quantity','property.facets',1),('amount','property.facets',1)})
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone()[0],before)
        fix=UpdateObject(target=StoredObjectReference(identity=invalid),set=(AuthoredValue(name='quantity',value=TextValue(kind='integer',text='-9223372036854775808')),AuthoredValue(name='amount',value=TextValue(kind='decimal',text='1.2300'))),unset=(),expected_version='1')
        semantic,request=self.input(assembly,tx,(fix,));request=assembly.group_context_in_transaction(tx).value.request('fix-before-narrow')
        self.assertIsInstance(self.apply(assembly,tx,semantic,request),GroupSuccess)
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='narrow-valid')
        self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        self.assertEqual(assembly.report_in_transaction(tx,revision=1).value.original_bytes,original_report)
        replay=self.apply(assembly,tx,original_input,original_request)
        self.assertIsInstance(replay.response,CommittedReceiptReplay)
        found=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(valid.id)).value
        self.assertIsInstance(found,ObjectFound);self.assertEqual(found.object.identity,valid);self.assertEqual(found.object.version,1);self.assertEqual(found.object.record_revision,before)
        self.assertEqual(dict(found.object.values)['amount'],TextValue(kind='decimal',text='1.23000'))
        rows=assembly.query_in_transaction(tx,sql='SELECT a.quantity, a.amount FROM "A" a WHERE a.quantity = :q',document_ids=('adoc',),parameters={'q':9007199254740993})
        self.assertIsInstance(rows,Ok,repr(rows));self.assertIsInstance(rows.value,QueryRows,repr(rows.value));self.assertEqual(rows.value.rows,((9007199254740993,Decimal('1.23000')),))
        widened=assembly.prepare_catalog((CatalogDocument('adoc','r3',json.dumps(original).encode()),),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        accepted=assembly.accept_in_transaction(tx,widened,request_key='widen')
        self.assertIsInstance(accepted.value,CatalogRegistration)
        self.assertTrue(assembly.accept_in_transaction(tx,widened,request_key='widen').value.replayed)
        host.detach();connection.commit()

class FacetEvolution08Tests(FacetEvolutionTests):
    source_version='0.8.0'
