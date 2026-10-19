"""Practical groups remain valid across explicitly fired deferred checks."""
from truss import (EdgeFound,Ok,ModuleAccessGrant,adopt_psycopg_host,
                   create_reference_assembly,CatalogRuntimeConfiguration,Error)
from truss.groups import (AliasObjectReference,StoredObjectReference,GroupSuccess,
                          GroupFailed,UpdateEdge,EndpointChange,Delete,
                          UnauthorizedPerson,RequestNone)
from truss.contracts import MapValue
from test_edge_mutations_native import EdgeMutationTests

class GraphCommitPracticalTests(EdgeMutationTests):
    for _name in tuple(n for n in dir(EdgeMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_retarget_after_explicit_checks_and_failed_unlink(self):
        def mandatory(source):
            source['modules'][0]['relationships'][0]['targetMultiplicity']['min']=1
        connection,host,assembly,tx=self.ready(mandatory)
        pin=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        created,_,_=self.run_group(assembly,tx,(
            self.create(label='a',alias='a'),self.create(label='b1',alias='b1',record='B'),
            self.create(label='b2',alias='b2',record='B'),
            self.link(pin,AliasObjectReference(alias='a'),AliasObjectReference(alias='b1'))),'initial')
        self.assertIsInstance(created,GroupSuccess)
        source,b1,b2,edge=(item.identity for item in created.response.semantic.results)
        connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
        connection.execute('SET CONSTRAINTS ALL DEFERRED')
        changed,_,_=self.run_group(assembly,tx,(UpdateEdge(target=StoredObjectReference(identity=edge),
            set=(),unset=(),endpoint_change=EndpointChange(source=StoredObjectReference(identity=source),
            target=StoredObjectReference(identity=b2)),expected_version='1'),),'retarget')
        self.assertIsInstance(changed,GroupSuccess)
        connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
        connection.execute('SET CONSTRAINTS ALL DEFERRED')
        failed,_,_=self.run_group(assembly,tx,(Delete(operation='delete_edge',target=StoredObjectReference(identity=edge),expected_version='2'),),'required-unlink')
        self.assertIsInstance(failed,GroupFailed)
        connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        found=assembly.get_edge_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',edge_id=int(edge.id))
        self.assertIsInstance(found,Ok);self.assertIsInstance(found.value,EdgeFound)
        self.assertEqual(found.value.edge.source,source)
        self.assertEqual(found.value.edge.target,b2)
        self.assertEqual(found.value.edge.version,2)
        host.detach();connection.rollback()

    def _unbounded_graph(self, mutate=None, setup=None):
        def unbounded(source):
            relation=source['modules'][0]['relationships'][0]
            relation['sourceMultiplicity']={'min':0,'max':'*'}
            relation['targetMultiplicity']={'min':0,'max':'*'}
            if mutate is not None: mutate(source)
        connection,host,assembly,tx=self.ready(unbounded)
        if setup is not None:
            setup(connection,host,assembly,tx)
        pin=assembly.get_relationship_reference_in_transaction(
            tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        result,_,_=self.run_group(assembly,tx,(self.create(alias='a'),
            self.create(label='b',value='b',alias='b',record='B'),
            self.link(pin,AliasObjectReference(alias='a'),AliasObjectReference(alias='b'))),'graph-seed')
        self.assertIsInstance(result,GroupSuccess)
        a,b,edge=(item.identity for item in result.response.semantic.results)
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        return connection,host,assembly,tx,a,b,edge

    def _create_independent_root(self, assembly, tx, key='graph-change'):
        # A new object is a structural graph change; a pure value update has no
        # affected graph members and correctly bypasses graph settlement.
        return self.run_group(assembly,tx,(self.create(label='new',value='new',alias='new-root'),),key)[0]

    def _create_linked_root(self, assembly, tx, b, key):
        pin=assembly.get_relationship_reference_in_transaction(
            tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        return self.run_group(assembly,tx,(self.create(label='new',value='new',alias='new-root'),
            self.link(pin,AliasObjectReference(alias='new-root'),StoredObjectReference(identity=b))),key)[0]

    def _seed_marker(self, marker):
        self.admin.execute('BEGIN')
        try:
            self.admin.execute("SET LOCAL session_replication_role='replica'")
            self.admin.execute('INSERT INTO truss.edge_limit(rel_type_id,side,endpoint_id,edge_id) VALUES(%s,%s,%s,%s)',marker)
            self.admin.commit()
        except BaseException:
            self.admin.rollback()
            raise

    def test_unbounded_marker_inserted_by_delete_statement_trigger_is_refused(self):
        connection,host,assembly,tx,a,b,edge=self._unbounded_graph()
        self.admin.execute('''CREATE FUNCTION public.graph_insert_incident_marker() RETURNS trigger
          LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,truss AS $$
          BEGIN
           INSERT INTO truss.edge_limit(rel_type_id,side,endpoint_id,edge_id)
           SELECT e.rel_type_id,'s',t.object_id,e.id
           FROM truss.runtime_object_transition t
           JOIN truss.edge e ON e.source_id=t.object_id AND e.source_type=t.type_id
           JOIN truss.rel_def r USING(rel_type_id)
           WHERE t.writer_xid=pg_current_xact_id() AND t.before_object IS NULL
             AND r.document_id='adoc' AND r.rel_id='A-B'
           ORDER BY t.operation_index DESC,e.id DESC LIMIT 1
           ON CONFLICT DO NOTHING;
           RETURN NULL;
          END $$''')
        self.admin.execute('CREATE TRIGGER graph_insert_incident_marker AFTER DELETE ON truss.edge_limit FOR EACH STATEMENT EXECUTE FUNCTION public.graph_insert_incident_marker()')
        try:
            before=self.admin.execute('SELECT (SELECT count(*) FROM truss.object),(SELECT count(*) FROM truss.edge),(SELECT count(*) FROM truss.journal),(SELECT count(*) FROM truss.edge_limit)').fetchone()
            context=assembly.group_context_in_transaction(tx).value
            pin=assembly.get_relationship_reference_in_transaction(
                tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
            failed=assembly.apply_in_transaction(tx,context.input((self.create(label='new',value='new',alias='new-root'),
                self.link(pin,AliasObjectReference(alias='new-root'),StoredObjectReference(identity=b))),MapValue(entries=())),
                RequestNone(),documents=self.documents)
            self.assertIsInstance(failed,Error)
            self.assertEqual(failed.error.sql_state,'55000',repr(failed))
            self.assertEqual(host._custody.last_attempt.phase,'contained')
            self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        finally:
            host.detach();connection.commit()
            self.assertEqual(self.admin.execute('SELECT (SELECT count(*) FROM truss.object),(SELECT count(*) FROM truss.edge),(SELECT count(*) FROM truss.journal),(SELECT count(*) FROM truss.edge_limit)').fetchone(),before)
            self.admin.execute('DROP TRIGGER IF EXISTS graph_insert_incident_marker ON truss.edge_limit')
            self.admin.execute('DROP FUNCTION IF EXISTS public.graph_insert_incident_marker()')

    def _hidden_endpoint_graph(self):
        def split_endpoint(source):
            module=source['modules'][0]
            endpoint=next(item for item in module['elements'] if item['id']=='B')
            fields=[item for item in module['elements'] if item.get('id','').startswith('B-')]
            endpoint['members']=[dict(member,module='hidden') for member in endpoint['members']]
            for key in endpoint['keys']:
                key['fields']=[dict(field,module='hidden') for field in key['fields']]
            module['elements']=[item for item in module['elements'] if item is not endpoint and item not in fields]
            source['modules'].append({'id':'hidden','namespace':'hidden','extensions':{},
                'elements':[endpoint,*fields],'relationships':[]})
            module['relationships'][0]['target'][0]['module']='hidden'
        def configure_endpoint_access(connection,host,assembly,tx):
            self.admin.execute('CREATE ROLE endpoint_reader NOLOGIN;CREATE ROLE endpoint_writer NOLOGIN')
            self.addCleanup(self.admin.execute,'DROP OWNED BY endpoint_reader,endpoint_writer;DROP ROLE endpoint_reader,endpoint_writer')
            self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
            admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
            configured=admin_assembly.configure_module_access_in_transaction(admin_host.adopt_transaction().value,
                (ModuleAccessGrant('adoc','hidden','endpoint_reader','endpoint_writer'),))
            self.assertIsInstance(configured,Ok);admin_host.detach();self.admin.commit()
            self.admin.execute('GRANT endpoint_reader,endpoint_writer TO consumer WITH SET FALSE')
        connection,host,assembly,tx,a,b,edge=self._unbounded_graph(split_endpoint,configure_endpoint_access)
        return connection,host,assembly,tx,a,b,edge

    def test_unaffected_endpoint_type_reader_is_still_required(self):
        connection,host,assembly,tx,a,b,edge=self._hidden_endpoint_graph()
        self.admin.execute('REVOKE endpoint_reader,endpoint_writer FROM consumer')
        before_count=self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0]
        before_object=self.read(assembly,tx,a).object
        refused=self._create_independent_root(assembly,tx,'missing-endpoint-reader')
        self.assertIsInstance(refused,GroupFailed)
        self.assertIsInstance(refused.failure,UnauthorizedPerson)
        self.assertEqual(self.read(assembly,tx,a).object,before_object)
        self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0],before_count)

    def test_reader_revoked_after_marker_refresh_is_rechecked(self):
        connection,host,assembly,tx,a,b,edge=self._hidden_endpoint_graph()
        # Keep the reader grant as the sole hidden-module authority so the
        # trigger's revocation changes the phase-two answer.
        self.admin.execute('REVOKE endpoint_writer FROM consumer')
        self.admin.execute('''CREATE FUNCTION public.graph_revoke_endpoint_reader() RETURNS trigger
          LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
          BEGIN REVOKE endpoint_reader FROM consumer; RETURN NULL; END $$''')
        self.admin.execute('CREATE TRIGGER graph_revoke_endpoint_reader AFTER DELETE ON truss.edge_limit FOR EACH STATEMENT EXECUTE FUNCTION public.graph_revoke_endpoint_reader()')
        try:
            before=self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0]
            marker_before=self.admin.execute('SELECT rel_type_id,side,endpoint_id,edge_id FROM truss.edge_limit ORDER BY rel_type_id,side,endpoint_id,edge_id').fetchall()
            refused=self._create_linked_root(assembly,tx,b,'revoked-after-refresh')
            self.assertIsInstance(refused,GroupFailed)
            self.assertIsInstance(refused.failure,UnauthorizedPerson)
            self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        finally:
            host.detach();connection.commit()
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0],before)
            self.assertEqual(self.admin.execute('SELECT rel_type_id,side,endpoint_id,edge_id FROM truss.edge_limit ORDER BY rel_type_id,side,endpoint_id,edge_id').fetchall(),marker_before)
            self.admin.execute('DROP TRIGGER IF EXISTS graph_revoke_endpoint_reader ON truss.edge_limit')
            self.admin.execute('DROP FUNCTION IF EXISTS public.graph_revoke_endpoint_reader()')

    def test_bounded_opposite_endpoint_keeps_legacy_marker(self):
        def bounded_opposite(source):
            source['modules'][0]['relationships'][0]['sourceMultiplicity']['max']=1
        connection,host,assembly,tx,a,b,edge=self._unbounded_graph(bounded_opposite)
        before=self.admin.execute('SELECT rel_type_id,side,endpoint_id,edge_id FROM truss.edge_limit ORDER BY rel_type_id,side,endpoint_id,edge_id').fetchall()
        self.assertTrue(before)
        result=self._create_independent_root(assembly,tx,'bounded-opposite')
        self.assertIsInstance(result,GroupSuccess)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT rel_type_id,side,endpoint_id,edge_id FROM truss.edge_limit ORDER BY rel_type_id,side,endpoint_id,edge_id').fetchall(),before)

    def test_nonincident_marker_survives_unbounded_validation(self):
        connection,host,assembly,tx,a,b,edge=self._unbounded_graph()
        relationship_id=self.admin.execute("SELECT rel_type_id FROM truss.rel_def WHERE document_id='adoc' AND rel_id='A-B'").fetchone()[0]
        marker=(int(relationship_id),'t',int(b.id),int(edge.id))
        self._seed_marker(marker)
        result=self._create_independent_root(assembly,tx,'nonincident-marker')
        self.assertIsInstance(result,GroupSuccess)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT rel_type_id,side,endpoint_id,edge_id FROM truss.edge_limit').fetchall(),[marker])
