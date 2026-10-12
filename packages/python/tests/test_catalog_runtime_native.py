"""Public catalog workflow on PostgreSQL: no private staging or fabricated IDs."""
import json
from pathlib import Path
import tempfile
import unittest
import psycopg
from truss import (LocalPostgres,Ok,Error,adopt_psycopg_host,
                   create_reference_assembly,CatalogRuntimeConfiguration,CatalogDocument)
from test_catalog_relational_support import relational_document

class PublicCatalogRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(tempfile.mkdtemp(prefix='truss-public-catalog-',dir='/private/tmp'))
        cls.runtime=LocalPostgres(cls.root/'data')
        cls.addClassCleanup(cls.cleanup)
        cls.runtime.__enter__();cls.info=cls.runtime.info
    @classmethod
    def cleanup(cls):
        cls.runtime.__exit__(None,None,None)
        import shutil
        shutil.rmtree(cls.root)
    def setUp(self):
        self.consumer_connections=[]
        self.admin=psycopg.connect(**psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),autocommit=True,options='-c statement_timeout=10000')
        self.addCleanup(self.admin.close)
        self.admin.execute('CREATE ROLE consumer LOGIN')
        self.admin.execute('BEGIN')
        self.host=adopt_psycopg_host(self.admin)
        self.addCleanup(self.host.detach)
        self.tx=self.host.adopt_transaction().value
        result=create_reference_assembly(CatalogRuntimeConfiguration(),self.host)
        self.assertIsInstance(result,Ok)
        self.assembly=result.value
    def tearDown(self):
        for connection,host in self.consumer_connections:
            host.detach();connection.rollback();connection.close()
        self.host.detach();self.admin.rollback()
        self.admin.execute('DROP SCHEMA IF EXISTS truss CASCADE')
        self.admin.execute('DROP ROLE consumer')
        if hasattr(self,'installation'):
            for role in (self.installation.owner_role,self.installation.registrar_role):
                self.admin.execute('DROP OWNED BY '+psycopg.sql.Identifier(role).as_string(self.admin))
                self.admin.execute('DROP ROLE '+psycopg.sql.Identifier(role).as_string(self.admin))
    def install(self):
        result=self.assembly.install_in_transaction(self.tx)
        if isinstance(result,Error):self.fail(repr(result.error)+' '+str(self.host._custody.last_attempt.error))
        self.installation=result.value
        self.assertEqual(result.value.status,'pending_commit')
        self.host.detach();self.admin.commit()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(result.value.registrar_role)))
    def consumer(self):
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
        connection=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000')
        self.addCleanup(connection.close);connection.execute('BEGIN')
        host=adopt_psycopg_host(connection);self.addCleanup(host.detach)
        self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        return connection,host,assembly,host.adopt_transaction().value
    def prepared(self,assembly):
        source=relational_document();docs=[]
        for identity in ('zdoc','adoc'):
            source['id']=identity;docs.append(CatalogDocument(identity,'r1',json.dumps(source).encode()))
        return assembly.prepare_catalog(tuple(docs),bun_executable='/opt/homebrew/bin/bun')
    def test_disposal_refuses_operations_without_settling_host_transaction(self):
        from truss import AssemblyDisposed
        self.admin.execute("CREATE TEMP TABLE prior_work(value text);INSERT INTO prior_work VALUES('kept')")
        self.assertIsInstance(self.assembly.dispose(),AssemblyDisposed)
        self.assertIsInstance(self.assembly.dispose(),AssemblyDisposed)
        for result in (self.assembly.install_in_transaction(self.tx),
                       self.assembly.status_in_transaction(self.tx),
                       self.assembly.report_in_transaction(self.tx),
                       self.assembly.accept_in_transaction(self.tx,None,request_key='disposed')):
            self.assertIsInstance(result,Error)
            self.assertEqual(result.error.message,'Assembly disposed')
        self.assertEqual(self.admin.execute('TABLE prior_work').fetchall(),[('kept',)])
        self.assertEqual(self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='truss')").fetchone(),(False,))
    def test_host_custom_adapters_cannot_change_catalog_parameters_or_results(self):
        from psycopg.adapt import Loader, Dumper
        class BadLoader(Loader):
            def load(self,data):raise AssertionError('host loader used by Truss')
        class BadDumper(Dumper):
            def dump(self,value):raise AssertionError('host dumper used by Truss')
        self.install();connection,host,assembly,tx=self.consumer()
        prepared=self.prepared(assembly)
        for oid in (16,17,18,19,20,21,23,25,26):
            connection.adapters.register_loader(oid,BadLoader)
        for kind in (str,bytes,int):connection.adapters.register_dumper(kind,BadDumper)
        registered=assembly.accept_in_transaction(tx,prepared,request_key='custom-adapters')
        if isinstance(registered,Error):self.fail(repr(registered.error))
        self.assertFalse(registered.value.replayed)
        replay=assembly.accept_in_transaction(tx,prepared,request_key='custom-adapters')
        self.assertIsInstance(replay,Ok);self.assertTrue(replay.value.replayed)
        report=assembly.report_in_transaction(tx)
        self.assertIsInstance(report,Ok);self.assertEqual(report.value.original_bytes,registered.value.report_bytes)
        host.detach();connection.commit()

    def test_install_ignores_and_restores_caller_search_path(self):
        self.admin.execute('CREATE SCHEMA hostile')
        self.addCleanup(self.admin.execute,'DROP SCHEMA IF EXISTS hostile CASCADE')
        self.admin.execute("""CREATE FUNCTION hostile.gen_random_uuid() RETURNS uuid LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'caller function used by installation'; END $$""")
        self.admin.execute("SET LOCAL search_path=hostile,pg_catalog,pg_temp")
        original=self.admin.execute('SHOW search_path').fetchone()[0]
        result=self.assembly.install_in_transaction(self.tx)
        self.assertIsInstance(result,Ok);self.installation=result.value
        self.assertEqual(self.admin.execute('SHOW search_path').fetchone()[0],original)
        self.host.detach();self.admin.commit()
    def test_optional_empty_root_metadata_may_be_absent(self):
        self.install();connection,host,assembly,tx=self.consumer()
        source=relational_document();source['id']='optional'
        source.pop('extensions',None)
        prepared=assembly.prepare_catalog((CatalogDocument('optional','r1',json.dumps(source).encode()),),bun_executable='/opt/homebrew/bin/bun')
        result=assembly.accept_in_transaction(tx,prepared,request_key='optional-root')
        if isinstance(result,Error):self.fail(repr(result.error))
        host.detach();connection.commit()

    def test_native_facade_refuses_duplicate_or_incomplete_declarations(self):
        import copy
        self.install();connection,host,assembly,tx=self.consumer()
        source=relational_document();source['id']='malformed'
        extra=copy.deepcopy(source['modules'][0]['relationships'][0]);extra['id']='A-B-second';extra['name']='A-B-second'
        source['modules'][0]['relationships'].append(extra)
        prepared=assembly.prepare_catalog((CatalogDocument('malformed','r1',json.dumps(source).encode()),),bun_executable='/opt/homebrew/bin/bun')
        original=json.loads(prepared.declarations_bytes)
        for mutation in ('duplicate-record','duplicate-relationship','field-swap','missing-records','missing-relationships'):
            declarations=copy.deepcopy(original)
            if mutation=='duplicate-record':declarations[0]['records'][1]=copy.deepcopy(declarations[0]['records'][0])
            elif mutation=='duplicate-relationship':declarations[0]['relationships'][1]=copy.deepcopy(declarations[0]['relationships'][0])
            elif mutation=='field-swap':
                field=declarations[0]['records'][0]['fields'][0]
                other=declarations[0]['records'][1]['fields'][0]
                for key in ('fieldModule','fieldId','declaration'):field[key]=copy.deepcopy(other[key])
            elif mutation=='missing-records':del declarations[0]['records']
            else:del declarations[0]['relationships']
            with self.subTest(mutation=mutation):
                connection.execute('SAVEPOINT malformed')
                error=psycopg.errors.FeatureNotSupported if mutation=='field-swap' else psycopg.errors.InvalidParameterValue
                with self.assertRaises(error):
                    connection.execute('SELECT * FROM truss.catalog_accept(%s,%s,%s,%s,%s,%s)',
                        (prepared.input_bytes,prepared.archive_documents_bytes,json.dumps(declarations).encode(),b'{}',b'{}',mutation),prepare=False)
                connection.execute('ROLLBACK TO malformed');connection.execute('RELEASE malformed')
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_registration_request').fetchone(),(0,))
        host.detach();connection.commit()

    def test_nested_definer_preserves_session_actor_and_cannot_entitle_outsider(self):
        self.install();connection,host,assembly,tx=self.consumer()
        self.admin.execute("""CREATE FUNCTION public.truss_fixture_forward_status() RETURNS SETOF record
          LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp
          AS 'SELECT * FROM truss.catalog_status()'""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.truss_fixture_forward_status()')
        self.admin.execute(psycopg.sql.SQL('ALTER FUNCTION public.truss_fixture_forward_status() OWNER TO {}').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        statement='SELECT * FROM public.truss_fixture_forward_status() AS s(installation text,release text,hash text,layout text,revision text)'
        self.assertEqual(connection.execute(statement).fetchone()[0],self.installation.installation_id)
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection.execute('SAVEPOINT denied')
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.execute(statement,prepare=False)
        connection.execute('ROLLBACK TO denied');connection.execute('RELEASE denied')
        host.detach();connection.rollback()
    def test_catalog_refuses_stale_authorization_snapshot_isolation(self):
        self.install();connection,host,assembly,tx=self.consumer()
        host.detach();connection.rollback()
        for isolation in ('REPEATABLE READ','SERIALIZABLE'):
            with self.subTest(isolation=isolation):
                connection.execute('BEGIN ISOLATION LEVEL '+isolation)
                with self.assertRaises(psycopg.errors.FeatureNotSupported):
                    connection.execute('SELECT * FROM truss.catalog_status()')
                connection.rollback()
    def test_install_rollback_leaves_no_schema_or_roles_and_keeps_prior_work(self):
        self.admin.execute("CREATE TEMP TABLE prior_work(value text);INSERT INTO prior_work VALUES('kept')")
        result=self.assembly.install_in_transaction(self.tx)
        self.assertIsInstance(result,Ok)
        self.installation=result.value
        self.assertEqual(self.admin.execute('TABLE prior_work').fetchall(),[('kept',)])
        self.host.detach();self.admin.rollback()
        self.assertEqual(self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='truss')").fetchone(),(False,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM pg_roles WHERE rolname IN (%s,%s)',(result.value.owner_role,result.value.registrar_role)).fetchone(),(0,))
        del self.installation
    def test_early_immediate_constraints_and_conflicting_retry(self):
        self.install();connection,host,assembly,tx=self.consumer()
        connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
        prepared=self.prepared(assembly)
        result=assembly.accept_in_transaction(tx,prepared,request_key='one',origin_bytes=b'{"x-action":"initial"}')
        if isinstance(result,Error):self.fail(repr(result.error)+' '+str(host._custody.last_attempt.error))
        conflict=assembly.accept_in_transaction(tx,prepared,request_key='one',origin_bytes=b'{"x-action":"changed"}')
        self.assertIsInstance(conflict,Error);self.assertEqual(conflict.error.sql_state,'23505')
        self.assertIsInstance(assembly.report_in_transaction(tx),Ok)
        host.detach();connection.commit()
    def test_suppressed_head_refuses_atomically_and_preserves_caller_work(self):
        self.install()
        self.admin.execute("""CREATE FUNCTION truss.fixture_suppress_head() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END $$;
         CREATE TRIGGER fixture_suppress_head BEFORE UPDATE ON truss.schema_head FOR EACH ROW EXECUTE FUNCTION truss.fixture_suppress_head()""")
        connection,host,assembly,tx=self.consumer()
        connection.execute("CREATE TEMP TABLE prior_work(value text);INSERT INTO prior_work VALUES('kept')")
        result=assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='suppressed')
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
        self.assertEqual(connection.execute('TABLE prior_work').fetchall(),[('kept',)])
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_registration_request').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.type_def').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
        host.detach();connection.commit()
    def test_late_report_failure_rolls_back_registration_and_keeps_caller_work(self):
        self.install()
        self.admin.execute("""CREATE FUNCTION truss.fixture_fail_report() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'injected report failure' USING ERRCODE='23514'; END $$;
          CREATE TRIGGER fixture_fail_report BEFORE INSERT ON truss.catalog_acceptance_report
          FOR EACH ROW EXECUTE FUNCTION truss.fixture_fail_report()""")
        connection,host,assembly,tx=self.consumer()
        connection.execute("CREATE TEMP TABLE prior_work(value text);INSERT INTO prior_work VALUES('kept')")
        result=assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='late-failure')
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'23514')
        self.assertEqual(connection.execute('TABLE prior_work').fetchall(),[('kept',)])
        for table in ('type_def','catalog_registration_request','catalog_acceptance_report'):
            self.assertEqual(self.admin.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(psycopg.sql.Identifier(table))).fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
        host.detach();connection.commit()

    def test_outsider_raw_tables_private_helpers_and_role_setting_refuse(self):
        self.install();connection,host,assembly,tx=self.consumer()
        for statement in ('SELECT * FROM truss.schema_doc','SELECT truss.catalog_actor()'):
            connection.execute('SAVEPOINT denied')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.execute(statement)
            connection.execute('ROLLBACK TO denied');connection.execute('RELEASE denied')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        result=assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='outsider')
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'42501')
        host.detach();connection.rollback()

    def test_explicit_role_setting_cannot_replace_authenticated_person(self):
        self.install();connection,host,assembly,tx=self.consumer()
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET TRUE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection.execute(psycopg.sql.SQL('SET LOCAL ROLE {}').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection.execute('SAVEPOINT denied')
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            connection.execute('SELECT * FROM truss.catalog_status()')
        connection.execute('ROLLBACK TO denied');connection.execute('RELEASE denied')
        connection.execute('RESET ROLE')
        self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        host.detach();connection.commit()

    def test_public_install_commit_accept_commit_report_and_retry(self):
        self.install()
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='consumer'
        with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as connection:
            connection.execute('BEGIN');host=adopt_psycopg_host(connection)
            self.addCleanup(host.detach)
            tx=host.adopt_transaction().value
            assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
            status=assembly.status_in_transaction(tx)
            self.assertIsInstance(status,Ok);self.assertEqual(status.value.revision,0)
            source=relational_document();docs=[]
            for identity in ('zdoc','adoc'):
                source['id']=identity;docs.append(CatalogDocument(identity,'r1',json.dumps(source).encode()))
            prepared=assembly.prepare_catalog(tuple(docs),bun_executable='/opt/homebrew/bin/bun')
            registered=assembly.accept_in_transaction(tx,prepared,request_key='stable-request',origin_bytes=b'{"x-action":"register"}')
            if isinstance(registered,Error):self.fail(repr(registered.error)+' '+str(host._custody.last_attempt.error))
            self.assertEqual(registered.value.status,'pending_commit');self.assertFalse(registered.value.replayed)
            host.detach();connection.commit()
            connection.execute('BEGIN');host=adopt_psycopg_host(connection);tx=host.adopt_transaction().value
            assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
            report=assembly.report_in_transaction(tx)
            self.assertIsInstance(report,Ok)
            self.assertEqual(report.value.original_bytes,registered.value.report_bytes)
            retry=assembly.accept_in_transaction(tx,prepared,request_key='stable-request',origin_bytes=b'{"x-action":"register"}')
            if isinstance(retry,Error):self.fail(repr(retry.error)+' '+str(host._custody.last_attempt.error))
            self.assertTrue(retry.value.replayed);self.assertEqual(retry.value.report_bytes,report.value.original_bytes)
            host.detach();connection.commit()

if __name__=='__main__':unittest.main(verbosity=2)
