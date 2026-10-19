# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic new date/generic decimal values, keys, import and rollback workflow."""
import os
from truss import Ok,ObjectFound
from truss.contracts import TextValue,MapValue
from truss.groups import AuthoredValue,CreateObject,RootlessOwnership,GroupSuccess,GroupFailed,UpdateObject,StoredObjectReference,RequestNone
from truss.imports import ImportReported,ImportCreated
from test_numeric_facets_native import NumericFacetTests

class DateDecimalTests(NumericFacetTests):
    for name in tuple(n for n in dir(NumericFacetTests) if n.startswith('test_')):locals()[name]=None

    def fields(self,source):
        super().fields(source);source['umf']='0.10.0'
        module=source['modules'][0];record=next(e for e in module['elements'] if e['id']=='A')
        next(e for e in module['elements'] if e['id']=='amount')['facets']={'precision':14.0,'scale':2.0}
        module['elements'].append({'id':'day','name':'day','kind':'field','scalarType':'date','nullability':'required','cardinality':'one','extensions':{}})
        record['members'].append({'module':'m','element':'day'})
        record['keys'].append({'id':'amount-key','name':'Amount','fields':[{'module':'m','element':'amount'}]})

    def date_values(self,label='one',amount='999999999999.99',day='2000-02-29'):
        return self.values(label=label,amount=amount)+(AuthoredValue(name='day',value=TextValue(kind='date',text=day)),)

    def test_public_values_keys_import_commit_reopen(self):
        c,h,a,t=self.ready(self.fields)
        op=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.date_values(),ownership=RootlessOwnership())
        semantic,request=self.input(a,t,(op,));created=self.apply(a,t,semantic,request)
        self.assertIsInstance(created,GroupSuccess,repr(created));identity=created.response.semantic.results[0].identity
        h.detach();c.commit();c,h,a,t=self.consumer()
        update=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='amount',value=TextValue(kind='decimal',text='1.2300')),AuthoredValue(name='day',value=TextValue(kind='date',text='2024-02-29'))),unset=())
        context=a.group_context_in_transaction(t).value
        changed=a.apply_in_transaction(t,context.input((update,),MapValue(entries=())),RequestNone(),documents=self.documents)
        self.assertIsInstance(changed,Ok,repr(changed));self.assertIsInstance(changed.value,GroupSuccess,repr(changed.value))
        for name,kind,text in (('day','date','2024-02-30'),('amount','decimal','1.234')):
            bad=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name=name,value=TextValue(kind=kind,text=text)),),unset=())
            refused=a.apply_in_transaction(t,context.input((bad,),MapValue(entries=())),RequestNone(),documents=self.documents)
            self.assertIsInstance(refused,Ok,repr(refused));self.assertIsInstance(refused.value,GroupFailed,repr(refused.value))
        built=a.object_import_record_in_transaction(t,document_id='adoc',module_id='m',record_id='A',values=self.date_values(label='imported',amount='2.34',day='2025-01-01'))
        self.assertIsInstance(built,Ok,repr(built));imports=a.import_context_in_transaction(t).value
        imported=a.import_in_transaction(t,imports.input((built.value,),load_id='date-import',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(imported,ImportReported,repr(imported));self.assertIsInstance(imported.report.outcomes[0],ImportCreated)
        h.detach();c.commit();c,h,a,t=self.consumer()
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(found.value,ObjectFound,repr(found));values=dict(found.value.object.values)
        self.assertEqual(values['day'],TextValue(kind='date',text='2024-02-29'))
        self.assertEqual(values['amount'],TextValue(kind='decimal',text='1.2300'))
        key=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='amount-key',values=(TextValue(kind='decimal',text='1.23'),))
        self.assertIsInstance(key,Ok,repr(key));self.assertIsInstance(key.value,ObjectFound,repr(key.value))
        self.assertEqual(key.value.object.identity.id,identity.id)
        h.detach();c.rollback()

class LargeScaleDecimalTests(DateDecimalTests):
    test_public_values_keys_import_commit_reopen=None

    def fields(self,source):
        super().fields(source)
        next(e for e in source['modules'][0]['elements'] if e['id']=='amount')['facets']={'precision':10000001,'scale':10000000}

    def test_short_exact_value_at_large_declared_scale(self):
        c,h,a,t=self.ready(self.fields)
        op=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.date_values(amount='1e-10000000'),ownership=RootlessOwnership())
        semantic,request=self.input(a,t,(op,));created=self.apply(a,t,semantic,request)
        self.assertIsInstance(created,GroupSuccess,repr(created));identity=created.response.semantic.results[0].identity
        h.detach();c.commit();c,h,a,t=self.consumer()
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(found.value,ObjectFound,repr(found))
        self.assertEqual(dict(found.value.object.values)['amount'],TextValue(kind='decimal',text='1e-10000000'))
        key=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='amount-key',values=(TextValue(kind='decimal',text='1e-10000000'),))
        self.assertIsInstance(key,Ok,repr(key));self.assertIsInstance(key.value,ObjectFound,repr(key.value))
        self.assertEqual(key.value.object.identity.id,identity.id)
        h.detach();c.rollback()


