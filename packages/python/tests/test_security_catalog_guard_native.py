"""Before-effect same-backend fact exclusion in accepted-catalog policy read."""
import json,sys
from pathlib import Path
from unittest.mock import patch
import psycopg
from psycopg import sql
from truss import Ok,Error
from truss._psycopg_fact_cut import _FactRelationComparison
import test_security_catalog_read_native as catalog
ROOT=Path(__file__).resolve().parents[3]

class CatalogFactGuardTests(catalog.AcceptedCatalogReadNativeTests):
 for name in tuple(n for n in dir(catalog.AcceptedCatalogReadNativeTests) if n.startswith('test_')):locals()[name]=None
 def install_guard(self):
  source=(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text()
  self.admin.execute(source)
  self.admin.execute(sql.SQL('ALTER FUNCTION truss.runtime_fence_authorization_fact_write() OWNER TO {}').format(sql.Identifier(self.installation.owner_role)))
  self.admin.execute('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON truss.object FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write();ALTER TABLE truss.object ENABLE ALWAYS TRIGGER fact_write_fence')
  oid,owner=self.admin.execute("SELECT oid,relowner FROM pg_class WHERE oid='truss.object'::regclass").fetchone()
  return _FactRelationComparison('truss','object',oid,owner,source.split('AS $$',1)[1].split('$$;',1)[0])
 def test_lock_only_allows_uncommitted_same_backend_fact_change(self):
  mapping=self.populated();assessment=json.loads(mapping.accepted_catalog_assessment)
  active=next(p['prop_id'] for p in assessment['inventory']['properties'] if p['element']=='active')
  original=catalog.read.subprocess.run;observed=[]
  def change(*args,**kwargs):
   self.admin.execute("UPDATE truss.object SET props=jsonb_set(props,%s::text[],'false'::jsonb) WHERE props->%s->>'kind'='boolean'",([str(active),'value'],str(active)))
   observed.append(self.admin.execute('SELECT count(*) FROM truss.object WHERE props->%s->>\'value\'=\'true\'',(str(active),)).fetchone()[0])
   return original(*args,**kwargs)
  with patch.object(catalog.read.subprocess,'run',change):result=catalog.read.run_owned_catalog_resource_read(self.host,self.tx,mapping,'s1')
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(observed,[0])
  self.assertEqual([r['key'] for r in result.value['rows']],[[{'string':'r1'}]])
 def test_selected_guard_refuses_all_events_before_effect(self):
  """@covers US-056-AC2; @covers US-056-AC9; component prerequisites only."""
  mapping=self.populated();relation=self.install_guard();original=catalog.read.subprocess.run;states=[]
  def refuse(*args,**kwargs):
   for command in ('UPDATE truss.object SET props=props','DELETE FROM truss.object','INSERT INTO truss.object SELECT * FROM truss.object','TRUNCATE truss.object CASCADE'):
    self.admin.execute('SAVEPOINT same_writer')
    try:
     with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as caught:self.admin.execute(command)
     self.assertEqual(caught.exception.diag.message_primary,'selected authorization fact cut excludes same-backend writes')
     states.append(caught.exception.sqlstate)
    finally:self.admin.execute('ROLLBACK TO same_writer');self.admin.execute('RELEASE same_writer')
   self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(10,))
   return original(*args,**kwargs)
  with patch.object(catalog.read.subprocess,'run',refuse):result=catalog.read.run_owned_catalog_resource_read(self.host,self.tx,mapping,'s1',fact_relations=(relation,))
  self.assertIsInstance(result,Ok,str(self.host._custody.last_attempt.error));self.assertEqual(states,['55000']*4)
  self.assertEqual([r['key'] for r in result.value['rows']],[[{'string':'r1'}]])
 def test_disabled_guard_refuses_before_evaluator(self):
  mapping=self.populated();relation=self.install_guard();self.admin.execute('ALTER TABLE truss.object DISABLE TRIGGER fact_write_fence')
  with patch.object(catalog.read.subprocess,'run') as evaluator:
   result=catalog.read.run_owned_catalog_resource_read(self.host,self.tx,mapping,'s1',fact_relations=(relation,));evaluator.assert_not_called()
  self.assertIsInstance(result,Error);attempt=self.host._custody.last_attempt
  self.assertEqual(str(attempt.error),'Exact installed ALWAYS fact guard required');self.assertEqual(attempt.phase,'contained');self.assertIsNone(attempt.cleanup_error)
