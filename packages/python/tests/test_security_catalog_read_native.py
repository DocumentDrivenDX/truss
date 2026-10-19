# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual accepted named model and ordinary-created native Record facts.
@covers US-056-AC2; component prerequisites, not backend case promotion.
"""
import json,sys,os,subprocess,shutil
import psycopg
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from truss import (Ok,Error,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration,
 ModuleAccessGrant,CatalogDocument)
from truss.contracts import TextValue,BooleanValue,MapValue
from truss.groups import AuthoredValue,CreateObject,RootlessOwnership,RequestNone,GroupSuccess
import test_security_accepted_catalog_native as accepted
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import security_catalog_read as read

class AcceptedCatalogReadNativeTests(accepted.AcceptedCatalogMappingTests):
 for name in tuple(n for n in dir(accepted.AcceptedCatalogMappingTests) if n.startswith('test_')):locals()[name]=None
 @classmethod
 def cleanup(cls):
  cls.runtime.__exit__(None,None,None)
  status=subprocess.run([str(cls.runtime.psql_path.parent/'pg_ctl'),'-D',str(cls.info.data_directory),'status'],capture_output=True,text=True,timeout=30)
  parameters=psycopg.conninfo.conninfo_to_dict(cls.info.connection_uri)
  socket=Path(parameters['host'])/('.s.PGSQL.'+parameters.get('port','5432'))
  receipt={'runtimeExitSucceeded':True,'statusExitCode':status.returncode,'socketAbsent':not socket.exists(),'serverVersion':cls.info.server_version}
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/'cleanup.json').write_text(json.dumps(receipt,indent=2)+'\n')
  if status.returncode!=3 or socket.exists():raise RuntimeError('Owned catalog read server cleanup failed')
  shutil.rmtree(cls.root)

 def populated(self,*,extra_rows=()):
  source=json.loads((read.BASE/'mapping-request.json').read_bytes());self.accepted(source=source)
  self.host.detach();self.admin.commit()
  self.admin.execute('CREATE ROLE catalog_fact_reader;CREATE ROLE catalog_fact_writer')
  for role in ('catalog_fact_reader','catalog_fact_writer'):self.addCleanup(self.admin.execute,'DROP OWNED BY '+role+';DROP ROLE '+role)
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
  self.assertIsInstance(assembly.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('domain','m','catalog_fact_reader','catalog_fact_writer'),)),Ok)
  self.host.detach();self.admin.commit();self.admin.execute('GRANT catalog_fact_writer TO consumer WITH SET FALSE')
  c,h,a,t=self.consumer();view=a.catalog_view_in_transaction(t,a.catalog_view_request()).value.view
  types={d.reference.authored_identity:d.reference for d in view.definitions if d.reference.kind=='type'}
  self.admin.execute('REVOKE '+self.installation.registrar_role+' FROM consumer')
  rows=[('Staff',{'staffId':'s1'}),('Project',{'projectId':'p1'}),('Project',{'projectId':'p2'}),
        ('Resource',{'resourceId':'r1','salary':100}),('Resource',{'resourceId':'r2','salary':200}),('Resource',{'resourceId':'orphan','salary':300}),
        ('Ownership',{'ownerId':'o1','ownerResource':'r1','ownerProject':'p1'}),('Ownership',{'ownerId':'o2','ownerResource':'r2','ownerProject':'p2'}),
        ('Assignment',{'assignmentId':'a1','assignmentStaff':'s1','assignmentProject':'p1','active':True}),('Assignment',{'assignmentId':'a2','assignmentStaff':'s1','assignmentProject':'p2','active':False})]
  rows+=list(extra_rows)
  operations=[]
  for index,(record,fields) in enumerate(rows):
   values=tuple(AuthoredValue(name=k,value=BooleanValue(value=v) if type(v) is bool else TextValue(kind='integer' if type(v) is int else 'string',text=str(v))) for k,v in fields.items())
   operations.append(CreateObject(type_definition_pin=types[record].definition_pin,values=values,ownership=RootlessOwnership(),alias='row'+str(index)))
  context=a.group_context_in_transaction(t).value
  documents=tuple(CatalogDocument(m['pin']['documentId'],m['pin']['revision'],m['documentJson'].encode()) for m in source['modules'])
  created=a.apply_in_transaction(t,context.input(tuple(operations),MapValue(entries=())),RequestNone(),documents=documents,bun_executable='/opt/homebrew/bin/bun')
  self.assertIsInstance(created,Ok,str(h._custody.last_attempt.error));self.assertIsInstance(created.value,GroupSuccess,str(created))
  h.detach();c.commit()
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  mapped=self.prepare_accepted();self.assertIsInstance(mapped,Ok,str(self.host._custody.last_attempt.error));return mapped.value
 def test_original_accepted_catalog_populated_records_feed_shared_policy(self):
  mapping=self.populated();original=read.subprocess.run;observed=[];captured=[]
  project=read._catalog_record_cells
  def retain_capture(recipes,rows):
   captured.append({'recipes':recipes,'rows':rows});return project(recipes,rows)
  def during_evaluation(*args,**kwargs):
   with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=100ms') as writer:
    with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute('UPDATE truss.object SET props=props')
   observed.append(True);return original(*args,**kwargs)
  with patch.object(read.subprocess,'run',during_evaluation),patch.object(read,'_catalog_record_cells',retain_capture):result=read.run_owned_catalog_resource_read(self.host,self.tx,mapping,'s1')
  self.assertEqual(observed,[True])
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:
   base=Path(directory)
   for name,raw in (('request',mapping.original_request),('assessment',mapping.accepted_catalog_assessment),('dependencies',mapping.native_dependencies),('owner-response',mapping.original_response)):(base/(name+'.json')).write_bytes(raw)
   (base/'decision.json').write_text(json.dumps(result.value,indent=2)+'\n')
   (base/'capture.json').write_text(json.dumps(captured,indent=2)+'\n')
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error))
  self.assertEqual([r['key'] for r in result.value['rows']],[[{'string':'r1'}]])
  self.assertEqual(result.value['rows'][0]['output'][0]['disposition'],'withheld')
  assessment=json.loads(mapping.accepted_catalog_assessment)
  self.assertEqual({t['element'] for t in assessment['inventory']['types']},{'Staff','Project','Resource','Assignment','Ownership'})
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(10,))
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
 def test_retained_assessment_substitution_refuses_before_evaluator(self):
  mapping=self.populated()
  for field,value in (('accepted_catalog_assessment',bytearray(mapping.accepted_catalog_assessment)),('accepted_catalog_assessment',memoryview(mapping.accepted_catalog_assessment)),('accepted_catalog_assessment',b''),('original_request',bytearray(mapping.original_request))):
   with self.subTest(field=field,carrier=type(value).__name__),patch.object(type(self.host),'_run_operation') as operation:
    with self.assertRaisesRegex(ValueError,'Original accepted-catalog fixture mapping required'):
     read.run_owned_catalog_resource_read(self.host,self.tx,replace(mapping,**{field:value}),'s1')
    operation.assert_not_called()
  assessment=json.loads(mapping.accepted_catalog_assessment);assessment['inventory']['types'][0]['type_id']+=1000
  forged=replace(mapping,accepted_catalog_assessment=json.dumps(assessment).encode())
  with patch.object(read.subprocess,'run') as evaluator:
   result=read.run_owned_catalog_resource_read(self.host,self.tx,forged,'s1');evaluator.assert_not_called()
  self.assertIsInstance(result,Error);attempt=self.host._custody.last_attempt
  self.assertEqual(str(attempt.error),'Original current accepted catalog correspondence required');self.assertEqual(attempt.phase,'contained');self.assertIsNone(attempt.cleanup_error)
  # Replacing the frozen dataclass's field after entry cannot replace the
  # immutable expected bytes already captured by this operation.
  selected=replace(mapping);original_operation=type(self.host)._run_operation
  def change_carrier(host,transaction,callback):
   object.__setattr__(selected,'accepted_catalog_assessment',bytearray(b'changed'))
   return original_operation(host,transaction,callback)
  with patch.object(type(self.host),'_run_operation',change_carrier):
   retry=read.run_owned_catalog_resource_read(self.host,self.tx,selected,'s1')
  self.assertIsInstance(retry,Ok,str(self.host._custody.last_attempt.error))
  self.assertEqual([r['key'] for r in retry.value['rows']],[[{'string':'r1'}]])
