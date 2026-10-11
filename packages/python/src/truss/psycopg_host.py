"""Supported synchronous psycopg host adoption; no graph or commit authority.

The caller owns the connection and outer transaction. Raw aliases must remain
unused during toolkit operations. The host may settle its transaction between calls. This initial selected tuple is local evidence,
not a claim of Lakebase, other libpq implementations or complete installation.
"""
from ._runtime_profile import SERVER_VERSION_NUM
from dataclasses import dataclass
from threading import Lock, Event, Timer
from time import monotonic
from uuid import uuid4
from weakref import WeakKeyDictionary, ref
from .execution import AccessMode, Error, ExecutionFailure, Isolation, Ok, TransactionHandle


_registry_lock = Lock()
_registry = WeakKeyDictionary()
_IDENTITY_SQL = """SELECT pg_catalog.pg_backend_pid()::pg_catalog.text,
 l.virtualtransaction::pg_catalog.text,
 pg_catalog.current_setting('transaction_isolation')::pg_catalog.text,
 pg_catalog.current_setting('transaction_read_only')::pg_catalog.text,
 pg_catalog.pg_current_xact_id_if_assigned()::pg_catalog.text,
 (SELECT setting::pg_catalog.text FROM pg_catalog.pg_settings WHERE name OPERATOR(pg_catalog.=) 'statement_timeout'::pg_catalog.text)
 FROM pg_catalog.pg_locks l WHERE l.locktype OPERATOR(pg_catalog.=) 'virtualxid'::pg_catalog.text
 AND l.pid OPERATOR(pg_catalog.=) pg_catalog.pg_backend_pid() AND l.granted AND l.mode OPERATOR(pg_catalog.=) 'ExclusiveLock'::pg_catalog.text
 LIMIT 2"""


@dataclass(frozen=True)
class PsycopgProfile:
    psycopg: str = '3.3.6'
    implementation: str = 'binary'
    libpq: int = 180006
    server: int = SERVER_VERSION_NUM


@dataclass
class _ConnectionCustody:
    lease: Lock
    attached: object = None
    quarantined: bool = False
    pending: object = None
    last_attempt: object = None
    retry_identity: tuple | None = None


@dataclass
class _TransactionCustody:
    handle: TransactionHandle
    identity: tuple
    permanent_xid: str | None
    usable: bool = True


@dataclass
class _Attempt:
    reference: str
    phase: str = 'prepared'
    result: object = None
    error: BaseException | None = None
    cleanup_error: BaseException | None = None


class _Deadline:
    """Supported cancellation only; join before another command/cleanup scope."""
    def __init__(self, connection, milliseconds):
        self.end = monotonic() + milliseconds / 1000
        self.expired = Event()
        self.error = None
        self.stopped = False
        self.stop_result = False
        def cancel():
            self.expired.set()
            try: connection.cancel_safe(timeout=1.0)
            except BaseException as error: self.error = error
        self.timer = Timer(milliseconds / 1000, cancel)
        self.timer.daemon = True
        self.timer.start()

    def finish(self):
        self.timer.cancel()
        self.timer.join(timeout=1.25)
        return not self.timer.is_alive() and self.error is None

    def check(self):
        if self.expired.is_set() or monotonic() >= self.end:
            raise TimeoutError('Original operation deadline expired')


class _GuardedCursor:
    """Check the original deadline before every supported SQL submission."""
    def __init__(self, cursor, deadline):
        self._cursor = cursor
        self._deadline = deadline

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def execute(self, *args, **kwargs):
        self._deadline.check()
        return self._cursor.execute(*args, **kwargs)


def _failure(code, message, sql_state=None, retry_scope='none'):
    return Error(ExecutionFailure(code, message, sql_state=sql_state, retry_scope=retry_scope))


