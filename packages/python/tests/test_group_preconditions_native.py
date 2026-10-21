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
        unstamped=json.loads(bytes(connection.execute('SELECT truss.apply_group(%s,%s,%s,%s,%s)',
            (original_input,original_documents,original_request,manifest['releaseId'],digest)).fetchone()[0]))
        self.assertEqual((unstamped['outcome'],unstamped['reason']),('unavailable','profile'))
        # Adopt a latest host transaction, then bypass host input validation to
        # exercise the native resource guard under the required cohort stamp.
        connection,host,assembly,tx=self.consumer()
        native=json.loads(bytes(connection.execute('SELECT truss.apply_group(%s,%s,%s,%s,%s)',
            (original_input,original_documents,original_request,manifest['releaseId'],digest)).fetchone()[0]))
        self.assertEqual((native['outcome'],native['reason']),('unavailable','resource'))
        malformed=_wire(original)
        malformed['preconditions']={}
        wrong_shape=_bytes(malformed)
        invalid=json.loads(bytes(connection.execute('SELECT truss.apply_group(%s,%s,%s,%s,%s)',
            (wrong_shape,original_documents,original_request,manifest['releaseId'],digest)).fetchone()[0]))
        self.assertEqual((invalid['outcome'],invalid['code'],invalid['nativeState']),('failed','invalid_input','22023'))
        small=_wire(context.input((operation,),MapValue(entries=()),
            preconditions=(ObjectExists(id='valid-target',reason='present',target=a),)))
        valid_target=small['preconditions'][0]
        missing_target=dict(valid_target)
        missing_target['id']='missing-target'
        missing_target.pop('target')
        invalid_variants=[]
        for case,field,value in (
            ('bad-pin','definitionPin','0'*64),
            ('bad-owner','owner',{'documentId':'adoc','moduleId':'other'}),
            ('bad-type-id','typeId','999999999'),
            ('bad-id','id','0'),
            ('extra-field','futureExtension','unexpected'),
        ):
            invalid_identity=json.loads(json.dumps(valid_target))
            invalid_identity['id']=f'invalid-{case}'
            invalid_identity['target'][field]=value
            invalid_variants.append((case,(valid_target,invalid_identity)))
        cases=(('missing-first',(missing_target,valid_target)),
            ('missing-after-valid',(valid_target,missing_target)),*invalid_variants)
        for case,preconditions in cases:
            candidate=dict(small)
            candidate['preconditions']=list(preconditions)
            invalid_target=json.loads(bytes(connection.execute('SELECT truss.apply_group(%s,%s,%s,%s,%s)',
                (_bytes(candidate),original_documents,original_request,manifest['releaseId'],digest)).fetchone()[0]))
            self.assertEqual((case,invalid_target['outcome'],invalid_target['code'],invalid_target['nativeState']),
                (case,'failed','invalid_input','22023'))
        host.detach();connection.commit()
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

    def test_owned_3072_mixed_preconditions_succeed(self):
        """@covers US-040-AC1: mixed predicates cover the full owned condition ceiling."""
        connection,host,assembly,tx,a,b,pin=self.initialized()
        context=assembly.group_context_in_transaction(tx).value
        conditions=[]
        for index in range(1024):
            identity=a if index%2==0 else b
            record='A' if index%2==0 else 'B'
            label='one' if record=='A' else 'two'
            value='value' if record=='A' else 'other'
            conditions.extend((
                ObjectExists(id=f'e{index:04d}',reason='r',target=identity),
                PropertyEquals(id=f'l{index:04d}',reason='r',target=identity,
                    name=f'{record}-label',value=TextValue(kind='string',text=label)),
                PropertyEquals(id=f'v{index:04d}',reason='r',target=identity,
                    name=f'{record}-value',value=TextValue(kind='string',text=value)),
            ))
        operation=UpdateObject(target=StoredObjectReference(identity=a),
            set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='after-mixed-3072')),),
            unset=(),expected_version='1')
        input=context.input((operation,),MapValue(entries=()),preconditions=tuple(conditions))
        from truss._group_runtime import _bytes,_wire
        self.assertLess(len(_bytes(_wire(input))),1048576)
        result=assembly.apply_in_transaction(tx,input,
            context.request('mixed-3072-preconditions'),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,GroupSuccess,repr(result))
        self.assertEqual(dict(self.read(assembly,tx,a).object.values)['A-label'],'after-mixed-3072')
        b_read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='B',object_id=int(b.id))
        self.assertIsInstance(b_read,Ok,repr(b_read))
        self.assertEqual(dict(b_read.value.object.values)['B-label'],'two')
        self.assertEqual(dict(b_read.value.object.values)['B-value'],'other')
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
        # Use a synthetic test-only component under the original caller; this does not readmit legacy execution.
        from truss._group_runtime import _wire
        accepted_input=json.dumps(_wire(candidate(128,'1')))
        refused_input=json.dumps(_wire(candidate(129,'1')))
        counts=('SELECT (SELECT count(*) FROM truss.runtime_object_attempt),'
            '(SELECT count(*) FROM truss.request_receipt),(SELECT count(*) FROM truss.journal),'
            '(SELECT count(*) FROM truss.object),(SELECT count(*) FROM truss.edge)')
        before=self.admin.execute(counts).fetchone()

        def drop_test_wrapper():
            self.admin.rollback()
            self.admin.execute('DROP FUNCTION IF EXISTS public.truss_test_legacy_condition_count(jsonb)')
            self.admin.commit()
        self.addCleanup(drop_test_wrapper)

        try:
            wrapper_sql = """
                CREATE FUNCTION public.truss_test_legacy_condition_count(input jsonb)
                RETURNS integer
                LANGUAGE plpgsql
                SECURITY DEFINER
                SET search_path=pg_catalog,pg_temp
                SET row_security=off
                AS $$
                BEGIN
                  PERFORM truss.runtime_person(false);
                  RETURN jsonb_array_length(truss.runtime_condition_inventory(input));
                END;
                $$
            """
            self.admin.execute(wrapper_sql)
            self.admin.execute(psycopg.sql.SQL(
                'ALTER FUNCTION public.truss_test_legacy_condition_count(jsonb) OWNER TO {}'
            ).format(psycopg.sql.Identifier(self.installation.owner_role)))
            self.admin.execute('REVOKE ALL ON FUNCTION public.truss_test_legacy_condition_count(jsonb) FROM PUBLIC')
            self.admin.execute('GRANT EXECUTE ON FUNCTION public.truss_test_legacy_condition_count(jsonb) TO consumer')
            self.admin.commit()

            accepted_count=connection.execute(
                'SELECT public.truss_test_legacy_condition_count(%s::jsonb)',(accepted_input,)
            ).fetchone()[0]
            self.assertEqual(accepted_count,128)
            connection.execute('SAVEPOINT legacy_inventory_ceiling')
            with self.assertRaises(psycopg.errors.ProgramLimitExceeded) as raised:
                connection.execute(
                    'SELECT public.truss_test_legacy_condition_count(%s::jsonb)',(refused_input,)
                )
            self.assertEqual(getattr(raised.exception,'sqlstate',None),'54000')
            connection.execute('ROLLBACK TO SAVEPOINT legacy_inventory_ceiling')
            connection.execute('RELEASE SAVEPOINT legacy_inventory_ceiling')
        finally:
            host.detach()
            connection.rollback()
            drop_test_wrapper()

        self.assertEqual(self.admin.execute(counts).fetchone(),before)
