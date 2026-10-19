# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public exact-instant query workflow over original timestamp tokens."""
from dataclasses import replace
from truss import Ok, QueryRows, QueryRefused, adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration
from truss.contracts import TextValue, NullValue
from truss.groups import AuthoredValue, GroupSuccess
import test_object_mutations_native as base

class TimestampQueryTests(base.ObjectMutationTests):
    for _name in tuple(n for n in dir(base.ObjectMutationTests) if n.startswith('test_')): locals()[_name]=None
    source_version='0.10.0'
    def fields(self,source):
        source['umf']=self.source_version
        module=source['modules'][0]
        for element in module['elements']:
            if element['kind']=='record':element['name']=element['id']
            if element['id']=='A':element['members'].extend(({'module':'m','element':'A-at'},{'module':'m','element':'A-optional-at'}))
        module['elements'].append(dict(id='A-at',name='at',kind='field',scalarType='timestamp',nullability='required',cardinality='one',extensions={}))
        module['elements'].append(dict(id='A-optional-at',name='optional_at',kind='field',scalarType='timestamp',nullability='absent-allowed',cardinality='one',extensions={}))
    def test_original_tokens_exact_instant_equality_and_readonly(self):
        c,h,a,t=self.ready(self.fields)
        query=a.compiled_execution(a.compiled_selection).capability
        invalid=query.query_in_transaction(t,sql='SELECT a."A-label" FROM "A" a WHERE a.at=:at',document_ids=('adoc',),parameters={'at':TextValue(kind='timestamp',text='2016-12-31T23:59:60Z')})
        self.assertIsInstance(invalid.value,QueryRefused,repr(invalid))
        tokens=[('one','2024-01-01T00:00:00.1234567Z'),('two','2023-12-31T19:00:00.123456700-05:00'),
                ('three','2024-01-01T00:00:00.1234568Z'),('unknown','1970-01-01T00:00:00-00:00')]
        operations=tuple(replace(self.create(label,alias=label),values=self.create(label,alias=label).values+(AuthoredValue(name='at',value=TextValue(kind='timestamp',text=token)),)) for label,token in tokens)
        operations=tuple(replace(operation,values=operation.values+(AuthoredValue(name='optional_at',value=NullValue() if index==2 else TextValue(kind='timestamp',text=tokens[index][1])),)) if index!=1 else operation for index,operation in enumerate(operations))
        created,_,_=self.run_group(a,t,operations);self.assertIsInstance(created,GroupSuccess,repr(created))
        self.assertEqual(dict(self.read(a,t,created.response.semantic.results[1].identity).object.values)['at'],TextValue(kind='timestamp',text=tokens[1][1]))
        query=a.compiled_execution(a.compiled_selection).capability
        def check(sql,parameters,rows,tx=t):
            result=query.query_in_transaction(tx,sql=sql,document_ids=('adoc',),parameters=parameters)
            self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,QueryRows,repr(result));self.assertEqual(sorted(result.value.rows),sorted(rows))
        sql='SELECT a."A-label" FROM "A" a WHERE a.at=:at'
        check(sql,{'at':TextValue(kind='timestamp',text=tokens[0][1])},(('one',),('two',)))
        check(sql,{'at':TextValue(kind='timestamp',text=tokens[2][1])},(('three',),))
        check(sql,{'at':TextValue(kind='timestamp',text='1970-01-01T00:00:00Z')},(('unknown',),))
        check('SELECT a."A-label" FROM "A" a WHERE a.optional_at=:at',{'at':TextValue(kind='timestamp',text=tokens[0][1])},(('one',),))
        check('SELECT a."A-label" FROM "A" a WHERE a.at=\'2024-01-01T00:00:00.1234567000Z\'',{},(('one',),('two',)))
        check('SELECT a."A-label" FROM "A" a JOIN "A" b ON a.at=b.at',{},(('one',),('one',),('two',),('two',),('three',),('unknown',)))
        page=query.query_page_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'at':TextValue(kind='timestamp',text=tokens[0][1])},limit=1)
        from truss import QueryPage
        self.assertIsInstance(page.value,QueryPage,repr(page));self.assertEqual(page.value.rows,(('one',),))
        for token in ['2016-12-31T23:59:60Z','2024-02-30T00:00:00Z','2024-01-01T00:00:00Z\n']:
            result=query.query_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'at':TextValue(kind='timestamp',text=token)})
            self.assertIsInstance(result.value,QueryRefused,repr(result))
        h.detach();c.commit();c.execute('BEGIN READ ONLY;SET LOCAL statement_timeout=10000')
        h=adopt_psycopg_host(c);t=h.adopt_transaction(access_mode='read_only').value
        query=create_reference_assembly(CatalogRuntimeConfiguration(),h).value.compiled_execution(a.compiled_selection).capability
        check(sql,{'at':TextValue(kind='timestamp',text=tokens[0][1])},(('one',),('two',)),tx=t)
        h.detach();c.rollback()
