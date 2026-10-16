"""Actual coordinator issuance; original artifact/native admission remains open."""
import unittest
from unittest.mock import patch
import test_native_arbitration as fixtures
from truss._native_pg8000 import NativeBoundaryRefusal
from truss._operation_ordinal import OperationOrdinalIssuer

class NativeOperationOrdinalTests(fixtures.NativeArbitrationTests):
    def test_original_session_issue_precedes_savepoint_and_survives_rollback(self):
        session=self.service.bind(self.attempt)
        coordinator=self.t._operation_ordinals
        before=self.boundary.last_call
        issued=self.service.issue_operation(session)
        self.assertEqual(issued.ordinal,'0')
        self.assertIs(self.boundary.last_call,before)
        point=self.t.savepoint('business',token=self.token)
        self.t.rollback_to(point,token=self.token)
        self.t.release(point,token=self.token)
        self.assertEqual(coordinator.observe(issued).ordinal,'0')
        self.assertEqual(issued.issuer._next,1)
        with self.assertRaises(NativeBoundaryRefusal):self.service.issue_operation(session)

    def test_lost_issue_reply_preserves_same_original_ordinal(self):
        session=self.service.bind(self.attempt)
        original=OperationOrdinalIssuer.reserve_into
        def lost(issuer,scope,reservation):
            original(issuer,scope,reservation)
            raise MemoryError('lost issuance reply')
        with patch.object(OperationOrdinalIssuer,'reserve_into',lost):
            with self.assertRaises(MemoryError):self.service.issue_operation(session)
        retained=self.t._operation_ordinals.attempts[-1]
        self.assertEqual(retained.ordinal,'0')
        self.assertEqual(retained.issuer._next,1)
        with self.assertRaises(NativeBoundaryRefusal):self.service.issue_operation(session)
        self.assertEqual(self.t._operation_ordinals.observe(retained).ordinal,'0')

    def test_attempt_capacity_refuses_before_ordinal_or_sql(self):
        session=self.service.bind(self.attempt)
        coordinator=self.t._operation_ordinals
        coordinator.maximum_attempts=0
        before=self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):self.service.issue_operation(session)
        self.assertEqual(coordinator.attempts,())
        self.assertIs(self.boundary.last_call,before)

    def test_uncertain_native_call_closes_issuance_without_ending_generation(self):
        session=self.service.bind(self.attempt)
        generation=session.generation
        issued=self.service.issue_operation(session)
        with patch.object(self.connection,'run',side_effect=OSError('transport lost')):
            with self.assertRaises(OSError):self.boundary.run('SELECT 1',token=self.token)
        self.assertTrue(self.t._operation_ordinals.closed)
        self.assertFalse(generation.ended)
        self.assertEqual(self.t._operation_ordinals.observe(issued).ordinal,'0')
        with self.assertRaises(NativeBoundaryRefusal):self.service.issue_operation(session)

    def test_competing_coordinator_cannot_restart_original_counter(self):
        from truss._native_operation_ordinals import NativeOperationOrdinals
        session=self.service.bind(self.attempt)
        self.assertEqual(self.service.issue_operation(session).ordinal,'0')
        competing=NativeOperationOrdinals(self.t)
        with self.assertRaises(NativeBoundaryRefusal):competing.issue(session)
        self.assertEqual(competing.attempts,())

    def test_confirmed_native_end_closes_original_issuer(self):
        session=self.service.bind(self.attempt)
        issued=self.service.issue_operation(session)
        self.t.rollback(token=self.token)
        self.assertTrue(session.generation.ended)
        self.assertTrue(issued.issuer._closed)
        self.assertEqual(self.t._operation_ordinals.observe(issued).ordinal,'0')
        with self.assertRaises(NativeBoundaryRefusal):self.service.issue_operation(session)

