"""Actual flat Assignment and native Truss edge fact-cut components."""
import unittest,hashlib,json,subprocess
from dataclasses import asdict
from pathlib import Path
import psycopg
from psycopg import sql
import test_psycopg_epoch_cut_native as epoch_tests
from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison,_run_fenced_fact_operation
from truss.execution import Ok,Error
from truss._psycopg_dependency_fact_cut import _DependencyFactProvider,_run_dependency_fact_operation,_run_epoch_bound_dependency_fact_operation,_capture_epoch_bound_dependency_cells
ROOT=Path(__file__).resolve().parents[3]

class PsycopgFactCutNativeTests(unittest.TestCase):
    run_pg=classmethod(epoch_tests.PsycopgEpochCutNativeTests.run_pg.__func__)
    @classmethod
    def setUpClass(cls):
        epoch_tests.PsycopgEpochCutNativeTests.setUpClass.__func__(cls)
        try:
            with psycopg.connect(host=str(cls.socket),user='postgres',dbname=cls.database,autocommit=True) as c:
                c.execute('CREATE TABLE truss.flat_assignment(staff_id bigint NOT NULL,project_id bigint NOT NULL,active boolean NOT NULL); INSERT INTO truss.flat_assignment VALUES(100,200,true)')
                c.execute("INSERT INTO truss.type_def(document_id,type_id,module,element,kind,since_rev,lineage_profile,lineage_bytes,definition_source_kind,binding_source_rev,binding_source_pointer,binding_source_bytes) VALUES('fixture',100,'fixture','Staff','entity',0,'fixture',decode('01','hex'),'accepted_binding',0,'#/Staff',decode('01','hex')),('fixture',101,'fixture','Project','entity',0,'fixture',decode('02','hex'),'accepted_binding',0,'#/Project',decode('02','hex'))")
                c.execute("INSERT INTO truss.schema_doc VALUES(0,0,'fixture','fixture','fixture',encode(sha256(convert_to('{}','UTF8')),'hex'),'{}','{}')")
                c.execute("INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,target_min,lifecycle,directed,since_rev,doc_ord,definition_source_kind,binding_source_rev,binding_source_pointer,binding_source_bytes) VALUES('fixture',100,'fixture','works_on','works_on',0,0,'fixture',true,0,0,'accepted_binding',0,'#/works_on',decode('03','hex')); INSERT INTO truss.rel_endpoint VALUES(100,100,101); INSERT INTO truss.object(id,type_id,rev) VALUES(100,100,0),(200,101,0); INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,props,rev) VALUES(100,100,100,100,200,101,'{}',0)")
                c.execute((ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text())
                for name in ('flat_assignment','edge'):
                    c.execute(sql.SQL('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON {} FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write()').format(sql.Identifier('truss',name)))
                    c.execute(sql.SQL('ALTER TABLE {} ENABLE ALWAYS TRIGGER fact_write_fence').format(sql.Identifier('truss',name)))
                c.execute("CREATE TABLE truss.sec_staff(staff_id text NOT NULL); CREATE TABLE truss.sec_project(project_id text NOT NULL); CREATE TABLE truss.sec_resource(resource_id text NOT NULL,salary bigint NOT NULL); CREATE TABLE truss.sec_ownership(owner_id text NOT NULL,resource_id text NOT NULL,project_id text NOT NULL); CREATE TABLE truss.sec_assignment(assignment_id text NOT NULL,staff_id text NOT NULL,project_id text NOT NULL,active boolean NOT NULL); INSERT INTO truss.sec_staff VALUES('s1'); INSERT INTO truss.sec_project VALUES('p1'); INSERT INTO truss.sec_resource VALUES('r1',100); INSERT INTO truss.sec_ownership VALUES('o1','r1','p1'); INSERT INTO truss.sec_assignment VALUES('a1','s1','p1',true)")
                cls.semantic_relations={}
                for name in ('sec_staff','sec_project','sec_resource','sec_ownership','sec_assignment'):
                    c.execute(sql.SQL('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON {} FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write()').format(sql.Identifier('truss',name)))
                    c.execute(sql.SQL('ALTER TABLE {} ENABLE ALWAYS TRIGGER fact_write_fence').format(sql.Identifier('truss',name)))
                    oid,owner=c.execute("SELECT oid,relowner FROM pg_catalog.pg_class WHERE oid=%s::regclass",('truss.'+name,)).fetchone()
                    cls.semantic_relations[name]=_FactRelationComparison('truss',name,oid,owner,(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0])
                cls.bindings={r[0]:_FactRelationComparison('truss',r[0],r[1],r[2],(ROOT/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text().split('AS $$',1)[1].split('$$;',1)[0]) for r in c.execute("SELECT relname,oid,relowner FROM pg_class WHERE oid IN ('truss.flat_assignment'::regclass,'truss.edge'::regclass)")}
                c.execute((ROOT/'packages/postgresql/native/source-epoch-shared-authority-writer.sql').read_text())
                c.execute((ROOT/'docs/helix/04-build/evidence/authority-epoch-reason.owner-export.sql').read_text())
                c.execute((ROOT/'packages/postgresql/native/source-epoch-authority-issue.sql').read_text())
        except BaseException:
            epoch_tests.PsycopgEpochCutNativeTests.tearDownClass.__func__(cls)
            raise
    tearDownClass=classmethod(epoch_tests.PsycopgEpochCutNativeTests.tearDownClass.__func__)
    setUp=epoch_tests.PsycopgEpochCutNativeTests.setUp
    tearDown=epoch_tests.PsycopgEpochCutNativeTests.tearDown
    begin=epoch_tests.PsycopgEpochCutNativeTests.begin
    comparison=epoch_tests.PsycopgEpochCutNativeTests.comparison
    def cut(self,t,callback,bindings=None,ddl_barrier=None):return _run_fenced_fact_operation(self.host,t,self.comparison(),bindings or tuple(self.bindings.values()),callback,ddl_barrier=ddl_barrier)
    def fact_shares(self):return self.connection.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND granted AND mode='ShareLock' AND relation IN ('truss.flat_assignment'::regclass,'truss.edge'::regclass)").fetchone()[0]
    def test_flat_and_native_graph_membership_under_joint_cut(self):
        t=self.begin()
        def read(c):
            c.execute("SELECT project_id::text FROM truss.flat_assignment WHERE staff_id=100 AND active");flat=c.fetchall()
            c.execute("SELECT target_id::text FROM truss.edge WHERE rel_type_id=100 AND source_id=100 AND source_type=100 AND target_type=101");graph=c.fetchall()
            self.assertEqual(flat,[('200',)]);self.assertEqual(graph,flat)
            with psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database,autocommit=True,options='-c lock_timeout=150ms -c statement_timeout=1500') as w:
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
        with psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database) as w:
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
            with psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database) as w:
                w.execute('UPDATE truss.flat_assignment SET active=false')
                w.execute('DELETE FROM truss.edge')
            fresh=self.begin();self.assertEqual(self.cut(fresh,projects),Ok(()))
        finally:
            self.connection.execute('ROLLBACK')
            with psycopg.connect(host=str(self.socket),user='postgres',dbname=self.database) as w:
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

    def dependency_providers(self):
        # Explicit original fixture mapping; no names-based mapping inference.
        specs=[('active','sec_assignment','active',4,16),('assignmentProject','sec_assignment','project_id',3,25),('assignmentStaff','sec_assignment','staff_id',2,25),('ownerProject','sec_ownership','project_id',3,25),('ownerResource','sec_ownership','resource_id',2,25),('projectId','sec_project','project_id',1,25),('resourceId','sec_resource','resource_id',1,25),('staffId','sec_staff','staff_id',1,25)]
        fields=tuple(_DependencyFactProvider('field',('domain','m',ref),self.semantic_relations[table],_FactColumnComparison(name,num,oid,-1,True,100 if oid==25 else 0)) for ref,table,name,num,oid in specs)
        return fields+tuple(_DependencyFactProvider('association',('domain','m',ref),self.semantic_relations[table]) for ref,table in [('Assignment','sec_assignment'),('Ownership','sec_ownership')])
    def dependency_cut(self,t,callback,providers=None):
        raw=(ROOT/'docs/helix/04-build/evidence/security-fact-requirements/requirements.json').read_bytes()
        return _run_dependency_fact_operation(self.host,t,self.comparison(),raw,hashlib.sha256(raw).hexdigest(),self.dependency_providers() if providers is None else providers,callback)
    def test_complete_original_dependency_fixture_cuts_all_five_tables(self):
        t=self.begin()
        def read(c):
            c.execute("SELECT r.resource_id::text FROM truss.sec_resource r JOIN truss.sec_ownership o ON o.resource_id=r.resource_id JOIN truss.sec_project p ON p.project_id=o.project_id JOIN truss.sec_assignment a ON a.project_id=p.project_id JOIN truss.sec_staff s ON s.staff_id=a.staff_id WHERE s.staff_id='s1' AND a.active")
            self.assertEqual(c.fetchall(),[('r1',)])
            c.execute("SELECT count(*)::text FROM pg_catalog.pg_locks l JOIN pg_catalog.pg_class t ON t.oid=l.relation WHERE l.pid=pg_catalog.pg_backend_pid() AND l.granted AND l.mode='ShareLock' AND t.relname IN ('sec_staff','sec_project','sec_resource','sec_ownership','sec_assignment')")
            return c.fetchone()[0]
        self.assertEqual(self.dependency_cut(t,read),Ok('5'))
    def test_missing_active_provider_refuses_before_native_assignment(self):
        t=self.begin();called=[]
        with self.assertRaisesRegex(ValueError,'Incomplete original'):
            self.dependency_cut(t,lambda c:called.append(True),self.dependency_providers()[1:])
        self.assertEqual(called,[]);self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))
    def test_association_only_providers_cannot_invoke_native_callback(self):
        t=self.begin();called=[]
        with self.assertRaisesRegex(ValueError,'Incomplete original'):
            self.dependency_cut(t,lambda c:called.append(True),self.dependency_providers()[-2:])
        self.assertEqual(called,[]);self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))
    def test_dependency_field_descriptor_substitution_refuses_callback(self):
        t=self.begin();called=[];providers=self.dependency_providers();p=providers[0]
        wrong=_DependencyFactProvider(p.kind,p.reference,p.relation,_FactColumnComparison('active',4,20,-1,True,0))
        self.assertIsInstance(self.dependency_cut(t,lambda c:called.append(True),(wrong,)+providers[1:]),Error);self.assertEqual(called,[])
    def test_complete_dependency_cut_excludes_same_writer_active_revocation(self):
        t=self.begin()
        result=self.dependency_cut(t,lambda c:c.execute('UPDATE truss.sec_assignment SET active=false'))
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
        self.assertEqual(self.connection.execute('SELECT active FROM truss.sec_assignment').fetchall(),[(True,)])

    def original_owner_decision(self, mutation=None, active_column='active', providers=None):
        t=self.begin()
        if mutation:self.connection.execute(mutation)
        def evaluate(c):
            capture={}
            queries={'Staff':'SELECT staff_id::text FROM truss.sec_staff','Project':'SELECT project_id::text FROM truss.sec_project','Resource':'SELECT resource_id::text,salary::text FROM truss.sec_resource','Ownership':'SELECT owner_id::text,resource_id::text,project_id::text FROM truss.sec_ownership','Assignment':'SELECT assignment_id::text,staff_id::text,project_id::text,active::text FROM truss.sec_assignment'}
            if active_column=='decoy_active':queries['Assignment']=queries['Assignment'].replace('active::text','decoy_active::text')
            elif active_column!='active':raise ValueError('Exact fixture decoder required')
            for name,query in queries.items():
                c.execute(query,prepare=False,binary=False)
                self.assertTrue(all(d.type_code==25 for d in c.description))
                rows=c.fetchmany(101);self.assertLessEqual(len(rows),100);capture[name]=rows
            result=subprocess.run(['/opt/homebrew/bin/bun','scripts/evaluate-security-flat-fixture.ts'],cwd=ROOT,input=json.dumps(capture),capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            return json.loads(result.stdout)
        result=self.dependency_cut(t,evaluate,providers);self.assertIsInstance(result,Ok);return result.value
    def test_original_owner_permits_native_same_project_and_withholds_salary(self):
        self.assertEqual(self.original_owner_decision(),{'decision':'permit','output':[{'field':{'documentId':'domain','moduleId':'m','elementId':'salary'},'disposition':'withheld'}]})
    def test_original_owner_denies_native_active_revocation(self):
        self.assertEqual(self.original_owner_decision('UPDATE truss.sec_assignment SET active=false')['decision'],'deny')
    def test_original_owner_denies_native_other_staff_assignment(self):
        self.assertEqual(self.original_owner_decision("UPDATE truss.sec_assignment SET staff_id='s2'")['decision'],'deny')
    def test_original_owner_denies_native_sibling_project_assignment(self):
        self.assertEqual(self.original_owner_decision("UPDATE truss.sec_assignment SET project_id='p2'")['decision'],'deny')
    def test_original_owner_denies_native_missing_ownership(self):
        self.assertEqual(self.original_owner_decision('DELETE FROM truss.sec_ownership')['decision'],'deny')
    def test_original_owner_denies_native_missing_assignment(self):
        self.assertEqual(self.original_owner_decision('DELETE FROM truss.sec_assignment')['decision'],'deny')

    def test_well_typed_wrong_active_mapping_counterexample_permits_revoked_staff(self):
        providers=self.dependency_providers();p=providers[0]
        # Negative control: complete declared refs and real native cuts do not
        # authenticate semantic correspondence to the original active field.
        wrong=_DependencyFactProvider(p.kind,p.reference,p.relation,_FactColumnComparison('decoy_active',5,16,-1,True,0))
        mutation='ALTER TABLE truss.sec_assignment ADD COLUMN decoy_active boolean NOT NULL DEFAULT true; UPDATE truss.sec_assignment SET active=false'
        observed=self.original_owner_decision(mutation,'decoy_active',(wrong,)+providers[1:])
        self.assertEqual(observed['decision'],'permit')
        self.assertEqual(self.connection.execute('SELECT active,decoy_active FROM truss.sec_assignment').fetchall(),[(False,True)])

    def bound_profile(self,providers=None):
        raw=(ROOT/'docs/helix/04-build/evidence/security-fact-requirements/requirements.json').read_bytes()
        return raw,json.dumps({'kind':'truss-flat-fact-provider-fixture/0.1','requirementsSha256':hashlib.sha256(raw).hexdigest(),'providers':[asdict(p) for p in (self.dependency_providers() if providers is None else providers)]},sort_keys=True,separators=(',',':')).encode()
    def issue_bound_profile(self,raw_profile):
        epoch=self.connection.execute("SELECT truss.runtime_issue_source_epoch('fixture',%s,'target',%s,%s)",(self.epoch,raw_profile,b'bound-fixture')).fetchone()[0]
        return epoch_tests._EpochComparison('fixture',epoch,'target',raw_profile,b'bound-fixture')
    def test_epoch_original_profile_derives_complete_native_provider_cuts(self):
        t=self.begin();raw,profile=self.bound_profile();comparison=self.issue_bound_profile(profile)
        self.assertEqual(_run_epoch_bound_dependency_fact_operation(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest(),lambda c:'original-recipe'),Ok('original-recipe'))
    def test_caller_replaced_well_typed_mapping_cannot_match_original_epoch(self):
        t=self.begin();raw,profile=self.bound_profile();comparison=self.issue_bound_profile(profile);called=[]
        self.connection.execute('ALTER TABLE truss.sec_assignment ADD COLUMN decoy_active boolean NOT NULL DEFAULT true')
        replacement=json.loads(profile);replacement['providers'][0]['column']['name']='decoy_active';replacement['providers'][0]['column']['number']=5
        bad=epoch_tests._EpochComparison(comparison.installation,comparison.epoch,comparison.incarnation,json.dumps(replacement).encode(),comparison.evidence)
        result=_run_epoch_bound_dependency_fact_operation(self.host,t,bad,raw,hashlib.sha256(raw).hexdigest(),lambda c:called.append(True))
        self.assertIsInstance(result,Error);self.assertEqual(called,[])
    def test_original_epoch_profile_missing_active_refuses_complete_cut(self):
        t=self.begin();raw,profile=self.bound_profile(self.dependency_providers()[1:]);comparison=self.issue_bound_profile(profile);called=[]
        with self.assertRaisesRegex(ValueError,'Incomplete original'):
            _run_epoch_bound_dependency_fact_operation(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest(),lambda c:called.append(True))
        self.assertEqual(called,[])
    def test_wrong_requirement_digest_cannot_select_original_provider_profile(self):
        t=self.begin();raw,profile=self.bound_profile();comparison=self.issue_bound_profile(profile);called=[]
        with self.assertRaisesRegex(ValueError,'requirement/profile'):
            _run_epoch_bound_dependency_fact_operation(self.host,t,comparison,raw,'0'*64,lambda c:called.append(True))
        self.assertEqual(called,[])

    def fixed_capture(self,t):
        raw,profile=self.bound_profile();comparison=self.issue_bound_profile(profile)
        return _capture_epoch_bound_dependency_cells(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest())
    def test_fixed_capture_reads_original_active_not_decoy_column(self):
        t=self.begin();self.connection.execute('ALTER TABLE truss.sec_assignment ADD COLUMN decoy_active boolean NOT NULL DEFAULT true; UPDATE truss.sec_assignment SET active=false')
        result=self.fixed_capture(t);self.assertIsInstance(result,Ok)
        assignment=next(r for r in result.value if r.relation[1]=='sec_assignment')
        active=next(i for i,(ref,number,oid) in enumerate(assignment.fields) if ref[-1]=='active')
        self.assertEqual(assignment.rows[0][active],'false')
        self.assertTrue(all(ref[-1]!='salary' for r in result.value for ref,_,_ in r.fields))
    def test_fixed_capture_empty_association_is_explicit_not_missing_binding(self):
        t=self.begin();self.connection.execute('DELETE FROM truss.sec_ownership')
        result=self.fixed_capture(t);self.assertIsInstance(result,Ok)
        ownership=next(r for r in result.value if r.relation[1]=='sec_ownership')
        self.assertEqual(ownership.associations,(('domain','m','Ownership'),));self.assertEqual(ownership.rows,())
    def test_fixed_capture_over_row_cap_refuses_whole_result(self):
        t=self.begin();self.connection.execute("INSERT INTO truss.sec_assignment SELECT 'a'||i::text,'s1','p1',true FROM generate_series(1,100) i")
        result=self.fixed_capture(t);self.assertIsInstance(result,Error)
    def test_fixed_capture_oversize_cell_refuses_without_partial_values(self):
        t=self.begin();self.connection.execute("UPDATE truss.sec_staff SET staff_id=repeat('x',65537)")
        result=self.fixed_capture(t);self.assertIsInstance(result,Error)

    def physical_capture_variant(self,t,column):
        providers=self.dependency_providers();index=next(i for i,p in enumerate(providers) if p.reference[-1]=='staffId');prior=providers[index]
        changed=_DependencyFactProvider(prior.kind,prior.reference,prior.relation,column)
        raw,profile=self.bound_profile(providers[:index]+(changed,)+providers[index+1:]);comparison=self.issue_bound_profile(profile)
        result=_capture_epoch_bound_dependency_cells(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest());self.assertIsInstance(result,Ok)
        return next(r for r in result.value if r.relation[1]=='sec_staff')
    def test_fixed_raw_capture_preserves_native_int8_above_javascript_safe_integer(self):
        # Physical encoding control only; this changed mapping is not qualified
        # against the original ontology's string-valued staff identity.
        t=self.begin();self.connection.execute("UPDATE truss.sec_staff SET staff_id='9007199254740993'; ALTER TABLE truss.sec_staff ALTER COLUMN staff_id TYPE bigint USING staff_id::bigint")
        cells=self.physical_capture_variant(t,_FactColumnComparison('staff_id',1,20,-1,True,0))
        self.assertEqual(cells.rows,(('9007199254740993',),));self.assertEqual(cells.fields[0][2],20)
    def test_fixed_raw_capture_preserves_native_null_without_empty_text_coercion(self):
        t=self.begin();self.connection.execute('ALTER TABLE truss.sec_staff ALTER COLUMN staff_id DROP NOT NULL; UPDATE truss.sec_staff SET staff_id=NULL')
        cells=self.physical_capture_variant(t,_FactColumnComparison('staff_id',1,25,-1,False,100))
        self.assertEqual(cells.rows,((None,),))
    def test_fixed_capture_ignores_host_custom_text_loader(self):
        from psycopg.types.string import TextLoader
        class SubstituteText(TextLoader):
            def load(self,data):return 'substituted'
        t=self.begin();raw,profile=self.bound_profile();comparison=self.issue_bound_profile(profile)
        self.connection.adapters.register_loader(25,SubstituteText)
        result=_capture_epoch_bound_dependency_cells(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest());self.assertIsInstance(result,Ok)
        cells=next(r for r in result.value if r.relation[1]=='sec_staff')
        self.assertEqual(cells.rows,(('s1',),))

    def identity_dependency_providers(self):
        return self.dependency_providers()+tuple(_DependencyFactProvider('field',('domain','m',ref),self.semantic_relations[table],_FactColumnComparison(column,1,25,-1,True,100)) for ref,table,column in [('assignmentId','sec_assignment','assignment_id'),('ownerId','sec_ownership','owner_id')])
    def identity_raw(self):return (ROOT/'docs/helix/04-build/evidence/security-identity-requirements/requirements.json').read_bytes()
    def identity_capture(self,t,providers=None):
        raw=self.identity_raw();profile=json.dumps({'kind':'truss-flat-fact-provider-fixture/0.1','requirementsSha256':hashlib.sha256(raw).hexdigest(),'providers':[asdict(p) for p in (self.identity_dependency_providers() if providers is None else providers)]},sort_keys=True,separators=(',',':')).encode()
        comparison=self.issue_bound_profile(profile)
        return _capture_epoch_bound_dependency_cells(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest())
    def reconstruct_identity_fixture(self,t,providers=None):
        captured=self.identity_capture(t,providers);self.assertIsInstance(captured,Ok)
        return subprocess.run(['/opt/homebrew/bin/bun','scripts/evaluate-security-captured-identity-fixture.ts'],cwd=ROOT,input=json.dumps([asdict(c) for c in captured.value]),capture_output=True,text=True,timeout=20)
    def identity_decision(self,mutation=None,providers=None):
        t=self.begin()
        if mutation:self.connection.execute(mutation)
        result=self.reconstruct_identity_fixture(t,providers);self.assertEqual(result.returncode,0,result.stderr);return json.loads(result.stdout)
    def test_original_identity_closure_refuses_missing_instance_key_providers(self):
        t=self.begin();called=[];raw=self.identity_raw()
        with self.assertRaisesRegex(ValueError,'Incomplete original'):
            _run_dependency_fact_operation(self.host,t,self.comparison(),raw,hashlib.sha256(raw).hexdigest(),self.dependency_providers(),lambda c:called.append(True))
        self.assertEqual(called,[]);self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))
    def test_fixed_identity_capture_reconstructs_original_keys_and_permits(self):
        result=self.identity_decision();self.assertEqual(result['decision'],{'decision':'permit','output':[{'field':{'documentId':'domain','moduleId':'m','elementId':'salary'},'disposition':'withheld'}]})
        keys={r['type']['elementId']:r['key'] for r in result['identities']}
        self.assertEqual(keys['Assignment'],[{'string':'a1'}]);self.assertEqual(keys['Ownership'],[{'string':'o1'}])
    def test_fixed_identity_capture_revoked_assignment_denies(self):
        self.assertEqual(self.identity_decision('UPDATE truss.sec_assignment SET active=false')['decision']['decision'],'deny')
    def test_fixed_identity_capture_missing_owner_denies(self):
        self.assertEqual(self.identity_decision('DELETE FROM truss.sec_ownership')['decision']['decision'],'deny')
    def test_fixed_identity_capture_reversed_provider_order_preserves_keys(self):
        result=self.identity_decision(providers=tuple(reversed(self.identity_dependency_providers())))
        self.assertEqual(result['decision']['decision'],'permit');keys={r['type']['elementId']:r['key'] for r in result['identities']}
        self.assertEqual(keys['Assignment'],[{'string':'a1'}]);self.assertEqual(keys['Ownership'],[{'string':'o1'}])
    def test_fixed_identity_capture_duplicate_instance_key_is_indeterminate(self):
        result=self.identity_decision("INSERT INTO truss.sec_assignment VALUES('a1','s1','p1',true)")
        self.assertEqual(result['decision']['decision'],'indeterminate')
    def test_fixed_identity_capture_wrong_native_literal_domain_refuses_fact_construction(self):
        t=self.begin();self.connection.execute('ALTER TABLE truss.sec_assignment ALTER COLUMN active TYPE text USING active::text')
        providers=self.identity_dependency_providers();p=providers[0];changed=_DependencyFactProvider(p.kind,p.reference,p.relation,_FactColumnComparison('active',4,25,-1,True,100))
        result=self.reconstruct_identity_fixture(t,(changed,)+providers[1:])
        self.assertNotEqual(result.returncode,0);self.assertEqual(result.stdout,'')

    def observe_native_capture_cardinality(self,omit_server_limit=False):
        from unittest.mock import patch
        from truss.psycopg_host import _GuardedCursor
        t=self.begin();self.connection.execute("INSERT INTO truss.sec_assignment SELECT 'a'||i::text,'s1','p1',true FROM generate_series(1,10000) i")
        self.assertEqual(self.connection.execute('SELECT count(*) FROM truss.sec_assignment').fetchone(),(10001,))
        original=_GuardedCursor.execute;observed=[]
        def execute(cursor,query,*args,**kwargs):
            text=query.as_string(cursor._cursor) if hasattr(query,'as_string') else str(query)
            selected=text.startswith('SELECT CASE WHEN') and 'FROM ONLY "truss"."sec_assignment"' in text
            if selected and omit_server_limit:
                self.assertTrue(text.endswith(' LIMIT 101'));query=sql.SQL(text[:-len(' LIMIT 101')])
            result=original(cursor,query,*args,**kwargs)
            if selected:observed.append(cursor.pgresult.ntuples)
            return result
        with patch.object(_GuardedCursor,'execute',execute):result=self.fixed_capture(t)
        self.assertIsInstance(result,Error);return observed
    def test_fixed_capture_server_result_is_capped_before_fetchmany(self):
        self.assertEqual(self.observe_native_capture_cardinality(),[101])
    def test_omitted_server_limit_receives_all_rows_despite_bounded_fetchmany(self):
        # Deliberately omit only the SQL limit; ordinary post-fetch refusal
        # remains intact and does not qualify this oversized native result.
        self.assertEqual(self.observe_native_capture_cardinality(True),[10001])

    def test_rls_enabled_fact_source_refuses_even_when_admin_can_see_all_rows(self):
        t=self.begin();self.connection.execute('ALTER TABLE truss.flat_assignment ENABLE ROW LEVEL SECURITY')
        self.assertEqual(self.connection.execute('SELECT count(*) FROM truss.flat_assignment').fetchone(),(1,));called=[]
        result=self.cut(t,lambda c:called.append(True),(self.bindings['flat_assignment'],))
        self.assertIsInstance(result,Error);self.assertEqual(called,[]);self.assertEqual(self.fact_shares(),0)
    def test_force_rls_flag_refuses_even_when_row_security_disabled(self):
        t=self.begin();self.connection.execute('ALTER TABLE truss.flat_assignment FORCE ROW LEVEL SECURITY');called=[]
        result=self.cut(t,lambda c:called.append(True),(self.bindings['flat_assignment'],))
        self.assertIsInstance(result,Error);self.assertEqual(called,[])
    def test_native_rls_hides_fact_rows_from_nonowner_and_refuses_cut(self):
        self.connection.execute("BEGIN; CREATE ROLE fact_visibility_reader; GRANT USAGE ON SCHEMA truss TO fact_visibility_reader; GRANT ALL ON ALL TABLES IN SCHEMA truss TO fact_visibility_reader; GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA truss TO fact_visibility_reader; ALTER TABLE truss.flat_assignment ENABLE ROW LEVEL SECURITY; CREATE POLICY hide_facts ON truss.flat_assignment FOR SELECT TO fact_visibility_reader USING(false); SET LOCAL ROLE fact_visibility_reader")
        self.assertEqual(self.connection.execute('SELECT count(*) FROM truss.flat_assignment').fetchone(),(0,))
        from unittest.mock import patch
        from truss.psycopg_host import _GuardedCursor
        original=_GuardedCursor.execute;metadata=[]
        def observe(cursor,query,*args,**kwargs):
            text=query.as_string(cursor._cursor) if hasattr(query,'as_string') else str(query)
            result=original(cursor,query,*args,**kwargs)
            if text.startswith('SELECT c.oid::pg_catalog.text') and 'c.relrowsecurity' in text:
                metadata.append(tuple(cursor.pgresult.get_value(0,i) for i in range(7)))
            return result
        t=self.begin();called=[]
        with patch.object(_GuardedCursor,'execute',observe):result=self.cut(t,lambda c:called.append(True),(self.bindings['flat_assignment'],))
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,None);self.assertEqual(called,[])
        self.assertEqual(len(metadata),1);self.assertEqual(metadata[0][4:6],(b'true',b'false'))

    def test_competing_visibility_ddl_blocks_until_cut_release_then_fresh_cut_refuses(self):
        t=self.begin()
        self.assertEqual(self.cut(t,lambda c:'retained'),Ok('retained'))
        self.assertEqual(self.fact_shares(),2)
        with psycopg.connect(host=str(self.socket),user='postgres',dbname='postgres',autocommit=True,options='-c lock_timeout=150ms -c statement_timeout=1500') as writer:
            for clause in ('ENABLE ROW LEVEL SECURITY','FORCE ROW LEVEL SECURITY'):
                with self.assertRaises(psycopg.errors.LockNotAvailable):
                    writer.execute('ALTER TABLE truss.flat_assignment '+clause)
            self.assertEqual(writer.execute("SELECT relrowsecurity,relforcerowsecurity FROM pg_catalog.pg_class WHERE oid='truss.flat_assignment'::regclass").fetchone(),(False,False))
            self.connection.execute('ROLLBACK')
            try:
                writer.execute('ALTER TABLE truss.flat_assignment ENABLE ROW LEVEL SECURITY')
                self.assertEqual(writer.execute("SELECT relrowsecurity FROM pg_catalog.pg_class WHERE oid='truss.flat_assignment'::regclass").fetchone(),(True,))
                fresh=self.begin();called=[]
                result=self.cut(fresh,lambda c:called.append(True))
                self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state)
                self.assertEqual(called,[]);self.assertEqual(self.fact_shares(),0)
            finally:
                self.connection.execute('ROLLBACK')
                writer.execute('ALTER TABLE truss.flat_assignment DISABLE ROW LEVEL SECURITY')

    def test_same_backend_visibility_ddl_is_a_counterexample_to_lock_only_lifetime(self):
        t=self.begin()
        def bypass(cursor):
            cursor.execute('ALTER TABLE truss.flat_assignment ENABLE ROW LEVEL SECURITY')
            cursor.execute("SELECT relrowsecurity::pg_catalog.text FROM pg_catalog.pg_class WHERE oid='truss.flat_assignment'::regclass")
            return cursor.fetchone()[0]
        # Actual native SHARE is retained, but its owner can upgrade its own
        # table lock. No arbitrary-callback safety or full lifetime claim.
        self.assertEqual(self.cut(t,bypass),Ok('true'))
        self.assertEqual(self.fact_shares(),2)
        called=[];result=self.cut(t,lambda c:called.append(True))
        self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state)
        self.assertEqual(called,[])

    def test_table_ddl_participation_refuses_same_backend_visibility_change(self):
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            t=self.begin()
            result=self.cut(t,lambda c:c.execute('ALTER TABLE truss.flat_assignment ENABLE ROW LEVEL SECURITY'))
            self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000')
            self.assertEqual(self.fact_shares(),0)
            self.assertEqual(self.connection.execute("SELECT relrowsecurity FROM pg_catalog.pg_class WHERE oid='truss.flat_assignment'::regclass").fetchone(),(False,))
        finally:
            self.connection.execute('ROLLBACK')
            self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')

    def test_pending_table_ddl_participant_refuses_epoch_read_until_abort(self):
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            t=self.begin();called=[]
            with psycopg.connect(host=str(self.socket),user='postgres',dbname='postgres') as writer:
                writer.execute('ALTER TABLE truss.flat_assignment ENABLE ROW LEVEL SECURITY')
                self.assertEqual(writer.execute("SELECT relrowsecurity FROM pg_catalog.pg_class WHERE oid='truss.flat_assignment'::regclass").fetchone(),(True,))
                result=self.cut(t,lambda c:called.append(True))
                self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55P03')
                self.assertEqual(called,[]);self.assertEqual(self.fact_shares(),0)
                writer.rollback()
            self.assertEqual(self.cut(t,lambda c:'fresh-after-abort'),Ok('fresh-after-abort'))
        finally:
            self.connection.execute('ROLLBACK')
            self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')

    def ddl_comparison(self):
        from truss._psycopg_epoch_cut import _DDLBarrierComparison
        oid,owner,source=self.connection.execute("SELECT oid,proowner,prosrc FROM pg_catalog.pg_proc WHERE oid='truss.runtime_fence_routine_ddl_writer()'::regprocedure").fetchone()
        return _DDLBarrierComparison(owner,oid,source)
    def test_original_installed_ddl_barriers_readback_passes(self):
        from truss._psycopg_epoch_cut import _run_ddl_fenced_epoch_operation
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            original=self.ddl_comparison();t=self.begin()
            self.assertEqual(_run_ddl_fenced_epoch_operation(self.host,t,self.comparison(),original,lambda c:'qualified-fixture'),Ok('qualified-fixture'))
            self.assertEqual(self.cut(t,lambda c:'joint-qualified-fixture',ddl_barrier=original),Ok('joint-qualified-fixture'))
            self.assertEqual(self.fact_shares(),2)
        finally:
            self.connection.execute('ROLLBACK');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')
    def test_missing_installed_table_barrier_refuses_before_callback(self):
        from truss._psycopg_epoch_cut import _run_ddl_fenced_epoch_operation
        original=self.ddl_comparison();t=self.begin();called=[]
        result=_run_ddl_fenced_epoch_operation(self.host,t,self.comparison(),original,lambda c:called.append(True))
        self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[]);self.assertEqual(self.fact_shares(),0)
    def test_disabled_installed_table_barrier_refuses_before_callback(self):
        from truss._psycopg_epoch_cut import _run_ddl_fenced_epoch_operation
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            original=self.ddl_comparison();self.connection.execute('ALTER EVENT TRIGGER truss_table_ddl_writer_barrier DISABLE');t=self.begin();called=[]
            result=_run_ddl_fenced_epoch_operation(self.host,t,self.comparison(),original,lambda c:called.append(True))
            self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        finally:
            self.connection.execute('ROLLBACK');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')

    def test_incomplete_native_table_barrier_tag_set_refuses(self):
        from truss._psycopg_epoch_cut import _run_ddl_fenced_epoch_operation
        self.connection.execute("CREATE EVENT TRIGGER truss_table_ddl_writer_barrier ON ddl_command_start WHEN TAG IN ('ALTER TABLE') EXECUTE FUNCTION truss.runtime_fence_routine_ddl_writer(); ALTER EVENT TRIGGER truss_table_ddl_writer_barrier ENABLE ALWAYS")
        try:
            original=self.ddl_comparison();t=self.begin();called=[]
            result=_run_ddl_fenced_epoch_operation(self.host,t,self.comparison(),original,lambda c:called.append(True))
            self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        finally:
            self.connection.execute('ROLLBACK');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')
    def test_wrong_original_barrier_owner_function_or_body_refuses(self):
        from truss._psycopg_epoch_cut import _run_ddl_fenced_epoch_operation,_DDLBarrierComparison
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            original=self.ddl_comparison();t=self.begin()
            for wrong in (_DDLBarrierComparison(original.owner_oid+1,original.function_oid,original.source),_DDLBarrierComparison(original.owner_oid,original.function_oid+1,original.source),_DDLBarrierComparison(original.owner_oid,original.function_oid,original.source+' ')):
                with self.subTest(comparison=wrong):
                    called=[];result=_run_ddl_fenced_epoch_operation(self.host,t,self.comparison(),wrong,lambda c:called.append(True))
                    self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        finally:
            self.connection.execute('ROLLBACK');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')
    def test_disabled_routine_barrier_refuses_even_with_table_barrier_always(self):
        from truss._psycopg_epoch_cut import _run_ddl_fenced_epoch_operation
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            original=self.ddl_comparison();self.connection.execute('ALTER EVENT TRIGGER truss_routine_ddl_writer_barrier DISABLE');t=self.begin();called=[]
            result=_run_ddl_fenced_epoch_operation(self.host,t,self.comparison(),original,lambda c:called.append(True))
            self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        finally:
            self.connection.execute('ROLLBACK');self.connection.execute('ALTER EVENT TRIGGER truss_routine_ddl_writer_barrier ENABLE ALWAYS');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')

    def test_joint_ddl_fact_cut_missing_barrier_refuses_before_fact_read(self):
        original=self.ddl_comparison();t=self.begin();called=[]
        result=self.cut(t,lambda c:called.append(True),ddl_barrier=original)
        self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state)
        self.assertEqual(called,[]);self.assertEqual(self.fact_shares(),0)

    def with_unprivileged_actor(self, operation, grant_owner=False, attribute=None):
        from truss.psycopg_host import PsycopgHost,PsycopgProfile
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        original=self.ddl_comparison()
        self.connection.execute('CREATE ROLE fact_cut_actor LOGIN')
        try:
            self.connection.execute('GRANT USAGE ON SCHEMA truss TO fact_cut_actor; GRANT ALL ON ALL TABLES IN SCHEMA truss TO fact_cut_actor; GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA truss TO fact_cut_actor')
            # Exact owned-layout administrative high-water routines are not
            # part of this invoker-only actor fixture. PUBLIC is already revoked.
            self.connection.execute('REVOKE ALL ON FUNCTION truss.catalog_global_high_water_v01(),truss.catalog_key_high_water_v01(integer) FROM fact_cut_actor')
            if grant_owner:self.connection.execute('GRANT postgres TO fact_cut_actor')
            if attribute:self.connection.execute('ALTER ROLE fact_cut_actor '+attribute)
            with psycopg.connect(host=str(self.socket),user='fact_cut_actor',dbname='postgres',autocommit=True,options='-c statement_timeout=3s') as connection:
                host=PsycopgHost(connection,profile=PsycopgProfile())
                try:
                    connection.execute('BEGIN');adopted=host.adopt_transaction();self.assertIsInstance(adopted,Ok)
                    operation(host,adopted.value,original,connection)
                    connection.execute('ROLLBACK')
                finally:host.detach()
        finally:
            self.connection.execute('DROP OWNED BY fact_cut_actor; DROP ROLE fact_cut_actor; DROP EVENT TRIGGER truss_table_ddl_writer_barrier')
    def test_selected_unprivileged_role_passes_and_cannot_disable_native_barrier(self):
        from truss._psycopg_epoch_cut import _run_unprivileged_ddl_fenced_epoch_operation
        def operation(host,t,original,connection):
            self.assertEqual(_run_unprivileged_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:'excluded-administration'),Ok('excluded-administration'))
            connection.execute('SAVEPOINT denied_admin')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.execute('ALTER EVENT TRIGGER truss_table_ddl_writer_barrier DISABLE')
            connection.execute('ROLLBACK TO denied_admin')
            self.assertEqual(connection.execute("SELECT evtenabled FROM pg_catalog.pg_event_trigger WHERE evtname='truss_table_ddl_writer_barrier'").fetchone(),('A',))
        self.with_unprivileged_actor(operation)
    def test_selected_superuser_role_refuses_before_callback(self):
        from truss._psycopg_epoch_cut import _run_unprivileged_ddl_fenced_epoch_operation
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            original=self.ddl_comparison();t=self.begin();called=[]
            result=_run_unprivileged_ddl_fenced_epoch_operation(self.host,t,self.comparison(),original,lambda c:called.append(True))
            self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        finally:
            self.connection.execute('ROLLBACK');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')
    def test_selected_owner_membership_refuses_before_callback(self):
        from truss._psycopg_epoch_cut import _run_unprivileged_ddl_fenced_epoch_operation
        def operation(host,t,original,connection):
            called=[];result=_run_unprivileged_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:called.append(True))
            self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        self.with_unprivileged_actor(operation,grant_owner=True)
    def test_selected_createrole_and_bypassrls_refuse_before_callback(self):
        from truss._psycopg_epoch_cut import _run_unprivileged_ddl_fenced_epoch_operation
        def operation(host,t,original,connection):
            called=[];result=_run_unprivileged_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:called.append(True))
            self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        for attribute in ('CREATEROLE','BYPASSRLS'):
            with self.subTest(attribute=attribute):self.with_unprivileged_actor(operation,attribute=attribute)

    def test_no_reachable_definer_profile_passes_original_invoker_fixture(self):
        from truss._psycopg_epoch_cut import _run_no_definer_ddl_fenced_epoch_operation
        def operation(host,t,original,connection):
            self.assertEqual(_run_no_definer_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:'invoker-only'),Ok('invoker-only'))
        self.with_unprivileged_actor(operation)
    def test_native_definer_can_disable_barrier_and_stronger_profile_refuses(self):
        from truss._psycopg_epoch_cut import _run_unprivileged_ddl_fenced_epoch_operation,_run_no_definer_ddl_fenced_epoch_operation
        self.connection.execute("CREATE FUNCTION truss.fixture_disable_barrier() RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN ALTER EVENT TRIGGER truss_table_ddl_writer_barrier DISABLE; END $$")
        try:
            def operation(host,t,original,connection):
                self.assertEqual(connection.execute("SELECT pg_catalog.has_function_privilege(current_user,'truss.fixture_disable_barrier()','EXECUTE'),pg_catalog.has_function_privilege(current_user,'truss.catalog_global_high_water_v01()','EXECUTE'),pg_catalog.has_function_privilege(current_user,'truss.catalog_key_high_water_v01(integer)','EXECUTE')").fetchone(),(True,False,False))
                called=[];result=_run_no_definer_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:called.append(True))
                self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
                # Actual nonowner role passes the weaker snapshot, then uses a
                # reachable original SECURITY DEFINER routine to administer it.
                def bypass(c):
                    c.execute('SELECT truss.fixture_disable_barrier()')
                    c.execute("SELECT evtenabled::pg_catalog.text FROM pg_catalog.pg_event_trigger WHERE evtname='truss_table_ddl_writer_barrier'")
                    return c.fetchone()[0]
                self.assertEqual(_run_unprivileged_ddl_fenced_epoch_operation(host,t,self.comparison(),original,bypass),Ok('D'))
            self.with_unprivileged_actor(operation)
        finally:self.connection.execute('DROP FUNCTION truss.fixture_disable_barrier()')
    def test_revoked_definer_execute_removes_native_reachability(self):
        from truss._psycopg_epoch_cut import _run_no_definer_ddl_fenced_epoch_operation
        self.connection.execute("CREATE FUNCTION truss.fixture_private_definer() RETURNS integer LANGUAGE sql SECURITY DEFINER AS $$ SELECT 1 $$; REVOKE ALL ON FUNCTION truss.fixture_private_definer() FROM PUBLIC")
        try:
            def operation(host,t,original,connection):
                self.connection.execute('REVOKE ALL ON FUNCTION truss.fixture_private_definer() FROM fact_cut_actor')
                self.assertEqual(connection.execute("SELECT pg_catalog.has_function_privilege(current_user,'truss.fixture_private_definer()','EXECUTE')").fetchone(),(False,))
                self.assertEqual(_run_no_definer_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:'not-reachable'),Ok('not-reachable'))
            self.with_unprivileged_actor(operation)
        finally:self.connection.execute('DROP FUNCTION truss.fixture_private_definer()')

    def test_set_reachable_createrole_without_inheritance_refuses_stronger_cut(self):
        from truss._psycopg_epoch_cut import _run_no_definer_ddl_fenced_epoch_operation,_run_set_role_excluded_ddl_fenced_epoch_operation
        self.connection.execute('CREATE ROLE fact_assumable CREATEROLE')
        try:
            def operation(host,t,original,connection):
                self.connection.execute('GRANT fact_assumable TO fact_cut_actor WITH INHERIT FALSE, SET TRUE')
                self.assertEqual(connection.execute("SELECT pg_catalog.pg_has_role(current_user,'fact_assumable','USAGE'),pg_catalog.pg_has_role(current_user,'fact_assumable','SET')").fetchone(),(False,True))
                self.assertEqual(_run_no_definer_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:'weak-snapshot'),Ok('weak-snapshot'))
                called=[];result=_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:called.append(True))
                self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
                connection.execute('SET LOCAL ROLE fact_assumable')
                self.assertEqual(connection.execute("SELECT rolcreaterole FROM pg_catalog.pg_roles WHERE rolname=current_user").fetchone(),(True,))
            self.with_unprivileged_actor(operation)
        finally:self.connection.execute('DROP ROLE fact_assumable')
    def test_set_reachable_definer_without_direct_execute_refuses_stronger_cut(self):
        from truss._psycopg_epoch_cut import _run_no_definer_ddl_fenced_epoch_operation,_run_set_role_excluded_ddl_fenced_epoch_operation
        self.connection.execute("CREATE ROLE fact_assumable; CREATE FUNCTION truss.fixture_assumed_definer() RETURNS integer LANGUAGE sql SECURITY DEFINER AS $$ SELECT 77 $$; REVOKE ALL ON FUNCTION truss.fixture_assumed_definer() FROM PUBLIC; GRANT USAGE ON SCHEMA truss TO fact_assumable; GRANT EXECUTE ON FUNCTION truss.fixture_assumed_definer() TO fact_assumable")
        try:
            def operation(host,t,original,connection):
                self.connection.execute('REVOKE ALL ON FUNCTION truss.fixture_assumed_definer() FROM fact_cut_actor; GRANT fact_assumable TO fact_cut_actor WITH INHERIT FALSE, SET TRUE')
                self.assertEqual(connection.execute("SELECT pg_catalog.has_function_privilege(current_user,'truss.fixture_assumed_definer()','EXECUTE'),pg_catalog.pg_has_role(current_user,'fact_assumable','SET')").fetchone(),(False,True))
                self.assertEqual(_run_no_definer_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:'weak-snapshot'),Ok('weak-snapshot'))
                called=[];result=_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:called.append(True))
                self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
                connection.execute('SET LOCAL ROLE fact_assumable')
                self.assertEqual(connection.execute('SELECT truss.fixture_assumed_definer()').fetchone(),(77,))
            self.with_unprivileged_actor(operation)
        finally:self.connection.execute('DROP FUNCTION truss.fixture_assumed_definer(); DROP OWNED BY fact_assumable; DROP ROLE fact_assumable')
    def test_set_reachable_profile_passes_original_invoker_actor(self):
        from truss._psycopg_epoch_cut import _run_set_role_excluded_ddl_fenced_epoch_operation
        def operation(host,t,original,connection):
            self.assertEqual(_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:'set-role-excluded'),Ok('set-role-excluded'))
        self.with_unprivileged_actor(operation)

    def test_transitive_set_role_chain_reaches_privileged_role(self):
        from truss._psycopg_epoch_cut import _run_set_role_excluded_ddl_fenced_epoch_operation
        self.connection.execute('CREATE ROLE fact_assumable; CREATE ROLE fact_inner CREATEROLE; GRANT fact_inner TO fact_assumable WITH INHERIT FALSE, SET TRUE')
        try:
            def operation(host,t,original,connection):
                self.connection.execute('GRANT fact_assumable TO fact_cut_actor WITH INHERIT FALSE, SET TRUE')
                self.assertEqual(connection.execute("SELECT pg_catalog.pg_has_role(current_user,'fact_inner','USAGE'),pg_catalog.pg_has_role(current_user,'fact_inner','SET')").fetchone(),(False,True))
                called=[];result=_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:called.append(True))
                self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
                connection.execute('SET LOCAL ROLE fact_inner; CREATE ROLE fact_assumed_created')
                self.assertEqual(connection.execute("SELECT count(*) FROM pg_catalog.pg_roles WHERE rolname='fact_assumed_created'").fetchone(),(1,))
            self.with_unprivileged_actor(operation)
            self.assertEqual(self.connection.execute("SELECT count(*) FROM pg_catalog.pg_roles WHERE rolname='fact_assumed_created'").fetchone(),(0,))
        finally:self.connection.execute('DROP ROLE fact_assumable; DROP ROLE fact_inner')
    def test_noninherited_membership_without_set_permission_does_not_refuse(self):
        from truss._psycopg_epoch_cut import _run_set_role_excluded_ddl_fenced_epoch_operation
        self.connection.execute('CREATE ROLE fact_assumable CREATEROLE')
        try:
            def operation(host,t,original,connection):
                self.connection.execute('GRANT fact_assumable TO fact_cut_actor WITH INHERIT FALSE, SET FALSE')
                self.assertEqual(connection.execute("SELECT pg_catalog.pg_has_role(current_user,'fact_assumable','MEMBER'),pg_catalog.pg_has_role(current_user,'fact_assumable','USAGE'),pg_catalog.pg_has_role(current_user,'fact_assumable','SET')").fetchone(),(True,False,False))
                self.assertEqual(_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:'no-set-path'),Ok('no-set-path'))
                connection.execute('SAVEPOINT no_set_permission')
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.execute('SET LOCAL ROLE fact_assumable')
                connection.execute('ROLLBACK TO no_set_permission')
            self.with_unprivileged_actor(operation)
        finally:self.connection.execute('DROP ROLE fact_assumable')

    def test_uncoordinated_shared_role_change_invalidates_retained_snapshot(self):
        from truss._psycopg_epoch_cut import _run_set_role_excluded_ddl_fenced_epoch_operation
        def operation(host,t,original,connection):
            def change(c):
                self.connection.execute('ALTER ROLE fact_cut_actor CREATEROLE')
                c.execute("SELECT rolcreaterole::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname=current_user")
                return c.fetchone()[0]
            self.assertEqual(_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,change),Ok('true'))
        self.with_unprivileged_actor(operation)
    def test_participating_shared_role_writer_refuses_until_reader_release(self):
        from truss._psycopg_epoch_cut import _run_set_role_excluded_ddl_fenced_epoch_operation
        def operation(host,t,original,connection):
            def read(c):
                with self.assertRaises(psycopg.errors.LockNotAvailable):self.connection.execute('SELECT truss.runtime_fence_shared_authority_writer()')
                self.assertEqual(self.connection.execute("SELECT rolcreaterole FROM pg_catalog.pg_roles WHERE rolname='fact_cut_actor'").fetchone(),(False,))
                return 'writer-refused'
            self.assertEqual(_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,read),Ok('writer-refused'))
            connection.execute('ROLLBACK')
            try:
                self.connection.execute('BEGIN; SELECT truss.runtime_fence_shared_authority_writer(); ALTER ROLE fact_cut_actor CREATEROLE')
                self.assertEqual(self.connection.execute("SELECT rolcreaterole FROM pg_catalog.pg_roles WHERE rolname='fact_cut_actor'").fetchone(),(True,))
            finally:self.connection.execute('ROLLBACK')
            self.assertEqual(self.connection.execute("SELECT rolcreaterole FROM pg_catalog.pg_roles WHERE rolname='fact_cut_actor'").fetchone(),(False,))
        self.with_unprivileged_actor(operation)
    def test_pending_shared_role_participant_excludes_reader_until_abort(self):
        from truss._psycopg_epoch_cut import _run_set_role_excluded_ddl_fenced_epoch_operation
        def operation(host,t,original,connection):
            try:
                self.connection.execute('BEGIN; SELECT truss.runtime_fence_shared_authority_writer(); ALTER ROLE fact_cut_actor CREATEROLE')
                self.assertEqual(self.connection.execute("SELECT rolcreaterole FROM pg_catalog.pg_roles WHERE rolname='fact_cut_actor'").fetchone(),(True,))
                called=[];result=_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:called.append(True))
                self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55P03');self.assertEqual(called,[])
            finally:self.connection.execute('ROLLBACK')
            self.assertEqual(_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:'fresh-after-abort'),Ok('fresh-after-abort'))
        self.with_unprivileged_actor(operation)
    def test_shared_authority_writer_refuses_same_backend_retained_reader(self):
        t=self.begin();result=self.cut(t,lambda c:c.execute('SELECT truss.runtime_fence_shared_authority_writer()'))
        self.assertIsInstance(result,Error);self.assertEqual(result.error.sql_state,'55000');self.assertEqual(self.fact_shares(),0)

    def test_authority_change_commit_invalidates_old_epoch_and_preserves_incarnation(self):
        from truss._psycopg_epoch_cut import _run_set_role_excluded_ddl_fenced_epoch_operation,_EpochComparison
        issued=[]
        try:
            def operation(host,t,original,connection):
                predecessor=self.epoch
                try:
                    self.connection.execute('BEGIN; SELECT truss.runtime_fence_shared_authority_writer(); ALTER ROLE fact_cut_actor NOINHERIT')
                    successor=self.connection.execute("SELECT truss.runtime_issue_authority_epoch('fixture',%s,'target',%s,%s)",(predecessor,b'\x03',b'\x04')).fetchone()[0]
                    self.connection.execute('COMMIT');issued.append(successor)
                except BaseException:
                    self.connection.execute('ROLLBACK');raise
                self.assertEqual(connection.execute("SELECT rolinherit FROM pg_catalog.pg_roles WHERE rolname=current_user").fetchone(),(False,))
                called=[];old=_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:called.append(True))
                self.assertIsInstance(old,Error);self.assertEqual(old.error.sql_state,'55000');self.assertEqual(called,[])
                selected=_EpochComparison('fixture',successor,'target',b'\x03',b'\x04')
                self.assertEqual(_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,selected,original,lambda c:'new-authority-epoch'),Ok('new-authority-epoch'))
                self.assertEqual(self.connection.execute('SELECT predecessor_epoch,transition_reason,target_incarnation FROM truss.source_epoch_registry WHERE source_epoch=%s',(successor,)).fetchone(),(predecessor,'authority-change','target'))
            self.with_unprivileged_actor(operation)
        finally:
            self.connection.execute('ROLLBACK')
            if issued:
                type(self).epoch=self.connection.execute("SELECT truss.runtime_issue_source_epoch('fixture',%s,'target',%s,%s)",(issued[-1],b'\x01',b'\x02')).fetchone()[0]
    def test_authority_change_abort_restores_role_pointer_and_registry(self):
        from truss._psycopg_epoch_cut import _run_set_role_excluded_ddl_fenced_epoch_operation
        def operation(host,t,original,connection):
            predecessor=self.epoch
            try:
                self.connection.execute('BEGIN; SELECT truss.runtime_fence_shared_authority_writer(); ALTER ROLE fact_cut_actor NOINHERIT')
                successor=self.connection.execute("SELECT truss.runtime_issue_authority_epoch('fixture',%s,'target',%s,%s)",(predecessor,b'\x03',b'\x04')).fetchone()[0]
                self.assertEqual(self.connection.execute('SELECT source_epoch FROM truss.source_epoch_current').fetchone(),(successor,))
            finally:self.connection.execute('ROLLBACK')
            self.assertEqual(connection.execute("SELECT rolinherit FROM pg_catalog.pg_roles WHERE rolname=current_user").fetchone(),(True,))
            self.assertEqual(connection.execute('SELECT source_epoch FROM truss.source_epoch_current').fetchone(),(predecessor,))
            self.assertEqual(connection.execute('SELECT count(*) FROM truss.source_epoch_registry WHERE source_epoch=%s',(successor,)).fetchone(),(0,))
            self.assertEqual(_run_set_role_excluded_ddl_fenced_epoch_operation(host,t,self.comparison(),original,lambda c:'original-after-abort'),Ok('original-after-abort'))
        self.with_unprivileged_actor(operation)
    def test_authority_change_cannot_silently_restore_different_incarnation(self):
        def operation(host,t,original,connection):
            try:
                self.connection.execute('BEGIN; SELECT truss.runtime_fence_shared_authority_writer(); ALTER ROLE fact_cut_actor NOINHERIT')
                with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):self.connection.execute("SELECT truss.runtime_issue_authority_epoch('fixture',%s,'different-target',%s,%s)",(self.epoch,b'\x03',b'\x04'))
            finally:self.connection.execute('ROLLBACK')
            self.assertEqual(connection.execute("SELECT rolinherit FROM pg_catalog.pg_roles WHERE rolname=current_user").fetchone(),(True,))
            self.assertEqual(connection.execute('SELECT source_epoch FROM truss.source_epoch_current').fetchone(),(self.epoch,))
        self.with_unprivileged_actor(operation)

    def test_authority_change_missing_or_stale_predecessor_has_no_committed_effect(self):
        def operation(host,t,original,connection):
            before=connection.execute('SELECT count(*) FROM truss.source_epoch_registry').fetchone()
            for predecessor in (None,'wrong-predecessor'):
                with self.subTest(predecessor=predecessor):
                    try:
                        self.connection.execute('BEGIN; SELECT truss.runtime_fence_shared_authority_writer(); ALTER ROLE fact_cut_actor NOINHERIT')
                        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):self.connection.execute("SELECT truss.runtime_issue_authority_epoch('fixture',%s,'target',%s,%s)",(predecessor,b'\x03',b'\x04'))
                    finally:self.connection.execute('ROLLBACK')
                    self.assertEqual(connection.execute("SELECT rolinherit FROM pg_catalog.pg_roles WHERE rolname=current_user").fetchone(),(True,))
                    self.assertEqual(connection.execute('SELECT source_epoch FROM truss.source_epoch_current').fetchone(),(self.epoch,))
                    self.assertEqual(connection.execute('SELECT count(*) FROM truss.source_epoch_registry').fetchone(),before)
        self.with_unprivileged_actor(operation)

    def issuer_comparison(self):
        from truss._psycopg_epoch_cut import _AuthorityIssuerComparison
        rows=self.connection.execute("SELECT proname,oid,proowner,prosrc FROM pg_catalog.pg_proc WHERE oid IN ('truss.runtime_fence_shared_authority_writer()'::regprocedure,'truss.runtime_issue_authority_epoch(text,text,text,bytea,bytea)'::regprocedure) ORDER BY proname").fetchall()
        return _AuthorityIssuerComparison(rows[0][2],rows[0][1],rows[0][3],rows[1][1],rows[1][3])
    def test_original_authority_issuer_installed_correspondence_passes(self):
        from truss._psycopg_epoch_cut import _run_issuer_verified_epoch_operation
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            original=self.issuer_comparison();barrier=self.ddl_comparison();t=self.begin()
            self.assertEqual(_run_issuer_verified_epoch_operation(self.host,t,self.comparison(),barrier,original,lambda c:'original-issuer-source'),Ok('original-issuer-source'))
        finally:self.connection.execute('ROLLBACK');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')
    def test_public_execute_drift_on_authority_issuer_refuses(self):
        from truss._psycopg_epoch_cut import _run_issuer_verified_epoch_operation
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            original=self.issuer_comparison();barrier=self.ddl_comparison();t=self.begin()
            self.connection.execute('GRANT EXECUTE ON FUNCTION truss.runtime_issue_authority_epoch(text,text,text,bytea,bytea) TO PUBLIC')
            called=[];result=_run_issuer_verified_epoch_operation(self.host,t,self.comparison(),barrier,original,lambda c:called.append(True))
            self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        finally:self.connection.execute('ROLLBACK');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')
    def test_definer_drift_on_authority_issuer_refuses(self):
        from truss._psycopg_epoch_cut import _run_issuer_verified_epoch_operation
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            original=self.issuer_comparison();barrier=self.ddl_comparison();t=self.begin()
            self.connection.execute('ALTER FUNCTION truss.runtime_issue_authority_epoch(text,text,text,bytea,bytea) SECURITY DEFINER')
            called=[];result=_run_issuer_verified_epoch_operation(self.host,t,self.comparison(),barrier,original,lambda c:called.append(True))
            self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        finally:self.connection.execute('ROLLBACK');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')

    def test_strict_issuer_skips_null_validation_but_source_admission_refuses(self):
        from truss._psycopg_epoch_cut import _run_issuer_verified_epoch_operation
        self.connection.execute((ROOT/'packages/postgresql/native/source-epoch-table-ddl-barrier.sql').read_text())
        try:
            original=self.issuer_comparison();barrier=self.ddl_comparison();t=self.begin()
            self.connection.execute('ALTER FUNCTION truss.runtime_issue_authority_epoch(text,text,text,bytea,bytea) STRICT')
            self.assertEqual(self.connection.execute("SELECT truss.runtime_issue_authority_epoch('fixture',NULL,'target',%s,%s)",(b'\x03',b'\x04')).fetchone(),(None,))
            called=[];result=_run_issuer_verified_epoch_operation(self.host,t,self.comparison(),barrier,original,lambda c:called.append(True))
            self.assertIsInstance(result,Error);self.assertIsNone(result.error.sql_state);self.assertEqual(called,[])
        finally:self.connection.execute('ROLLBACK');self.connection.execute('DROP EVENT TRIGGER truss_table_ddl_writer_barrier')

    def source_bound_profile(self):
        from truss._psycopg_dependency_fact_cut import _OriginalFactSources
        base=ROOT/'docs/helix/04-build/evidence/security-identity-requirements'
        sources=_OriginalFactSources((base/'policy.json').read_bytes(),(base/'resolution.json').read_bytes())
        raw=self.identity_raw()
        profile=json.dumps({'kind':'truss-flat-fact-provider-fixture/0.2','requirementsSha256':hashlib.sha256(raw).hexdigest(),'policyUtf8':sources.policy.decode('utf8'),'resolutionUtf8':sources.resolution.decode('utf8'),'providers':[asdict(p) for p in self.identity_dependency_providers()]},sort_keys=True,separators=(',',':')).encode()
        return raw,profile,sources
    def test_source_bound_native_profile_captures_original_identity_cells(self):
        t=self.begin();raw,profile,sources=self.source_bound_profile();comparison=self.issue_bound_profile(profile)
        result=_capture_epoch_bound_dependency_cells(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest(),sources=sources)
        self.assertIsInstance(result,Ok);self.assertEqual(len(result.value),5)
    def test_source_bound_profile_requires_original_source_bundle(self):
        t=self.begin();raw,profile,sources=self.source_bound_profile()
        comparison=epoch_tests._EpochComparison('fixture',self.epoch,'target',profile,b'fixture')
        with self.assertRaisesRegex(ValueError,'Original policy/resolution'):_capture_epoch_bound_dependency_cells(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest())
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))
    def test_source_bound_profile_refuses_changed_policy_or_resolution_bytes(self):
        from truss._psycopg_dependency_fact_cut import _OriginalFactSources
        t=self.begin();raw,profile,sources=self.source_bound_profile()
        comparison=epoch_tests._EpochComparison('fixture',self.epoch,'target',profile,b'fixture')
        for wrong in (_OriginalFactSources(sources.policy+b' ',sources.resolution),_OriginalFactSources(sources.policy,sources.resolution+b' ')):
            with self.subTest(source=wrong):
                with self.assertRaisesRegex(ValueError,'requirement/source'):_capture_epoch_bound_dependency_cells(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest(),sources=wrong)
        self.assertEqual(self.connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone(),(None,))
    def test_replacing_all_source_bound_caller_copies_cannot_match_native_generation(self):
        from truss._psycopg_dependency_fact_cut import _OriginalFactSources
        t=self.begin();raw,profile,sources=self.source_bound_profile();comparison=self.issue_bound_profile(profile)
        wrong_sources=_OriginalFactSources(sources.policy+b' ',sources.resolution)
        wrong_raw=json.loads(raw);wrong_raw['policySha256']=hashlib.sha256(wrong_sources.policy).hexdigest();wrong_raw=json.dumps(wrong_raw).encode();wrong_digest=hashlib.sha256(wrong_raw).hexdigest()
        replacement=json.loads(profile);replacement['policyUtf8']=wrong_sources.policy.decode();replacement['requirementsSha256']=wrong_digest
        wrong=epoch_tests._EpochComparison(comparison.installation,comparison.epoch,comparison.incarnation,json.dumps(replacement).encode(),comparison.evidence)
        result=_capture_epoch_bound_dependency_cells(self.host,t,wrong,wrong_raw,wrong_digest,sources=wrong_sources)
        self.assertIsInstance(result,Error);self.assertEqual(self.fact_shares(),0)

    def test_source_bundle_snapshot_ignores_later_caller_carrier_mutation(self):
        import truss._psycopg_dependency_fact_cut as producer
        from unittest.mock import patch
        t=self.begin();raw,profile,sources=self.source_bound_profile();comparison=self.issue_bound_profile(profile)
        validate=producer._inspect_original_fact_sources
        def mutate(*args):
            validate(*args)
            object.__setattr__(sources,'policy',sources.policy+b' ')
        with patch.object(producer,'_inspect_original_fact_sources',mutate):
            result=_capture_epoch_bound_dependency_cells(self.host,t,comparison,raw,hashlib.sha256(raw).hexdigest(),sources=sources)
        self.assertIsInstance(result,Ok);self.assertTrue(sources.policy.endswith(b' '))
