"""One real installed candidate upgrade workflow, including caller rollback."""
import json,os,pickle,subprocess,sys,tempfile,unittest
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
                env=dict(os.environ,PYTHONPATH=os.environ['TRUSS_UPGRADE_SOURCE_PACKAGE']+os.pathsep+str(tests)+os.pathsep+str(tests.parents[2]/'scripts')+os.pathsep+os.environ.get('PYTHONPATH',''))
                subprocess.run([sys.executable,str(tests/'_seed_runtime_upgrade_023.py'),runtime.info.connection_uri,str(artifact)],env=env,check=True,timeout=120)
                documents,input,request,identity,token,report,page,next_operation=pickle.loads(artifact.read_bytes())
                params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri)
                with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as admin:
                    installation=admin.execute('SELECT installation_id::text,source_epoch::text FROM truss.catalog_runtime_installation').fetchone()
                    genesis_release=admin.execute('SELECT release_id FROM truss.catalog_runtime_installation').fetchone()[0]
                    original_ledger=admin.execute("SELECT to_regclass('truss.runtime_release') IS NOT NULL").fetchone()[0]
                    receipt_exists=admin.execute("SELECT to_regclass('truss.runtime_feed_ack_receipt') IS NOT NULL").fetchone()[0]
                    original_receipt_table=admin.execute("SELECT oid,relowner,relacl FROM pg_class WHERE oid='truss.runtime_feed_ack_receipt'::regclass").fetchone() if receipt_exists else None
                    original_receipts=admin.execute('SELECT to_jsonb(r) FROM truss.runtime_feed_ack_receipt r ORDER BY registration_id,prior_sha256,target_sha256').fetchall() if receipt_exists else []
                    if not receipt_exists:
                        # The new private receipt table must not inherit direct consumer
                        # access from administrator defaults during an additive upgrade.
                        admin.execute('ALTER DEFAULT PRIVILEGES GRANT SELECT ON TABLES TO consumer')
                        admin.execute('BEGIN')
                        host=adopt_psycopg_host(admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
                        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
                        tx=host.adopt_transaction().value
                        blocked=assembly.upgrade_in_transaction(tx)
                        self.assertNotIsInstance(blocked,Ok)
                        self.assertIn('Owner-only ACK receipt',str(host._custody.last_attempt.error))
                        host.detach();admin.rollback()
                        self.assertIsNone(admin.execute("SELECT to_regclass('truss.runtime_feed_ack_receipt')").fetchone()[0])
                        admin.execute('ALTER DEFAULT PRIVILEGES REVOKE SELECT ON TABLES FROM consumer')
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
                            self.assertEqual(admin.execute("SELECT to_regclass('truss.runtime_release') IS NOT NULL").fetchone()[0],original_ledger)
                    self.assertEqual(admin.execute('SELECT installation_id::text,source_epoch::text FROM truss.catalog_runtime_installation').fetchone(),installation)
                    if receipt_exists:
                        self.assertEqual(admin.execute("SELECT oid,relowner,relacl FROM pg_class WHERE oid='truss.runtime_feed_ack_receipt'::regclass").fetchone(),original_receipt_table)
                        self.assertEqual(admin.execute('SELECT to_jsonb(r) FROM truss.runtime_feed_ack_receipt r ORDER BY registration_id,prior_sha256,target_sha256').fetchall(),original_receipts)
                    self.assertEqual(admin.execute('SELECT release_id FROM truss.catalog_runtime_installation').fetchone()[0],genesis_release)
                    self.assertEqual(admin.execute('SELECT release_id FROM truss.runtime_current_installation()').fetchone()[0],'truss-catalog-runtime/0.57-candidate')
                    from truss._security_home_installation import bootstrap_security_homes_in_transaction
                    admin.execute('BEGIN');bootstrap_host=adopt_psycopg_host(admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
                    try:
                        bootstrap_tx=bootstrap_host.adopt_transaction().value
                        bootstrap=bootstrap_security_homes_in_transaction(bootstrap_host,bootstrap_tx,installation_identity=installation[0].encode(),authored_profile=b'upgraded-bootstrap-fixture/0.1',max_retained=6)
                        self.assertIsInstance(bootstrap,Ok,str(bootstrap_host._custody.last_attempt.error))
                        self.assertFalse(bootstrap.value.security_ready)
                        self.assertEqual(admin.execute('SELECT generation FROM truss.policy_generation_guard').fetchone(),(1,))
                    finally:bootstrap_host.detach()
                    admin.commit()

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
                    current=assembly.read_feed_in_transaction(tx,consumer_id=page.consumer_id)
                    self.assertIsInstance(current.value,FeedPage)
                    configuration=json.loads(current.value.content)['configuration']
                    self.assertEqual(configuration['layoutProfile']['version'],'1.0')
                    self.assertEqual(configuration['releaseId'],'truss-catalog-runtime/0.57-candidate')

                    host.detach();self.assertIsNone(consumer.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0]);consumer.rollback()
