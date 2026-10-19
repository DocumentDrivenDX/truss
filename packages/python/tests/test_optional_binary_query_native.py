# SPDX-License-Identifier: MIT OR Apache-2.0
"""Optional binary equality preserves absent/null/empty/present reads."""
from dataclasses import replace
from truss import Ok,QueryRows,QueryRefused,QueryAbsent,QueryPage,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import TextValue,NullValue
from truss.groups import AuthoredValue,GroupSuccess
import test_binary_query_native as base

class OptionalBinaryTests(base.BinaryQueryTests):
    test_write_read_literal_parameter_join_empty_and_readonly=None
    def fields(self,source):
        super().fields(source)
        module=source['modules'][0]
        next(e for e in module['elements'] if e['id']=='A')['members'].append({'module':'m','element':'A-optional'})
        module['elements'].append(dict(id='A-optional',name='optional_blob',kind='field',scalarType='binary',nullability='absent-allowed',cardinality='one',extensions={}))
    def test_absent_null_empty_present_filter_join_page_and_readonly(self):
        c,h,a,t=self.ready(self.fields)
        values=[('absent',None),('null',NullValue()),('empty',TextValue(kind='binary',text='')),('present',TextValue(kind='binary',text='AP8='))]
        operations=[]
        for label,value in values:
            operation=self.create(label,alias=label)
            properties=operation.values+(AuthoredValue(name='blob',value=TextValue(kind='binary',text='' if label=='empty' else 'AP8=')),)
            if value is not None:properties+=(AuthoredValue(name='optional_blob',value=value),)
            operations.append(replace(operation,values=properties))
        created,_,_=self.run_group(a,t,tuple(operations));self.assertIsInstance(created,GroupSuccess,repr(created))
        query=a.compiled_execution(a.compiled_selection).capability
        projected=query.query_in_transaction(t,sql='SELECT a."A-label",a.optional_blob FROM "A" a',document_ids=('adoc',));self.assertIsInstance(projected.value,QueryRows,repr(projected))
        self.assertEqual(dict(projected.value.rows),{'absent':QueryAbsent(),'null':None,'empty':TextValue(kind='binary',text=''),'present':TextValue(kind='binary',text='AP8=')})
        sql='SELECT a."A-label" FROM "A" a WHERE a.optional_blob=:blob'
        for token,label in [('AP8=','present'),('','empty')]:
            result=query.query_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'blob':TextValue(kind='binary',text=token)});self.assertIsInstance(result.value,QueryRows,repr(result));self.assertEqual(result.value.rows,((label,),))
        literal=query.query_in_transaction(t,sql='SELECT a."A-label" FROM "A" a WHERE a.optional_blob=\'AP8=\'',document_ids=('adoc',));self.assertEqual(literal.value.rows,(('present',),))
        joined=query.query_in_transaction(t,sql='SELECT a."A-label" FROM "A" a JOIN "A" b ON a.optional_blob=b.blob',document_ids=('adoc',));self.assertIsInstance(joined.value,QueryRows,repr(joined));self.assertEqual(sorted(joined.value.rows),[('empty',),('present',),('present',),('present',)])
        page=query.query_page_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'blob':TextValue(kind='binary',text='AP8=')},limit=1);self.assertIsInstance(page.value,QueryPage,repr(page));self.assertEqual(page.value.rows,(('present',),))
        from unittest.mock import patch
        from truss import _query_runtime
        old_backend=dict(_query_runtime.BACKEND,backendVersion='0.4.24')
        # Relabelling only the backend version forges a current-binding tuple.
        # This checks binding admission, not retained0.4.24/IR0.2.5 compatibility;
        # that separate oracle needs its original valid retained binding.
        with patch.object(_query_runtime,'BACKEND',old_backend):
            refused=query.query_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'blob':TextValue(kind='binary',text='AP8=')})
        self.assertIsInstance(refused.value,QueryRefused,repr(refused))
        self.assertTrue(any(d.code=='WFT-BINDING' for d in refused.value.diagnostics),repr(refused))
        h.detach();c.commit();c.execute('BEGIN READ ONLY;SET LOCAL statement_timeout=10000');h=adopt_psycopg_host(c);t=h.adopt_transaction(access_mode='read_only').value;query=create_reference_assembly(CatalogRuntimeConfiguration(),h).value.compiled_execution(a.compiled_selection).capability
        result=query.query_in_transaction(t,sql=sql,document_ids=('adoc',),parameters={'blob':TextValue(kind='binary',text='AP8=')});self.assertIsInstance(result.value,QueryRows,repr(result));self.assertEqual(result.value.rows,(('present',),));h.detach();c.rollback()
