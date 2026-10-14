"""Preserve a genuine native60 report while adding required rebinding in native61."""
import json,os,pickle,subprocess,sys,tempfile,unittest
from pathlib import Path
import psycopg
from truss import LocalPostgres,Ok,CatalogDocument,CatalogRegistration,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly,HistoryEntity,HistoricalRecord,ObjectFound,QueryRows

@unittest.skipUnless(os.environ.get('TRUSS_REBIND_UPGRADE_SOURCE_PACKAGE'),'Installed native60 predecessor required')
class CatalogRebindUpgradeTests(unittest.TestCase):
    def test_original_optional_report_and_new_required_rebind(self):
        with tempfile.TemporaryDirectory(prefix='truss-rebind-upgrade-',dir='/private/tmp') as directory:
            with LocalPostgres(Path(directory)/'data') as runtime:
                artifact=Path(directory)/'original.pickle';tests=Path(__file__).parent.resolve()
                env={**os.environ,'PYTHONPATH':os.environ['TRUSS_REBIND_UPGRADE_SOURCE_PACKAGE']+os.pathsep+str(tests)}
                subprocess.run([sys.executable,str(tests/'_seed_catalog_rebind_upgrade_060.py'),runtime.info.connection_uri,str(artifact)],env=env,check=True,timeout=120)
                document,identity,revision,original_report=pickle.loads(artifact.read_bytes())
                self.assertEqual(json.loads(original_report)['rebindProfile'],'truss-native-catalog-rebind/0.1')
                with psycopg.connect(runtime.info.connection_uri,autocommit=True,options="-c statement_timeout=10000") as admin:
                    admin.execute('BEGIN');host=adopt_psycopg_host(admin);assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;adopted=host.adopt_transaction();self.assertIsInstance(adopted,Ok,repr(adopted));tx=adopted.value
                    upgraded=assembly.upgrade_in_transaction(tx)
                    self.assertIsInstance(upgraded,Ok,repr(upgraded)+' '+str(host._custody.last_attempt.error));host.detach();admin.commit()
                params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri);params['user']='consumer'
                with psycopg.connect(**params,autocommit=True,options="-c statement_timeout=10000") as connection:
                    connection.execute('BEGIN');host=adopt_psycopg_host(connection);assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;adopted=host.adopt_transaction();self.assertIsInstance(adopted,Ok,repr(adopted));tx=adopted.value
                    self.assertEqual(assembly.report_in_transaction(tx,revision).value.original_bytes,original_report)
                    source=json.loads(document.content);module=source['modules'][0]
                    module['elements'].append({'id':'laterRequired','name':'laterRequired','kind':'field','scalarType':'string','cardinality':'one','nullability':'required','extensions':{}})
                    next(e for e in module['elements'] if e['id']=='A')['members'].append({'module':'m','element':'laterRequired'})
                    prepared=assembly.prepare_catalog((CatalogDocument('adoc','r3',json.dumps(source).encode()),),source_version='0.8.0',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    accepted=assembly.accept_in_transaction(tx,prepared,request_key='new-required-rebind')
                    self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(accepted.value,CatalogRegistration)
                    self.assertEqual(json.loads(accepted.value.report_bytes)['rebindProfile'],'truss-native-catalog-rebind/0.2')
                    self.assertEqual(assembly.report_in_transaction(tx,revision).value.original_bytes,original_report)
                    read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
                    self.assertIsInstance(read.value,ObjectFound);self.assertEqual(read.value.object.version,3);self.assertEqual(dict(read.value.object.values)['laterRequired'],'retained later')
                    query=assembly.query_in_transaction(tx,sql='SELECT a.* FROM "A" a',document_ids=('adoc',),read_profile='complete-entity')
                    self.assertIsInstance(query.value,QueryRows,repr(query)+' '+str(host._custody.last_attempt.error))
                    host.detach();connection.commit();connection.execute('BEGIN');host=adopt_psycopg_host(connection);adopted=host.adopt_transaction();self.assertIsInstance(adopted,Ok,repr(adopted));tx=adopted.value;assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
                    for version in (2,3):
                        history=assembly.reconstruct_in_transaction(tx,entity=HistoryEntity(kind='object',document_id='adoc',module_id='m',definition_id='A',id=int(identity.id)),version=version)
                        self.assertIsInstance(history.value,HistoricalRecord,repr(history)+' '+str(host._custody.last_attempt.error))
                    host.detach();connection.rollback()
