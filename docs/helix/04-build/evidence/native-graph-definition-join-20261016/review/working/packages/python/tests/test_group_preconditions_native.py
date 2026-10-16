"""Basic public precondition and typed-refusal adopter workflows."""
from dataclasses import replace
from truss import Ok
from truss.contracts import MapValue,TextValue
from truss.groups import (ObjectExists,KeyAbsent,PropertyEquals,RelationshipAbsent,RelationshipCount,
    UpdateObject,StoredObjectReference,AuthoredValue,GroupSuccess,GroupFailed,PreconditionFailed,
    InvalidGroupInput,UnauthorizedPerson,CommittedReceiptReplay)
import test_object_mutations_native as mutation_tests

class GroupPreconditionTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def initialized(self):
        connection,host,assembly,tx=self.ready()
        result,_,_=self.run_group(assembly,tx,(self.create(),self.create(label='two',value='other',alias='b',record='B')),'initial')
        self.assertIsInstance(result,GroupSuccess)
        a,b=(v.identity for v in result.response.semantic.results)
        relation=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B')
        self.assertIsInstance(relation,Ok);self.assertIsNotNone(relation.value)
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        return connection,host,assembly,tx,a,b,relation.value.definition_pin

    def condition_group(self,assembly,tx,identity,conditions,key):
        context=assembly.group_context_in_transaction(tx).value
        operation=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='new')),),unset=(),expected_version='1')
        input=context.input((operation,),MapValue(entries=()),preconditions=conditions);request=context.request(key)
        result=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        if not isinstance(result,Ok):self.fail(repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        return result.value,input,request

    def test_all_failures_keep_ids_reasons_and_no_group_effects(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        counts='SELECT (SELECT count(*) FROM truss.runtime_object_attempt),(SELECT count(*) FROM truss.request_receipt),(SELECT count(*) FROM truss.request_receipt_route_guard),(SELECT count(*) FROM truss.key_bucket_guard),(SELECT count(*) FROM truss.journal)'
        before=self.admin.execute(counts).fetchone()
        conditions=(ObjectExists(id='missing',reason='must exist',target=replace(a,id='99999999')),
            KeyAbsent(id='unused',reason='new key allowed',type_definition_pin=a.definition_pin,key_id='a-primary',values=(TextValue(kind='string',text='value'),TextValue(kind='string',text='unused'))),
            KeyAbsent(id='duplicate',reason='key not taken',type_definition_pin=a.definition_pin,key_id='a-primary',values=(TextValue(kind='string',text='value'),TextValue(kind='string',text='one'))),
            PropertyEquals(id='value',reason='still original',target=a,name='A-label',value=TextValue(kind='string',text='wrong')),
            RelationshipAbsent(id='unlinked',reason='not already linked',relationship_definition_pin=pin,source=a,target=b),
            RelationshipCount(id='count',reason='has a neighbor',relationship_definition_pin=pin,anchor=a,direction='outgoing',minimum='1'))
        result,_,_=self.condition_group(assembly,tx,a,conditions,'failed-preconditions')
        self.assertIsInstance(result,GroupFailed);self.assertIsInstance(result.failure,PreconditionFailed)
        self.assertEqual([(f.condition_id,f.reason) for f in result.failure.failures],[(c.id,c.reason) for c in conditions if c.id in ('missing','duplicate','value','count')])
        self.assertEqual(dict(self.read(assembly,tx,a).object.values)['A-label'],'one')
        self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        host.detach();connection.commit();self.assertEqual(self.admin.execute(counts).fetchone(),before)

    def test_success_replay_and_explicit_invalid_unauthorized(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        conditions=(ObjectExists(id='exists',reason='must exist',target=a),
            KeyAbsent(id='new-key',reason='free live key',type_definition_pin=a.definition_pin,key_id='a-primary',values=(TextValue(kind='string',text='value'),TextValue(kind='string',text='new'))),
            PropertyEquals(id='old-value',reason='still original',target=a,name='A-label',value=TextValue(kind='string',text='one')),
            RelationshipAbsent(id='unlinked',reason='not linked',relationship_definition_pin=pin,source=a,target=b),
            RelationshipCount(id='count',reason='no neighbors',relationship_definition_pin=pin,anchor=a,direction='outgoing',maximum='0'))
        invalid,_,_=self.condition_group(assembly,tx,a,(replace(conditions[1],key_id='missing-key'),),'invalid')
        self.assertIsInstance(invalid.failure,InvalidGroupInput)
        result,input,request=self.condition_group(assembly,tx,a,conditions,'conditional-update')
        self.assertIsInstance(result,GroupSuccess);self.assertEqual(dict(self.read(assembly,tx,a).object.values)['A-label'],'new')
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        # Receipt recovery must not recompile original key conditions.
        replay=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/no-owner-producer-needed-for-replay')
        self.assertIsInstance(replay,Ok);self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
        self.assertEqual(replay.value.response.semantic,result.response.semantic)
        host.detach();connection.rollback();self.admin.execute('REVOKE group_writer FROM consumer')
        connection,host,assembly,tx=self.consumer()
        refused=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable='/no-owner-producer-needed-for-replay')
        self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value.failure,UnauthorizedPerson)
        self.assertEqual(connection.execute('SELECT 42').fetchone(),(42,))
        host.detach();connection.rollback()
