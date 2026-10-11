"""Connected administrative original-custody finalization, rollback-only."""
import hashlib,importlib.util,json,unittest
from pathlib import Path
from truss import Ok,Error,PsycopgProfile,adopt_psycopg_host
from test_catalog_prerequisites_psycopg_native import PrerequisitePsycopgNativeTests
DRAFT=Path(__file__).parent;ROOT=Path(__file__).resolve().parents[5]
class CustodyBranchNativeTests(unittest.TestCase):
 run_pg=classmethod(PrerequisitePsycopgNativeTests.run_pg.__func__)
 setUpClass=classmethod(PrerequisitePsycopgNativeTests.setUpClass.__func__)
 cleanup_fixture=classmethod(PrerequisitePsycopgNativeTests.cleanup_fixture.__func__)
 setUp=PrerequisitePsycopgNativeTests.setUp
 tearDown=PrerequisitePsycopgNativeTests.tearDown
 query=PrerequisitePsycopgNativeTests.query
 archive=PrerequisitePsycopgNativeTests.archive
 stage=PrerequisitePsycopgNativeTests.stage
 additional_install_paths=('docs/helix/04-build/evidence/catalog-revision-custody-storage.owner-export.sql',)+tuple('packages/postgresql/native/catalog-custody/'+n+'.sql' for n in ['configured-graph','fresh-lifecycle','stage-issued','configured-stage','report-write'])
 stage_recipe_path='packages/python/src/truss/_profiles/catalog-report-custody-composition-candidate.json'
 stage_function='runtime_stage_custody_catalog_with_release_candidate'
