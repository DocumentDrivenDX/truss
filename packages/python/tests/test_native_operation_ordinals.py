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