class PsycopgHost:
    """Borrow a selected live connection without changing its ownership.

    Adoption requires an already active transaction. The host commits or rolls
    back through its own connection. Detach and disposal never settle or close it.
    Operation callbacks are private toolkit composition using guarded execute()
    only, not a public SQL API. executemany/copy/stream are outside this profile.
    """
    def __init__(self, connection, *, profile=PsycopgProfile(), statement_timeout_ms=2000, operation_timeout_ms=5000):
        import psycopg
        from psycopg import pq
        if (type(profile) is not PsycopgProfile
                or type(profile.psycopg) is not str or type(profile.implementation) is not str
                or type(profile.libpq) is not int or type(profile.server) is not int
                or profile not in (PsycopgProfile(), PsycopgProfile(server=SERVER_VERSION_NUM))):
            raise ValueError('Explicit supported psycopg profile required')
        if (type(connection) is not psycopg.Connection
                or psycopg.__version__ != profile.psycopg or pq.__impl__ != profile.implementation
                or pq.version() != profile.libpq or connection.info.server_version != profile.server):
            raise ValueError('Selected psycopg/libpq/PostgreSQL tuple required')
        if type(statement_timeout_ms) is not int or not 1 <= statement_timeout_ms <= 60000:
            raise ValueError('Statement timeout must be 1..60000 milliseconds')
        if connection.closed or connection.broken or connection.pgconn.pipeline_status != pq.PipelineStatus.OFF:
            raise ValueError('Live non-pipeline connection required')
        if type(operation_timeout_ms) is not int or not 1 <= operation_timeout_ms <= 60000:
            raise ValueError('Operation timeout must be 1..60000 milliseconds')
        self._deadline_ms = operation_timeout_ms
        self._connection = connection
        self._profile = profile
        self._timeout = statement_timeout_ms
        self._issuer = object()
        self._transactions = {}
        self._closed = False
        with _registry_lock:
            custody = _registry.setdefault(connection, _ConnectionCustody(Lock()))
            if custody.quarantined or (custody.attached is not None and custody.attached() is not None):
                raise ValueError('Connection already attached or quarantined')
            custody.attached = ref(self)
            self._custody = custody

    @property
    def connection(self):
        return self._connection

    @property
    def session(self):
        return self

    @property
    def profile(self):
        return self._profile

    def _status(self):
        from psycopg import pq
        if self.connection.closed or self.connection.broken:
            return pq.TransactionStatus.UNKNOWN
        if self.connection.pgconn.pipeline_status != pq.PipelineStatus.OFF:
            return pq.TransactionStatus.UNKNOWN
        return self.connection.info.transaction_status

    def _cursor(self):
        from psycopg import Cursor
        from psycopg.rows import tuple_row
        from psycopg.types.string import TextLoader
        cursor = Cursor(self.connection, row_factory=tuple_row)
        # All observer columns are native text, independent of host loaders.
        cursor.adapters.register_loader(25, TextLoader)
        return cursor

    def _observe(self, cursor):
        import re
        cursor.execute(_IDENTITY_SQL, prepare=False, binary=False)
        rows = cursor.fetchmany(2)
        if len(rows) != 1 or len(rows[0]) != 6 or cursor.description is None:
            raise ValueError('One original native identity row required')
        if len(cursor.description) != 6 or any(d.type_code != 25 for d in cursor.description):
            raise ValueError('Native text identity descriptors required')
        pid, vxid, isolation, readonly, xid, timeout = rows[0]
        if (any(type(v) is not str or len(v.encode('utf8')) > 128
                for v in (pid, vxid, isolation, readonly, timeout))
                or re.fullmatch(r'[1-9][0-9]{0,9}', pid) is None
                or re.fullmatch(r'[0-9]{1,10}/[0-9]{1,20}', vxid) is None
                or isolation not in ('read committed', 'repeatable read', 'serializable')
                or readonly not in ('on', 'off')
                or re.fullmatch(r'[0-9]{1,10}', timeout) is None
                or (xid is not None and (type(xid) is not str or re.fullmatch(r'[0-9]{1,20}', xid) is None))):
            raise ValueError('Exact native identity/profile required')
        return (pid, vxid, isolation.replace(' ', '_'),
                'read_only' if readonly == 'on' else 'read_write'), xid, timeout

    def _match(self, custody, observation):
        identity, xid, _ = observation
        if identity != custody.identity or (custody.permanent_xid is not None and xid != custody.permanent_xid):
            custody.usable = False
            raise ValueError('Original caller transaction changed')
        if custody.permanent_xid is None and xid is not None:
            custody.permanent_xid = xid

    def _stop_deadline(self, deadline, attempt):
        if deadline is None: return True
        if deadline.stopped: return deadline.stop_result
        deadline.stopped = True
        try:
            deadline.stop_result = deadline.finish()
            if not deadline.stop_result: self._custody.quarantined = True
            return deadline.stop_result
        except BaseException as error:
            if attempt is not None: attempt.cleanup_error = error
            self._custody.quarantined = True
            if not isinstance(error, Exception) and (attempt is None or attempt.error is None):
                raise
            return False

    def _attempt(self, callback, custody=None, publish=None):
        """Retain one attempt before SQL; contain BaseException and cursor failures."""
        from psycopg import pq, sql
        if not self._custody.lease.acquire(blocking=False):
            return _failure('execution_obligation', 'Connection operation already in flight')
        cursor = None
        deadline = None
        attempt = None
        established = False
        before = None
        primary = None
        name = None
        result = None
        try:
            name = sql.Identifier('truss_op_' + uuid4().hex)
            if self._closed or self._custody.quarantined:
                return _failure('transaction_unusable', 'Session disposed or connection quarantined')
            status = self._status()
            if status != pq.TransactionStatus.INTRANS:
                if status == pq.TransactionStatus.IDLE:
                    for item in self._transactions.values(): item.usable = False
                elif status in (pq.TransactionStatus.UNKNOWN, pq.TransactionStatus.ACTIVE):
                    self._custody.quarantined = True
                return _failure('invalid_transaction', 'Already active caller transaction required')
            if custody is not None and not custody.usable:
                return _failure('invalid_transaction', 'Original transaction handle is stale')
            if publish is not None and len(self._transactions) >= 256:
                return _failure('execution_obligation', 'Transaction custody capacity reached')
            attempt = _Attempt(uuid4().hex)
            self._custody.pending = attempt
            self._custody.last_attempt = attempt
            try:
                deadline = _Deadline(self.connection, self._deadline_ms)
                cursor = _GuardedCursor(self._cursor(), deadline)
                deadline.check()
                cursor.execute(sql.SQL('SAVEPOINT {}').format(name), prepare=False)
                established = True
                attempt.phase = 'savepoint'
                before = self._observe(cursor)
                deadline.check()
                if not 1 <= int(before[2]) <= 60000:
                    raise ValueError('Host statement_timeout must be 1..60000 milliseconds')
                if self._custody.retry_identity == before[0]:
                    raise ValueError('Whole caller transaction must be retried')
                if self._custody.retry_identity is not None:
                    self._custody.retry_identity = None
                if custody is not None: self._match(custody, before)
                cursor.execute("SET LOCAL statement_timeout = '" + str(self._timeout) + "ms'", prepare=False)
                deadline.check()
                attempt.phase = 'executing'
                result = callback(cursor, before)
                attempt.result = result
                attempt.phase = 'command_returned'
                deadline.check()
                after = self._observe(cursor)
                if before[0] != after[0]:
                    raise ValueError('Original caller transaction changed during operation')
                if custody is not None: self._match(custody, after)
                cursor.execute("SET LOCAL statement_timeout = '" + before[2] + "ms'", prepare=False)
                final = self._observe(cursor)
                if final[0] != before[0] or final[2] != before[2]:
                    raise ValueError('Original transaction or timeout restoration unavailable')
                if custody is not None: self._match(custody, final)
                deadline.check()
                cursor.execute(sql.SQL('RELEASE SAVEPOINT {}').format(name), prepare=False)
                if cursor.statusmessage != 'RELEASE':
                    raise ValueError('Original release completion required')
                established = False
                attempt.phase = 'released'
                # No observer SQL after containment has been released.
                joined = self._stop_deadline(deadline, attempt)
                deadline.check()
                if not joined or self._status() != pq.TransactionStatus.INTRANS:
                    raise ValueError('Original deadline/release completion unresolved')
                cursor.close()
                cursor = None
                if publish is not None: publish(result)
                attempt.phase = 'published'
                self._custody.pending = None
                return Ok(result)
            except BaseException as error:
                primary = error
                attempt.error = error
                if not self._stop_deadline(deadline, attempt):
                    self._custody.quarantined = True
                if (not self._custody.quarantined and established and cursor is not None
                        and not cursor.closed and self._status() in (pq.TransactionStatus.INTRANS, pq.TransactionStatus.INERROR)):
                    cleanup = None
                    try:
                        cleanup = _Deadline(self.connection, 2000)
                        cursor = _GuardedCursor(cursor._cursor, cleanup)
                        cursor.execute(sql.SQL('ROLLBACK TO SAVEPOINT {}').format(name), prepare=False)
                        attempt.phase = 'rolled_back'
                        restored = self._observe(cursor)
                        if before is not None and (restored[0] != before[0] or restored[2] != before[2]):
                            raise ValueError('Original containment correspondence unavailable')
                        if custody is not None and custody.usable: self._match(custody, restored)
                        cleanup.check()
                        cursor.execute(sql.SQL('RELEASE SAVEPOINT {}').format(name), prepare=False)
                        if cursor.statusmessage != 'RELEASE': raise ValueError('Original cleanup release required')
                        established = False
                        joined = self._stop_deadline(cleanup, attempt)
                        cleanup.check()
                        if not joined or self._status() != pq.TransactionStatus.INTRANS:
                            raise ValueError('Original cleanup completion unresolved')
                        attempt.phase = 'contained'
                    except BaseException as error:
                        attempt.cleanup_error = error
                        self._custody.quarantined = True
                    finally:
                        if not self._stop_deadline(cleanup, attempt): self._custody.quarantined = True
                else:
                    self._custody.quarantined = True
                if cursor is not None:
                    try: cursor.close(); cursor = None
                    except BaseException as error:
                        attempt.cleanup_error = error
                        self._custody.quarantined = True
                if not self._custody.quarantined:
                    self._custody.pending = None
                if not isinstance(primary, Exception): raise primary
                state = getattr(primary, 'sqlstate', None)
                if self._custody.quarantined:
                    return _failure('transaction_unusable', 'Original containment or completion unresolved', state)
                if state in ('40001', '40P01'):
                    self._custody.retry_identity = before[0] if before is not None else None
                    if custody is not None: custody.usable = False
                    return _failure('retry', 'Whole caller transaction must be retried', state, 'whole_transaction')
                if state == '57014' or isinstance(primary, TimeoutError):
                    return _failure('cancelled', 'Original operation cancelled and locally contained', state)
                if isinstance(primary, ValueError):
                    return _failure('invalid_transaction', 'Original transaction/profile admission refused', state)
                return _failure('execution_obligation', 'Original operation failed and locally contained', state)
        finally:
            if not self._stop_deadline(deadline, attempt): self._custody.quarantined = True
            self._custody.lease.release()

    def adopt_transaction(self, *, isolation: Isolation='read_committed', access_mode: AccessMode='read_write'):
        if len(self._transactions) >= 256:
            return _failure('execution_obligation', 'Transaction custody capacity reached')
        if isolation not in ('read_committed', 'repeatable_read', 'serializable') or access_mode not in ('read_only', 'read_write'):
            return _failure('invalid_transaction', 'Unsupported requested transaction profile')
        def adopt(cursor, observed):
            if observed[0][2:] != (isolation, access_mode):
                raise ValueError('Actual caller transaction profile differs')
            for previous in self._transactions.values():
                if previous.usable and previous.identity == observed[0]:
                    raise ValueError('Caller transaction already adopted')
            handle = TransactionHandle(self._issuer, uuid4().hex, isolation, access_mode)
            return _TransactionCustody(handle, observed[0], observed[1])
        def publish(custody):
            self._transactions[custody.handle._key] = custody
        result = self._attempt(adopt, publish=publish)
        if isinstance(result, Error): return result
        custody = result.value
        return Ok(custody.handle)

    def _run_operation(self, transaction, callback):
        custody = (self._transactions.get(transaction._key)
                   if type(transaction) is TransactionHandle and transaction._issuer is self._issuer else None)
        if (custody is None or custody.handle is not transaction
                or (transaction.isolation, transaction.access_mode) != custody.identity[2:]):
            return _failure('invalid_transaction', 'Original issued transaction handle required')
        return self._attempt(callback, custody)

    def detach(self):
        self._closed = True
        if not self._custody.lease.acquire(blocking=False): return False
        try:
            self._closed = True
            for custody in self._transactions.values(): custody.usable = False
            with _registry_lock:
                if self._custody.attached is not None and self._custody.attached() is self:
                    self._custody.attached = None
            return not self._custody.quarantined
        finally:
            self._custody.lease.release()

    def dispose(self):
        return self.detach()


def adopt_psycopg_host(connection, *, profile=PsycopgProfile(), statement_timeout_ms=2000, operation_timeout_ms=5000):
    """Attach without beginning, committing, rolling back or closing a host connection."""
    return PsycopgHost(connection, profile=profile, statement_timeout_ms=statement_timeout_ms, operation_timeout_ms=operation_timeout_ms)
