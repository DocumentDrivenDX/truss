"""Actual flat Assignment and native Truss edge fact-cut components."""
import unittest
from pathlib import Path
import psycopg
from psycopg import sql
import test_psycopg_epoch_cut_native as epoch_tests
from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison,_run_fenced_fact_operation
from truss.execution import Ok,Error
ROOT=Path(__file__).resolve().parents[3]

class PsycopgFactCutNativeTests(unittest.TestCase):
    run_pg=classmethod(epoch_tests.PsycopgEpochCutNativeTests.run_pg.__func__)
    @classmethod
    def setUpClass(cls):
        epoch_tests.PsycopgEpochCutNativeTests.setUpClass.__func__(cls)
        try:
            with psycopg.connect(host=str(cls.socket),user='postgres',dbname='postgres',autocommit=True) as c:
                c.execute('CREATE TABLE truss.flat_assignment(staff_id bigint NOT NULL,project_id bigint NOT NULL,active boolean NOT NULL); INSERT INTO truss.flat_assignment VALUES(100,200,true)')
                c.execute("INSERT INTO truss.type_def(document_id,type_id,module,element,kind,since_rev,lineage_profile,lineage_bytes,definition_source_kind,binding_source_rev,binding_source_pointer,binding_source_bytes) VALUES('fixture',100,'fixture','Staff','entity',0,'fixture',decode('01','hex'),'accepted_binding',0,'#/Staff',decode('01','hex')),('fixture',101,'fixture','Project','entity',0,'fixture',decode('02','hex'),'accepted_binding',0,'#/Project',decode('02','hex'))")
                c.execute("INSERT INTO truss.schema_doc VALUES(0,0,'fixture','fixture','fixture',encode(sha256(convert_to('{}','UTF8')),'hex'),'{}','{}')")
                c.execute("INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,target_min,lifecycle,directed,since_rev,doc_ord,definition_source_kind,binding_source_rev,binding_source_pointer,binding_source_bytes) VALUES('fixture',100,'fixture','works_on','works_on',0,0,'fixture',true,0,0,'accepted_binding',0,'#/works_on',decode('03','hex')); INSERT INTO truss.rel_endpoint VALUES(100,100,101); INSERT INTO truss.object(id,type_id,rev) VALUES(100,100,0),(200,101,0); INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,props,rev) VALUES(100,100,100,100,200,101,'{}',0)")
                c.execute((ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text())
                for name in ('flat_assignment','edge'):
                    c.execute(sql.SQL('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON {} FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write()').format(sql.Identifier('truss',name)))
                    c.execute(sql.SQL('ALTER TABLE {} ENABLE ALWAYS TRIGGER fact_write_fence').format(sql.Identifier('truss',name)))
                cls.bindings={r[0]:_FactRelationComparison('truss',r[0],r[1],r[2],(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0]) for r in c.execute("SELECT relname,oid,relowner FROM pg_class WHERE oid IN ('truss.flat_assignment'::regclass,'truss.edge'::regclass)")}
        except BaseException:
            epoch_tests.PsycopgEpochCutNativeTests.tearDownClass.__func__(cls)
            raise
    tearDownClass=classmethod(epoch_tests.PsycopgEpochCutNativeTests.tearDownClass.__func__)
    setUp=epoch_tests.PsycopgEpochCutNativeTests.setUp
    tearDown=epoch_tests.PsycopgEpochCutNativeTests.tearDown
    begin=epoch_tests.PsycopgEpochCutNativeTests.begin
    comparison=epoch_tests.PsycopgEpochCutNativeTests.comparison
    def cut(self,t,callback,bindings=None):return _run_fenced_fact_operation(self.host,t,self.comparison(),bindings or tuple(self.bindings.values()),callback)
    def fact_shares(self):return self.connection.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.flat_assignment'::regclass,'truss.edge'::regclass)").fetchone()[0]
    def test_flat_and_native_graph_membership_under_joint_cut(self):
        t=self.begin()
        def read(c):
            c.execute("SELECT project_id::text FROM truss.flat_assignment WHERE staff_id=100 AND active");flat=c.fetchall()
            c.execute("SELECT target_id::text FROM truss.edge WHERE rel_type_id=100 AND source_id=100 AND source_type=100 AND target_type=101");graph=c.fetchall()
            self.assertEqual(flat,[('200',)]);self.assertEqual(graph,flat)
            with psycopg.connect(host=str(self.socket),user='postgres',dbname='postgres',autocommit=True,options='-c lock_timeout=150ms -c statement_timeout=1500') as w:
                for statement in ('UPDATE truss.flat_assignment SET active=false',"UPDATE truss.edge SET ver=ver+1",'INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(101,100,100,100,200,101,0)','DELETE FROM truss.edge','TRUNCATE truss.edge CASCADE'):
                    with self.assertRaises(psycopg.errors.LockNotAvailable):w.execute(statement)
            return 'same-project'
        self.assertEqual(self.cut(t,read),Ok('same-project'))
    def test_same_writer_all_four_events_refuse_before_effect(self):
        t=self.begin()
        for statement in ('INSERT INTO truss.flat_assignment VALUES(100,201,true)','UPDATE truss.flat_assignment SET active=false','DELETE FROM truss.flat_assignment','TRUNCATE truss.flat_assignment',"UPDATE truss.edge SET ver=ver+1",'INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(101,100,100,100,200,101,0)','DELETE FROM truss.edge','TRUNCATE truss.edge CASCADE'):
            result=self.cut(t,lambda c:c.execute(statement));self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
        self.assertEqual(self.connection.execute('TABLE truss.flat_assignment').fetchall(),[(100,200,True)])
    def test_pending_fact_writer_refuses_before_callback(self):
        t=self.begin();called=[]
        with psycopg.connect(host=str(self.socket),user='postgres',dbname='postgres') as w:
            w.execute('UPDATE truss.flat_assignment SET active=false')
            result=self.cut(t,lambda c:called.append(True));self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55P03');self.assertEqual(called,[])
            self.assertEqual(self.fact_shares(),0)
            w.rollback()
        self.assertEqual(self.cut(t,lambda c:'fresh'),Ok('fresh'))
    def test_changed_original_relation_binding_refuses_before_callback(self):
        t=self.begin();called=[];r=self.bindings['flat_assignment']
        result=self.cut(t,lambda c:called.append(True),(_FactRelationComparison(r.schema,r.name,r.oid+1,r.owner_oid,r.guard_source),))
        self.assertIsInstance(result,Error);self.assertEqual(called,[])
        self.assertEqual(self.fact_shares(),0)
    def test_omitted_trigger_allows_own_fact_change_despite_lock(self):
        self.connection.execute('ALTER TABLE truss.flat_assignment DISABLE TRIGGER fact_write_fence')
        try:
            t=self.begin()
            def change(c):
                c.execute('UPDATE truss.flat_assignment SET active=false');c.execute('SELECT active FROM truss.flat_assignment');return c.fetchone()[0]
            called=[]
            result=self.cut(t,lambda c:called.append(True));self.assertIsInstance(result,Error);self.assertEqual(called,[])
            # Deliberately omit installed-guard qualification but retain actual SHARE.
            def omitted(c):
                c.execute('LOCK TABLE truss.flat_assignment IN SHARE MODE NOWAIT');return change(c)
            self.assertEqual(epoch_tests._run_fenced_epoch_operation(self.host,t,self.comparison(),omitted),Ok(False))
        finally:
            self.connection.execute('ROLLBACK');self.connection.execute('ALTER TABLE truss.flat_assignment ENABLE ALWAYS TRIGGER fact_write_fence')
    def test_replica_mode_still_refuses_fact_change(self):
        t=self.begin();self.connection.execute('SET LOCAL session_replication_role=replica')
        result=self.cut(t,lambda c:c.execute('DELETE FROM truss.flat_assignment'));self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
    def test_host_temp_catalog_shadows_do_not_substitute_native_binding(self):
        t=self.begin()
        self.connection.execute('CREATE TEMP TABLE pg_database(oid oid,datname name); CREATE TEMP TABLE pg_class(oid oid,relowner oid,relkind text,relpersistence text,relnamespace oid); CREATE TEMP TABLE pg_inherits(inhrelid oid,inhparent oid); SET LOCAL search_path=pg_temp,pg_catalog')
        self.assertEqual(self.cut(t,lambda c:'original-catalogs'),Ok('original-catalogs'))
    def test_inherited_fact_source_refuses_before_callback(self):
        t=self.begin();self.connection.execute('CREATE TABLE truss.assignment_child() INHERITS(truss.flat_assignment)');called=[]
        result=self.cut(t,lambda c:called.append(True));self.assertIsInstance(result,Error);self.assertEqual(called,[])
    def test_duplicate_binding_refuses_before_native_assignment(self):
        t=self.begin();r=self.bindings['edge']
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))
        with self.assertRaises(ValueError):self.cut(t,lambda c:'unreachable',(r,r))
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))
    def test_committed_revocation_visible_after_original_reader_release(self):
        t=self.begin()
        def projects(c):
            c.execute('SELECT project_id::text FROM truss.flat_assignment WHERE staff_id=100 AND active');flat=c.fetchall()
            c.execute("SELECT target_id::text FROM truss.edge WHERE rel_type_id=100 AND source_id=100 AND source_type=100 AND target_type=101")
            graph=c.fetchall();self.assertEqual(graph,flat);return tuple(r[0] for r in flat)
        self.assertEqual(self.cut(t,projects),Ok(('200',)))
        self.connection.execute('ROLLBACK')
        try:
            with psycopg.connect(host=str(self.socket),user='postgres',dbname='postgres') as w:
                w.execute('UPDATE truss.flat_assignment SET active=false')
                w.execute('DELETE FROM truss.edge')
            fresh=self.begin();self.assertEqual(self.cut(fresh,projects),Ok(()))
        finally:
            self.connection.execute('ROLLBACK')
            with psycopg.connect(host=str(self.socket),user='postgres',dbname='postgres') as w:
                w.execute('UPDATE truss.flat_assignment SET active=true')
                w.execute('INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(100,100,100,100,200,101,0)')

    def field_binding(self, column=None):
        r=self.bindings['flat_assignment']
        return _FactRelationComparison(r.schema,r.name,r.oid,r.owner_oid,r.guard_source,
                                       (column or _FactColumnComparison('active',3,16,-1,True,0),))
    def test_original_active_column_descriptor_passes_under_cut(self):
        t=self.begin()
        self.assertEqual(self.cut(t,lambda c:'original-field',(self.field_binding(),)),Ok('original-field'))
    def test_valid_wrong_column_descriptor_refuses_before_callback(self):
        t=self.begin();called=[]
        wrong=_FactColumnComparison('active',3,20,-1,True,0)
        result=self.cut(t,lambda c:called.append(True),(self.field_binding(wrong),))
        self.assertIsInstance(result,Error);self.assertEqual(called,[]);self.assertEqual(self.fact_shares(),0)
    def test_changed_native_nullability_refuses_before_callback(self):
        t=self.begin();self.connection.execute('ALTER TABLE truss.flat_assignment ALTER COLUMN active DROP NOT NULL');called=[]
        result=self.cut(t,lambda c:called.append(True),(self.field_binding(),))
        self.assertIsInstance(result,Error);self.assertEqual(called,[]);self.assertEqual(self.fact_shares(),0)
    def test_drop_recreate_same_named_column_refuses_original_number(self):
        t=self.begin();self.connection.execute('ALTER TABLE truss.flat_assignment DROP COLUMN active');self.connection.execute('ALTER TABLE truss.flat_assignment ADD COLUMN active boolean NOT NULL DEFAULT true');called=[]
        result=self.cut(t,lambda c:called.append(True),(self.field_binding(),))
        self.assertIsInstance(result,Error);self.assertEqual(called,[]);self.assertEqual(self.fact_shares(),0)
    def test_duplicate_column_recipe_refuses_before_native_assignment(self):
        t=self.begin();r=self.field_binding();bad=_FactRelationComparison(r.schema,r.name,r.oid,r.owner_oid,r.guard_source,r.columns*2)
        with self.assertRaises(ValueError):self.cut(t,lambda c:'unreachable',(bad,))
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))

    def test_changed_native_field_type_refuses_before_callback(self):
        t=self.begin();self.connection.execute('ALTER TABLE truss.flat_assignment ALTER COLUMN active TYPE text USING active::text');called=[];prior_shares=self.fact_shares()
        result=self.cut(t,lambda c:called.append(True),(self.field_binding(),))
        self.assertIsInstance(result,Error);self.assertEqual(called,[]);self.assertEqual(self.fact_shares(),prior_shares)
    def test_temp_attribute_catalog_cannot_substitute_original_field(self):
        t=self.begin();self.connection.execute('CREATE TEMP TABLE pg_attribute(attname text,attnum smallint,atttypid oid,atttypmod integer,attnotnull boolean,attcollation oid,attgenerated text,attidentity text,attisdropped boolean,attrelid oid); SET LOCAL search_path=pg_temp,pg_catalog')
        self.assertEqual(self.cut(t,lambda c:'original-field',(self.field_binding(),)),Ok('original-field'))
