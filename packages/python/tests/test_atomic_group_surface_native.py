"""An ordinary writer can apply a group but cannot drive its private steps."""
import psycopg
from truss import Ok,ModuleAccessGrant,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly
from truss.groups import GroupSuccess,RequestNone
from test_group_create_native import PublicCreateGroupTests

class AtomicGroupSurfaceTests(PublicCreateGroupTests):
    for _name in tuple(n for n in dir(PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_private_steps_refused_and_public_group_still_commits(self):
        connection,host,assembly,tx=self.ready()
        probes=(
            "SELECT truss.object_group_begin(NULL::bytea,NULL::bytea,NULL::bytea,NULL::text,NULL::text,NULL::bytea,false)",
            "SELECT truss.object_group_metadata(NULL::uuid,0)",
            "SELECT truss.object_group_step(NULL::uuid,0,NULL::bytea)",
            "SELECT truss.object_group_finish(NULL::uuid)",
            "SELECT truss.apply_create_group(NULL::bytea,NULL::bytea,NULL::bytea,NULL::bytea,NULL::text,NULL::text)",
        )
        for sql in probes:
            with self.subTest(sql=sql):
                with self.assertRaises((psycopg.errors.InsufficientPrivilege,psycopg.errors.UndefinedFunction)):
                    with connection.transaction():
                        connection.execute(sql)
        exposed=connection.execute("SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND p.proname IN ('object_group_begin','object_group_metadata','object_group_step','object_group_finish','apply_create_group') AND has_function_privilege(current_user,p.oid,'EXECUTE')").fetchall()
        self.assertEqual(exposed,[])
        input,_=self.input(assembly,tx,(self.create(label='public',value='kept'),))
        applied=self.apply(assembly,tx,input,RequestNone())
        self.assertIsInstance(applied,GroupSuccess)
        identity=applied.response.semantic.results[0].identity
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        found=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(found,Ok)
        self.assertEqual(dict(found.value.object.values)['A-label'],'public')
        host.detach();connection.rollback()

    def test_reconfiguration_closes_an_earlier_roles_partial_grant(self):
        connection,host,assembly,tx=self.ready()
        self.admin.execute('CREATE ROLE earlier_writer NOLOGIN')
        self.addCleanup(self.admin.execute,'DROP ROLE earlier_writer')
        self.admin.execute('GRANT EXECUTE ON FUNCTION truss.object_group_step(uuid,int,bytea) TO earlier_writer')
        self.admin.execute('GRANT earlier_writer TO consumer WITH SET FALSE')
        self.assertTrue(connection.execute("SELECT has_function_privilege(current_user,'truss.object_group_step(uuid,int,bytea)','EXECUTE')").fetchone()[0])
        self.admin.execute('BEGIN')
        admin_host=adopt_psycopg_host(self.admin)
        self.addCleanup(admin_host.detach)
        admin_tx=admin_host.adopt_transaction().value
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
        configured=admin_assembly.configure_module_access_in_transaction(admin_tx,(ModuleAccessGrant('adoc','m','group_reader','group_writer'),))
        self.assertIsInstance(configured,Ok)
        admin_host.detach();self.admin.commit()
        self.assertFalse(self.admin.execute("SELECT has_function_privilege('consumer','truss.object_group_step(uuid,int,bytea)','EXECUTE')").fetchone()[0])
        host.detach();connection.rollback()
        connection,host,assembly,tx=self.consumer()
        self.assertFalse(connection.execute("SELECT has_function_privilege(current_user,'truss.object_group_step(uuid,int,bytea)','EXECUTE')").fetchone()[0])
        input,_=self.input(assembly,tx,(self.create(label='after-closure',value='kept'),))
        self.assertIsInstance(self.apply(assembly,tx,input,RequestNone()),GroupSuccess)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
