"""Real prepared catalog through original host custody; no accepted authority."""
import json
from unittest.mock import patch
from test_native_operation_ordinals import ReservedNativeOperationOrdinalTests
from test_catalog_staging import ROOT, COMPONENTS
from test_catalog_support import selected
from truss._native_catalog_request import NativeCatalogStageInput
from truss._native_catalog_capture import NativeCatalogCapture
from truss._native_deadline import NativeOperationDeadline
from truss._native_pg8000 import NativeBoundaryRefusal


class NativeCatalogDispatchTests(ReservedNativeOperationOrdinalTests):
    def _prepare_catalog(self, *, bad_response=False):
        setup=(ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text()
        for name in COMPONENTS:
            if name!='operation-admission':
                setup+=';\n'+(ROOT/f'packages/postgresql/native/{name}.sql').read_text()
        for name in ('issued-operation-admission/operation-admission',
                     'edge-limit/verify-current-scope','catalog-stage-issued'):
            setup+=';\n'+(ROOT/f'packages/postgresql/native/{name}.sql').read_text()
        if bad_response:
            original="convert_from(decode(provisional_result_hex,'hex'),'UTF8')::jsonb"
            expressions={True: "jsonb_build_object('interfaceVersion','truss-native-provisional-catalog/0.1',"
                "'writerXid',writer_xid,'ordinal',ordinal,'accepted',false)",
                'documents': "jsonb_set("+original+",'{documents,0,content_sha256}',to_jsonb(repeat('0',64)))",
                'extra': original+"||jsonb_build_object('extra',true)",
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
        original=NativeCatalogStageInput(selected(),b'{"x-action":"test"}',b'fixture definition',
            b'fixture obligations',b'fixture group')
        request=issued.owner.prepare_catalog_stage(issued,original)
        return session,issued,request

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
        self.assertFalse(issued.controls.forward_ready)
        before=self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):
            issued.owner.dispatch_catalog_stage_candidate(request)
        self.assertIs(self.boundary.last_call,before)
        self._restore_catalog(session,issued)

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
        self.assertIsNone(session.result_custody.original_observation)
        self.assertTrue(request.entry.native_call.capture_complete)
        self._restore_catalog(session,issued)

    def test_well_shaped_substituted_document_hash_refuses(self):
        self._assert_substituted_response('documents')

    def test_extra_native_response_field_refuses(self):
        self._assert_substituted_response('extra')

    def test_substituted_native_inventory_count_refuses(self):
        self._assert_substituted_response('counts')
