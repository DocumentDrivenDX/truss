"""Declared failed conditions win over operation failures on the same locked prestate."""
from dataclasses import replace
from truss import Ok
from truss.contracts import MapValue,TextValue
from truss.groups import (ObjectExists,KeyAbsent,UpdateObject,StoredObjectReference,
    GroupFailed,PreconditionFailed,AliasObjectReference,CreateEdge,NullOrderKey)
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
