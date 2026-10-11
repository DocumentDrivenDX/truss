"""Event refusal controls on actual Truss relations; not DDL/ordinary-role custody."""
import importlib.util,json,unittest
from pathlib import Path
import psycopg
ROOT=Path(__file__).resolve().parents[5];DRAFT=ROOT/'packages/postgresql/native/catalog-event-guards'
spec=importlib.util.spec_from_file_location('connected',ROOT/'docs/helix/04-build/evidence/catalog-finalization-pg18/check.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Events(m.Finalization):
 additional_install_paths=m.Finalization.additional_install_paths+(str(DRAFT/'business-statement-guards.owner-export.sql'),str(DRAFT/'business-guard-inventory.owner-export.sql'))
 def setUp(self):
  # No catalog admission/custody/source packet is needed for an unconditional
  # selected business guard. Keep the baseline caller transaction intact.
  m.CustodyBranchNativeTests.setUp(self)
 def refused(self,query,params=None):
  self.query('SAVEPOINT refusal')
  try:
   with self.assertRaises(psycopg.Error) as error:self.query(query,params)
   self.assertEqual(error.exception.sqlstate,'0A000');self.assertIn('business writes are outside selected catalog-only scope',str(error.exception))
  finally:self.query('ROLLBACK TO SAVEPOINT refusal');self.query('RELEASE SAVEPOINT refusal')
 def test_all26_zero_row_statement_paths_and_truncate(self):
  names=json.loads((ROOT/'packages/python/src/truss/_profiles/catalog-only-business-guards-candidate.json').read_bytes())['relations']
  self.assertEqual(self.query('SELECT count(*) FROM truss.row_home_operation').fetchone(),(0,))
  for name in names:
   columns=self.query("SELECT attname FROM pg_attribute WHERE attrelid=%s::regclass AND attnum>0 AND NOT attisdropped AND attgenerated='' AND attidentity<>'a' ORDER BY attnum",('truss.'+name,)).fetchall()
   quoted=','.join('"'+c[0].replace('"','""')+'"' for c in columns)
   self.refused('INSERT INTO truss.'+name+' ('+quoted+') SELECT '+quoted+' FROM truss.'+name+' WHERE false')
   column=self.query("SELECT attname FROM pg_attribute WHERE attrelid=%s::regclass AND attnum>0 AND NOT attisdropped AND attgenerated='' ORDER BY attnum LIMIT 1",('truss.'+name,)).fetchone()[0]
   # All names/columns come from selected native catalogs, not user SQL input.
   self.refused('UPDATE truss.'+name+' SET "'+column.replace('"','""')+'"="'+column.replace('"','""')+'" WHERE false')
   self.refused('DELETE FROM truss.'+name+' WHERE false')
   self.refused('TRUNCATE truss.'+name+' CASCADE')
  self.assertEqual(self.query('SELECT count(*) FROM truss.row_home_operation').fetchone(),(0,))
 def test_copy_merge_replica_mode_and_external_caller_work(self):
  self.query('CREATE TEMP TABLE caller_work(v text)');self.query("INSERT INTO caller_work VALUES ('keep')")
  self.query('SAVEPOINT copy_refusal')
  try:
   with self.assertRaises(psycopg.Error) as error:
    with self.connection.cursor().copy('COPY truss.object FROM STDIN') as copy:pass
   self.assertEqual(error.exception.sqlstate,'0A000')
  finally:self.query('ROLLBACK TO SAVEPOINT copy_refusal');self.query('RELEASE SAVEPOINT copy_refusal')
  self.refused('MERGE INTO truss.object t USING (SELECT NULL::bigint id WHERE false) s ON t.id=s.id WHEN MATCHED THEN DELETE')
  self.query("SET LOCAL session_replication_role='replica'");self.refused('DELETE FROM truss.object WHERE false')
  self.query("SET LOCAL session_replication_role='origin'")
  self.assertEqual(self.query('SELECT v FROM caller_work').fetchall(),[('keep',)])
 def test_exact_guard_inventory_and_disable_refusal(self):
  self.query('SELECT truss.runtime_require_catalog_only_business_guards_candidate()')
  self.query('SAVEPOINT broken_guard');self.query('ALTER TABLE truss.object DISABLE TRIGGER a_truss_catalog_only_business_refusal')
  with self.assertRaises(psycopg.Error) as error:self.query('SELECT truss.runtime_require_catalog_only_business_guards_candidate()')
  self.assertEqual(error.exception.sqlstate,'55000');self.query('ROLLBACK TO SAVEPOINT broken_guard');self.query('RELEASE SAVEPOINT broken_guard')
  self.query('SELECT truss.runtime_require_catalog_only_business_guards_candidate()')
def load_tests(loader,tests,pattern):return unittest.TestSuite(Events(n) for n in ['test_all26_zero_row_statement_paths_and_truncate','test_copy_merge_replica_mode_and_external_caller_work','test_exact_guard_inventory_and_disable_refusal'])
if __name__=='__main__':unittest.main(verbosity=2)
