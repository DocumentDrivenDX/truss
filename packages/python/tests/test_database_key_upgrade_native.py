"""Genuine predecessor → database-derived keys, preserving stored key/context bytes."""
import json,os,pickle,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import psycopg
from truss.catalog_runtime import _release
from truss import LocalPostgres,Ok,CatalogDocument,CatalogRegistration,ObjectFound,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import MapValue,TextValue
from truss.groups import UpdateObject,StoredObjectReference,AuthoredValue,RequestNone,GroupSuccess

@unittest.skipUnless(os.environ.get('TRUSS_DB_KEY_PREDECESSOR'),'Original native65 package required')
class DatabaseKeyUpgradeTests(unittest.TestCase):
    def test_upgrade_preserves_original_key_bytes_and_derives_new_keys(self):
        with tempfile.TemporaryDirectory(prefix='truss-db-key-upgrade-') as directory:
            with LocalPostgres(Path(directory)/'data') as runtime:
                artifact=Path(directory)/'original.pickle';tests=Path(__file__).parent.resolve()
                env={**os.environ,'PYTHONPATH':os.environ['TRUSS_DB_KEY_PREDECESSOR']+os.pathsep+str(tests)}
                subprocess.run([sys.executable,str(tests/'_seed_database_key_upgrade.py'),runtime.info.connection_uri,str(artifact)],env=env,check=True,timeout=120)
                documents,identity,keys,reservations=pickle.loads(artifact.read_bytes())
                with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=10000') as admin:
                    admin.execute('BEGIN');h=adopt_psycopg_host(admin);a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value;t=h.adopt_transaction().value
                    upgraded=a.upgrade_in_transaction(t)
                    self.assertIsInstance(upgraded,Ok,repr(upgraded)+' '+str(h._custody.last_attempt.error))
                    self.assertEqual(upgraded.value.release_id,_release()[0]['releaseId'])
                    h.detach();admin.commit()
                    self.assertEqual(admin.execute("""SELECT count(*) FROM pg_proc WHERE pronamespace='truss'::regnamespace
                        AND proname IN ('query_export_objects','query_export_edges','query_export_page_objects')
                        AND proowner=(SELECT owner_oid FROM truss.catalog_runtime_installation)
                        AND has_function_privilege('consumer',oid,'EXECUTE')""").fetchone(), (3,))
                    self.assertEqual(admin.execute('SELECT storage_row_id,namespace_bytes,key_bytes,original_context_bytes FROM truss.object_key_bucket ORDER BY storage_row_id').fetchall(),keys)
                    self.assertEqual(admin.execute('SELECT storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes FROM truss.object_key_reservation_bucket ORDER BY storage_row_id').fetchall(),reservations)
                    for _,_,_,raw in keys:
                        original_context=json.loads(raw)
                        if original_context.get('profile')=='truss-created-key-context/0.2':
                            self.assertEqual(original_context['derivation'],'postgresql-umf-key-tuple-v1')
                        else:self.assertIn('ownerReceiptBase64',original_context)
                    params=psycopg.conninfo.conninfo_to_dict(runtime.info.connection_uri);params['user']='consumer'
                    with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as c:
                        c.execute('BEGIN');h=adopt_psycopg_host(c);a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value;t=h.adopt_transaction().value
                        with patch('truss._umf_key_tuples.encode_key_tuples',side_effect=AssertionError('client encoder')):
                            found=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('legacy-value','legacy-é'),bun_executable='/missing/bun')
                            self.assertIsInstance(found.value,ObjectFound,repr(found))
                            context=a.group_context_in_transaction(t).value
                            op=UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='native-new')),),unset=(),expected_version='1')
                            updated=a.apply_in_transaction(t,context.input((op,),MapValue(entries=())),RequestNone(),documents=documents,bun_executable='/missing/bun')
                            self.assertIsInstance(updated.value,GroupSuccess,repr(updated)+' '+str(h._custody.last_attempt.error))
                            found=a.lookup_key_in_transaction(t,document_id='adoc',module_id='m',record_id='A',key_id='a-primary',values=('legacy-value','native-new'))
                            self.assertIsInstance(found.value,ObjectFound)
                        h.detach();c.commit()
                    # Historical reservations remain original; new contexts carry no owner receipt.
                    for (raw,) in admin.execute("SELECT original_context_bytes FROM truss.object_key_bucket WHERE object_id=%s",(int(identity.id),)):
                        self.assertEqual(json.loads(raw)['profile'],'truss-updated-key-context/0.2')
