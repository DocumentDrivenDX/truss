# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native initial factory source correspondence and savepoint containment."""
from dataclasses import replace
from truss import Ok,Error
from truss._security_catalog_source_installation import bootstrap_catalog_source_marker_in_transaction
from truss._security_source_epoch_installation import bootstrap_source_epoch_infrastructure_in_transaction
from truss._security_catalog_source_epoch import issue_initial_catalog_source_epoch_in_transaction
import test_security_guarded_subject_native as guarded

class CatalogSourceFactoryNativeTests(guarded.GuardedSubjectTests):
 for name in tuple(n for n in dir(guarded.GuardedSubjectTests) if n.startswith('test_')):locals()[name]=None
 def ready_factory(self):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  marked=bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,mapping)
  self.assertIsInstance(marked,Ok,str(self.host._custody.last_attempt.error))
  installed=bootstrap_source_epoch_infrastructure_in_transaction(self.host,self.tx,installation_identity=self.installation.installation_id.encode())
  self.assertIsInstance(installed,Ok,str(self.host._custody.last_attempt.error))
  return dict(mapping=mapping,marker=marked.value,infrastructure=installed.value,fact_relations=relations,subject_source=(guarded.ROOT/'scripts/security-catalog-subject.sql').read_bytes())
 def mint(self,inputs):return issue_initial_catalog_source_epoch_in_transaction(self.host,self.tx,**inputs)
 def empty_epoch(self):
  self.assertEqual(self.admin.execute('SELECT (SELECT count(*) FROM truss.source_epoch_registry),(SELECT count(*) FROM truss.source_epoch_current)').fetchone(),(0,0))
 def test_original_factory_issues_exact_initial_profile_and_refuses_reuse(self):
  """@covers US-056-AC6/AC9/AC10; source construction, not protected admission."""
  inputs=self.ready_factory();result=self.mint(inputs)
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertFalse(result.value.security_ready)
  comparison=result.value.comparison
  self.assertIn(b'"interfaceVersion":"truss-owned-catalog-source-profile/0.4"',comparison.profile)
  self.assertEqual(self.admin.execute('SELECT source_epoch,profile_bytes,evidence_bytes FROM truss.source_epoch_registry').fetchall(),[(comparison.epoch,comparison.profile,comparison.evidence)])
  self.assertIsInstance(self.mint(inputs),Error)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.source_epoch_registry').fetchone(),(1,))
 def test_stale_generation_refuses_before_epoch_effect(self):
  inputs=self.ready_factory();self.admin.execute('UPDATE truss.policy_generation_guard SET generation=2')
  self.assertIsInstance(self.mint(inputs),Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original source factory current guard required');self.empty_epoch()
 def test_original_marker_incarnation_substitution_refuses(self):
  inputs=self.ready_factory();inputs['marker']=replace(inputs['marker'],target_incarnation=b'foreign-target')
  self.assertIsInstance(self.mint(inputs),Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original source factory incarnation required');self.empty_epoch()
 def test_unexpected_native_pointer_trigger_refuses_before_issuance(self):
  """@covers US-056-AC9; unexpected native pointer hook refuses before issuance."""
  inputs=self.ready_factory()
  self.admin.execute("CREATE FUNCTION truss.factory_suppress_pointer() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RETURN NULL;END$$;CREATE TRIGGER factory_suppress_pointer BEFORE INSERT ON truss.source_epoch_current FOR EACH ROW EXECUTE FUNCTION truss.factory_suppress_pointer()")
  # Existing unexpected user trigger is rejected by infrastructure census first.
  result=self.mint(inputs);self.assertIsInstance(result,Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Bounded exact source epoch inventory required');self.empty_epoch()
 def test_outer_rollback_removes_epoch_retains_original_installation(self):
  inputs=self.ready_factory();self.admin.execute('SAVEPOINT before_initial_epoch')
  self.assertIsInstance(self.mint(inputs),Ok,str(self.host._custody.last_attempt.error))
  self.admin.execute('ROLLBACK TO before_initial_epoch');self.empty_epoch()
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_archive').fetchone(),(6,))

 def test_actual_pointer_removed_after_issuance_is_detected_and_contained(self):
  """@covers US-056-AC9; native issued token alone cannot prove publication state."""
  from unittest.mock import patch
  import truss._security_catalog_source_epoch as factory
  inputs=self.ready_factory()
  self.admin.execute("CREATE TEMP TABLE prior_factory_work(value text);INSERT INTO prior_factory_work VALUES('kept')")
  original=factory._text_rows;mutated=[]
  def remove_pointer(cursor,query,*args,**kwargs):
   if query.startswith('SELECT c.installation_id::text,c.source_epoch::text,r.target_incarnation::text'):
    self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.source_epoch_registry').fetchone(),(1,))
    self.admin.execute('DELETE FROM truss.source_epoch_current');mutated.append(True)
   return original(cursor,query,*args,**kwargs)
  with patch.object(factory,'_text_rows',remove_pointer):result=self.mint(inputs)
  self.assertEqual(mutated,[True]);self.assertIsInstance(result,Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Exact original source factory epoch readback required')
  self.empty_epoch();self.assertEqual(self.admin.execute('TABLE prior_factory_work').fetchall(),[('kept',)])
