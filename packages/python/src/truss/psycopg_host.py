"""Supported synchronous psycopg host adoption; no graph or commit authority.

The caller owns the connection and outer transaction. Raw aliases must remain
unused during toolkit operations. The host may settle its transaction between calls. This initial selected tuple is local evidence,
not a claim of Lakebase, other libpq implementations or complete installation.
"""
from ._runtime_profile import SERVER_VERSION_NUM
from dataclasses import dataclass, field
from threading import Lock, Event, Timer, get_ident
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
# Same six facts, one row, so a single-statement call can carry its own admission
# check. Evaluated after the payload so a write's assigned xid is visible.
_ADMISSION_TAIL = """(SELECT pg_catalog.pg_backend_pid()::pg_catalog.text),
 (SELECT l.virtualtransaction::pg_catalog.text FROM pg_catalog.pg_locks l
   WHERE l.locktype OPERATOR(pg_catalog.=) 'virtualxid'::pg_catalog.text
   AND l.pid OPERATOR(pg_catalog.=) pg_catalog.pg_backend_pid() AND l.granted
   AND l.mode OPERATOR(pg_catalog.=) 'ExclusiveLock'::pg_catalog.text LIMIT 2),
 (SELECT pg_catalog.current_setting('transaction_isolation')::pg_catalog.text),
 (SELECT pg_catalog.current_setting('transaction_read_only')::pg_catalog.text),
 (SELECT pg_catalog.pg_current_xact_id_if_assigned()::pg_catalog.text),
 (SELECT setting::pg_catalog.text FROM pg_catalog.pg_settings WHERE name OPERATOR(pg_catalog.=) 'statement_timeout'::pg_catalog.text)"""


def _parse_identity_row(row):
    import re
    if len(row) != 6:
        raise ValueError('One original native identity row required')
    pid, vxid, isolation, readonly, xid, timeout = row
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


def _fusable(query, kwargs):
    """A single SELECT/WITH can sit in a subquery and carry the admission tail."""
    if type(query) is not str or kwargs.get('binary'):
        return False
    text = query.lstrip()
    if not (text[:6].upper().startswith('SELECT') or text[:4].upper() == 'WITH'):
        return False
    if ';' in text:
        return False
    upper = text.upper()
    if (' INTO ' in upper or ' FOR UPDATE' in upper or ' FOR SHARE' in upper
            or ' FOR NO KEY' in upper or ' FOR KEY SHARE' in upper):
        return False
    return True


def _fuse_admission(query):
    return 'SELECT payload.*, ' + _ADMISSION_TAIL + ' FROM (' + query + ') payload'


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
    reservation: object = None
    retry_identity: tuple | None = None
    semantic_issuers: dict = field(default_factory=dict)


class _HostPairReservation:
    """Private original two-host operation reservation; never an authority token."""
    def __init__(self, first, second):
        if type(first) is not PsycopgHost or type(second) is not PsycopgHost or first._custody is second._custody:
            raise ValueError('Two separate original hosts required')
        self.hosts=(first,second);self.thread=get_ident();self.active=False;self.deadline=None
        self.custodies=tuple(sorted((first._custody,second._custody),key=id))
    def __enter__(self):
        acquired=[]
        try:
            for custody in self.custodies:
                if not custody.lease.acquire(blocking=False):raise ValueError('Original host pair unavailable')
                acquired.append(custody)
                if custody.quarantined or custody.pending is not None or custody.reservation is not None:
                    raise ValueError('Original host pair custody unavailable')
            if any(h._closed for h in self.hosts):raise ValueError('Original host pair disposed')
            for custody in self.custodies:custody.reservation=self
            self.active=True
            return self
        except BaseException:
            for custody in reversed(acquired):custody.lease.release()
            raise
    def __exit__(self,*error):
        self.active=False
        for custody in reversed(self.custodies):
            if custody.pending is not None:custody.quarantined=True
            custody.reservation=None;custody.lease.release()


class _HostOperationReservation(_HostPairReservation):
    """Private exclusive caller-host scope for sequential contained operations."""
    def __init__(self,host):
        if type(host) is not PsycopgHost:raise ValueError('Original host required')
        self.hosts=(host,);self.thread=get_ident();self.active=False;self.custodies=(host._custody,)


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
    ordinal_reservation: object = None
    dispatch_parameters: tuple | None = None


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


