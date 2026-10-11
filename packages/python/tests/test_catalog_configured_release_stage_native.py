"""Configured native stage/source composition. Administrative fixtures, no PA authority."""
import copy,hashlib,json,unittest
from test_native_pg8000 import NativeBoundaryFixture
from test_catalog_staging import ROOT,COMPONENTS
from test_catalog_support import selected
from truss._native_catalog_request import NativeCatalogStageInput,encode_catalog_stage
from truss._native_catalog_report_sources import compose_captured_catalog_sources

class ConfiguredReleaseStageNativeTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass();c=cls.Connection(**cls.kwargs)
        try:
            c.run('DROP SCHEMA IF EXISTS truss CASCADE')
            c.run((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text())
            c.run((ROOT/'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql').read_text())
            for name in COMPONENTS:
                if name!='operation-admission':c.run((ROOT/f'packages/postgresql/native/{name}.sql').read_text())
            for name in ('source-epoch-lock','issued-operation-admission/operation-admission',
                         'issued-operation-admission/operation-configuration-context-admission',
                         'catalog-epoch-context','operation-configuration-current','catalog-admission-configuration',
                         'catalog-report/release-selection','catalog-report/empty-graph',
                         'catalog-report/configured-graph','catalog-report/absent-binding-index-declarations',
                         'catalog-report/fresh-lifecycle','edge-limit/verify-current-scope',
                         'catalog-stage-issued','catalog-report/configured-stage'):
                c.run((ROOT/f'packages/postgresql/native/{name}.sql').read_text())
            fixture=(ROOT/'docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql').read_text()
            c.run(fixture.split('INSERT INTO truss.row_home_operation')[0])
            c.run("INSERT INTO truss.source_epoch_current VALUES(1,'guard-fixture','guard-fixture-epoch')")
        finally:c.close()
    @classmethod
    def tearDownClass(cls):
        c=cls.Connection(**cls.kwargs)
        try:c.run('DROP SCHEMA truss CASCADE')
        finally:c.close()
        super().tearDownClass()
    def setUp(self):
        self.connection=self.Connection(**self.kwargs);self.prepared=selected()
        self.policy=(ROOT/'packages/python/src/truss/_profiles/catalog-report-release.json').read_bytes()
        self.profile=(ROOT/'packages/python/src/truss/_profiles/catalog-report-configuration.json').read_bytes()
        self.configuration=json.dumps({'interfaceVersion':'truss-catalog-report-configuration/0.1',
            'catalogReportRelease':{'artifactIdentity':'truss.catalog-report-release/0.1.0',
                                  'sha256':hashlib.sha256(self.policy).hexdigest()}}).encode()
        self.connection.run("""INSERT INTO truss.installation_admission(head_id,installation_id_utf8,
            source_epoch_utf8,configuration_generation,key_reuse,journal_mode,configuration_bytes,
            selected_binding_bytes,installed_inventory_bytes) VALUES(1,convert_to('guard-fixture','UTF8'),
            convert_to('guard-fixture-epoch','UTF8'),7,'forbid','engine',:configuration,
            convert_to('binding fixture','UTF8'),convert_to('inventory fixture','UTF8'))""",configuration=self.configuration)
        self.connection.run('BEGIN')
    def tearDown(self):
        self.connection.run('ROLLBACK');self.connection.run('DELETE FROM truss.installation_admission');self.connection.close()
    def archive(self):
        self.connection.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,
            artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',
            'truss.catalog-report-release/0.1.0',:raw,sha256(convert_to('truss.catalog-report-release/0.1.0','UTF8')))""",raw=self.policy)
    def admit(self):
        p=self.prepared;pre=self.connection.run('SELECT truss.runtime_capture_catalog_prestate()')[0][0]
        writer,ordinal,context=self.connection.run("""SELECT * FROM truss.runtime_admit_operation_with_configuration_context(
            0,'catalog-acceptance',decode('01','hex'),:input,decode(:pre,'hex'),:candidate,
            decode('05','hex'),decode('06','hex'),convert_to('{}','UTF8'),
            convert_to('original capture fixture','UTF8'),'guard-fixture','guard-fixture-epoch',
            'guard-fixture-incarnation',:profile)""",input=p.input_bytes,pre=pre,candidate=p.declarations_bytes,profile=self.profile)[0]
        self.context=bytes.fromhex(context);self.prestate=bytes.fromhex(pre);return writer,ordinal
    def invoke(self):
        p=self.prepared
        rows=self.connection.run("""SELECT * FROM truss.runtime_stage_catalog_with_release(0,
            decode('01','hex'),:input,:candidate,decode('05','hex'),decode('06','hex'),
            :documents,:candidate,convert_to('{}','UTF8'),:pre,:context,:profile)""",
            input=p.input_bytes,candidate=p.declarations_bytes,documents=p.archive_documents_bytes,
            pre=self.prestate,context=self.context,profile=self.profile)
        self.result=json.loads(bytes.fromhex(rows[0][3]));return rows[0]
    def compose(self,result=None,context=None):
        value=NativeCatalogStageInput(self.prepared,b'{}',b'\x01',b'\x05',b'\x06')
        encoded=encode_catalog_stage(value,'0')
        return compose_captured_catalog_sources(encoded,self.result if result is None else result,
            self.context if context is None else context)
    def test_one_configured_native_stage_retains_release_and_metadata(self):
        self.archive();writer,ordinal=self.admit();row=self.invoke();snapshot=self.compose()
        result=self.result;source=result['reportSources']['catalogRelease']
        self.assertEqual((row[0],row[1]),(writer,ordinal))
        self.assertEqual(result['interfaceVersion'],'truss-native-provisional-catalog/0.3')
        self.assertEqual(source['policyHex'],self.policy.hex());self.assertEqual(source['configurationGeneration'],'7')
        self.assertEqual(source['effectGeneration'],result['effectGeneration'])
        self.assertEqual(result['reportSources']['start']['metadata_source'],result['reportSources']['end']['metadata_source'])
        payload=json.loads(snapshot.snapshot_bytes);assembly=json.loads(snapshot.assembly_bytes)
        self.assertFalse(payload['configuredReleaseCandidate']['registeredAuthority'])
        self.assertEqual(len(assembly['requiredSources']),4);self.assertIsNone(assembly['completeReportBytes'])
        self.assertEqual(self.connection.run('SELECT home FROM truss.prop_def'),[['json']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        self.connection.run('ROLLBACK')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.operation_configuration'),[[0]])
    def test_missing_release_refuses_before_any_catalog_effect(self):
        from pg8000.exceptions import DatabaseError
        self.admit()
        self.connection.run("CREATE TEMP SEQUENCE catalog_first_effect; CREATE FUNCTION truss.fixture_first_effect() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM nextval('pg_temp.catalog_first_effect'); RETURN NEW; END $$; CREATE TRIGGER fixture_first_effect BEFORE INSERT ON truss.schema_rev FOR EACH ROW EXECUTE FUNCTION truss.fixture_first_effect()")
        self.connection.run('SAVEPOINT attempt')
        with self.assertRaises(DatabaseError) as caught:self.invoke()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.assertEqual(caught.exception.args[0]['M'],'unique original report release archive required')
        self.connection.run('ROLLBACK TO SAVEPOINT attempt')
        self.assertEqual(self.connection.run('SELECT is_called FROM pg_temp.catalog_first_effect'),[[False]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])
    def test_uncovered_or_populated_graph_still_refuses(self):
        from pg8000.exceptions import DatabaseError
        self.archive();self.admit()
        for statement in ('CREATE TABLE truss.uncovered(value text)',
                          "INSERT INTO truss.request_receipt_route_guard VALUES(decode(repeat('00',32),'hex'),decode(repeat('01',32),'hex'),0)"):
            self.connection.run('SAVEPOINT graph');self.connection.run(statement)
            with self.assertRaises(DatabaseError):self.invoke()
            self.connection.run('ROLLBACK TO SAVEPOINT graph');self.connection.run('RELEASE SAVEPOINT graph')
    def test_configured_source_substitutions_never_issue_report(self):
        self.archive();self.admit();self.invoke()
        for path,value in ((('catalogRelease','policyHex'),'00'),(('catalogRelease','configurationGeneration'),'8'),
                           (('catalogRelease','effectGeneration'),'0'),(('end','metadata_source'),'{}')):
            changed=copy.deepcopy(self.result);changed['reportSources'][path[0]][path[1]]=value
            with self.assertRaises(ValueError):self.compose(changed)
        changed=json.loads(self.context);changed['sourceEpoch']='other'
        with self.assertRaises(ValueError):self.compose(context=json.dumps(changed).encode())
        changed=copy.deepcopy(self.result);del changed['reportSources']['catalogRelease']
        with self.assertRaises(ValueError):self.compose(changed)
