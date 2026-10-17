"""Basic owned-action settlement custody; no action authority claim."""
import unittest
from unittest.mock import Mock,patch
from psycopg import pq
from truss._engine_action_session import _EngineActionSession
from truss._scram_preparation_login import ScramPreparationLogin
from truss.engine_import import _EngineImportSession
from truss.execution import Ok,ExecutionFailure

class EngineActionSessionTests(unittest.TestCase):
    def session(self):
        return _EngineActionSession(ScramPreparationLogin('/unused',5432,'postgres','person','test-secret'))

    def adopted(self):
        session=self.session();session._phase='active'
        connection=Mock();connection.closed=False;connection.broken=False;connection.autocommit=True
        connection.info.backend_pid=123;connection.info.transaction_status=pq.TransactionStatus.INTRANS
        connection.pgconn.pipeline_status=pq.PipelineStatus.OFF
        session.connection=session._original_connection=connection;session._backend_pid=123
        session.host=session._original_host=Mock();session.host.detach.return_value=True
        session.host._run_operation.return_value=Ok(None)
        session._transaction=object()
        return session

    def control(self,status,cleanup_error=False):
        session=_EngineImportSession('unused',1000,1000)
        connection=Mock();connection.info.transaction_status=status
        cursor=connection.execute.return_value;cursor.statusmessage='COMMIT'
        if cleanup_error:cursor.close.side_effect=RuntimeError('cleanup')
        session.connection=connection
        deadline=Mock();deadline.finish.return_value=True
        committed,rolled=object(),object()
        with patch('truss.psycopg_host._Deadline',return_value=deadline):
            result=session.control('COMMIT',{'COMMIT':committed,'ROLLBACK':rolled})
        return session,committed,result

    def test_native_tag_requires_matching_idle(self):
        session,committed,(observed,error)=self.control(pq.TransactionStatus.INTRANS)
        self.assertIsNone(observed);self.assertIsNone(session.last_settlement)
        self.assertEqual(error.code,'commit_unknown')

    def test_native_ack_survives_later_cleanup_error(self):
        session,committed,(observed,error)=self.control(pq.TransactionStatus.IDLE,True)
        self.assertIs(observed,committed);self.assertIs(session.last_settlement,committed)
        self.assertEqual(error.code,'transaction_unusable')

    def test_unknown_completion_has_no_second_attempt(self):
        session=self.adopted();error=ExecutionFailure('commit_unknown','original acknowledgement missing')
        def unknown(command,settlements):session.submitted=True;return None,error
        session.control=Mock(side_effect=unknown)
        committed,rolled=object(),object()
        self.assertEqual(session.complete(commit=True,committed=committed,rolled_back=rolled),(None,error))
        self.assertEqual(session.completion_observation().disposition,'unknown')
        with self.assertRaises(ValueError):session.complete(commit=True,committed=committed,rolled_back=rolled)
        session.control.assert_called_once()

    def test_settlement_uses_remaining_absolute_deadline(self):
        session=self.adopted();committed,rolled=object(),object()
        session.control=Mock(return_value=(committed,None))
        with patch('truss._engine_action_session.monotonic',return_value=session._deadline-.5):
            observed,error=session.complete(commit=True,committed=committed,rolled_back=rolled)
        self.assertIs(observed,committed);self.assertIsNone(error)
        self.assertLessEqual(session.operation_timeout_ms,500)
        self.assertEqual(session.completion_observation().disposition,'committed')

    def test_nonidle_open_is_refused_without_repair_or_reopen(self):
        session=self.adopted();connection=session.connection;session._phase='new'
        session.control=Mock()
        with patch.object(ScramPreparationLogin,'open_connection',return_value=connection) as opener:
            with self.assertRaises(ValueError):session.begin()
            with self.assertRaises(ValueError):session.begin()
        opener.assert_called_once();session.control.assert_not_called()
        session.close();connection.close.assert_called_once()

    def test_foreign_connection_is_never_closed(self):
        session=self.adopted();original=session.connection;foreign=Mock();session.connection=foreign
        session.control=Mock()
        observed,error=session.complete(commit=True,committed=object(),rolled_back=object())
        self.assertIsNone(observed);self.assertEqual(session.completion_observation().disposition,'unresolved')
        session.control.assert_not_called();session.close()
        original.close.assert_called_once();foreign.close.assert_not_called()
