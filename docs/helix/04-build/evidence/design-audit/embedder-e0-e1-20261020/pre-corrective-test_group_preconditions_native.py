# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public precondition and typed-refusal adopter workflows."""
from dataclasses import replace
import json
import psycopg
from truss import Ok
from truss.contracts import MapValue,TextValue,ProfilePin
from truss.groups import (ObjectExists,KeyAbsent,PropertyEquals,RelationshipAbsent,RelationshipCount,
    UpdateObject,StoredObjectReference,AuthoredValue,GroupSuccess,GroupFailed,PreconditionFailed,
    InvalidGroupInput,UnauthorizedPerson,CommittedReceiptReplay,GroupUnavailable)
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

    def test_owned_153_preconditions_accept_51_objects_times_three(self):
        """@covers US-040-AC1 / @covers US-040-AC2: bounded condition batches commit atomically."""
        connection,host,assembly,tx,a,b,pin=self.initialized()
        context=assembly.group_context_in_transaction(tx).value
        creations=tuple(self.create(label=f'condition-target-{index:02d}',value='before',alias=f'target-{index:02d}')
            for index in range(51))
        created=assembly.apply_in_transaction(tx,context.input(creations,MapValue(entries=())),
            context.request('condition-targets'),documents=self.documents)
        self.assertIsInstance(created,Ok,repr(created));self.assertIsInstance(created.value,GroupSuccess,repr(created))
        identities=tuple(result.identity for result in created.value.response.semantic.results)
        host.detach();connection.commit()

        connection,host,assembly,tx=self.consumer()
        context=assembly.group_context_in_transaction(tx).value
        conditions=tuple(condition for object_index,identity in enumerate(identities) for condition in (
            ObjectExists(id=f'exists-{object_index:02d}',reason='target remains present',target=identity),
            PropertyEquals(id=f'label-{object_index:02d}',reason='original label remains',target=identity,
                name='A-label',value=TextValue(kind='string',text=f'condition-target-{object_index:02d}')),
            KeyAbsent(id=f'key-{object_index:02d}',reason='alternate key remains free',
                type_definition_pin=identity.definition_pin,key_id='a-primary',
                values=(TextValue(kind='string',text=f'condition-target-{object_index:02d}'),
                    TextValue(kind='string',text='unallocated')))))
        operation=UpdateObject(target=StoredObjectReference(identity=identities[0]),
            set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='after-conditions')),),
            unset=(),expected_version='1')
        result=assembly.apply_in_transaction(tx,context.input((operation,),MapValue(entries=()),preconditions=conditions),
            context.request('153-preconditions'),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,GroupSuccess,repr(result))
        host.detach();connection.commit()

    def test_owned_precondition_ceiling_plus_one_refuses_in_native(self):
        """@covers US-040-AC2: over-ceiling input refuses without group effects."""
        connection,host,assembly,tx,a,b,pin=self.initialized()
        context=assembly.group_context_in_transaction(tx).value
        conditions=tuple(ObjectExists(id=f'ceiling-{index:04d}',reason='bounded native condition',target=a)
            for index in range(3073))
        operation=UpdateObject(target=StoredObjectReference(identity=a),
            set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='must-not-apply')),),
            unset=(),expected_version='1')
        original=context.input((operation,),MapValue(entries=()),preconditions=conditions)
        request=context.request('condition-ceiling-plus-one')
        from truss._group_runtime import _bytes,_wire
        from truss.catalog_runtime import _release
        manifest,digest,_=_release()
        original_input=_bytes(_wire(original))
        self.assertLess(len(original_input),1048576)
        original_documents=_bytes([{'documentId':d.document_id,'sourceText':d.content.decode('utf8')} for d in self.documents])
        original_request=_bytes(_wire(request))
        before=self.admin.execute('SELECT (SELECT count(*) FROM truss.runtime_object_attempt),(SELECT count(*) FROM truss.request_receipt),(SELECT count(*) FROM truss.journal)').fetchone()
        host.detach();connection.commit()
        native=json.loads(bytes(connection.execute('SELECT truss.apply_group(%s,%s,%s,%s,%s)',
            (original_input,original_documents,original_request,manifest['releaseId'],digest)).fetchone()[0]))
        self.assertEqual((native['outcome'],native['reason']),('unavailable','resource'))
        malformed=_wire(original)
        malformed['preconditions']={}
        wrong_shape=_bytes(malformed)
        invalid=json.loads(bytes(connection.execute('SELECT truss.apply_group(%s,%s,%s,%s,%s)',
            (wrong_shape,original_documents,original_request,manifest['releaseId'],digest)).fetchone()[0]))
        self.assertEqual((invalid['outcome'],invalid['code'],invalid['nativeState']),('failed','invalid_input','22023'))
        connection.commit()
        self.assertEqual(self.admin.execute('SELECT (SELECT count(*) FROM truss.runtime_object_attempt),(SELECT count(*) FROM truss.request_receipt),(SELECT count(*) FROM truss.journal)').fetchone(),before)

    def test_owned_3072_preconditions_succeed(self):
        """@covers US-040-AC1: the full owned condition ceiling is accepted."""
        connection,host,assembly,tx,a,b,pin=self.initialized()
        context=assembly.group_context_in_transaction(tx).value
        conditions=tuple(ObjectExists(id=f'c{index:04d}',reason='r',target=a) for index in range(3072))
        operation=UpdateObject(target=StoredObjectReference(identity=a),
            set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='after-3072')),),
            unset=(),expected_version='1')
        result=assembly.apply_in_transaction(tx,context.input((operation,),MapValue(entries=()),preconditions=conditions),
            context.request('condition-ceiling'),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,GroupSuccess,repr(result))
        self.assertEqual(dict(self.read(assembly,tx,a).object.values)['A-label'],'after-3072')
        host.detach();connection.commit()

    def test_middle_false_condition_and_duplicate_ids_leave_prestate_unchanged(self):
        """@covers US-040-AC2: condition failure and invalid IDs preserve pre-state."""
        connection,host,assembly,tx,a,b,pin=self.initialized()
        counts='SELECT (SELECT count(*) FROM truss.runtime_object_attempt),(SELECT count(*) FROM truss.request_receipt),(SELECT count(*) FROM truss.journal)'
        before=self.admin.execute(counts).fetchone()
        context=assembly.group_context_in_transaction(tx).value
        operation=UpdateObject(target=StoredObjectReference(identity=a),
            set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='must-not-apply')),),
            unset=(),expected_version='1')
        conditions=(ObjectExists(id='first',reason='present',target=a),
            PropertyEquals(id='middle-fails',reason='wrong prior value',target=a,name='A-label',value=TextValue(kind='string',text='wrong')),
            ObjectExists(id='last',reason='present',target=a))
        failed=assembly.apply_in_transaction(tx,context.input((operation,),MapValue(entries=()),preconditions=conditions),
            context.request('middle-condition-fails'),documents=self.documents)
        self.assertIsInstance(failed,Ok,repr(failed));self.assertIsInstance(failed.value,GroupFailed,repr(failed))
        self.assertIsInstance(failed.value.failure,PreconditionFailed)
        self.assertEqual(tuple(item.condition_id for item in failed.value.failure.failures),('middle-fails',))
        self.assertEqual(dict(self.read(assembly,tx,a).object.values)['A-label'],'one')

        duplicate=(ObjectExists(id='same-id',reason='present',target=a),ObjectExists(id='same-id',reason='present',target=a))
        invalid=assembly.apply_in_transaction(tx,context.input((operation,),MapValue(entries=()),preconditions=duplicate),
            context.request('duplicate-condition-id'),documents=self.documents)
        self.assertIsInstance(invalid,Ok,repr(invalid));self.assertIsInstance(invalid.value,GroupFailed,repr(invalid))
        self.assertIsInstance(invalid.value.failure,InvalidGroupInput)
        self.assertEqual(dict(self.read(assembly,tx,a).object.values)['A-label'],'one')
        host.detach();connection.commit();self.assertEqual(self.admin.execute(counts).fetchone(),before)

    def test_legacy_precondition_128_accepts_and_129_refuses(self):
        """@covers US-040-AC1 / @covers US-040-AC2: legacy inventory retains its 128 limit."""
        connection,host,assembly,tx,a,b,pin=self.initialized()
        context=assembly.group_context_in_transaction(tx).value
        legacy=ProfilePin(identity='truss-rootless-scalar-graph',version='0.4',
            sha256='b814eb5b33ff59340d2f9bd13866ccb97d49f42fd38ce1e9c97facab5668a2f8')
        def candidate(count,version):
            conditions=tuple(ObjectExists(id=f'legacy-{index:03d}',reason='r',target=a) for index in range(count))
            operation=UpdateObject(target=StoredObjectReference(identity=a),
                set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text=f'legacy-{count}')),),
                unset=(),expected_version=version)
            return replace(context.input((operation,),MapValue(entries=()),preconditions=conditions),mutation_profile=legacy)
        # This retired profile is intentionally not admitted for group execution.
        # Exercise its retained SQL inventory ceiling directly under the current actor.
        self.admin.execute('GRANT EXECUTE ON FUNCTION truss.runtime_condition_inventory(jsonb) TO consumer')
        self.admin.commit()
        def revoke_inventory_access():
            self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.runtime_condition_inventory(jsonb) FROM consumer')
            self.admin.commit()
        self.addCleanup(revoke_inventory_access)
        from truss._group_runtime import _wire
        accepted_input=json.dumps(_wire(candidate(128,'1')))
        inventory=connection.execute('SELECT truss.runtime_condition_inventory(%s::jsonb)',(accepted_input,)).fetchone()[0]
        self.assertEqual(len(inventory),128)
        refused_input=json.dumps(_wire(candidate(129,'1')))
        connection.execute('SAVEPOINT legacy_inventory_ceiling')
        with self.assertRaises(psycopg.errors.ProgramLimitExceeded) as raised:
            connection.execute('SELECT truss.runtime_condition_inventory(%s::jsonb)',(refused_input,))
        self.assertEqual(getattr(raised.exception,'sqlstate',None),'54000')
        connection.execute('ROLLBACK TO SAVEPOINT legacy_inventory_ceiling')
        connection.execute('RELEASE SAVEPOINT legacy_inventory_ceiling')
        host.detach();connection.rollback()
        self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.runtime_condition_inventory(jsonb) FROM consumer')
        self.admin.commit()
