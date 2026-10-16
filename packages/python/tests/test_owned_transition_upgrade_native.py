"""One public populated predecessor upgrade for cascade transition storage."""
import os,pickle,subprocess,sys,tempfile,unittest
from pathlib import Path
import psycopg
from truss import LocalPostgres,Ok,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly,EdgeFound,ObjectFound
from truss.contracts import TextValue,MapValue
from truss.groups import AuthoredValue,UpdateObject,Delete,CreateEdge,CreateObject,RootlessOwnership,AliasObjectReference,NullOrderKey,StoredObjectReference,GroupSuccess,CommittedReceiptReplay

@unittest.skipUnless(os.environ.get('TRUSS_OWNED_UPGRADE_SOURCE_PACKAGE'),'Retained predecessor package required')
class OwnedTransitionUpgradeTests(unittest.TestCase):
    def test_preserve_transitions_and_receipt_then_continue(self):
        with tempfile.TemporaryDirectory(prefix='truss-owned-upgrade-') as directory:
            with LocalPostgres(Path(directory)/'data') as runtime:
                tests=Path(__file__).parent.resolve();artifact=Path(directory)/'original.pickle'
                env={**os.environ,'PYTHONPATH':os.environ['TRUSS_OWNED_UPGRADE_SOURCE_PACKAGE']+os.pathsep+str(tests)}
                subprocess.run([sys.executable,str(tests/'_seed_owned_upgrade_064.py'),runtime.info.connection_uri,str(artifact)],env=env,check=True,timeout=120)
                documents,object_identity,edge_identity,input,request,semantic=pickle.loads(artifact.read_bytes())
                with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=10000') as admin:
                    objects=admin.execute('SELECT to_jsonb(t)::text FROM truss.runtime_object_transition t ORDER BY transition_id').fetchall()
                    edges=admin.execute('SELECT to_jsonb(t)::text FROM truss.runtime_edge_transition t ORDER BY transition_id').fetchall()
                    self.assertEqual(len(objects),1 if os.environ.get('TRUSS_OWNED_UPGRADE_SOURCE_RELEASE','truss-catalog-runtime/0.64-candidate')=='truss-catalog-runtime/0.64-candidate' else 3);self.assertEqual(len(edges),1)
                    admin.execute('BEGIN');host=adopt_psycopg_host(admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
                    assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                    upgraded=assembly.upgrade_in_transaction(tx)
                    self.assertIsInstance(upgraded,Ok,repr(upgraded)+' '+str(host._custody.last_attempt.error))
                    self.assertEqual(upgraded.value.previous_release_id,os.environ.get('TRUSS_OWNED_UPGRADE_SOURCE_RELEASE','truss-catalog-runtime/0.64-candidate'))
                    from truss.catalog_runtime import _release
                    self.assertEqual(upgraded.value.release_id,_release()[0]['releaseId'])
                    self.assertEqual(upgraded.value.outcome,'upgraded');host.detach();admin.commit()
                    self.assertEqual(admin.execute("SELECT attgenerated FROM pg_attribute WHERE attrelid='truss.runtime_object_attempt'::regclass AND attname='result_count'").fetchone(),('s',))
                    self.assertEqual(admin.execute('SELECT count(*) FROM truss.runtime_object_attempt WHERE result_count IS DISTINCT FROM jsonb_array_length(results)').fetchone(),(0,))
                    private_names=['runtime_can_read_qualified','runtime_module_writer_qualified','runtime_object_values_readable_qualified','runtime_owned_object_transition_validate_qualified','runtime_owned_history_record_in_metadata','runtime_owned_group_step_in_input','apply_create_group_qualified']
                    private_rows=admin.execute("SELECT p.proname,has_function_privilege('consumer',p.oid,'EXECUTE'),p.proowner=i.owner_oid FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN truss.catalog_runtime_installation i WHERE n.nspname='truss' AND p.proname=ANY(%s) ORDER BY p.proname",(private_names,)).fetchall()
                    self.assertEqual(private_rows,[(name,False,True) for name in sorted(private_names)])
                    journal_guard=admin.execute("SELECT c.relname,t.tgenabled,t.tgdeferrable,t.tginitdeferred,t.tgfoid='truss.runtime_owned_journal_insert_check()'::regprocedure,has_function_privilege('consumer',t.tgfoid,'EXECUTE'),p.proowner=i.owner_oid FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_proc p ON p.oid=t.tgfoid CROSS JOIN truss.catalog_runtime_installation i WHERE t.tgname='runtime_owned_journal_insert_commit' ORDER BY c.relname").fetchall()
                    self.assertEqual(journal_guard,[(name,'A',True,True,True,False,True) for name in ('journal','journal_runtime_horizon')])
                    self.assertEqual(admin.execute('SELECT to_jsonb(t)::text FROM truss.runtime_object_transition t ORDER BY transition_id').fetchall(),objects)
                    if upgraded.value.previous_release_id=='truss-catalog-runtime/0.64-candidate':
                        self.assertEqual(admin.execute("SELECT (to_jsonb(t)-'endpoint_ownership')::text FROM truss.runtime_edge_transition t ORDER BY transition_id").fetchall(),edges)
                        self.assertEqual(admin.execute('SELECT endpoint_ownership FROM truss.runtime_edge_transition').fetchall(),[(None,)])
                    else:
                        self.assertEqual(admin.execute('SELECT to_jsonb(t)::text FROM truss.runtime_edge_transition t ORDER BY transition_id').fetchall(),edges)
                params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri);params['user']='consumer'
                with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as connection:
                    connection.execute('BEGIN');host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
                    assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                    replay=assembly.apply_in_transaction(tx,input,request,documents=documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    self.assertIsInstance(replay.value.response,CommittedReceiptReplay,repr(replay))
                    self.assertEqual(replay.value.response.semantic,semantic)
                    edge=assembly.get_edge_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',edge_id=int(edge_identity.id)).value
                    self.assertIsInstance(edge,EdgeFound)
                    found=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(object_identity.id))
                    self.assertIsInstance(found.value,ObjectFound)
                    context=assembly.group_context_in_transaction(tx).value
                    update=UpdateObject(target=StoredObjectReference(identity=found.value.object.identity),set=(AuthoredValue(name='value',value=TextValue(kind='string',text='after-upgrade')),),unset=())
                    unchanged=Delete(operation='delete_edge',target=StoredObjectReference(identity=edge.edge.identity))
                    parallel=CreateEdge(relationship_definition_pin=edge.edge.identity.definition_pin,source=StoredObjectReference(identity=edge.edge.source),target=StoredObjectReference(identity=edge.edge.target),values=(),order_key=NullOrderKey())
                    changed=assembly.apply_in_transaction(tx,context.input((update,unchanged,parallel),MapValue(entries=())),context.request('post-upgrade'),documents=documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    self.assertIsInstance(changed,Ok,repr(changed)+str(host._custody.last_attempt.error));self.assertIsInstance(changed.value,GroupSuccess,repr(changed))
                    # New creation and deletion use the upgraded provider in one group.
                    created=CreateObject(type_definition_pin=found.value.object.identity.definition_pin,
                        values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='new-after-upgrade')),
                                AuthoredValue(name='A-value',value=TextValue(kind='string',text='new-after-upgrade'))),
                        ownership=RootlessOwnership(),alias='new-after-upgrade')
                    removed=Delete(operation='delete_object',target=AliasObjectReference(alias='new-after-upgrade'),expected_version='1')
                    continued=assembly.apply_in_transaction(tx,context.input((created,removed),MapValue(entries=())),
                        context.request('post-upgrade-create-delete'),documents=documents,
                        bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    self.assertIsInstance(continued,Ok,repr(continued)+str(host._custody.last_attempt.error))
                    self.assertIsInstance(continued.value,GroupSuccess,repr(continued))
                    self.assertEqual([r.outcome for r in continued.value.response.semantic.results],['created','deleted'])
                    capacity=tuple(CreateObject(type_definition_pin=found.value.object.identity.definition_pin,
                        values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text=f'upgrade-capacity-{i}')),
                                AuthoredValue(name='A-value',value=TextValue(kind='string',text='upgraded'))),
                        ownership=RootlessOwnership()) for i in range(129))
                    expanded=assembly.apply_in_transaction(tx,context.input(capacity,MapValue(entries=())),
                        context.request('post-upgrade-129'),documents=documents,
                        bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    self.assertIsInstance(expanded,Ok,repr(expanded)+str(host._custody.last_attempt.error))
                    self.assertIsInstance(expanded.value,GroupSuccess,repr(expanded))
                    self.assertEqual(len(expanded.value.response.semantic.results),129)
                    self.assertTrue(all(r.outcome=='created' for r in expanded.value.response.semantic.results))
                    host.detach();connection.commit()
                with psycopg.connect(runtime.info.connection_uri,autocommit=True) as admin:
                    contexts=admin.execute('SELECT endpoint_ownership::text FROM truss.runtime_edge_transition WHERE endpoint_ownership IS NOT NULL ORDER BY transition_id').fetchall()
                    self.assertEqual(len(contexts),2 if upgraded.value.previous_release_id=='truss-catalog-runtime/0.64-candidate' else 3)
                    contexts=contexts[-2:]
                    import json
                    first,second=(json.loads(row[0]) for row in contexts)
                    self.assertEqual(first['before']['source']['ownership'],{'state':'rootless'})
                    self.assertIsNone(first['after'])
                    self.assertIsNone(second['before']);self.assertEqual(second['after']['source']['ownership'],{'state':'rootless'})
