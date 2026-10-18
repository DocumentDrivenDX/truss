"""Consumer reader catalog/source workflows on actual protected PostgreSQL."""
import hashlib
import psycopg
from truss import Ok, ReaderCatalog, AcceptedDocument, CatalogRefused, CatalogInvalid, CatalogUnavailable
import test_group_create_native as group_tests

class ReaderCatalogTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def reader(self,mutate_source=None):
        connection,host,assembly,tx=self.ready(mutate_source)
        self.admin.execute('REVOKE group_writer FROM consumer')
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        return connection,host,assembly,tx

    def test_reader_catalog_and_exact_document_without_registrar(self):
        connection,host,assembly,tx=self.reader()
        result=assembly.reader_catalog_in_transaction(tx)
        self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,ReaderCatalog)
        self.assertEqual([(m['documentId'],m['moduleId']) for m in result.value.modules],[('adoc','m')])
        module=result.value.modules[0]
        self.assertEqual([t['recordId'] for t in module['types']],['A','B'])
        self.assertEqual(len(module['properties']),4);self.assertEqual(len(module['keys']),4);self.assertEqual(len(module['relationships']),1)
        source=assembly.accepted_document_in_transaction(tx,document_id='adoc')
        self.assertIsInstance(source.value,AcceptedDocument)
        original=next(d.content for d in self.documents if d.document_id=='adoc')
        self.assertEqual(source.value.content,original);self.assertEqual(source.value.sha256,hashlib.sha256(original).hexdigest())
        self.assertEqual(source.value.document_revision,'r1');self.assertEqual(source.value.artifact_identity,'adoc')
        self.assertEqual(source.value.catalog_revision,1);self.assertTrue(source.value.registration_id)
        for doc in ('zdoc','unknown'):
            self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id=doc).value,CatalogRefused)
        self.assertIsInstance(assembly.reader_catalog_in_transaction(tx,maximum_count=1).value,CatalogUnavailable)
        self.assertIsInstance(assembly.reader_catalog_in_transaction(tx,maximum_bytes=0).value,CatalogInvalid)
        self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id='adoc',maximum_bytes=10).value,CatalogUnavailable)
        self.admin.execute('REVOKE group_reader FROM consumer')
        self.assertIsInstance(assembly.reader_catalog_in_transaction(tx).value,CatalogRefused)
        self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id='adoc').value,CatalogRefused)
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id='adoc').value,AcceptedDocument)
        host.detach();connection.rollback()

    def test_unreadable_empty_module_prevents_whole_document_disclosure(self):
        def mixed(source):source['modules'].append({'id':'hidden','namespace':'hidden','extensions':{},'elements':[],'relationships':[]})
        connection,host,assembly,tx=self.reader(mixed)
        catalog=assembly.reader_catalog_in_transaction(tx)
        self.assertEqual([(m['documentId'],m['moduleId']) for m in catalog.value.modules],[('adoc','m')])
        self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id='adoc').value,CatalogRefused)

        from truss import ModuleAccessGrant, adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        admin_tx=admin_host.adopt_transaction().value
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        configured=admin_assembly.configure_module_access_in_transaction(admin_tx,(ModuleAccessGrant('adoc','hidden','group_reader','group_writer'),))
        self.assertIsInstance(configured,Ok);admin_host.detach();self.admin.commit()
        catalog=assembly.reader_catalog_in_transaction(tx).value
        self.assertEqual([(m['documentId'],m['moduleId']) for m in catalog.modules],[('adoc','hidden'),('adoc','m')])
        self.assertEqual(catalog.modules[0]['types'],[])
        self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id='adoc').value,AcceptedDocument)

    def test_hidden_field_and_key_dependencies_are_not_projected(self):
        def mixed(source):
            module=source['modules'][0]
            field=next(e for e in module['elements'] if e['id']=='A-label');module['elements'].remove(field)
            source['modules'].append({'id':'hidden','namespace':'hidden','extensions':{},'elements':[field],'relationships':[]})
            for element in module['elements']:
                for reference in element.get('members',[]):
                    if reference['element']=='A-label':reference['module']='hidden'
                for key in element.get('keys',[]):
                    for reference in key['fields']:
                        if reference['element']=='A-label':reference['module']='hidden'
        connection,host,assembly,tx=self.reader(mixed)
        catalog=assembly.reader_catalog_in_transaction(tx).value
        self.assertIsInstance(catalog,ReaderCatalog)
        self.assertEqual(len(catalog.modules[0]['properties']),3)
        self.assertEqual(len(catalog.modules[0]['keys']),2)
        self.assertNotIn('A-label',str(catalog.modules))

    def test_dependency_revoked_after_host_admission_filters_retained_catalog_baseline(self):
        """Concurrent revocation precedes the native query; no mid-SQL hook is claimed."""
        import concurrent.futures
        import threading
        from unittest.mock import patch
        import truss.catalog_runtime as runtime
        from truss import ModuleAccessGrant, adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration
        def mixed(source):
            module=source['modules'][0]
            field=next(e for e in module['elements'] if e['id']=='A-label');module['elements'].remove(field)
            source['modules'].append({'id':'z','namespace':'z','extensions':{},'elements':[field],'relationships':[]})
            for element in module['elements']:
                for reference in element.get('members',[]):
                    if reference['element']=='A-label':reference['module']='z'
                for key in element.get('keys',[]):
                    for reference in key['fields']:
                        if reference['element']=='A-label':reference['module']='z'
        connection,host,assembly,tx=self.reader(mixed)
        self.admin.execute('CREATE ROLE dependency_reader NOLOGIN');self.admin.execute('CREATE ROLE dependency_writer NOLOGIN')
        self.addCleanup(self.admin.execute,'DROP ROLE dependency_writer');self.addCleanup(self.admin.execute,'DROP ROLE dependency_reader')
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin);admin_tx=admin_host.adopt_transaction().value
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        self.assertIsInstance(admin_assembly.configure_module_access_in_transaction(admin_tx,(ModuleAccessGrant('adoc','z','dependency_reader','dependency_writer'),)),Ok)
        admin_host.detach();self.admin.commit();self.admin.execute('GRANT dependency_reader TO consumer WITH SET FALSE')
        baseline=assembly.reader_catalog_in_transaction(tx).value
        self.assertEqual(len(baseline.modules[0]['properties']),4)
        connection.execute("CREATE TEMP TABLE reader_prior(value text);INSERT INTO reader_prior VALUES('kept')")
        # Pause the actual public operation after host admission and immediately
        # before its native SELECT. Replacing an installed authorization routine
        # invalidates installation identity and cannot exercise its native loop.
        # This boundary test covers a retained baseline and live permissions;
        # revocation after an in-SQL projection has buffered fields is separate.
        entered=threading.Event();release=threading.Event()
        original_pin=runtime._pin_cursor
        def admitted_query(cursor):
            original_pin(cursor)
            entered.set()
            if not release.wait(timeout=5):
                raise AssertionError('reader query gate was not released')
        with patch('truss.catalog_runtime._pin_cursor',side_effect=admitted_query):
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                pending=executor.submit(assembly.reader_catalog_in_transaction,tx)
                try:
                    self.assertTrue(entered.wait(timeout=3),'reader did not reach the admitted query boundary')
                    self.assertFalse(pending.done())
                    self.admin.execute('REVOKE dependency_reader FROM consumer')
                finally:
                    release.set()
                observed=pending.result(timeout=5)
        self.assertIsInstance(observed,Ok,repr(observed))
        self.assertIsInstance(observed.value,ReaderCatalog,repr(observed))
        self.assertEqual(len(observed.value.modules[0]['properties']),3)
        self.assertEqual(len(observed.value.modules[0]['keys']),2)
        self.assertNotIn('A-label',str(observed.value.modules))
        self.assertNotIn('z',[module['moduleId'] for module in observed.value.modules])
        self.assertEqual(len(baseline.modules[0]['properties']),4)
        self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id='adoc').value,CatalogRefused)
        self.assertEqual(connection.execute('TABLE reader_prior').fetchall(),[('kept',)])

    def test_relationship_endpoint_metadata_requires_both_module_scopes(self):
        def mixed(source):
            module=source['modules'][0]
            endpoint=next(e for e in module['elements'] if e['id']=='B');module['elements'].remove(endpoint)
            source['modules'].append({'id':'hidden','namespace':'hidden','extensions':{},'elements':[endpoint],'relationships':[]})
            module['relationships'][0]['target'][0]['module']='hidden'
        connection,host,assembly,tx=self.reader(mixed)
        catalog=assembly.reader_catalog_in_transaction(tx).value
        self.assertEqual([(m['documentId'],m['moduleId']) for m in catalog.modules],[('adoc','m')])
        self.assertEqual([t['recordId'] for t in catalog.modules[0]['types']],['A'])
        self.assertEqual(catalog.modules[0]['relationships'],[])
        self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id='adoc').value,CatalogRefused)
        from truss import ModuleAccessGrant,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
        self.admin.execute('CREATE ROLE endpoint_reader NOLOGIN;CREATE ROLE endpoint_writer NOLOGIN')
        try:
            self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin);admin_tx=admin_host.adopt_transaction().value
            admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
            self.assertIsInstance(admin_assembly.configure_module_access_in_transaction(admin_tx,(ModuleAccessGrant('adoc','hidden','endpoint_reader','endpoint_writer'),)),Ok)
            admin_host.detach();self.admin.commit()
            self.admin.execute('GRANT endpoint_reader TO consumer WITH SET FALSE')
            visible=assembly.reader_catalog_in_transaction(tx).value
            modules={m['moduleId']:m for m in visible.modules}
            self.assertEqual([t['recordId'] for t in modules['hidden']['types']],['B'])
            relation=modules['m']['relationships'][0]
            self.assertEqual(relation['endpoints'],[{'sourceType':modules['m']['types'][0]['typeId'],'targetType':modules['hidden']['types'][0]['typeId']}])
            self.assertIsInstance(assembly.accepted_document_in_transaction(tx,document_id='adoc').value,AcceptedDocument)
            self.admin.execute('REVOKE endpoint_reader FROM consumer')
            hidden=assembly.reader_catalog_in_transaction(tx).value
            self.assertEqual(hidden.modules[0]['relationships'],[])
            self.assertEqual([t['recordId'] for t in hidden.modules[0]['types']],['A'])
        finally:
            host.detach();connection.rollback()
            self.admin.execute('REVOKE endpoint_reader FROM consumer')
            self.admin.execute('DELETE FROM truss.module_access WHERE document_id=\'adoc\' AND module=\'hidden\'')
            self.admin.execute('DROP OWNED BY endpoint_reader,endpoint_writer;DROP ROLE endpoint_reader,endpoint_writer')
