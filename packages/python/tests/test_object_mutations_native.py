"""Basic adopter workflows for the public object mutation interface."""
import os
import psycopg
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
        result=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        if not isinstance(result,Ok):self.fail(repr(result)+" "+str(assembly._host._custody.last_attempt.error))
        return result.value,input,request

    def read(self,assembly,tx,identity):
        result=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(result,Ok);return result.value

    def test_unnamed_fields_register_create_update_and_reopen(self):
        def unnamed(source):
            for module in source['modules']:
                for field in module['elements']:
                    if field['kind']=='field':
                        field.pop('name',None)
        connection,host,assembly,tx=self.ready(unnamed,document_ids=('adoc',))
        created,_,_=self.run_group(assembly,tx,(self.create(),),'unnamed-create')
        self.assertIsInstance(created,GroupSuccess,repr(created))
        identity=created.response.semantic.results[0].identity
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(dict(self.read(assembly,tx,identity).object.values)['A-label'],'one')
        update=UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='updated')),),unset=())
        changed,_,_=self.run_group(assembly,tx,(update,),'unnamed-update')
        self.assertIsInstance(changed,GroupSuccess,repr(changed))
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(dict(self.read(assembly,tx,identity).object.values)['A-label'],'updated')
        host.detach();connection.rollback()

    def test_global_journal_check_ignores_caller_flags_and_prior_constraint_flush(self):
        connection,host,assembly,tx=self.ready()
        # Administrative fault injection adds a fact for an unrelated entity.
        # Per-object validation still passes; whole-transaction closure must fail.
        self.admin.execute("""CREATE FUNCTION public.inject_unrelated_journal() RETURNS void
         LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
          INSERT INTO truss.journal
          SELECT (jsonb_populate_record(NULL::truss.journal,to_jsonb(j)||
           jsonb_build_object('seq',nextval('truss.journal_seq'),'entity_id',j.entity_id+1000000))).*
          FROM truss.journal j WHERE j.xid=pg_current_xact_id() LIMIT 1
         $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.inject_unrelated_journal()')
        for mode in ('caller_flags','constraint_flush'):
            with self.subTest(mode=mode):
                if mode=='caller_flags':
                    connection.execute("SET LOCAL truss.object_commit_checked='1'")
                    connection.execute("SET LOCAL truss.create_journal_checked='1'")
                first,_,_=self.run_group(assembly,tx,(self.create(),))
                self.assertIsInstance(first,GroupSuccess)
                if mode=='constraint_flush':
                    connection.execute('SET CONSTRAINTS ALL IMMEDIATE')
                    connection.execute('SET CONSTRAINTS ALL DEFERRED')
                    second,_,_=self.run_group(assembly,tx,(self.create(label='two',value='other'),))
                    self.assertIsInstance(second,GroupSuccess)
                connection.execute('SELECT public.inject_unrelated_journal()')
                host.detach()
                with self.assertRaisesRegex(psycopg.errors.ObjectNotInPrerequisiteState,'complete .*journal required'):
                    connection.commit()
                connection.rollback()
                self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
                connection,host,assembly,tx=self.consumer()

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
        replay=assembly.apply_in_transaction(tx,update_input,update_request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun')).value
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
            replay=assembly.apply_in_transaction(tx,original_input,request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
            self.assertIsInstance(replay,Ok);self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
        self.assertIsInstance(self.read(assembly,tx,identity),ObjectNotFound)
        host.detach();connection.rollback()

    def test_mixed_alias_batch_and_failed_batch_are_atomic(self):
        connection,host,assembly,tx=self.ready()
        result,mixed_input,mixed_request=self.run_group(assembly,tx,(self.create(alias='new'),
            UpdateObject(target=AliasObjectReference(alias='new'),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='changed')),),unset=(),expected_version='1'),
            Delete(operation='delete_object',target=AliasObjectReference(alias='new'),expected_version='2')),'mixed')
        self.assertIsInstance(result,GroupSuccess)
        self.assertEqual([r.outcome for r in result.response.semantic.results],['created','changed','deleted'])
        identity=result.response.semantic.results[0].identity
        self.assertIsInstance(self.read(assembly,tx,identity),ObjectNotFound)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        replay=assembly.apply_in_transaction(tx,mixed_input,mixed_request,documents=self.documents,
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(replay,Ok);self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
        self.assertEqual(replay.value.response.semantic.results,result.response.semantic.results)
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

    def test_writer_revoked_after_attempt_constraint_flush_still_aborts(self):
        connection,host,assembly,tx=self.ready()
        created_input,_=self.input(assembly,tx)
        created=self.apply(assembly,tx,created_input,RequestNone())
        self.assertIsInstance(created,GroupSuccess)
        identity=created.response.semantic.results[0].identity
        host.detach();connection.commit()
        original=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o WHERE id=%s AND type_id=%s',(int(identity.id),int(identity.type_id))).fetchone()
        connection,host,assembly,tx=self.consumer()
        change=UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text='pending-change')),),unset=())
        changed_input,_=self.input(assembly,tx,(change,),action='update')
        self.assertIsInstance(self.apply(assembly,tx,changed_input,RequestNone()),GroupSuccess)
        connection.execute('SET CONSTRAINTS truss.runtime_object_attempt_commit IMMEDIATE')
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        self.admin.execute('REVOKE group_writer FROM consumer')
        host.detach()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            connection.commit()
        connection.rollback()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o WHERE id=%s AND type_id=%s',(int(identity.id),int(identity.type_id))).fetchone(),original)