class DateQueryTests(DateDecimalTests):
    test_public_values_keys_import_commit_reopen = None

    def fields(self, source):
        super().fields(source)
        module = source['modules'][0]
        next(e for e in module['elements'] if e['id'] == 'amount')['facets'] = {'precision':18,'scale':4}
        next(e for e in module['elements'] if e['id'] == 'day')['nullability'] = 'absent-allowed'

    def test_public_date_queries_and_pages(self):
        from truss import QueryRows, QueryPage
        from truss.contracts import NullValue
        from truss.query import QueryAbsent, QueryRefused
        c,h,a,t = self.ready(self.fields)
        operations = tuple(CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,
            values=self.date_values(label=label,amount=amount)[:-1]+extra,ownership=RootlessOwnership())
            for label,amount,extra in (
                ('dated','1.0',(AuthoredValue(name='day',value=TextValue(kind='date',text='2000-02-29')),)),
                ('absent','2.0',()),
                ('null','3.0',(AuthoredValue(name='day',value=NullValue()),))))
        semantic,request = self.input(a,t,operations)
        self.assertIsInstance(self.apply(a,t,semantic,request),GroupSuccess)
        h.detach();c.commit();c,h,a,t = self.consumer()
        for sql,parameters in (
            ('SELECT a.day FROM A a WHERE a.day=\'2000-02-29\'',{}),
            ('SELECT a.day FROM A a WHERE a.day=:day',{'day':TextValue(kind='date',text='2000-02-29')}),
            ('SELECT a.day FROM A a INNER JOIN A b ON a.day=b.day',{})):
            rows = a.query_in_transaction(t,sql=sql,document_ids=('adoc',),parameters=parameters)
            self.assertIsInstance(rows,Ok,repr(rows));self.assertIsInstance(rows.value,QueryRows,repr(rows.value))
            self.assertEqual(rows.value.rows,((TextValue(kind='date',text='2000-02-29'),),))
        rows = a.query_in_transaction(t,sql='SELECT a.day FROM A a ORDER BY a."A-label"',document_ids=('adoc',))
        self.assertIsInstance(rows.value,QueryRows,repr(rows))
        self.assertEqual(rows.value.rows,((QueryAbsent(),),(TextValue(kind='date',text='2000-02-29'),),(None,)))
        page = a.query_page_in_transaction(t,sql='SELECT a.day FROM A a',document_ids=('adoc',),limit=1)
        self.assertIsInstance(page,Ok,repr(page));self.assertIsInstance(page.value,QueryPage,repr(page.value))
        all_rows = list(page.value.rows)
        while page.value.next_cursor is not None:
            page = a.query_page_in_transaction(t,sql='SELECT a.day FROM A a',document_ids=('adoc',),limit=1,cursor=page.value.next_cursor)
            self.assertIsInstance(page.value,QueryPage,repr(page));all_rows.extend(page.value.rows)
        self.assertCountEqual(all_rows,rows.value.rows)
        for token in ('1900-02-29','0000-01-01','2024-2-01'):
            refused=a.query_in_transaction(t,sql='SELECT a.day FROM A a WHERE a.day=:day',document_ids=('adoc',),parameters={'day':TextValue(kind='date',text=token)})
            self.assertIsInstance(refused.value,QueryRefused,repr(refused))
        h.detach();c.rollback()
