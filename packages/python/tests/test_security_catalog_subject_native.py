# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native ordinary subject bound to the actual accepted-catalog policy read."""
import json,sys,os,subprocess
from pathlib import Path
from unittest.mock import patch
import psycopg
from psycopg import sql
from truss import Ok,Error
from truss._psycopg_subject_observation import _SubjectSelection
import test_security_catalog_read_native as catalog
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import security_catalog_subject_read as subject

class NativeCatalogSubjectTests(catalog.AcceptedCatalogReadNativeTests):
 for name in tuple(n for n in dir(catalog.AcceptedCatalogReadNativeTests) if n.startswith('test_')):locals()[name]=None
 def setup_subject(self):
  mapping=self.populated();self.host.detach();self.admin.commit()
  self.admin.execute('BEGIN');self.host=catalog.adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  from truss._security_catalog_subject_installation import bootstrap_catalog_subjects_in_transaction
  registered=bootstrap_catalog_subjects_in_transaction(self.host,self.tx,mapping=mapping,bindings=getattr(self,'subject_bindings',(('consumer','s1'),)))
  self.assertIsInstance(registered,Ok,str(self.host._custody.last_attempt.error));self.assertFalse(registered.value.security_ready)
  self.registered_subjects=registered.value
  self.host.detach();self.admin.commit()
  self.admin.execute('GRANT USAGE ON SCHEMA truss TO consumer;REVOKE catalog_fact_writer FROM consumer')
  self.admin.execute('BEGIN');self.host=catalog.adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  c,h,a,t=self.consumer()
  selection=_SubjectSelection(mapping.original_request,(subject.BASE/'document.json').read_bytes(),'m','Staff','pk','consumer','truss','catalog_subject_current',('staff_id',))
  def inspector(request,probe):
   env=dict(os.environ);env['PYTHONPATH']='/private/tmp/subject-consumer-python'
   result=subprocess.run([sys.executable,'-c',"import weft,sys,json; x=json.load(sys.stdin); print(weft.inspect_security_mapping_subject_key_json(x[0],x[1]))"],env=env,input=json.dumps([request,probe]),capture_output=True,text=True,timeout=10)
   self.assertEqual(result.returncode,0,result.stderr);return result.stdout.strip()
  return mapping,c,h,t,selection,inspector
 def test_native_subject_with_no_raw_graph_or_issuer_table_access(self):
  """@covers US-056-AC2; @covers US-056-AC10; component prerequisites only."""
  mapping,c,h,t,selection,inspector=self.setup_subject()
  for table in ('truss.object','truss.catalog_subject_map'):
   for privilege in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE'):
    self.assertEqual(c.execute('SELECT pg_catalog.has_table_privilege(%s,%s)',(table,privilege)).fetchone(),(False,))
  self.assertEqual(c.execute("SELECT pg_catalog.pg_has_role('catalog_fact_writer','MEMBER')").fetchone(),(False,))
  for table in ('object','catalog_subject_map'):
   c.execute('SAVEPOINT raw_probe')
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(sql.SQL('TABLE {}').format(sql.Identifier('truss',table)))
   c.execute('ROLLBACK TO raw_probe');c.execute('RELEASE raw_probe')
  result=subject.run_owned_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector)
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error))
  self.assertEqual([r['key'] for r in result.value['rows']],[[{'string':'r1'}]])
  self.assertEqual(result.value['rows'][0]['output'][0]['disposition'],'withheld')
  # The caller's helper cut survives the private executor operation.
  with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=100ms') as writer:
   for statement in ('UPDATE truss.object SET props=props','UPDATE truss.catalog_subject_map SET staff_key=staff_key'):
    with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute(statement)
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/'decision.json').write_text(json.dumps(result.value,indent=2)+'\n')
 def test_missing_role_subject_mapping_refuses_before_executor(self):
  mapping,c,h,t,selection,inspector=self.setup_subject();self.admin.execute('DELETE FROM truss.catalog_subject_map');self.host.detach();self.admin.commit()
  self.admin.execute('BEGIN');self.host=catalog.adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  with patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.run_owned_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector);evaluator.assert_not_called()
  self.assertIsInstance(result,Error);attempt=h._custody.last_attempt
  self.assertEqual(str(attempt.error),'Exact original native TEXT subject tuple required');self.assertEqual(attempt.phase,'contained');self.assertIsNone(attempt.cleanup_error)

 def test_other_native_database_refuses_before_policy_evaluation(self):
  mapping,c,h,t,selection,inspector=self.setup_subject();self.host.detach();self.admin.commit()
  self.admin.execute("CREATE DATABASE catalog_subject_other TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'")
  self.addCleanup(self.admin.execute,'DROP DATABASE catalog_subject_other')
  parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['dbname']='catalog_subject_other'
  other=psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000');self.addCleanup(other.close)
  # Deliberately copy the installation UUID: native database identity must also match.
  other.execute('CREATE SCHEMA truss;CREATE TABLE truss.catalog_runtime_installation(singleton boolean,installation_id uuid)')
  other.execute('INSERT INTO truss.catalog_runtime_installation VALUES(true,%s::uuid)',(json.loads(mapping.accepted_catalog_assessment)['installationId'],))
  other.execute('BEGIN');executor=catalog.adopt_psycopg_host(other);self.addCleanup(executor.detach)
  adopted=executor.adopt_transaction();self.assertIsInstance(adopted,Ok,str(executor._custody.last_attempt.error));transaction=adopted.value
  with patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.run_owned_native_catalog_resource_read(h,t,executor,transaction,mapping,selection,inspector);evaluator.assert_not_called()
  self.assertIsInstance(result,Error);attempt=h._custody.last_attempt
  self.assertEqual(str(attempt.error),'Original caller/executor installation correspondence required');self.assertEqual(attempt.phase,'contained');self.assertIsNone(attempt.cleanup_error)
 def test_helper_definition_drift_refuses_before_subject_and_executor(self):
  mapping,c,h,t,selection,inspector=self.setup_subject()
  self.admin.execute('ALTER FUNCTION truss.catalog_subject_current(text) SET search_path TO pg_temp,pg_catalog');self.host.detach();self.admin.commit()
  self.admin.execute('BEGIN');self.host=catalog.adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  with patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.run_owned_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector);evaluator.assert_not_called()
  self.assertIsInstance(result,Error);attempt=h._custody.last_attempt
  self.assertEqual(str(attempt.error),'Exact installed catalog subject helper snapshot required');self.assertEqual(attempt.phase,'contained');self.assertIsNone(attempt.cleanup_error)
