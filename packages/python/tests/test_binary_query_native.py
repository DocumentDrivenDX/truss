# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public binary writes, reads and Weft byte equality."""
from dataclasses import replace
from truss import Ok,QueryRows,QueryRefused,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import TextValue
from truss.groups import AuthoredValue,GroupSuccess
import test_object_mutations_native as base

class BinaryQueryTests(base.ObjectMutationTests):
    for _name in tuple(n for n in dir(base.ObjectMutationTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.10.0'
    def fields(self,source):
        source['umf']=self.source_version
        module=source['modules'][0]
        for element in module['elements']:
            if element['kind']=='record':element['name']=element['id']
            if element['id']=='A':element['members'].append({'module':'m','element':'A-blob'})
        module['elements'].append(dict(id='A-blob',name='blob',kind='field',scalarType='binary',nullability='required',cardinality='one',extensions={}))
    def test_write_read_literal_parameter_join_empty_and_readonly(self):
        c,h,a,t=self.ready(self.fields)
        operations=tuple(replace(self.create(label,alias=label),values=self.create(label,alias=label).values+(AuthoredValue(name='blob',value=TextValue(kind='binary',text=token)),)) for label,token in [('one','AP8='),('two',''),('three','AQ==')])
        created,_,_=self.run_group(a,t,operations);self.assertIsInstance(created,GroupSuccess,repr(created))
        self.assertEqual(dict(self.read(a,t,created.response.semantic.results[0].identity).object.values)['blob'],TextValue(kind='binary',text='AP8='))
        query=a.compiled_execution(a.compiled_selection).capability
        def check(sql,parameters,rows,tx=t):
            result=query.query_in_transaction(tx,sql=sql,document_ids=('adoc',),parameters=parameters)
            self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,QueryRows,repr(result.value));self.assertEqual(sorted(result.value.rows),sorted(rows))
        sql='SELECT a."A-label" FROM "A" a WHERE a.blob=:blob'
        check(sql,{'blob':TextValue(kind='binary',text='AP8=')},(('one',),))
        check(sql,{'blob':TextValue(kind='binary',text='')},(('two',),))
        check(sql,{'blob':TextValue(kind='binary',text='Ag==')},())
        page=query.query_page_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'blob':TextValue(kind='binary',text='AP8=')},limit=1)
        from truss import QueryPage
        self.assertIsInstance(page.value,QueryPage,repr(page));self.assertEqual(page.value.rows,(('one',),))
        check('SELECT a."A-label" FROM "A" a WHERE a.blob=\'AP8=\'',{},(('one',),))
        check('SELECT a."A-label" FROM "A" a JOIN "A" b ON a.blob=b.blob',{},(('one',),('two',),('three',)))
        for value in ['AP8=',TextValue(kind='binary',text='AP9='),TextValue(kind='timestamp',text='2024-01-01T00:00:00Z')]:
            result=query.query_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'blob':value});self.assertIsInstance(result.value,QueryRefused,repr(result))
        h.detach();c.commit();c.execute('BEGIN READ ONLY;SET LOCAL statement_timeout=10000');h=adopt_psycopg_host(c);t=h.adopt_transaction(access_mode='read_only').value;query=create_reference_assembly(CatalogRuntimeConfiguration(),h).value.compiled_execution(a.compiled_selection).capability
        check(sql,{'blob':TextValue(kind='binary',text='AP8=')},(('one',),),tx=t);h.detach();c.rollback()
