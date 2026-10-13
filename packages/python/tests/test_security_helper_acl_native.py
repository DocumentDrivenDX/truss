"""Actual helper ACL drift; component admission, not complete backend B11."""
from unittest.mock import patch
import test_security_catalog_source_cut_native as source
from truss import Error,adopt_psycopg_host

class HelperAclNativeTests(source.CatalogSourceCutTests):
 for name in tuple(n for n in dir(source.CatalogSourceCutTests) if n.startswith('test_')):locals()[name]=None
 def test_public_execute_before_admission_refuses_without_setting_bypass(self):
  """@covers US-056-AC9; original native helper grant comparison."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute('GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO PUBLIC')
  self.settle_drift()
  self.assertEqual(self.admin.execute("SELECT current_setting('event_triggers')").fetchone(),('on',))
  with patch.object(source.subject,'encode_literal_key_tuple',wraps=source.subject.encode_literal_key_tuple) as encoder:
   result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   self.assertIsInstance(result,Error)
   encoder.assert_not_called()
  self.assertEqual(delivered,[])
  self.assertEqual(str(h._custody.last_attempt.error),'Exact installed catalog subject helper ACL required')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)

 def settle_drift(self):
  self.host.detach();self.admin.commit();self.admin.execute('BEGIN')
  self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
 def assert_acl_drift(self,statement):
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute(statement)
  self.settle_drift()
  with patch.object(source.subject,'encode_literal_key_tuple',wraps=source.subject.encode_literal_key_tuple) as encoder:
   result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   self.assertIsInstance(result,Error);encoder.assert_not_called()
  self.assertEqual(delivered,[])
  self.assertEqual(str(h._custody.last_attempt.error),'Exact installed catalog subject helper ACL required')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)
  self.assertEqual(str(h._custody.last_attempt.error),'Exact installed catalog subject helper ACL required')
 def test_context_helper_public_execute_refuses(self):
  self.assert_acl_drift('GRANT EXECUTE ON FUNCTION truss.catalog_subject_context(text) TO PUBLIC')
 def test_caller_grant_option_refuses(self):
  self.assert_acl_drift('GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO consumer WITH GRANT OPTION')
 def test_missing_caller_execute_refuses(self):
  self.assert_acl_drift('REVOKE EXECUTE ON FUNCTION truss.catalog_subject_current(text) FROM consumer')
 def test_other_role_execute_refuses(self):
  self.assert_acl_drift('GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO catalog_fact_reader')

 def test_committed_late_acl_drift_refuses_publication(self):
  """@covers US-056-AC9; excluded administrator bypass, final comparison."""
  import psycopg
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  original=source.subject.run_owned_catalog_resource_read
  def evaluate(*args,**kwargs):
   result=original(*args,**kwargs)
   with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c statement_timeout=5000') as writer:
    writer.execute('SET event_triggers=off')
    writer.execute('GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO PUBLIC')
   self.assertEqual(self.admin.execute("SELECT current_setting('event_triggers')").fetchone(),('on',))
   return result
  with patch.object(source.subject,'run_owned_catalog_resource_read',evaluate):
   result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(h._custody.last_attempt.error),'Exact installed catalog subject helper ACL required')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)
