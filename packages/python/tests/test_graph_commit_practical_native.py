# SPDX-License-Identifier: MIT OR Apache-2.0
"""Practical groups remain valid across explicitly fired deferred checks."""
from truss import (EdgeFound,Ok,ModuleAccessGrant,adopt_psycopg_host,
                   create_reference_assembly,CatalogRuntimeConfiguration)
from truss.groups import (AliasObjectReference,StoredObjectReference,GroupSuccess,
                          GroupFailed,UpdateEdge,EndpointChange,Delete,
                          UnauthorizedPerson)
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

    def _unbounded_graph(self, mutate=None, setup=None, linked=True):
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
        operations=(self.create(alias='a'),self.create(label='b',value='b',alias='b',record='B'))
        if linked:
            operations=(*operations,self.link(pin,AliasObjectReference(alias='a'),AliasObjectReference(alias='b')))
        result,_,_=self.run_group(assembly,tx,operations,'graph-seed')
        self.assertIsInstance(result,GroupSuccess)
        identities=tuple(item.identity for item in result.response.semantic.results)
        a,b=identities[:2];edge=identities[2] if linked else None
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        return connection,host,assembly,tx,a,b,edge

    def _create_independent_root(self, assembly, tx, key='graph-change'):
        # A new object is a structural graph change; a pure value update has no
        # affected graph members and correctly bypasses graph settlement.
        return self.run_group(assembly,tx,(self.create(label='new',value='new',alias='new-root'),),key)[0]

    def _create_linked_root(self, assembly, tx, b, key, pin=None):
        if pin is None:pin=assembly.get_relationship_reference_in_transaction(
            tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        return self.run_group(assembly,tx,(self.create(label='new',value='new',alias='new-root'),
            self.link(pin,AliasObjectReference(alias='new-root'),StoredObjectReference(identity=b))),key)[0]

    def _hidden_endpoint_graph(self, linked=True):
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
        connection,host,assembly,tx,a,b,edge=self._unbounded_graph(split_endpoint,configure_endpoint_access,linked)
        return connection,host,assembly,tx,a,b,edge

    def test_delete_without_incident_edges_does_not_require_unrelated_endpoint_reader(self):
        connection,host,assembly,tx,a,b,_=self._hidden_endpoint_graph(linked=False)
        self.admin.execute('REVOKE endpoint_reader,endpoint_writer FROM consumer')
        before_count=self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0]
        deleted,_,_=self.run_group(assembly,tx,(Delete(operation='delete_object',
            target=StoredObjectReference(identity=a),expected_version='1'),),'unrelated-endpoint-reader')
        self.assertIsInstance(deleted,GroupSuccess)
        self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0],before_count-1)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object WHERE id=%s',(int(b.id),)).fetchone()[0],1)

    def test_affected_endpoint_reader_is_required(self):
        connection,host,assembly,tx,a,b,edge=self._hidden_endpoint_graph()
        pin=assembly.get_relationship_reference_in_transaction(
            tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        self.admin.execute('REVOKE endpoint_reader,endpoint_writer FROM consumer')
        before=self.admin.execute('SELECT (SELECT count(*) FROM truss.object),(SELECT count(*) FROM truss.edge),(SELECT count(*) FROM truss.journal)').fetchone()
        refused=self._create_linked_root(assembly,tx,b,'missing-affected-endpoint-reader',pin)
        self.assertIsInstance(refused,GroupFailed)
        self.assertIsInstance(refused.failure,UnauthorizedPerson)
        self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT (SELECT count(*) FROM truss.object),(SELECT count(*) FROM truss.edge),(SELECT count(*) FROM truss.journal)').fetchone(),before)

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
