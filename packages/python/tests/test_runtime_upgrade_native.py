"""One real installed .23 -> .24 public workflow, including caller rollback."""
import os,pickle,subprocess,sys,tempfile,unittest
from pathlib import Path
import psycopg
from truss import (LocalPostgres,Ok,adopt_psycopg_host,create_reference_assembly,
    CatalogRuntimeConfiguration,PendingRuntimeUpgrade,ReceiptIncluded,FeedPage,ObjectFound)
from truss.contracts import MapValue
from truss.groups import GroupSuccess,CommittedReceiptReplay

@unittest.skipUnless(os.environ.get('TRUSS_UPGRADE_SOURCE_PACKAGE'),'Exact installed .23 source package required')
class RuntimeUpgradeTests(unittest.TestCase):
    def test_preserve_original_facts_rollback_upgrade_and_continue(self):
        with tempfile.TemporaryDirectory(prefix='truss-upgrade-',dir='/private/tmp') as directory:
            root=Path(directory)
            with LocalPostgres(root/'data') as runtime:
                artifact=root/'original-facts.pickle'
                tests=Path(__file__).parent.resolve()
                env=dict(os.environ,PYTHONPATH=os.environ['TRUSS_UPGRADE_SOURCE_PACKAGE']+os.pathsep+str(tests)+os.pathsep+str(tests.parents[2]/'scripts'))
                subprocess.run([sys.executable,str(tests/'_seed_runtime_upgrade_023.py'),runtime.info.connection_uri,str(artifact)],env=env,check=True,timeout=120)
                documents,input,request,identity,token,report,page,next_operation=pickle.loads(artifact.read_bytes())
                params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
                with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as admin:
                    installation=admin.execute('SELECT installation_id::text,source_epoch::text FROM truss.catalog_runtime_installation').fetchone()
                    for commit in (False,True):
                        admin.execute('BEGIN')
                        host=adopt_psycopg_host(admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
                        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
                        adopted=host.adopt_transaction()
                        self.assertIsInstance(adopted,Ok,repr(adopted));tx=adopted.value
                        upgraded=assembly.upgrade_in_transaction(tx)
                        if not isinstance(upgraded,Ok):self.fail(repr(upgraded)+' '+str(host._custody.last_attempt.error))
                        self.assertIsInstance(upgraded.value,PendingRuntimeUpgrade);self.assertEqual(upgraded.value.outcome,'upgraded')
                        self.assertEqual(upgraded.value.status,'pending_commit')
                        self.assertEqual(upgraded.value.installation_id,installation[0])
                        self.assertTrue(assembly.status_in_transaction(tx).value.installed)
                        host.detach()
                        if commit:admin.commit()
                        else:
                            admin.rollback()
                            self.assertIsNone(admin.execute("SELECT to_regclass('truss.runtime_release')").fetchone()[0])
                    self.assertEqual(admin.execute('SELECT installation_id::text,source_epoch::text FROM truss.catalog_runtime_installation').fetchone(),installation)
                    self.assertEqual(admin.execute('SELECT release_id FROM truss.catalog_runtime_installation').fetchone()[0],'truss-catalog-runtime/0.23-candidate')
                    self.assertEqual(admin.execute('SELECT release_id FROM truss.runtime_current_installation()').fetchone()[0],'truss-catalog-runtime/0.24-candidate')
                params['user']='consumer'
                with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as consumer:
                    consumer.execute('BEGIN');host=adopt_psycopg_host(consumer)
                    assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                    self.assertEqual(assembly.report_in_transaction(tx).value.original_bytes,report)
                    found=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
                    self.assertIsInstance(found.value,ObjectFound)
                    replay=assembly.apply_in_transaction(tx,input,request,documents=documents,bun_executable='/opt/homebrew/bin/bun')
                    self.assertIsInstance(replay,Ok);self.assertIsInstance(replay.value.response,CommittedReceiptReplay)
                    self.assertEqual(replay.value.response.receipt_token,token)
                    context=assembly.group_context_in_transaction(tx).value
                    created=assembly.groups(assembly.group_selection,documents=documents,bun_executable='/opt/homebrew/bin/bun').capability.apply_in_transaction(tx,
                        context.input((next_operation,),MapValue(entries=())),context.request('upgrade-new'))
                    self.assertIsInstance(created.value,GroupSuccess)
                    host.detach();consumer.commit()
                    consumer.execute('BEGIN READ ONLY');host=adopt_psycopg_host(consumer)
                    assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction(access_mode='read_only').value
                    self.assertIsInstance(assembly.reached_in_transaction(tx,token).value,ReceiptIncluded)
                    reread=assembly.feed(assembly.feed_selection).capability.reread_feed_in_transaction(tx,page)
                    self.assertIsInstance(reread.value,FeedPage);self.assertEqual(reread.value.content,page.content)
                    host.detach();self.assertIsNone(consumer.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0]);consumer.rollback()
