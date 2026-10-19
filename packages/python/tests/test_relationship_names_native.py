# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public relationship presentation names evolve while edge identities remain."""
import json,os
from truss import Ok,CatalogDocument,CatalogRegistration,QueryRows,HistoryEntity,HistoricalRecord,TraversalHop,TraversalComplete,EdgeFound
from truss.contracts import MapValue,TextValue
from truss.groups import GroupSuccess,CommittedReceiptReplay,CreateEdge,AliasObjectReference,NullOrderKey,UpdateEdge,StoredObjectReference,AuthoredValue
import test_group_create_native as base

class RelationshipNameTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.10.0'
    def fields(self,source):
        source['umf']=self.source_version
        for element in source['modules'][0]['elements']:
            if element['kind']=='record':element['name']=element['id']
        source['modules'][0]['relationships'][0]['inverse']='B-A'
    def test_rename_query_traverse_update_history_and_original_replay(self):
        bun=os.environ.get('TRUSS_BUN_EXECUTABLE','bun')
        c,h,a,t=self.ready(self.fields);original_documents=self.documents
        original_ref=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value
        context=a.group_context_in_transaction(t).value
        semantic=context.input((self.create('one',alias='a'),self.create('two',record='B',alias='b'),CreateEdge(relationship_definition_pin=original_ref.definition_pin,source=AliasObjectReference(alias='a'),target=AliasObjectReference(alias='b'),values=(),order_key=NullOrderKey())),MapValue(entries=()));request=context.request('original-relationship-labels')
        created=self.apply(a,t,semantic,request);self.assertIsInstance(created,GroupSuccess)
        source=created.response.semantic.results[0].identity;target=created.response.semantic.results[1].identity;edge=created.response.semantic.results[2].identity
        h.detach();c.commit();rows=self.admin.execute('SELECT to_jsonb(e) FROM truss.edge e ORDER BY id').fetchall()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE');c,h,a,t=self.consumer()
        report=a.report_in_transaction(t).value.original_bytes
        original=json.loads(next(d.content for d in self.documents if d.document_id=='adoc'));renamed=json.loads(json.dumps(original));relationship=renamed['modules'][0]['relationships'][0]
        relationship['name']='Forward';relationship['inverse']='Backward'
        document=CatalogDocument('adoc','r2',json.dumps(renamed).encode());prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=bun)
        accepted=a.accept_in_transaction(t,prepared,request_key='rename-relationship');self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted.value))
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT to_jsonb(e) FROM truss.edge e ORDER BY id').fetchall(),rows)
        self.documents=tuple(document if d.document_id=='adoc' else d for d in self.documents);c,h,a,t=self.consumer()
        current_ref=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value
        self.assertEqual(current_ref.relationship_id,original_ref.relationship_id);self.assertNotEqual(current_ref.definition_pin,original_ref.definition_pin)
        for sql in ['SELECT COUNT(*) FROM "A" a WHERE HAS_RELATED(a."Forward",KEY(\'value\',\'two\'))','SELECT COUNT(*) FROM "B" b WHERE HAS_RELATED(b."Backward",KEY(\'value\',\'one\'))']:
            result=a.query_in_transaction(t,sql=sql,document_ids=('adoc',));self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,QueryRows,repr(result.value));self.assertEqual(result.value.rows,((1,),))
        traversed=a.traverse_in_transaction(t,start=source,hops=(TraversalHop(relationship=current_ref),)).value
        self.assertIsInstance(traversed,TraversalComplete);self.assertEqual(tuple(o.identity.id for o in traversed.objects),(target.id,))
        found=a.get_edge_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B',edge_id=int(edge.id)).value;self.assertIsInstance(found,EdgeFound);self.assertEqual(found.edge.version,1)
        context=a.group_context_in_transaction(t).value
        updated=self.apply(a,t,context.input((UpdateEdge(target=StoredObjectReference(identity=found.edge.identity),set=(AuthoredValue(name='note',value=TextValue(kind='string',text='changed')),),unset=()),),MapValue(entries=())),context.request('update-renamed-edge'));self.assertIsInstance(updated,GroupSuccess)
        h.detach();c.commit();c,h,a,t=self.consumer()
        history=a.reconstruct_in_transaction(t,entity=HistoryEntity(kind='edge',document_id='adoc',module_id='m',definition_id='A-B',id=int(edge.id)),version=1).value
        self.assertIsInstance(history,HistoricalRecord);self.assertEqual(json.loads(history.record)['recordVersion'],'1')
        replay=a.apply_in_transaction(t,semantic,request,documents=original_documents,bun_executable=bun);self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
        self.assertEqual(a.report_in_transaction(t,revision=1).value.original_bytes,report)
        h.detach();c.rollback()
