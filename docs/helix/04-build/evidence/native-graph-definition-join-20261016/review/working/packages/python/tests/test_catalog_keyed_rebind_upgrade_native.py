"""One populated native62 upgrade through public keyed rebinding."""
import json,os,pickle,subprocess,sys,tempfile,unittest
from pathlib import Path
import psycopg
from truss import LocalPostgres,Ok,CatalogDocument,CatalogRegistration,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly,ObjectFound,QueryRows

@unittest.skipUnless(os.environ.get('TRUSS_KEYED_UPGRADE_SOURCE_PACKAGE'),'Native62 predecessor required')
class CatalogKeyedRebindUpgradeTests(unittest.TestCase):
    def test_preserve_original_report_then_backfill_key(self):
        with tempfile.TemporaryDirectory(prefix='truss-key-upgrade-') as directory:
            with LocalPostgres(Path(directory)/'data') as runtime:
                artifact=Path(directory)/'original.pickle';tests=Path(__file__).parent.resolve()
                env={**os.environ,'PYTHONPATH':os.environ['TRUSS_KEYED_UPGRADE_SOURCE_PACKAGE']+os.pathsep+str(tests)}
                subprocess.run([sys.executable,str(tests/'_seed_catalog_key_backfill_upgrade_062.py'),runtime.info.connection_uri,str(artifact)],env=env,check=True,timeout=120)
                document,identity,revision,report=pickle.loads(artifact.read_bytes())
                self.assertEqual(json.loads(report)['keyBackfillProfile'],'truss-catalog-key-backfill/0.1')
                with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=10000') as admin:
                    admin.execute('BEGIN');host=adopt_psycopg_host(admin,statement_timeout_ms=10000,operation_timeout_ms=30000);assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                    upgraded=assembly.upgrade_in_transaction(tx)
                    self.assertIsInstance(upgraded,Ok,repr(upgraded)+' '+str(host._custody.last_attempt.error))
                    self.assertEqual(upgraded.value.previous_release_id,'truss-catalog-runtime/0.62-candidate')
                    self.assertEqual(upgraded.value.release_id,'truss-catalog-runtime/0.63-candidate')
                    self.assertEqual(upgraded.value.outcome,'upgraded')
                    host.detach();admin.commit()
                params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri);params['user']='consumer'
                with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as connection:
                    connection.execute('BEGIN');host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                    self.assertEqual(assembly.report_in_transaction(tx,revision).value.original_bytes,report)
                    source=json.loads(document.content)
                    module=source['modules'][0]
                    module['elements'].append({'id':'giftCode','name':'giftCode','kind':'field','cardinality':'one','nullability':'required','scalarType':'string','extensions':{}})
                    record=next(e for e in module['elements'] if e['id']=='A')
                    record['members'].append({'module':'m','element':'giftCode'})
                    record['keys'].append({'id':'gift-key','name':'gift-key','fields':[{'module':'m','element':'giftCode'}],'primary':False})
                    prepared=assembly.prepare_catalog((CatalogDocument('adoc','r3',json.dumps(source).encode()),),source_version='0.8.0',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    accepted=assembly.accept_in_transaction(tx,prepared,request_key='upgraded-key',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(accepted.value,CatalogRegistration)
                    self.assertEqual(json.loads(accepted.value.report_bytes)['keyBackfillProfile'],'truss-catalog-key-backfill/0.2')
                    self.assertEqual(json.loads(accepted.value.report_bytes)['rebindProfile'],'truss-native-catalog-rebind/0.3')
                    found=assembly.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id='gift-key',values=('retained-code',),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    self.assertIsInstance(found.value,ObjectFound,repr(found));self.assertEqual(found.value.object.id,int(identity.id));self.assertEqual(found.value.object.version,2)
                    self.assertEqual(assembly.report_in_transaction(tx,revision).value.original_bytes,report)
                    query=assembly.query_in_transaction(tx,sql='SELECT a."giftCode" FROM "A" a',document_ids=('adoc',))
                    self.assertIsInstance(query.value,QueryRows,repr(query));self.assertEqual(query.value.rows,(('retained-code',),));host.detach();connection.commit()
