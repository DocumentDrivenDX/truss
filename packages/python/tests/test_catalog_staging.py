"""Real Python catalog effects on administrative native component custody."""
import dataclasses
import json
from pathlib import Path
import unittest
from test_native_pg8000 import NativeBoundaryFixture
from test_preparation import prepare,document
from truss.preparation import _require_original_preparation, CatalogDocument
from truss._catalog_staging import stage_new_catalog, CatalogStagingCleanupFailure
def native_document(identity):
    original=document(identity)
    value=json.loads(original.content)
    value['modules'][0]['elements'][1]['name']='label'
    return CatalogDocument(identity,'r1',json.dumps(value).encode())

ROOT=Path(__file__).resolve().parents[3]
COMPONENTS=['operation-admission','operation-commit-barrier','catalog-generation-observer','catalog-document-batch','catalog-lineage-producer','catalog-source-integrity','catalog-type-match','catalog-type-stage','catalog-property-match','catalog-property-stage','catalog-key-match','catalog-key-stage','catalog-key-batch','catalog-relationship-match','catalog-relationship-stage','catalog-report-documents','catalog-new-inventory','catalog-observation-recheck','catalog-input-custody','catalog-prestate-capture','catalog-new-prestate-parity','catalog-new-counts','catalog-provisional-empty','catalog-report-immutability','catalog-original-context']

class CatalogPreparationCustodyTests(unittest.TestCase):
    def test_original_and_copy(self):
        value=prepare((document('original'),))
        _require_original_preparation(value)
        with self.assertRaises(ValueError):_require_original_preparation(dataclasses.replace(value))
    def test_mutated_bytes(self):
        for field in ('input_bytes','declarations_bytes','archive_documents_bytes','report_evidence_bytes'):
            with self.subTest(field=field):
                value=prepare((document('original'),))
                object.__setattr__(value,field,getattr(value,field)+b' ')
                with self.assertRaises(ValueError):_require_original_preparation(value)

    def test_forged_preparation_refuses_before_sql(self):
        class NoCalls:
            def run(self,*args,**kwargs):raise AssertionError('SQL must not run')
        value=prepare((document('original'),))
        with self.assertRaises(ValueError):
            stage_new_catalog(NoCalls(),dataclasses.replace(value),origin_bytes=b'{}')
    def test_spoofed_bytes_and_nested_originals_refuse(self):
        class EqualBytes(bytes):
            def __eq__(self,other):return True
        for target,field in (('prepared','declarations_bytes'),('document','content'),('observation','observation_bytes'),('provenance','owner_revision')):
            value=prepare((document('original'),))
            item={'prepared':value,'document':value.documents[0].document,'observation':value.documents[0],'provenance':value.provenance}[target]
            replacement='changed' if target=='provenance' else EqualBytes(b'[]')
            object.__setattr__(item,field,replacement)
            with self.assertRaises(ValueError):_require_original_preparation(value)
    def test_ambiguous_or_numeric_origin_refuses_before_sql(self):
        class NoCalls:
            def run(self,*args,**kwargs):raise AssertionError('SQL must not run')
        value=prepare((document('original'),))
        for wire in (b'{"value":9007199254740993.0}',b'{"source":"first","source":"last"}',b'{"value":NaN}'):
            with self.assertRaises(ValueError):stage_new_catalog(NoCalls(),value,origin_bytes=wire)

    def test_cleanup_failure_retains_primary_without_claiming_containment(self):
        primary=RuntimeError('original stage failure')
        for command in ('ROLLBACK TO','RELEASE'):
            cleanup=RuntimeError('lost cleanup reply')
            class FailingPort:
                def run(self,sql,**parameters):
                    if sql.startswith('SELECT'):raise primary
                    if sql.startswith(command):raise cleanup
            with self.assertRaises(CatalogStagingCleanupFailure) as caught:
                stage_new_catalog(FailingPort(),prepare((document('original'),)),origin_bytes=b'{}')
            self.assertIs(caught.exception.primary_failure,primary)
            self.assertIs(caught.exception.cleanup_failure,cleanup)
            self.assertFalse(caught.exception.containment_confirmed)

class CatalogNativeFixture(NativeBoundaryFixture):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:
            c.run((ROOT/'docs/helix/04-build/evidence/qualified-property-layout-0.15.owner-export.sql').read_text())
            for component in COMPONENTS:c.run((ROOT/f'packages/postgresql/native/{component}.sql').read_text())
            c.run((ROOT/'packages/postgresql/native/edge-limit/verify-current-scope.sql').read_text())
        finally:c.close()
    def setUp(self):
        self.connection=self.Connection(**self.kwargs)
        self.prepared=prepare((native_document('catalog'),))
        self.connection.run('BEGIN')
        self.admit(self.prepared)
    def admit(self, prepared):
        prestate=self.connection.run('SELECT truss.runtime_capture_catalog_prestate()')[0][0]
        self.connection.run("SELECT * FROM truss.runtime_admit_operation('catalog-acceptance',decode('01','hex'),decode(:input,'hex'),decode(:prestate,'hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'))",input=prepared.input_bytes.hex(),prestate=prestate)
    def tearDown(self):
        self.connection.run('ROLLBACK');self.connection.close()
    def stage(self,prepared=None):
        return stage_new_catalog(self.connection,self.prepared if prepared is None else prepared,origin_bytes=b'{"source":"native-component"}')
