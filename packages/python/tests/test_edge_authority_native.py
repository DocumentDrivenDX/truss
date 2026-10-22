# SPDX-License-Identifier: MIT OR Apache-2.0
"""Edge authority remains current at post-write and deferred settlement boundaries."""
import psycopg
from truss import Ok
from truss.contracts import MapValue
from truss.groups import GroupFailed,GroupSuccess,StoredObjectReference,UnauthorizedPerson
import test_edge_mutations_native as edge_tests


class EdgeAuthorityTests(edge_tests.EdgeMutationTests):
    for _name in tuple(n for n in dir(edge_tests.EdgeMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_edge_writer_revoked_after_attempt_flush_aborts(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        created,_,_=self.run_group(assembly,tx,(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b)),),'pending-edge')
        self.assertIsInstance(created,GroupSuccess)
        connection.execute('SET CONSTRAINTS truss.runtime_object_attempt_commit IMMEDIATE')
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        self.admin.execute('REVOKE group_writer FROM consumer')
        host.detach()
        try:
            connection.commit()
        except psycopg.ProgrammingError as denied:
            self.assertEqual(denied.sqlstate,'P1403')
            connection.rollback()
        else:
            durable=self.admin.execute('SELECT count(*) FROM truss.edge').fetchone()[0]
            self.fail('Revoked edge writer COMMIT succeeded; durable edges='+str(durable)+'; transaction='+connection.info.transaction_status.name)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_edge_transition').fetchone(),(0,))

    def test_unsafe_actor_after_effect_and_result_writes_refuses(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        connection.execute("CREATE TEMP TABLE prior_edge_work(value text);INSERT INTO prior_edge_work VALUES('kept')")
        self.admin.execute("CREATE FUNCTION public.edge_actor_change() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ BEGIN ALTER ROLE consumer CREATEROLE;RETURN NEW;END $$")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.edge_actor_change()')
        for table,event in (('runtime_edge_transition','AFTER INSERT'),('runtime_object_attempt','AFTER UPDATE')):
            with self.subTest(boundary=table):
                self.admin.execute('CREATE TRIGGER edge_actor_change '+event+' ON truss.'+table+' FOR EACH ROW'+(' WHEN (NOT NEW.complete)' if table=='runtime_object_attempt' else '')+' EXECUTE FUNCTION public.edge_actor_change()')
                try:
                    context=assembly.group_context_in_transaction(tx).value
                    original=context.input((self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b)),),MapValue(entries=()))
                    result=assembly.apply_in_transaction(tx,original,context.request('actor-'+table),documents=self.documents)
                    self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,GroupFailed,repr(result))
                    self.assertIsInstance(result.value.failure,UnauthorizedPerson,repr(result))
                    self.assertEqual(connection.execute('TABLE prior_edge_work').fetchall(),[('kept',)])
                    self.assertEqual(self.admin.execute("SELECT rolcreaterole FROM pg_roles WHERE rolname='consumer'").fetchone(),(False,))
                    self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
                finally:
                    self.admin.execute('DROP TRIGGER edge_actor_change ON truss.'+table)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
