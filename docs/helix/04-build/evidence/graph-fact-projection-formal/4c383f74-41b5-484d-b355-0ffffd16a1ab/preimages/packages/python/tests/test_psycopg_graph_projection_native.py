"""Private native graph projection guards, not ordinary mutation admission."""
import unittest,json
from pathlib import Path
import psycopg
import test_psycopg_fact_cut_native as fact_tests
import test_psycopg_epoch_cut_native as epoch_tests
from truss.execution import Ok,Error
ROOT=Path(__file__).resolve().parents[3]

class PsycopgGraphProjectionNativeTests(unittest.TestCase):
    run_pg=classmethod(fact_tests.PsycopgFactCutNativeTests.run_pg.__func__)
    @classmethod
    def setUpClass(cls):
        fact_tests.PsycopgFactCutNativeTests.setUpClass.__func__(cls)
        try:
            with psycopg.connect(host=str(cls.socket),user='postgres',dbname='postgres',autocommit=True) as c:
                c.execute('DROP TRIGGER fact_write_fence ON truss.edge')
                c.execute((ROOT/'docs/helix/04-build/evidence/authorization-graph-fact-scope.owner-export.sql').read_text())
                c.execute((ROOT/'packages/postgresql/native/authorization-graph-fact-scope.sql').read_text())
                c.execute("INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,target_min,lifecycle,directed,since_rev,doc_ord,definition_source_kind,binding_source_rev,binding_source_pointer,binding_source_bytes) VALUES('fixture',101,'fixture','mentors','mentors',0,0,'fixture',true,0,0,'accepted_binding',0,'#/mentors',decode('04','hex')); INSERT INTO truss.rel_endpoint VALUES(101,100,100)")
        except BaseException:
            epoch_tests.PsycopgEpochCutNativeTests.tearDownClass.__func__(cls);raise
    tearDownClass=classmethod(epoch_tests.PsycopgEpochCutNativeTests.tearDownClass.__func__)
    setUp=epoch_tests.PsycopgEpochCutNativeTests.setUp
    tearDown=epoch_tests.PsycopgEpochCutNativeTests.tearDown
    begin=epoch_tests.PsycopgEpochCutNativeTests.begin
    comparison=epoch_tests.PsycopgEpochCutNativeTests.comparison
    def cut(self,t,callback,types=(100,),evidence=b'original-fixture-scope'):
        def acquire(c):
            c.execute('LOCK TABLE truss.edge IN SHARE MODE NOWAIT')
            if types is not None:
                c.execute('SELECT truss.runtime_register_graph_fact_scope(%s,%s)::text',(list(types),evidence))
                self.assertEqual(c.fetchone()[0],str(len(set(types))))
            return callback(c)
        return epoch_tests._run_fenced_epoch_operation(self.host,t,self.comparison(),acquire)
    def test_unrelated_business_edge_insert_update_delete_allowed(self):
        t=self.begin()
        def work(c):
            c.execute('INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(101,101,100,100,100,100,0)')
            c.execute('UPDATE truss.edge SET ver=ver+1 WHERE id=101');self.assertEqual(c.rowcount,1)
            c.execute('DELETE FROM truss.edge WHERE id=101');self.assertEqual(c.rowcount,1)
            c.execute('SELECT id::text,rel_type_id::text FROM truss.edge');return c.fetchall()
        self.assertEqual(self.cut(t,work),Ok([('100','100')]))
    def test_selected_association_insert_update_delete_and_truncate_refuse(self):
        t=self.begin()
        commands=['INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(102,100,100,100,200,101,0)','UPDATE truss.edge SET ver=ver+1 WHERE id=100','DELETE FROM truss.edge WHERE id=100','TRUNCATE truss.edge CASCADE']
        for q in commands:
            result=self.cut(t,lambda c:c.execute(q));self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
    def test_old_or_new_selected_type_excludes_reclassification(self):
        t=self.begin();self.connection.execute('INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(101,101,100,100,100,100,0)')
        for q in ('UPDATE truss.edge SET rel_type_id=100,target_id=200,target_type=101 WHERE id=101','UPDATE truss.edge SET rel_type_id=101,target_id=100,target_type=100 WHERE id=100'):
            result=self.cut(t,lambda c:c.execute(q));self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
    def test_missing_original_scope_refuses_unrelated_write(self):
        t=self.begin();q='INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(101,101,100,100,100,100,0)'
        result=self.cut(t,lambda c:c.execute(q),types=None);self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
    def test_scope_is_native_retained_and_cannot_shrink(self):
        t=self.begin()
        def observe(c):
            c.execute('SELECT original_writer_xid::text,original_context_bytes,original_evidence_bytes FROM truss.authorization_graph_fact_scope')
            row=c.fetchone();context=json.loads(bytes(row[1]));self.assertEqual(context['xid'],row[0]);self.assertEqual(bytes(row[2]),b'original-fixture-scope')
            return row[0]
        self.assertIsInstance(self.cut(t,observe),Ok)
        for q in ('DELETE FROM truss.authorization_graph_fact_scope','UPDATE truss.authorization_graph_fact_scope SET rel_type_id=101','TRUNCATE truss.authorization_graph_fact_scope'):
            result=self.host._run_operation(t,lambda c,o:c.execute(q));self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
        result=self.cut(t,lambda c:'bad',evidence=b'changed');self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
        self.assertEqual(self.cut(t,lambda c:'same'),Ok('same'))
    def test_native_rollback_removes_scope_with_original_lock(self):
        t=self.begin();self.connection.execute('SAVEPOINT before_scope');self.assertEqual(self.cut(t,lambda c:'held'),Ok('held'))
        xid=self.connection.execute('SELECT pg_current_xact_id()::text').fetchone()
        self.connection.execute('ROLLBACK TO before_scope')
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id()::text').fetchone(),xid)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM truss.authorization_graph_fact_scope').fetchone(),(0,))
        self.assertEqual(self.cut(t,lambda c:'new'),Ok('new'))
    def test_omitted_required_association_scope_allows_changed_fact(self):
        t=self.begin()
        def omitted(c):
            c.execute('DELETE FROM truss.edge WHERE id=100');c.execute('SELECT count(*)::text FROM truss.edge WHERE rel_type_id=100');return c.fetchone()[0]
        self.assertEqual(self.cut(t,omitted,types=(101,)),Ok('0'))
    def test_replica_mode_still_excludes_selected_fact(self):
        t=self.begin();self.connection.execute('SET LOCAL session_replication_role=replica')
        result=self.cut(t,lambda c:c.execute('DELETE FROM truss.edge WHERE id=100'));self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
    def test_scope_extension_retains_earlier_association(self):
        t=self.begin();self.assertEqual(self.cut(t,lambda c:'first'),Ok('first'))
        def extend(c):
            c.execute('SELECT truss.runtime_register_graph_fact_scope(%s,%s)::text',([101],b'original-fixture-scope'));self.assertEqual(c.fetchone(),('2',))
            c.execute('SELECT rel_type_id::text FROM truss.authorization_graph_fact_scope ORDER BY rel_type_id');return c.fetchall()
        self.assertEqual(self.host._run_operation(t,lambda c,o:extend(c)),Ok([('100',),('101',)]))
        for q in ('DELETE FROM truss.edge WHERE id=100','INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(101,101,100,100,100,100,0)'):
            result=self.host._run_operation(t,lambda c,o:c.execute(q));self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
    def test_malformed_or_over_capacity_scope_has_no_partial_rows(self):
        t=self.begin();self.assertEqual(self.cut(t,lambda c:'first'),Ok('first'))
        for types,evidence,state in (([],b'original-fixture-scope','55000'),([100,100],b'original-fixture-scope','55000'),([102],b'original-fixture-scope','55000'),([100],b'','55000'),(list(range(101,133)),b'original-fixture-scope','54000')):
            def attempt(c,o):c.execute('SELECT truss.runtime_register_graph_fact_scope(%s,%s)',(types,evidence))
            result=self.host._run_operation(t,attempt);self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,state)
            self.assertEqual(self.connection.execute('SELECT rel_type_id FROM truss.authorization_graph_fact_scope').fetchall(),[(100,)])
    def test_foreign_native_xid_scope_insert_refuses(self):
        t=self.begin()
        result=self.host._run_operation(t,lambda c,o:c.execute("INSERT INTO truss.authorization_graph_fact_scope VALUES((pg_current_xact_id()::text::numeric+1)::text::xid8,100,decode('01','hex'),decode('02','hex'))"))
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM truss.authorization_graph_fact_scope').fetchone(),(0,))
