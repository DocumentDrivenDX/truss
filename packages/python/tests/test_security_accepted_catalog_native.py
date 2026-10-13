"""Accepted core0.8 sources through genuine Weft under the native guard.
@covers US-056-AC2
@covers US-056-AC6
@covers US-056-AC9
"""
import json,copy
from truss import Ok,Error,CatalogDocument,adopt_psycopg_host
from truss._security_mapping import SecurityMappingBoundary,prepare_security_mapping_in_transaction
from truss._security_home_installation import bootstrap_security_homes_in_transaction
import test_security_mapping_native as mapping

class AcceptedCatalogMappingTests(mapping.MappingNativeTests):
 for name in tuple(n for n in dir(mapping.MappingNativeTests) if n.startswith('test_')):locals()[name]=None
 def accepted(self,second=False):
  self.install();source=json.loads(mapping.FIXTURE.read_text());self.reference=mapping.encoded(source)
  c,h,a,t=self.consumer();m=source['modules'][0];p=m['pin']
  prepared=a.prepare_catalog((CatalogDocument(p['documentId'],p['revision'],m['documentJson'].encode()),),source_version='0.8.0',bun_executable='/opt/homebrew/bin/bun')
  result=a.accept_in_transaction(t,prepared,request_key='accepted-mapping08');self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error))
  if second:
   h.detach();c.commit()
   self.admin.execute("CREATE ROLE assessment_writer;INSERT INTO truss.module_access VALUES('domain','m','consumer','assessment_writer')")
   self.addCleanup(self.admin.execute,'DROP OWNED BY assessment_writer;DROP ROLE assessment_writer')
   c,h,a,t=self.consumer()
   another=a.prepare_catalog((CatalogDocument(p['documentId'],'schema-2',m['documentJson'].encode()),),source_version='0.8.0',bun_executable='/opt/homebrew/bin/bun')
   result=a.accept_in_transaction(t,another,request_key='accepted-mapping08-second');self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error))
  h.detach();c.commit()
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  self.calls=[]
  def original(text):self.calls.append(text);return self.original(text)
  self.boundary=SecurityMappingBoundary(original,self.reference);self.identity=self.installation.installation_id.encode()
  self.assertIsInstance(bootstrap_security_homes_in_transaction(self.host,self.tx,installation_identity=self.identity,authored_profile=self.boundary.original_profile,max_retained=8),Ok)
  self.admin.execute("CREATE TEMP TABLE accepted_prior(value text);INSERT INTO accepted_prior VALUES('kept')")
 def prepare_accepted(self):
  return prepare_security_mapping_in_transaction(self.host,self.tx,boundary=self.boundary,installation_identity=self.identity,expected_generation=1,original_request=self.reference,require_accepted_catalog=True)
 def test_original_accepted_model_and_native_inventory(self):
  self.accepted();result=self.prepare_accepted();self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  self.assertFalse(result.value.security_ready);assessment=json.loads(result.value.accepted_catalog_assessment)
  self.assertEqual(assessment['revision'],'1');self.assertEqual(assessment['modelPins'],[m['pin'] for m in json.loads(self.reference)['modules']])
  self.assertEqual({t['element'] for t in assessment['inventory']['types']},{'Staff','Project','Resource','Ownership','Assignment'})
  self.assertEqual(len(json.loads(result.value.original_response)['handoff']['scans']),2)
  dependencies=json.loads(result.value.native_dependencies)
  self.assertEqual([s['scan'] for s in dependencies['scans']],['s0','s1'])
  self.assertEqual(len(dependencies['uses']),6)
  self.assertEqual({a['reference']['elementId'] for s in dependencies['scans'] for action in s['actions'] for a in action['associations']},{'Ownership','Assignment'})
  self.assertFalse(dependencies['securityReady'])
  from truss._security_catalog_mapping import map_catalog_dependencies
  for mutation in ('missing-property','duplicate-type','wrong-key-fields','missing-scan'):
   native=copy.deepcopy(assessment);response=json.loads(result.value.original_response)
   if mutation=='missing-property':native['inventory']['properties']=[p for p in native['inventory']['properties'] if p['element']!='salary']
   elif mutation=='duplicate-type':native['inventory']['types'].append(copy.deepcopy(next(t for t in native['inventory']['types'] if t['element']=='Resource')))
   elif mutation=='wrong-key-fields':native['inventory']['keys'][0]['prop_ids']=[]
   else:response['handoff']['scans']=response['handoff']['scans'][1:]
   with self.subTest(mutation=mutation):
    with self.assertRaises(ValueError):map_catalog_dependencies(json.dumps(native).encode(),json.dumps(response).encode())
  self.assertEqual(self.admin.execute('TABLE accepted_prior').fetchall(),[('kept',)])
 def test_unaccepted_source_refused_before_compiler(self):
  self.accepted();source=json.loads(self.reference);source['modules'][0]['pin']['revision']='substituted'
  self.reference=mapping.encoded(source)
  def counted(text):self.calls.append(text);return self.original(text)
  self.boundary=SecurityMappingBoundary(counted,self.reference)
  result=self.prepare_accepted();self.assertIsInstance(result,Error);self.assertEqual(self.calls,[])
  self.assertEqual(self.admin.execute('TABLE accepted_prior').fetchall(),[('kept',)])
 def test_native_definition_substitution_refused_before_compiler(self):
  self.accepted();self.admin.execute("ALTER TABLE truss.prop_def DISABLE TRIGGER USER;UPDATE truss.prop_def SET element='substituted' WHERE element='salary';ALTER TABLE truss.prop_def ENABLE TRIGGER USER")
  result=self.prepare_accepted();self.assertIsInstance(result,Error);self.assertEqual(self.calls,[])
  self.assertEqual(self.admin.execute('TABLE accepted_prior').fetchall(),[('kept',)])
 def test_late_definition_change_contained_and_prior_work_preserved(self):
  self.accepted()
  def changed(text):
   self.calls.append(text)
   self.admin.execute("ALTER TABLE truss.prop_def DISABLE TRIGGER USER;UPDATE truss.prop_def SET element='late-substitution' WHERE element='salary';ALTER TABLE truss.prop_def ENABLE TRIGGER USER")
   return self.original(text)
  self.boundary=SecurityMappingBoundary(changed,self.reference)
  result=self.prepare_accepted();self.assertIsInstance(result,Error);self.assertEqual(len(self.calls),1)
  self.assertEqual(self.admin.execute("SELECT count(*) FROM truss.prop_def WHERE element='salary'").fetchone(),(1,))
  self.assertEqual(self.admin.execute('TABLE accepted_prior').fetchall(),[('kept',)])
 def test_missing_report_refused_before_compiler(self):
  self.accepted();self.admin.execute('ALTER TABLE truss.catalog_acceptance_report DISABLE TRIGGER USER;DELETE FROM truss.catalog_acceptance_report WHERE rev=1;ALTER TABLE truss.catalog_acceptance_report ENABLE TRIGGER USER')
  result=self.prepare_accepted();self.assertIsInstance(result,Error);self.assertEqual(self.calls,[])
  self.assertEqual(self.admin.execute('TABLE accepted_prior').fetchall(),[('kept',)])
 def test_head_mismatch_refused_before_compiler(self):
  self.accepted();self.admin.execute("ALTER TABLE truss.schema_head DISABLE TRIGGER USER;UPDATE truss.schema_head SET rev=0 WHERE id=1;ALTER TABLE truss.schema_head ENABLE TRIGGER USER")
  result=self.prepare_accepted();self.assertIsInstance(result,Error);self.assertEqual(self.calls,[])
  self.assertEqual(self.admin.execute('TABLE accepted_prior').fetchall(),[('kept',)])
 def test_stale_positive_head_refused_before_compiler(self):
  self.accepted(second=True);self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(),(2,))
  self.admin.execute("ALTER TABLE truss.schema_head DISABLE TRIGGER USER;UPDATE truss.schema_head SET rev=1 WHERE id=1;ALTER TABLE truss.schema_head ENABLE TRIGGER USER")
  result=self.prepare_accepted();self.assertIsInstance(result,Error);self.assertEqual(self.calls,[])
  self.assertIn('Exact current accepted revision history required',str(self.host._custody.last_attempt.error))
  self.assertEqual(self.admin.execute('TABLE accepted_prior').fetchall(),[('kept',)])
 def test_missing_historical_report_refused_before_compiler(self):
  self.accepted(second=True);self.admin.execute('ALTER TABLE truss.catalog_acceptance_report DISABLE TRIGGER USER;DELETE FROM truss.catalog_acceptance_report WHERE rev=1;ALTER TABLE truss.catalog_acceptance_report ENABLE TRIGGER USER')
  result=self.prepare_accepted();self.assertIsInstance(result,Error);self.assertEqual(self.calls,[])
  self.assertIn('Complete accepted revision receipt history required',str(self.host._custody.last_attempt.error))
  self.assertEqual(self.admin.execute('TABLE accepted_prior').fetchall(),[('kept',)])
