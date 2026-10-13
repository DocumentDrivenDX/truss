"""Missing/null refusal and empty/nonempty repair for flat containers."""
import json,os
from truss import CatalogDocument,CatalogAcceptanceRefused,CatalogRegistration,ObjectFound,QueryRows,Ok
from truss.contracts import NullValue,SequenceValue,MapValue,TextValue
from truss.groups import CreateObject,RootlessOwnership,AuthoredValue,UpdateObject,StoredObjectReference,GroupSuccess,CommittedReceiptReplay
import test_scalar_containers_native as base

class ContainerRequiredEvolutionTests(base.ScalarContainerTests):
    for _name in tuple(n for n in dir(base.ScalarContainerTests) if n.startswith('test_')):locals()[_name]=None
    def test_missing_null_repair_empty_accept_read_and_retry(self):
        c,h,a,t=self.ready_containers();original_documents=self.documents
        missing=self.create('missing',value='missing',alias='missing')
        null=CreateObject(type_definition_pin=self.types[('adoc','A')].definition_pin,values=self.create('null',value='null').values+(AuthoredValue(name='tags',value=NullValue()),AuthoredValue(name='amounts',value=NullValue())),ownership=RootlessOwnership(),alias='null')
        created,semantic,request=self.run_group(a,t,(missing,null),'original-containers');self.assertIsInstance(created,GroupSuccess);identities=tuple(r.identity for r in created.response.semantic.results);h.detach();c.commit();self.admin.execute('GRANT '+self.installation.registrar_role+' TO consumer WITH SET FALSE');c,h,a,t=self.consumer()
        doc=json.loads(next(d.content for d in self.documents if d.document_id=='adoc'))
        for field in doc['modules'][0]['elements']:
            if field['id'] in ('tags','amounts'):field['nullability']='required'
        document=CatalogDocument('adoc','r2',json.dumps(doc).encode());prepared=a.prepare_catalog((document,),source_version=self.source_version,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        refused=a.accept_in_transaction(t,prepared,request_key='required-containers-missing');self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,CatalogAcceptanceRefused);self.assertEqual({(v.field_id,v.rule,v.affected_object_count) for v in refused.value.violations},{('tags','property.required',2),('amounts','property.required',2)})
        ops=tuple(UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='tags',value=SequenceValue(items=() if index==0 else (TextValue(kind='string',text='x'),))),AuthoredValue(name='amounts',value=MapValue(entries=()) if index==0 else self.amounts())),unset=()) for index,identity in enumerate(identities))
        fixed,_,_=self.run_group(a,t,ops,'repair-containers');self.assertIsInstance(fixed,GroupSuccess);h.detach();c.commit();c,h,a,t=self.consumer()
        before=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall()
        accepted=a.accept_in_transaction(t,prepared,request_key='required-containers-compatible');self.assertIsInstance(accepted,Ok,repr(accepted));self.assertIsInstance(accepted.value,CatalogRegistration,repr(accepted));h.detach();c.commit();c,h,a,t=self.consumer()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(),before);self.assertTrue(a.accept_in_transaction(t,prepared,request_key='required-containers-compatible').value.replayed)
        for index,identity in enumerate(identities):
            found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id)).value;self.assertIsInstance(found,ObjectFound);self.assertEqual(found.object.version,2);self.assertEqual(dict(found.object.values)['tags'],ops[index].set[0].value);self.assertEqual(dict(found.object.values)['amounts'],ops[index].set[1].value)
        rows=a.query_in_transaction(t,sql='SELECT a.tags,a.amounts FROM "A" a WHERE a."A-label" = :label',parameters={'label':'missing'},document_ids=('adoc',));self.assertIsInstance(rows.value,QueryRows,repr(rows));self.assertEqual(rows.value.rows,(((),{}),))
        replay=a.apply_in_transaction(t,semantic,request,documents=original_documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'));self.assertIsInstance(replay.value.response,CommittedReceiptReplay);h.detach();c.commit()

class ContainerRequiredEvolution08Tests(ContainerRequiredEvolutionTests):
    source_version='0.8.0'
