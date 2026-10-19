# SPDX-License-Identifier: MIT OR Apache-2.0
"""One populated native63 upgrade through public keyed rebinding."""
import json,os,pickle,subprocess,sys,tempfile,unittest
from pathlib import Path
import psycopg
from truss.contracts import MapValue,MapEntry,SequenceValue,TextValue
from truss.groups import AuthoredValue,UpdateObject,StoredObjectReference,GroupSuccess
from truss import LocalPostgres,Ok,CatalogDocument,CatalogRegistration,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly,ObjectFound,QueryRows

@unittest.skipUnless(os.environ.get('TRUSS_RECURSIVE_UPGRADE_SOURCE_PACKAGE'),'Native63 predecessor required')
class RecursiveUpgradeTests(unittest.TestCase):
    def test_preserve_original_report_then_backfill_key(self):
        with tempfile.TemporaryDirectory(prefix='truss-key-upgrade-') as directory:
            with LocalPostgres(Path(directory)/'data') as runtime:
                artifact=Path(directory)/'original.pickle';tests=Path(__file__).parent.resolve()
                env={**os.environ,'PYTHONPATH':os.environ['TRUSS_RECURSIVE_UPGRADE_SOURCE_PACKAGE']+os.pathsep+str(tests)}
                subprocess.run([sys.executable,str(tests/'_seed_recursive_upgrade_063.py'),runtime.info.connection_uri,str(artifact)],env=env,check=True,timeout=120)
                document,identity,revision,report=pickle.loads(artifact.read_bytes())
                self.assertEqual(json.loads(report)['keyBackfillProfile'],'truss-catalog-key-backfill/0.1')
                with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=10000') as admin:
                    admin.execute('BEGIN');host=adopt_psycopg_host(admin,statement_timeout_ms=10000,operation_timeout_ms=30000);assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                    upgraded=assembly.upgrade_in_transaction(tx)
                    self.assertIsInstance(upgraded,Ok,repr(upgraded)+' '+str(host._custody.last_attempt.error))
                    self.assertEqual(upgraded.value.previous_release_id,'truss-catalog-runtime/0.63-candidate')
                    from truss.catalog_runtime import _release
                    self.assertEqual(upgraded.value.release_id,_release()[0]['releaseId'])
                    self.assertEqual(upgraded.value.outcome,'upgraded')
                    host.detach();admin.commit()
                params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri);params['user']='consumer'
                with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as connection:
                    connection.execute('BEGIN');host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                    self.assertEqual(assembly.report_in_transaction(tx,revision).value.original_bytes,report)
                    source=json.loads(document.content)
                    module=source['modules'][0]
                    module['elements'] += [
                        {'id':'nestedData','name':'nestedData','kind':'field','cardinality':'map','nullability':'absent-allowed','itemType':{'module':'m','element':'nestedSequence'},'extensions':{}},
                        {'id':'nestedSequence','name':'nestedSequence','kind':'field','cardinality':'array','nullability':'required','itemType':{'module':'m','element':'nestedDecimal'},'extensions':{}},
                        {'id':'nestedDecimal','name':'nestedDecimal','kind':'field','cardinality':'one','nullability':'required','scalarType':'decimal','facets':{'precision':18,'scale':4},'extensions':{}}]
                    next(e for e in module['elements'] if e['id']=='A')['members'].append({'module':'m','element':'nestedData'})
                    prepared=assembly.prepare_catalog((CatalogDocument('adoc','r3',json.dumps(source).encode()),),source_version='0.8.0',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    accepted=assembly.accept_in_transaction(tx,prepared,request_key='upgraded-key',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    self.assertIsInstance(accepted,Ok,repr(accepted)+' '+str(host._custody.last_attempt.error));self.assertIsInstance(accepted.value,CatalogRegistration)
                    found=assembly.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id='a-backfill',values=('value',),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    self.assertIsInstance(found.value,ObjectFound,repr(found));self.assertEqual(found.value.object.id,int(identity.id));self.assertEqual(found.value.object.version,1)
                    self.assertEqual(assembly.report_in_transaction(tx,revision).value.original_bytes,report)
                    context=assembly.group_context_in_transaction(tx).value
                    nested=MapValue(entries=(MapEntry(key='values',value=SequenceValue(items=(TextValue(kind='decimal',text='1.23000'),))),))
                    update=UpdateObject(target=StoredObjectReference(identity=found.value.object.identity),set=(AuthoredValue(name='nestedData',value=nested),),unset=())
                    updated=assembly.apply_in_transaction(tx,context.input((update,),MapValue(entries=())),context.request('upgraded-nested-write'),documents=(CatalogDocument('adoc','r3',json.dumps(source).encode()),),bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
                    self.assertIsInstance(updated.value,GroupSuccess,repr(updated))
                    query=assembly.query_in_transaction(tx,sql='SELECT a."nestedData" FROM "A" a',document_ids=('adoc',))
                    self.assertIsInstance(query.value,QueryRows,repr(query));self.assertEqual(str(query.value.rows[0][0]['values'][0]),'1.23000')
                    self.assertEqual(assembly.report_in_transaction(tx,revision).value.original_bytes,report)
                    host.detach();connection.commit()
