# SPDX-License-Identifier: MIT OR Apache-2.0
"""Installed original mapping source admission through the native publication cut."""
from unittest.mock import patch
import psycopg
from truss import Ok,Error
import test_security_catalog_source_cut_native as source

class CatalogArchiveNativeTests(source.CatalogSourceCutTests):
 for name in tuple(n for n in dir(source.CatalogSourceCutTests) if n.startswith('test_')):locals()[name]=None
 def test_substituted_installed_policy_request_refuses_before_subject(self):
  """@covers US-056-AC6/AC9; installed source binding prerequisite."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute("UPDATE truss.installation_archive SET artifact_bytes=artifact_bytes||decode('20','hex') WHERE artifact_identity='catalog:original-mapping-request'")
  with patch.object(source.subject,'encode_literal_key_tuple') as encoder,patch.object(source.subject,'run_owned_catalog_resource_read') as evaluator:
   result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original installed catalog mapping archive required')
 def test_late_archive_drift_refuses_after_actual_evaluation(self):
  """@covers US-057-AC7; original release comparison prerequisite."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[];completed=[]
  original=source.subject.run_owned_catalog_resource_read
  def drift(*args,**kwargs):
   result=original(*args,**kwargs);self.assertIsInstance(result,Ok)
   completed.append(True)
   self.admin.execute("DELETE FROM truss.installation_archive WHERE artifact_identity='catalog:original-compiler-handoff'")
   return result
  with patch.object(source.subject,'run_owned_catalog_resource_read',drift):
   result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
  self.assertEqual(completed,[True]);self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original installed catalog mapping archive required')
 def test_archive_source_cut_is_held_through_delivery(self):
  """@covers US-056-AC9; selected cross-transaction source writer exclusion."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  def publish(packet):
   self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation='truss.installation_archive'::regclass").fetchone(),(1,))
   with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=100ms') as writer:
    with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute("UPDATE truss.installation_archive SET artifact_bytes=artifact_bytes")
   delivered.append(packet)
  result=source.subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,publish)
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(delivered,[result.value])
