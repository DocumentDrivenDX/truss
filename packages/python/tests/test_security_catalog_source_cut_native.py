# SPDX-License-Identifier: MIT OR Apache-2.0
"""Selected native source epoch/DDL cut through actual Subject publication."""
import json,os
from pathlib import Path
from unittest.mock import patch
import psycopg
from psycopg import sql
from truss import Ok,Error,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss._psycopg_epoch_cut import _EpochComparison,_DDLBarrierComparison
import test_security_guarded_subject_native as guarded
ROOT=guarded.ROOT;subject=guarded.subject

class CatalogSourceCutTests(guarded.GuardedSubjectTests):
 for name in tuple(n for n in dir(guarded.GuardedSubjectTests) if n.startswith('test_')):locals()[name]=None
 def consumer(self):
  # This fixture seeds ten public Records; use explicitly bounded setup custody.
  c,prior,a,t=super().consumer();prior.detach()
  h=adopt_psycopg_host(c,statement_timeout_ms=10000,operation_timeout_ms=30000)
  self.addCleanup(h.detach);self.consumer_connections.append((c,h))
  a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value
  adopted=h.adopt_transaction();self.assertIsInstance(adopted,Ok)
  return c,h,a,adopted.value

 def source_setup(self,foreign_installation=False,profile_override=None,evidence_override=None):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  self.host.detach();self.admin.commit()
  if foreign_installation:
   for name in ('source-epoch-immutability','source-epoch-lock','source-epoch-issue','source-epoch-fresh-lock','source-epoch-read-fence','source-epoch-fenced-fresh-lock'):
    self.admin.execute((ROOT/'packages/postgresql/native'/ (name+'.sql')).read_text())
  installation=self.admin.execute('SELECT gen_random_uuid()::text').fetchone()[0] if foreign_installation else self.installation.installation_id
  incarnation='catalog-fixture-target'
  if foreign_installation:
   # Excluded administrative foreign-marker negative control only.
   self.admin.execute("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0',%s,'fixture',sha256(decode('01','hex')),'fixture',sha256(decode('02','hex')),'fixture','truss',now(),now()::text)",(installation,))
  else:
   from truss._security_catalog_source_installation import bootstrap_catalog_source_marker_in_transaction
   self.admin.execute('BEGIN');issuer=adopt_psycopg_host(self.admin)
   try:
    issued=bootstrap_catalog_source_marker_in_transaction(issuer,issuer.adopt_transaction().value,mapping)
    self.assertIsInstance(issued,Ok,str(issuer._custody.last_attempt.error));self.assertFalse(issued.value.security_ready)
    self.assertEqual(issued.value.installation_id,installation)
    incarnation=issued.value.target_incarnation.decode('utf8')
   finally:issuer.detach()
   self.admin.commit()
  if foreign_installation:
   # Excluded administrative foreign-marker negative control only.
   source=(ROOT/'packages/postgresql/native/source-epoch-routine-ddl-barrier.sql').read_text()
   self.admin.execute(source);self.admin.execute((ROOT/'packages/postgresql/native/source-epoch-schema-ddl-barrier.sql').read_text());self.admin.execute((ROOT/'packages/postgresql/native/source-epoch-database-ddl-barrier.sql').read_text());self.admin.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text());self.admin.execute((ROOT/'packages/postgresql/native/source-epoch-alter-routine-ddl-barrier.sql').read_text())
   oid,owner=self.admin.execute("SELECT oid,proowner FROM pg_proc WHERE oid='truss.runtime_fence_routine_ddl_writer()'::regprocedure").fetchone()
   barrier=_DDLBarrierComparison(owner,oid,source.split('AS $$',1)[1].split('$$;',1)[0],include_alter_routine=True,include_schema_ddl=True,include_database_ddl=True)
  else:
   from truss._security_source_epoch_installation import bootstrap_source_epoch_infrastructure_in_transaction
   self.admin.execute('BEGIN');installer=adopt_psycopg_host(self.admin)
   try:
    installed=bootstrap_source_epoch_infrastructure_in_transaction(installer,installer.adopt_transaction().value,installation_identity=installation.encode())
    self.assertIsInstance(installed,Ok,str(installer._custody.last_attempt.error));self.assertFalse(installed.value.security_ready)
    barrier=installed.value.barrier
   finally:installer.detach()
   self.admin.commit()
  profile=subject.derive_catalog_source_epoch_profile(mapping,relations,barrier) if profile_override is None else profile_override
  evidence=mapping.accepted_catalog_assessment if evidence_override is None else evidence_override
  if foreign_installation or profile_override is not None or evidence_override is not None:
   # Explicit excluded administrative negative controls bypass factory source binding.
   epoch=self.admin.execute('SELECT truss.runtime_issue_source_epoch(%s,NULL,%s,%s,%s)',(installation,incarnation,profile,evidence)).fetchone()[0]
   cut=(_EpochComparison(installation,epoch,incarnation,profile,evidence),barrier)
  else:
   from truss._security_catalog_source_epoch import issue_initial_catalog_source_epoch_in_transaction
   self.admin.execute('BEGIN');factory=adopt_psycopg_host(self.admin)
   try:
    minted=issue_initial_catalog_source_epoch_in_transaction(factory,factory.adopt_transaction().value,mapping=mapping,marker=issued.value,infrastructure=installed.value,fact_relations=relations,subject_source=(ROOT/'scripts/security-catalog-subject.sql').read_bytes())
    self.assertIsInstance(minted,Ok,str(factory._custody.last_attempt.error));self.assertFalse(minted.value.security_ready)
    self.assertEqual(minted.value.comparison.profile,profile)
    cut=(minted.value.comparison,minted.value.barrier)
   finally:factory.detach()
   self.admin.commit()
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  return mapping,c,h,t,selection,inspector,relations,cut
 def test_source_cut_precedes_key_and_survives_receiver(self):
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();encoded=[];delivered=[]
  original=subject.encode_literal_key_tuple
  def shares():
   self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)").fetchone(),(2,))
  def encode(*args,**kwargs):shares();encoded.append(True);return original(*args,**kwargs)
  def publish(packet):
   shares()
   with psycopg.connect(self.info.connection_uri,autocommit=True) as writer:
    for command in ('ALTER FUNCTION truss.catalog_subject_current(text) STABLE','ALTER ROUTINE truss.catalog_subject_current(text) STABLE','CREATE SCHEMA source_cut_foreign','ALTER SCHEMA truss RENAME TO source_cut_foreign','DROP SCHEMA truss CASCADE',"COMMENT ON TABLE truss.object IS 'changed'",'CREATE TYPE truss.source_cut_type AS ENUM (\'changed\')','GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO PUBLIC','REVOKE EXECUTE ON FUNCTION truss.catalog_subject_current(text) FROM PUBLIC'):
     with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute(command)
   delivered.append(packet)
  for table in ('truss.source_epoch_current','truss.source_epoch_registry'):
   self.assertEqual(c.execute('SELECT has_table_privilege(%s,%s)',(table,'SELECT')).fetchone(),(False,))
  with patch.object(subject,'encode_literal_key_tuple',encode):
   result=subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,publish)
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertEqual(encoded,[True,True]);self.assertEqual(delivered,[result.value])
  decision=json.loads(result.value);self.assertEqual([r['key'] for r in decision['rows']],[[{'string':'r1'}]])
  self.assertEqual(decision['rows'][0]['output'][0]['disposition'],'withheld')
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/'decision.json').write_bytes(result.value)
 def test_disabled_source_barrier_refuses_before_subject_and_delivery(self):
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup()
  self.admin.execute('ALTER EVENT TRIGGER truss_routine_ddl_writer_barrier DISABLE');delivered=[]
  with patch.object(subject,'encode_literal_key_tuple') as encoder,patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(h._custody.last_attempt.error),'Original executor source epoch and DDL barrier refused')
  self.assertEqual(str(self.host._custody.last_attempt.error),'Exact original installed DDL barriers required')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)
 def test_stale_original_epoch_refuses_before_subject_and_delivery(self):
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup()
  self.host.detach();self.admin.commit()
  self.admin.execute('SELECT truss.runtime_issue_source_epoch(%s,%s,%s,%s,%s)',(cut[0].installation,cut[0].epoch,cut[0].incarnation,cut[0].profile,cut[0].evidence))
  self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value;delivered=[]
  with patch.object(subject,'encode_literal_key_tuple') as encoder,patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(h._custody.last_attempt.error),'Original executor source epoch and DDL barrier refused')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)

 def test_foreign_runtime_installation_refuses_before_subject_and_delivery(self):
  # Valid native fixture epoch for another marker; actual runtime is unchanged.
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup(foreign_installation=True);delivered=[]
  self.assertNotEqual(cut[0].installation,self.installation.installation_id)
  with patch.object(subject,'encode_literal_key_tuple') as encoder,patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original source epoch installation correspondence required')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)

 def assert_unrelated_epoch_binding(self,**kwargs):
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup(**kwargs)
  # Native issuer accepted these exact bytes; semantic selection must reject them.
  stored=self.admin.execute('SELECT profile_bytes,evidence_bytes FROM truss.source_epoch_registry WHERE source_epoch=%s',(cut[0].epoch,)).fetchone()
  self.assertEqual(stored,(cut[0].profile,cut[0].evidence))
  with patch.object(subject,'_prepare_subject_operation') as prepare,patch.object(type(h),'_run_published_operation') as operation:
   with self.assertRaisesRegex(ValueError,'Original catalog source profile and evidence binding required'):
    subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,lambda packet:None)
   prepare.assert_not_called();operation.assert_not_called()
 def test_native_epoch_for_unrelated_semantic_profile_refuses_before_inspection(self):
  self.assert_unrelated_epoch_binding(profile_override=b'unrelated-native-source-profile')
 def test_native_epoch_for_unrelated_catalog_evidence_refuses_before_inspection(self):
  self.assert_unrelated_epoch_binding(evidence_override=b'unrelated-native-catalog-evidence')

 def test_default_publication_without_source_binding_regression(self):
  guarded.GuardedSubjectTests.test_guarded_publication_after_native_completion_under_caller_lease(self)

 def test_disabled_schema_barrier_refuses_before_subject_and_delivery(self):
  """@covers US-056-AC9; selected schema writer exclusion prerequisite."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup()
  self.admin.execute('ALTER EVENT TRIGGER truss_schema_ddl_writer_barrier DISABLE');delivered=[]
  with patch.object(subject,'encode_literal_key_tuple') as encoder,patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Exact original installed DDL barriers required')
  self.assertEqual(h._custody.last_attempt.phase,'contained');self.assertIsNone(h._custody.last_attempt.cleanup_error)

 def test_same_executor_schema_ddl_refuses_before_effect_in_receiver(self):
  """@covers US-056-AC9; same-backend schema DDL exclusion prerequisite."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[];states=[]
  def publish(packet):
   for command in ('CREATE SCHEMA source_cut_local','ALTER SCHEMA truss RENAME TO source_cut_local','DROP SCHEMA truss CASCADE',"COMMENT ON TABLE truss.object IS 'changed'",'CREATE TYPE truss.source_cut_type AS ENUM (\'changed\')','GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO PUBLIC','REVOKE EXECUTE ON FUNCTION truss.catalog_subject_current(text) FROM PUBLIC'):
    self.admin.execute('SAVEPOINT schema_writer')
    try:
     with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as caught:self.admin.execute(command)
     self.assertEqual(caught.exception.diag.message_primary,'selected epoch cut excludes routine DDL')
     states.append(caught.exception.sqlstate)
    finally:
     self.admin.execute('ROLLBACK TO schema_writer');self.admin.execute('RELEASE schema_writer')
   self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_namespace WHERE nspname='source_cut_local'").fetchone(),(0,))
   self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(10,))
   delivered.append(packet)
  result=subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,publish)
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertEqual(states,['55000']*7);self.assertEqual(delivered,[result.value])

 def test_disabled_unfiltered_barrier_refuses_before_subject_and_delivery(self):
  """@covers US-056-AC9; database DDL participation prerequisite."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup()
  self.admin.execute('ALTER EVENT TRIGGER truss_database_ddl_writer_barrier DISABLE');delivered=[]
  with patch.object(subject,'encode_literal_key_tuple') as encoder,patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Exact original installed DDL barriers required')

 def test_disabled_session_event_triggers_refuses_before_subject_and_delivery(self):
  """@covers US-056-AC9; ALWAYS installation does not override event_triggers=off."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup()
  self.admin.execute('SET LOCAL event_triggers=off');delivered=[]
  with patch.object(subject,'encode_literal_key_tuple') as encoder,patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original native event trigger execution required')

 def test_session_event_trigger_drift_refuses_final_delivery(self):
  """@covers US-056-AC9; late execution-setting drift prevents publication."""
  mapping,c,h,t,selection,inspector,relations,cut=self.source_setup();delivered=[]
  original=subject.run_owned_catalog_resource_read
  def evaluate(*args,**kwargs):
   result=original(*args,**kwargs)
   # ALWAYS does not override this session switch; verify a real ACL effect.
   self.assertEqual(self.admin.execute("SELECT evtenabled,evttags FROM pg_event_trigger WHERE evtname='truss_database_ddl_writer_barrier'").fetchone(),('A',None))
   public_execute="SELECT EXISTS(SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE p.oid='truss.catalog_subject_current(text)'::regprocedure AND a.grantee=0 AND a.privilege_type='EXECUTE')"
   self.assertEqual(self.admin.execute(public_execute).fetchone(),(False,))
   self.admin.execute('SET LOCAL event_triggers=off')
   self.admin.execute('GRANT EXECUTE ON FUNCTION truss.catalog_subject_current(text) TO PUBLIC')
   self.assertEqual(self.admin.execute(public_execute).fetchone(),(True,))
   self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_locks WHERE pid=pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.source_epoch_current'::regclass,'truss.source_epoch_registry'::regclass)").fetchone(),(2,))
   directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
   if directory:(Path(directory)/'event-trigger-disabled-counterexample.json').write_text(json.dumps({'always':'A','tags':None,'setting':'off','sourceShareLocks':2,'publicExecuteBefore':False,'publicExecuteAfter':True,'scope':'excluded administrative same-session bypass; final publication must refuse'},indent=2)+'\n')
   return result
  with patch.object(subject,'run_owned_catalog_resource_read',evaluate):
   result=subject.publish_ddl_epoch_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations,cut,delivered.append)
  self.assertIsInstance(result,Error);self.assertEqual(delivered,[])
  self.assertEqual(str(self.host._custody.last_attempt.error),'Original native event trigger execution required')
