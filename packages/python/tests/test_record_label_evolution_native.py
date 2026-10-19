# SPDX-License-Identifier: MIT OR Apache-2.0
"""Stable catalog IDs with Record SQL names/member order and retained history."""
import json,os
from truss import Ok,CatalogDocument,CatalogRegistration,ObjectFound,QueryRows,HistoryEntity,HistoricalRecord
from truss.contracts import MapValue,TextValue
from truss.groups import GroupSuccess,CommittedReceiptReplay,CreateEdge,AliasObjectReference,NullOrderKey,UpdateObject,UpdateEdge,StoredObjectReference,AuthoredValue
import test_group_create_native as create_tests

class RecordLabelEvolutionTests(create_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(create_tests.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    source_version='0.10.0'
    def fields(self,source):
        source['umf']=self.source_version
        for e in source['modules'][0]['elements']:
            if e['kind']=='record':e['name']=e['id']
    def test_public_rename_reorder_update_history_and_original_replay(self):
        c,h,a,t=self.ready(self.fields);original_documents=self.documents
        pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        context=a.group_context_in_transaction(t).value
        semantic=context.input((self.create('one',alias='a'),self.create('two',alias='b',record='B'),CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias='a'),target=AliasObjectReference(alias='b'),values=(),order_key=NullOrderKey())),MapValue(entries=()));request=context.request('original-labels')
        created=self.apply(a,t,semantic,request);self.assertIsInstance(created,GroupSuccess);identity=created.response.semantic.results[0].identity;edge=created.response.semantic.results[2].identity
        h.detach();c.commit()
        objects=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall();keys=self.admin.execute('SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall()
        self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE');c,h,a,t=self.consumer()
        first_report=a.report_in_transaction(t).value.original_bytes
        original=json.loads(next(d.content for d in self.documents if d.document_id=='adoc'));renamed=json.loads(json.dumps(original));record=next(e for e in renamed['modules'][0]['elements'] if e['id']=='A');record['name']='RenamedA';record['members'].reverse()
        document=CatalogDocument('adoc','r2',json.dumps(renamed).encode());prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        accepted=a.accept_in_transaction(t,prepared,request_key='rename-reorder');self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration)
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(),objects);self.assertEqual(self.admin.execute('SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall(),keys)
        self.documents=tuple(document if d.document_id=='adoc' else d for d in self.documents);c,h,a,t=self.consumer()
        found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value;self.assertIsInstance(found,ObjectFound);self.assertEqual((found.object.identity.id,found.object.identity.type_id,found.object.version),(identity.id,identity.type_id,1));self.assertNotEqual(found.object.identity.definition_pin,identity.definition_pin)
        lookup=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=(TextValue(kind='string',text='value'),TextValue(kind='string',text='one')),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'));self.assertIsInstance(lookup.value,ObjectFound);self.assertEqual(lookup.value.object.identity.id,identity.id)
        query=a.query_in_transaction(t,sql='SELECT a.* FROM "RenamedA" a',document_ids=('adoc',));self.assertIsInstance(query.value,QueryRows,repr(query.value));self.assertEqual(query.value.columns,('A-value','A-label'));self.assertEqual(query.value.rows,(('value','one'),))
        context=a.group_context_in_transaction(t).value
        changed=self.apply(a,t,context.input((UpdateObject(target=StoredObjectReference(identity=found.object.identity),set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text='changed')),),unset=()),UpdateEdge(target=StoredObjectReference(identity=edge),set=(AuthoredValue(name='note',value=TextValue(kind='string',text='changed')),),unset=())),MapValue(entries=())),context.request('post-rename-update'));self.assertIsInstance(changed,GroupSuccess,repr(changed))
        h.detach();c.commit();c,h,a,t=self.consumer()
        for kind,entity_id,definition in [('object',identity.id,'A'),('edge',edge.id,'A-B')]:
            history=a.reconstruct_in_transaction(t,entity=HistoryEntity(kind=kind,document_id='adoc',module_id='m',definition_id=definition,id=int(entity_id)),version=2).value;self.assertIsInstance(history,HistoricalRecord,repr(history))
        replay=a.apply_in_transaction(t,semantic,request,documents=original_documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'));self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
        self.assertEqual(a.report_in_transaction(t,revision=1).value.original_bytes,first_report)
        h.detach();c.commit();c,h,a,t=self.consumer()
        restored=CatalogDocument('adoc','r3',json.dumps(original).encode());prepared=a.prepare_catalog((restored,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'));self.assertIsInstance(a.accept_in_transaction(t,prepared,request_key='restore-labels').value,CatalogRegistration)
        query=a.query_in_transaction(t,sql='SELECT a.* FROM "A" a',document_ids=('adoc',));self.assertIsInstance(query.value,QueryRows,repr(query.value));self.assertEqual(query.value.columns,('A-label','A-value'));self.assertEqual(query.value.rows,(('one','changed'),))
        h.detach();c.commit()
