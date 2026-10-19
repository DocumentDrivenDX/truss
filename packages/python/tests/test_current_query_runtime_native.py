# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public ordinary-person query with original UMF/Weft and private SQL."""
import os
import shutil
from typing import get_type_hints
from truss import (Ok, Error, CurrentQueryExecutor, adopt_psycopg_host, activate_current_query_protection_in_transaction)
import psycopg
import json
from truss.contracts import TextValue,BooleanValue,MapValue
from truss.groups import CreateObject,AuthoredValue,RootlessOwnership,RequestNone,GroupSuccess
from truss.query import QueryRows, QueryRefused
import test_current_query_full_sources_native as full
import test_current_query_subjects_native as subject


class CurrentQueryRuntimeNativeTests(full.CurrentQueryFullSourcesNativeTests):
    for name in tuple(n for n in dir(full.CurrentQueryFullSourcesNativeTests) if n.startswith('test_')):
        locals()[name]=None

    def create_query_graph(self, *, active=True, resources=True, exercise_activation_refusals=False):
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
        # Retain a real pre-activation binding: cached facade inputs must not
        # preserve ordinary data access after the committed lockdown.
        from truss.catalog_runtime import _release
        manifest,digest,_=_release()
        c,h,a,t=self.consumer()
        self.legacy_binding=json.loads(bytes(c.execute('SELECT truss.query_binding(%s::jsonb,%s,%s,%s,%s,%s)',
            (json.dumps(['domain']),10000,10000,16777216,manifest['releaseId'],digest)).fetchone()[0]))
        for connection,host in self.consumer_connections:
            if not connection.closed:
                host.detach();connection.rollback();connection.close()
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        if exercise_activation_refusals:
            owner=self.current_subject_registration.owner_oid
            owner_name=self.admin.execute('SELECT rolname FROM pg_roles WHERE oid=%s',(owner,)).fetchone()[0]
            from psycopg import sql as pgsql
            # A pre-existing external definer is a real alternate entry point even
            # if no ordinary role has direct SELECT on the original object table.
            self.admin.execute("CREATE FUNCTION public.preexisting_raw_resource() RETURNS jsonb LANGUAGE sql SECURITY DEFINER AS 'SELECT jsonb_agg(props) FROM truss.object'")
            self.admin.execute(pgsql.SQL('ALTER FUNCTION public.preexisting_raw_resource() OWNER TO {}').format(pgsql.Identifier(owner_name)))
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('externally delegated',str(self.host._custody.last_attempt.error))
            self.admin.execute('REVOKE ALL ON FUNCTION public.preexisting_raw_resource() FROM PUBLIC')
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('externally delegated',str(self.host._custody.last_attempt.error))
            self.admin.execute('DROP FUNCTION public.preexisting_raw_resource()')
            self.admin.execute('CREATE VIEW public.preexisting_resource_view AS SELECT props FROM truss.object')
            self.admin.execute('CREATE VIEW public.preexisting_resource_outer AS SELECT props FROM public.preexisting_resource_view')
            self.admin.execute('GRANT SELECT(props) ON public.preexisting_resource_outer TO subject_outsider')
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('externally delegated',str(self.host._custody.last_attempt.error))
            self.admin.execute('DROP VIEW public.preexisting_resource_outer')
            self.admin.execute('DROP VIEW public.preexisting_resource_view')
            self.admin.execute('ALTER ROLE subject_outsider BYPASSRLS')
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('externally delegated',str(self.host._custody.last_attempt.error))
            self.admin.execute('ALTER ROLE subject_outsider NOBYPASSRLS')
            self.admin.execute('CREATE TABLE public.preexisting_feed_carrier(xid xid8)')
            self.admin.execute('ALTER TABLE public.preexisting_feed_carrier OWNER TO subject_outsider')
            self.admin.execute("CREATE TRIGGER external_feed_capture AFTER INSERT ON public.preexisting_feed_carrier FOR EACH ROW EXECUTE FUNCTION truss.runtime_capture_feed_configuration('xid')")
            self.admin.execute('ALTER TABLE public.preexisting_feed_carrier DISABLE TRIGGER external_feed_capture')
            refused=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
            self.assertIsInstance(refused,Error)
            self.assertIn('External routine attachments',str(self.host._custody.last_attempt.error))
            self.admin.execute('DROP TABLE public.preexisting_feed_carrier')
        activated=activate_current_query_protection_in_transaction(self.host,self.tx,subject_registration=self.current_subject_registration)
        self.assertIsInstance(activated,Ok,str(self.host._custody.last_attempt.error))
        self.host.detach();self.admin.commit()
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

    def test_protected_activation_closes_legacy_data_facades(self):
        self.create_query_graph(exercise_activation_refusals=True)
        from truss.catalog_runtime import _release
        manifest,digest,_=_release()
        c,h,a,t=self.consumer()
        binding=self.legacy_binding['bindingJson']
        resource=next(r for r in self.legacy_binding['binding']['records'] if r['identity']['element']=='Resource')
        calls=[('SELECT * FROM truss.query_objects(%s::jsonb,%s)',(binding,int(resource['typeId']))),
               ('SELECT * FROM truss.query_edges(%s::jsonb,%s)',(binding,1)),
               ('SELECT * FROM truss.query_page_objects(%s::jsonb,%s,%s)',(binding,int(resource['typeId']),'pk')),
               ('SELECT * FROM truss.query_export_objects(%s::jsonb,%s)',(binding,int(resource['typeId']))),
               ('SELECT * FROM truss.query_export_edges(%s::jsonb,%s)',(binding,1)),
               ('SELECT * FROM truss.query_export_page_objects(%s::jsonb,%s,%s)',(binding,int(resource['typeId']),'pk')),
               ('SELECT truss.get_object(%s,%s,%s,%s::bigint,%s,%s,%s)',('domain','m','Resource',3,1048576,manifest['releaseId'],digest)),
               ('SELECT truss.read_history(%s::jsonb,%s,%s::bigint,%s,%s,%s,%s)',('{}',b'',1,100,1048576,manifest['releaseId'],digest)),
               ('SELECT truss.read_feed(%s,%s,%s,%s,%s)',('probe',100,1048576,manifest['releaseId'],digest))]
        for statement,parameters in calls:
            with self.subTest(statement=statement),self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with c.transaction():
                    c.execute(statement,parameters)
        result=a.get_object_in_transaction(t,document_id='domain',module_id='m',record_id='Resource',object_id=3)
        self.assertIsInstance(result,Error)
        self.assertEqual(result.error.sql_state,'42501')
        self.assertEqual(c.execute("SELECT has_table_privilege('truss.object','SELECT')").fetchone(),(False,))
        self.assertIsInstance(a.reader_catalog_in_transaction(t),Ok)

        # Supported configuration methods cannot silently restore the revoked
        # legacy grants, including replay of an existing feed registration.
        from truss import create_reference_assembly,CatalogRuntimeConfiguration,ModuleAccessGrant
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000)
        self.tx=self.host.adopt_transaction().value
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        blocked=admin_assembly.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('domain','m','subject_reader','subject_writer'),))
        self.assertIsInstance(blocked,Error)
        blocked=admin_assembly.register_feed_consumer_in_transaction(self.tx,consumer_id='protected',reader_role='subject_reader')
        self.assertIsInstance(blocked,Error)
        from truss._preparation_catalog_cut import bootstrap_preparation_catalog_cut_in_transaction
        blocked=bootstrap_preparation_catalog_cut_in_transaction(self.host,self.tx,executor_role='consumer')
        self.assertIsInstance(blocked,Error)
        self.assertIn('protection migration',str(self.host._custody.last_attempt.error))
        self.assertEqual(self.admin.execute("SELECT to_regprocedure('truss.acquire_preparation_catalog_cut()')").fetchone(),(None,))
        from truss._security_catalog_subject_installation import bootstrap_role_catalog_cut_issuer_in_transaction
        blocked=bootstrap_role_catalog_cut_issuer_in_transaction(self.host,self.tx,executor_role='consumer')
        self.assertIsInstance(blocked,Error)
        self.assertIn('protection migration',str(self.host._custody.last_attempt.error))
        self.assertEqual(self.admin.execute("SELECT to_regprocedure('truss.acquire_registered_role_catalog_cut()')").fetchone(),(None,))
        blocked=admin_assembly.upgrade_in_transaction(self.tx)
        self.assertIsInstance(blocked,Error)
        self.assertIn('protection migration',str(self.host._custody.last_attempt.error))
        self.host.detach();self.admin.rollback()
        self.assertEqual(c.execute("SELECT has_function_privilege('truss.query_objects(jsonb,integer)','EXECUTE')").fetchone(),(False,))
        from truss._current_query_sources import capture_current_query_sources_with_cursor
        from truss._current_query_protection import verify_current_query_protection
        from truss.catalog_runtime import _pin_cursor
        with self.admin.transaction():
            with self.admin.cursor() as cursor:
                _pin_cursor(cursor)
                sources=capture_current_query_sources_with_cursor(cursor)
                verify_current_query_protection(cursor,sources,self.current_subject_registration)
            for signature in ('query_export_objects(jsonb,int)','query_export_edges(jsonb,int)',
                              'query_export_page_objects(jsonb,int,text)'):
                statement=psycopg.sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO subject_reader').format(psycopg.sql.SQL(signature))
                self.admin.execute(statement)
                try:
                    with self.admin.cursor() as cursor:
                        _pin_cursor(cursor)
                        with self.assertRaisesRegex(ValueError,'closed ordinary routine grants'):
                            verify_current_query_protection(cursor,sources,self.current_subject_registration)
                finally:
                    self.admin.execute(psycopg.sql.SQL('REVOKE EXECUTE ON FUNCTION truss.{} FROM subject_reader').format(psycopg.sql.SQL(signature)))
