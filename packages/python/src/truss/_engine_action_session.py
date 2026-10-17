"""Private one-invocation RC lifetime; native settlement is not action authority."""
from dataclasses import dataclass
from time import monotonic
from psycopg import pq
from .engine_import import _EngineImportSession
from .execution import Error, ExecutionFailure
from .psycopg_host import adopt_psycopg_host
from ._scram_preparation_login import ScramPreparationLogin


@dataclass(frozen=True, slots=True)
class _ActionCompletion:
    disposition: str
    acknowledged: object | None
    error: ExecutionFailure | None


class _EngineActionSession(_EngineImportSession):
    def __init__(self, login, statement_timeout_ms=10000, operation_timeout_ms=30000):
        if (type(login) is not ScramPreparationLogin
                or type(statement_timeout_ms) is not int or not 1<=statement_timeout_ms<=10000
                or type(operation_timeout_ms) is not int or not 1<=operation_timeout_ms<=30000):
            raise ValueError('Original SCRAM action session and bounded deadlines required')
        super().__init__(None,statement_timeout_ms,operation_timeout_ms)
        self._login=login
        self._deadline=monotonic()+operation_timeout_ms/1000
        self._phase='new'
        self._original_connection=None
        self._backend_pid=None
        self._transaction=None
        self._original_host=None
        self._completion=None

    def _remaining(self):
        remaining=int((self._deadline-monotonic())*1000)
        if remaining<1:raise TimeoutError('Original action deadline expired')
        return remaining

    def _original(self, status):
        connection=self.connection
        if (connection is None or connection is not self._original_connection
                or connection.closed or connection.broken or not connection.autocommit
                or connection.info.backend_pid!=self._backend_pid
                or connection.info.transaction_status!=status
                or connection.pgconn.pipeline_status!=pq.PipelineStatus.OFF):
            raise ValueError('Original action connection and transaction required')

    def begin(self):
        if self._phase!='new':raise ValueError('One original action connection required')
        self._phase='opening'
        try:
            self._remaining()
            login=self._login;self._login=None
            self.connection=login.open_connection()
            self._original_connection=self.connection
            self._backend_pid=self.connection.info.backend_pid
            self._original(pq.TransactionStatus.IDLE)
            self._remaining()
            if self.statement_timeout_ms!=10000:
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT pg_catalog.set_config('statement_timeout',%s,false)",
                        (str(self.statement_timeout_ms),),prepare=False)
                    cursor.fetchone()
            self.operation_timeout_ms=self._remaining()
            _,error=self.control('BEGIN ISOLATION LEVEL READ COMMITTED READ WRITE',None)
            if error is not None:raise ValueError('Original action BEGIN unavailable')
            self._original(pq.TransactionStatus.INTRANS)
            self.host=adopt_psycopg_host(self.connection,statement_timeout_ms=self.statement_timeout_ms,
                operation_timeout_ms=self._remaining())
            self._original_host=self.host
            adopted=self.host.adopt_transaction(isolation='read_committed',access_mode='read_write')
            if isinstance(adopted,Error):raise ValueError('Original action adoption unavailable')
            self._remaining()
            self._transaction=adopted.value;self._phase='active'
            return self.host,self._transaction
        except BaseException:
            self._phase='unresolved'
            raise

    def _run_current(self, callback):
        if self.host is None or self.host is not self._original_host:
            raise ValueError('Original action host required')
        self._original(pq.TransactionStatus.INTRANS)
        return self.host._run_operation(self._transaction,callback,operation_deadline=self._deadline)

    def run_operation(self, callback):
        if self._phase!='active':
            return Error(ExecutionFailure('invalid_transaction','Original active action transaction required'))
        return self._run_current(callback)

    def complete(self, *, commit, committed, rolled_back):
        if (self._phase!='active' or type(commit) is not bool
                or committed is None or rolled_back is None or committed is rolled_back):
            raise ValueError('One original action completion required')
        self._phase='settling';self.submitted=False
        observed=None;error=None;interrupted=None
        try:
            custody=self._run_current(lambda cursor,observed:None)
            if isinstance(custody,Error):
                error=custody.error
            elif not self.host.detach():
                error=ExecutionFailure('transaction_unusable','Action operation completion unresolved')
            else:
                self.host=None
                self._original(pq.TransactionStatus.INTRANS)
                self.operation_timeout_ms=self._remaining()
                observed,error=self.control('COMMIT' if commit else 'ROLLBACK',
                    {'COMMIT':committed,'ROLLBACK':rolled_back})
        except BaseException as failure:
            if not isinstance(failure,Exception):interrupted=failure
            observed=self.last_settlement
            if observed is not committed and observed is not rolled_back:observed=None
            error=ExecutionFailure('commit_unknown' if commit and self.submitted and observed is None else 'transaction_unusable',
                'Original action completion unavailable')
        self._phase='ended'
        disposition=('committed' if observed is committed else 'rolled_back' if observed is rolled_back
            else 'unknown' if commit and self.submitted else 'unresolved')
        self._completion=_ActionCompletion(disposition,observed,error)
        if error is not None:self.reconnect=True
        if interrupted is not None:raise interrupted
        return observed,error

    def completion_observation(self):
        return self._completion

    def close(self):
        self._phase='closed';self._login=None
        self.connection=self._original_connection
        self.host=self._original_host
        super().close()
