"""Published-scope edge writer closure and populated native68 upgrade."""
import os,pickle,subprocess,sys,tempfile,unittest
from pathlib import Path
import psycopg
from truss import (LocalPostgres,Ok,EdgeFound,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration)
from truss.catalog_runtime import _release,_PARTIAL_GROUP_FUNCTIONS
from truss.contracts import MapValue
from truss.groups import (UpdateEdge,TextOrderKey,StoredObjectReference,RequestNone,GroupSuccess,CommittedReceiptReplay)
import test_edge_mutations_native as edge_tests

class EdgeWriterHotfixTests(edge_tests.EdgeMutationTests):
    for _name in tuple(n for n in dir(edge_tests.EdgeMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_writer_revocation_after_attempt_flush_aborts(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        result,_,_=self.run_group(assembly,tx,(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b)),),'pending-edge')
        self.assertIsInstance(result,GroupSuccess)
        connection.execute('SET CONSTRAINTS truss.runtime_object_attempt_commit IMMEDIATE')
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        self.admin.execute('REVOKE group_writer FROM consumer')
        host.detach()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.commit()
        connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_edge_transition').fetchone(),(0,))

@unittest.skipUnless(os.environ.get('TRUSS_EDGE_HOTFIX_SOURCE_PACKAGE'),'Checksum-verified published35 package required')
class PublishedEdgeWriterUpgradeTests(unittest.TestCase):
    def test_populated35_upgrade_replay_new_write_and_writer_revocation(self):
        with tempfile.TemporaryDirectory(prefix='truss-edge-hotfix-') as directory:
            with LocalPostgres(Path(directory)/'data') as runtime:
                tests=Path(__file__).parent.resolve();artifact=Path(directory)/'original.pickle'
                env={**os.environ,'PYTHONPATH':os.environ['TRUSS_EDGE_HOTFIX_SOURCE_PACKAGE']+os.pathsep+str(tests)}
                subprocess.run([sys.executable,str(tests/'_seed_edge_writer_hotfix.py'),runtime.info.connection_uri,str(artifact)],env=env,check=True,timeout=120)
                documents,a,b,edge,original,request,semantic=pickle.loads(artifact.read_bytes())
                intermediate=os.environ.get('TRUSS_EDGE_HOTFIX_INTERMEDIATE_PACKAGE')
                previous_release='truss-catalog-runtime/0.68-candidate'
                if intermediate:
                    # Real published35 genesis, then real hotfix70 active ledger.
                    # Never synthesize or relabel predecessor installation rows.
                    middle_env={**os.environ,'PYTHONPATH':intermediate}
                    subprocess.run([sys.executable,'-c',"""
import sys,psycopg
from truss import Ok,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
with psycopg.connect(sys.argv[1],autocommit=True,options='-c statement_timeout=10000') as c:
    c.execute('BEGIN');h=adopt_psycopg_host(c,statement_timeout_ms=10000,operation_timeout_ms=30000)
    assembled=create_reference_assembly(CatalogRuntimeConfiguration(),h)
    assert isinstance(assembled,Ok),repr(assembled)
    a=assembled.value;t=h.adopt_transaction().value
    result=a.upgrade_in_transaction(t)
    assert isinstance(result,Ok),repr(result)
    assert result.value.release_id=='truss-catalog-runtime/0.70-candidate',repr(result)
    h.detach();c.commit()
    assert c.execute('SELECT release_id FROM truss.catalog_runtime_installation').fetchone()==('truss-catalog-runtime/0.68-candidate',)
    assert c.execute('SELECT release_id FROM truss.runtime_current_installation()').fetchone()==('truss-catalog-runtime/0.70-candidate',)
""",runtime.info.connection_uri],env=middle_env,check=True,timeout=120)
                    previous_release='truss-catalog-runtime/0.70-candidate'
                with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=10000') as admin:
                    tables=('object','edge','journal','request_receipt','runtime_object_attempt','runtime_object_transition','runtime_edge_transition')
                    def facts():return {name:admin.execute("SELECT to_jsonb(t)-'result_count' FROM truss."+name+" t ORDER BY (to_jsonb(t)-'result_count')::text COLLATE \"C\"").fetchall() for name in tables}
                    before=facts()
                    def routines():return admin.execute("SELECT p.oid,p.proowner,p.proacl FROM pg_proc p WHERE p.pronamespace='truss'::regnamespace ORDER BY p.oid").fetchall()
                    routine_custody=routines()
                    partial_oids={row[0] for row in admin.execute('SELECT to_regprocedure(s)::oid FROM unnest(%s::text[]) s',(['truss.'+s for s in _PARTIAL_GROUP_FUNCTIONS],)).fetchall()}
                    def assert_routine_custody(closed=False):
                        current={row[0]:row for row in routines()}
                        for original_routine in routine_custody:
                            actual=current[original_routine[0]]
                            if closed and actual[0] in partial_oids:self.assertEqual(actual[:2],original_routine[:2])
                            else:self.assertEqual(actual,original_routine)
                        if closed:
                            self.assertEqual(admin.execute("SELECT EXISTS(SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE p.oid=ANY(%s::oid[]) AND a.grantee<>p.proowner)",(list(partial_oids),)).fetchone(),(False,))
                            self.assertEqual(admin.execute("SELECT has_function_privilege('group_writer','truss.apply_group(bytea,bytea,bytea,text,text)','EXECUTE')").fetchone(),(True,))
                    installation=admin.execute('SELECT installation_id,source_epoch,owner_oid,registrar_oid FROM truss.catalog_runtime_installation').fetchone()
                    for commit,expected in ((False,'upgraded'),(True,'upgraded'),(True,'unchanged')):
                        admin.execute('BEGIN');host=adopt_psycopg_host(admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
                        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                        upgraded=assembly.upgrade_in_transaction(tx)
                        self.assertIsInstance(upgraded,Ok,repr(upgraded)+' '+str(host._custody.last_attempt.error))
                        self.assertEqual(upgraded.value.outcome,expected)
                        self.assertEqual(upgraded.value.release_id,_release()[0]['releaseId'])
                        host.detach()
                        if commit:admin.commit()
                        else:
                            admin.rollback()
                            self.assertEqual(admin.execute('SELECT release_id FROM truss.runtime_current_installation()').fetchone(),(previous_release,))
                            self.assertEqual(facts(),before);self.assertEqual(routines(),routine_custody)
                    self.assertEqual(facts(),before);assert_routine_custody(closed=True)
                    self.assertEqual(admin.execute('SELECT installation_id,source_epoch,owner_oid,registrar_oid FROM truss.catalog_runtime_installation').fetchone(),installation)
                    params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri);params['user']='consumer'
                    with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as connection:
                        def adopt():
                            connection.execute('BEGIN');host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
                            assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
                            return host,assembly,host.adopt_transaction().value
                        host,assembly,tx=adopt()
                        replay=assembly.apply_in_transaction(tx,original,request,documents=documents)
                        self.assertIsInstance(replay,Ok,repr(replay));self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
                        self.assertEqual(replay.value.response.semantic,semantic)
                        found=assembly.get_edge_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',edge_id=int(edge.id))
                        self.assertIsInstance(found.value,EdgeFound)
                        context=assembly.group_context_in_transaction(tx).value
                        new=UpdateEdge(target=StoredObjectReference(identity=edge),set=(),unset=(),order_key_change=TextOrderKey(text='after-hotfix'))
                        created=assembly.apply_in_transaction(tx,context.input((new,),MapValue(entries=())),RequestNone(),documents=documents)
                        self.assertIsInstance(created,Ok,repr(created));self.assertIsInstance(created.value,GroupSuccess,repr(created))
                        host.detach();connection.commit();committed=facts()
                        self.assertEqual(admin.execute('SELECT order_key FROM truss.edge WHERE id=%s',(int(edge.id),)).fetchone(),('after-hotfix',))
                        host,assembly,tx=adopt();context=assembly.group_context_in_transaction(tx).value
                        change=UpdateEdge(target=StoredObjectReference(identity=edge),set=(),unset=(),order_key_change=TextOrderKey(text='must-rollback'))
                        result=assembly.apply_in_transaction(tx,context.input((change,),MapValue(entries=())),RequestNone(),documents=documents)
                        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,GroupSuccess,repr(result))
                        connection.execute('SET CONSTRAINTS truss.runtime_object_attempt_commit IMMEDIATE')
                        admin.execute('GRANT group_reader TO consumer WITH SET FALSE');admin.execute('REVOKE group_writer FROM consumer')
                        host.detach()
                        with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.commit()
                        connection.rollback();self.assertEqual(facts(),committed)
