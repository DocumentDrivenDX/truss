"""Final edge membership still refuses an actual edge absent from the plan."""
from truss import Error,EdgeFound
from truss.contracts import MapValue,TextValue
from truss.groups import StoredObjectReference,AliasObjectReference,UpdateEdge,AuthoredValue,GroupSuccess
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

    def test_two_edge_attempts_in_one_transaction_commit_and_read_back(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        first,_,_=self.run_group(assembly,tx,
            (self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b)),),'first-edge')
        self.assertIsInstance(first,GroupSuccess)
        edge=first.response.semantic.results[0].identity
        second,_,_=self.run_group(assembly,tx,(UpdateEdge(
            target=StoredObjectReference(identity=edge),
            set=(AuthoredValue(name='note',value=TextValue(kind='string',text='changed')),),
            unset=(),expected_version='1'),),'second-edge')
        self.assertIsInstance(second,GroupSuccess)
        self.assertEqual(second.response.semantic.results[0].version,'2')
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute(
            'SELECT count(*) FROM truss.runtime_edge_transition WHERE edge_id=%s',
            (int(edge.id),)).fetchone(),(2,))
        connection,host,assembly,tx=self.consumer()
        found=assembly.get_edge_in_transaction(tx,document_id='adoc',module_id='m',
            relationship_id='A-B',edge_id=int(edge.id)).value
        self.assertIsInstance(found,EdgeFound)
        self.assertEqual(dict(found.edge.retained),{'note':'changed'})
        host.detach();connection.rollback()

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

    def test_future_result_slot_refuses_before_next_edge_effect(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        connection.execute("CREATE TEMP TABLE prior_slot_work(value text);INSERT INTO prior_slot_work VALUES('kept')")
        self.admin.execute("""CREATE FUNCTION public.preseal_future_edge_slot() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ BEGIN
            UPDATE truss.runtime_owned_operation SET result='{}'::jsonb
             WHERE attempt_id=NEW.id AND operation_index=2 AND result IS NULL;
            RETURN NEW;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.preseal_future_edge_slot()')
        self.admin.execute("""CREATE FUNCTION public.reject_second_edge_effect() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ BEGIN
            IF EXISTS(SELECT 1 FROM truss.edge) THEN
             RAISE EXCEPTION 'later edge effect reached' USING ERRCODE='P9999';END IF;
            RETURN NEW;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.reject_second_edge_effect()')
        self.admin.execute("""CREATE TRIGGER preseal_future_edge_slot AFTER UPDATE ON truss.runtime_object_attempt
            FOR EACH ROW WHEN (OLD.next_index=1 AND NEW.next_index=2)
            EXECUTE FUNCTION public.preseal_future_edge_slot()""")
        self.admin.execute('CREATE TRIGGER reject_second_edge_effect BEFORE INSERT ON truss.edge FOR EACH ROW EXECUTE FUNCTION public.reject_second_edge_effect()')
        try:
            context=assembly.group_context_in_transaction(tx).value
            # A dependent create followed by alias edges requires the ordered
            # executor. Independent stored-endpoint edges now seal as one batch.
            operations=(self.create(label='ordered-source',alias='source'),
                *(self.link(pin,AliasObjectReference(alias='source'),StoredObjectReference(identity=b),alias=f'edge{i}') for i in range(2)))
            result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),context.request('future-edge-slot'),documents=self.documents)
            self.assertIsInstance(result,Error,repr(result))
            self.assertEqual(result.error.sql_state,'55000',repr(result))
            self.assertIn('original completed edge operation progress required',str(host._custody.last_attempt.error))
            self.assertEqual(connection.execute('TABLE prior_slot_work').fetchall(),[('kept',)])
        finally:
            self.admin.execute('DROP TRIGGER preseal_future_edge_slot ON truss.runtime_object_attempt')
            self.admin.execute('DROP TRIGGER reject_second_edge_effect ON truss.edge')
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_edge_transition').fetchone(),(0,))

    def test_presealed_batch_slot_refuses_before_any_edge_insert(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        self.admin.execute("""CREATE FUNCTION public.preseal_captured_edge_slot() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ BEGIN
            UPDATE truss.runtime_owned_operation SET result='{}'::jsonb
             WHERE attempt_id=NEW.attempt_id AND operation_index=1 AND result IS NULL;
            RETURN NEW;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.preseal_captured_edge_slot()')
        self.admin.execute("""CREATE TRIGGER preseal_captured_edge_slot AFTER INSERT ON truss.runtime_owned_operation
            FOR EACH ROW WHEN (NEW.operation_index=1) EXECUTE FUNCTION public.preseal_captured_edge_slot()""")
        self.admin.execute("""CREATE FUNCTION public.reject_any_batch_edge() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ BEGIN
            RAISE EXCEPTION 'batch edge effect reached' USING ERRCODE='P9999';END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.reject_any_batch_edge()')
        self.admin.execute('CREATE TRIGGER reject_any_batch_edge BEFORE INSERT ON truss.edge FOR EACH ROW EXECUTE FUNCTION public.reject_any_batch_edge()')
        try:
            context=assembly.group_context_in_transaction(tx).value
            operations=tuple(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b),alias=f'edge{i}') for i in range(2))
            result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),context.request('presealed-edge-batch'),documents=self.documents)
            self.assertIsInstance(result,Error,repr(result))
            self.assertEqual(result.error.sql_state,'55000',repr(result))
            self.assertIn('exact stored prepared operation required',str(host._custody.last_attempt.error))
        finally:
            self.admin.execute('DROP TRIGGER preseal_captured_edge_slot ON truss.runtime_owned_operation')
            self.admin.execute('DROP TRIGGER reject_any_batch_edge ON truss.edge')
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