class _AdmissionCursor:
    """Carry admission on the first fusable statement. Other statements stay unchanged.

    The savepoint is already open. A mismatched admission raises before the
    callback sees a row, and the attempt rolls that savepoint back. statement_timeout
    is changed only when the admitted session value differs, and only around the
    statements the callback actually submits.
    """
    def __init__(self, inner, host, custody, baseline, restore_to):
        self._inner = inner
        self._host = host
        self._custody = custody
        self._baseline = baseline
        self._restore_to = restore_to
        self._desired = host._timeout
        self._rows = None
        self._pos = 0
        self._desc = None
        self.executions = 0
        self.checked = False
        self.did_set = False
        self.admission = None
        self._timeout_applied = False

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def _ensure_timeout(self):
        if self._timeout_applied or self._restore_to is None:
            return
        self._timeout_applied = True
        if int(self._restore_to) == self._desired:
            return
        self._inner.execute("SET LOCAL statement_timeout = '" + str(self._desired) + "ms'", prepare=False)
        self.did_set = True

    def _remember(self, observation):
        self.admission = self._host._apply_admission(observation, self._custody, self._baseline)
        self.checked = True

    def execute(self, query, *args, **kwargs):
        self.executions += 1
        self._rows = None
        self._desc = None
        self._pos = 0
        if not self.checked and _fusable(query, kwargs):
            self._ensure_timeout()
            self._inner.execute(_fuse_admission(query), *args, **kwargs)
            description = self._inner.description
            rows = self._inner.fetchall()
            if description is None or len(description) < 6 or any(item.type_code != 25 for item in description[-6:]):
                raise ValueError('Native text identity descriptors required')
            self._desc = description[:-6]
            if not rows:
                self._remember(self._host._read_identity(self._inner))
                self._rows = []
                return self
            if any(len(row) < 6 for row in rows):
                raise ValueError('One original native identity row required')
            self._remember(_parse_identity_row(rows[0][-6:]))
            self._rows = [row[:-6] for row in rows]
            return self
        self._ensure_timeout()
        return self._inner.execute(query, *args, **kwargs)

    @property
    def description(self):
        if self._rows is not None:
            return self._desc
        return self._inner.description

    def fetchone(self):
        if self._rows is None:
            return self._inner.fetchone()
        if self._pos >= len(self._rows):
            return None
        row = self._rows[self._pos]
        self._pos += 1
        return row

    def fetchmany(self, size=None):
        if self._rows is None:
            return self._inner.fetchmany(size) if size is not None else self._inner.fetchmany()
        if size is None:
            size = getattr(self._inner, 'arraysize', 1) or 1
        chunk = self._rows[self._pos:self._pos + size]
        self._pos += len(chunk)
        return chunk

    def fetchall(self):
        if self._rows is None:
            return self._inner.fetchall()
        chunk = self._rows[self._pos:]
        self._pos = len(self._rows)
        return chunk


def _failure(code, message, sql_state=None, retry_scope='none'):
    return Error(ExecutionFailure(code, message, sql_state=sql_state, retry_scope=retry_scope))


