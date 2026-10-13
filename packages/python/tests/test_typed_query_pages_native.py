"""Basic exact composite business-key SQL page workflow."""
import json
from decimal import Decimal
from truss import Ok,QueryPage,QueryRefused,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly
from truss.contracts import MapValue,TextValue,BooleanValue
from truss.groups import CreateObject,AuthoredValue,RootlessOwnership,GroupSuccess
import test_group_create_native as create_tests

class TypedQueryPagesTests(create_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(create_tests.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.7.0'
    def fields(self,source):
        source['umf']=self.source_version;m=source['modules'][0]
        for e in m['elements']:
            if e['kind']=='record':e['name']=e['id']
            elif e['id']=='A-value':e['scalarType']='integer';e['facets']={'integerWidth':{'bits':64,'signed':True}}
        a=next(e for e in m['elements'] if e['id']=='A')
        for name,family,facets in [('A-amount','decimal',{'precision':18,'scale':4}),('A-active','boolean',{})]:
            m['elements'].append({'id':name,'name':name,'kind':'field','scalarType':family,'facets':facets,'cardinality':'one','nullability':'required','extensions':{}})
            a['members'].append({'module':'m','element':name})
        a['keys']=[{'id':'a-primary','name':'primary','primary':True,'fields':[{'module':'m','element':name} for name in ('A-value','A-amount','A-active')]}]
    def test_exact_pages_and_readonly_continuation(self):
        c,h,a,t=self.ready(self.fields)
        values=[('9007199254740993','1.23000',False),('-9007199254740993','1.2000',True),('0','1.2',False),('0','1.2100',False),('0','1.21000',True)]
        operations=tuple(CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text=str(i))),AuthoredValue(name='A-value',value=TextValue(kind='integer',text=integer)),AuthoredValue(name='A-amount',value=TextValue(kind='decimal',text=decimal)),AuthoredValue(name='A-active',value=BooleanValue(value=active))),ownership=RootlessOwnership(),alias='a'+str(i)) for i,(integer,decimal,active) in enumerate(values))
        context=a.group_context_in_transaction(t).value;created=self.apply(a,t,context.input(operations,MapValue(entries=())),context.request('typed-pages'));self.assertIsInstance(created,GroupSuccess)
        h.detach();c.commit();c,h,a,t=self.consumer();h.detach();c.execute('SET TRANSACTION READ ONLY')
        h=adopt_psycopg_host(c);self.addCleanup(h.detach);a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value;t=h.adopt_transaction(access_mode='read_only').value
        sql='SELECT a."A-value",a."A-amount",a."A-active" FROM "A" a'
        def page(cursor=None):
            result=a.query_page_in_transaction(t,sql=sql,document_ids=('adoc',),limit=2,cursor=cursor)
            self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,QueryPage,repr(result.value));return result.value
        first=page();self.assertEqual(first.rows,((-9007199254740993,Decimal('1.2000'),True),(0,Decimal('1.2'),False)))
        token=json.loads(first.next_cursor.original_bytes);self.assertEqual(token['profile'],'truss-query-page/0.2');self.assertEqual(token['after'],['0','1.2','false'])
        second=page(first.next_cursor);self.assertEqual(second.rows,((0,Decimal('1.2100'),False),(0,Decimal('1.21000'),True)))
        third=page(second.next_cursor);self.assertEqual(third.rows,((9007199254740993,Decimal('1.23000'),False),));self.assertIsNone(third.next_cursor)
        self.assertEqual(str(second.rows[1][1]),'1.21000');self.assertEqual(str(third.rows[0][1]),'1.23000')
        legacy=a.query_in_transaction(t,sql=sql+' ORDER BY a."A-value",a."A-amount",a."A-active" LIMIT 2',document_ids=('adoc',),read_profile='entity-page')
        self.assertIsInstance(legacy.value,QueryRefused)
        h.detach();c.rollback()

class TypedQueryPages08Tests(TypedQueryPagesTests):
    source_version='0.8.0'

class StringQueryPagesTests(create_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(create_tests.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    def test_existing_string_primary_key_page_facade(self):
        def names(source):
            for e in source['modules'][0]['elements']:
                if e['kind']=='record':e['name']=e['id']
        c,h,a,t=self.ready(names);context=a.group_context_in_transaction(t).value
        result=self.apply(a,t,context.input((self.create('beta',alias='beta'),self.create('alpha',alias='alpha')),MapValue(entries=())),context.request('string-pages'));self.assertIsInstance(result,GroupSuccess)
        first=a.query_page_in_transaction(t,sql='SELECT a."A-label" FROM "A" a',document_ids=('adoc',),limit=1).value
        self.assertIsInstance(first,QueryPage,repr(first));self.assertEqual(first.rows,(('alpha',),))
        second=a.query_page_in_transaction(t,sql='SELECT a."A-label" FROM "A" a',document_ids=('adoc',),limit=1,cursor=first.next_cursor).value
        self.assertIsInstance(second,QueryPage,repr(second));self.assertEqual(second.rows,(('beta',),));self.assertIsNone(second.next_cursor)
        h.detach();c.rollback()
