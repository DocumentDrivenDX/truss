"""Original named Subject construction and bounded native role registration."""
from truss import Ok,Error
from truss._security_catalog_subject_installation import bootstrap_catalog_subjects_in_transaction
import test_security_catalog_read_native as catalog

class CatalogSubjectInstallationNativeTests(catalog.AcceptedCatalogReadNativeTests):
 for name in tuple(n for n in dir(catalog.AcceptedCatalogReadNativeTests) if n.startswith('test_')):locals()[name]=None
 def install_subjects(self,mapping,bindings=(('consumer','s1'),)):
  return bootstrap_catalog_subjects_in_transaction(self.host,self.tx,mapping=mapping,bindings=bindings)
 def no_subjects(self):
  self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relname='catalog_subject_map'").fetchone(),(0,))
  self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND p.proname IN ('catalog_subject_current','catalog_subject_context')").fetchone(),(0,))
 def test_original_subject_registration_and_no_repair(self):
  """@covers US-056-AC2/AC9/AC10; original Subject construction prerequisite."""
  mapping=self.populated();result=self.install_subjects(mapping)
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertFalse(result.value.security_ready)
  self.assertEqual(result.value.installation_id,self.installation.installation_id)
  self.assertEqual(self.admin.execute('SELECT role_oid::text,staff_key FROM truss.catalog_subject_map').fetchall(),[(str(result.value.bindings[0][0]),'s1')])
  self.assertIsInstance(self.install_subjects(mapping),Error)
 def test_missing_staff_refuses_before_subject_effects(self):
  mapping=self.populated();self.assertIsInstance(self.install_subjects(mapping,(('consumer','missing'),)),Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Unique original stored Staff identity required');self.no_subjects()
 def test_multiple_native_role_bindings_match_exact_helper_acl(self):
  mapping=self.populated();self.admin.execute('CREATE ROLE second_subject LOGIN')
  result=self.install_subjects(mapping,(('consumer','s1'),('second_subject','s1')))
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(len(result.value.bindings),2)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_subject_map').fetchone(),(2,))
 def test_unsafe_login_role_refuses_before_subject_effects(self):
  mapping=self.populated();self.admin.execute('CREATE ROLE unsafe_subject LOGIN BYPASSRLS')
  self.assertIsInstance(self.install_subjects(mapping,(('unsafe_subject','s1'),)),Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original ordinary login Subject principal required');self.no_subjects()
 def test_outer_rollback_retains_prior_caller_work(self):
  mapping=self.populated();self.admin.execute("CREATE TEMP TABLE prior_subject_work(value text);INSERT INTO prior_subject_work VALUES('kept');SAVEPOINT before_subjects")
  self.assertIsInstance(self.install_subjects(mapping),Ok,str(self.host._custody.last_attempt.error))
  self.admin.execute('ROLLBACK TO before_subjects');self.no_subjects()
  self.assertEqual(self.admin.execute('TABLE prior_subject_work').fetchall(),[('kept',)])

 def test_missing_owner_select_default_refuses_without_subject_residue(self):
  """@covers US-056-AC9/AC10; direct owner-only ACL alone does not prove SELECT."""
  from psycopg import sql
  mapping=self.populated();actor=self.admin.execute('SELECT SESSION_USER::pg_catalog.text').fetchone()[0]
  self.admin.execute(sql.SQL('ALTER DEFAULT PRIVILEGES REVOKE SELECT ON TABLES FROM {}').format(sql.Identifier(actor)))
  result=self.install_subjects(mapping);self.assertIsInstance(result,Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original Subject helper owner read privileges required');self.no_subjects()
 def test_registered_second_login_observes_only_its_native_subject(self):
  """@covers US-056-AC2; actual second native session/helper source, not full read admission."""
  import psycopg
  mapping=self.populated();self.admin.execute('CREATE ROLE second_login_subject LOGIN')
  registered=self.install_subjects(mapping,(('consumer','s1'),('second_login_subject','s1')))
  self.assertIsInstance(registered,Ok,str(self.host._custody.last_attempt.error))
  self.host.detach();self.admin.commit()
  parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']='second_login_subject'
  with psycopg.connect(**parameters,autocommit=True) as caller:
   self.assertEqual(caller.execute('SELECT SESSION_USER::pg_catalog.text').fetchone(),('second_login_subject',))
   self.assertEqual(caller.execute('SELECT * FROM truss.catalog_subject_current(%s)',('second_login_subject',)).fetchall(),[('s1',)])
   self.assertEqual(caller.execute('SELECT * FROM truss.catalog_subject_current(%s)',('consumer',)).fetchall(),[])
   self.assertEqual(caller.execute("SELECT pg_catalog.has_table_privilege('truss.catalog_subject_map','SELECT')").fetchone(),(False,))