class Finalization(CustodyBranchNativeTests):
 selected_profile=PsycopgProfile(server=180006)
 additional_install_paths=CustodyBranchNativeTests.additional_install_paths+('packages/postgresql/native/catalog-completion/configured-state-candidate.sql', 'packages/postgresql/native/catalog-custody/reference-collectors.sql', 'packages/postgresql/native/catalog-custody/composition-admission.sql', 'packages/postgresql/native/catalog-custody/capture.sql', 'packages/postgresql/native/catalog-custody/registration-composition-admission.sql', 'packages/postgresql/native/catalog-custody/registration-capture.sql', 'packages/postgresql/native/catalog-custody/registrar.sql', 'packages/postgresql/native/catalog-custody/prerequisite-composition/composition-admission.sql', 'packages/postgresql/native/catalog-custody/prerequisite-composition/registration-capture.sql', 'packages/postgresql/native/catalog-custody/prerequisite-composition/registrar.sql', 'packages/postgresql/native/catalog-custody/prerequisite-composition/prerequisites.sql', 'packages/postgresql/native/catalog-finalization/finalization-composition-admission.owner-export.sql', 'packages/postgresql/native/catalog-finalization/finalizing-capture.owner-export.sql', 'packages/postgresql/native/catalog-finalization/finalizing-registrar.owner-export.sql', 'packages/postgresql/native/catalog-finalization/finalizing-prerequisites.owner-export.sql', 'packages/postgresql/native/catalog-finalization/readonly-custody-preflight.owner-export.sql', 'packages/postgresql/native/catalog-finalization/readonly-business-preflight.owner-export.sql', 'packages/postgresql/native/catalog-finalization/finalizing-completion-state.owner-export.sql', 'packages/postgresql/native/catalog-finalization/finalize-feed.owner-export.sql', 'packages/postgresql/native/catalog-finalization/finalizing-head.owner-export.sql', 'packages/postgresql/native/catalog-finalization/manifest-encoder.owner-export.sql', 'packages/postgresql/native/catalog-finalization/original-manifest.owner-export.sql')
 def setUp(self):
  CustodyBranchNativeTests.setUp(self)
  self.host.detach()
  self.host=adopt_psycopg_host(self.connection,profile=self.selected_profile,statement_timeout_ms=25000,operation_timeout_ms=30000)
  self.addCleanup(self.host.detach)
  self.transaction=self.host.adopt_transaction().value
  self.query('LOCK TABLE truss.schema_head IN EXCLUSIVE MODE NOWAIT')
  packet=getattr(self,'packet',DRAFT);raw=(packet/'reference.original.json').read_bytes()
  descriptor=self.query('SELECT truss.runtime_collect_catalog_custody_target_descriptor_candidate()::text').fetchone()[0]
  inventory={'interfaceVersion':'truss-catalog-custody-installation-inventory/0.5-finalization-candidate','scope':'administrative_rollback_only_catalog_custody',
   'referenceManifest':{'identity':'truss.catalog-custody-finalization-independent-reference/0.1-candidate','sha256':hashlib.sha256(raw).hexdigest()},
   'custodyDescriptorSha256':hashlib.sha256(descriptor.encode()).hexdigest()}
  self.query('UPDATE truss.installation_admission SET installed_inventory_bytes=%s',(json.dumps(inventory,separators=(',',':')).encode(),))
  self.archive(inventory['referenceManifest']['identity'],raw)
  selected=json.loads((getattr(self,'selection',DRAFT/'selection.json')).read_bytes())
  manifest=json.loads(raw)
  for i,entry in enumerate(selected['resources']):
   original=(ROOT/entry['file']).read_bytes()
   self.assertEqual(hashlib.sha256(original).hexdigest(),manifest['resources'][i]['sha256'])
   self.archive(entry['path'],original)
 def archive(self,identity,raw):
  previous=self.query("SELECT artifact_bytes FROM truss.installation_archive WHERE installation_id='guard-fixture' AND artifact_role='input' AND artifact_identity=%s",(identity,)).fetchall()
  if previous:self.assertEqual(previous,[(raw,)]);return
  super().archive(identity,raw)
 def capture_original(self):
  self.query("SET LOCAL TimeZone='UTC'");self.stage()
  def capture(cursor,observed):
   cursor.execute('SELECT * FROM truss.runtime_capture_catalog_finalizing_custody_candidate(%s,%s,%s,%s,%s,%s,%s)',(self.writer,self.ordinal,self.generation,self.identity,self.registration,(ROOT/'packages/python/src/truss/_profiles/fresh-catalog-lifecycle.json').read_bytes(),(ROOT/'packages/python/src/truss/_profiles/absent-binding-index-declarations.json').read_bytes()),prepare=False)
   return cursor.fetchmany(2)
  result=self.host._run_operation(self.transaction,capture)
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.generation=self.query('SELECT effect_generation::text FROM truss.row_home_operation').fetchone()[0]
 def apply_prerequisites(self,fail_after=False):
  def run(cursor,observed):
   cursor.execute('SELECT * FROM truss.runtime_register_finalizing_catalog_prerequisites_candidate(%s,%s,%s)',(self.writer,self.ordinal,self.generation),prepare=False);return cursor.fetchmany(2)
  return self.host._run_operation(self.transaction,run)
 def finalize(self):
  def run(cursor,observed):
   cursor.execute('SELECT * FROM truss.runtime_finalize_original_catalog_feed_candidate(%s,%s,%s)',(self.writer,self.ordinal,self.generation),prepare=False);return cursor.fetchmany(2)
  return self.host._run_operation(self.transaction,run)
 def test_original_registration_publication_and_repeat(self):
  self.capture_original();result=self.apply_prerequisites();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  before=self.query('SELECT record_send(t) FROM truss.catalog_revision_custody t').fetchall()
  op=self.query('SELECT record_send(t) FROM truss.row_home_operation t').fetchall()
  expected=self.original_manifest_oracle()
  result=self.finalize();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  self.assertEqual(len(result.value),1)
  tree,wire,digest,generation=result.value[0]
  self.assertEqual((tree,wire,digest),(expected['treeBytes'].hex(),expected['wireBytes'].hex(),expected['semanticSha256']))
  self.assertEqual(self.query('SELECT encode(manifest_bytes,\'hex\'),encode(manifest_sha256,\'hex\'),finalized_generation::text FROM truss.feed_tx').fetchone(),(tree,digest,generation))
  self.assertEqual(self.query('SELECT delivery_ordinal FROM truss.feed_member').fetchone(),(0,))
  again=self.finalize();self.assertIsInstance(again,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(again.value,result.value)
  self.assertEqual(self.query('SELECT record_send(t) FROM truss.catalog_revision_custody t').fetchall(),before)
  self.assertEqual(self.query('SELECT record_send(t) FROM truss.row_home_operation t').fetchall(),op)
  self.assertEqual(self.query('SELECT rev FROM truss.schema_head').fetchone(),(0,))
 def test_connected_head_last_and_raw_commit_refusal(self):
  self.capture_original()
  custody=self.query('SELECT record_send(t) FROM truss.catalog_revision_custody t').fetchall();g=self.generation
  def run(cursor,observed):
   cursor.execute('SELECT * FROM truss.runtime_register_finalizing_catalog_and_head_candidate(%s,%s,%s)',(self.writer,self.ordinal,self.generation),prepare=False);return cursor.fetchmany(2)
  result=self.host._run_operation(self.transaction,run);self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  self.assertEqual(result.value[0][2],str(int(g)+1));self.assertEqual(result.value[0][-2:],(False,False))
  self.assertEqual(self.query('SELECT rev FROM truss.schema_head').fetchone(),(1,))
  self.assertEqual(self.query('SELECT record_send(t) FROM truss.catalog_revision_custody t').fetchall(),custody)
  self.assertEqual(self.query('SELECT capture_generation::text FROM truss.catalog_revision_custody').fetchone(),(g,))
  self.assertEqual(self.query('SELECT finalized_generation=membership_generation FROM truss.feed_tx').fetchone(),(True,))
  import psycopg
  with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as refused:self.connection.commit()
  self.assertIn('complete runtime finalizer is not installed',str(refused.exception))
 def original_manifest_oracle(self):
  spec=importlib.util.spec_from_file_location('oracle',ROOT/'docs/helix/04-build/evidence/original-manifest-pg18/oracle.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
  original=json.loads(self.query("SELECT convert_from(original_input_bytes,'UTF8') FROM truss.row_home_operation").fetchone()[0])
  cfg=self.query('SELECT configuration_generation::text,key_reuse,journal_mode,source_epoch,installation_id,target_incarnation,admission_profile_bytes,configuration_bytes,selected_binding_bytes,installed_inventory_bytes FROM truss.operation_configuration').fetchone()
  payload,profile,revision=self.query('SELECT original_payload_bytes,original_payload_profile_bytes,original_revision::text FROM truss.catalog_revision_custody').fetchone()
  recipe=json.loads((ROOT/'packages/python/src/truss/_profiles/catalog-feed-finalization-candidate.json').read_bytes())
  return oracle.expected_manifest(original_input=original,revision=revision,xid=self.writer,
   feed_context={'sourceEpoch':cfg[3],'feedProfile':recipe['feedProfile'],'scopeIdentity':'administrative_single_original_operation_fresh_catalog_rollback_only'},
   manifest_definition_bytes=(ROOT/'packages/postgresql/native/catalog-finalization/manifest-definition-v0.4.canonical').read_bytes(),payload_profile_bytes=profile,original_payload_bytes=payload,
   original_configuration=dict(zip(['generation','keyReuse','journalMode','sourceEpoch','installationId','targetIncarnation','admissionProfileBytes','configurationBytes','bindingBytes','inventoryBytes'],cfg)),
   original_configuration_profile_bytes=bytes.fromhex(recipe['configurationProfileHex']))
 def test_malformed_ordinal_refuses_without_repair(self):
  self.capture_original();result=self.apply_prerequisites();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  self.query('UPDATE truss.feed_member SET delivery_ordinal=1')
  before=self.query('SELECT record_send(t) FROM truss.feed_member t').fetchall()
  result=self.finalize();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
  self.assertEqual(self.query('SELECT record_send(t) FROM truss.feed_member t').fetchall(),before)
  self.assertEqual(self.query('SELECT manifest_bytes,finalized_generation FROM truss.feed_tx').fetchone(),(None,None))
 def test_late_failure_restores_finalized_tuple_and_caller_work(self):
  self.capture_original();result=self.apply_prerequisites();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  result=self.finalize();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  before=self.query('SELECT record_send(t) FROM truss.feed_tx t').fetchall();member=self.query('SELECT record_send(t) FROM truss.feed_member t').fetchall()
  self.query('CREATE TEMP TABLE caller_work(v text)');self.query("INSERT INTO caller_work VALUES ('keep')")
  def run(cursor,observed):
   cursor.execute('SELECT * FROM truss.runtime_finalize_original_catalog_feed_candidate(%s,%s,%s)',(self.writer,self.ordinal,self.generation),prepare=False);cursor.fetchall();cursor.execute('SELECT 1/0',prepare=False)
  result=self.host._run_operation(self.transaction,run);self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'22012')
  self.assertEqual(self.query('SELECT record_send(t) FROM truss.feed_tx t').fetchall(),before);self.assertEqual(self.query('SELECT record_send(t) FROM truss.feed_member t').fetchall(),member)
  self.assertEqual(self.query('SELECT v FROM caller_work').fetchall(),[('keep',)])
class Suppressed(Finalization):
 def test_suppressed_original_publication_step_rolls_back(self):
  self.capture_original();result=self.apply_prerequisites();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  names=['feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite','catalog_revision_custody','row_home_operation','operation_configuration']
  before={name:self.query('SELECT record_send(t) FROM truss.'+name+' t ORDER BY encode(record_send(t),\'hex\') COLLATE "C"').fetchall() for name in names}
  self.query('CREATE TEMP TABLE caller_work(v text)');self.query("INSERT INTO caller_work VALUES ('keep')")
  result=self.finalize();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,getattr(self,'expected_state','P0002'))
  self.assertIn(getattr(self,'expected_message','query returned no rows'),str(self.host._custody.last_attempt.error))
  for name in names:self.assertEqual(self.query('SELECT record_send(t) FROM truss.'+name+' t ORDER BY encode(record_send(t),\'hex\') COLLATE "C"').fetchall(),before[name])
  self.assertEqual(self.query('SELECT v FROM caller_work').fetchall(),[('keep',)])
