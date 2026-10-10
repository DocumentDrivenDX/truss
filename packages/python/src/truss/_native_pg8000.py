"""Private pg8000 1.31.5 original-call boundary, not qualified adoption.

Attach on an idle connection before beginning host work. All supported host
calls must use this wrapper; retained raw/core aliases and driver mutation are
outside the cooperative host contract. No SQL classification or transaction
identity is inferred here. Operation tokens are internal exclusion, not receipts
or verified arbitration completion. Native lifecycle integration remains pending.
"""
from dataclasses import dataclass
from importlib.metadata import version
from threading import Lock

_attachment_lock = Lock()


class NativeBoundaryRefusal(RuntimeError):
    pass


@dataclass(frozen=True)
class NativeEvent:
    code: bytes
    payload: bytes


@dataclass(frozen=True)
class NativeCall:
    events: tuple[NativeEvent, ...]
    driver_raised: bool
    capture_complete: bool
    final_status: bytes | None


class NativeBoundary:
    def __init__(self, connection, *, event_bytes=65536, event_count=256):
        from pg8000.native import Connection
        if version('pg8000') != '1.31.5' or type(connection) is not Connection:
            raise NativeBoundaryRefusal('Unselected original driver')
        if type(event_bytes) is not int or event_bytes < 1 or type(event_count) is not int or event_count < 1:
            raise ValueError('Positive exact capture limits required')
        self._connection = connection
        self._lock = Lock()
        self._operation = None
        self._calling = False
        self._quarantined = False
        self._events = []
        self._bytes = 0
        self._complete = True
        self._event_bytes, self._event_count = event_bytes, event_count
        self.last_call = None
        self._ready_error = None
        with _attachment_lock:
            if connection._transaction_status != b'I' or hasattr(connection, '_truss_native_boundary'):
                raise NativeBoundaryRefusal('Requires original idle, unattached connection')
            originals = {code: connection.message_types[code] for code in (b'C', b'E', b'Z')}
            hooks = {code: self._hook(code, handler) for code, handler in originals.items()}
            connection.message_types.update(hooks)
            connection._truss_native_boundary = self

    def _hook(self, code, original):
        def capture(data, context):
            with self._lock:
                if not self._calling:
                    self._quarantined = True
                elif (len(self._events) >= self._event_count or self._bytes + len(data) + 1 > self._event_bytes):
                    self._complete = False
                    self._quarantined = True
                else:
                    try:
                        self._events.append(NativeEvent(code, bytes(data)))
                        self._bytes += len(data) + 1
                        if code == b'Z':
                            self._ready_error = context.error
                    except BaseException:
                        self._complete = False
                        self._quarantined = True
                        raise
            # Capture precedes delegation: a synthesized driver exception cannot
            # erase a CommandComplete already returned by the original server.
            return original(data, context)
        return capture

    def acquire_operation(self):
        with self._lock:
            if self._quarantined or self._calling or self._operation is not None:
                raise NativeBoundaryRefusal('Native boundary unavailable or busy')
            self._operation = object()
            return self._operation

    def release_operation(self, token):
        with self._lock:
            if token is not self._operation or token is None or self._calling or self._quarantined:
                raise NativeBoundaryRefusal('Original operation cannot be released')
            self._operation = None

    def _call(self, invoke, token=None, *, closing=False, preflight=None):
        with self._lock:
            if (self._quarantined or self._calling or
                    (self._operation is not None and token is not self._operation) or
                    (token is not None and token is not self._operation)):
                raise NativeBoundaryRefusal('Native boundary unavailable or busy')
            if preflight is not None:
                preflight()
            self._calling = True
            self._ready_error = None
            self._events, self._bytes, self._complete = [], 0, True
        raised = True
        native_error = False
        try:
            result = invoke()
            raised = False
            return result
        except BaseException as error:
            # pg8000 raises the exact Context.error after its final Ready.
            # A transport/conversion failure after an earlier Ready is unknown.
            native_error = error is self._ready_error
            raise
        finally:
            with self._lock:
                events = tuple(self._events)
                # Every extended-query Ready belongs to this original call;
                # only return/raise settles the call, never the first Ready.
                ready = bool(events) and events[-1].code == b'Z'
                complete = self._complete and ready and not self._quarantined and (not raised or native_error)
                self.last_call = NativeCall(events, raised, complete, self._connection._transaction_status)
                if closing or not complete:
                    self._quarantined = True
                self._calling = False

    def run(self, sql, *, token=None, **params):
        """Trusted host SQL; lifecycle classification is not provided here."""
        return self._call(lambda: self._connection.run(sql, **params), token)

    def prepare(self, sql, *, token=None):
        prepared = self._call(lambda: self._connection.prepare(sql), token)
        return _Prepared(self, prepared)

    def close(self, *, token=None):
        return self._call(self._connection.close, token, closing=True)


class _Prepared:
    def __init__(self, boundary, original):
        self._boundary, self._original = boundary, original
        self._closed = False

    def _open(self):
        if self._closed:
            raise NativeBoundaryRefusal('Original prepared statement closed')

    def run(self, *, token=None, **params):
        return self._boundary._call(lambda: self._original.run(**params), token,
                                    preflight=self._open)

    def close(self, *, token=None):
        def close_original():
            result = self._original.close()
            with self._boundary._lock:
                self._closed = True
            return result
        return self._boundary._call(close_original, token, preflight=self._open)
