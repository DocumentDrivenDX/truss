# SPDX-License-Identifier: MIT OR Apache-2.0
"""HF-04 compiler-owned result metadata across empty, null and page results."""
from dataclasses import replace
from truss import Error, Ok, QueryRows, QueryPage
from truss.contracts import NullValue
from truss.groups import AuthoredValue, GroupSuccess
import test_compiled_query_native as fixtures


class QueryDescriptorTests(fixtures.CompiledQueryTests):
    for _name in tuple(n for n in dir(fixtures.CompiledQueryTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_damaged_query_binding_grant_remains_execution_error(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        c.execute("CREATE TEMP TABLE prior_query_work(value text);INSERT INTO prior_query_work VALUES('kept')")
        self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.query_binding_if_changed(jsonb,integer,integer,integer,text,text,text) FROM group_writer')
        result=a.query_in_transaction(t,sql='SELECT COUNT(*) FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(result,Error,repr(result));self.assertEqual(result.error.sql_state,'42501')
        self.assertEqual(c.execute('TABLE prior_query_work').fetchall(),[('kept',)])

    def test_empty_and_aggregate_types_come_from_compiler_without_sample_rows(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        empty=a.query_in_transaction(t,sql='SELECT a."A-label" AS label FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(empty,Ok,repr(empty));self.assertIsInstance(empty.value,QueryRows)
        self.assertEqual(empty.value.rows,())
        column=empty.value.column_descriptors[0]
        self.assertEqual((column.position,column.output_name,column.logical_type['family'],column.sql_nullable),(1,'label','string',False))
        counted=a.query_in_transaction(t,sql='SELECT COUNT(*) AS total FROM "A" a',document_ids=('adoc',))
        self.assertEqual(counted.value.rows,((0,),))
        descriptor=counted.value.column_descriptors[0]
        self.assertEqual(descriptor.logical_type,{'family':'integer','facets':{},'nullable':False})
        self.assertEqual(descriptor.output_name,'total')
        with self.assertRaises(TypeError):column.representation['kind']='invented'

    def test_all_null_projection_retains_availability_and_native_envelope_metadata(self):
        def optional(source):
            module=source['modules'][0];record=next(e for e in module['elements'] if e['id']=='A')
            record['members'].append({'module':'m','element':'A-note'})
            module['elements'].append({'id':'A-note','name':'note','kind':'field','scalarType':'string',
                'nullability':'absent-allowed','cardinality':'one','extensions':{}})
        c,h,a,t=self.ready(optional,document_ids=('adoc',))
        op=self.create();op=replace(op,values=op.values+(AuthoredValue(name='note',value=NullValue()),))
        self.assertIsInstance(self.run_group(a,t,(op,))[0],GroupSuccess)
        result=a.query_in_transaction(t,sql='SELECT a.note AS only_null FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(result.value,QueryRows,repr(result));self.assertEqual(result.value.rows,((None,),))
        descriptor=result.value.column_descriptors[0]
        self.assertEqual(descriptor.output_name,'only_null')
        self.assertEqual(descriptor.logical_type['family'],'string')
        self.assertEqual(descriptor.value_descriptor['availability'],'absent-allowed')
        self.assertTrue(descriptor.representation['nativeNull'])
        self.assertFalse(descriptor.sql_nullable)

    def test_page_descriptors_exclude_compiler_hidden_sort_outputs(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        created,_,_=self.run_group(a,t,(self.create(label='a',alias='a'),self.create(label='b',alias='b')))
        self.assertIsInstance(created,GroupSuccess)
        page=a.query_page_in_transaction(t,sql='SELECT a."A-label" AS label FROM "A" a',document_ids=('adoc',),limit=1)
        self.assertIsInstance(page.value,QueryPage,repr(page));self.assertIsNotNone(page.value.next_cursor)
        self.assertEqual(page.value.columns,('label',));self.assertEqual(len(page.value.column_descriptors),1)
        self.assertEqual(page.value.column_descriptors[0].output_name,'label')
        tail=a.query_page_in_transaction(t,sql='SELECT a."A-label" AS label FROM "A" a',document_ids=('adoc',),limit=1,cursor=page.value.next_cursor)
        self.assertEqual(tail.value.column_descriptors,page.value.column_descriptors)
        self.assertIsNone(tail.value.next_cursor)
