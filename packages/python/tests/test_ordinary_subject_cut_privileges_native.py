# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fixed native least-privilege cut spike; no production policy/release admission.
@covers US-056-AC5
@covers US-056-AC10
"""
import unittest,json,os,hashlib
from pathlib import Path
import psycopg
from unittest.mock import patch
from truss.psycopg_host import adopt_psycopg_host
from truss.execution import Ok,Error
from truss._umf_key_tuples import encode_literal_key_tuple
import test_psycopg_epoch_cut_native as epoch_tests
ROOT=Path(__file__).resolve().parents[3]

class OrdinarySubjectCutPrivilegeTests(unittest.TestCase):
 isolated_lifecycle=True
 run_pg=classmethod(epoch_tests.PsycopgEpochCutNativeTests.run_pg.__func__)
 @classmethod
 def setUpClass(cls):
  epoch_tests.PsycopgEpochCutNativeTests.setUpClass.__func__(cls)
  with psycopg.connect(host=str(cls.socket),user='postgres',dbname=cls.database,autocommit=True) as c:
   c.execute("CREATE ROLE cut_owner NOLOGIN NOSUPERUSER NOBYPASSRLS;CREATE ROLE cut_reader NOLOGIN;CREATE ROLE cut_alice LOGIN;CREATE ROLE cut_outsider LOGIN;GRANT cut_reader TO cut_alice;CREATE TABLE truss.spike_subject_fact(actor text PRIMARY KEY,staff_id text NOT NULL);INSERT INTO truss.spike_subject_fact VALUES('cut_alice','s1'),('cut_outsider','s2')")
   c.execute('GRANT SELECT,MAINTAIN ON truss.source_epoch_current,truss.source_epoch_registry,truss.spike_subject_fact TO cut_owner;GRANT USAGE,CREATE ON SCHEMA truss TO cut_owner;GRANT USAGE ON SCHEMA truss TO cut_reader,cut_outsider')
   c.execute((ROOT/'docs/helix/02-design/spikes/security/ordinary-subject-cut-definer-v0.1.sql').read_text())
   c.execute('ALTER FUNCTION truss.spike_acquire_ordinary_subject_cut(text,text,text) OWNER TO cut_owner;GRANT EXECUTE ON FUNCTION truss.spike_acquire_ordinary_subject_cut(text,text,text) TO cut_reader')
   c.execute('REVOKE CREATE ON SCHEMA truss FROM cut_owner')
 tearDownClass=classmethod(epoch_tests.PsycopgEpochCutNativeTests.tearDownClass.__func__)
 def test_least_privilege_cut_and_original_key_share_host_operation(self):
  import sys
  module_dir=os.environ['TRUSS_SUBJECT_OWNER_MODULE_DIR']
  sys.path.insert(0,module_dir)
  import weft
  self.assertEqual(Path(weft.__file__).resolve(),(Path(module_dir)/'weft.so').resolve())
  request=(ROOT/'packages/python/tests/fixtures/security-mapping-request.json').read_text()
  document=json.loads(request)['modules'][0]['documentJson'].encode()
  probe=json.dumps({'sourceSha256':hashlib.sha256(document).hexdigest(),'identity':{'module':'m','element':'Staff','key':'pk'}})
  inspected=json.loads(weft.inspect_security_mapping_subject_key_json(request,probe))
  self.assertEqual(inspected,{'interfaceVersion':'weft-security-subject-selection/0.1.0','status':'inspected','securityReady':False})
  params={'host':str(self.socket),'dbname':self.database,'autocommit':True,'options':'-c statement_timeout=2000'}
  with psycopg.connect(**params,user='cut_alice') as actor,psycopg.connect(**params,user='postgres') as admin:
   host=adopt_psycopg_host(actor)
   try:
    admin.execute("UPDATE truss.spike_subject_fact SET staff_id='s1' WHERE actor='cut_alice';SET lock_timeout='100ms'")
    actor.execute('BEGIN');transaction=host.adopt_transaction();self.assertIsInstance(transaction,Ok)
    encoded=[]
    def acquire(cursor,observed):
     cursor.execute('SELECT * FROM truss.spike_acquire_ordinary_subject_cut(%s,%s,%s)',('fixture',self.epoch,'target'),prepare=False,binary=False)
     names=('installation_id','source_epoch','target_incarnation','profile_hex','evidence_hex','evidence_sha256','actual_xid','actual_database_oid','actual_backend_pid','original_actor','privileged_actor','staff_id')
     self.assertEqual(tuple(d.name for d in cursor.description),names)
     self.assertTrue(all(d.type_code==25 for d in cursor.description))
     rows=cursor.fetchmany(2);self.assertEqual(len(rows),1);row=rows[0]
     self.assertEqual(row[:6],('fixture',self.epoch,'target','01','02',hashlib.sha256(b'\x02').hexdigest()))
     self.assertEqual(row[-3:],('cut_alice','cut_owner','s1'))
     self.assertEqual(row[8],observed[0][0])
     cursor.execute("SELECT pg_current_xact_id()::text,(SELECT oid::text FROM pg_database WHERE datname=current_database()),pg_backend_pid()::text,SESSION_USER::text,CURRENT_USER::text",prepare=False,binary=False)
     self.assertTrue(all(d.type_code==25 for d in cursor.description))
     self.assertEqual(cursor.fetchmany(2),[(*row[6:9],'cut_alice','cut_alice')])
     with self.assertRaises(psycopg.errors.LockNotAvailable):admin.execute("UPDATE truss.spike_subject_fact SET staff_id='revoked' WHERE actor='cut_alice'")
     result=encode_literal_key_tuple(document,('m','Staff','pk'),(json.dumps({'string':row[-1]}),),bun_executable='/opt/homebrew/bin/bun')
     encoded.append(True)
     return result
    result=host._run_operation(transaction.value,acquire)
    self.assertIsInstance(result,Ok,str(host._custody.last_attempt.error));self.assertEqual(encoded,[True])
    self.assertEqual(json.loads(result.value.original_receipt_bytes)['values'],[{'string':'s1'}])
    with self.assertRaises(psycopg.errors.LockNotAvailable):admin.execute("UPDATE truss.spike_subject_fact SET staff_id='revoked' WHERE actor='cut_alice'")
    actor.execute('ROLLBACK');admin.execute("UPDATE truss.spike_subject_fact SET staff_id='revoked' WHERE actor='cut_alice'")
    # A failed original codec cannot publish a host result or retain its acquired locks.
    admin.execute("UPDATE truss.spike_subject_fact SET staff_id='s1' WHERE actor='cut_alice'")
    actor.execute('BEGIN');transaction=host.adopt_transaction();self.assertIsInstance(transaction,Ok)
    with patch(__name__+'.encode_literal_key_tuple',side_effect=ValueError('original codec refusal')) as codec:
     refused=host._run_operation(transaction.value,acquire)
    self.assertIsInstance(refused,Error);codec.assert_called_once()
    attempt=host._custody.last_attempt
    self.assertIsInstance(attempt.error,ValueError);self.assertEqual(str(attempt.error),'original codec refusal')
    self.assertEqual(attempt.phase,'contained');self.assertIsNone(attempt.cleanup_error)
    admin.execute("UPDATE truss.spike_subject_fact SET staff_id='after_failure' WHERE actor='cut_alice'")
    actor.execute('ROLLBACK')
    output=os.environ.get('TRUSS_ORDINARY_KEY_COMPOSITION_EVIDENCE')
    if output:Path(output).write_text(json.dumps({'cases':['original Weft ontology subject selection','least-privilege cut inside original host operation','native writer excluded during original UMF encoding','held cut survives successful operation until caller rollback','original codec failure refuses and releases operation locks'],'receipt':json.loads(result.value.original_receipt_bytes),'scope':'Fixed-home spike composition only; test-authored correspondence, not authenticated generic installer, complete callable closure or protected query release'},indent=2)+'\n')
   finally:host.detach()
 def test_ordinary_cut_without_direct_source_or_fact_privileges(self):
  cases=[];params={'host':str(self.socket),'dbname':self.database,'autocommit':True,'options':'-c statement_timeout=2000'}
  with psycopg.connect(**params,user='cut_alice') as actor,psycopg.connect(**params,user='postgres') as admin,psycopg.connect(**params,user='cut_outsider') as outsider:
   admin.execute("UPDATE truss.spike_subject_fact SET staff_id='s1' WHERE actor='cut_alice'")
   args=('fixture',self.epoch,'target');call='SELECT * FROM truss.spike_acquire_ordinary_subject_cut(%s,%s,%s)'
   for relation in ['source_epoch_current','source_epoch_registry','spike_subject_fact']:
    for statement in [f'SELECT * FROM truss.{relation}',f'DELETE FROM truss.{relation}',f'TRUNCATE truss.{relation}']:
     with self.assertRaises(psycopg.errors.InsufficientPrivilege):actor.execute(statement)
     cases.append('direct denied: '+statement)
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):actor.execute("UPDATE truss.spike_subject_fact SET staff_id='forged'")
   cases.append('direct fact update denied')
   for relation,column in [('source_epoch_current','source_epoch'),('source_epoch_registry','source_epoch')]:
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):actor.execute(f'UPDATE truss.{relation} SET {column}={column}')
    cases.append('direct source update denied '+relation)

   with self.assertRaises(psycopg.errors.InsufficientPrivilege):outsider.execute(call,args)
   cases.append('outsider execute denied despite own fact row')
   for role in ['cut_owner','postgres']:
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):actor.execute('SET ROLE '+role)
    cases.append('privileged role adoption denied '+role)
   actor.execute('BEGIN');actor.execute('SAVEPOINT before_cut')
   row=actor.execute(call,args).fetchone()
   self.assertEqual(row[:6],('fixture',self.epoch,'target','01','02',hashlib.sha256(b'\x02').hexdigest()))
   self.assertEqual(row[-3:],('cut_alice','cut_owner','s1'))
   self.assertEqual(actor.execute('SELECT SESSION_USER::text,CURRENT_USER::text').fetchone(),('cut_alice','cut_alice'))
   cases.append('caller kept separate from fixed no-login privileged owner')
   admin.execute("SET lock_timeout='100ms'")
   with self.assertRaises(psycopg.errors.LockNotAvailable):admin.execute("UPDATE truss.spike_subject_fact SET staff_id='changed' WHERE actor='cut_alice'")
   cases.append('fact writer blocked after returned cut until outer rollback')
   actor.execute('ROLLBACK TO SAVEPOINT before_cut')
   admin.execute("UPDATE truss.spike_subject_fact SET staff_id='after_savepoint' WHERE actor='cut_alice'")
   cases.append('rollback past acquisition releases cut; returned rows are historical')
   actor.execute('ROLLBACK')
   admin.execute("UPDATE truss.spike_subject_fact SET staff_id='fresh' WHERE actor='cut_alice'")
   actor.execute('BEGIN');self.assertEqual(actor.execute(call,args).fetchone()[-1],'fresh');actor.execute('ROLLBACK');cases.append('new cut sees committed fact')
   admin.execute('BEGIN');admin.execute("UPDATE truss.spike_subject_fact SET staff_id='pending' WHERE actor='cut_alice'")
   with self.assertRaises(psycopg.errors.LockNotAvailable):actor.execute(call,args)
   admin.execute('ROLLBACK');cases.append('pending writer refuses cut')
   for begin in ['BEGIN READ ONLY','BEGIN ISOLATION LEVEL REPEATABLE READ']:
    actor.execute(begin)
    with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):actor.execute(call,args)
    actor.execute('ROLLBACK');cases.append('profile refused '+begin)
   with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):actor.execute(call,('fixture','foreign','target'))
   cases.append('wrong epoch refused')
   actor.execute('SET ROLE cut_reader')
   with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):actor.execute(call,args)
   actor.execute('RESET ROLE');cases.append('changed effective caller refused')
   privs=admin.execute("SELECT rolsuper,rolbypassrls,rolcanlogin FROM pg_roles WHERE rolname='cut_owner'").fetchone();self.assertEqual(privs,(False,False,False))
   for relation in ['source_epoch_current','source_epoch_registry','spike_subject_fact']:
    self.assertEqual(admin.execute("SELECT has_table_privilege('cut_alice',%s,'SELECT'),has_table_privilege('cut_alice',%s,'UPDATE'),has_table_privilege('cut_owner',%s,'UPDATE')",('truss.'+relation,)*3).fetchone(),(False,False,False))
    for privilege in ['INSERT','DELETE','TRUNCATE']:
     self.assertFalse(admin.execute("SELECT has_table_privilege('cut_owner',%s,%s)",('truss.'+relation,privilege)).fetchone()[0])
   cases.append('effective caller and owner table rights checked independently')
   output=os.environ.get('TRUSS_ORDINARY_CUT_EVIDENCE')
   if output:Path(output).write_text(json.dumps({'serverVersion':admin.execute('SHOW server_version').fetchone()[0],'cases':cases,'nativeProjection':row,'scope':'Fixed declared-home SECURITY DEFINER spike; no direct source/fact table rights for caller, ownerSELECT/MAINTAIN only; not complete native callable/role/configclosure, issuer/currentauthority, genericstorageinstallation or protectedqueryrelease'},indent=2)+'\n')
