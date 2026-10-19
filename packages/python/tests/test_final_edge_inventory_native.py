# SPDX-License-Identifier: MIT OR Apache-2.0
"""Final edge membership still refuses an actual edge absent from the plan."""
from truss import Error,EdgeFound
from truss.contracts import MapValue,TextValue
from truss.groups import StoredObjectReference,UpdateEdge,AuthoredValue,GroupSuccess
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

    def test_suppressed_edge_insert_refuses_atomically(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        baseline=self.admin.execute('SELECT (SELECT count(*) FROM truss.object),(SELECT count(*) FROM truss.edge),(SELECT count(*) FROM truss.journal),(SELECT count(*) FROM truss.runtime_object_attempt),(SELECT count(*) FROM truss.runtime_owned_operation),(SELECT count(*) FROM truss.runtime_object_transition),(SELECT count(*) FROM truss.runtime_edge_transition)').fetchone()
        connection.execute("CREATE TEMP TABLE prior_edge_work(value text);INSERT INTO prior_edge_work VALUES('kept')")
        self.admin.execute("""CREATE FUNCTION public.suppress_edge_insert() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ BEGIN
            RETURN NULL;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.suppress_edge_insert()')
        self.admin.execute('CREATE TRIGGER suppress_edge_insert BEFORE INSERT ON truss.edge FOR EACH ROW EXECUTE FUNCTION public.suppress_edge_insert()')
        try:
            context=assembly.group_context_in_transaction(tx).value
            operations=tuple(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b),alias=f'edge{i}') for i in range(2))
            result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),context.request('suppressed-edge-insert'),documents=self.documents)
            self.assertIsInstance(result,Error,repr(result))
            self.assertEqual(result.error.sql_state,'55000',repr(result))
            self.assertEqual(connection.execute('TABLE prior_edge_work').fetchall(),[('kept',)])
        finally:
            self.admin.execute('DROP TRIGGER suppress_edge_insert ON truss.edge')
        host.detach();connection.commit()
        after=self.admin.execute('SELECT (SELECT count(*) FROM truss.object),(SELECT count(*) FROM truss.edge),(SELECT count(*) FROM truss.journal),(SELECT count(*) FROM truss.runtime_object_attempt),(SELECT count(*) FROM truss.runtime_owned_operation),(SELECT count(*) FROM truss.runtime_object_transition),(SELECT count(*) FROM truss.runtime_edge_transition)').fetchone()
        self.assertEqual(after,baseline)
