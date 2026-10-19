# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original core0.10 native catalog metadata; protected security remains unqualified.
@covers US-056-AC2
@covers US-056-AC9
@covers US-056-AC10
"""
import json
from pathlib import Path
import psycopg
from truss import Ok,Error,CatalogDocument,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
import test_catalog_runtime_native as catalog
from truss._catalog_support import DATE10_PROFILE
FIXTURE=Path(__file__).parent/'fixtures/catalog-security-core-umf10.json'
class Core10CatalogNativeTests(catalog.PublicCatalogRuntimeTests):
 for name in tuple(n for n in dir(catalog.PublicCatalogRuntimeTests) if n.startswith('test_')):locals()[name]=None
 def source10(self):
  source=json.loads(FIXTURE.read_text())
  return (CatalogDocument(source['id'],'schema-1',FIXTURE.read_bytes()),)
 def test_original10_prepare_register_commit_report_and_view(self):
  self.install();c,h,a,t=self.consumer()
  prepared=a.prepare_catalog(self.source10(),source_version='0.10.0',bun_executable='/opt/homebrew/bin/bun')
  self.assertEqual(prepared.input()['supportProfile'],DATE10_PROFILE)
  c.execute("CREATE TEMP TABLE prior10(value text);INSERT INTO prior10 VALUES('kept')")
  registered=a.accept_in_transaction(t,prepared,request_key='native10-original')
  self.assertIsInstance(registered,Ok,str(h._custody.last_attempt.error))
  self.assertEqual(c.execute('TABLE prior10').fetchall(),[('kept',)])
  h.detach();c.commit()
  self.assertEqual(self.admin.execute('SELECT umf_version,document FROM truss.schema_doc').fetchall(),[('0.10.0',self.source10()[0].content.decode())])
  c,h,a,t=self.consumer();view=a.catalog_view_in_transaction(t,a.catalog_view_request())
  self.assertIsInstance(view,Ok,str(h._custody.last_attempt.error));self.assertEqual(view.value.outcome,'available')
  self.assertGreater(len(view.value.view.definitions),20)
  self.assertEqual(self.admin.execute("SELECT facets FROM truss.prop_def WHERE element='salary'").fetchone(),({'integerWidth':{'bits':64,'signed':True}},))
  self.assertTrue(all(e.provenance.document_revision=='schema-1' for e in view.value.view.definitions))
  report=a.report_in_transaction(t);self.assertIsInstance(report,Ok,str(h._custody.last_attempt.error))
  self.assertEqual(report.value.original_bytes,registered.value.report_bytes)
  retry=a.accept_in_transaction(t,prepared,request_key='native10-original');self.assertIsInstance(retry,Ok);self.assertTrue(retry.value.replayed)
  self.assertEqual(retry.value.report_bytes,registered.value.report_bytes)
 def test_original10_registration_rollback_preserves_prior_work(self):
  self.install();c,h,a,t=self.consumer();prepared=a.prepare_catalog(self.source10(),source_version='0.10.0',bun_executable='/opt/homebrew/bin/bun')
  c.execute("CREATE TEMP TABLE rollback_prior10(value text);INSERT INTO rollback_prior10 VALUES('kept');SAVEPOINT caller_before10")
  registered=a.accept_in_transaction(t,prepared,request_key='rollback10');self.assertIsInstance(registered,Ok,str(h._custody.last_attempt.error))
  c.execute('ROLLBACK TO SAVEPOINT caller_before10');self.assertEqual(c.execute('TABLE rollback_prior10').fetchall(),[('kept',)])
  h.detach();c.commit()
  self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_registration_request').fetchone(),(0,))

 def test_missing_null_and_wrong_profile_refuse_without_partial_registration(self):
  self.install();c,h,a,t=self.consumer();prepared=a.prepare_catalog((CatalogDocument(catalog.relational_document()['id'],'r1',json.dumps(catalog.relational_document()).encode()),),bun_executable='/opt/homebrew/bin/bun')
  c.execute("CREATE TEMP TABLE profile_prior10(value text);INSERT INTO profile_prior10 VALUES('kept')")
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
    self.assertEqual(c.execute('TABLE profile_prior10').fetchall(),[('kept',)])
  h.detach();c.commit()
  self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.catalog_registration_request').fetchone(),(0,))

 def test_original10_default_and_allowed_values_correspondence(self):
  self.install();c,h,a,t=self.consumer();original=self.source10()[0];doc=json.loads(original.content)
  field=next(e for e in doc['modules'][0]['elements'] if e['id']=='resourceId')
  field['default']={'value':{'string':'EXACT'},'on':'missing'};field['allowedValues']=[{'string':'EXACT'},{'string':'OTHER'}]
  document=CatalogDocument(original.document_id,original.document_revision,json.dumps(doc).encode())
  prepared=a.prepare_catalog((document,),source_version='0.10.0',bun_executable='/opt/homebrew/bin/bun')
  result=a.accept_in_transaction(t,prepared,request_key='properties10')
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error))
  h.detach();c.commit()
  self.assertEqual(json.loads(self.admin.execute('SELECT document FROM truss.schema_doc').fetchone()[0]),doc)

 def test_native_signed64_exact_lexical_boundaries_and_private_helper(self):
  self.install();self.host.detach();self.admin.commit()
  facets={'integerWidth':{'bits':64,'signed':True}}
  for text,expected in [('0',True),('-0',True),('9223372036854775807',True),('-9223372036854775808',True),('9223372036854775808',False),('-9223372036854775809',False),('9'*10000,False),('01',False),('1.0',False)]:
   with self.subTest(text=text[:30]):
    self.assertEqual(self.admin.execute('SELECT truss.valid_scalar_property(%s::jsonb,%s,%s,%s::jsonb)',(json.dumps({'kind':'integer','text':text}),'integer',False,json.dumps(facets))).fetchone(),(expected,))
  self.assertEqual(self.admin.execute("SELECT has_function_privilege('consumer','truss.valid_scalar_property(jsonb,text,boolean,jsonb)','EXECUTE')").fetchone(),(False,))