def _prepare_synchronous_publisher(publisher):
    """Trusted sink shape/completion check, never delivery authentication."""
    import inspect
    call = getattr(publisher, '__call__', None)
    if (not callable(publisher) or any(check(value) for value in (publisher,call)
            for check in (inspect.iscoroutinefunction,inspect.isgeneratorfunction,inspect.isasyncgenfunction))):
        raise ValueError('Original synchronous private publisher required')
    def publish(value):
        completion=publisher(value)
        if completion is not None:
            if inspect.iscoroutine(completion) or inspect.isgenerator(completion):completion.close()
            raise ValueError('Exact synchronous publisher completion required')
    return publish


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
        self._admitted = None
        self._admission_satisfied = None
        self._attempt_seen = None
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

    def _read_identity(self, cursor):
        cursor.execute(_IDENTITY_SQL, prepare=False, binary=False)
        rows = cursor.fetchmany(2)
        if len(rows) != 1 or len(rows[0]) != 6 or cursor.description is None:
            raise ValueError('One original native identity row required')
        if len(cursor.description) != 6 or any(d.type_code != 25 for d in cursor.description):
            raise ValueError('Native text identity descriptors required')
        return _parse_identity_row(rows[0])

    def _observe(self, cursor):
        # Fault injection observes this call after the callback returns. When the
        # attempt already admitted itself, the call still happens and submits no SQL.
        satisfied = self._admission_satisfied
        attempt = self._custody.last_attempt
        if satisfied is not None and attempt is not None and attempt.phase == 'command_returned':
            self._admission_satisfied = None
            return satisfied
        return self._read_identity(cursor)

    def _apply_admission(self, observation, custody, baseline):
        identity, _xid, timeout = observation
        if not 1 <= int(timeout) <= 60000:
            raise ValueError('Host statement_timeout must be 1..60000 milliseconds')
        if baseline is not None and identity != baseline:
            # The statement entered a transaction this handle did not adopt.
            # Cleanup compares against this row: savepoint rollback restores
            # that transaction, not the adopted generation.
            self._attempt_seen = observation
            if custody is not None:
                custody.usable = False
            raise ValueError('Original caller transaction changed during operation')
        if custody is not None:
            self._match(custody, observation)
        self._admitted = observation
        return observation

    def _live_backend_pid(self):
        try:
            return str(self.connection.info.backend_pid)
        except Exception:
            return None

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

    def _attempt(self, callback, custody=None, publish=None, *, semantic=False, parameter_producer=None):
        """Retain one attempt before SQL; contain BaseException and cursor failures."""
        from psycopg import pq, sql
        host_reservation=self._custody.reservation
        reserved=(type(host_reservation) in (_HostPairReservation,_HostOperationReservation) and host_reservation.active
                  and host_reservation.thread==get_ident() and any(h is self for h in host_reservation.hosts))
        if reserved:
            if self._custody.pending is not None:
                return _failure('execution_obligation', 'Connection operation already in flight')
        elif not self._custody.lease.acquire(blocking=False):
            return _failure('execution_obligation', 'Connection operation already in flight')
        cursor = None
        deadline = None
        attempt = None
        established = False
        before = None
        work = None
        primary = None
        name = None
        result = None
        semantic_preflight = semantic
        try:
            name = sql.Identifier('truss_op_' + uuid4().hex)
            if self._closed or self._custody.quarantined:
                return _failure('transaction_unusable', 'Session disposed or connection quarantined')
            with _registry_lock:
                if (_registry.get(self.connection) is not self._custody or self._custody.attached is None
                        or self._custody.attached() is not self):
                    return _failure('invalid_transaction', 'Original registered host attachment required')
            status = self._status()
            if status != pq.TransactionStatus.INTRANS:
                if status == pq.TransactionStatus.IDLE:
                    for item in self._transactions.values(): item.usable = False
                    self._admitted = None
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
                if semantic:
                    from ._operation_ordinal import OperationOrdinalIssuer, OrdinalReservation
                    if custody is None:
                        raise ValueError('Adopted transaction required for semantic operation')
                    # Isolation/access mode are handle checks, not transaction identities.
                    key = custody.identity[:2]
                    binding = self._custody.semantic_issuers.get(key)
                    if binding is None:
                        if len(self._custody.semantic_issuers) >= 256:
                            raise ValueError('Semantic transaction custody capacity reached')
                        anchor = object()
                        binding = (anchor, OperationOrdinalIssuer(anchor, maximum=255))
                        self._custody.semantic_issuers[key] = binding
                    reservation = OrdinalReservation()
                    attempt.ordinal_reservation = reservation
                    issued = binding[1].reserve_into(binding[0], reservation)
                    if issued.outcome != 'issued':
                        raise ValueError('Semantic operation ordinal unavailable')

                milliseconds=self._deadline_ms
                parent=getattr(host_reservation,'deadline',None) if reserved else None
                if parent is not None:
                    parent.check()
                    milliseconds=min(milliseconds,max(1,int((parent.end-monotonic())*1000)))
                deadline = _Deadline(self.connection, milliseconds)
                cursor = _GuardedCursor(self._cursor(), deadline)
                if parameter_producer is not None:
                    from psycopg.types.string import (StrBinaryDumper, StrDumperUnknown,
                                                     BytesDumper, BytesBinaryDumper)
                    # Retained semantic inputs use selected stock adapters, not
                    # host custom dumpers. The caller connection is unchanged.
                    for kind, dumper in ((str, StrBinaryDumper), (str, StrDumperUnknown),
                                         (bytes, BytesDumper), (bytes, BytesBinaryDumper)):
                        cursor.adapters.register_dumper(kind, dumper)
                deadline.check()
                semantic_preflight = False
                self._admission_satisfied = None
                self._attempt_seen = None
                # Hosts may change session settings between completed calls. Read
                # the current generation and timeout before setting the call budget;
                # a cached timeout cannot establish either execution or restoration.
                cursor.execute(sql.SQL('SAVEPOINT {}').format(name), prepare=False)
                established = True
                attempt.phase = 'savepoint'
                before = self._apply_admission(self._observe(cursor), custody, None)
                deadline.check()
                if not 1 <= int(before[2]) <= 60000:
                    raise ValueError('Host statement_timeout must be 1..60000 milliseconds')
                if self._custody.retry_identity == before[0]:
                    raise ValueError('Whole caller transaction must be retried')
                if self._custody.retry_identity is not None:
                    self._custody.retry_identity = None
                deadline.check()
                attempt.phase = 'executing'
                work = _AdmissionCursor(cursor, self, custody, before[0], before[2])
                if parameter_producer is not None:
                    parameters = parameter_producer(attempt.ordinal_reservation.result.ordinal)
                    if (type(parameters) is not tuple or not 1 <= len(parameters) <= 64
                            or any(type(cell) not in (str, bytes) for cell in parameters)):
                        raise ValueError('Exact immutable semantic parameters required')
                    if sum(len(cell.encode('utf8')) if type(cell) is str else len(cell)
                           for cell in parameters) > 4194304:
                        raise ValueError('Semantic parameter capacity exceeded')
                    attempt.dispatch_parameters = parameters
                    deadline.check()
                    result = callback(work, before, attempt.ordinal_reservation.result.ordinal, parameters)
                else:
                    result = (callback(work, before, attempt.ordinal_reservation.result.ordinal)
                              if semantic else callback(work, before))
                if work.checked and work.admission is not None:
                    self._admission_satisfied = work.admission
                elif work.executions == 0:
                    self._admission_satisfied = before
                attempt.result = result
                attempt.phase = 'command_returned'
                deadline.check()
                after = self._observe(cursor)
                if before[0] != after[0]:
                    raise ValueError('Original caller transaction changed during operation')
                if custody is not None: self._match(custody, after)
                if work.did_set or after[2] != before[2]:
                    deadline.check()
                    cursor.execute("SET LOCAL statement_timeout = '" + before[2] + "ms'", prepare=False)
                    if self._admitted is not None:
                        self._admitted = (self._admitted[0], self._admitted[1], before[2])
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
                # Savepoint rollback undoes SET LOCAL. Keep the admitted timeout
                # aligned with the caller's value when containment succeeds.
                if before is not None and self._admitted is not None and self._admitted[2] != before[2]:
                    self._admitted = (self._admitted[0], self._admitted[1], before[2])
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
                        # A fused check can be the first observation of a replacement
                        # transaction. Rollback returns that transaction to the timeout
                        # it had before this attempt's SET LOCAL, which the fused row
                        # (taken after the SET) did not record.
                        seen = self._attempt_seen
                        anchor = seen if seen is not None else before
                        skip_timeout = seen is not None and work is not None and work.did_set
                        if anchor is not None and (restored[0] != anchor[0]
                                or (not skip_timeout and restored[2] != anchor[2])):
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
                elif not semantic_preflight:
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
            if not reserved:self._custody.lease.release()

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

    def _run_published_operation(self, transaction, callback, publisher):
        """Private trusted receiver hook after native completion, under lease.

        Receiver side effects cannot be rolled back. A receiver failure therefore
        quarantines the original session; no delivery/retry authority is issued.
        The receiver must be bounded by its separately admitted sink contract.
        """
        publisher=_prepare_synchronous_publisher(publisher)
        custody = (self._transactions.get(transaction._key)
                   if type(transaction) is TransactionHandle and transaction._issuer is self._issuer else None)
        if (custody is None or custody.handle is not transaction
                or (transaction.isolation, transaction.access_mode) != custody.identity[2:]):
            return _failure('invalid_transaction', 'Original issued transaction handle required')
        return self._attempt(callback, custody, publish=publisher)

    def _run_semantic_operation(self, transaction, callback, *, parameter_producer=None):
        """Reserve a nonrewinding ordinal before SQL on the shared connection.

        Private execution primitive for protected catalog/group facades. An
        issued ordinal is host custody, never database authorization. Inspection
        calls use _run_operation and consume no semantic ordinal. An optional
        trusted SDK producer derives exact immutable parameters after native
        custody validation. The retained tuple is passed unchanged to the
        callback; fixed statement/parameter correspondence belongs to that
        registered executor. Bounds count every cell, including the ordinal,
        using UTF-8 bytes for text.
        """
        custody = (self._transactions.get(transaction._key)
                   if type(transaction) is TransactionHandle and transaction._issuer is self._issuer else None)
        if (custody is None or custody.handle is not transaction
                or (transaction.isolation, transaction.access_mode) != custody.identity[2:]):
            return _failure('invalid_transaction', 'Original issued transaction handle required')
        return self._attempt(callback, custody, semantic=True, parameter_producer=parameter_producer)

    def detach(self):
        self._closed = True
        if not self._custody.lease.acquire(blocking=False): return False
        try:
            with _registry_lock:
                if (_registry.get(self.connection) is not self._custody or self._custody.attached is None
                        or self._custody.attached() is not self):
                    return False
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