class ReservedNativeOperationOrdinalTests(fixtures.NativeArbitrationTests):
    def setUp(self):
        from truss._native_transactions import NativeTransactions
        with patch.object(fixtures, 'NativeTransactions',
                          side_effect=lambda boundary: NativeTransactions(boundary, mediated_namespace=True)):
            super().setUp()

    def test_complete_original_controls_reserved_before_ordinal(self):
        session = self.service.bind(self.attempt)
        before = self.boundary.last_call
        issued = self.service.issue_operation(session, reserve_controls=True)
        controls = issued.controls
        self.assertEqual(issued.ordinal, '0')
        self.assertIs(controls.session, session)
        self.assertIs(controls.port, self.port)
        self.assertIs(session._reserved_controls, controls)
        self.assertIs(session._call_root, controls.initial_root)
        self.assertEqual(controls.initial_root.held_cleanup, 2)
        self.assertEqual(controls.admission_root.calls,
                         (controls.savepoint_entry, controls.admission_entry))
        self.assertRegex(controls.savepoint_name, r'^truss_sp_[0-9a-f]{32}_1$')
        self.assertIs(self.boundary.last_call, before)
        with self.assertRaises(NativeBoundaryRefusal):
            self.boundary.run('SELECT 1', token=self.token)
        self.assertIs(self.boundary.last_call, before)

    def test_lost_ordinal_reply_retains_original_reserved_controls(self):
        session = self.service.bind(self.attempt)
        original = OperationOrdinalIssuer.reserve_into
        def lost(issuer, scope, reservation):
            original(issuer, scope, reservation)
            raise MemoryError('lost issuance reply')
        with patch.object(OperationOrdinalIssuer, 'reserve_into', lost):
            with self.assertRaises(MemoryError):
                self.service.issue_operation(session, reserve_controls=True)
        retained = self.t._operation_ordinals.attempts[-1]
        self.assertEqual(retained.ordinal, '0')
        self.assertIs(retained.controls, session._reserved_controls)
        self.assertEqual(retained.controls.initial_root.held_cleanup, 2)
        self.assertTrue(session.admission_closed)

    def test_initial_root_publication_fault_retains_both_original_owners(self):
        from truss._native_arbitration import NativeOperationSession
        session = self.service.bind(self.attempt)
        before = self.boundary.last_call
        original = NativeOperationSession._publish_call_root
        def lost(owner, root):
            original(owner, root)
            raise MemoryError('initial root reply lost')
        with patch.object(NativeOperationSession, '_publish_call_root', lost):
            with self.assertRaises(MemoryError):
                self.service.issue_operation(session, reserve_controls=True)
        retained = self.t._operation_ordinals.attempts[-1]
        self.assertIs(retained.controls, session._reserved_controls)
        self.assertIs(session._call_root, retained.controls.initial_root)
        self.assertIsNone(retained.ordinal)
        self.assertTrue(session.admission_closed)
        self.assertIs(self.boundary.last_call, before)
        with self.assertRaises(NativeBoundaryRefusal):
            self.service.issue_operation(session, reserve_controls=True)

    def test_initial_root_prepublication_fault_retains_both_original_owners(self):
        from truss._native_arbitration import NativeOperationSession
        session = self.service.bind(self.attempt)
        before = self.boundary.last_call
        previous = session._call_root
        with patch.object(NativeOperationSession, '_publish_call_root',
                          side_effect=MemoryError('initial root allocation reply')):
            with self.assertRaises(MemoryError):
                self.service.issue_operation(session, reserve_controls=True)
        retained = self.t._operation_ordinals.attempts[-1]
        self.assertIs(retained.controls, session._reserved_controls)
        self.assertIs(session._call_root, previous)
        self.assertIsNone(retained.ordinal)
        self.assertTrue(session.admission_closed)
        self.assertIs(self.boundary.last_call, before)
        with self.assertRaises(NativeBoundaryRefusal):
            self.service.issue_operation(session, reserve_controls=True)

    def test_original_reserved_savepoint_rollback_release_uses_preallocated_branches(self):
        session = self.service.bind(self.attempt)
        issued = self.service.issue_operation(session, reserve_controls=True)
        controls = issued.controls
        controls.run_control('savepoint')
        self.assertIs(session._call_root, controls.savepoint_root)
        self.assertTrue(controls.savepoint_entry.native_call.capture_complete)
        controls.run_control('rollback_to')
        self.assertEqual(session._call_root.held_cleanup, 1)
        controls.run_control('release')
        self.assertEqual(session._call_root.held_cleanup, 0)
        self.assertEqual(session.cleanup_calls, (controls.rollback_entry, controls.release_entry))
        self.assertIsNone(session._call_root.retirement_state)
        self.assertFalse(session.generation.ended)
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): controls.run_control('release')
        self.assertIs(self.boundary.last_call, before)

    def test_original_reserved_success_release_retires_only_after_native_confirmation(self):
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        controls.run_control('savepoint')
        controls.run_control('release')
        self.assertEqual(session.cleanup_calls, (controls.release_entry,))
        self.assertEqual(session._call_root.held_cleanup, 0)
        self.assertIsNone(controls.rollback_entry.native_call)
        self.assertFalse(session.generation.ended)

    def test_reserved_control_rejects_sql_override_before_native_submission(self):
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        before = self.boundary.last_call
        original = self.t._control
        def altered(kind, sql, **kwargs):
            return original(kind, 'SELECT 99', **kwargs)
        with patch.object(self.t, '_control', altered):
            with self.assertRaisesRegex(NativeBoundaryRefusal, 'control SQL'):
                controls.run_control('savepoint')
        self.assertIs(self.boundary.last_call, before)
        self.assertIsNone(controls.savepoint_entry.native_call)
        self.assertEqual(session.calls, ())

    def test_reserved_control_rejects_foreign_callback_with_matching_metadata(self):
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        before = self.boundary.last_call
        with patch.object(self.boundary, '_call', side_effect=MemoryError('unsent invocation')):
            with self.assertRaises(MemoryError): controls.run_control('savepoint')
        permit = controls.savepoint_permit
        self.assertIsNotNone(permit.control)
        invoked = []
        with self.assertRaises(NativeBoundaryRefusal):
            self.boundary._call(lambda: invoked.append(True), self.token,
                                lifecycle=permit.control, call_permit=permit)
        self.assertEqual(invoked, [])
        self.assertIs(self.boundary.last_call, before)
        self.assertEqual(session.calls, ())

    def test_unused_cleanup_permit_rejects_unregistered_invocation_record(self):
        from truss._native_transactions import _Control, _ControlInvocation
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        controls.run_control('savepoint')
        handle = self.port._savepoints[controls.savepoint_name]
        control = _Control('rollback_to', self.t._state, savepoint=handle)
        invoked = []
        foreign = _ControlInvocation(self.t, control, lambda: invoked.append(True),
                                     'ROLLBACK TO SAVEPOINT ' + self.t._name(handle.name))
        before = self.boundary.last_call
        with self.boundary._lock:
            with self.assertRaisesRegex(NativeBoundaryRefusal, 'tracker control invocation'):
                session._bind_reserved_control(controls.rollback_permit, foreign)
        self.assertEqual(invoked, [])
        self.assertIsNone(controls.rollback_permit.invoke)
        self.assertIs(self.boundary.last_call, before)

    def test_expired_settlement_deadline_preserves_unused_containment(self):
        from truss._native_deadline import NativeOperationDeadline, NativeDeadlineExpired
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        controls.run_control('savepoint')
        session.deadline = NativeOperationDeadline(1000, 1000)
        session.deadline.settlement_cutoff_ns = 0
        before = self.boundary.last_call
        root = session._call_root
        with self.assertRaises(NativeDeadlineExpired): controls.run_control('rollback_to')
        self.assertIs(self.boundary.last_call, before)
        self.assertIs(session._call_root, root)
        self.assertIsNone(controls.rollback_entry.native_call)
        self.assertFalse(session.generation.ended)

    def test_reserved_containment_remains_usable_after_executor_disposal(self):
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        controls.run_control('savepoint')
        self.executor.dispose()
        controls.run_control('rollback_to')
        controls.run_control('release')
        self.assertEqual(session._call_root.held_cleanup, 0)
        self.assertFalse(session.generation.ended)

    def _assert_release_retirement_fault(self, after):
        from truss._native_arbitration import NativeOperationSession
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        controls.run_control('savepoint')
        retired = session._call_root.release_state.retirement_state
        original = NativeOperationSession._publish_call_root
        def lost(owner, root):
            if root is retired:
                if after: original(owner, root)
                raise MemoryError('retirement reply lost')
            return original(owner, root)
        with patch.object(NativeOperationSession, '_publish_call_root', lost):
            with self.assertRaises(MemoryError): controls.run_control('release')
        self.assertTrue(session.admission_closed)
        self.assertTrue(controls.release_entry.native_call.capture_complete)
        self.assertEqual(session._call_root.held_cleanup, 0 if after else 1)
        self.assertFalse(session.generation.ended)
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): self.boundary.run('SELECT 1', token=self.token)
        self.assertIs(self.boundary.last_call, before)

    def test_release_retirement_prepublication_fault_retains_exclusion(self):
        self._assert_release_retirement_fault(False)

    def test_release_retirement_lost_reply_retains_exclusion(self):
        self._assert_release_retirement_fault(True)

    def test_port_retention_exhaustion_refuses_before_ordinal_or_sql(self):
        session = self.service.bind(self.attempt)
        port = session.context.custody.port
        port._control_records = (object(),) * 4094
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):
            self.service.issue_operation(session, reserve_controls=True)
        self.assertIsNone(self.t._operation_ordinals.attempts[-1].ordinal)
        self.assertIs(self.boundary.last_call, before)

    def test_tracker_retention_exhaustion_refuses_before_ordinal_or_sql(self):
        session = self.service.bind(self.attempt)
        self.t._control_invocations = (object(),) * 4094
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):
            self.service.issue_operation(session, reserve_controls=True)
        self.assertIsNone(self.t._operation_ordinals.attempts[-1].ordinal)
        self.assertIs(self.boundary.last_call, before)

    def test_joint_owner_partial_publication_closes_issuance(self):
        from truss._native_transactions import NativeTransactions
        session = self.service.bind(self.attempt)
        before = self.boundary.last_call
        with patch.object(NativeTransactions, '_publish_invocation_retention',
                          side_effect=MemoryError('second owner publication')):
            with self.assertRaises(MemoryError):
                self.service.issue_operation(session, reserve_controls=True)
        controls = session._reserved_controls
        self.assertIs(controls, self.t._operation_ordinals.attempts[-1].controls)
        self.assertFalse(controls.retention.ready())
        self.assertTrue(session.admission_closed)
        self.assertIsNone(controls.attempt.ordinal)
        self.assertIs(self.boundary.last_call, before)
        with self.assertRaises(NativeBoundaryRefusal): controls.run_control('savepoint')
        self.assertIs(self.boundary.last_call, before)

    def test_reserved_cleanup_survives_full_owner_retention(self):
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        port = controls.port
        port._control_records += (object(),) * (4096 - len(port._control_records))
        self.t._control_invocations += (object(),) * (4096 - len(self.t._control_invocations))
        controls.run_control('savepoint')
        controls.run_control('release')
        self.assertEqual(len(port._control_records), 4096)
        self.assertEqual(len(self.t._control_invocations), 4096)
        self.assertTrue(controls.retention.slots[1].retired)
        self.assertIsNone(controls.retention.slots[1].invocation)
        self.assertIsNone(controls.retention.records[1].native_call)

    def test_lost_invocation_slot_fill_preserves_one_use_and_closes_admission(self):
        from truss._native_transactions import NativeTransactions
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        before = self.boundary.last_call
        original = NativeTransactions._publish_control_invocation
        def lost(tracker, slot, invocation):
            original(tracker, slot, invocation)
            raise MemoryError('lost slot fill reply')
        with patch.object(NativeTransactions, '_publish_control_invocation', lost):
            with self.assertRaises(MemoryError): controls.run_control('savepoint')
        slot = controls.retention.slots[0]
        retained = slot.invocation
        self.assertIsNotNone(retained)
        self.assertTrue(session.admission_closed)
        self.assertIsNone(controls.savepoint_entry.native_call)
        self.assertIs(self.boundary.last_call, before)
        with self.assertRaises(NativeBoundaryRefusal): controls.run_control('savepoint')
        self.assertIs(slot.invocation, retained)
        self.assertIs(self.boundary.last_call, before)

    def test_direct_tracker_cannot_consume_unclaimed_port_record(self):
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        controls.run_control('savepoint')
        handle = controls.savepoint_permit.control.savepoint
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):
            self.t.rollback_to(handle, token=self.token, cleanup=session.cleanup_permit,
                               call_permit=controls.rollback_permit)
        self.assertIsNone(controls.retention.slots[1].invocation)
        self.assertEqual(controls.retention.records[1].phase, 'reserved')
        self.assertIs(self.boundary.last_call, before)
        controls.run_control('rollback_to')
        controls.run_control('release')

    def test_hostile_permit_is_not_dereferenced_or_retained(self):
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        controls.run_control('savepoint')
        class Hostile:
            @property
            def controls(self):
                raise AssertionError('foreign permit dereferenced')
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):
            self.t.rollback_to(controls.savepoint_permit.control.savepoint,
                               token=self.token, cleanup=session.cleanup_permit,
                               call_permit=Hostile())
        self.assertIsNone(controls.retention.slots[1].invocation)
        self.assertIs(self.boundary.last_call, before)
        controls.run_control('release')

    def test_initial_port_hostile_permit_preserves_namespace_and_slots(self):
        session = self.service.bind(self.attempt)
        controls = self.service.issue_operation(session, reserve_controls=True).controls
        issued = next(item for ns in session.generation.namespaces for item in ns.issued
                      if item.name == controls.savepoint_name)
        class Hostile:
            @property
            def controls(self):
                raise AssertionError('foreign permit dereferenced')
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal):
            controls.port.control('SAVEPOINT ' + controls.savepoint_name, call_permit=Hostile())
        self.assertFalse(issued.submitted)
        self.assertIsNone(controls.retention.slots[0].invocation)
        self.assertEqual(controls.retention.records[0].phase, 'reserved')
        self.assertIs(self.boundary.last_call, before)
        controls.run_control('savepoint')
        controls.run_control('release')
