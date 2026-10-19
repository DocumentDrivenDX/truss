# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native original source marker construction; no protected profile activation."""
from dataclasses import replace
from truss import Ok,Error
from truss._security_catalog_source_installation import bootstrap_catalog_source_marker_in_transaction
import test_security_catalog_subject_native as subject

class CatalogSourceInstallationTests(subject.NativeCatalogSubjectTests):
 for name in tuple(n for n in dir(subject.NativeCatalogSubjectTests) if n.startswith('test_')):locals()[name]=None
 def test_original_release_catalog_archive_and_no_repair(self):
  """@covers US-056-AC10; source issuer construction prerequisite."""
  mapping,*_=self.setup_subject()
  result=bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,mapping)
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertFalse(result.value.security_ready)
  self.assertEqual(result.value.installation_id,self.installation.installation_id)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_archive').fetchone(),(6,))
  self.assertIsInstance(bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,mapping),Error)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_archive').fetchone(),(6,))
 def test_substituted_catalog_has_no_marker_effect(self):
  mapping,*_=self.setup_subject()
  bad=replace(mapping,accepted_catalog_assessment=mapping.accepted_catalog_assessment+b' ')
  result=bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,bad)
  self.assertIsInstance(result,Error)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_marker').fetchone(),(0,))

 def test_hostile_function_resolution_is_pinned_and_restored(self):
  mapping,*_=self.setup_subject()
  self.admin.execute("CREATE SCHEMA hostile_source;CREATE FUNCTION hostile_source.clock_timestamp() RETURNS timestamptz LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'hostile clock executed'; END$$;CREATE FUNCTION hostile_source.current_database() RETURNS name LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'hostile database executed'; END$$")
  self.addCleanup(self.admin.execute,'DROP SCHEMA IF EXISTS hostile_source CASCADE')
  self.admin.execute('SET LOCAL search_path=hostile_source,pg_catalog')
  result=bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,mapping)
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  self.assertEqual(self.admin.execute("SELECT pg_catalog.current_setting('search_path')").fetchone(),('hostile_source, pg_catalog',))

 def test_caller_rollback_leaves_no_marker_or_archive(self):
  mapping,*_=self.setup_subject()
  self.admin.execute('CREATE TEMP TABLE original_source_work(value text)');self.admin.execute("INSERT INTO original_source_work VALUES('kept')")
  self.admin.execute('SAVEPOINT before_source_marker')
  self.assertIsInstance(bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,mapping),Ok)
  self.admin.execute('ROLLBACK TO before_source_marker')
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_marker').fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_archive').fetchone(),(0,))
  self.assertEqual(self.admin.execute('TABLE original_source_work').fetchall(),[('kept',)])
 def test_suppressed_archive_insert_refuses_and_rolls_back(self):
  mapping,*_=self.setup_subject()
  self.admin.execute("CREATE FUNCTION truss.source_archive_suppress() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RETURN NULL;END$$;CREATE TRIGGER source_archive_suppress BEFORE INSERT ON truss.installation_archive FOR EACH ROW EXECUTE FUNCTION truss.source_archive_suppress()")
  result=bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,mapping)
  self.assertIsInstance(result,Error)
  self.assertEqual(str(self.host._custody.last_attempt.error),'Exact original catalog source archive readback required')
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_marker').fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_archive').fetchone(),(0,))
 def test_ordinary_caller_cannot_install_marker(self):
  mapping,c,h,t,*_=self.setup_subject()
  result=bootstrap_catalog_source_marker_in_transaction(h,t,mapping)
  self.assertIsInstance(result,Error)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.installation_marker').fetchone(),(0,))

 def test_committed_archive_retains_exact_original_bytes(self):
  from importlib.resources import files
  from hashlib import sha256
  from truss import adopt_psycopg_host
  mapping,*_=self.setup_subject()
  original=files('truss').joinpath('_catalog_runtime','manifest.json').read_bytes()
  result=bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,mapping)
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  self.host.detach();self.admin.commit();self.admin.execute('BEGIN')
  self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  observed=self.admin.execute('SELECT artifact_identity,artifact_bytes,artifact_sha256 FROM truss.installation_archive ORDER BY artifact_identity COLLATE pg_catalog."C"').fetchall()
  expected=[('catalog:original-accepted-assessment',mapping.accepted_catalog_assessment),('catalog:original-release-manifest',original),('catalog:recaptured-accepted-assessment',mapping.accepted_catalog_assessment),('catalog:original-mapping-request',mapping.original_request),('catalog:original-compiler-handoff',mapping.original_response),('catalog:original-native-dependencies',mapping.native_dependencies)]
  expected.sort(key=lambda row:row[0])
  self.assertEqual(observed,[(name,raw,sha256(raw).digest()) for name,raw in expected])

 def test_original_carriers_are_captured_before_native_callbacks(self):
  """@covers US-056-AC6/AC9; source custody before host callback."""
  from unittest.mock import patch
  import truss._security_catalog_source_installation as installation
  mapping,*_=self.setup_subject()
  original=(mapping.original_request,mapping.original_response,mapping.accepted_catalog_assessment,mapping.native_dependencies)
  release=installation._release
  def mutate():
   for name,raw in zip(('original_request','original_response','accepted_catalog_assessment','native_dependencies'),original):
    object.__setattr__(mapping,name,raw+b' ')
   return release()
  with patch.object(installation,'_release',mutate):
   result=bootstrap_catalog_source_marker_in_transaction(self.host,self.tx,mapping)
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  for identity,raw in zip(('catalog:original-mapping-request','catalog:original-compiler-handoff','catalog:original-accepted-assessment','catalog:original-native-dependencies'),original):
   self.assertEqual(self.admin.execute('SELECT artifact_bytes FROM truss.installation_archive WHERE artifact_identity=%s',(identity,)).fetchall(),[(raw,)])
