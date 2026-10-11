"""Real prepared catalog through original host custody; no accepted authority."""
import json
from unittest.mock import patch
from test_native_operation_ordinals import ReservedNativeOperationOrdinalTests
from test_catalog_staging import ROOT, COMPONENTS
from test_catalog_support import selected
from truss._native_catalog_request import NativeCatalogStageInput,ConfiguredCatalogSelection
from truss._native_catalog_capture import NativeCatalogCapture
from truss._native_deadline import NativeOperationDeadline
from truss._native_pg8000 import NativeBoundaryRefusal


class NativeCatalogDispatchTests(ReservedNativeOperationOrdinalTests):
    def _prepare_catalog(self, *, bad_response=False, prepared=None, configured=False):
        setup=(ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text()
        for name in COMPONENTS:
            if name!='operation-admission':
                setup+=';\n'+(ROOT/f'packages/postgresql/native/{name}.sql').read_text()
        for name in ('issued-operation-admission/operation-admission',
                     'edge-limit/verify-current-scope','catalog-report/empty-graph',
                     'catalog-report/fresh-lifecycle','catalog-report/absent-binding-index-declarations',
                     'catalog-stage-issued'):
            setup+=';\n'+(ROOT/f'packages/postgresql/native/{name}.sql').read_text()
        # Install development fixture components outside the adopted host
        # transaction. DDL locks cannot masquerade as a fresh graph start cut.
        fixture=self.Connection(**self.kwargs)
        try:
            fixture.run('DROP SCHEMA IF EXISTS truss CASCADE')
            fixture.run(setup)
            if configured:
                import hashlib
                fixture.run((ROOT/'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql').read_text())
                for name in ('source-epoch-lock','issued-operation-admission/operation-configuration-context-admission',
                    'catalog-epoch-context','operation-configuration-current','catalog-admission-configuration',
                    'canonical-string-bytes','canonical-tree-bytes','catalog-report/source-candidate',
                    'catalog-report/release-selection','catalog-report/configured-metadata','catalog-report/configured-graph','catalog-report/configured-stage','catalog-stage-configured'):
                    fixture.run((ROOT/f'packages/postgresql/native/{name}.sql').read_text())
                guard=(ROOT/'docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql').read_text()
                fixture.run(guard.split('INSERT INTO truss.row_home_operation')[0])
                fixture.run("INSERT INTO truss.source_epoch_current VALUES(1,'guard-fixture','guard-fixture-epoch')")
                policy=(ROOT/'packages/python/src/truss/_profiles/catalog-report-release.json').read_bytes()
                configuration_profile=(ROOT/'packages/python/src/truss/_profiles/catalog-report-configuration.json').read_bytes()
                configuration=json.dumps({'interfaceVersion':'truss-catalog-report-configuration/0.1',
                    'catalogReportRelease':{'artifactIdentity':'truss.catalog-report-release/0.1.0',
                    'sha256':hashlib.sha256(policy).hexdigest()}}).encode()
                fixture.run("""INSERT INTO truss.installation_admission(head_id,installation_id_utf8,
                    source_epoch_utf8,configuration_generation,key_reuse,journal_mode,configuration_bytes,
                    selected_binding_bytes,installed_inventory_bytes) VALUES(1,convert_to('guard-fixture','UTF8'),
                    convert_to('guard-fixture-epoch','UTF8'),7,'forbid','engine',:configuration,
                    convert_to('binding fixture','UTF8'),convert_to('inventory fixture','UTF8'))""",configuration=configuration)
                fixture.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,
                    artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',
                    'truss.catalog-report-release/0.1.0',:raw,sha256(convert_to('truss.catalog-report-release/0.1.0','UTF8')))""",raw=policy)
        finally:fixture.close()
        setup=''
        if bad_response:
            original="convert_from(decode(provisional_result_hex,'hex'),'UTF8')::jsonb"
            expressions={True: "jsonb_build_object('interfaceVersion','truss-native-provisional-catalog/0.2',"
                "'writerXid',writer_xid,'ordinal',ordinal,'accepted',false)",
                'documents': "jsonb_set("+original+",'{documents,0,content_sha256}',to_jsonb(repeat('0',64)))",
                'extra': original+"||jsonb_build_object('extra',true)",
                'cut': "jsonb_set("+original+",'{reportSources,start,effect_generation}','\"1\"'::jsonb)",
                'policy': "jsonb_set("+original+",'{reportSources,lifecycle,policyHex}','\"00\"'::jsonb)",
                'counts': "jsonb_set("+original+",'{counts,types_added}','\"9\"'::jsonb)"}
            setup += """ALTER FUNCTION truss.runtime_stage_catalog_issued(
          bigint,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea) RENAME TO fixture_stage_original;
          CREATE FUNCTION truss.runtime_stage_catalog_issued(
            bigint,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea)
          RETURNS TABLE(writer_xid text,ordinal text,context_hex text,provisional_result_hex text)
          LANGUAGE SQL VOLATILE AS $$
            SELECT writer_xid,ordinal,context_hex,encode(convert_to((RESULT_EXPRESSION)::text,'UTF8'),'hex')
            FROM truss.fixture_stage_original($1,$2,$3,$4,$5,$6,$7,$8,$9)
          $$""".replace('RESULT_EXPRESSION',expressions[bad_response])
        setup+='; CREATE TEMP TABLE catalog_host_sentinel(value int); INSERT INTO catalog_host_sentinel VALUES (7);'
        self.boundary.run(setup, token=self.token)
        session=self.service.bind(self.attempt)
        session.deadline=NativeOperationDeadline(30000,5000)
        issued=self.service.issue_operation(session,reserve_controls=True)
        issued.controls.run_control('savepoint')
        original=NativeCatalogStageInput(selected() if prepared is None else prepared,b'{"x-action":"test"}',b'fixture definition',
            b'fixture obligations',b'fixture group',
            ConfiguredCatalogSelection('guard-fixture','guard-fixture-epoch','guard-fixture-incarnation',
                b'original capture fixture',configuration_profile) if configured else None)
        request=issued.owner.prepare_catalog_stage(issued,original)
        return session,issued,request

    def test_configured_original_host_dispatch_and_cleanup(self):
        session,issued,request=self._prepare_catalog(configured=True)
        result=issued.owner.dispatch_catalog_stage_candidate(request)
        self.assertIs(result.original_call,request.entry.native_call)
        self.assertEqual(json.loads(result.original_context)['interfaceVersion'],'truss-native-operation-context/0.4')
        self.assertEqual(json.loads(result.original_report_assembly)['missingReportFields'],
                         ['reportProfile','originalExecution','assertions'])
        before=self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):issued.owner.dispatch_catalog_stage_candidate(request)
        self.assertIs(self.boundary.last_call,before)
        self._restore_catalog(session,issued)
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.operation_configuration'),[[0]])

    def test_configured_lost_publication_preserves_original_cleanup(self):
        session,issued,request=self._prepare_catalog(configured=True)
        original=NativeCatalogCapture.observe
        def lost(gate,rows,call,ordinal):
            original(gate,rows,call,ordinal)
            raise MemoryError('lost configured publication')
        with patch.object(NativeCatalogCapture,'observe',lost),self.assertRaises(MemoryError):
            issued.owner.dispatch_catalog_stage_candidate(request)
        observed=session.result_custody.original_observation
        self.assertIs(observed.original_call,request.entry.native_call)
        self.assertIsNotNone(observed.original_report_source_snapshot)
        with self.assertRaises(NativeBoundaryRefusal):issued.owner.dispatch_catalog_stage_candidate(request)
        self._restore_catalog(session,issued)

    def _restore_catalog(self,session,issued):
        issued.controls.run_control('rollback_to')
        issued.controls.run_control('release')
        session.result_custody.detach()
        self.assertEqual(self.connection.run('SELECT value FROM catalog_host_sentinel'),[[7]])
        for name in ('row_home_operation','type_def','prop_def','schema_doc'):
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.'+name),[[0]])

    def test_original_prepared_dispatch_and_replay_refusal(self):
        session,issued,request=self._prepare_catalog()
        result=issued.owner.dispatch_catalog_stage_candidate(request)
        native=json.loads(result.original_provisional_result)
        self.assertIs(result,session.result_custody.original_observation)
        self.assertIs(result.original_call,request.entry.native_call)
        self.assertEqual(native['counts']['properties_added'],'1')
        self.assertEqual(result.ordinal,issued.ordinal)
        self.assertFalse(native['accepted'])
        assembly=json.loads(result.original_report_assembly)
        self.assertEqual(len(assembly['requiredReportFields']),19)
        self.assertEqual(assembly['producedFields']['rev'],native['revision'])
        self.assertEqual(assembly['producedFields']['documents'],native['documents'])
        self.assertEqual(assembly['missingReportFields'],['reportProfile','originalExecution','assertions'])
        self.assertIsNone(assembly['completeReportBytes'])
        self.assertIn('originalInstalledExecution',assembly['requiredSources'])
        self.assertFalse(issued.controls.forward_ready)
        before=self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):
            issued.owner.dispatch_catalog_stage_candidate(request)
        self.assertIs(self.boundary.last_call,before)
        self._restore_catalog(session,issued)

    def test_combined_sources_and_large_result_complete_ready_and_cleanup(self):
        import copy
        from test_preparation import CONFIG,prepare
        from test_catalog_staging import native_document
        from truss._catalog_support import PROFILE
        config=copy.deepcopy(CONFIG);config['supportProfile']=dict(PROFILE)
        prepared=prepare((native_document('document-'+('x'*2500)),),config)
        session,issued,request=self._prepare_catalog(prepared=prepared)
        result=issued.owner.dispatch_catalog_stage_candidate(request)
        self.assertGreater(len(result.original_provisional_result),16384)
        snapshot=json.loads(result.original_report_source_snapshot)
        self.assertFalse(snapshot['acceptedReportQualified'])
        self.assertFalse(snapshot['currentStateRevalidated'])
        self.assertEqual(snapshot['nativeSources']['start']['effect_generation'],'0')
        self.assertEqual(snapshot['nativeSources']['lifecycle']['inputHex'],prepared.input_bytes.hex())
        self.assertEqual(snapshot['nativeSources']['indexDeclarations']['declaredJobs'],[])
        self.assertEqual(snapshot['semanticSourceFields']['state'],'source_fields_ready')
        self.assertTrue(request.entry.native_call.capture_complete)
        self._restore_catalog(session,issued)

    def test_python_composition_failure_retains_original_native_sources(self):
        session,issued,request=self._prepare_catalog()
        with patch('truss._native_catalog_capture.compose_captured_catalog_sources',side_effect=ValueError('refuse composition')):
            with self.assertRaises(NativeBoundaryRefusal):
                issued.owner.dispatch_catalog_stage_candidate(request)
        observed=session.result_custody.original_observation
        self.assertIs(observed.original_call,request.entry.native_call)
        self.assertIn('reportSources',json.loads(observed.original_provisional_result))
        self.assertIsNone(observed.original_report_source_snapshot)
        self._restore_catalog(session,issued)

    def test_changed_source_cut_refuses(self):
        self._assert_substituted_response('cut')

    def test_changed_lifecycle_policy_refuses(self):
        self._assert_substituted_response('policy')

    def test_lost_observation_preserves_original_result_without_replay(self):
        session,issued,request=self._prepare_catalog()
        original=NativeCatalogCapture.observe
        def lost(gate,rows,call,ordinal):
            original(gate,rows,call,ordinal)
            raise MemoryError('lost result publication')
        with patch.object(NativeCatalogCapture,'observe',lost):
            with self.assertRaises(MemoryError):
                issued.owner.dispatch_catalog_stage_candidate(request)
        self.assertIs(session.result_custody.original_observation.original_call,request.entry.native_call)
        self.assertTrue(session.admission_closed)
        before=self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):
            issued.owner.dispatch_catalog_stage_candidate(request)
        self.assertIs(self.boundary.last_call,before)
        self._restore_catalog(session,issued)

    def test_foreign_nominal_request_refuses_before_dereference(self):
        from truss._native_operation_ordinals import PreparedNativeCatalogStage
        session,issued,request=self._prepare_catalog()
        class Hostile:
            @property
            def original_input(self):raise AssertionError('Foreign object dereferenced')
        foreign=PreparedNativeCatalogStage(issued,Hostile(),request.entry)
        before=self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):
            issued.owner.dispatch_catalog_stage_candidate(foreign)
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(request.entry.native_call)
        issued.controls.run_control('rollback_to')
        issued.controls.run_control('release')

    def test_incomplete_actual_native_response_never_publishes(self):
        session,issued,request=self._prepare_catalog(bad_response=True)
        # Deliberately substitute the installed producer in this administrative
        # fixture. This tests result validation, not complete body admission.

        with self.assertRaises(NativeBoundaryRefusal):
            issued.owner.dispatch_catalog_stage_candidate(request)
        self.assertIsNone(session.result_custody.original_observation)
        self.assertTrue(request.entry.native_call.capture_complete)
        self.assertTrue(session.admission_closed)
        self._restore_catalog(session,issued)

    def _assert_substituted_response(self,kind):
        session,issued,request=self._prepare_catalog(bad_response=kind)
        with self.assertRaises(NativeBoundaryRefusal):
            issued.owner.dispatch_catalog_stage_candidate(request)
        observed=session.result_custody.original_observation
        if kind in ('cut','policy'):
            self.assertIs(observed.original_call,request.entry.native_call)
            self.assertIsNone(observed.original_report_source_snapshot)
        else:
            self.assertIsNone(observed)
        self.assertTrue(request.entry.native_call.capture_complete)
        self._restore_catalog(session,issued)

    def test_well_shaped_substituted_document_hash_refuses(self):
        self._assert_substituted_response('documents')

    def test_extra_native_response_field_refuses(self):
        self._assert_substituted_response('extra')

    def test_substituted_native_inventory_count_refuses(self):
        self._assert_substituted_response('counts')

    def test_original_configured_encoder_capture_and_rollback(self):
        session,issued,request=self._prepare_catalog(configured=True)
        result=issued.owner.dispatch_catalog_stage_candidate(request)
        native=json.loads(result.original_provisional_result)
        context=json.loads(result.original_context)
        self.assertEqual(native['interfaceVersion'],'truss-native-provisional-catalog/0.3')
        self.assertEqual(context['assertedOriginUtf8Hex'],request.encoded.original_input.origin.hex())
        self.assertIs(result.original_call,request.entry.native_call)
        self.assertTrue(result.original_call.capture_complete)
        self.assertFalse(json.loads(result.original_report_source_snapshot)['configuredReleaseCandidate']['registeredAuthority'])
        self.assertIsNone(json.loads(result.original_report_assembly)['completeReportBytes'])
        self.assertFalse(issued.controls.forward_ready)
        self._restore_catalog(session,issued)
