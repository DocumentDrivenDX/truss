"""Original core0.8 native catalog metadata; protected security remains unqualified.
@covers US-056-AC2
@covers US-056-AC9
@covers US-056-AC10
"""
import json,os,pickle,subprocess,sys,tempfile
from types import SimpleNamespace
from pathlib import Path
import psycopg
from truss import Ok,Error,CatalogDocument,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
import test_catalog_runtime_native as catalog
from truss._catalog_support import CORE08_PROFILE
FIXTURE=Path(__file__).parent/'fixtures/security-mapping-request.json'
class Core08CatalogNativeTests(catalog.PublicCatalogRuntimeTests):
 for name in tuple(n for n in dir(catalog.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[name]=None
 def source08(self):
  r=json.loads(FIXTURE.read_text());m=r['modules'][0];p=m['pin']
  return (CatalogDocument(p['documentId'],p['revision'],m['documentJson'].encode()),)
 def test_original08_prepare_register_commit_report_and_view(self):
  self.install();c,h,a,t=self.consumer()
  prepared=a.prepare_catalog(self.source08(),source_version='0.8.0',bun_executable='/opt/homebrew/bin/bun')
  self.assertEqual(prepared.input()['supportProfile'],CORE08_PROFILE)
  c.execute("CREATE TEMP TABLE prior08(value text);INSERT INTO prior08 VALUES('kept')")
  registered=a.accept_in_transaction(t,prepared,request_key='native08-original')
  self.assertIsInstance(registered,Ok,str(h._custody.last_attempt.error))
  self.assertEqual(c.execute('TABLE prior08').fetchall(),[('kept',)])
  h.detach();c.commit()
  self.assertEqual(self.admin.execute('SELECT umf_version,document FROM truss.schema_doc').fetchall(),[('0.8.0',self.source08()[0].content.decode())])
  c,h,a,t=self.consumer();view=a.catalog_view_in_transaction(t,a.catalog_view_request())
  self.assertIsInstance(view,Ok,str(h._custody.last_attempt.error));self.assertEqual(view.value.outcome,'available')
  self.assertGreater(len(view.value.view.definitions),20)
  self.assertEqual(self.admin.execute("SELECT facets FROM truss.prop_def WHERE element='salary'").fetchone(),({'integerWidth':{'bits':64,'signed':True}},))
  self.assertTrue(all(e.provenance.document_revision=='schema-1' for e in view.value.view.definitions))
  report=a.report_in_transaction(t);self.assertIsInstance(report,Ok,str(h._custody.last_attempt.error))
  self.assertEqual(report.value.original_bytes,registered.value.report_bytes)
  retry=a.accept_in_transaction(t,prepared,request_key='native08-original');self.assertIsInstance(retry,Ok);self.assertTrue(retry.value.replayed)
  self.assertEqual(retry.value.report_bytes,registered.value.report_bytes)
 def test_original08_registration_rollback_preserves_prior_work(self):
  self.install();c,h,a,t=self.consumer();prepared=a.prepare_catalog(self.source08(),source_version='0.8.0',bun_executable='/opt/homebrew/bin/bun')
  c.execute("CREATE TEMP TABLE rollback_prior08(value text);INSERT INTO rollback_prior08 VALUES('kept');SAVEPOINT caller_before08")
  registered=a.accept_in_transaction(t,prepared,request_key='rollback08');self.assertIsInstance(registered,Ok,str(h._custody.last_attempt.error))
  c.execute('ROLLBACK TO SAVEPOINT caller_before08');self.assertEqual(c.execute('TABLE rollback_prior08').fetchall(),[('kept',)])
  h.detach();c.commit()
  self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_registration_request').fetchone(),(0,))

 def test_missing_null_and_wrong_profile_refuse_without_partial_registration(self):
  self.install();c,h,a,t=self.consumer();prepared=a.prepare_catalog((CatalogDocument(catalog.relational_document()['id'],'r1',json.dumps(catalog.relational_document()).encode()),),bun_executable='/opt/homebrew/bin/bun')
  c.execute("CREATE TEMP TABLE profile_prior08(value text);INSERT INTO profile_prior08 VALUES('kept')")
  self.admin.execute('SELECT truss.catalog_require_sources(%s,%s,%s)',(prepared.input_bytes,prepared.archive_documents_bytes,prepared.declarations_bytes),prepare=False)
  for mutation in ('missing','null','wrong'):
   payload=prepared.input()
   if mutation=='missing':del payload['supportProfile']
   elif mutation=='null':payload['supportProfile']=None
   else:payload['supportProfile']={'version':'wrong'}
   with self.subTest(mutation=mutation):
    c.execute('SAVEPOINT bad_profile')
    with self.assertRaises(psycopg.errors.InvalidParameterValue):
     self.admin.execute('SELECT truss.catalog_require_sources(%s,%s,%s)',(json.dumps(payload).encode(),prepared.archive_documents_bytes,prepared.declarations_bytes),prepare=False)
    c.execute('ROLLBACK TO bad_profile');c.execute('RELEASE bad_profile')
    self.assertEqual(c.execute('TABLE profile_prior08').fetchall(),[('kept',)])
  h.detach();c.commit()
  self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_registration_request').fetchone(),(0,))

 def test_original08_default_and_allowed_values_correspondence(self):
  self.install();c,h,a,t=self.consumer();original=self.source08()[0];doc=json.loads(original.content)
  field=next(e for e in doc['modules'][0]['elements'] if e['id']=='resourceId')
  field['default']={'value':{'string':'EXACT'},'on':'missing'};field['allowedValues']=[{'string':'EXACT'},{'string':'OTHER'}]
  document=CatalogDocument(original.document_id,original.document_revision,json.dumps(doc).encode())
  prepared=a.prepare_catalog((document,),source_version='0.8.0',bun_executable='/opt/homebrew/bin/bun')
  result=a.accept_in_transaction(t,prepared,request_key='properties08')
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error))
  h.detach();c.commit()
  self.assertEqual(json.loads(self.admin.execute('SELECT document FROM truss.schema_doc').fetchone()[0]),doc)

 def test_populated034_upgrade_rollback_preserves_original_reports_data_and_routines(self):
  source=os.environ.get('TRUSS_CORE08_UPGRADE_SOURCE034')
  if not source:raise RuntimeError('Exact committed runtime0.34 source package required')
  self.host.detach();self.admin.rollback();self.admin.execute('DROP ROLE consumer')
  tests=Path(__file__).parent.resolve()
  with tempfile.TemporaryDirectory(prefix='core08-upgrade-',dir='/private/tmp') as folder:
   artifact=Path(folder)/'original-facts.pickle'
   environment=dict(os.environ,PYTHONPATH=source+os.pathsep+str(tests)+os.pathsep+os.environ.get('PYTHONPATH',''))
   seeded=subprocess.run([sys.executable,str(tests/'_seed_runtime_upgrade_023.py'),self.info.connection_uri,str(artifact)],env=environment,capture_output=True,text=True,timeout=120)
   self.assertEqual(seeded.returncode,0,seeded.stderr)
   documents,original_input,request,identity,token,report,page,next_operation=pickle.loads(artifact.read_bytes())
  for role in ('group_reader','group_writer'):
   self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP OWNED BY {};DROP ROLE {}').format(psycopg.sql.Identifier(role),psycopg.sql.Identifier(role)))
  owner,registrar=self.admin.execute('SELECT o.rolname,r.rolname FROM truss.catalog_runtime_installation i JOIN pg_roles o ON o.oid=i.owner_oid JOIN pg_roles r ON r.oid=i.registrar_oid').fetchone()
  self.installation=SimpleNamespace(owner_role=owner,registrar_role=registrar)
  original_release=self.admin.execute('SELECT release_id,release_sha256 FROM truss.runtime_current_installation()').fetchone()
  self.assertEqual(original_release[0],'truss-catalog-runtime/0.34-candidate')
  original_objects=self.admin.execute('SELECT id,type_id,props::text FROM truss.object ORDER BY id').fetchall();self.assertGreater(len(original_objects),0)
  original_reports=self.admin.execute('SELECT rev,report_bytes FROM truss.catalog_acceptance_report ORDER BY rev').fetchall()
  original_routines=self.admin.execute("SELECT p.oid,p.proowner,p.proacl FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' ORDER BY p.oid").fetchall()
  for commit in (False,True):
   self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
   a=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
   upgraded=a.upgrade_in_transaction(self.tx);self.assertIsInstance(upgraded,Ok,str(self.host._custody.last_attempt.error))
   self.assertEqual(upgraded.value.previous_release_id,original_release[0]);self.assertEqual(upgraded.value.release_id,'truss-catalog-runtime/0.35-candidate')
   self.assertEqual(self.admin.execute('SELECT id,type_id,props::text FROM truss.object ORDER BY id').fetchall(),original_objects)
   self.assertEqual(self.admin.execute('SELECT rev,report_bytes FROM truss.catalog_acceptance_report ORDER BY rev').fetchall(),original_reports)
   self.assertEqual(self.admin.execute("SELECT p.oid,p.proowner,p.proacl FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' ORDER BY p.oid").fetchall(),original_routines)
   self.host.detach()
   if commit:self.admin.commit()
   else:
    self.admin.rollback();self.assertEqual(self.admin.execute('SELECT release_id,release_sha256 FROM truss.runtime_current_installation()').fetchone(),original_release)
    self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_release').fetchone(),(0,))
  c,h,a,t=self.consumer();retained=a.report_in_transaction(t);self.assertIsInstance(retained,Ok);self.assertEqual(retained.value.original_bytes,report)
  prepared=a.prepare_catalog(self.source08(),source_version='0.8.0',bun_executable='/opt/homebrew/bin/bun')
  accepted=a.accept_in_transaction(t,prepared,request_key='after-upgrade08');self.assertIsInstance(accepted,Ok,str(h._custody.last_attempt.error));h.detach();c.commit()
  self.assertEqual(self.admin.execute("SELECT umf_version FROM truss.schema_doc WHERE doc_id='domain'").fetchall(),[('0.8.0',)])
  self.assertEqual(self.admin.execute('SELECT id,type_id,props::text FROM truss.object ORDER BY id').fetchall(),original_objects)
