"""Fixed native least-privilege cut spike; no production policy/release admission.
@covers US-056-AC5
@covers US-056-AC10
"""
import unittest,json,os,hashlib
from pathlib import Path
import psycopg
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
 def test_ordinary_cut_without_direct_source_or_fact_privileges(self):
  cases=[];params={'host':str(self.socket),'dbname':self.database,'autocommit':True,'options':'-c statement_timeout=2000'}
  with psycopg.connect(**params,user='cut_alice') as actor,psycopg.connect(**params,user='postgres') as admin,psycopg.connect(**params,user='cut_outsider') as outsider:
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
