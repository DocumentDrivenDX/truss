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
            host.detach()
            if not connection.closed:connection.rollback();connection.close()
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
        schema_path=Path(__file__).resolve().parents[3]/'docs/helix/02-design/contracts/catalog-view-v0.1.schema.json'
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
        prepared=assembly.prepare_catalog((CatalogDocument('cross-module','r1',json.dumps(source).encode()),),bun_executable='/opt/homebrew/bin/bun')
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

    def test_public_view_refuses_corrupt_archive_or_report(self):
        self.install();connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(assembly.accept_in_transaction(tx,self.prepared(assembly),request_key='corruption'),Ok)
        host.detach();connection.commit()
        connection.execute('BEGIN');host=adopt_psycopg_host(connection)
        self.consumer_connections.append((connection,host))
        tx=host.adopt_transaction().value;assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        for table,column,value in (('schema_doc','document','{}'),('catalog_acceptance_report','report_bytes',b'{}')):
            with self.subTest(table=table):
                self.admin.execute('BEGIN')
                self.admin.execute(psycopg.sql.SQL('ALTER TABLE truss.{} DISABLE TRIGGER USER').format(psycopg.sql.Identifier(table)))
                self.admin.execute(psycopg.sql.SQL('UPDATE truss.{} SET {}=%s').format(psycopg.sql.Identifier(table),psycopg.sql.Identifier(column)),(value,))
                self.admin.execute(psycopg.sql.SQL('ALTER TABLE truss.{} ENABLE TRIGGER USER').format(psycopg.sql.Identifier(table)))
                self.admin.commit()
                result=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request())
                self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
                # Restore this controlled administrative corruption from the
                # original accepted request, keeping later cases independent.
                self.admin.execute('BEGIN')
                self.admin.execute(psycopg.sql.SQL('ALTER TABLE truss.{} DISABLE TRIGGER USER').format(psycopg.sql.Identifier(table)))
                if table=='schema_doc':
                    self.admin.execute("""UPDATE truss.schema_doc d SET document=a.value->>'originalText'
                     FROM truss.catalog_registration_request r CROSS JOIN LATERAL jsonb_array_elements(convert_from(r.document_bytes,'UTF8')::jsonb) a
                     WHERE a.value->>'documentId'=d.doc_id""")
                else:
                    self.admin.execute('UPDATE truss.catalog_acceptance_report SET report_bytes=truss.catalog_make_report(r) FROM truss.catalog_registration_request r')
                self.admin.execute(psycopg.sql.SQL('ALTER TABLE truss.{} ENABLE ALWAYS TRIGGER catalog_immutable').format(psycopg.sql.Identifier(table)))
                self.admin.commit()
        host.detach();connection.commit()
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