class NativeCatalogStagingTests(CatalogNativeFixture,unittest.TestCase):
    def test_actual_ids_inventory_counts_and_host_rollback(self):
        result=self.stage()
        self.assertEqual(result.scope,'verified_provisional_new_catalog_only')
        inventory=json.loads(result.inventory_bytes)
        self.assertEqual(sorted(r['family'] for r in inventory),['property','type'])
        self.assertEqual(json.loads(result.counts_bytes),{'types_added':'1','properties_added':'1','keys_added':'0','relationships_added':'0','endpoints_added':'0','elements_retired':'0'})
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
        self.assertEqual(self.connection.run('SELECT home FROM truss.prop_def'),[['json']])
        self.connection.run('ROLLBACK')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.schema_doc'),[[0]])
    def test_different_original_input_is_contained(self):
        from pg8000.exceptions import DatabaseError
        other=prepare((document('different'),))
        with self.assertRaises(DatabaseError):self.stage(other)
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.schema_rev'),[[1]])
        self.assertEqual(self.connection.run('SELECT 42'),[[42]])
    def test_original_consumer_core_stages_all_records_fields_and_keys(self):
        self.connection.run('ROLLBACK');self.connection.run('BEGIN')
        source=(ROOT/'packages/python/tests/fixtures/security-association-core.json').read_bytes()
        original=prepare((CatalogDocument('domain','schema-natural-1',source),))
        self.admit(original)
        result=self.stage(original)
        self.assertEqual(json.loads(result.counts_bytes),{'types_added':'5','properties_added':'9','keys_added':'5','relationships_added':'0','endpoints_added':'0','elements_retired':'0'})
        self.assertEqual(self.connection.run('SELECT document FROM truss.schema_doc WHERE rev=CAST(:rev AS int)',rev=result.revision),[[source.decode()]])
    def test_relationship_endpoints_resolve_actual_allocated_records(self):
        self.connection.run('ROLLBACK');self.connection.run('BEGIN')
        value={'umf':'0.7.0','id':'cohort','vocabularies':{},'extensions':{},'modules':[{'id':'m','namespace':'m','elements':[
            *[{'id':name,'kind':'record','members':[{'module':'m','element':name+'-label'}],'keys':[{'id':'label-key','name':'label-key','fields':[{'module':'m','element':name+'-label'}],'primary':True}],'extensions':{}} for name in ('A','B')],
            *[{'id':name+'-label','name':name+'-label','kind':'field','scalarType':'string','nullability':'required','cardinality':'one','extensions':{}} for name in ('A','B')]],
            'relationships':[{'id':'A-B','name':'A-B','source':[{'module':'m','element':'A'}],'target':[{'module':'m','element':'B','key':'label-key'}],'sourceMultiplicity':{'min':0,'max':1},'targetMultiplicity':{'min':0,'max':2},'targetLifecycle':'independent','directed':True}]}]}
        original=prepare((CatalogDocument('cohort','r1',json.dumps(value).encode()),))
        self.admit(original);result=self.stage(original)
        self.assertEqual(json.loads(result.counts_bytes),{'types_added':'2','properties_added':'2','keys_added':'2','relationships_added':'1','endpoints_added':'1','elements_retired':'0'})
        endpoints=self.connection.run('SELECT e.source_type::text,e.target_type::text,s.element,t.element FROM truss.rel_endpoint e JOIN truss.type_def s ON s.type_id=e.source_type JOIN truss.type_def t ON t.type_id=e.target_type')
        self.assertEqual(len(endpoints),1);self.assertEqual(endpoints[0][2:],['A','B'])
        self.assertNotEqual(endpoints[0][0],endpoints[0][1])
    def test_late_home_corruption_rolls_back_complete_cohort_and_keeps_host_work(self):
        self.connection.run('CREATE TEMP TABLE host_work(value text)')
        self.connection.run("INSERT INTO host_work VALUES('preserve')")
        original=self.connection
        class AlteredPort:
            @property
            def columns(self):return original.columns
            def run(self,sql,**parameters):
                if sql.startswith('SELECT prop_id::pg_catalog.text AS property_id,type_id::pg_catalog.text AS owner_type_id,home FROM truss.prop_def'):
                    original.run("UPDATE truss.prop_def SET home='row'")
                return original.run(sql,**parameters)
        with self.assertRaises(ValueError):
            stage_new_catalog(AlteredPort(),self.prepared,origin_bytes=b'{}')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.schema_doc'),[[0]])
        self.assertEqual(self.connection.run('SELECT value FROM host_work'),[['preserve']])
        self.assertEqual(self.connection.run('SELECT effect_generation::text,phase FROM truss.row_home_operation'),[['0','admitted']])
    def test_commit_barrier_stays_closed(self):
        from pg8000.exceptions import DatabaseError
        self.stage()
        with self.assertRaises(DatabaseError) as failure:self.connection.run('COMMIT')
        self.assertEqual(failure.exception.args[0]['C'],'55000')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
