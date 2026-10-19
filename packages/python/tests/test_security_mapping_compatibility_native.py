# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original producer compatibility diagnostics, not backend admission.
@covers US-056-AC2
@covers US-056-AC9
@covers US-056-AC10
"""
import json,os
from hashlib import sha256
from pathlib import Path
import psycopg
from truss import Ok,Error,CatalogDocument
from truss._security_mapping import SecurityMappingBoundary,prepare_security_mapping_in_transaction
import test_security_mapping_native as mapping
from test_catalog_relational_support import relational_document

class MappingCompatibilityNativeTests(mapping.MappingNativeTests):
 for name in tuple(n for n in dir(mapping.MappingNativeTests) if n.startswith('test_')):locals()[name]=None
 def retain(self,name,value):
  output=os.environ.get('TRUSS_SECURITY_COMPATIBILITY_EVIDENCE_DIR')
  if output:
   root=Path(output);root.mkdir(parents=True,exist_ok=True)
   (root/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 def accepted07(self):
  self.install();c,h,a,t=self.consumer();source=relational_document();source['id']='domain'
  original=json.dumps(source,ensure_ascii=False,indent=2).encode()
  prepared=a.prepare_catalog((CatalogDocument('domain','schema-1',original),),bun_executable='/opt/homebrew/bin/bun')
  accepted=a.accept_in_transaction(t,prepared,request_key='original-native07')
  self.assertIsInstance(accepted,Ok,str(h._custody.last_attempt.error));h.detach();c.commit()
  c,h,a,t=self.consumer();view=a.catalog_view_in_transaction(t,a.catalog_view_request())
  self.assertIsInstance(view,Ok,str(h._custody.last_attempt.error));self.assertEqual(view.value.outcome,'available')
  self.assertGreater(len(view.value.view.definitions),0)
  return original,c,h,a,t,view.value.view
 def test_original08_compiler_source_refused_by_actual_native_ingress(self):
  self.install();source=json.loads(mapping.FIXTURE.read_text());reference=mapping.encoded(source)
  boundary=SecurityMappingBoundary(self.original,reference);result=boundary.prepare(reference)
  self.assertFalse(result.security_ready);self.assertEqual(len(json.loads(result.original_response)['handoff']['scans']),2)
  c,h,a,t=self.consumer();c.execute("CREATE TEMP TABLE compatibility_prior(value text);INSERT INTO compatibility_prior VALUES('kept')")
  module=source['modules'][0];pin=module['pin']
  prepared=a.prepare_catalog((CatalogDocument(pin['documentId'],pin['revision'],module['documentJson'].encode()),),bun_executable='/opt/homebrew/bin/bun')
  accepted=a.accept_in_transaction(t,prepared,request_key='original08')
  self.assertIsInstance(accepted,Error);failure=str(h._custody.last_attempt.error)
  self.assertIn('Unselected catalog support source',failure)
  self.assertEqual(c.execute('TABLE compatibility_prior').fetchall(),[('kept',)])
  h.detach();c.commit() # Expose any partial effects; another session alone cannot see uncommitted effects.
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.schema_doc').fetchone(),(0,))
  self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(0,))
  self.retain('original08-native-refusal',{'originalRequest':source,'originalCompilerResponse':json.loads(result.original_response),'nativeVersion':self.admin.execute('SHOW server_version_num').fetchone()[0],'failure':failure,'priorWork':'kept','acceptedDocuments':0,'head':0,'outerSettlement':'committed after contained refusal','qualification':'Original core0.8 compiler metadata succeeds; original native ingress refuses. No migration or protected execution.'})
 def test_actual_accepted07_original_bytes_refused_by_compiler_transport(self):
  original,c,h,a,t,view=self.accepted07();request=json.loads(mapping.FIXTURE.read_text())
  pin={'documentId':'domain','revision':'schema-1','umfVersion':'0.7.0','sha256':sha256(original).hexdigest()}
  request['modules']=[{'documentJson':original.decode(),'pin':pin,'selectedModuleIds':['m']}]
  response=json.loads(self.original(mapping.encoded(request).decode()))
  self.assertEqual(response['status'],'refused');self.assertFalse(response['securityReady']);self.assertNotIn('handoff',response)
  self.assertEqual(response['diagnostics'][0]['code'],'WFT-SECURITY-MAPPING-TRANSPORT')
  archived=self.admin.execute('SELECT document,content_sha256,umf_version FROM truss.schema_doc WHERE doc_id=%s',('domain',)).fetchone()
  self.assertEqual(archived,(original.decode(),pin['sha256'],'0.7.0'))
  self.retain('accepted07-compiler-refusal',{'originalRequest':request,'originalCompilerResponse':response,'nativeArchiveSha256':archived[1],'nativeView':json.loads(view.original_bytes),'qualification':'Schema-level original0.7 transport refusal; policy/model equivalence is not evaluated or claimed.'})
 def test_original_catalog_producer_and_guard_have_separate_actor_boundaries(self):
  original,c,h,a,t,view=self.accepted07()
  ordinary=c.execute('SELECT session_user::text,current_user::text').fetchone();self.assertEqual(ordinary,('consumer','consumer'))
  # The public native catalog basis deliberately refuses the excluded installer.
  with self.assertRaises(psycopg.errors.InsufficientPrivilege) as refusal:
   self.admin.execute('SELECT truss.catalog_view_basis(NULL,65536,16777216)')
  self.assertEqual(refusal.exception.sqlstate,'42501')
  c.execute("CREATE TEMP TABLE compatibility_actor_prior(value text);INSERT INTO compatibility_actor_prior VALUES('kept')")
  request=json.loads(mapping.FIXTURE.read_text());calls=[]
  def compiler(text):calls.append(text);return self.original(text)
  boundary=SecurityMappingBoundary(compiler,mapping.encoded(request))
  guarded=prepare_security_mapping_in_transaction(h,t,boundary=boundary,installation_identity=self.installation.installation_id.encode(),expected_generation=1,original_request=mapping.encoded(request))
  self.assertIsInstance(guarded,Error);self.assertEqual(guarded.error.sql_state,'42501');self.assertEqual(calls,[])
  self.assertEqual(c.execute('TABLE compatibility_actor_prior').fetchall(),[('kept',)])
  self.retain('separate-native-actor-boundaries',{'ordinaryCaller':ordinary,'ordinaryCatalogDefinitions':len(view.definitions),'installerCatalogBasisRefusal':refusal.exception.sqlstate,'ordinaryGuardRefusal':guarded.error.code,'ordinaryGuardSqlState':guarded.error.sql_state,'ordinaryPriorWork':'kept','compilerCalls':0,'qualification':'Separate selected producer/guard gates; does not prove exhaustive roles or authenticated cross-context composition.'})
