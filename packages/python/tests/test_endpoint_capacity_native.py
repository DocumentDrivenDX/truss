"""Atomic edge capacity includes two distinct stored endpoints per operation."""
import unittest
from truss import Ok
from truss.contracts import MapValue
from truss.groups import GroupSuccess,RequestNone,StoredObjectReference
import test_edge_mutations_native as base
class EndpointCapacityTests(base.EdgeMutationTests):
 for n in tuple(n for n in dir(base.EdgeMutationTests) if n.startswith('test_')):locals()[n]=None
 def test_disjoint_endpoints(self):
  def independent(source):
   for r in source['modules'][0]['relationships']:
    r['sourceMultiplicity']={'min':0,'max':'*'};r['targetMultiplicity']={'min':0,'max':'*'}
  c,h,a,t=self.ready(independent,document_ids=('adoc',))
  identities=[]
  for record in ('A','B'):
   context=a.group_context_in_transaction(t).value
   result=a.apply_in_transaction(t,context.input(tuple(self.create(label=f'{record}-{i}',value=f'{record}-{i}',alias=f'row-{i}',record=record) for i in range(1024)),MapValue(entries=())),RequestNone(),documents=self.documents)
   self.assertIsInstance(result,Ok,repr(result)+' '+str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
   identities.append(tuple(r.identity for r in result.value.response.semantic.results));h.detach();c.commit();c,h,a,t=self.consumer()
  pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
  context=a.group_context_in_transaction(t).value
  result=a.apply_in_transaction(t,context.input(tuple(self.link(pin,StoredObjectReference(identity=x),StoredObjectReference(identity=y),alias=f'edge-{i}') for i,(x,y) in enumerate(zip(*identities))),MapValue(entries=())),RequestNone(),documents=self.documents)
  self.assertIsInstance(result,Ok,repr(result)+' '+str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess)
  h.detach();c.commit()
  self.assertEqual(self.admin.execute('SELECT count(*),count(DISTINCT source_id),count(DISTINCT target_id) FROM truss.edge').fetchone(),(1024,1024,1024))
  import psycopg
  for edges in ('[{"edge":0,"source":0,"target":0}]','[{"edge":0,"source":0,"target":1},{"edge":1,"source":1,"target":0}]'):
   with self.assertRaises(psycopg.errors.InvalidParameterValue):self.admin.execute('SELECT truss.owned_forest_projection(2048,%s::jsonb)',(edges,))
if __name__=='__main__':unittest.main()
