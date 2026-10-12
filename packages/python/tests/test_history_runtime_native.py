"""One public object/edge reconstruction workflow after canonical deletion."""
import json
from truss import (Ok,Error,HistoryEntity,HistoryPage,HistoricalRecord,HistoricalDeleted,
    HistoryUnavailable,CapabilityAvailable)
from truss.groups import (GroupSuccess,UpdateObject,StoredObjectReference,AuthoredValue,
    CreateEdge,NullOrderKey,Delete)
from truss.contracts import TextValue
import test_receipt_visibility_native as receipt_tests


class HistoryRuntimeTests(receipt_tests.ReceiptVisibilityTests):
    for _name in tuple(n for n in dir(receipt_tests.ReceiptVisibilityTests) if n.startswith('test_')):
        locals()[_name]=None

    def result(self,value,assembly):
        if not isinstance(value,Ok):self.fail(repr(value)+' '+str(assembly._host._custody.last_attempt.error))
        return value.value

    def test_committed_complete_groups_original_versions_and_deleted_edges(self):
        connection,host,assembly,tx=self.ready()
        created,_,_=self.run_group(assembly,tx,(self.create(),self.create(label='target',value='target',record='B',alias='b')),'history-create')
        self.assertIsInstance(created,GroupSuccess);a,b=(v.identity for v in created.response.semantic.results)
        changed,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=a),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='edited')),),unset=()),),'history-update')
        self.assertIsInstance(changed,GroupSuccess)
        relationship=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value
        linked,_,_=self.run_group(assembly,tx,(CreateEdge(relationship_definition_pin=relationship.definition_pin,
            source=StoredObjectReference(identity=a),target=StoredObjectReference(identity=b),values=(),order_key=NullOrderKey()),),'history-link')
        self.assertIsInstance(linked,GroupSuccess);edge=linked.response.semantic.results[0].identity
        removed,_,_=self.run_group(assembly,tx,(Delete(operation='delete_edge',target=StoredObjectReference(identity=edge)),Delete(operation='delete_object',target=StoredObjectReference(identity=a))), 'history-delete')
        self.assertIsInstance(removed,GroupSuccess)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object WHERE id=%s',(int(a.id),)).fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge WHERE id=%s',(int(edge.id),)).fetchone(),(0,))
        connection,host,assembly,tx=self.readonly()
        selected=assembly.history(assembly.history_selection)
        self.assertIsInstance(selected,CapabilityAvailable);history=selected.capability
        entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(a.id))
        first=self.result(history.page_history_in_transaction(tx,entity=entity),assembly)
        self.assertIsInstance(first,HistoryPage);self.assertEqual(len(first.events),1)
        second=self.result(history.page_history_in_transaction(tx,entity=entity,cursor=first.continuation),assembly)
        self.assertEqual([json.loads(v.content)['operation'] for v in second.events],['property','metadata'])
        third=self.result(history.page_history_in_transaction(tx,entity=entity,cursor=second.continuation),assembly)
        self.assertEqual([json.loads(v.content)['operation'] for v in third.events],['delete'])
        initial=self.result(history.reconstruct_in_transaction(tx,entity=entity,version=1),assembly)
        edited=self.result(history.reconstruct_in_transaction(tx,entity=entity,version=2),assembly)
        deleted=self.result(history.reconstruct_in_transaction(tx,entity=entity,version=3),assembly)
        self.assertIsInstance(initial,HistoricalRecord);self.assertIsInstance(edited,HistoricalRecord);self.assertIsInstance(deleted,HistoricalDeleted)
        self.assertEqual(json.loads(initial.record)['recordVersion'],'1')
        self.assertEqual(json.loads(edited.record)['recordVersion'],'2')
        self.assertEqual(deleted.deletion_version,3);self.assertEqual(json.loads(deleted.before)['recordVersion'],'2')
        self.assertIn({'kind':'string','text':'edited'},[v['value'] for v in json.loads(edited.record)['properties']])
        edge_entity=HistoryEntity(kind='edge',document_id='adoc',module_id='m',definition_id='A-B',id=int(edge.id))
        old_edge=self.result(history.reconstruct_in_transaction(tx,entity=edge_entity,version=1),assembly)
        deleted_edge=self.result(history.reconstruct_in_transaction(tx,entity=edge_entity,version=2),assembly)
        self.assertIsInstance(old_edge,HistoricalRecord);self.assertIsInstance(deleted_edge,HistoricalDeleted)
        self.assertEqual(json.loads(old_edge.record)['source']['id'],a.id)
        self.assertEqual(json.loads(deleted_edge.before)['recordVersion'],'1')
        missing=self.result(history.reconstruct_in_transaction(tx,entity=entity,version=4),assembly)
        self.assertIsInstance(missing,HistoryUnavailable);self.assertEqual(missing.reason,'history')
        host.detach();self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0]);connection.rollback()
