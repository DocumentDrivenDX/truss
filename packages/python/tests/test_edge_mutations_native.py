# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic adopter workflows for native relationship groups."""
from dataclasses import replace
from truss import Ok,EdgeFound,EdgeNotFound,EdgePage,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import MapValue,TextValue
from truss.groups import (CreateEdge,UpdateEdge,Delete,NullOrderKey,TextOrderKey,EndpointChange,StoredObjectReference,AliasObjectReference,
    AuthoredValue,GroupSuccess,GroupFailed,RelationshipCount,PreconditionFailed,CommittedReceiptReplay,Unchanged)
import test_group_preconditions_native as condition_tests

class EdgeMutationTests(condition_tests.GroupPreconditionTests):
    for _name in tuple(n for n in dir(condition_tests.GroupPreconditionTests) if n.startswith('test_')):
        locals()[_name]=None

    def link(self,pin,source,target,alias='edge'):
        return CreateEdge(relationship_definition_pin=pin,source=source,target=target,values=(AuthoredValue(name='note',value=TextValue(kind='string',text='linked')),),order_key=TextOrderKey(text='a'),alias=alias)

    def test_link_retarget_unlink_and_original_retry(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        applied,input,request=self.run_group(assembly,tx,(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b)),),'link')
        self.assertIsInstance(applied,GroupSuccess);edge=applied.response.semantic.results[0].identity
        read=assembly.get_edge_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',edge_id=int(edge.id))
        self.assertIsInstance(read.value,EdgeFound);self.assertEqual(read.value.edge.source,a);self.assertEqual(dict(read.value.edge.retained),{'note':'linked'})
        no_op,_ ,_=self.run_group(assembly,tx,(UpdateEdge(target=StoredObjectReference(identity=edge),set=(),unset=(),expected_version='1'),))
        self.assertIsInstance(no_op,GroupSuccess);self.assertIsInstance(no_op.response.semantic.results[0],Unchanged)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        host.detach();connection.execute('SET TRANSACTION READ ONLY')
        host=adopt_psycopg_host(connection);self.addCleanup(host.detach)
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction(access_mode='read_only').value
        read_only=assembly.get_edge_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',edge_id=int(edge.id))
        self.assertIsInstance(read_only.value,EdgeFound)
        page=assembly.page_edges_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',anchor=a).value
        self.assertEqual(page.edges[0].identity,edge)
        host.detach();connection.rollback();connection,host,assembly,tx=self.consumer()
        replay=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(replay,Ok);self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
        added,_,_=self.run_group(assembly,tx,(self.create(label='third',value='third',alias='third',record='B'),
            replace(self.link(pin,StoredObjectReference(identity=a),AliasObjectReference(alias='third'),alias='second'),order_key=NullOrderKey())), 'second-link')
        self.assertIsInstance(added,GroupSuccess);third,second=(v.identity for v in added.response.semantic.results)
        first=assembly.page_edges_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',anchor=a,limit=1).value
        self.assertIsInstance(first,EdgePage);self.assertEqual(first.edges[0].identity,edge);self.assertIsNotNone(first.continuation)
        tail=assembly.page_edges_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',anchor=a,limit=1,continuation=first.continuation).value
        self.assertEqual(tail.edges[0].identity,second);self.assertIsNone(tail.continuation)
        next_result,_,_=self.run_group(assembly,tx,(Delete(operation='delete_edge',target=StoredObjectReference(identity=second)),
            UpdateEdge(target=StoredObjectReference(identity=edge),set=(),unset=(),endpoint_change=EndpointChange(source=StoredObjectReference(identity=a),target=StoredObjectReference(identity=third)),order_key_change=NullOrderKey(),expected_version='1'),
            Delete(operation='delete_edge',target=StoredObjectReference(identity=edge),expected_version='2')),'unlink')
        self.assertIsInstance(next_result,GroupSuccess)
        missing=assembly.get_edge_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',edge_id=int(edge.id));self.assertIsInstance(missing.value,EdgeNotFound)
        host.detach();connection.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
        connection,host,assembly,tx=self.consumer()
        replay=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(replay.value.response,CommittedReceiptReplay);self.assertEqual(replay.value.response.semantic,applied.response.semantic)
        host.detach();connection.rollback()

    def test_mandatory_link_and_failed_count_are_atomic(self):
        def mandatory(source):source['modules'][0]['relationships'][0]['targetMultiplicity']['min']=1
        connection,host,assembly,tx=self.ready(mandatory)
        pin=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        bad,_,_=self.run_group(assembly,tx,(self.create(),),'missing-required-edge');self.assertIsInstance(bad,GroupFailed)
        result,_,_=self.run_group(assembly,tx,(self.create(),self.create(label='two',value='other',alias='b',record='B'),self.link(pin,AliasObjectReference(alias='item'),AliasObjectReference(alias='b'))),'mandatory')
        self.assertIsInstance(result,GroupSuccess);a=result.response.semantic.results[0].identity
        context=assembly.group_context_in_transaction(tx).value
        input=context.input((self.create(label='new',value='new',alias='new',record='B'),),MapValue(entries=()),preconditions=(RelationshipCount(id='empty',reason='must be empty',relationship_definition_pin=pin,anchor=a,direction='outgoing',maximum='0'),))
        failed=assembly.apply_in_transaction(tx,input,context.request('count-failed'),documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(failed.value.failure,PreconditionFailed)
        host.detach();connection.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(2,))
