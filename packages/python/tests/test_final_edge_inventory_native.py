"""Final edge membership still refuses an actual edge absent from the plan."""
from truss import Error
from truss.contracts import MapValue
from truss.groups import StoredObjectReference
import test_edge_mutations_native as edge_tests


class FinalEdgeInventoryTests(edge_tests.EdgeMutationTests):
    for _name in tuple(n for n in dir(edge_tests.EdgeMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def ready(self):
        def allow_parallel(source):
            relation=source['modules'][0]['relationships'][0]
            relation['sourceMultiplicity']['max']=2
            relation['targetMultiplicity']['max']=2
        return super().ready(allow_parallel)

    def test_unplanned_parallel_incident_edge_refuses_and_rolls_back(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        connection.execute("CREATE TEMP TABLE prior_inventory_work(value text);INSERT INTO prior_inventory_work VALUES('kept')")
        self.admin.execute("""CREATE FUNCTION public.add_unplanned_edge() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ BEGIN
            INSERT INTO truss.edge(rel_type_id,source_id,source_type,target_id,target_type,props,order_key,rev)
            SELECT rel_type_id,source_id,source_type,target_id,target_type,props,order_key,rev
            FROM truss.edge WHERE id=NEW.edge_id;
            RETURN NEW;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.add_unplanned_edge()')
        self.admin.execute('CREATE TRIGGER add_unplanned_edge AFTER INSERT ON truss.runtime_edge_transition FOR EACH ROW EXECUTE FUNCTION public.add_unplanned_edge()')
        try:
            context=assembly.group_context_in_transaction(tx).value
            operation=self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b))
            result=assembly.apply_in_transaction(tx,context.input((operation,),MapValue(entries=())),context.request('unplanned-edge'),documents=self.documents)
            self.assertIsInstance(result,Error,repr(result))
            self.assertEqual(result.error.sql_state,'55000',repr(result))
            self.assertIn('complete final incident edge inventory required',str(host._custody.last_attempt.error))
            self.assertEqual(connection.execute('TABLE prior_inventory_work').fetchall(),[('kept',)])
        finally:
            self.admin.execute('DROP TRIGGER add_unplanned_edge ON truss.runtime_edge_transition')
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_edge_transition').fetchone(),(0,))
