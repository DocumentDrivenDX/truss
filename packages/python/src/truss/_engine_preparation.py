"""One engine-owned RR session; does not issue authority, cuts or seals.

Only trusted native preparation orchestration may use this session. Ordinary
READ COMMITTED graph facades are not admitted by its handle. Plan handlers do
not receive this object or its connection. Native authorization/coordinator and
protected seal persistence remain separate required dependencies. Host adoption
performs native identity queries and can establish the RR snapshot; subsequent
head/source admission must revalidate that original cut, never call it fresh.
"""
from dataclasses import dataclass
from threading import RLock
import inspect
from .engine_import import _EngineImportSession
from .execution import Error,ExecutionFailure

@dataclass(frozen=True, slots=True)
class _PreparationCompletion:
    disposition: str
    acknowledged: object | None
    error: ExecutionFailure | None

class _EnginePreparationSession(_EngineImportSession):
    def __init__(self, connection_info, statement_timeout_ms, operation_timeout_ms):
        super().__init__(connection_info, statement_timeout_ms, operation_timeout_ms)
        self._opened=False
        self._adopted=False
        self._ended=False
        self._completion=None
        self._original_host=None
        self._transaction=None
        self._phase_lock=RLock()
        self._phase='new'
        self._physical_opened=False
        self._original_connection=None
        self._backend_pid=None
        self._connection_cap=None

    def _open_connection(self):
        if self._physical_opened:
            raise ValueError('Original preparation connection cannot reopen')
        self._physical_opened=True
        return super()._open_connection()

    def _idle_original(self):
        from psycopg import pq
        connection=self.connection
        if (connection is None or connection is not self._original_connection
                or connection.closed or connection.broken or not connection.autocommit
                or connection.info.backend_pid!=self._backend_pid
                or connection.info.transaction_status!=pq.TransactionStatus.IDLE
                or connection.pgconn.pipeline_status!=pq.PipelineStatus.OFF):
            raise ValueError('Original idle preparation connection required')

    def _prepare_locked(self):
        from .psycopg_host import adopt_psycopg_host
        if self._phase!='new':raise ValueError('One original preparation connection required')
        self._phase='opening'
        try:
            self.connection=self._open_connection()
            self._original_connection=self.connection
            self._backend_pid=self.connection.info.backend_pid
            self._idle_original()
            # Constructor validates the original driver/libpq/server tuple before
            # any trusted native capture dispatch. No adoption/snapshot yet.
            checked=adopt_psycopg_host(self.connection,statement_timeout_ms=self.statement_timeout_ms,
                operation_timeout_ms=self.operation_timeout_ms)
            if not checked.detach():raise ValueError('Preparation connection profile custody unresolved')
            self._connection_cap=object()
            self._phase='prepared'
            return self._connection_cap
        except BaseException:
            self._phase='poisoned';self._connection_cap=None
            raise

    def prepare_connection(self):
        """Engine-only opaque capture capability before the first RR snapshot.

        It is neither an anchor nor an authority grant. No raw connection reaches
        plan handlers; the native anchor issuer must still authenticate this peer.
        """
        with self._phase_lock:
            if self._opened:raise ValueError('Preparation already attempted')
            return self._prepare_locked()

    def capture_before_snapshot(self,capability,callback):
        from .psycopg_host import _Deadline,_GuardedCursor
        from psycopg import Cursor
        from psycopg.rows import tuple_row
        from psycopg.types.string import TextLoader
        from ._security_catalog_subject_installation import _text_rows
        with self._phase_lock:
            if (self._phase!='prepared' or self._opened or capability is not self._connection_cap
                    or not callable(callback)):
                raise ValueError('Original pre-snapshot capture capability required')
            self._phase='capturing'
            deadline=None;cursor=None;raw_cursor=None;value=None;failure=None
            try:
                self._idle_original()
                deadline=_Deadline(self.connection,self.operation_timeout_ms)
                raw_cursor=Cursor(self.connection,row_factory=tuple_row)
                raw_cursor.adapters.register_loader(25,TextLoader)
                cursor=_GuardedCursor(raw_cursor,deadline)
                query="""SELECT a.datid::pg_catalog.text,a.usesysid::pg_catalog.text,a.pid::pg_catalog.text,a.backend_start::pg_catalog.text,
                    session_user::pg_catalog.text,current_user::pg_catalog.text,pg_catalog.current_setting('role')::pg_catalog.text
                    FROM pg_catalog.pg_stat_activity a WHERE a.pid OPERATOR(pg_catalog.=) pg_catalog.pg_backend_pid()"""
                before=_text_rows(cursor,query,limit=1)
                if len(before)!=1 or before[0][4]!=before[0][5] or before[0][6]!='none':
                    raise ValueError('Original native preparation person required')
                value=callback(cursor)
                if inspect.isawaitable(value) or inspect.isgenerator(value) or inspect.isasyncgen(value):
                    if inspect.iscoroutine(value) or inspect.isgenerator(value):value.close()
                    raise ValueError('Synchronous materialized native capture required')
                if cursor._cursor is not raw_cursor:raise ValueError('Original native capture cursor replaced')
                raw_cursor.row_factory=tuple_row
                raw_cursor.adapters.register_loader(25,TextLoader)
                if _text_rows(cursor,query,limit=1)!=before:
                    raise ValueError('Original physical preparation identity changed')
            except BaseException as error:failure=error
            finally:
                try:
                    if raw_cursor is not None:raw_cursor.close()
                except BaseException as error:
                    if failure is None:failure=error
                try:
                    if deadline is not None:
                        if not deadline.finish():raise ValueError('Native preparation capture cancellation unresolved')
                        deadline.check()
                except BaseException as error:
                    if failure is None:failure=error
            try:self._idle_original()
            except BaseException as error:
                if failure is None:failure=error
            if failure is not None:
                self._phase='poisoned';self._connection_cap=None
                raise failure
            self._phase='prepared'
            return value

    def begin(self):
        from .psycopg_host import adopt_psycopg_host
        with self._phase_lock:
            if self._opened:raise ValueError('Original preparation session cannot restart')
            self._opened=True
            try:
                if self._phase=='new':self._prepare_locked()
                if self._phase!='prepared':raise ValueError('Original preparation prephase unavailable')
                self._idle_original()
                self._connection_cap=None
                self._phase='beginning'
                _,error=self.control('BEGIN ISOLATION LEVEL REPEATABLE READ READ WRITE',None)
                if error is not None:raise ValueError('Original preparation BEGIN unavailable')
                self.host=adopt_psycopg_host(self.connection,statement_timeout_ms=self.statement_timeout_ms,
                    operation_timeout_ms=self.operation_timeout_ms)
                adopted=self.host.adopt_transaction(isolation='repeatable_read',access_mode='read_write')
                if isinstance(adopted,Error):raise ValueError('Original preparation adoption unavailable')
                self._original_host,self._transaction=self.host,adopted.value
                self._adopted=True;self._phase='begun'
                return self.host,self._transaction
            except BaseException:
                self._phase='poisoned';self._connection_cap=None
                raise

    def close(self):
        with self._phase_lock:
            if self._phase=='capturing':raise ValueError('Cannot close during native capture')
            self._phase='closed';self._connection_cap=None
            return super().close()

    def run_operation(self, callback):
        """Trusted native adapter callback under the original adopted custody.

        This is not a plan-handler SQL port or an authority admission grant.
        """
        if (not self._adopted or self._ended or self.host is not self._original_host
                or self._original_host is None):
            return Error(ExecutionFailure('invalid_transaction','Original preparation transaction required'))
        return self._original_host._run_operation(self._transaction,callback)

    def complete(self, *, commit, committed, rolled_back):
        with self._phase_lock:
            return self._complete_locked(commit=commit,committed=committed,rolled_back=rolled_back)

    def _complete_locked(self, *, commit, committed, rolled_back):
        """Retain the original native acknowledgement before cleanup.

        Tokens are private orchestration outcomes, never commit evidence on their
        own. Missing acknowledgement stays unknown; this method never retries.
        """
        if (type(commit) is not bool or not self._opened or self._ended
                or not self._adopted
                or committed is None or rolled_back is None or committed is rolled_back):
            raise ValueError('One original preparation completion required')
        custody=self.run_operation(lambda cursor,observed:None)
        self._ended=True
        if isinstance(custody,Error):
            self._completion=_PreparationCompletion('unresolved',None,custody.error)
            return None,custody.error
        if self.host is not None:
            if not self.host.detach():
                self.reconnect=True
                error=ExecutionFailure('transaction_unusable','Preparation operation completion unresolved')
                self._completion=_PreparationCompletion('unresolved',None,error)
                return None,error
            self.host=None
        if self.reconnect or self.connection is None:
            error=ExecutionFailure('transaction_unusable','Preparation session custody unresolved')
            self._completion=_PreparationCompletion('unresolved',None,error)
            return None,error
        self.submitted=False
        interrupted=None
        try:
            observed,error=self.control('COMMIT' if commit else 'ROLLBACK',
                {'COMMIT':committed,'ROLLBACK':rolled_back})
        except BaseException as failure:
            if not isinstance(failure,Exception):interrupted=failure
            observed=self.last_settlement
            if observed is not committed and observed is not rolled_back:observed=None
            code='commit_unknown' if commit and self.submitted and observed is None else 'transaction_unusable'
            error=ExecutionFailure(code,'Original preparation completion unavailable')
        disposition=('committed' if observed is committed else 'rolled_back' if observed is rolled_back
            else 'unknown' if commit and self.submitted else 'unresolved')
        self._completion=_PreparationCompletion(disposition,observed,error)
        if interrupted is not None:raise interrupted
        return observed,error

    def completion_observation(self):
        """Original in-process acknowledgement only; never receipt-based inference.

        Missing state is not rollback. Cross-process recovery and authorized seal
        disclosure require the protected native attempt/receipt provider. Closing
        a connection does not change this retained disposition.
        """
        return self._completion
