"""Basic public one-call traversal of a diamond/cycle on stock PostgreSQL18."""
from truss import (Ok,Error,ObjectFound,TraversalHop,TraversalComplete,TraversalLimited,
    adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration)
from truss.groups import CreateEdge,AliasObjectReference,NullOrderKey,GroupSuccess
import test_group_create_native as create_tests

class PublicTraversalTests(create_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(create_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_diamond_cycle_directions_limits_and_read_only(self):
        def graph(source):
            relation=source['modules'][0]['relationships'][0]
            relation['target'][0]['element']='A'
            relation['sourceMultiplicity']['max']='*'
            relation['targetMultiplicity']['max']='*'
        connection,host,assembly,tx=self.ready(graph)
        relationship=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value
        operations=[self.create(label=name,value=name,alias=name) for name in ('a','b','c','d','e')]
        for i,(source,target) in enumerate((('a','b'),('a','c'),('b','d'),('c','d'),('d','a'),('d','e'))):
            operations.append(CreateEdge(relationship_definition_pin=relationship.definition_pin,source=AliasObjectReference(alias=source),target=AliasObjectReference(alias=target),values=(),order_key=NullOrderKey(),alias='edge'+str(i)))
        input,request=self.input(assembly,tx,tuple(operations));applied=self.apply(assembly,tx,input,request)
        self.assertIsInstance(applied,GroupSuccess)
        identities={result.alias:result.identity for result in applied.response.semantic.results[:5]}
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        host.detach();connection.execute('SET TRANSACTION READ ONLY')
        host=adopt_psycopg_host(connection);self.addCleanup(host.detach)
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction(access_mode='read_only').value
        hop=TraversalHop(relationship=relationship)
        for count,expected in ((1,('b','c')),(2,('d',)),(3,('e',))):
            result=assembly.traverse_in_transaction(tx,start=identities['a'],hops=(hop,)*count)
            if isinstance(result,Error):self.fail(str(result.error)+' '+str(assembly._host._custody.last_attempt.error))
            self.assertIsInstance(result.value,TraversalComplete)
            self.assertEqual(tuple(o.id for o in result.value.objects),tuple(sorted(int(identities[n].id) for n in expected)))
        incoming=assembly.traverse_in_transaction(tx,start=identities['d'],hops=(TraversalHop(relationship=relationship,direction='incoming'),)).value
        self.assertEqual(tuple(o.id for o in incoming.objects),tuple(sorted(int(identities[n].id) for n in ('b','c'))))
        both=assembly.traverse_in_transaction(tx,start=identities['a'],hops=(TraversalHop(relationship=relationship,direction='both'),)).value
        self.assertEqual(tuple(o.id for o in both.objects),tuple(sorted(int(identities[n].id) for n in ('b','c','d'))))
        limited=assembly.traverse_in_transaction(tx,start=identities['a'],hops=(hop,)*3,maximum_path_states=4).value
        self.assertIsInstance(limited,TraversalLimited);self.assertEqual(limited.reason,'path_states');self.assertFalse(hasattr(limited,'objects'))
        limited=assembly.traverse_in_transaction(tx,start=identities['a'],hops=(hop,),maximum_objects=1).value
        self.assertIsInstance(limited,TraversalLimited);self.assertEqual(limited.reason,'result_limit')
        read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identities['a'].id))
        self.assertIsInstance(read.value,ObjectFound)

    def test_property_declaration_owner_is_required_for_object_reads(self):
        from truss import ModuleAccessGrant,ObjectNotFound
        def private_field(source):
            module=source['modules'][0]
            field=next(v for v in module['elements'] if v['id']=='A-value')
            module['elements'].remove(field)
            source['modules'].append({'id':'secret','namespace':'secret','extensions':{},'elements':[field],'relationships':[]})
            record=next(v for v in module['elements'] if v['id']=='A')
            for ref in record['members']:
                if ref['element']=='A-value':ref['module']='secret'
            for key in record['keys']:
                for ref in key['fields']:
                    if ref['element']=='A-value':ref['module']='secret'
        connection,host,assembly,tx=self.ready(private_field)
        # Give the creator both declaration owners, then remove only the field
        # owner. Object rows are produced through the ordinary public group API.
        host.detach();connection.rollback()
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value;admin_tx=admin_host.adopt_transaction().value
        configured=admin_assembly.configure_module_access_in_transaction(admin_tx,(ModuleAccessGrant('adoc','secret','group_reader','group_writer'),))
        self.assertIsInstance(configured,Ok);admin_host.detach();self.admin.commit()
        connection,host,assembly,tx=self.consumer();input,request=self.input(assembly,tx)
        created=self.apply(assembly,tx,input,request);self.assertIsInstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        allowed=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(allowed.value,ObjectFound);host.detach();connection.rollback()
        # Retain current record-module authority; remove field-module policy.
        self.admin.execute("DELETE FROM truss.module_access WHERE document_id='adoc' AND module='secret'")
        connection,host,assembly,tx=self.consumer()
        refused=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(refused.value,ObjectNotFound)
