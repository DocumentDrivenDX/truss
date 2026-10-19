# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original packaged native epoch/barrier installation into accepted catalog."""
from truss import Ok,Error
from truss._security_catalog_source_installation import bootstrap_catalog_source_marker_in_transaction
from truss._security_source_epoch_installation import bootstrap_source_epoch_infrastructure_in_transaction
import test_security_catalog_subject_native as subject

class SourceEpochInstallationNativeTests(subject.NativeCatalogSubjectTests):
 for name in tuple(n for n in dir(subject.NativeCatalogSubjectTests) if n.startswith('test_')):locals()[name]=None
 def marker(self):
  mapping,c,h,t,selection,inspector=self.setup_subject()
  marked=bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,mapping)
  self.assertIsInstance(marked,Ok,str(self.host._custody.last_attempt.error))
  return mapping,c,h,t
 def install_epoch(self):
  return bootstrap_source_epoch_infrastructure_in_transaction(self.host,self.tx,installation_identity=self.installation.installation_id.encode())
 def test_original_packaged_inventory_and_no_repair(self):
  """@covers US-056-AC9/AC10; installed issuer construction prerequisite."""
  self.marker();prior=self.admin.execute("SELECT current_setting('search_path')").fetchone()
  result=self.install_epoch();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertFalse(result.value.security_ready)
  self.assertEqual(result.value.installation_id,self.installation.installation_id)
  self.assertEqual(self.admin.execute("SELECT current_setting('search_path')").fetchone(),prior)
  self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_event_trigger WHERE evtname LIKE 'truss%ddl_writer_barrier'").fetchone(),(5,))
  again=self.install_epoch();self.assertIsInstance(again,Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Existing source epoch routines require explicit migration')
 def test_missing_original_marker_refuses_without_routines(self):
  self.setup_subject();result=self.install_epoch();self.assertIsInstance(result,Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original catalog source marker required')
  self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_proc WHERE proname='runtime_issue_source_epoch'").fetchone(),(0,))
 def test_outer_rollback_removes_pending_infrastructure(self):
  self.marker();self.admin.execute('SAVEPOINT before_epoch_infrastructure')
  self.assertIsInstance(self.install_epoch(),Ok,str(self.host._custody.last_attempt.error))
  self.admin.execute('ROLLBACK TO before_epoch_infrastructure')
  self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_proc WHERE proname='runtime_issue_source_epoch'").fetchone(),(0,))
  self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_event_trigger WHERE evtname LIKE 'truss%ddl_writer_barrier'").fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_archive').fetchone(),(6,))
 def test_original_ordinary_caller_refuses_installation(self):
  mapping,c,h,t=self.marker()
  result=bootstrap_source_epoch_infrastructure_in_transaction(h,t,installation_identity=self.installation.installation_id.encode())
  self.assertIsInstance(result,Error)
  self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_proc WHERE proname='runtime_issue_source_epoch'").fetchone(),(0,))
 def test_third_party_default_routine_grant_refuses_atomically(self):
  """@covers US-056-AC9/AC10; unsafe native installer defaults refuse."""
  self.marker()
  self.admin.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA truss GRANT EXECUTE ON FUNCTIONS TO consumer')
  result=self.install_epoch();self.assertIsInstance(result,Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Exact private source epoch routine ACL required')
  self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_proc WHERE proname='runtime_issue_source_epoch'").fetchone(),(0,))
  self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_event_trigger WHERE evtname LIKE 'truss%ddl_writer_barrier'").fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_archive').fetchone(),(6,))
 def test_hostile_text_domain_cannot_run_before_path_pin(self):
  """@covers US-056-AC9/AC10; pre-pin type resolution is native pg_catalog."""
  self.marker()
  self.admin.execute("CREATE SCHEMA hostile_epoch;CREATE FUNCTION hostile_epoch.reject_text(pg_catalog.text) RETURNS pg_catalog.bool LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'hostile installer text domain executed';END$$;CREATE DOMAIN hostile_epoch.text AS pg_catalog.text CHECK(hostile_epoch.reject_text(VALUE))")
  self.admin.execute('SET LOCAL search_path=hostile_epoch,pg_catalog')
  # Exact previous pre-pin query executes the hostile domain CHECK natively.
  import psycopg
  self.admin.execute('SAVEPOINT previous_unsafe_cast')
  with self.assertRaises(psycopg.errors.RaiseException) as caught:
   self.admin.execute("SELECT pg_catalog.current_setting('search_path')::text")
  self.assertEqual(caught.exception.diag.message_primary,'hostile installer text domain executed')
  self.admin.execute('ROLLBACK TO previous_unsafe_cast');self.admin.execute('RELEASE previous_unsafe_cast')
  result=self.install_epoch();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  self.assertEqual(self.admin.execute("SELECT pg_catalog.current_setting('search_path')").fetchone(),('hostile_epoch, pg_catalog',))
