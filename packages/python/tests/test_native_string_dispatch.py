# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original Python host dispatch of real pending effects; no public apply."""
import unittest
from test_native_operation_ordinals import ReservedNativeOperationOrdinalTests
from test_native_connected_string_writer import install_string_fixture
from truss._native_deadline import NativeOperationDeadline
from truss._native_string_request import NativeStringReplacementInput
from truss._native_admission_request import NativeAdmissionInput
from truss._native_pg8000 import NativeBoundaryRefusal

class NativeStringDispatchTests(ReservedNativeOperationOrdinalTests):
    def _prepare_writer(self,version='1'):
        install_string_fixture(lambda sql: self.boundary.run(sql,token=self.token))
        self.boundary.run("CREATE TEMP TABLE caller_sentinel(value text); INSERT INTO caller_sentinel VALUES('prior')",token=self.token)
        session=self.service.bind(self.attempt)
        session.deadline=NativeOperationDeadline(30000,5000)
        issued=self.service.issue_operation(session,reserve_controls=True)
        issued.controls.run_control('savepoint')
        request=issued.owner.prepare_string_replacement(issued,NativeStringReplacementInput(
            state_id='501',expected_version=version,replacement="quoted ' ☃",original_token=b'"quoted \' \u2603"'))
        return session,issued,request

    def _restore_writer(self,session,issued):
        issued.controls.run_control('rollback_to')
        issued.controls.run_control('release')
        session.result_custody.detach()
        self.assertEqual(self.connection.run('SELECT value FROM caller_sentinel'),[['prior']])
        self.assertEqual(self.connection.run('SELECT ver::text FROM truss.object'),[['1']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'),[[0]])

    def test_original_host_dispatches_exact_pending_effect_once(self):
        session,issued,request=self._prepare_writer()
        observation=issued.owner.dispatch_string_replacement_candidate(request)
        self.assertEqual(observation.scope,'pending_native_effects_only')
        self.assertEqual(observation.ordinal,issued.ordinal)
        self.assertIs(observation.original_call,request.entry.native_call)
        self.assertFalse(issued.controls.forward_ready)
        before=self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):issued.owner.dispatch_string_replacement_candidate(request)
        self.assertIs(self.boundary.last_call,before)
        self._restore_writer(session,issued)

    def test_writer_and_admission_share_one_original_request_slot(self):
        session,issued,request=self._prepare_writer()
        with self.assertRaises(NativeBoundaryRefusal):
            issued.owner.prepare_admission(issued,NativeAdmissionInput(family='base',kind='mutation',artifacts=(b'x',)*6))
        issued.owner.dispatch_string_replacement_candidate(request)
        self._restore_writer(session,issued)

    def test_stale_write_uses_original_cleanup_and_preserves_host_work(self):
        from pg8000.exceptions import DatabaseError
        session,issued,request=self._prepare_writer('2')
        with self.assertRaises(DatabaseError):issued.owner.dispatch_string_replacement_candidate(request)
        self._restore_writer(session,issued)

    def test_lost_observation_retains_call_without_replay(self):
        from unittest.mock import patch
        from truss._native_admission_capture import NativeAdmissionCapture
        session,issued,request=self._prepare_writer()
        original=NativeAdmissionCapture.observe
        def lose(gate,*args):
            original(gate,*args)
            raise MemoryError('lost observation reply')
        with patch.object(NativeAdmissionCapture,'observe',lose):
            with self.assertRaises(MemoryError):issued.owner.dispatch_string_replacement_candidate(request)
        self.assertTrue(request.entry.native_call.capture_complete)
        before=self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):issued.owner.dispatch_string_replacement_candidate(request)
        self.assertIs(self.boundary.last_call,before)
        self._restore_writer(session,issued)

    def test_lost_invocation_publication_prevents_send(self):
        from unittest.mock import patch
        from truss._native_operation_ordinals import NativeOperationOrdinals
        session,issued,request=self._prepare_writer()
        before=self.boundary.last_call
        original=NativeOperationOrdinals._publish_admission_invocations
        def lose(owner,root):
            original(owner,root)
            raise MemoryError('lost invocation publication reply')
        with patch.object(NativeOperationOrdinals,'_publish_admission_invocations',lose):
            with self.assertRaises(MemoryError):issued.owner.dispatch_string_replacement_candidate(request)
        self.assertIs(self.boundary.last_call,before)
        self.assertIsNone(request.entry.native_call)
        self._restore_writer(session,issued)

    def test_input_refusal_precedes_original_request_or_sql(self):
        from dataclasses import replace
        session,issued,request=self._prepare_writer()
        from truss._native_string_request import encode_string_replacement
        value=request.encoded.original_input
        before=self.boundary.last_call
        for bad in (replace(value,state_id='01'),replace(value,expected_version=True),
                    replace(value,replacement='\0'),replace(value,replacement='\ud800'),
                    replace(value,original_token=bytearray(b'"x"'))):
            with self.assertRaises(NativeBoundaryRefusal):encode_string_replacement(bad,issued.ordinal)
        self.assertIs(self.boundary.last_call,before)
        self.assertEqual(len(request.encoded.sql),request.encoded.encoded_bytes)
        issued.owner.dispatch_string_replacement_candidate(request)
        self._restore_writer(session,issued)
