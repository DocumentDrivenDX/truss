import hashlib,importlib.util,json,unittest
from pathlib import Path
from truss import Ok,Error
ROOT=Path(__file__).resolve().parents[5];DRAFT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('connected',ROOT/'docs/helix/04-build/evidence/catalog-finalization-pg18/check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Current(m.Finalization):
 additional_install_paths=m.Finalization.additional_install_paths+tuple(e['path'] for e in json.loads((DRAFT/'selection.json').read_bytes())['sources'][-13:])
 def setUp(self):
  self.packet=DRAFT;self.selection=DRAFT/'selection.json'
  # Base initial setup plus explicit catalog exclusion, before metadata FKs.
  m.CustodyBranchNativeTests.setUp(self);self.host.detach()
  from truss import adopt_psycopg_host
  self.host=adopt_psycopg_host(self.connection,profile=self.selected_profile,statement_timeout_ms=25000,operation_timeout_ms=30000);self.addCleanup(self.host.detach);self.transaction=self.host.adopt_transaction().value
  self.query('LOCK TABLE truss.schema_head IN EXCLUSIVE MODE NOWAIT')
  raw=(self.packet/'reference.original.json').read_bytes();descriptor=self.query('SELECT truss.runtime_collect_catalog_custody_target_descriptor_candidate()::text').fetchone()[0]
  inventory={'interfaceVersion':'truss-catalog-custody-installation-inventory/0.6-current-union-candidate','scope':'administrative_rollback_only_catalog_custody','referenceManifest':{'identity':'truss.current-catalog-union-independent-reference/0.1-candidate','sha256':hashlib.sha256(raw).hexdigest()},'custodyDescriptorSha256':hashlib.sha256(descriptor.encode()).hexdigest()}
  self.query('UPDATE truss.installation_admission SET installed_inventory_bytes=%s',(json.dumps(inventory,separators=(',',':')).encode(),));self.archive(inventory['referenceManifest']['identity'],raw)
  for i,e in enumerate(json.loads(self.selection.read_bytes())['resources']):self.archive(e['path'],(ROOT/e['path']).read_bytes())
 def capture_original(self):
  self.query("SET LOCAL TimeZone='UTC'");self.stage()
  def capture(cursor,observed):
   cursor.execute('SELECT * FROM truss.runtime_capture_current_union_catalog_custody_candidate(%s,%s,%s,%s,%s,%s,%s)',(self.writer,self.ordinal,self.generation,self.identity,self.registration,(ROOT/'packages/python/src/truss/_profiles/fresh-catalog-lifecycle.json').read_bytes(),(ROOT/'packages/python/src/truss/_profiles/absent-binding-index-declarations.json').read_bytes()),prepare=False);return cursor.fetchmany(2)
  result=self.host._run_operation(self.transaction,capture);self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.generation=self.query('SELECT effect_generation::text FROM truss.row_home_operation').fetchone()[0]
 def publish(self):
  self.capture_original()
  def run(cursor,observed):
   cursor.execute('SELECT * FROM truss.runtime_register_current_union_catalog_and_head_candidate(%s,%s,%s)',(self.writer,self.ordinal,self.generation),prepare=False);return cursor.fetchmany(2)
  result=self.host._run_operation(self.transaction,run);self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.generation=result.value[0][2]
 def validate(self):
  return self.host._run_operation(self.transaction,lambda cursor,observed:cursor.execute('SELECT truss.runtime_feed_union_validate_current_scope_candidate()',prepare=False).fetchone())
 def full_rows(self):
  return self.query('SELECT truss.runtime_capture_current_union_completion_state_candidate(%s,%s,%s)::text',(self.writer,self.ordinal,self.generation)).fetchone()[0]
 def test_posthead_repeat_validation_is_write_free(self):
  self.publish();before=self.full_rows()
  for i in range(2):
   result=self.validate();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(self.full_rows(),before)
 def test_corrupt_final_tuple_refuses_without_repair(self):
  self.publish();self.query('UPDATE truss.feed_member SET delivery_ordinal=1');before=self.full_rows()
  result=self.validate();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000');self.assertEqual(self.full_rows(),before)
 def test_posthead_operation_tampering_refuses_without_repair(self):
  self.publish()
  for change in ('effect_generation=effect_generation+1', "phase='effects_ready',readiness_generation=effect_generation"):
   with self.subTest(change=change):
    self.query('SAVEPOINT tamper')
    self.query('UPDATE truss.row_home_operation SET '+change)
    before=self.query('SELECT row_to_json(t)::text FROM truss.row_home_operation t').fetchone()[0]
    result=self.validate();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
    self.assertEqual(self.query('SELECT row_to_json(t)::text FROM truss.row_home_operation t').fetchone()[0],before)
    self.query('ROLLBACK TO SAVEPOINT tamper');self.query('RELEASE SAVEPOINT tamper')
 def test_missing_current_scope_refuses(self):
  result=self.validate();self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
def load_tests(loader,tests,pattern):return unittest.TestSuite(Current(n) for n in ['test_posthead_repeat_validation_is_write_free','test_corrupt_final_tuple_refuses_without_repair','test_missing_current_scope_refuses','test_posthead_operation_tampering_refuses_without_repair'])
if __name__=='__main__':unittest.main(verbosity=2)
