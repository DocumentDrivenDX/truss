"""Basic adopter workflows for the public object mutation interface."""
from truss import Ok,ObjectFound,ObjectNotFound
from truss.contracts import MapValue,TextValue
from truss.groups import (UpdateObject,Delete,StoredObjectReference,AliasObjectReference,AuthoredValue,
    RequestNone,GroupSuccess,GroupFailed,Changed,Unchanged,Deleted,CommittedReceiptReplay)
import test_group_create_native as group_tests

class ObjectMutationTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def run_group(self,assembly,tx,operations,request_id=None):
        context=assembly.group_context_in_transaction(tx).value
        input=context.input(operations,MapValue(entries=()))
        request=RequestNone() if request_id is None else context.request(request_id)
        result=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        if not isinstance(result,Ok):self.fail(repr(result)+" "+str(assembly._host._custody.last_attempt.error))
        return result.value,input,request

    def read(self,assembly,tx,identity):
        result=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(result,Ok);return result.value

    def test_create_update_read_dryrun_delete_and_durable_retry(self):
        connection,host,assembly,tx=self.ready()
        result,_,_=self.run_group(assembly,tx,(self.create(),),'create')
        self.assertIsInstance(result,GroupSuccess);identity=result.response.semantic.results[0].identity
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        identity=self.read(assembly,tx,identity).object.identity
        update=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='two')),),unset=(),expected_version='1')
        result,update_input,update_request=self.run_group(assembly,tx,(update,),'update')
        self.assertIsInstance(result,GroupSuccess);self.assertIsInstance(result.response.semantic.results[0],Changed)
        self.assertEqual(result.response.semantic.results[0].version,'2')
        self.assertEqual(dict(self.read(assembly,tx,identity).object.values)['A-label'],'two')
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        replay=assembly.apply_in_transaction(tx,update_input,update_request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun').value
        self.assertIsInstance(replay.response,CommittedReceiptReplay);self.assertEqual(replay.response.semantic,result.response.semantic)
        noop=UpdateObject(target=StoredObjectReference(identity=identity),set=update.set,unset=(),expected_version='2')
        before=self.read(assembly,tx,identity).object
        nooped,_,_=self.run_group(assembly,tx,(noop,),'noop')
        self.assertIsInstance(nooped.response.semantic.results[0],Unchanged);self.assertEqual(self.read(assembly,tx,identity).object,before)
        stale,_,_=self.run_group(assembly,tx,(update,))
        self.assertIsInstance(stale,GroupFailed);self.assertEqual(self.read(assembly,tx,identity).object,before)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        dry=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='dry')),),unset=(),expected_version='2')
        self.assertIsInstance(self.run_group(assembly,tx,(dry,))[0],GroupSuccess)
        host.detach();connection.rollback();connection,host,assembly,tx=self.consumer()
        self.assertEqual(dict(self.read(assembly,tx,identity).object.values)['A-label'],'two')
        deletion=Delete(operation='delete_object',target=StoredObjectReference(identity=identity),expected_version='2')
        result,delete_input,delete_request=self.run_group(assembly,tx,(deletion,),'delete')
        self.assertIsInstance(result.response.semantic.results[0],Deleted);self.assertIsInstance(self.read(assembly,tx,identity),ObjectNotFound)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        for original_input,request in ((delete_input,delete_request),(update_input,update_request)):
            replay=assembly.apply_in_transaction(tx,original_input,request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
            self.assertIsInstance(replay,Ok);self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
        self.assertIsInstance(self.read(assembly,tx,identity),ObjectNotFound)
        host.detach();connection.rollback()

    def test_mixed_alias_batch_and_failed_batch_are_atomic(self):
        connection,host,assembly,tx=self.ready()
        result,_,_=self.run_group(assembly,tx,(self.create(alias='new'),
            UpdateObject(target=AliasObjectReference(alias='new'),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='changed')),),unset=(),expected_version='1'),
            Delete(operation='delete_object',target=AliasObjectReference(alias='new'),expected_version='2')),'mixed')
        self.assertIsInstance(result,GroupSuccess)
        self.assertEqual([r.outcome for r in result.response.semantic.results],['created','changed','deleted'])
        identity=result.response.semantic.results[0].identity
        self.assertIsInstance(self.read(assembly,tx,identity),ObjectNotFound)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        result,_,_=self.run_group(assembly,tx,(self.create(label='kept',value='other'),),'kept')
        identity=result.response.semantic.results[0].identity
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        result,_,_=self.run_group(assembly,tx,(
            UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='temporary')),),unset=(),expected_version='1'),
            Delete(operation='delete_object',target=StoredObjectReference(identity=identity),expected_version='1')))
        self.assertIsInstance(result,GroupFailed)
        self.assertEqual(dict(self.read(assembly,tx,identity).object.values)['A-label'],'kept')
        self.assertEqual(self.read(assembly,tx,identity).object.version,1)
        host.detach();connection.commit()
