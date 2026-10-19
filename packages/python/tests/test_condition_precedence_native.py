# SPDX-License-Identifier: MIT OR Apache-2.0
"""Declared failed conditions win over operation failures on the same locked prestate."""
from dataclasses import replace
from truss import Ok
from truss.contracts import MapValue,TextValue
from truss.groups import (ObjectExists,KeyAbsent,UpdateObject,StoredObjectReference,
    GroupFailed,PreconditionFailed,AliasObjectReference,CreateEdge,NullOrderKey,
    RelationshipCount,AuthoredValue,GroupSuccess)
import test_group_preconditions_native as base
class ConditionPrecedenceTests(base.GroupPreconditionTests):
    for name in tuple(n for n in dir(base.GroupPreconditionTests) if n.startswith('test_')):locals()[name]=None
    def check(self,assembly,tx,operations,condition,key):
        context=assembly.group_context_in_transaction(tx).value
        result=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=()),preconditions=(condition,)),context.request(key),documents=self.documents)
        self.assertIsInstance(result,Ok,repr(result)+' '+str(assembly._host._custody.last_attempt.error))
        self.assertIsInstance(result.value,GroupFailed,repr(result))
        self.assertIsInstance(result.value.failure,PreconditionFailed,repr(result))
        self.assertEqual([(f.condition_id,f.reason) for f in result.value.failure.failures],[(condition.id,condition.reason)])
    def test_missing_target_condition_precedes_missing_update(self):
        c,h,a,t,first,second,pin=self.initialized();missing=replace(first,id='99999999')
        self.check(a,t,(UpdateObject(target=StoredObjectReference(identity=missing),set=(),unset=()),),ObjectExists(id='exists',reason='no such object',target=missing),'missing-update')
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(2,))
    def test_key_absent_precedes_duplicate_create(self):
        c,h,a,t,first,second,pin=self.initialized()
        condition=KeyAbsent(id='fresh',reason='key already held',type_definition_pin=first.definition_pin,key_id='a-primary',values=(TextValue(kind='string',text='value'),TextValue(kind='string',text='one')))
        self.check(a,t,(self.create(),),condition,'duplicate-create')
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(2,))
    def test_missing_target_condition_precedes_create_and_edge_plan(self):
        c,h,a,t,first,second,pin=self.initialized();missing=replace(second,id='99999999')
        operations=(self.create(label='new',value='new',alias='new'),CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias='new'),target=StoredObjectReference(identity=missing),values=(),order_key=NullOrderKey()))
        self.check(a,t,operations,ObjectExists(id='use_case_exists',reason='no such use case',target=missing),'missing-edge')
        h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(2,))

    def test_relationship_count_threshold_boundaries_preserve_precondition_semantics(self):
        c,h,a,t,first,second,pin=self.initialized()
        context=a.group_context_in_transaction(t).value
        edge=CreateEdge(relationship_definition_pin=pin,
            source=StoredObjectReference(identity=first),target=StoredObjectReference(identity=second),
            values=(),order_key=NullOrderKey())
        created=a.apply_in_transaction(t,context.input((edge,),MapValue(entries=())),
            context.request('threshold-edge'),documents=self.documents)
        self.assertIsInstance(created,Ok,repr(created))
        self.assertIsInstance(created.value,GroupSuccess,repr(created.value))
        h.detach();c.commit();c,h,a,t=self.consumer()

        failed_cases=(
            ('out-min2','outgoing',first,'2',None),
            ('in-min2','incoming',second,'2',None),
            ('out-max0','outgoing',first,'0','0'),
            ('in-max0','incoming',second,'0','0'),
        )
        for condition_id,direction,anchor,minimum,maximum in failed_cases:
            condition=RelationshipCount(id=condition_id,reason='threshold must hold',
                relationship_definition_pin=pin,anchor=anchor,direction=direction,
                minimum=minimum,**({'maximum':maximum} if maximum is not None else {}))
            result,_,_=self.condition_group(a,t,first,(condition,),f'threshold-{condition_id}')
            self.assertIsInstance(result,GroupFailed,repr(result))
            self.assertIsInstance(result.failure,PreconditionFailed,repr(result.failure))
            self.assertEqual([(f.condition_id,f.reason) for f in result.failure.failures],
                [(condition_id,'threshold must hold')])
            current=self.read(a,t,first)
            self.assertEqual(dict(current.object.values)['A-label'],'one')
            self.assertEqual(current.object.version,1)

        success_cases=(
            ('min1','1',None),
            ('max-bigint','1','9223372036854775807'),
            ('max-one','1','1'),
        )
        for index,(name,minimum,maximum) in enumerate(success_cases,start=1):
            condition=RelationshipCount(id=f'count-{name}',reason='one edge is in range',
                relationship_definition_pin=pin,anchor=first,direction='outgoing',minimum=minimum,
                **({'maximum':maximum} if maximum is not None else {}))
            context=a.group_context_in_transaction(t).value
            operation=UpdateObject(target=StoredObjectReference(identity=first),
                set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text=f'new-{name}')),
                     ),unset=(),expected_version=str(index))
            result=a.apply_in_transaction(t,context.input((operation,),MapValue(entries=()),
                preconditions=(condition,)),context.request(f'threshold-success-{name}'),
                documents=self.documents)
            self.assertIsInstance(result,Ok,repr(result))
            self.assertIsInstance(result.value,GroupSuccess,repr(result.value))
            current=self.read(a,t,first)
            self.assertEqual(dict(current.object.values)['A-label'],f'new-{name}')
            self.assertEqual(current.object.version,index+1)
        h.detach();c.commit()
