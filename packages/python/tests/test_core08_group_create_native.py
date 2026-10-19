# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original core0.8 create/commit/read/key/replay prerequisite; no security admission.
@covers US-056-AC2
@covers US-056-AC9
"""
import test_group_create_native as groups
class Core08GroupCreateTests(groups.PublicCreateGroupTests):
 for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
 def ready(self,mutate_source=None):
  def current(source):
   source['umf']='0.8.0'
   if mutate_source is not None:mutate_source(source)
  return super().ready(current)
 def test_original08_create_commit_read_and_durable_retry(self):
  return groups.PublicCreateGroupTests.test_create_commit_read_and_original_durable_replay(self)
 def test_original08_native_single_and_compound_key_lookup(self):
  c,h,a,t=self.ready();input,request=self.input(a,t);created=self.apply(a,t,input,request).response.semantic.results[0].identity
  h.detach();c.commit();c,h,a,t=self.consumer()
  for key,values in (('z-alt',('one',)),('a-primary',('value','one'))):
   result=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id=key,values=values,bun_executable='/opt/homebrew/bin/bun')
   self.assertIsInstance(result,groups.Ok);self.assertIsInstance(result.value,groups.ObjectFound,str(a._host._custody.last_attempt.error))
   self.assertEqual(result.value.object.identity.id,created.id)
  reversed_key=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('one','value'),bun_executable='/opt/homebrew/bin/bun')
  self.assertIsInstance(reversed_key,groups.Ok);self.assertEqual(reversed_key.value.outcome,'not_found')
