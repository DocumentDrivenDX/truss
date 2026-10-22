# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public catalog workflow on PostgreSQL: no private staging or fabricated IDs."""
import json
import os
from pathlib import Path
import tempfile
import unittest
import psycopg
from truss import (LocalPostgres,Ok,Error,adopt_psycopg_host,
                   create_reference_assembly,CatalogRuntimeConfiguration,CatalogDocument,ModuleAccessBatchRefused)
from test_catalog_relational_support import relational_document

class PublicCatalogRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(tempfile.mkdtemp(prefix='truss-public-catalog-'))
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
        self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        self.addCleanup(self.host.detach)
        self.tx=self.host.adopt_transaction().value
        result=create_reference_assembly(CatalogRuntimeConfiguration(),self.host)
        self.assertIsInstance(result,Ok)
        self.assembly=result.value
    def _after_consumer_cleanup(self,backend_pids):
        pass
    def tearDown(self):
        backend_pids=[]
        for connection,host in self.consumer_connections:
            if not connection.closed:
                try:backend_pids.append(connection.info.backend_pid)
                except Exception:backend_pids.append(None)
            host.detach()
            if not connection.closed:connection.rollback();connection.close()
        self._after_consumer_cleanup(tuple(backend_pids))
        self.host.detach();self.admin.rollback()
        self.admin.execute('DROP SCHEMA IF EXISTS truss CASCADE')
        self.admin.execute('DROP ROLE consumer')
        if hasattr(self,'installation'):
            for role in (self.installation.owner_role,self.installation.registrar_role):
                self.admin.execute('DROP OWNED BY '+psycopg.sql.Identifier(role).as_string(self.admin))
                self.admin.execute('DROP ROLE '+psycopg.sql.Identifier(role).as_string(self.admin))
    def assert_module_refused(self,result,errors):
        self.assertIsInstance(result,Ok,result)
        self.assertIsInstance(result.value,ModuleAccessBatchRefused,result)
        self.assertEqual(tuple((error.index,error.code) for error in result.value.errors),errors)

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
        host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);self.addCleanup(host.detach)
        self.consumer_connections.append((connection,host))
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        return connection,host,assembly,host.adopt_transaction().value
    def prepared(self,assembly):
        source=relational_document();docs=[]
        for identity in ('zdoc','adoc'):
            source['id']=identity;docs.append(CatalogDocument(identity,'r1',json.dumps(source).encode()))
        return assembly.prepare_catalog(tuple(docs),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
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
        prepared=assembly.prepare_catalog((CatalogDocument('optional','r1',json.dumps(source).encode()),),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        result=assembly.accept_in_transaction(tx,prepared,request_key='optional-root')
        if isinstance(result,Error):self.fail(repr(result.error))
        host.detach();connection.commit()

    def test_native_facade_rejects_retired_declaration_payload_atomically(self):
        self.install();connection,host,assembly,tx=self.consumer()
        connection.execute("CREATE TEMP TABLE prior_work(value text);INSERT INTO prior_work VALUES('kept')")
        prepared=self.prepared(assembly)
        connection.execute('SAVEPOINT retired_declarations')
        with self.assertRaises(psycopg.errors.InvalidParameterValue) as raised:
            connection.execute('SELECT * FROM truss.catalog_accept(%s,%s,%s,%s,%s,%s)',
                (prepared.input_bytes,prepared.archive_documents_bytes,b'[]',b'{}',b'{}','retired-declarations'),prepare=False)
        self.assertEqual(raised.exception.sqlstate,'22023')
        connection.execute('ROLLBACK TO retired_declarations');connection.execute('RELEASE retired_declarations')
        self.assertEqual(connection.execute('TABLE prior_work').fetchall(),[('kept',)])
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
    def test_verified_catalog_basis_has_native_ids_and_atomic_limits(self):
        self.install();connection,host,assembly,tx=self.consumer()
        registered=assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='view')
        self.assertIsInstance(registered,Ok)
        original=connection.execute('SELECT truss.catalog_view_basis(NULL,100,1048576)').fetchone()[0]
        basis=json.loads(bytes(original))
        self.assertEqual(basis['revision'],'1')
        self.assertEqual(len(basis['types']),4);self.assertEqual(len(basis['properties']),8)
        self.assertEqual(len(basis['keys']),8);self.assertEqual(len(basis['relationships']),2)
        self.assertEqual({t['document_id'] for t in basis['types']},{'adoc','zdoc'})
        self.assertIsNone(connection.execute('SELECT truss.catalog_view_basis(2,100,1048576)').fetchone()[0])
        for count,size in ((1,1048576),(100,1)):
            connection.execute('SAVEPOINT budget')
            with self.assertRaises(psycopg.errors.ProgramLimitExceeded):
                connection.execute('SELECT truss.catalog_view_basis(1,%s,%s)',(count,size))
            connection.execute('ROLLBACK TO budget');connection.execute('RELEASE budget')
        for count,size in ((None,1048576),(100,None)):
            connection.execute('SAVEPOINT budget')
            with self.assertRaises(psycopg.errors.InvalidParameterValue):
                connection.execute('SELECT truss.catalog_view_basis(1,%s,%s)',(count,size))
            connection.execute('ROLLBACK TO budget');connection.execute('RELEASE budget')
        host.detach();connection.commit()
    def test_public_catalog_view_exact_sources_dependencies_and_limits(self):
        import base64
        from dataclasses import replace
        from truss import CatalogViewAvailable, CatalogViewUnavailable, HistoricalCatalogSelection
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='public-view'),Ok)
        request=assembly.catalog_view_request()
        result=assembly.catalog_view_in_transaction(tx,request)
        if isinstance(result,Error):self.fail(repr(result.error))
        self.assertIsInstance(result.value,CatalogViewAvailable)
        view=result.value.view
        from jsonschema import Draft202012Validator
        schema_path=Path(__file__).resolve().parents[3]/'docs/helix/02-design/contracts/catalog-view-v0.2.schema.json'
        Draft202012Validator(json.loads(schema_path.read_bytes())).validate(json.loads(view.original_bytes))
        self.assertEqual(len(view.definitions),22)
        self.assertEqual([entry.reference.kind for entry in view.definitions],['type']*4+['property']*8+['key']*8+['relationship']*2)
        keys=[entry for entry in view.definitions if entry.reference.kind=='key']
        self.assertTrue(all(entry.provenance.authored_pointer.endswith('/keys/1') for entry in keys[::2]))
        self.assertTrue(all(entry.reference.authored_identity=='a-primary' for entry in keys[::2]))
        self.assertTrue(all(len(entry.dependencies)==3 for entry in keys[::2]))
        for entry in view.definitions:
            import hashlib
            self.assertEqual(hashlib.sha256(base64.b64decode(entry.definition.bytes_base64)).hexdigest(),entry.definition.sha256)
        historical=assembly.catalog_view_in_transaction(tx,replace(request,selection=HistoricalCatalogSelection(catalog_revision='1')))
        self.assertEqual(historical.value.view.original_bytes,view.original_bytes)
        for limited in (assembly.catalog_view_request(definition_count='1'),assembly.catalog_view_request(encoded_bytes='1')):
            refused=assembly.catalog_view_in_transaction(tx,limited)
            self.assertIsInstance(refused.value,CatalogViewUnavailable);self.assertEqual(refused.value.reason,'resource')
        host.detach();connection.commit()
    def test_public_view_cross_module_fields_self_and_multiple_targets(self):
        import copy
        self.install();connection,host,assembly,tx=self.consumer()
        source=relational_document();source['id']='cross-module'
        module=source['modules'][0]
        fields=[element for element in module['elements'] if element['kind']=='field']
        module['elements']=[element for element in module['elements'] if element['kind']=='record']
        for record in module['elements']:
            for member in record['members']:member['module']='fields'
            for key in record['keys']:
                for member in key['fields']:member['module']='fields'
        source['modules'].append({'id':'fields','namespace':'fields','extensions':{},'elements':fields})
        prototype=module['relationships'][0]
        self_relation=copy.deepcopy(prototype);self_relation['id']='self';self_relation['name']='self'
        self_relation['target']=[{'module':'m','element':'A','key':'a-primary'}]
        multi=copy.deepcopy(prototype);multi['id']='multi';multi['name']='multi'
        multi['target']=[{'module':'m','element':'A','key':'a-primary'},{'module':'m','element':'B','key':'a-primary'}]
        module['relationships']=[self_relation,multi]
        prepared=assembly.prepare_catalog((CatalogDocument('cross-module','r1',json.dumps(source).encode()),),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='cross-module')
        if isinstance(accepted,Error):self.fail(repr(accepted.error))
        result=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request())
        if isinstance(result,Error):self.fail(repr(result.error))
        definitions=result.value.view.definitions
        properties=[entry for entry in definitions if entry.reference.kind=='property']
        self.assertTrue(all(entry.reference.owner.module_id=='fields' for entry in properties))
        self.assertTrue(all(entry.provenance.authored_pointer.startswith('/modules/1/elements/') for entry in properties))
        relationships={entry.reference.authored_identity:entry for entry in definitions if entry.reference.kind=='relationship'}
        self.assertEqual([ref.authored_identity for ref in relationships['self'].dependencies],['A','A','a-primary'])
        self.assertEqual([ref.authored_identity for ref in relationships['multi'].dependencies],['A','A','a-primary','B','a-primary'])
        self.assertNotEqual(relationships['multi'].dependencies[2].type_id,relationships['multi'].dependencies[4].type_id)
        host.detach();connection.commit()
    def test_view_budget_failure_preserves_quarantined_cleanup_outcome(self):
        from unittest.mock import patch
        from truss import psycopg_host
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='cleanup-view'),Ok)
        original=psycopg_host._Deadline;calls=[0]
        def deadline(*args):
            calls[0]+=1
            if calls[0]==2:raise MemoryError('injected cleanup failure')
            return original(*args)
        with patch('truss.psycopg_host._Deadline',side_effect=deadline):
            result=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request(definition_count='1'))
        self.assertIsInstance(result,Error)
        self.assertEqual(result.error.code,'transaction_unusable');self.assertEqual(result.error.sql_state,'54000')
        self.assertTrue(host._custody.quarantined)
        host.detach();connection.rollback()
    def test_second_registrar_reads_catalog_without_becoming_origin_actor(self):
        self.install();connection,host,assembly,tx=self.consumer()
        registered=assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='actor-a')
        self.assertIsInstance(registered,Ok)
        first=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request()).value.view
        host.detach();connection.commit()
        self.admin.execute('CREATE ROLE reader_b LOGIN')
        self.addCleanup(self.admin.execute,'DROP ROLE IF EXISTS reader_b')
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO reader_b WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='reader_b'
        second_connection=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000')
        second_connection.execute('BEGIN');second_host=adopt_psycopg_host(second_connection)
        self.consumer_connections.append((second_connection,second_host))
        second_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),second_host).value
        second_tx=second_host.adopt_transaction().value
        result=second_assembly.catalog_view_in_transaction(second_tx,second_assembly.catalog_view_request())
        if isinstance(result,Error):self.fail(repr(result.error))
        self.assertEqual(result.value.view.original_bytes,first.original_bytes)
        report=second_assembly.report_in_transaction(second_tx)
        self.assertEqual(json.loads(report.value.original_bytes)['actor'],'consumer')
        second_host.detach();second_connection.commit()

    def test_public_view_refuses_corrupt_archive(self):
        self.install();connection,host,assembly,tx=self.consumer()
        prepared=self.prepared(assembly)
        original_documents={item.document.document_id:item.document.content.decode('utf-8') for item in prepared.documents}
        self.assertIsInstance(assembly.accept_in_transaction(tx,prepared,request_key='corruption'),Ok)
        host.detach();connection.commit()
        connection.execute('BEGIN');host=adopt_psycopg_host(connection)
        self.consumer_connections.append((connection,host))
        tx=host.adopt_transaction().value;assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        self.admin.execute('BEGIN')
        self.admin.execute('ALTER TABLE truss.schema_doc DISABLE TRIGGER USER')
        self.admin.execute("UPDATE truss.schema_doc SET document='{}'")
        self.admin.execute('ALTER TABLE truss.schema_doc ENABLE TRIGGER USER')
        self.admin.commit()
        result=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request())
        self.assertIsInstance(result,Error)
        self.assertEqual(result.error.code,'invalid_transaction')
        self.assertIsNone(result.error.sql_state)
        # Restore this controlled administrative corruption from the exact
        # prepared source, keeping recovery independent.
        self.admin.execute('BEGIN')
        self.admin.execute('ALTER TABLE truss.schema_doc DISABLE TRIGGER USER')
        for document_id,document_text in original_documents.items():
            self.admin.execute('UPDATE truss.schema_doc SET document=%s WHERE doc_id=%s',(document_text,document_id))
        self.admin.execute('ALTER TABLE truss.schema_doc ENABLE ALWAYS TRIGGER catalog_immutable')
        self.admin.commit()
        recovered=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request())
        self.assertIsInstance(recovered,Ok)
        host.detach();connection.commit()
    def test_public_module_access_configuration_is_qualified_atomic_and_host_owned(self):
        from truss import ModuleAccessGrant
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='module-config'),Ok)
        host.detach();connection.commit()
        for role in ('app_reader','app_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,'DROP ROLE IF EXISTS '+role)
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin)
        self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        valid=ModuleAccessGrant('adoc','m','app_reader','app_writer')
        second=ModuleAccessGrant('zdoc','m','app_reader','app_writer')
        invalid=ModuleAccessGrant('absent','m','app_reader','app_writer')
        failed=self.assembly.configure_module_access_in_transaction(self.tx,(valid,invalid))
        self.assert_module_refused(failed,((1,'unknown_module'),))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.module_access').fetchone(),(0,))
        for unsafe in ('consumer','postgres',self.installation.owner_role,self.installation.registrar_role):
            with self.subTest(unsafe=unsafe):
                denied=self.assembly.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('adoc','m','app_reader',unsafe),))
                self.assert_module_refused(denied,((0,'unsafe_role'),))
        self.admin.execute("""CREATE FUNCTION truss.fixture_suppress_module_grant() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NEW.document_id='zdoc' THEN RETURN NULL; END IF; RETURN NEW; END $$;
          CREATE TRIGGER fixture_suppress_module_grant BEFORE INSERT ON truss.module_access
          FOR EACH ROW EXECUTE FUNCTION truss.fixture_suppress_module_grant()""")
        suppressed=self.assembly.configure_module_access_in_transaction(self.tx,(valid,second))
        self.assertIsInstance(suppressed,Error)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.module_access').fetchone(),(0,))
        self.admin.execute('DROP TRIGGER fixture_suppress_module_grant ON truss.module_access')
        self.admin.execute('DROP FUNCTION truss.fixture_suppress_module_grant()')
        self.admin.execute("""CREATE FUNCTION truss.fixture_rewrite_earlier_grant() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF NEW.document_id='zdoc' THEN UPDATE truss.module_access SET writer_role='consumer' WHERE document_id='adoc'; END IF;
          RETURN NEW; END $$;
          CREATE TRIGGER fixture_rewrite_earlier_grant BEFORE INSERT ON truss.module_access
          FOR EACH ROW EXECUTE FUNCTION truss.fixture_rewrite_earlier_grant()""")
        rewritten=self.assembly.configure_module_access_in_transaction(self.tx,(valid,second))
        self.assertIsInstance(rewritten,Error)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.module_access').fetchone(),(0,))
        self.admin.execute('DROP TRIGGER fixture_rewrite_earlier_grant ON truss.module_access')
        self.admin.execute('DROP FUNCTION truss.fixture_rewrite_earlier_grant()')
        self.admin.execute('CREATE SCHEMA hostile')
        self.admin.execute("""CREATE FUNCTION hostile.reject_eq(text,text) RETURNS boolean LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'host equality used'; END $$;
          CREATE OPERATOR hostile.= (LEFTARG=pg_catalog.text,RIGHTARG=pg_catalog.text,FUNCTION=hostile.reject_eq)""")
        self.admin.execute('SET LOCAL search_path=hostile,pg_catalog,pg_temp')
        original_path=self.admin.execute('SHOW search_path').fetchone()[0]
        result=self.assembly.configure_module_access_in_transaction(self.tx,(valid,))
        self.assertIsInstance(result,Ok);self.assertEqual(result.value.status,'pending_commit')
        self.assertEqual(self.admin.execute('SHOW search_path').fetchone()[0],original_path)
        unchanged=self.admin.execute('SELECT ctid::text FROM truss.module_access').fetchone()
        self.assertIsInstance(self.assembly.configure_module_access_in_transaction(self.tx,(valid,)),Ok)
        self.assertEqual(self.admin.execute('SELECT ctid::text FROM truss.module_access').fetchone(),unchanged)
        self.assertEqual(self.admin.execute('SELECT document_id,module,reader_role,writer_role FROM truss.module_access').fetchall(),[('adoc','m','app_reader','app_writer')])
        self.host.detach();self.admin.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.module_access').fetchone(),(0,))
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin)
        self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        self.assertIsInstance(self.assembly.configure_module_access_in_transaction(self.tx,(valid,second)),Ok)
        self.host.detach();self.admin.commit()
        self.assertEqual(self.admin.execute('SELECT document_id,module FROM truss.module_access ORDER BY document_id').fetchall(),[('adoc','m'),('zdoc','m')])
        with self.assertRaises(ValueError):ModuleAccessGrant('adoc','m','r'*63+'suffix','app_writer')

    def test_module_configuration_refuses_server_capability_permission_roles(self):
        from truss import ModuleAccessGrant
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='module-capabilities'),Ok)
        host.detach();connection.commit()
        for role in ('app_reader','app_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,'DROP ROLE IF EXISTS '+role)
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin)
        self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        for role in ('pg_read_server_files','pg_write_server_files','pg_execute_server_program'):
            for position in ('reader','writer'):
                with self.subTest(role=role,position=position):
                    self.admin.execute('SAVEPOINT variant')
                    try:
                        grant=ModuleAccessGrant('adoc','m',role if position=='reader' else 'app_reader',role if position=='writer' else 'app_writer')
                        result=self.assembly.configure_module_access_in_transaction(self.tx,(grant,))
                        self.assert_module_refused(result,((0,'unsafe_role'),))
                        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.module_access').fetchone(),(0,))
                    finally:
                        self.admin.execute('ROLLBACK TO variant');self.admin.execute('RELEASE variant')

    def test_module_configuration_refuses_indirect_server_capability_roles(self):
        from truss import ModuleAccessGrant
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='indirect-module-capabilities'),Ok)
        host.detach();connection.commit()
        for role in ('app_reader','app_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,'DROP ROLE IF EXISTS '+role)
        self.admin.execute('GRANT pg_read_server_files TO app_reader WITH INHERIT FALSE, SET TRUE')
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin)
        self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        self.admin.execute("CREATE TEMP TABLE caller_module_sentinel(value text); INSERT INTO caller_module_sentinel VALUES ('kept')")
        grant=ModuleAccessGrant('adoc','m','app_reader','app_writer')
        result=self.assembly.configure_module_access_in_transaction(self.tx,(grant,))
        self.assert_module_refused(result,((0,'unsafe_role'),))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.module_access').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT value FROM caller_module_sentinel').fetchall(),[('kept',)])
        self.admin.execute('REVOKE pg_read_server_files FROM app_reader')
        self.assertIsInstance(self.assembly.configure_module_access_in_transaction(self.tx,(grant,)),Ok)
        self.assertEqual(self.admin.execute('SELECT reader_role,writer_role FROM truss.module_access').fetchall(),[('app_reader','app_writer')])

    def test_module_configuration_refuses_ordinary_caller_and_stale_isolation(self):
        from truss import ModuleAccessGrant
        self.install();connection,host,assembly,tx=self.consumer()
        grant=ModuleAccessGrant('adoc','m','unused_reader','unused_writer')
        self.assertIsInstance(assembly.configure_module_access_in_transaction(tx,(grant,)),Error)
        self.assertEqual(connection.execute('SELECT 1').fetchone(),(1,))
        host.detach();connection.rollback()
        for mode in ('ISOLATION LEVEL REPEATABLE READ','ISOLATION LEVEL SERIALIZABLE','READ ONLY'):
            with self.subTest(mode=mode):
                self.admin.execute('BEGIN '+mode)
                admin_host=adopt_psycopg_host(self.admin)
                isolation={'ISOLATION LEVEL REPEATABLE READ':'repeatable_read','ISOLATION LEVEL SERIALIZABLE':'serializable','READ ONLY':'read_committed'}[mode]
                adopted=admin_host.adopt_transaction(isolation=isolation,access_mode='read_only' if mode=='READ ONLY' else 'read_write')
                self.assertIsInstance(adopted,Ok);admin_tx=adopted.value
                admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
                self.assertIsInstance(admin_assembly.configure_module_access_in_transaction(admin_tx,(grant,)),Error)
                admin_host.detach();self.admin.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.module_access').fetchone(),(0,))

    def test_module_configuration_refuses_inherited_owner_and_raw_privileges(self):
        from truss import ModuleAccessGrant
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='unsafe-grant'),Ok)
        host.detach();connection.commit()
        for role in ('safe_reader','unsafe_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,'DROP ROLE IF EXISTS '+role)
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin)
        self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        grant=ModuleAccessGrant('adoc','m','safe_reader','unsafe_writer')
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO unsafe_writer').format(psycopg.sql.Identifier(self.installation.owner_role)))
        self.assert_module_refused(self.assembly.configure_module_access_in_transaction(self.tx,(grant,)),((0,'unsafe_role'),))
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM unsafe_writer').format(psycopg.sql.Identifier(self.installation.owner_role)))
        self.admin.execute('GRANT SELECT ON truss.object TO unsafe_writer')
        self.assert_module_refused(self.assembly.configure_module_access_in_transaction(self.tx,(grant,)),((0,'unsafe_role'),))
        self.admin.execute('REVOKE SELECT ON truss.object FROM unsafe_writer')
        self.admin.execute('GRANT SELECT(id) ON truss.object TO unsafe_writer')
        self.assert_module_refused(self.assembly.configure_module_access_in_transaction(self.tx,(grant,)),((0,'unsafe_role'),))
        self.admin.execute('REVOKE SELECT(id) ON truss.object FROM unsafe_writer')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.module_access').fetchone(),(0,))
        self.host.detach();self.admin.rollback()

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
        self.assertIsInstance(conflict,Error);self.assertEqual(conflict.error.sql_state,'P1001')
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

    def test_public_actor_refuses_predefined_file_and_program_roles(self):
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        for role in ('pg_read_server_files','pg_write_server_files','pg_execute_server_program'):
            with self.subTest(role=role):
                self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH INHERIT TRUE, SET FALSE').format(psycopg.sql.Identifier(role)))
                try:
                    self.assertEqual(connection.execute("SELECT m.inherit_option,m.set_option FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid JOIN pg_roles a ON a.oid=m.member WHERE a.rolname=session_user AND r.rolname=%s",(role,)).fetchone(),(True,False))
                    self.assertIsInstance(assembly.status_in_transaction(tx),Error)
                    self.assertFalse(host._custody.quarantined)
                finally:self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(role)))
                self.assertIsInstance(assembly.status_in_transaction(tx),Ok)

    def test_public_actor_refuses_indirect_server_capability_membership(self):
        self.install();connection,host,assembly,tx=self.consumer()
        self.admin.execute('CREATE ROLE server_capability_bridge NOLOGIN')
        try:
            self.admin.execute('GRANT pg_read_server_files TO server_capability_bridge WITH INHERIT TRUE, SET FALSE')
            self.admin.execute('GRANT server_capability_bridge TO consumer WITH INHERIT FALSE, SET TRUE')
            self.assertIsInstance(assembly.status_in_transaction(tx),Error)
            self.admin.execute('REVOKE server_capability_bridge FROM consumer')
            self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        finally:
            self.admin.execute('REVOKE server_capability_bridge FROM consumer')
            self.admin.execute('DROP ROLE server_capability_bridge')

    def test_public_actor_refuses_inherited_private_column_privileges(self):
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        self.admin.execute('CREATE ROLE column_privilege_bridge NOLOGIN')
        try:
            self.admin.execute('GRANT SELECT (installation_id) ON truss.catalog_runtime_installation TO column_privilege_bridge')
            self.admin.execute('GRANT column_privilege_bridge TO consumer WITH INHERIT TRUE, SET FALSE')
            try:
                self.assertIsInstance(assembly.status_in_transaction(tx),Error)
            finally:self.admin.execute('REVOKE column_privilege_bridge FROM consumer')
            self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        finally:
            self.admin.execute('DROP OWNED BY column_privilege_bridge')
            self.admin.execute('DROP ROLE column_privilege_bridge')

    def test_public_actor_refuses_switchable_private_column_privileges(self):
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        self.admin.execute('CREATE ROLE switchable_column_bridge NOLOGIN')
        try:
            self.admin.execute('GRANT SELECT (installation_id) ON truss.catalog_runtime_installation TO switchable_column_bridge')
            self.admin.execute('GRANT switchable_column_bridge TO consumer WITH INHERIT FALSE, SET TRUE')
            try:self.assertIsInstance(assembly.status_in_transaction(tx),Error)
            finally:self.admin.execute('REVOKE switchable_column_bridge FROM consumer')
            self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        finally:
            self.admin.execute('DROP OWNED BY switchable_column_bridge')
            self.admin.execute('DROP ROLE switchable_column_bridge')

    def test_public_actor_refuses_late_column_and_reference_privileges(self):
        self.install();connection,host,assembly,tx=self.consumer()
        connection.execute("CREATE TEMP TABLE caller_privilege_sentinel(value text); INSERT INTO caller_privilege_sentinel VALUES ('kept')")
        self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        grants=[('SELECT (installation_id)','SELECT (installation_id)'),
                ('INSERT (installation_id)','INSERT (installation_id)'),
                ('UPDATE (installation_id)','UPDATE (installation_id)'),
                ('REFERENCES (installation_id)','REFERENCES (installation_id)'),
                ('REFERENCES','REFERENCES')]
        for grant,revoke in grants:
            with self.subTest(grant=grant):
                self.admin.execute('GRANT '+grant+' ON truss.catalog_runtime_installation TO consumer')
                try:
                    result=assembly.status_in_transaction(tx)
                    self.assertIsInstance(result,Error)
                    self.assertFalse(host._custody.quarantined)
                    self.assertEqual(connection.execute('SELECT value FROM caller_privilege_sentinel').fetchall(),[('kept',)])
                finally:self.admin.execute('REVOKE '+revoke+' ON truss.catalog_runtime_installation FROM consumer')
                self.assertIsInstance(assembly.status_in_transaction(tx),Ok)

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
            prepared=assembly.prepare_catalog(tuple(docs),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
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


    def test_unknown_document_extension_is_retained_without_policy_interpretation(self):
        from hashlib import sha256
        from truss import AcceptedDocument,ModuleAccessGrant
        self.install();connection,host,assembly,tx=self.consumer()
        connection.execute("CREATE TEMP TABLE prior_work(value text);INSERT INTO prior_work VALUES('kept')")
        source=relational_document();source['id']='opaque-policy'
        source['vocabularies']={'security-next':{'version':'99.0.0'}}
        source['extensions']={'security-next':{'opaquePolicy':{'subject':'Staff','resource':'Projects','rule':'active assignment required'}}}
        content=json.dumps(source).encode()
        prepared=assembly.prepare_catalog((CatalogDocument('opaque-policy','r1',content),),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertEqual(prepared.documents[0].observation()['source'],source)
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='opaque-document-extension')
        self.assertIsInstance(accepted,Ok)
        report=assembly.report_in_transaction(tx)
        self.assertIsInstance(report,Ok)
        validation=json.loads(report.value.original_bytes)['source']['documentValidations'][0]
        self.assertTrue(validation['valid'])
        self.assertFalse(validation['complete'])
        self.assertEqual(connection.execute('TABLE prior_work').fetchall(),[('kept',)])
        host.detach();connection.commit()

        for role in ('opaque_reader','opaque_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE IF EXISTS {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        admin_tx=admin_host.adopt_transaction().value
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        configured=admin_assembly.configure_module_access_in_transaction(admin_tx,
            (ModuleAccessGrant('opaque-policy','m','opaque_reader','opaque_writer'),))
        self.assertIsInstance(configured,Ok)
        admin_host.detach();self.admin.commit()
        self.admin.execute('GRANT opaque_reader TO consumer WITH SET FALSE')

        connection,host,assembly,tx=self.consumer()
        archived=assembly.accepted_document_in_transaction(tx,document_id='opaque-policy')
        self.assertIsInstance(archived.value,AcceptedDocument)
        self.assertEqual(archived.value.content,content)
        self.assertEqual(archived.value.sha256,sha256(content).hexdigest())
        host.detach();connection.rollback()


    def test_public_actor_refuses_admin_option_private_storage_escalation(self):
        self.install();connection,host,assembly,tx=self.consumer()
        self.admin.execute('CREATE ROLE admin_storage_bridge NOLOGIN')
        try:
            self.admin.execute('GRANT USAGE ON SCHEMA truss TO admin_storage_bridge')
            self.admin.execute('GRANT SELECT(installation_id) ON truss.catalog_runtime_installation TO admin_storage_bridge')
            self.admin.execute('GRANT admin_storage_bridge TO consumer WITH ADMIN TRUE, INHERIT FALSE, SET FALSE')
            # Independently demonstrate the actual native self-grant route.
            connection.execute('SAVEPOINT native_escalation')
            connection.execute('GRANT admin_storage_bridge TO consumer WITH SET TRUE')
            connection.execute('SET ROLE admin_storage_bridge')
            self.assertEqual(len(connection.execute('SELECT installation_id FROM truss.catalog_runtime_installation').fetchall()),1)
            connection.execute('RESET ROLE')
            connection.execute('ROLLBACK TO SAVEPOINT native_escalation');connection.execute('RELEASE SAVEPOINT native_escalation')
            self.assertIsInstance(assembly.status_in_transaction(tx),Error)
            self.admin.execute('REVOKE admin_storage_bridge FROM consumer')
            self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        finally:
            self.admin.execute('REVOKE admin_storage_bridge FROM consumer')
            self.admin.execute('DROP OWNED BY admin_storage_bridge; DROP ROLE admin_storage_bridge')

    def test_public_actor_refuses_effective_admin_grantor_paths(self):
     self.install();connection,host,assembly,tx=self.consumer()
     for inherit,set_role in [(True,False),(False,True),(False,False),(True,True)]:
      self.admin.execute('CREATE ROLE grantor_path NOLOGIN;CREATE ROLE grantable_storage NOLOGIN')
      try:
       self.admin.execute('GRANT USAGE ON SCHEMA truss TO grantable_storage')
       self.admin.execute('GRANT SELECT(installation_id) ON truss.catalog_runtime_installation TO grantable_storage')
       self.admin.execute('GRANT grantable_storage TO grantor_path WITH ADMIN TRUE, INHERIT FALSE, SET FALSE')
       self.admin.execute(f'GRANT grantor_path TO consumer WITH INHERIT {inherit}, SET {set_role}')
       admitted=isinstance(assembly.status_in_transaction(tx),Ok)
       connection.execute('SAVEPOINT native_grantor')
       exposed=False;state=None
       try:
        if set_role:connection.execute('SET ROLE grantor_path')
        connection.execute('GRANT grantable_storage TO consumer WITH SET TRUE')
        if set_role:connection.execute('RESET ROLE')
        connection.execute('SET ROLE grantable_storage')
        exposed=len(connection.execute('SELECT installation_id FROM truss.catalog_runtime_installation').fetchall())==1
        connection.execute('RESET ROLE')
       except psycopg.Error as e:state=e.sqlstate
       finally:
        connection.execute('ROLLBACK TO SAVEPOINT native_grantor');connection.execute('RELEASE SAVEPOINT native_grantor')
       self.assertEqual(exposed,inherit or set_role)
       self.assertEqual(state,None if (inherit or set_role) else "XX000")
       self.assertEqual(admitted,not (inherit or set_role))
      finally:
       self.admin.execute('REVOKE grantor_path FROM consumer')
       self.admin.execute('DROP OWNED BY grantor_path,grantable_storage;DROP ROLE grantor_path,grantable_storage')


    def test_public_actor_refuses_public_private_storage_grants(self):
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.status_in_transaction(tx),Ok)
        for privilege in ('SELECT','INSERT','UPDATE','REFERENCES'):
            with self.subTest(privilege=privilege):
                self.admin.execute(psycopg.sql.SQL('GRANT {}(installation_id) ON truss.catalog_runtime_installation TO PUBLIC').format(psycopg.sql.SQL(privilege)))
                try:
                    self.assertEqual(connection.execute('SELECT has_column_privilege(session_user,%s,%s,%s)',
                        ('truss.catalog_runtime_installation','installation_id',privilege)).fetchone(),(True,))
                    if privilege=='SELECT':
                        self.assertEqual(len(connection.execute('SELECT installation_id FROM truss.catalog_runtime_installation').fetchall()),1)
                    refused=assembly.status_in_transaction(tx)
                    self.assertIsInstance(refused,Error);self.assertEqual(refused.error.sql_state,'42501')
                finally:
                    self.admin.execute(psycopg.sql.SQL('REVOKE {}(installation_id) ON truss.catalog_runtime_installation FROM PUBLIC').format(psycopg.sql.SQL(privilege)))
                self.assertIsInstance(assembly.status_in_transaction(tx),Ok)

if __name__=='__main__':unittest.main(verbosity=2)
