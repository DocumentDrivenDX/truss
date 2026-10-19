# SPDX-License-Identifier: MIT OR Apache-2.0
"""The unchanged eight-key, 1,024-operation capacity with one native writer gate."""
import unittest,json
from truss import Ok
from truss.contracts import MapValue
from truss.groups import GroupSuccess,RequestNone
import test_bulk_create_sql_native as base
class KeyFootprintCapacityTests(base.BulkUpdateSqlTests):
 for n in tuple(n for n in dir(base.BulkUpdateSqlTests) if n.startswith('test_')):locals()[n]=None
 def test_eight_keys(self):
  def eight(source):
   module=source['modules'][0]
   for r in tuple(module['elements']):
    if r['kind']=='record':
     for i in range(6):
      field={'module':'m','element':r['id']+'-extra'+str(i)}
      module['elements'].append({'id':field['element'],'name':field['element'],'kind':'field','scalarType':'string','nullability':'required','cardinality':'one','extensions':{}})
      r['members'].append(field);r['keys'].append({'id':'extra'+str(i),'name':'extra'+str(i),'fields':[field]})
  c,h,a,t=self.ready(eight,document_ids=('adoc',))
  from dataclasses import replace
  from truss.groups import AuthoredValue
  from truss.contracts import TextValue
  def create(i):
   original=self.create(label=f'key-{i}',value=f'before-{i}',alias=f'row-{i}')
   return replace(original,values=original.values+tuple(AuthoredValue(name='A-extra'+str(p),value=TextValue(kind='string',text=f'key-{p}-{i}')) for p in range(6)))
  context=a.group_context_in_transaction(t).value
  result=a.apply_in_transaction(t,context.input(tuple(create(i) for i in range(1024)),MapValue(entries=())),RequestNone(),documents=self.documents)
  self.assertIsInstance(result,Ok,repr(result)+' '+str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess,repr(result))
  import psycopg
  with self.assertRaises(psycopg.errors.LockNotAvailable):
   self.admin.execute('SELECT * FROM truss.lock_string_key_bucket(%s,%s)',(b'contending-namespace',b'umf-key-tuple-v1:hex:00'))
  identities=tuple(r.identity for r in result.value.response.semantic.results);h.detach();c.commit();c,h,a,t=self.consumer()
  context=a.group_context_in_transaction(t).value
  result=a.apply_in_transaction(t,context.input(tuple(replace(op,set=op.set+tuple(AuthoredValue(name='A-extra'+str(p),value=TextValue(kind='string',text=f'after-{p}-{i}')) for p in range(6))) for i,op in enumerate(self.updates(identities))),MapValue(entries=())),RequestNone(),documents=self.documents)
  self.assertIsInstance(result,Ok,repr(result)+' '+str(h._custody.last_attempt.error));self.assertIsInstance(result.value,GroupSuccess,repr(result))
  h.detach();c.commit();self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object_key_bucket').fetchone(),(8192,))
if __name__=='__main__':unittest.main()
