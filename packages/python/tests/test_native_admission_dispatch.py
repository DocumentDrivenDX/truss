"""Administrative issued-candidate dispatch only; synthetic artifacts grant no authority."""
from pathlib import Path
from unittest.mock import patch
from truss._native_operation_ordinals import NativeOperationOrdinals
from truss._native_admission_capture import NativeAdmissionCapture
from truss._native_deadline import NativeOperationDeadline
from test_native_operation_ordinals import ReservedNativeOperationOrdinalTests
from truss._native_admission_request import NativeAdmissionInput
from truss._native_pg8000 import NativeBoundaryRefusal

class NativeAdmissionDispatchTests(ReservedNativeOperationOrdinalTests):
    def test_losing_capture_install_preserves_winning_custody(self):
        from truss._native_result_custody import NativeTextLimits
        session, issued, request = self._prepare('base')
        winner = NativeAdmissionCapture(session, NativeTextLimits(columns=4, rows=1), entry=request.entry)
        install = NativeAdmissionCapture.install
        def compete(loser):
            install(winner)
            return install(loser)
        with patch.object(NativeAdmissionCapture, 'install', compete):
            with self.assertRaises(NativeBoundaryRefusal):
                issued.owner.dispatch_admission_candidate(request)
        self.assertIs(session.result_custody, winner)
        self.assertFalse(session.admission_closed)
        self.assertIsNone(request.entry.native_call)
        issued.controls.run_control('rollback_to')
        issued.controls.run_control('release')
        self.assertIs(session.result_custody, winner)

    def _prepare(self, family, *, denied=False):
        root = Path(__file__).resolve().parents[3]
        setup = (root/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text()
        setup += ';\n' + (root/'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql').read_text()
        setup += ';\n' + (root/'packages/postgresql/native/source-epoch-lock.sql').read_text()
        setup += ';\n' + (root/'docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql').read_text().split('INSERT INTO truss.row_home_operation')[0]
        setup += "INSERT INTO truss.source_epoch_current VALUES (1,'guard-fixture','guard-fixture-epoch');"
        setup += "INSERT INTO truss.installation_admission (head_id,installation_id_utf8,source_epoch_utf8,configuration_generation,key_reuse,journal_mode,configuration_bytes,selected_binding_bytes,installed_inventory_bytes) VALUES (1,convert_to('guard-fixture','UTF8'),convert_to('guard-fixture-epoch','UTF8'),7,'forbid','engine',decode('0001ff','hex'),convert_to('binding fixture','UTF8'),convert_to('inventory fixture','UTF8'));"
        for name in ('operation-admission.sql', 'operation-asserted-origin-admission.sql', 'operation-epoch-context-admission.sql', 'operation-configuration-context-admission.sql'):
            setup += ';\n' + (root/'packages/postgresql/native/issued-operation-admission'/name).read_text()
        setup += '; CREATE TEMP TABLE caller_sentinel(value int); INSERT INTO caller_sentinel VALUES (7);'
        self.boundary.run(setup, token=self.token)
        if denied:
            self.boundary.run('CREATE ROLE truss_candidate_denied; GRANT USAGE ON SCHEMA truss TO truss_candidate_denied; SET LOCAL ROLE truss_candidate_denied', token=self.token)
        session = self.service.bind(self.attempt)
        session.deadline = NativeOperationDeadline(30000, 5000)
        issued = self.service.issue_operation(session, reserve_controls=True)
        issued.controls.run_control('savepoint')
        fields = dict(family=family, kind='mutation', artifacts=tuple(bytes([i]) for i in range(1,7)))
        if family != 'base': fields.update(asserted=b'original asserted fixture', capture_profile=b'original capture profile fixture')
        if family in ('epoch', 'configuration'): fields.update(installation='guard-fixture', source_epoch='guard-fixture-epoch', incarnation='guard-fixture-incarnation')
        if family == 'configuration': fields['configuration_profile']=b'configuration admission fixture'
        request = issued.owner.prepare_admission(issued, NativeAdmissionInput(**fields))
        return session, issued, request

    def _restore(self, session, issued):
        issued.controls.run_control('rollback_to')
        issued.controls.run_control('release')
        session.result_custody.detach()
        self.assertEqual(self.connection.run('SELECT value FROM caller_sentinel'), [[7]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'), [[0]])

    def _exercise(self, family):
        session, issued, request = self._prepare(family)
        observation = issued.owner.dispatch_admission_candidate(request)
        self.assertEqual(observation.ordinal, issued.ordinal)
        self.assertIs(observation.original_call, request.entry.native_call)
        self.assertFalse(issued.controls.forward_ready)
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.dispatch_admission_candidate(request)
        self.assertIs(self.boundary.last_call, before)
        self._restore(session, issued)

    def test_base_candidate_dispatch(self): self._exercise('base')
    def test_asserted_candidate_dispatch(self): self._exercise('asserted')
    def test_epoch_candidate_dispatch(self): self._exercise('epoch')
    def test_configuration_candidate_dispatch(self): self._exercise('configuration')

    def _publication_fault(self, after):
        session, issued, request = self._prepare('base')
        before = self.boundary.last_call
        original = NativeOperationOrdinals._publish_admission_invocations
        def fault(owner, root):
            if after: original(owner, root)
            raise MemoryError('invocation publication fault')
        with patch.object(NativeOperationOrdinals, '_publish_admission_invocations', fault):
            with self.assertRaises(MemoryError): issued.owner.dispatch_admission_candidate(request)
        self.assertIs(self.boundary.last_call, before)
        self.assertIsNone(request.entry.native_call)
        self.assertTrue(session.admission_closed)
        self.assertEqual(len(issued.owner.admission_invocations), 1 if after else 0)
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.dispatch_admission_candidate(request)
        self._restore(session, issued)

    def test_invocation_prepublication_fault_preserves_host_work(self):
        self._publication_fault(False)

    def test_invocation_lost_publication_reply_preserves_host_work(self):
        self._publication_fault(True)

    def test_lost_observation_reply_retains_native_call_without_replay(self):
        session, issued, request = self._prepare('base')
        original = NativeAdmissionCapture.observe
        def lost(gate, rows, call, ordinal):
            original(gate, rows, call, ordinal)
            raise MemoryError('observation reply lost')
        with patch.object(NativeAdmissionCapture, 'observe', lost):
            with self.assertRaises(MemoryError): issued.owner.dispatch_admission_candidate(request)
        self.assertTrue(request.entry.native_call.capture_complete)
        self.assertTrue(session.admission_closed)
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.dispatch_admission_candidate(request)
        self.assertIs(self.boundary.last_call, before)
        self._restore(session, issued)

    def test_native_acl_refusal_preserves_host_work_without_retry(self):
        from pg8000.exceptions import DatabaseError
        session, issued, request = self._prepare('base', denied=True)
        with self.assertRaises(DatabaseError) as raised:
            issued.owner.dispatch_admission_candidate(request)
        self.assertEqual(raised.exception.args[0]['C'], '42501')
        self.assertTrue(request.entry.native_call.capture_complete)
        self.assertTrue(request.entry.native_call.driver_raised)
        self.assertEqual(request.entry.native_call.final_status, b'E')
        self.assertTrue(session.admission_closed)
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.dispatch_admission_candidate(request)
        self.assertIs(self.boundary.last_call, before)
        issued.controls.run_control('rollback_to')
        issued.controls.run_control('release')
        session.result_custody.detach()
        self.connection.run('RESET ROLE')
        self.assertEqual(self.connection.run('SELECT value FROM caller_sentinel'), [[7]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'), [[0]])

    def _entry_publication_fault(self, after):
        from truss._native_arbitration import NativeOperationSession
        session, issued, request = self._prepare('base')
        before = self.boundary.last_call
        original = NativeOperationSession._publish_call_root
        def fault(owner, root):
            if root is issued.controls.admission_root:
                if after: original(owner, root)
                raise MemoryError('admission entry publication fault')
            return original(owner, root)
        with patch.object(NativeOperationSession, '_publish_call_root', fault):
            with self.assertRaises(MemoryError): issued.owner.dispatch_admission_candidate(request)
        self.assertIs(self.boundary.last_call, before)
        self.assertIsNone(request.entry.native_call)
        self.assertTrue(session.admission_closed)
        self.assertEqual(self.boundary._quarantined, after)
        self.assertFalse(session.generation.ended)
        if after:
            with self.assertRaises(NativeBoundaryRefusal): issued.controls.run_control('rollback_to')
            self.assertIs(self.boundary.last_call, before)
        else:
            self._restore(session, issued)

    def test_admission_entry_prepublication_fault_preserves_host_work(self):
        self._entry_publication_fault(False)

    def test_admission_entry_lost_reply_retains_exclusion_without_native_call(self):
        self._entry_publication_fault(True)

    def test_missing_deadline_refuses_before_capture_installation(self):
        session, issued, request = self._prepare('base')
        session.deadline = None
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.dispatch_admission_candidate(request)
        self.assertIsNone(session.result_custody)
        self.assertIs(self.boundary.last_call, before)
        self.assertEqual(issued.owner.admission_invocations, ())
        session.deadline = issued.deadline
        issued.controls.run_control('release')

    def test_replaced_deadline_cannot_restart_operation_allowance(self):
        session, issued, request = self._prepare('base')
        session.deadline = NativeOperationDeadline(30000, 5000)
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.dispatch_admission_candidate(request)
        self.assertIsNone(session.result_custody)
        self.assertIs(self.boundary.last_call, before)
        session.deadline = issued.deadline
        issued.controls.run_control('release')

    def test_driver_run_mutation_refuses_before_capture_installation(self):
        session, issued, request = self._prepare('base')
        before = self.boundary.last_call
        original = self.connection.run
        with patch.object(self.connection, 'run', lambda *args, **kwargs: original(*args, **kwargs)):
            with self.assertRaises(NativeBoundaryRefusal): issued.owner.dispatch_admission_candidate(request)
        self.assertIsNone(session.result_custody)
        self.assertIs(self.boundary.last_call, before)
        issued.controls.run_control('release')

    def test_send_fault_retains_context_before_native_submission(self):
        from truss._native_outbound import NativeOutbound
        from pg8000.exceptions import InterfaceError
        session, issued, request = self._prepare('base')
        with patch.object(NativeOutbound, 'write', side_effect=OSError('send fault')):
            with self.assertRaises(InterfaceError): issued.owner.dispatch_admission_candidate(request)
        invocation = issued.owner.admission_invocations[-1]
        self.assertIs(invocation.gate.admission_context, invocation.context)
        self.assertIs(invocation.gate.contexts[0], invocation.context)
        self.assertEqual(invocation.gate.context_count, 1)
        self.assertFalse(request.entry.native_call.capture_complete)
        self.assertTrue(session.admission_closed)
        self.assertTrue(self.boundary._quarantined)
        self.assertFalse(session.generation.ended)

    def test_flush_fault_retains_context_without_replay(self):
        from truss._native_outbound import NativeOutbound
        from pg8000.exceptions import InterfaceError
        session, issued, request = self._prepare('base')
        original = NativeOutbound.flush
        def lost(sock):
            original(sock)
            raise OSError('flush reply lost')
        with patch.object(NativeOutbound, 'flush', lost):
            with self.assertRaises(InterfaceError): issued.owner.dispatch_admission_candidate(request)
        invocation = issued.owner.admission_invocations[-1]
        self.assertIs(invocation.gate.admission_context, invocation.context)
        self.assertFalse(request.entry.native_call.capture_complete)
        self.assertTrue(self.boundary._quarantined)
        before = self.boundary.last_call
        with self.assertRaises(NativeBoundaryRefusal): issued.owner.dispatch_admission_candidate(request)
        self.assertIs(self.boundary.last_call, before)

    def test_replaced_context_or_flush_refuses_before_capture_and_sql(self):
        import pg8000.core as core
        from truss._native_driver_profile import original_admission_symbols
        session, issued, request = self._prepare('base')
        before = self.boundary.last_call
        original_context, original_flush = original_admission_symbols()
        for name, replacement in (('Context', lambda sql: original_context(sql, stream=object())),
                                   ('_flush', lambda sock: original_flush(sock))):
            with self.subTest(symbol=name), patch.object(core, name, replacement):
                self.assertIsNone(original_admission_symbols())
                with self.assertRaises(NativeBoundaryRefusal):
                    issued.owner.dispatch_admission_candidate(request)
            self.assertIsNone(session.result_custody)
            self.assertIs(self.boundary.last_call, before)
        issued.controls.run_control('release')
