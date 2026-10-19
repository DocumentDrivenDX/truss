# SPDX-License-Identifier: MIT OR Apache-2.0
"""Declared-cut native composition; broad fixture grants are not protected admission.
@covers US-056-AC2
@covers US-056-AC10
"""
import unittest,json,os,sys,hashlib
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace
import psycopg
import test_psycopg_epoch_cut_native as epoch_tests
from truss.execution import Ok,Error
from truss.psycopg_host import adopt_psycopg_host
from truss._psycopg_epoch_cut import _EpochComparison
from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison
from truss._psycopg_subject_observation import _SubjectSelection,_observe_fenced_subject_key,_observe_ordinary_subject_key
from truss._umf_key_tuples import encode_literal_key_tuple
ROOT=Path(__file__).resolve().parents[3]

class FencedSubjectKeyNativeTests(unittest.TestCase):
 isolated_lifecycle=True
 run_pg=classmethod(epoch_tests.PsycopgEpochCutNativeTests.run_pg.__func__)
 @classmethod
 def setUpClass(cls):
  epoch_tests.PsycopgEpochCutNativeTests.setUpClass.__func__(cls)
  with psycopg.connect(host=str(cls.socket),user='postgres',dbname=cls.database,autocommit=True) as c:
   c.execute("CREATE ROLE fenced_alice LOGIN;CREATE TABLE truss.subject_fact(staff_id text NOT NULL);INSERT INTO truss.subject_fact VALUES('old')")
   c.execute((ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text())
   c.execute('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON truss.subject_fact FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write();ALTER TABLE truss.subject_fact ENABLE ALWAYS TRIGGER fact_write_fence')
   c.execute("CREATE FUNCTION truss.subject_current(actor text) RETURNS TABLE(staff_id text) LANGUAGE sql SET search_path=pg_catalog AS $$ SELECT f.staff_id FROM truss.subject_fact f WHERE actor=SESSION_USER::text AND actor='fenced_alice' $$")
   # Deliberately broad invoker fixture grants; bypass-safe production installation remains missing.
   c.execute('GRANT USAGE ON SCHEMA truss TO fenced_alice;GRANT ALL ON truss.source_epoch_current,truss.source_epoch_registry,truss.subject_fact TO fenced_alice')
   c.execute('GRANT EXECUTE ON FUNCTION truss.runtime_lock_source_epoch(text,text,text),truss.runtime_lock_fresh_source_epoch(text,text,text),truss.runtime_lock_fenced_fresh_source_epoch(text,text,text),truss.runtime_fence_authorization_fact_write() TO fenced_alice')
   oid,owner=c.execute("SELECT oid,relowner FROM pg_class WHERE oid='truss.subject_fact'::regclass").fetchone()
   collation=c.execute("SELECT attcollation FROM pg_attribute WHERE attrelid='truss.subject_fact'::regclass AND attname='staff_id'").fetchone()[0]
   body=(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0]
   cls.relations=(_FactRelationComparison('truss','subject_fact',oid,owner,body,(_FactColumnComparison('staff_id',1,25,-1,True,collation),)),)
 tearDownClass=classmethod(epoch_tests.PsycopgEpochCutNativeTests.tearDownClass.__func__)
 def test_fresh_declared_fact_cut_and_subject_key_share_original_operation(self):
  module_dir=os.environ.get('TRUSS_SUBJECT_OWNER_MODULE_DIR')
  if not module_dir:raise RuntimeError('Original source owner module required')
  sys.path.insert(0,module_dir);import weft
  self.assertEqual(Path(weft.__file__).resolve(),(Path(module_dir)/'weft.so').resolve())
  request=(ROOT/'packages/python/tests/fixtures/security-mapping-request.json').read_bytes()
  source=json.loads(request)['modules'][0]['documentJson'].encode()
  selection=_SubjectSelection(request,source,'m','Staff','pk','fenced_alice','truss','subject_current',('staff_id',))
  comparison=_EpochComparison('fixture',self.epoch,'target',b'\x01',b'\x02')
  c=psycopg.connect(host=str(self.socket),user='fenced_alice',dbname=self.database,autocommit=True,options='-c statement_timeout=2000')
  admin=psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database,autocommit=True,options='-c statement_timeout=2000')
  host=adopt_psycopg_host(c)
  try:
   c.execute('BEGIN');self.assertEqual(c.execute('SELECT staff_id FROM truss.subject_fact').fetchone(),('old',))
   t=host.adopt_transaction();self.assertIsInstance(t,Ok)
   admin.execute("UPDATE truss.subject_fact SET staff_id='fresh'")
   held=[]
   def inspected_encoder(*args,**kwargs):
    with self.assertRaises(psycopg.errors.LockNotAvailable):admin.execute("UPDATE truss.subject_fact SET staff_id='blocked'")
    held.append(True);return encode_literal_key_tuple(*args,**kwargs)
   def bind():return _observe_fenced_subject_key(host,t.value,selection,weft.inspect_security_mapping_subject_key_json,('string',),comparison,self.relations,bun_executable='/opt/homebrew/bin/bun')
   with patch('truss._umf_key_tuples.encode_literal_key_tuple',side_effect=inspected_encoder):
    # NOWAIT on writer side gives deterministic exclusion instead of waiting.
    admin.execute("SET lock_timeout='100ms'")
    result=bind()
   self.assertIsInstance(result,Ok,str(host._custody.last_attempt.error));self.assertEqual(held,[True]);self.assertEqual(result.value.observation.values,('fresh',))
   self.assertEqual(json.loads(result.value.original_receipt_bytes)['values'],[{'string':'fresh'}])
   self.assertIsInstance(_observe_ordinary_subject_key(host,t.value,selection,weft.inspect_security_mapping_subject_key_json,('string',),bun_executable='/opt/homebrew/bin/bun'),Error)
   c.execute('ROLLBACK')
   admin.execute('BEGIN');admin.execute("UPDATE truss.subject_fact SET staff_id='pending'")
   c.execute('BEGIN');t=host.adopt_transaction();self.assertIsInstance(t,Ok)
   self.assertIsInstance(bind(),Error);admin.execute('ROLLBACK');c.execute('ROLLBACK')
   c.execute('BEGIN');t=host.adopt_transaction();self.assertIsInstance(t,Ok)
   bad=(replace(self.relations[0],oid=self.relations[0].oid+1),)
   encoded=[]
   def forbidden_encoder(*args,**kwargs):encoded.append(True);raise AssertionError('must not encode')
   with patch('truss._umf_key_tuples.encode_literal_key_tuple',side_effect=forbidden_encoder):
    self.assertIsInstance(_observe_fenced_subject_key(host,t.value,selection,weft.inspect_security_mapping_subject_key_json,('string',),comparison,bad,bun_executable='/opt/homebrew/bin/bun'),Error)
   self.assertEqual(encoded,[]);c.execute('ROLLBACK')
   c.execute('BEGIN');t=host.adopt_transaction();self.assertIsInstance(t,Ok)
   def same_writer_encoder(*args,**kwargs):
    c.execute("UPDATE truss.subject_fact SET staff_id='forbidden'")
    return encode_literal_key_tuple(*args,**kwargs)
   with patch('truss._umf_key_tuples.encode_literal_key_tuple',side_effect=same_writer_encoder):self.assertIsInstance(bind(),Error)
   self.assertEqual(admin.execute('SELECT staff_id FROM truss.subject_fact').fetchone(),('fresh',));c.execute('ROLLBACK')
   c.execute('BEGIN READ ONLY');ro=host.adopt_transaction(access_mode='read_only');self.assertIsInstance(ro,Ok)
   self.assertIsInstance(_observe_fenced_subject_key(host,ro.value,selection,weft.inspect_security_mapping_subject_key_json,('string',),comparison,self.relations,bun_executable='/opt/homebrew/bin/bun'),Error)
   c.execute('ROLLBACK')
   output=os.environ.get('TRUSS_FENCED_SUBJECT_EVIDENCE')
   if output:Path(output).write_text(json.dumps({'serverVersion':admin.execute('SHOW server_version').fetchone()[0],'cases':['read committed sees post-transaction-start committed subject value','writer blocked during original codec','pending writer refuses acquisition','original stable profile still rejects read committed','fenced profile rejects read-only','wrong relation binding refuses before encoder','same-reader write refuses without changing fact'],'observedValues':result.value.observation.values,'originalReceipt':result.value.original_receipt_bytes.decode(),'scope':'Ordinary-role source/declared fact cut component with deliberately broad invoker fixture grants; not bypass-safe installation, complete dependency closure, role/helper/configwriter exclusion, current authority or protected release'},indent=2)+'\n')
  finally:host.detach();c.close();admin.close()
