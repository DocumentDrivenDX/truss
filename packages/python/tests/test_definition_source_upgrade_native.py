# SPDX-License-Identifier: MIT OR Apache-2.0
"""Populated published native71 upgrade preserves originals and derives exact pins."""
import os,pickle,subprocess,sys,tempfile,unittest
from pathlib import Path
import psycopg
from truss import LocalPostgres,Ok,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration

@unittest.skipUnless(os.environ.get('TRUSS_NATIVE71_PACKAGE'),'Installed published native71 package required')
class DefinitionSourceUpgradeTests(unittest.TestCase):
    def test_populated_upgrade_is_atomic_and_preserves_exact_definition_pins(self):
        with tempfile.TemporaryDirectory(prefix='truss-native71-upgrade-') as directory:
            with LocalPostgres(Path(directory)/'data') as runtime:
                snapshot=Path(directory)/'source.pickle';tests=Path(__file__).parent.resolve()
                env={**os.environ,'PYTHONPATH':os.environ['TRUSS_NATIVE71_PACKAGE']+os.pathsep+str(tests)}
                subprocess.run([sys.executable,str(tests/'_seed_import_source_upgrade.py'),runtime.info.connection_uri,str(snapshot)],env=env,check=True,timeout=120)
                _,_,identities=pickle.loads(snapshot.read_bytes())
                with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=10000') as admin:
                    tables=('schema_doc','catalog_acceptance_report','object','journal','runtime_import_source','record_source','request_receipt')
                    before={t:admin.execute('SELECT to_jsonb(t) FROM truss.'+t+' t ORDER BY to_jsonb(t)::text').fetchall() for t in tables}
                    pins=admin.execute("SELECT t.type_id,p.definition_pin,p.original_fragment,p.original_pointer FROM truss.type_def t CROSS JOIN LATERAL truss.runtime_definition('type',t.type_id) p ORDER BY t.type_id").fetchall()
                    for commit in (False,True):
                        admin.execute('BEGIN');host=adopt_psycopg_host(admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
                        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;tx=host.adopt_transaction().value
                        result=assembly.upgrade_in_transaction(tx)
                        self.assertIsInstance(result,Ok,repr(result)+' '+str(host._custody.last_attempt.error))
                        for t in tables:self.assertEqual(admin.execute('SELECT to_jsonb(t) FROM truss.'+t+' t ORDER BY to_jsonb(t)::text').fetchall(),before[t],t)
                        self.assertEqual(admin.execute("SELECT t.type_id,p.definition_pin,p.original_fragment,p.original_pointer FROM truss.type_def t CROSS JOIN LATERAL truss.runtime_definition('type',t.type_id) p ORDER BY t.type_id").fetchall(),pins)
                        self.assertGreater(admin.execute('SELECT count(*) FROM truss.runtime_definition_source').fetchone()[0],0)
                        host.detach()
                        if commit:admin.commit()
                        else:
                            admin.rollback();self.assertIsNone(admin.execute("SELECT to_regclass('truss.runtime_definition_source')").fetchone()[0])
                    self.assertEqual(admin.execute('SELECT release_id FROM truss.catalog_runtime_installation').fetchone()[0],'truss-catalog-runtime/0.71-candidate')
                    self.assertEqual(admin.execute('SELECT release_id FROM truss.runtime_current_installation()').fetchone()[0],'truss-catalog-runtime/0.72-candidate')
