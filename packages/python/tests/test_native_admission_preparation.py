# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original attempt request custody; never artifact authority/admission evidence."""
from unittest.mock import patch
from test_native_operation_ordinals import ReservedNativeOperationOrdinalTests
from truss._native_operation_ordinals import NativeOperationOrdinals
from truss._native_admission_request import NativeAdmissionInput
from truss._native_pg8000 import NativeBoundaryRefusal

class NativeAdmissionPreparationTests(ReservedNativeOperationOrdinalTests):
    def _input(self):
        return NativeAdmissionInput('base', 'catalog-acceptance', (b'opaque',)*6)

    def test_original_ordinal_request_is_retained_without_sql(self):
        session = self.service.bind(self.attempt)
        issued = self.service.issue_operation(session, reserve_controls=True)
        controls = issued.controls
        controls.run_control('savepoint')
        before = self.boundary.last_call
        value = self._input()
        request = issued.owner.prepare_admission(issued, value)
        self.assertIs(issued.admission_request, request)
        self.assertIs(request.encoded.original_input, value)
        self.assertEqual(request.encoded.ordinal, issued.ordinal)
        self.assertIs(request.entry, controls.admission_entry)
        self.assertIs(self.boundary.last_call, before)
        self.assertFalse(controls.forward_ready)
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.prepare_admission(issued, value)
        controls.run_control('release')

    def test_pre_savepoint_and_post_cleanup_requests_refuse(self):
        session = self.service.bind(self.attempt)
        issued = self.service.issue_operation(session, reserve_controls=True)
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.prepare_admission(issued, self._input())
        self.assertIs(self.boundary.last_call, before)
        issued.controls.run_control('savepoint')
        issued.controls.run_control('rollback_to')
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.prepare_admission(issued, self._input())
        self.assertIs(self.boundary.last_call, before)
        issued.controls.run_control('release')

    def test_lost_request_publication_retains_original_and_cleanup(self):
        session = self.service.bind(self.attempt)
        issued = self.service.issue_operation(session, reserve_controls=True)
        issued.controls.run_control('savepoint')
        before = self.boundary.last_call
        original = NativeOperationOrdinals._publish_admission_requests
        def lost(owner, root):
            original(owner, root)
            raise MemoryError('lost request publication')
        with patch.object(NativeOperationOrdinals, '_publish_admission_requests', lost):
            with self.assertRaises(MemoryError): issued.owner.prepare_admission(issued, self._input())
        self.assertIsNotNone(issued.admission_request)
        self.assertTrue(session.admission_closed)
        self.assertTrue(issued.owner.closed)
        self.assertIs(self.boundary.last_call, before)
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.prepare_admission(issued, self._input())
        issued.controls.run_control('rollback_to')
        issued.controls.run_control('release')

    def test_foreign_attempt_refuses_without_attribute_access(self):
        class Hostile:
            def __getattr__(self, name): raise AssertionError('foreign attempt accessed')
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): self.t._operation_ordinals.prepare_admission(Hostile(), self._input())
        self.assertIs(self.boundary.last_call, before)

    def test_request_prepublication_fault_preserves_absence_and_cleanup(self):
        session = self.service.bind(self.attempt)
        issued = self.service.issue_operation(session, reserve_controls=True)
        issued.controls.run_control('savepoint')
        before = self.boundary.last_call
        with patch.object(NativeOperationOrdinals, '_publish_admission_requests',
                          side_effect=MemoryError('before request publication')):
            with self.assertRaises(MemoryError): issued.owner.prepare_admission(issued, self._input())
        self.assertIsNone(issued.admission_request)
        self.assertTrue(session.admission_closed)
        self.assertTrue(issued.owner.closed)
        self.assertIs(self.boundary.last_call, before)
        issued.controls.run_control('rollback_to')
        issued.controls.run_control('release')

    def test_disposal_during_encoding_refuses_before_request_publication(self):
        from truss._native_admission_request import encode_admission_request
        session = self.service.bind(self.attempt)
        issued = self.service.issue_operation(session, reserve_controls=True)
        issued.controls.run_control('savepoint')
        before = self.boundary.last_call
        def disposed(value, ordinal):
            result = encode_admission_request(value, ordinal)
            self.executor.dispose()
            return result
        with patch('truss._native_operation_ordinals.encode_admission_request', disposed):
            with self.assertRaises(NativeBoundaryRefusal): issued.owner.prepare_admission(issued, self._input())
        self.assertIsNone(issued.admission_request)
        self.assertIs(self.boundary.last_call, before)
        issued.controls.run_control('rollback_to')
        issued.controls.run_control('release')
