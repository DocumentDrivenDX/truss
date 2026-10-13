"""Selected native source epoch/DDL cut through actual Subject publication."""
import json,os
from pathlib import Path
from unittest.mock import patch
import psycopg
from psycopg import sql
from truss import Ok,Error,adopt_psycopg_host
from truss._psycopg_epoch_cut import _EpochComparison,_DDLBarrierComparison
import test_security_guarded_subject_native as guarded
ROOT=guarded.ROOT;subject=guarded.subject

class CatalogSourceCutTests(guarded.GuardedSubjectTests):
 for name in tuple(n for n in dir(guarded.GuardedSubjectTests) if n.startswith('test_')):locals()[name]=None
 def source_setup(self,foreign_installation=False):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  self.host.detach();self.admin.commit()
  for name in ('source-epoch-immutability','source-epoch-lock','source-epoch-issue','source-epoch-fresh-lock','source-epoch-read-fence','source-epoch-fenced-fresh-lock'):
   self.admin.execute((ROOT/'packages/postgresql/native'/ (name+'.sql')).read_text())
  installation=self.admin.execute('SELECT gen_random_uuid()::text').fetchone()[0] if foreign_installation else self.installation.installation_id
  # Administrative marker seed is explicit; not the production bootstrap issuer.
  self.admin.execute("INSERT INTO truss.installation_marker VALUES(1,'truss-bootstrap-marker/0.1.0',%s,'fixture',sha256(decode('01','hex')),'fixture',sha256(decode('02','hex')),'fixture','truss',now(),now()::text)",(installation,))
  profile=b'accepted-catalog-selected-source-cut/0.1';evidence=mapping.accepted_catalog_assessment
  epoch=self.admin.execute('SELECT truss.runtime_issue_source_epoch(%s,NULL,%s,%s,%s)',(installation,'catalog-fixture-target',profile,evidence)).fetchone()[0]
  source=(ROOT/'packages/postgresql/native/source-epoch-routine-ddl-barrier.sql').read_text()
  self.admin.execute(source);self.admin.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text());self.admin.execute((ROOT/'packages/postgresql/native/source-epoch-alter-routine-ddl-barrier.sql').read_text())
  oid,owner=self.admin.execute("SELECT oid,proowner FROM pg_proc WHERE oid='truss.runtime_fence_routine_ddl_writer()'::regprocedure").fetchone()
  cut=(_EpochComparison(installation,epoch,'catalog-fixture-target',profile,evidence),_DDLBarrierComparison(owner,oid,source.split('AS $$',1)[1].split('$$;',1)[0],include_alter_routine=True))
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
    for command in ('ALTER FUNCTION truss.catalog_subject_current(text) STABLE','ALTER ROUTINE truss.catalog_subject_current(text) STABLE'):
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
