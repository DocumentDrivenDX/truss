# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual bounded protocol capture; no protected routine or artifact qualification."""
from test_native_arbitration import NativeArbitrationTests
from truss._native_admission_capture import NativeAdmissionCapture
from truss._native_result_custody import NativeTextLimits
from truss._native_pg8000 import NativeBoundaryRefusal

class NativeAdmissionCaptureTests(NativeArbitrationTests):
    def _gate(self):
        session = self.service.bind(self.attempt)
        gate = NativeAdmissionCapture(session, NativeTextLimits(columns=4, rows=1))
        gate.install()
        self.session = session
        return gate

    def test_actual_text_capture_correlates_writer_ordinal_and_context(self):
        gate = self._gate()
        rows = self.boundary.run("SELECT pg_catalog.pg_current_xact_id()::text AS writer_xid, '0'::text AS ordinal, '00ff'::text AS context_hex, pg_catalog.pg_current_xact_id()::text AS actual_writer_xid", token=self.token)
        observation = gate.observe(rows, self.boundary.last_call, '0')
        self.assertEqual(observation.original_context, b'\0\xff')
        self.assertEqual(observation.ordinal, '0')
        self.assertIs(observation.original_call, self.boundary.last_call)
        self.session.admission_closed = True
        gate.detach()

    def test_substituted_ordinal_cannot_produce_observation(self):
        gate = self._gate()
        rows = self.boundary.run("SELECT pg_catalog.pg_current_xact_id()::text AS writer_xid, '1'::text AS ordinal, '00ff'::text AS context_hex, pg_catalog.pg_current_xact_id()::text AS actual_writer_xid", token=self.token)
        with self.assertRaises(NativeBoundaryRefusal): gate.observe(rows, self.boundary.last_call, '0')
        self.session.admission_closed = True
        gate.detach()

    def test_foreign_column_name_refuses_before_driver_row_decode(self):
        gate = self._gate()
        with self.assertRaises(NativeBoundaryRefusal):
            self.boundary.run("SELECT '1'::text AS wrong, '0'::text AS ordinal, '00ff'::text AS context_hex, '1'::text AS actual_writer_xid", token=self.token)
        self.assertTrue(gate.failed)
        self.assertTrue(self.boundary._quarantined)
        self.assertEqual(gate.rows_seen, 0)

    def test_two_result_sets_refuse_duplicate_description(self):
        gate = self._gate()
        statement = "SELECT '1'::text AS writer_xid, '0'::text AS ordinal, '00ff'::text AS context_hex, '1'::text AS actual_writer_xid"
        with self.assertRaises(NativeBoundaryRefusal):
            self.boundary.run(statement + '; ' + statement, token=self.token)
        self.assertTrue(gate.failed)
        self.assertTrue(self.boundary._quarantined)

    def test_second_row_refused_before_decode(self):
        gate = self._gate()
        with self.assertRaises(NativeBoundaryRefusal):
            self.boundary.run("SELECT '1'::text AS writer_xid, '0'::text AS ordinal, '00ff'::text AS context_hex, '1'::text AS actual_writer_xid FROM generate_series(1,2)", token=self.token)
        self.assertEqual(gate.rows_seen, 1)
        self.assertTrue(gate.failed)

    def test_cleanup_call_cannot_borrow_admission_rows(self):
        gate = self._gate()
        rows = self.boundary.run("SELECT pg_catalog.pg_current_xact_id()::text AS writer_xid, '0'::text AS ordinal, '00ff'::text AS context_hex, pg_catalog.pg_current_xact_id()::text AS actual_writer_xid", token=self.token)
        self.boundary.run("SELECT 'cleanup'::text", token=self.token, cleanup=self.session.cleanup_permit)
        with self.assertRaises(NativeBoundaryRefusal): gate.observe(rows, self.boundary.last_call, '0')
        self.session.admission_closed = True
        gate.detach()
