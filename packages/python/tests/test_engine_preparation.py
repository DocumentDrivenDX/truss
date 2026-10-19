# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic lifecycle containment; no native seal qualification."""
import unittest
from unittest.mock import Mock,patch
from truss._engine_preparation import _EnginePreparationSession
from truss.engine_import import _EngineImportSession
from truss.execution import Error,Ok,ExecutionFailure

class EnginePreparationTests(unittest.TestCase):
    def session(self):return _EnginePreparationSession('unused',1000,1000)

    def adopted(self):
        session=self.session();session._opened=True;session._adopted=True;session.connection=object()
        session.host=Mock();session.host.detach.return_value=True
        session.host._run_operation.return_value=Ok(None)
        session._original_host=session.host;session._transaction=object()
        return session

    def test_failed_scram_login_has_no_default_connection_fallback(self):
        from truss._scram_preparation_login import ScramPreparationLogin
        login=ScramPreparationLogin('/unused',5432,'postgres','person','private-test-value')
        session=_EnginePreparationSession.from_scram_login(login,1000,1000)
        with patch.object(ScramPreparationLogin,'open_connection',side_effect=RuntimeError('private-test-value')) as opener, patch.object(_EngineImportSession,'_open_connection') as fallback:
            with self.assertRaisesRegex(ValueError,'^Original SCRAM preparation login refused$'):
                session.prepare_connection()
            with self.assertRaises(ValueError):session.prepare_connection()
            opener.assert_called_once();fallback.assert_not_called()
        self.assertIsNone(session._scram_login)

    def test_close_unused_scram_session_drops_factory_reference(self):
        from truss._scram_preparation_login import ScramPreparationLogin
        session=_EnginePreparationSession.from_scram_login(ScramPreparationLogin('/unused',5432,'postgres','person','private-test-value'),1000,1000)
        session.close()
        self.assertIsNone(session._scram_login)

    def test_failed_start_cannot_replace_original_cut(self):
        session=self.session()
        with patch.object(session,'_prepare_locked',side_effect=ValueError('start failed')):
            with self.assertRaises(ValueError):session.begin()
        with self.assertRaises(ValueError):session.begin()
        session.control=Mock()
        with self.assertRaises(ValueError):session.complete(commit=True,committed=object(),rolled_back=object())
        session.control.assert_not_called()

    def test_unresolved_operation_withholds_commit(self):
        session=self.adopted()
        session.host.detach.return_value=False
        session.control=Mock()
        observed,error=session.complete(commit=True,committed=object(),rolled_back=object())
        self.assertIsNone(observed);self.assertEqual(error.code,'transaction_unusable')
        session.control.assert_not_called()
        with self.assertRaises(ValueError):session.complete(commit=True,committed=object(),rolled_back=object())

    def test_unknown_commit_is_not_retried(self):
        session=self.adopted()
        error=ExecutionFailure('commit_unknown','original acknowledgement missing')
        def unknown(command,settlements):
            session.submitted=True
            return None,error
        session.control=Mock(side_effect=unknown)
        committed,rolled=object(),object()
        self.assertEqual(session.complete(commit=True,committed=committed,rolled_back=rolled),(None,error))
        session.control.assert_called_once_with('COMMIT',{'COMMIT':committed,'ROLLBACK':rolled})
        self.assertEqual(session.completion_observation().disposition,'unknown')
        self.assertIsNone(session.completion_observation().acknowledged)
        with self.assertRaises(ValueError):session.begin()
        with self.assertRaises(ValueError):session.complete(commit=True,committed=committed,rolled_back=rolled)

    def test_confirmed_commit_survives_cleanup_error(self):
        session=self.adopted()
        committed,rolled=object(),object()
        error=ExecutionFailure('transaction_unusable','cursor cleanup unresolved')
        session.control=Mock(return_value=(committed,error))
        session.complete(commit=True,committed=committed,rolled_back=rolled)
        original=session.completion_observation()
        self.assertEqual(original.disposition,'committed')
        self.assertIs(original.acknowledged,committed);self.assertIs(original.error,error)
        self.assertIs(session.completion_observation(),original)

    def test_control_exception_after_dispatch_preserves_unknown(self):
        session=self.adopted()
        def interrupted(command,settlements):
            session.submitted=True
            raise RuntimeError('transport failure')
        session.control=Mock(side_effect=interrupted)
        observed,error=session.complete(commit=True,committed=object(),rolled_back=object())
        self.assertIsNone(observed);self.assertEqual(error.code,'commit_unknown')
        self.assertEqual(session.completion_observation().disposition,'unknown')

    def test_changed_native_transaction_prevents_commit(self):
        session=self.adopted();session.control=Mock()
        error=ExecutionFailure('invalid_transaction','original transaction ended')
        session.host._run_operation.return_value=Error(error)
        observed,actual=session.complete(commit=True,committed=object(),rolled_back=object())
        self.assertIsNone(observed);self.assertIs(actual,error)
        session.control.assert_not_called()
        self.assertEqual(session.completion_observation().disposition,'unresolved')

    def test_interruption_after_ack_retains_commit(self):
        session=self.adopted();committed,rolled=object(),object()
        def interrupted(command,settlements):
            session.submitted=True;session.last_settlement=committed
            raise KeyboardInterrupt()
        session.control=Mock(side_effect=interrupted)
        with self.assertRaises(KeyboardInterrupt):
            session.complete(commit=True,committed=committed,rolled_back=rolled)
        original=session.completion_observation()
        self.assertEqual(original.disposition,'committed');self.assertIs(original.acknowledged,committed)

    def test_failed_physical_open_burns_allowance(self):
        session=self.session()
        with patch.object(_EngineImportSession,'_open_connection',side_effect=ValueError('connect failed')) as opened:
            with self.assertRaises(ValueError):session.prepare_connection()
            with self.assertRaises(ValueError):session.prepare_connection()
            with self.assertRaises(ValueError):session.begin()
            opened.assert_called_once()

    def test_foreign_capture_cap_has_no_dispatch(self):
        session=self.session();session._phase='prepared';session._connection_cap=object()
        callback=Mock()
        with self.assertRaises(ValueError):session.capture_before_snapshot(object(),callback)
        callback.assert_not_called()
