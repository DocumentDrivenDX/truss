"""Basic public signed64/fixed-decimal workflow; no rounding or float path."""
from decimal import Decimal
import psycopg
import json
import os
from truss import Ok,ObjectFound,QueryRows,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import TextValue,MapValue
from truss.groups import AuthoredValue,CreateObject,RootlessOwnership,GroupSuccess,GroupFailed,UpdateObject,StoredObjectReference
from truss.imports import ImportReported,ImportCreated
import test_group_create_native as groups

class NumericFacetTests(groups.PublicCreateGroupTests):
    for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None

    def fields(self,source):
        module=source['modules'][0]
        for element in module['elements']:
            if element['kind']=='record':element['name']=element['id']
        record=next(e for e in module['elements'] if e['id']=='A')
        for name,family,facets in (('quantity','integer',{'integerWidth':{'bits':64,'signed':True}}),('amount','decimal',{'precision':18,'scale':4})):
            module['elements'].append({'id':name,'name':name,'kind':'field','scalarType':family,'nullability':'required','cardinality':'one','extensions':{},'facets':facets})
            record['members'].append({'module':'m','element':name})

    def values(self,label='one',quantity='9007199254740993',amount='1.2300'):
        return self.create(label=label).values+(AuthoredValue(name='quantity',value=TextValue(kind='integer',text=quantity)),AuthoredValue(name='amount',value=TextValue(kind='decimal',text=amount)))

    def test_public_accept_create_update_import_read_and_query(self):
        c,h,a,t=self.ready(self.fields)
        create=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.values(),ownership=RootlessOwnership(),alias='created')
        semantic,request=self.input(a,t,(create,));result=self.apply(a,t,semantic,request)
        self.assertIsInstance(result,GroupSuccess);identity=result.response.semantic.results[0].identity
        h.detach();c.commit();c,h,a,t=self.consumer()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        report=a.report_in_transaction(t);self.assertIsInstance(report,Ok)
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        self.assertEqual(len(json.loads(report.value.original_bytes)['runtimeFacetEnforcement']['properties']),4)
        update=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='amount',value=TextValue(kind='decimal',text='1.23000')),),unset=(),expected_version='1')
        semantic,request=self.input(a,t,(update,),action='update');request=a.group_context_in_transaction(t).value.request('update-facets')
        self.assertIsInstance(self.apply(a,t,semantic,request),GroupSuccess)
        for quantity,amount in (('9223372036854775808','1.2300'),('1','1.23001'),('1','100000000000000.0000')):
            bad=CreateObject(type_definition_pin=create.type_definition_pin,values=self.values('bad',quantity,amount),ownership=RootlessOwnership())
            context=a.group_context_in_transaction(t).value
            from truss.groups import RequestNone
            self.assertIsInstance(a.apply_in_transaction(t,context.input((bad,),MapValue(entries=())),RequestNone(),documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun')).value,GroupFailed)
        built=a.object_import_record_in_transaction(t,document_id='adoc',module_id='m',record_id='A',values=self.values('imported','-9223372036854775808','1.2'))
        self.assertIsInstance(built,Ok);context=a.import_context_in_transaction(t).value
        imported=a.import_in_transaction(t,context.input((built.value,),load_id='facets',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(imported,ImportReported);self.assertIsInstance(imported.report.outcomes[0],ImportCreated)
        h.detach();c.commit();c,h,a,t=self.consumer();h.detach();c.execute('SET TRANSACTION READ ONLY')
        h=adopt_psycopg_host(c);self.addCleanup(h.detach);a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value;t=h.adopt_transaction(access_mode='read_only').value
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(found.value,ObjectFound);self.assertEqual(dict(found.value.object.values)['amount'],TextValue(kind='decimal',text='1.23000'))
        self.assertEqual(dict(found.value.object.values)['quantity'],TextValue(kind='integer',text='9007199254740993'))
        rows=a.query_in_transaction(t,sql='SELECT a.quantity, a.amount FROM "A" a WHERE a.quantity = :q AND a.amount = :d',document_ids=('adoc',),parameters={'q':9007199254740993,'d':Decimal('1.2300')})
        self.assertIsInstance(rows,Ok,repr(rows));self.assertIsInstance(rows.value,QueryRows,repr(rows.value))
        self.assertEqual(rows.value.rows,((9007199254740993,Decimal('1.23000')),));self.assertEqual(str(rows.value.rows[0][1]),'1.23000')
        h.detach();c.rollback()

class NumericFacet08Tests(NumericFacetTests):
    def fields(self, source):
        source['umf'] = '0.8.0'
        super().fields(source)