for phase in ['clear-parent','clear-member','assign-ordinal','publish-manifest']:
 name='Suppressed_'+phase.replace('-','_')
 globals()[name]=type(name,(Suppressed,),{'packet':DRAFT/'phase-faults'/phase,'selection':DRAFT/'phase-faults'/phase/'selection.json'})
class ForgedPublish(Suppressed):
 packet=DRAFT/'phase-faults/forged-publish-return'
 selection=packet/'selection.json'
 expected_state='55000'
 expected_message='full original manifest publication correspondence required'
def load_tests(loader,tests,pattern):
 return unittest.TestSuite([
  Finalization('test_original_registration_publication_and_repeat'),
  Finalization('test_malformed_ordinal_refuses_without_repair'),
  Finalization('test_late_failure_restores_finalized_tuple_and_caller_work'),
  Finalization('test_connected_head_last_and_raw_commit_refusal'),
  Suppressed_clear_parent('test_suppressed_original_publication_step_rolls_back'),
  Suppressed_clear_member('test_suppressed_original_publication_step_rolls_back'),
  Suppressed_assign_ordinal('test_suppressed_original_publication_step_rolls_back'),
  Suppressed_publish_manifest('test_suppressed_original_publication_step_rolls_back'),
  ForgedPublish('test_suppressed_original_publication_step_rolls_back')])
if __name__=='__main__':unittest.main(verbosity=2)
