# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual Truss object/edge facts fed into the original shared UMF policy."""
import unittest,json,sys
from pathlib import Path
from unittest.mock import patch
import psycopg
from truss.execution import Ok,Error
from truss._psycopg_fact_cut import _FactRelationComparison
import test_psycopg_fact_cut_native as facts
import test_psycopg_epoch_cut_native as epochs
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import security_graph_read as graph


def string(value):return {'kind':'string','text':value}


class SecurityGraphReadNativeTests(unittest.TestCase):
    run_pg=classmethod(facts.PsycopgFactCutNativeTests.run_pg.__func__)
    @classmethod
    def setUpClass(cls):
        facts.PsycopgFactCutNativeTests.setUpClass.__func__(cls)
        try:
            with psycopg.connect(host=str(cls.socket),user='postgres',dbname=cls.database,autocommit=True) as c:
                c.execute("INSERT INTO truss.type_def(document_id,type_id,module,element,kind,since_rev,lineage_profile,lineage_bytes,definition_source_kind,binding_source_rev,binding_source_pointer,binding_source_bytes) VALUES('fixture',102,'fixture','Resource','entity',0,'fixture',decode('05','hex'),'accepted_binding',0,'#/Resource',decode('05','hex'))")
                c.execute("INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,target_min,lifecycle,directed,since_rev,doc_ord,definition_source_kind,binding_source_rev,binding_source_pointer,binding_source_bytes) VALUES('fixture',102,'fixture','owned_by','owned_by',0,0,'fixture',true,0,0,'accepted_binding',0,'#/owned_by',decode('06','hex')); INSERT INTO truss.rel_endpoint VALUES(102,102,101)")
                c.execute("UPDATE truss.object SET props=%s::jsonb WHERE id=100",(json.dumps({'1':string('s1')}),))
                c.execute("UPDATE truss.object SET props=%s::jsonb WHERE id=200",(json.dumps({'2':string('p1')}),))
                c.execute("INSERT INTO truss.object(id,type_id,props,rev) VALUES(300,102,%s::jsonb,0),(301,102,%s::jsonb,0),(201,101,%s::jsonb,0)",(json.dumps({'3':string('r1')}),json.dumps({'3':string('r2')}),json.dumps({'2':string('p2')})))
                c.execute("UPDATE truss.edge SET props=%s::jsonb WHERE id=100",(json.dumps({'4':string('a1'),'5':{'kind':'boolean','value':True}}),))
                c.execute("INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,props,rev) VALUES(102,102,300,102,200,101,%s::jsonb,0),(103,102,301,102,201,101,%s::jsonb,0),(104,100,100,100,201,101,%s::jsonb,0)",(json.dumps({'6':string('o1')}),json.dumps({'6':string('o2')}),json.dumps({'4':string('a2'),'5':{'kind':'boolean','value':False}})))
                c.execute("INSERT INTO truss.object(id,type_id,props,rev) VALUES(302,102,%s::jsonb,0),(303,102,%s::jsonb,0),(202,101,%s::jsonb,0)",(json.dumps({'3':string('r3')}),json.dumps({'3':string('r4')}),json.dumps({'2':string('p3')})))
                c.execute("INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,props,rev) VALUES(105,102,303,102,202,101,%s::jsonb,0)",(json.dumps({'6':string('o3')}),))
                c.execute('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON truss.object FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write(); ALTER TABLE truss.object ENABLE ALWAYS TRIGGER fact_write_fence')
                oid,owner=c.execute("SELECT oid,relowner FROM pg_class WHERE oid='truss.object'::regclass").fetchone()
                source=(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0]
                cls.graph_relations=(_FactRelationComparison('truss','object',oid,owner,source),cls.bindings['edge'])
        except BaseException:
            epochs.PsycopgEpochCutNativeTests.tearDownClass.__func__(cls);raise
    tearDownClass=classmethod(epochs.PsycopgEpochCutNativeTests.tearDownClass.__func__)
    def setUp(self):
        epochs.PsycopgEpochCutNativeTests.setUp(self)
        self.connection.execute('ALTER TABLE truss.object ENABLE ALWAYS TRIGGER fact_write_fence')
        for row,address,value in ((100,'1','s1'),(200,'2','p1'),(201,'2','p2'),(300,'3','r1'),(301,'3','r2')):
            self.connection.execute('UPDATE truss.object SET props=%s::jsonb WHERE id=%s',(json.dumps({address:string(value)}),row))
        self.connection.execute("UPDATE truss.edge SET props=jsonb_set(props,'{5,value}','false') WHERE id=104")
    tearDown=epochs.PsycopgEpochCutNativeTests.tearDown
    begin=epochs.PsycopgEpochCutNativeTests.begin
    comparison=epochs.PsycopgEpochCutNativeTests.comparison
    def assert_refusal(self,result,message):
        self.assertIsInstance(result,Error)
        attempt=self.host._custody.last_attempt
        self.assertIsInstance(attempt.error,ValueError)
        self.assertEqual(str(attempt.error),message)
        self.assertEqual(attempt.phase,'contained')
        self.assertIsNone(attempt.cleanup_error)
    def read(self,t,subject='s1'):return graph.run_owned_graph_resource_read(self.host,t,self.comparison(),self.graph_relations,subject)
    def test_graph_business_keys_and_shared_policy_under_native_cut(self):
        """@covers US-056-AC2; @covers US-056-AC6; component prerequisites only."""
        t=self.begin();original=graph.subprocess.run;observed=[]
        def during_evaluation(*args,**kwargs):
            observed.append(True)
            with psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database,autocommit=True,options='-c lock_timeout=100ms') as writer:
                for sql in ("UPDATE truss.object SET props='{}' WHERE id=100",'DELETE FROM truss.edge WHERE id=100'):
                    with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute(sql)
            return original(*args,**kwargs)
        with patch.object(graph.subprocess,'run',during_evaluation):result=self.read(t)
        self.assertIsInstance(result,Ok,str(result));self.assertEqual(observed,[True])
        self.assertEqual([r['key'] for r in result.value['rows']],[[{'string':'r1'}]])
        self.assertEqual(result.value['rows'][0]['output'][0]['disposition'],'withheld')
        self.assertNotIn('300',json.dumps(result.value))
        for sql in ("UPDATE truss.object SET props='{}' WHERE id=100",'DELETE FROM truss.edge WHERE id=100'):
            refusal=self.host._run_operation(t,lambda c,o:c.execute(sql));self.assertIsInstance(refusal,Error);self.assertEqual(refusal.error.sql_state,'55000')
    def test_changed_assignment_uses_same_ontology_policy(self):
        self.connection.execute("UPDATE truss.edge SET props=jsonb_set(props,'{5,value}','true') WHERE id=104")
        result=self.read(self.begin());self.assertIsInstance(result,Ok,str(result))
        self.assertEqual([r['key'] for r in result.value['rows']],[[{'string':'r1'}],[{'string':'r2'}]])
    def test_malformed_business_key_refuses_before_evaluator(self):
        self.connection.execute("UPDATE truss.object SET props='{}' WHERE id=100")
        with patch.object(graph.subprocess,'run',side_effect=AssertionError('Must not evaluate partial graph')) as evaluator:
            result=self.read(self.begin())
            evaluator.assert_not_called()
        self.assert_refusal(result,'Exact mapped native graph scalar required')
    def test_duplicate_semantic_identity_refuses_entire_read(self):
        self.connection.execute("UPDATE truss.object SET props=%s::jsonb WHERE id=301",(json.dumps({'3':string('r1')}),))
        original=graph.subprocess.run;errors=[]
        def inspect_refusal(*args,**kwargs):
            result=original(*args,**kwargs);errors.append(result.stderr);return result
        with patch.object(graph.subprocess,'run',inspect_refusal):
            self.assert_refusal(self.read(self.begin()),'Original graph UMF fixture evaluation refused')
        self.assertEqual(len(errors),1)
        self.assertIn('Unique original captured semantic identity required',errors[0])
    def test_missing_graph_guard_refuses_before_evaluator(self):
        self.connection.execute('ALTER TABLE truss.object DISABLE TRIGGER fact_write_fence')
        with patch.object(graph.subprocess,'run',side_effect=AssertionError('Must not evaluate unguarded graph')) as evaluator:
            result=self.read(self.begin())
            evaluator.assert_not_called()
        self.assert_refusal(result,'Exact installed ALWAYS fact guard required')
