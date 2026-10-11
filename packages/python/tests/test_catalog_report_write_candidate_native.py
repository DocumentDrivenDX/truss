"""Actual native report INSERT/readback algorithm; every fixture rolls back.

The explicit candidate recipe is not an installed authority producer. These
checks cannot activate public catalog APIs, publish head/feed, or permit commit.
"""
import copy
import hashlib
import json
import unittest
import test_catalog_configured_release_stage_native as fixture
from test_catalog_staging import ROOT
from truss._acceptance_json import decode_acceptance_json
from truss._catalog_report_assembly import encode_unissued_complete_report_wire, ENFORCEMENT_SHA256
from truss._catalog_report_semantics import canonical_numeric_free
from truss._report_schema import validate_complete_report


class ReportWriteCandidateNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ConfiguredReleaseStageNativeTests.setUpClass()
        cls.Connection=fixture.ConfiguredReleaseStageNativeTests.Connection
        cls.kwargs=fixture.ConfiguredReleaseStageNativeTests.kwargs
        c=cls.Connection(**cls.kwargs)
        try:
            c.run((ROOT/'packages/postgresql/native/catalog-report/report-write-candidate.sql').read_text())
        finally:c.close()
    @classmethod
    def tearDownClass(cls):fixture.ConfiguredReleaseStageNativeTests.tearDownClass()
    setUp=fixture.ConfiguredReleaseStageNativeTests.setUp
    tearDown=fixture.ConfiguredReleaseStageNativeTests.tearDown
    archive=fixture.ConfiguredReleaseStageNativeTests.archive

    def stage(self):
        self.archive()
        recipe_path='packages/python/src/truss/_profiles/catalog-report-composition-candidate.json'
        recipe_bytes=(ROOT/recipe_path).read_bytes();recipe=json.loads(recipe_bytes)
        self.registration={'interfaceVersion':'truss-catalog-report-candidate-registration/0.1',
            'scope':'administrative_rollback_only_report_write',
            'layoutProfile':self.prepared.input()['layoutProfile'],
            'composition':{'identity':recipe_path,'sha256':hashlib.sha256(recipe_bytes).hexdigest()}}
        artifacts=[(recipe_path,recipe_bytes)]
        for field,ref in recipe['profileArtifacts'].items():
            raw=(ROOT/ref['path']).read_bytes();profile=json.loads(raw)
            self.registration[field]={'identity':profile['identity'],'version':profile['version'],
                'sha256':hashlib.sha256(raw).hexdigest()}
            artifacts.append((ref['path'],raw))
            if field=='captureProfile':self.capture_bytes=raw
        for identity,raw in artifacts:
            # Enforcement/mapping are already in the declared release archive.
            if self.connection.run('SELECT count(*) FROM truss.installation_archive WHERE artifact_identity=:identity',identity=identity)[0][0]:continue
            self.connection.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,
                artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',
                :identity,:raw,sha256(convert_to(:identity,'UTF8')))""",identity=identity,raw=raw)
        self.registration_bytes=canonical_numeric_free(self.registration)
        self.identity='fixture.catalog-report-composition/0.1'
        self.connection.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,
            artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',
            :identity,:raw,sha256(convert_to(:identity,'UTF8')))""",identity=self.identity,raw=self.registration_bytes)
        self.writer,self.ordinal=self.admit()
        if getattr(self,'skip_stage',False):return
        self.invoke()
        from truss._catalog_report_assembly import assemble_catalog_report_sources
        from truss._catalog_report_semantics import compose_catalog_report_semantics
        from truss._catalog_support import evaluate_catalog_support
        self.original_assembly=assemble_catalog_report_sources(self.prepared,self.result,
            compose_catalog_report_semantics(self.prepared,evaluate_catalog_support(self.prepared),self.result['revision']))
        self.generation=self.result['effectGeneration']

    def admit(self):
        from truss._catalog_candidate import encode_original_catalog_candidate
        p=self.prepared;pre=self.connection.run('SELECT truss.runtime_capture_catalog_prestate()')[0][0]
        candidate=json.loads(encode_original_catalog_candidate(p))
        if hasattr(self,'candidate_transform'):self.candidate_transform(candidate)
        self.candidate_bytes=canonical_numeric_free(candidate)
        self.origin_bytes=getattr(self,'origin_bytes',b'{}')
        writer,ordinal,context=self.connection.run("""SELECT * FROM truss.runtime_admit_operation_with_configuration_context(
            0,'catalog-acceptance',decode('01','hex'),:input,decode(:pre,'hex'),:candidate,
            decode('05','hex'),decode('06','hex'),:origin,
            :capture,'guard-fixture','guard-fixture-epoch','guard-fixture-incarnation',:profile)""",
            input=p.input_bytes,pre=pre,candidate=self.candidate_bytes,origin=self.origin_bytes,capture=self.capture_bytes,profile=self.profile)[0]
        self.context=bytes.fromhex(context);self.prestate=bytes.fromhex(pre);return writer,ordinal

    def invoke(self):
        p=self.prepared
        rows=self.connection.run("""SELECT * FROM truss.runtime_stage_catalog_with_release(0,
            decode('01','hex'),:input,:candidate,decode('05','hex'),decode('06','hex'),
            :documents,:declarations,:origin,:pre,:context,:profile)""",
            input=p.input_bytes,candidate=self.candidate_bytes,declarations=p.declarations_bytes,documents=p.archive_documents_bytes,
            origin=self.origin_bytes,pre=self.prestate,context=self.context,profile=self.profile)
        self.result=json.loads(bytes.fromhex(rows[0][3]));return rows[0]

    def write(self,raw=None,identity=None,generation=None):
        return self.connection.run("""SELECT * FROM truss.runtime_write_catalog_report_candidate(
            :writer,:ordinal,:generation,:identity,:registration,:lifecycle,:indexes)""",
            writer=self.writer,ordinal=self.ordinal,generation=self.generation if generation is None else generation,
            identity=self.identity if identity is None else identity,
            registration=self.registration_bytes if raw is None else raw,
            lifecycle=(ROOT/'packages/python/src/truss/_profiles/fresh-catalog-lifecycle.json').read_bytes(),
            indexes=(ROOT/'packages/python/src/truss/_profiles/absent-binding-index-declarations.json').read_bytes())[0]

    def test_complete_report_native_construction_insert_and_readback(self):
        self.stage();row=self.write()
        wire=bytes.fromhex(row[3]);report=decode_acceptance_json(wire)
        self.assertEqual(row[:2],[self.writer,self.ordinal])
        self.assertEqual(row[2],str(int(self.generation)+1))
        self.assertEqual(row[4:],[self.registration['scope'],False])
        self.assertEqual(len(report),19)
        validate_complete_report(report)
        context=json.loads(self.context)
        execution={'installationId':context['installationId'],'sourceEpoch':context['sourceEpoch'],
            'origin':{'asserted':{},'databaseRole':context['actingUser']},
            'journalOrigin':{'asserted':{'kind':'map','entries':[]},'databaseRole':context['actingUser']},
            'originMappingProfile':self.registration['originMappingProfile'],
            'captureProfile':self.registration['captureProfile'],
            'contextEvidence':{'identity':f'truss.original-native-operation-context4/{self.writer}/{self.ordinal}',
                'bytesBase64':__import__('base64').b64encode(self.context).decode(),
                'sha256':hashlib.sha256(self.context).hexdigest()}}
        sources={'originalInstalledExecution':execution,'admittedLayout':self.registration['layoutProfile'],
            'registeredEnforcementReportProfile':self.registration['enforcementProfile'],
            'registeredAcceptanceReportProfile':self.registration['reportProfile']}
        expected=encode_unissued_complete_report_wire(self.original_assembly,sources)
        self.assertEqual(wire,bytes.fromhex(expected.original_utf8_hex))
        self.assertEqual(self.connection.run('SELECT report_bytes FROM truss.catalog_acceptance_report'),[[wire]])
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.feed_tx'),[[0]])
        self.assertEqual(self.connection.run('SELECT phase FROM truss.row_home_operation'),[['admitted']])

    def test_missing_changed_duplicate_registration_and_production_scope_refuse(self):
        from pg8000.exceptions import DatabaseError
        self.stage()
        cases=[('missing',self.registration_bytes),('changed',self.registration_bytes+b' ')]
        changed=copy.deepcopy(self.registration);changed['scope']='installed_report_authority'
        cases.append(('scope',canonical_numeric_free(changed)))
        for kind,raw in cases:
            self.connection.run('SAVEPOINT refusal')
            try:
                with self.subTest(kind=kind),self.assertRaises(DatabaseError):
                    self.write(raw=raw,identity='absent' if kind=='missing' else None)
            finally:self.connection.run('ROLLBACK TO refusal');self.connection.run('RELEASE refusal')
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
        self.connection.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,
            artifact_bytes,artifact_identity_sha256) SELECT installation_id,artifact_role,artifact_identity,
            artifact_bytes,artifact_identity_sha256 FROM truss.installation_archive WHERE artifact_identity=:identity""",identity=self.identity)
        with self.assertRaises(DatabaseError) as caught:self.write()
        self.assertEqual(caught.exception.args[0]['M'],'unique original candidate registration archive required')

    def test_stale_generation_and_second_write_refuse(self):
        from pg8000.exceptions import DatabaseError
        self.stage();self.connection.run('SAVEPOINT stale')
        with self.assertRaises(DatabaseError):self.write(generation=str(int(self.generation)+1))
        self.connection.run('ROLLBACK TO stale');self.connection.run('RELEASE stale')
        first=self.write();self.connection.run('SAVEPOINT repeat')
        with self.assertRaises(DatabaseError):self.write(generation=first[2])
        self.connection.run('ROLLBACK TO repeat');self.connection.run('RELEASE repeat')
        self.assertEqual(self.connection.run('SELECT report_bytes FROM truss.catalog_acceptance_report'),[[bytes.fromhex(first[3])]])

    def test_insert_byte_substitution_refuses_and_preserves_host_work(self):
        from pg8000.exceptions import DatabaseError
        self.stage()
        self.connection.run("CREATE TEMP TABLE report_host_work(value text); INSERT INTO report_host_work VALUES('keep')")
        self.connection.run("""CREATE FUNCTION truss.fixture_report_substitute() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN NEW.report_bytes:=convert_to('{}','UTF8'); RETURN NEW; END $$;
            CREATE TRIGGER fixture_report_substitute BEFORE INSERT ON truss.catalog_acceptance_report
            FOR EACH ROW EXECUTE FUNCTION truss.fixture_report_substitute()""")
        self.connection.run('SAVEPOINT write_report')
        with self.assertRaises(DatabaseError) as caught:self.write()
        self.assertEqual(caught.exception.args[0]['M'],'original report insert and independent byte readback required')
        self.connection.run('ROLLBACK TO write_report');self.connection.run('RELEASE write_report')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
        self.assertEqual(self.connection.run('SELECT value FROM report_host_work'),[['keep']])
        self.assertEqual(self.connection.run('SELECT effect_generation::text FROM truss.row_home_operation'),[[self.generation]])

    def test_late_metadata_change_refuses_at_final_cut(self):
        from pg8000.exceptions import DatabaseError
        self.stage()
        self.connection.run("""CREATE FUNCTION truss.fixture_report_metadata_change() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN UPDATE truss.installation_marker SET layout_version='changed'; RETURN NEW; END $$;
            CREATE TRIGGER fixture_report_metadata_change AFTER INSERT ON truss.catalog_acceptance_report
            FOR EACH ROW EXECUTE FUNCTION truss.fixture_report_metadata_change()""")
        self.connection.run('SAVEPOINT write_report')
        with self.assertRaises(DatabaseError) as caught:self.write()
        self.assertEqual(caught.exception.args[0]['M'],'original candidate report final source cut required')
        self.connection.run('ROLLBACK TO write_report');self.connection.run('RELEASE write_report')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])

    def test_native_values_and_origin_mapping_reject_numbers(self):
        from pg8000.exceptions import DatabaseError
        c=self.connection
        for routine in ['runtime_catalog_report_native_tree']:
            c.run('SAVEPOINT numeric')
            with self.subTest(routine=routine),self.assertRaises(DatabaseError):
                c.run('SELECT truss.'+routine+'(:value::jsonb)',value='{"number":9007199254740993}')
            c.run('ROLLBACK TO numeric');c.run('RELEASE numeric')
        origin={'kind':'asserted-label','a':[None,True,'123.000'],'é':'snow ☃'}
        wire=c.run('SELECT truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_map_origin_tree(truss.runtime_catalog_report_original_tree(:value)))',value=json.dumps(origin).encode())[0][0]
        mapped=json.loads(bytes(wire))
        self.assertEqual(mapped['kind'],'map')
        self.assertEqual([entry['key'] for entry in mapped['entries']],sorted(origin,key=lambda s:s.encode()))
        self.assertEqual(mapped['entries'][0]['value']['items'][2],{'kind':'string','text':'123.000'})

    def test_original_origin_codec_preserves_nul_keys_and_values(self):
        from truss._canonical_wire_tree import prepare_canonical_wire_tree
        values=[{'a\x00':[None,True,'nul\x00','astral 😀','\b\f\n\r\t']},'a\x00z',False,None,[],{}]
        for value in values:
            raw=json.dumps(value,ensure_ascii=True).encode()
            tree=self.connection.run('SELECT truss.runtime_catalog_report_original_tree(:raw)',raw=raw)[0][0]
            expected=prepare_canonical_wire_tree(canonical_numeric_free(value))
            self.assertEqual(tree,json.loads(expected.native_tree_text))
            wire=self.connection.run('SELECT truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_map_origin_tree(:tree::jsonb))',tree=json.dumps(tree))[0][0]
            mapped=json.loads(bytes(wire))
            if isinstance(value,str):self.assertEqual(mapped,{'kind':'string','text':value})
            if isinstance(value,dict) and value:
                self.assertEqual(mapped['entries'][0]['key'],'a\x00')
                self.assertEqual(mapped['entries'][0]['value']['items'][2],{'kind':'string','text':'nul\x00'})

    def test_original_json_parser_rejects_invalid_duplicate_and_numeric_sources(self):
        from pg8000.exceptions import DatabaseError
        for raw in [b'{"a":true,"\\u0061":false}',b'1',b'[true,]',b'"\\ud800"',b'"\\udc00"',b'"\\x00"',b'true false',b'{null:true}',b'"unterminated',b'"\x01"']:
            self.connection.run('SAVEPOINT parse')
            with self.subTest(raw=raw),self.assertRaises(DatabaseError):
                self.connection.run('SELECT truss.runtime_catalog_report_original_tree(:raw)',raw=raw)
            self.connection.run('ROLLBACK TO parse');self.connection.run('RELEASE parse')

    def test_late_registration_duplicate_and_catalog_change_refuse(self):
        from pg8000.exceptions import DatabaseError
        self.stage()
        for body in ["INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) SELECT installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256 FROM truss.installation_archive WHERE artifact_identity='fixture.catalog-report-composition/0.1';",
                     "UPDATE truss.type_def SET retired_rev=1;"]:
            self.connection.run('SAVEPOINT drift')
            self.connection.run("CREATE FUNCTION truss.fixture_report_drift() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "+body+" RETURN NEW; END $$; CREATE TRIGGER fixture_report_drift AFTER INSERT ON truss.catalog_acceptance_report FOR EACH ROW EXECUTE FUNCTION truss.fixture_report_drift()")
            with self.subTest(body=body),self.assertRaises(DatabaseError) as caught:self.write()
            self.assertEqual(caught.exception.args[0]['C'],'55000')
            self.assertEqual(caught.exception.args[0]['M'],'catalog observation stale or unrelated' if body.startswith('UPDATE') else 'original candidate report final source cut required')
            self.connection.run('ROLLBACK TO drift');self.connection.run('RELEASE drift')
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])

    def test_raw_commit_remains_refused_after_report_write(self):
        from pg8000.exceptions import DatabaseError
        self.stage();self.write()
        with self.assertRaises(DatabaseError):self.connection.run('COMMIT')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])

    def test_suppressed_report_insert_refuses_and_preserves_prestate(self):
        from pg8000.exceptions import DatabaseError
        self.stage()
        self.connection.run("CREATE TEMP TABLE report_host_work(value text); INSERT INTO report_host_work VALUES('keep')")
        self.connection.run("""CREATE FUNCTION truss.fixture_report_suppress() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RETURN NULL; END $$; CREATE TRIGGER fixture_report_suppress BEFORE INSERT ON truss.catalog_acceptance_report
            FOR EACH ROW EXECUTE FUNCTION truss.fixture_report_suppress()""")
        self.connection.run('SAVEPOINT suppressed')
        with self.assertRaises(DatabaseError) as caught:self.write()
        self.assertEqual(caught.exception.args[0]['C'],'P0002')
        self.connection.run('ROLLBACK TO suppressed');self.connection.run('RELEASE suppressed')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
        self.assertEqual(self.connection.run('SELECT value FROM report_host_work'),[['keep']])
        self.assertEqual(self.connection.run('SELECT effect_generation::text FROM truss.row_home_operation'),[[self.generation]])

    def test_malformed_nested_host_sources_refuse_before_report_insert(self):
        from pg8000.exceptions import DatabaseError
        def diagnostics(candidate):
            node=next(m['node'] for m in candidate['hostSources']['members'] if m['keyUtf8Hex']==b'diagnostics'.hex())
            node['items']=[{'kind':'null'}]
        def rule_name(candidate):
            node=next(m['node'] for m in candidate['hostSources']['members'] if m['keyUtf8Hex']==b'assertionEntries'.hex())
            next(m for m in node['items'][0]['members'] if m['keyUtf8Hex']==b'ruleName'.hex())['node']={'kind':'null'}
        for transform in [diagnostics,rule_name]:
            self.connection.run('SAVEPOINT invalid_shape');self.candidate_transform=transform
            self.stage()
            with self.subTest(transform=transform.__name__),self.assertRaises(DatabaseError) as caught:self.write()
            self.assertEqual(caught.exception.args[0]['M'],'complete selected candidate report shape required')
            self.connection.run('ROLLBACK TO invalid_shape');self.connection.run('RELEASE invalid_shape')
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
        del self.candidate_transform

    def test_current_stage_refuses_nul_origin_and_retains_original_bytes(self):
        from pg8000.exceptions import DatabaseError
        self.skip_stage=True;self.origin_bytes=json.dumps({'key\x00':'value\x00'}).encode()
        self.stage();self.connection.run('SAVEPOINT unsupported_origin')
        with self.assertRaises(DatabaseError) as caught:self.invoke()
        self.assertEqual(caught.exception.args[0]['C'],'22P05')
        self.connection.run('ROLLBACK TO unsupported_origin');self.connection.run('RELEASE unsupported_origin')
        retained=self.connection.run('SELECT original_context_bytes FROM truss.row_home_operation')[0][0]
        self.assertEqual(bytes(retained),self.context)
        self.assertEqual(bytes.fromhex(json.loads(bytes(retained))['assertedOriginUtf8Hex']),self.origin_bytes)
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'),[[0]])

    def test_late_selected_lifecycle_resource_mutation_and_duplicate_refuse(self):
        from pg8000.exceptions import DatabaseError
        self.stage()
        identity='packages/python/src/truss/_profiles/fresh-catalog-lifecycle.json'
        for body,message in [
            ("UPDATE truss.installation_archive SET artifact_bytes=decode('01','hex') WHERE artifact_identity='"+identity+"';",'original report resource digest correspondence required'),
            ("INSERT INTO truss.installation_archive(installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256) SELECT installation_id,artifact_role,artifact_identity,artifact_bytes,artifact_identity_sha256 FROM truss.installation_archive WHERE artifact_identity='"+identity+"';",'unique original report resource archive required')]:
            self.connection.run('SAVEPOINT resource_drift')
            self.connection.run("CREATE FUNCTION truss.fixture_report_resource_drift() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "+body+" RETURN NEW; END $$; CREATE TRIGGER fixture_report_resource_drift AFTER INSERT ON truss.catalog_acceptance_report FOR EACH ROW EXECUTE FUNCTION truss.fixture_report_resource_drift()")
            with self.subTest(body=body),self.assertRaises(DatabaseError) as caught:self.write()
            self.assertEqual(caught.exception.args[0]['M'],message)
            self.connection.run('ROLLBACK TO resource_drift');self.connection.run('RELEASE resource_drift')
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'),[[0]])
            self.assertEqual(self.connection.run('SELECT effect_generation::text FROM truss.row_home_operation'),[[self.generation]])

    def test_deep_valid_schema_value_reports_capacity_instead_of_invalidity(self):
        from pg8000.exceptions import DatabaseError
        from truss._canonical_wire_tree import prepare_canonical_wire_tree
        value=None
        for _ in range(90):value=[value]
        tree=json.loads(prepare_canonical_wire_tree(canonical_numeric_free(value)).native_tree_text)
        schema=json.loads((ROOT/'packages/python/src/truss/_report_schemas/acceptance-input-v0.1.schema.json').read_bytes())
        self.connection.run('SAVEPOINT shape_capacity')
        with self.assertRaises(DatabaseError) as caught:
            self.connection.run('SELECT truss.runtime_catalog_report_shape_matches(:tree::jsonb,:rule::jsonb,:registry::jsonb,:base)',
                tree=json.dumps(tree),rule=json.dumps(schema['$defs']['canonicalTree']),registry=json.dumps({schema['$id']:schema}),base=schema['$id'])
        self.assertEqual(caught.exception.args[0]['C'],'54000')
        self.assertEqual(caught.exception.args[0]['M'],'selected report schema evaluation depth capacity')
        self.connection.run('ROLLBACK TO shape_capacity');self.connection.run('RELEASE shape_capacity')
