"""Restricted native caller plus qualified caller/executor fact guards."""
import json,sys,os
from pathlib import Path
from unittest.mock import patch
from psycopg import sql
from truss import Ok,Error
from truss._psycopg_fact_cut import _FactRelationComparison
import test_security_catalog_subject_native as native
ROOT=Path(__file__).resolve().parents[3]
subject=native.subject

class GuardedSubjectTests(native.NativeCatalogSubjectTests):
 for name in tuple(n for n in dir(native.NativeCatalogSubjectTests) if n.startswith('test_')):locals()[name]=None
 def guarded_setup(self,disabled=None):
  mapping,c,h,t,selection,inspector=self.setup_subject()
  source=(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text()
  self.admin.execute(source)
  self.admin.execute(sql.SQL('ALTER FUNCTION truss.runtime_fence_authorization_fact_write() OWNER TO {}').format(sql.Identifier(self.installation.owner_role)))
  relations=[]
  for name in ('object','catalog_subject_map'):
   self.admin.execute(sql.SQL('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON {} FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write()').format(sql.Identifier('truss',name)))
   self.admin.execute(sql.SQL('ALTER TABLE {} ENABLE ALWAYS TRIGGER fact_write_fence').format(sql.Identifier('truss',name)))
   oid,owner=self.admin.execute('SELECT oid,relowner FROM pg_class WHERE oid=%s::regclass',('truss.'+name,)).fetchone()
   relations.append(_FactRelationComparison('truss',name,oid,owner,source.split('AS $$',1)[1].split('$$;',1)[0]))
  if disabled:self.admin.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER fact_write_fence').format(sql.Identifier('truss',disabled)))
  self.host.detach();self.admin.commit();self.admin.execute('BEGIN');self.host=native.catalog.adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
  return mapping,c,h,t,selection,inspector,tuple(relations)
 def test_complete_guarded_chain_without_raw_caller_privileges(self):
  """@covers US-056-AC2; @covers US-056-AC9; component prerequisites only."""
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  for table in ('truss.object','truss.catalog_subject_map'):
   for privilege in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE'):
    self.assertEqual(c.execute('SELECT pg_catalog.has_table_privilege(%s,%s)',(table,privilege)).fetchone(),(False,))
  original_encoder=subject.encode_literal_key_tuple;original_read=subject.run_owned_catalog_resource_read;encoded=[];delegated=[]
  def encode(*args,**kwargs):
   for relation in relations:
    self.assertEqual(self.admin.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND relation=%s AND mode='ShareLock' AND granted)",(c.info.backend_pid,relation.oid)).fetchone(),(True,))
   encoded.append(True);return original_encoder(*args,**kwargs)
  def execute(*args,**kwargs):
   self.assertEqual(len(kwargs['fact_relations']),1);self.assertEqual(kwargs['fact_relations'][0].name,'object')
   delegated.append(True);return original_read(*args,**kwargs)
  with patch.object(subject,'encode_literal_key_tuple',encode),patch.object(subject,'run_owned_catalog_resource_read',execute):
   result=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
  self.assertIsInstance(result,Ok,str(h._custody.last_attempt.error));self.assertEqual(encoded,[True,True]);self.assertEqual(delegated,[True])
  self.assertEqual([r['key'] for r in result.value['rows']],[[{'string':'r1'}]])
  self.assertEqual(result.value['rows'][0]['output'][0]['disposition'],'withheld')
  directory=os.environ.get('TRUSS_CATALOG_POLICY_READ_EVIDENCE')
  if directory:(Path(directory)/'decision.json').write_text(json.dumps(result.value,indent=2)+'\n')
 def assert_disabled_guard(self,disabled):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup(disabled)
  with patch.object(subject,'encode_literal_key_tuple') as encoder,patch.object(subject,'run_owned_catalog_resource_read') as evaluator:
   result=subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,relations)
   encoder.assert_not_called();evaluator.assert_not_called()
  self.assertIsInstance(result,Error);attempt=h._custody.last_attempt
  self.assertEqual(str(attempt.error),'Exact installed ALWAYS fact guard required');self.assertEqual(attempt.phase,'contained');self.assertIsNone(attempt.cleanup_error)
 def test_disabled_object_guard_refuses_before_codec_and_executor(self):
  self.assert_disabled_guard('object')
 def test_disabled_subject_map_guard_refuses_before_codec_and_executor(self):
  self.assert_disabled_guard('catalog_subject_map')
 def test_missing_mandatory_cut_never_calls_inspector_or_hosts(self):
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  with patch.object(type(h),'_run_operation') as operation,patch.object(subject,'_prepare_subject_operation') as prepare:
   with self.assertRaisesRegex(ValueError,'Mandatory native caller fact cuts required'):
    subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,None)
   operation.assert_not_called();prepare.assert_not_called()

 def test_invalid_column_carriers_refuse_before_inspector_and_hosts(self):
  from dataclasses import replace,dataclass
  mapping,c,h,t,selection,inspector,relations=self.guarded_setup()
  @dataclass
  class ForeignColumn:
   name:str='foreign'
  for columns in ([],iter(()),(ForeignColumn(),),(None,)*1601):
   invalid=(replace(relations[0],columns=columns),relations[1])
   with patch.object(type(h),'_run_operation') as operation,patch.object(subject,'_prepare_subject_operation') as prepare:
    with self.assertRaisesRegex(ValueError,'Exact bounded caller fact column comparisons required'):
     subject.run_guarded_native_catalog_resource_read(h,t,self.host,self.tx,mapping,selection,inspector,invalid)
    operation.assert_not_called();prepare.assert_not_called()
