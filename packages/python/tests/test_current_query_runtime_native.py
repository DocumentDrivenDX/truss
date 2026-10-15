"""Basic public ordinary-person query with original UMF/Weft and private SQL."""
import os
import shutil
from typing import get_type_hints
from truss import (Ok, CurrentQueryExecutor, adopt_psycopg_host)
from truss.contracts import TextValue,BooleanValue,MapValue
from truss.groups import CreateObject,AuthoredValue,RootlessOwnership,RequestNone,GroupSuccess
from truss.query import QueryRows, QueryRefused
import test_current_query_full_sources_native as full
import test_current_query_subjects_native as subject


class CurrentQueryRuntimeNativeTests(full.CurrentQueryFullSourcesNativeTests):
    for name in tuple(n for n in dir(full.CurrentQueryFullSourcesNativeTests) if n.startswith('test_')):
        locals()[name]=None

    def create_query_graph(self, *, active=True, resources=True):
        subject.CurrentQuerySubjectsNativeTests.test_ordinary_session_observes_only_enrolled_subject_and_original_key(self)
        bun=os.environ.get('TRUSS_BUN_EXECUTABLE',shutil.which('bun') or 'bun')
        for connection,host in self.consumer_connections:
            host.detach();connection.rollback();connection.close()
        c,h,a,t=self.consumer()
        self.assertIs(get_type_hints(a.query_current_in_transaction)['executor'],CurrentQueryExecutor)
        view=a.catalog_view_in_transaction(t,a.catalog_view_request()).value.view
        types={d.reference.authored_identity:d.reference for d in view.definitions if d.reference.kind=='type'}
        inputs=[('Project',{'projectId':'p1'}),
                ('Resource',{'resourceId':'r1','salary':9007199254740993,'token':'opaque-one'}),
                ('Resource',{'resourceId':'r2','salary':9007199254740993,'token':'opaque-two'}),
                ('Ownership',{'ownerId':'o1','ownerResource':'r1','ownerProject':'p1'}),
                ('Assignment',{'assignmentId':'a1','assignmentStaff':'alice','assignmentProject':'p1','active':active})]
        if not resources:inputs=[item for item in inputs if item[0] not in ('Resource','Ownership')]
        operations=[]
        for index,(record,fields) in enumerate(inputs):
            values=tuple(AuthoredValue(name=name,value=BooleanValue(value=value) if type(value) is bool else TextValue(kind='integer' if type(value) is int else 'string',text=str(value))) for name,value in fields.items())
            operations.append(CreateObject(type_definition_pin=types[record].definition_pin,values=values,ownership=RootlessOwnership(),alias='query'+str(index)))
        context=a.group_context_in_transaction(t).value
        result=a.apply_in_transaction(t,context.input(tuple(operations),MapValue(entries=())),RequestNone(),documents=self.current_source_documents,bun_executable=bun)
        self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
        h.detach();c.commit()
        return bun

    def test_public_masked_projection_with_authorized_exact_raw_predicate(self):
        bun=self.create_query_graph()
        self.admin.execute('BEGIN');self.admin.execute('SET LOCAL search_path=public,pg_catalog')
        self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        private=CurrentQueryExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        c,h,a,t=self.consumer()
        c.execute('SET LOCAL search_path=pg_catalog,truss,pg_temp')
        result=a.query_current_in_transaction(t,executor=private,sql='SELECT r.salary FROM Resource r WHERE r.salary=:minimum',
            document_ids=('domain',),parameters={'minimum':9007199254740993},maximum_bytes=len('[private]'),maximum_scan_rows=1)
        self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(result.value,QueryRows,str(self.host._custody.last_attempt.error))
        self.assertEqual(result.value.rows,(('[private]',),))
        self.assertEqual(result.value.columns,('salary',))
        self.assertEqual(c.execute('SHOW search_path').fetchone(),('pg_catalog, truss, pg_temp',))
        self.assertEqual(self.admin.execute('SHOW search_path').fetchone(),('public, pg_catalog',))
        self.assertEqual(c.execute("SELECT has_table_privilege('truss.object','SELECT')").fetchone(),(False,))
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_class WHERE relnamespace=pg_my_temp_schema() AND relname LIKE 'truss_current_%'").fetchone(),(0,))
        self.host.detach();self.admin.rollback()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        private=CurrentQueryExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        neighboring=a.query_current_in_transaction(t,executor=private,
            sql='SELECT r.salary FROM Resource r WHERE r.salary=:minimum',document_ids=('domain',),
            parameters={'minimum':9007199254740992})
        self.assertIsInstance(neighboring,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(neighboring.value,QueryRows,str(self.host._custody.last_attempt.error))
        self.assertEqual(neighboring.value.rows,())
        self.host.detach();self.admin.rollback()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        private=CurrentQueryExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        refused=a.query_current_in_transaction(t,executor=private,
            sql='SELECT r.salary FROM Resource r ORDER BY r.salary',document_ids=('domain',))
        self.assertIsInstance(refused,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(refused.value,QueryRefused)
        self.assertEqual(refused.value.code,'unsupported_query')
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_class WHERE relnamespace=pg_my_temp_schema() AND relname LIKE 'truss_current_%'").fetchone(),(0,))
        self.host.detach();self.admin.rollback()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        private=CurrentQueryExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        limited=a.query_current_in_transaction(t,executor=private,
            sql='SELECT r.salary FROM Resource r WHERE r.salary=:minimum',document_ids=('domain',),
            parameters={'minimum':9007199254740993},maximum_bytes=1)
        self.assertIsInstance(limited,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(limited.value,QueryRefused)
        self.assertEqual(limited.value.code,'limits')
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_class WHERE relnamespace=pg_my_temp_schema() AND relname LIKE 'truss_current_%'").fetchone(),(0,))

    def assert_empty_query(self, *, active=True, resources=True):
        bun=self.create_query_graph(active=active,resources=resources)
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        private=CurrentQueryExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        c,h,a,t=self.consumer()
        result=a.query_current_in_transaction(t,executor=private,
            sql='SELECT r.salary FROM Resource r WHERE r.salary=:minimum',document_ids=('domain',),
            parameters={'minimum':9007199254740993})
        self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(result.value,QueryRows,str(self.host._custody.last_attempt.error))
        self.assertEqual(result.value.rows,())
        self.assertEqual(result.value.columns,('salary',))
        self.host.detach();self.admin.rollback()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        private=CurrentQueryExecutor(self.host,self.tx,self.current_subject_registration,bun_executable=bun)
        refused=a.query_current_in_transaction(t,executor=private,
            sql='SELECT r.salary FROM Resource r WHERE FALSE AND r.salary=:minimum ORDER BY r.salary',
            document_ids=('domain',),parameters={'minimum':9007199254740993})
        self.assertIsInstance(refused,Ok,str(self.host._custody.last_attempt.error))
        self.assertIsInstance(refused.value,QueryRefused)
        self.assertEqual(refused.value.code,'unsupported_query')
        self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_class WHERE relnamespace=pg_my_temp_schema() AND relname LIKE 'truss_current_%'").fetchone(),(0,))

    def test_all_denied_population_returns_empty_rows(self):
        self.assert_empty_query(active=False)

    def test_empty_population_returns_empty_rows(self):
        self.assert_empty_query(resources=False)
