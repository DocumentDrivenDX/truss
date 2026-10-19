# SPDX-License-Identifier: MIT OR Apache-2.0
"""Current native guard comparison in owned catalog reads; no ready authority."""
from unittest.mock import patch
import test_security_catalog_source_cut_native as source
from truss import Error

class CatalogAuthorityNativeTests(source.CatalogSourceCutTests):
 for name in tuple(n for n in dir(source.CatalogSourceCutTests) if n.startswith('test_')):locals()[name]=None
 def test_native_generation_drift_refuses_before_evaluator(self):
  """@covers US-056-AC9; @covers US-057-AC3; prerequisite only."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.assertEqual(mapping.native_guard[2],1)
  self.admin.execute('UPDATE truss.policy_generation_guard SET generation=2')
  import subprocess
  original=subprocess.run
  with patch('security_catalog_read.subprocess.run',wraps=original) as calls:
   result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   self.assertIsInstance(result,Error)
   self.assertFalse(any(len(call.args[0])>1 and str(call.args[0][1]).endswith('evaluate-security-captured-identity-fixture.ts') for call in calls.call_args_list))
  self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original current native authority comparison required')

 def test_foreign_native_generation_descriptor_refuses(self):
  """@covers US-056-AC9; guard descriptor refusal before row fetch/Loader.load decoding."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute('ALTER TABLE truss.policy_generation_guard ALTER COLUMN generation TYPE numeric USING generation::numeric')
  result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Exact native authority guard descriptors required')
 def test_fresh_generation_two_is_carried_to_shared_evaluator(self):
  """@covers US-057-AC3; actual current guard transport, not ready authority."""
  from truss import Ok
  from truss._security_mapping import prepare_security_mapping_in_transaction
  import subprocess,json
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute('UPDATE truss.policy_generation_guard SET generation=2')
  fresh=prepare_security_mapping_in_transaction(self.host,self.tx,boundary=self.boundary,installation_identity=self.identity,expected_generation=2,original_request=self.reference,require_accepted_catalog=True)
  self.assertIsInstance(fresh,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(fresh.value.native_guard[2],2)
  original=subprocess.run
  with patch('security_catalog_read.subprocess.run',wraps=original) as calls:
   result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,fresh.value,selection,inspector,relations,cut,delivered.append)
   self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error))
   inputs=[json.loads(call.kwargs['input']) for call in calls.call_args_list if len(call.args[0])>1 and str(call.args[0][1]).endswith('evaluate-security-captured-identity-fixture.ts')]
  self.assertEqual(len(inputs),1);self.assertEqual(inputs[0]['authorityGeneration'],'2');self.assertEqual(delivered,[result.value])

 def test_late_native_generation_drift_refuses_publication(self):
  """@covers US-056-AC9; @covers US-057-AC7; final native comparison."""
  import subprocess
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[];evaluated=[]
  original=subprocess.run
  def run(*args,**kwargs):
   result=original(*args,**kwargs)
   if len(args[0])>1 and str(args[0][1]).endswith('evaluate-security-captured-identity-fixture.ts'):
    self.assertEqual(result.returncode,0);evaluated.append(True)
    self.admin.execute('UPDATE truss.policy_generation_guard SET generation=2')
   return result
  with patch('security_catalog_read.subprocess.run',run):
   result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
  self.assertIsInstance(result,Error);self.assertEqual(evaluated,[True]);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original current native authority comparison required')
