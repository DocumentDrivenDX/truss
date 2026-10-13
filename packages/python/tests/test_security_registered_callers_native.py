"""Registered Alice/Bob/outsider native callers through one guarded source profile."""
from dataclasses import replace
import json,uuid
from unittest.mock import patch
import psycopg
from psycopg import sql
from truss import Ok,Error,adopt_psycopg_host
import test_security_catalog_source_cut_native as source

class RegisteredCallersNativeTests(source.CatalogSourceCutTests):
 for name in tuple(n for n in dir(source.CatalogSourceCutTests) if n.startswith('test_')):locals()[name]=None
 def setup_subject(self):
  suffix=uuid.uuid4().hex[:12];self.bob='registered_bob_'+suffix;self.outsider='registered_outsider_'+suffix
  for name in (self.bob,self.outsider):self.admin.execute(sql.SQL('CREATE ROLE {} LOGIN').format(sql.Identifier(name)))
  self.subject_bindings=(('consumer','s1'),(self.bob,'s2'),(self.outsider,'s3'))
  return super().setup_subject()
 def populated(self):
  return super().populated(extra_rows=(('Staff',{'staffId':'s2'}),('Staff',{'staffId':'s3'}),('Assignment',{'assignmentId':'bob-a1','assignmentStaff':'s2','assignmentProject':'p2','active':True})))
 def publish(self,caller,transaction,mapping,selection,inspector,relations,cut,subjects,delivered):
  return source.subject.publish_registered_ddl_epoch_guarded_native_catalog_resource_read(caller,transaction,self.host,self.tx,mapping,selection,inspector,relations,cut,subjects,delivered.append)
 def test_three_actual_callers_obey_own_project_membership(self):
  """@covers US-056-AC2; B01 population prerequisite, not complete backend admission."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();subjects=self.registered_subjects
  rows=[]
  for role,expected in (('consumer',['r1']),(self.bob,['r2']),(self.outsider,[])):
   parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=role
   with psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000') as native:
    native.execute('BEGIN');caller=adopt_psycopg_host(native,statement_timeout_ms=10000,operation_timeout_ms=30000)
    try:
     adopted=caller.adopt_transaction();self.assertIsInstance(adopted,Ok,str(caller._custody.last_attempt.error))
     transaction=adopted.value;delivered=[]
     self.assertEqual(native.execute('SELECT SESSION_USER::pg_catalog.text').fetchone(),(role,))
     result=self.publish(caller,transaction,mapping,replace(selection,principal=role),inspector,relations,cut,subjects,delivered)
     self.assertIsInstance(result,Ok,str(caller._custody.last_attempt.error));self.assertEqual(delivered,[result.value])
     receipt=json.loads(result.value);actual=[r['key'][0]['string'] for r in receipt['rows']]
     self.assertEqual(actual,expected)
     for row in receipt['rows']:self.assertEqual(row['output'][0]['disposition'],'withheld')
     for table in ('truss.object','truss.catalog_subject_map'):
      self.assertEqual(native.execute('SELECT has_table_privilege(%s,\'SELECT\')',(table,)).fetchone(),(False,))
     rows.append({'role':role,'resources':actual,'salaryWithheld':True})
    finally:caller.detach();native.rollback()
  self.assertEqual([r['resources'] for r in rows],[['r1'],['r2'],[]])
 def test_unregistered_extra_helper_grant_refuses_before_subject(self):
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute('GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO PUBLIC')
  with patch.object(source.subject,'encode_literal_key_tuple') as encoder,patch.object(source.subject,'run_owned_catalog_resource_read') as evaluator:
   result=self.publish(h,t,mapping,selection,inspector,relations,cut,self.registered_subjects,delivered)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Exact installed catalog subject helper ACL required')
 def test_changed_registered_staff_binding_refuses_before_subject(self):
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute("UPDATE truss.catalog_subject_map SET staff_key='s2' WHERE role_oid=(SELECT oid FROM pg_roles WHERE rolname='consumer')")
  with patch.object(source.subject,'encode_literal_key_tuple') as encoder:
   result=self.publish(h,t,mapping,selection,inspector,relations,cut,self.registered_subjects,delivered);encoder.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original registered Subject map changed')

 def test_hostile_text_domain_cannot_run_in_registered_checker(self):
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute("CREATE SCHEMA registered_hostile;CREATE FUNCTION registered_hostile.reject_text(pg_catalog.text) RETURNS pg_catalog.bool LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'registered hostile text executed';END$$;CREATE DOMAIN registered_hostile.text AS pg_catalog.text CHECK(registered_hostile.reject_text(VALUE))")
  self.admin.execute('SET LOCAL search_path=registered_hostile,pg_catalog')
  result=self.publish(h,t,mapping,selection,inspector,relations,cut,self.registered_subjects,delivered)
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertEqual(delivered,[result.value])

 def test_registered_role_privilege_drift_refuses_before_subject(self):
  """@covers US-056-AC9; selected role drift, not complete concurrent authority."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  self.admin.execute(sql.SQL('ALTER ROLE {} BYPASSRLS').format(sql.Identifier(self.bob)))
  with patch.object(source.subject,'encode_literal_key_tuple') as encoder,patch.object(source.subject,'run_owned_catalog_resource_read') as evaluator:
   result=self.publish(h,t,mapping,selection,inspector,relations,cut,self.registered_subjects,delivered)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original ordinary registered Subject principals required')
