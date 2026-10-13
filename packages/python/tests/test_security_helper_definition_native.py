"""Committed helper owner/definition drift; selected B11 prerequisites only."""
from unittest.mock import patch
import test_security_helper_acl_native as acl
from truss import Error

class HelperDefinitionNativeTests(acl.HelperAclNativeTests):
 for name in tuple(n for n in dir(acl.HelperAclNativeTests) if n.startswith('test_')):locals()[name]=None
 def assert_definition_drift(self,statement):
  """@covers US-056-AC9; exact native primary before encoding/publication."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute(statement);self.settle_drift()
  self.assertEqual(self.admin.execute("SELECT current_setting('event_triggers')").fetchone(),('on',))
  with patch.object(acl.source.subject,'encode_literal_key_tuple',wraps=acl.source.subject.encode_literal_key_tuple) as encoder:
   result=acl.source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   self.assertIsInstance(result,Error);encoder.assert_not_called()
  self.assertEqual(delivered,[])
  self.assertEqual(str(h._custody.last_attempt.error),'Exact installed catalog subject helper snapshot required')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)
 def test_helper_owner_replacement_refuses(self):
  """@covers US-056-AC9; committed native helper snapshot drift."""
  self.assert_definition_drift('ALTER FUNCTION truss.catalog_subject_current(text) OWNER TO postgres')
 def test_helper_invoker_replacement_refuses(self):
  """@covers US-056-AC9; committed native helper snapshot drift."""
  self.assert_definition_drift('ALTER FUNCTION truss.catalog_subject_current(text) SECURITY INVOKER')
 def test_context_resolution_replacement_refuses(self):
  """@covers US-056-AC9; committed native helper snapshot drift."""
  self.assert_definition_drift('ALTER FUNCTION truss.catalog_subject_context(text) SET search_path TO pg_temp,pg_catalog')
 def test_helper_volatility_replacement_refuses(self):
  """@covers US-056-AC9; committed native helper snapshot drift."""
  self.assert_definition_drift('ALTER FUNCTION truss.catalog_subject_current(text) STABLE')
