"""One public workflow using a CREATEROLE installer with no superuser privilege."""
import psycopg
from truss import (Ok,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration,
    ModuleAccessGrant,FeedPage,FeedAcknowledged,ObjectFound)
from truss.groups import GroupSuccess
import test_object_mutations_native as mutation_tests

class ManagedInstallationTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def setUp(self):
        super().setUp();self.host.detach();self.admin.rollback()
        self.admin.execute('CREATE ROLE installer LOGIN CREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS')
        database=self.admin.execute('SELECT current_database()').fetchone()[0]
        self.admin.execute(psycopg.sql.SQL('GRANT CREATE ON DATABASE {} TO installer WITH GRANT OPTION').format(psycopg.sql.Identifier(database)))
        self.addCleanup(self.admin.execute,'DROP ROLE installer')
        self.addCleanup(self.admin.execute,'DROP OWNED BY installer')
        params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']='installer'
        self.manager=psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000');self.addCleanup(self.manager.close)
        self.assertEqual(self.manager.execute("SELECT rolsuper,rolcreaterole,rolcreatedb,rolbypassrls FROM pg_roles WHERE rolname=session_user").fetchone(),(False,True,False,False))

    def administrative(self):
        self.manager.execute('BEGIN')
        self.host=adopt_psycopg_host(self.manager,statement_timeout_ms=10000,operation_timeout_ms=30000)
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        self.tx=self.host.adopt_transaction().value
        return self.assembly,self.tx

    def test_non_super_install_configure_create_lookup_feed_and_ack(self):
        assembly,tx=self.administrative()
        result=assembly.install_in_transaction(tx)
        if not isinstance(result,Ok):self.fail(repr(result)+' '+str(self.host._custody.last_attempt.error))
        self.installation=result.value
        self.assertTrue(assembly.status_in_transaction(tx).value.installed)
        self.host.detach();self.manager.commit()
        self.manager.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection,host,assembly,tx=self.consumer()
        prepared=self.prepared(assembly);self.documents=tuple(d.document for d in prepared.documents)
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='managed-model');self.assertIsInstance(accepted,Ok)
        view=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request()).value.view
        self.types={(d.reference.owner.document_id,d.reference.authored_identity):d.reference for d in view.definitions if d.reference.kind=='type'}
        host.detach();connection.commit()
        for role in ('group_reader','group_writer'):
            self.manager.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        assembly,tx=self.administrative()
        configured=assembly.configure_module_access_in_transaction(tx,tuple(ModuleAccessGrant(doc,'m','group_reader','group_writer') for doc in ('adoc','zdoc')))
        if not isinstance(configured,Ok):self.fail(repr(configured)+' '+str(self.host._custody.last_attempt.error))
        enrolled=assembly.register_feed_consumer_in_transaction(tx,consumer_id='managed-adapter',reader_role='group_reader')
        if not isinstance(enrolled,Ok):self.fail(repr(enrolled)+' '+str(self.host._custody.last_attempt.error))
        self.host.detach();self.manager.commit()
        self.manager.execute('GRANT group_reader,group_writer TO consumer WITH SET FALSE')
        owner=self.manager.execute('SELECT owner_oid FROM truss.catalog_runtime_installation').fetchone()[0]
        self.assertFalse(self.manager.execute("SELECT has_database_privilege(%s,current_database(),'CREATE')",(owner,)).fetchone()[0])
        connection,host,assembly,tx=self.consumer()
        created,_,_=self.run_group(assembly,tx,(self.create(),),'managed-create');self.assertIsInstance(created,GroupSuccess)
        reader=assembly.direct_reads(assembly.direct_read_selection).capability
        found=reader.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('value','one'),bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(found.value,ObjectFound)
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        feed=assembly.feed(assembly.feed_selection).capability
        revision=feed.read_feed_in_transaction(tx,consumer_id='managed-adapter');self.assertIsInstance(revision.value,FeedPage)
        self.assertIsInstance(feed.acknowledge_feed_in_transaction(tx,revision.value).value,FeedAcknowledged)
        data=feed.read_feed_in_transaction(tx,consumer_id='managed-adapter');self.assertIsInstance(data.value,FeedPage)
        self.assertEqual(data.value.outcome,'transaction')
        self.assertIsInstance(feed.acknowledge_feed_in_transaction(tx,data.value).value,FeedAcknowledged)
        host.detach();connection.commit()
