# SPDX-License-Identifier: MIT OR Apache-2.0
"""Practical groups remain valid across explicitly fired deferred checks."""
from truss import EdgeFound,Ok
from truss.groups import (AliasObjectReference,StoredObjectReference,GroupSuccess,
                          GroupFailed,UpdateEdge,EndpointChange,Delete)
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
