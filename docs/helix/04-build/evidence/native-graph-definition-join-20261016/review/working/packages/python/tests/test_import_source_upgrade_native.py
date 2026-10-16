"""Published source rows survive the operation-indexed storage upgrade."""
import os,pickle,subprocess,sys,tempfile,unittest
from pathlib import Path
import psycopg
from truss import LocalPostgres,Ok,HistoryEntity,ImportSourceFound,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.imports import ImportReported,ImportSkipped,ImportCreated
from truss.contracts import MapValue,TextValue
from truss.groups import AuthoredValue

@unittest.skipUnless(os.environ.get('TRUSS_IMPORT_SOURCE_PREDECESSOR'),'Checksum-verified published predecessor required')
class ImportSourceUpgradeTests(unittest.TestCase):
    def test_populated_sources_preserved_through_rollback_upgrade_and_retry(self):
        with tempfile.TemporaryDirectory(prefix='truss-import-source-upgrade-') as directory:
            with LocalPostgres(Path(directory)/'data') as runtime:
                snapshot=Path(directory)/'source.pickle';tests=Path(__file__).parent.resolve()
                env={**os.environ,'PYTHONPATH':os.environ['TRUSS_IMPORT_SOURCE_PREDECESSOR']+os.pathsep+str(tests)}
                subprocess.run([sys.executable,str(tests/'_seed_import_source_upgrade.py'),runtime.info.connection_uri,str(snapshot)],env=env,check=True,timeout=120)
                documents,original,identities=pickle.loads(snapshot.read_bytes())
                with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=10000') as admin:
                    before=admin.execute('SELECT to_jsonb(s) FROM truss.runtime_import_source s ORDER BY entity_kind,entity_id').fetchall()
                    sources=admin.execute('SELECT to_jsonb(s) FROM truss.record_source s ORDER BY entity_kind,entity_id').fetchall()
                    self.assertEqual(len(before),2)
                    for commit in (False,True):
                        admin.execute('BEGIN');host=adopt_psycopg_host(admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
                        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                        result=assembly.upgrade_in_transaction(tx)
                        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error))
                        self.assertEqual(admin.execute("SELECT to_jsonb(s)-'operation_index' FROM truss.runtime_import_source s ORDER BY entity_kind,entity_id").fetchall(),before)
                        self.assertEqual(admin.execute('SELECT operation_index FROM truss.runtime_import_source').fetchall(),[(0,),(0,)])
                        host.detach()
                        if commit:admin.commit()
                        else:
                            admin.rollback()
                            self.assertEqual(admin.execute('SELECT to_jsonb(s) FROM truss.runtime_import_source s ORDER BY entity_kind,entity_id').fetchall(),before)
                    self.assertEqual(admin.execute('SELECT to_jsonb(s) FROM truss.record_source s ORDER BY entity_kind,entity_id').fetchall(),sources)
                params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri);params['user']='consumer'
                with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as connection:
                    connection.execute('BEGIN');host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
                    assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                    context=assembly.import_context_in_transaction(tx).value
                    retry=context.input(original.records,load_id='replacement-load',asserted_origin=original.asserted_origin)
                    result=assembly.import_in_transaction(tx,retry,documents=documents)
                    self.assertIsInstance(result,ImportReported,repr(result))
                    self.assertTrue(all(isinstance(o,ImportSkipped) for o in result.report.outcomes))
                    for identity in identities:
                        found=assembly.lookup_import_source_in_transaction(tx,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identity.id)))
                        self.assertIsInstance(found,Ok,repr(found));self.assertIsInstance(found.value,ImportSourceFound)
                        self.assertEqual(found.value.load_id,'original-load')
                    record=assembly.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',
                        values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='post-upgrade')),
                                AuthoredValue(name='A-value',value=TextValue(kind='string',text='post-upgrade'))))
                    self.assertIsInstance(record,Ok,repr(record))
                    created=assembly.import_in_transaction(tx,context.input((record.value,),load_id='new-load',asserted_origin=MapValue(entries=())),documents=documents)
                    self.assertIsInstance(created,ImportReported,repr(created))
                    self.assertIsInstance(created.report.outcomes[0],ImportCreated)
                    host.detach();connection.commit()
                with psycopg.connect(runtime.info.connection_uri,autocommit=True) as admin:
                    self.assertEqual(admin.execute('SELECT operation_index FROM truss.runtime_import_source ORDER BY entity_id').fetchall(),[(0,),(0,),(0,)])
                    self.assertEqual(admin.execute('SELECT load_id FROM truss.record_source ORDER BY entity_id').fetchall(),[('original-load',),('original-load',),('new-load',)])


class ImportSourceMigrationIntegrityTests(unittest.TestCase):
    def test_changed_migration_bytes_are_refused_before_execution(self):
        from importlib.resources import files
        from unittest.mock import patch
        from truss.catalog_runtime import _release
        package=files('truss')
        class ChangedMigration:
            def __init__(self,path):self.path=path
            def joinpath(self,name):return ChangedMigration(self.path.joinpath(name))
            def read_bytes(self):
                raw=self.path.read_bytes()
                return raw+b'-- changed' if self.path.name=='import-source-upgrade.sql' else raw
        with patch('truss.catalog_runtime.files',return_value=ChangedMigration(package)):
            with self.assertRaisesRegex(ValueError,'Original migration/preparation baseline required'):
                _release()
