"""Private pg8000 1.31.5 original-call boundary, not qualified adoption.

Attach on an idle connection before beginning host work. All supported host
calls must use this wrapper; retained raw/core aliases and driver mutation are
outside the cooperative host contract. No SQL classification or transaction
identity is inferred here. Operation tokens are internal exclusion, not receipts
or verified arbitration completion. Native lifecycle integration remains pending.
"""
from dataclasses import dataclass, replace
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
    original_control: object = None
    revision: int = 0
    original_resource: object = None
    original_cleanup: object = None


@dataclass(frozen=True, eq=False)
class _Ownership:
    operation: object = None
    ledger: object = None
    pending: object = None
    completed: tuple = ()


@dataclass(eq=False)
class _OperationRelease:
    owner: object
    token: object
    before: object
    after: object
    published: bool = False

class NativeBoundary:
    def __init__(self, connection, *, event_bytes=65536, event_count=256, prepared_limit=256):
        from pg8000.native import Connection
        if version('pg8000') != '1.31.5' or type(connection) is not Connection:
            raise NativeBoundaryRefusal('Unselected original driver')
        if type(event_bytes) is not int or event_bytes < 1 or type(event_count) is not int or event_count < 1:
            raise ValueError('Positive exact capture limits required')
        if type(prepared_limit) is not int or prepared_limit < 1:
            raise ValueError('Positive exact prepared custody limit required')
        self._resources = ()
        self._host_control_pending = None
        self._host_control_records = ()
        self._resource_baseline = None
        self._unnamed_pending = True
        self._prepared_limit = prepared_limit
        self._active_resource = None
        self._native_arbitration_sessions = ()
        self._native_arbitration_bindings = ()
        self._connection = connection
        self._lock = Lock()
        self._ownership = _Ownership()
        self._calling = False
        self._quarantined = False
        self._events = []
        self._bytes = 0
        self._complete = True
        self._event_bytes, self._event_count = event_bytes, event_count
        self.last_call = None
        self._ready_error = None
        self._transaction_tracker = None
        self._active_control = None
        self._revision = 0
        with _attachment_lock:
            if connection._transaction_status != b'I' or hasattr(connection, '_truss_native_boundary'):
                raise NativeBoundaryRefusal('Requires original idle, unattached connection')
            self._original_driver_handlers = dict(connection.message_types)
            originals = {code: connection.message_types[code] for code in (b'C', b'E', b'Z', b'1', b'3')}
            hooks = {code: self._hook(code, handler) for code, handler in originals.items()}
            connection.message_types.update(hooks)
            self._original_handlers = dict(connection.message_types)
            connection._truss_native_boundary = self
            original_parse = connection.send_PARSE
            self._original_parse = original_parse
            original_close = connection.close_prepared_statement
            self._original_close = original_close
            def parse(name, *args, **kwargs):
                with self._lock: self._unnamed_pending = True
                self._resource_name('prepare', name)
                return original_parse(name, *args, **kwargs)
            def close_prepared(name, *args, **kwargs):
                self._resource_name('close', name)
                return original_close(name, *args, **kwargs)
            self._parse_entry = parse
            self._close_entry = close_prepared
            connection.send_PARSE = parse
            connection.close_prepared_statement = close_prepared
            self._original_bind = connection.send_BIND
            def bind(*args, **kwargs):
                with self._lock: self._unnamed_pending = True
                return self._original_bind(*args, **kwargs)
            self._bind_entry = bind
            connection.send_BIND = bind

    def _resource_name(self, kind, name):
        # Original driver argument retained before native submission; no inferred
        # name from set differences or caller-created statement inventory.
        with self._lock:
            descriptor = self._active_resource
            if not self._calling or descriptor is None:
                return
            if descriptor[0] == 'probe' and kind == 'prepare' and name == b'\0':
                return
            if descriptor[0] != kind:
                self._quarantined = True
                raise NativeBoundaryRefusal('Foreign resource submission')
            resource = descriptor[1]
            if type(name) is not bytes or not name or not name.endswith(b'\0'):
                self._quarantined = True
                raise NativeBoundaryRefusal('Original statement name unavailable')
            if kind == 'prepare':
                if resource.name is not None:
                    self._quarantined = True
                    raise NativeBoundaryRefusal('Repeated resource creation')
                resource.name = name
            elif name != resource.name:
                self._quarantined = True
                raise NativeBoundaryRefusal('Original close name mismatch')

    @property
    def _operation(self): return self._ownership.operation
    @_operation.setter
    def _operation(self, value): self._ownership = replace(self._ownership, operation=value)
    @property
    def _operation_ledger(self): return self._ownership.ledger
    @_operation_ledger.setter
    def _operation_ledger(self, value): self._ownership = replace(self._ownership, ledger=value)
    @property
    def _pending_operation_ledger(self): return self._ownership.pending
    @_pending_operation_ledger.setter
    def _pending_operation_ledger(self, value): self._ownership = replace(self._ownership, pending=value)
    def _publish_ownership(self, root): self._ownership = root

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

    def acquire_operation(self, *, original_token=None):
        if original_token is not None and type(original_token) is not object:
            raise NativeBoundaryRefusal('Original preallocated scope token required')
        with self._lock:
            if self._quarantined or self._calling or self._operation is not None or self._host_control_pending is not None:
                raise NativeBoundaryRefusal('Native boundary unavailable or busy')
            self._operation = object() if original_token is None else original_token
            return self._operation

    def reserve_operation_release(self, token):
        with self._lock:
            if token is not self._operation or token is None or self._calling or self._quarantined or self._operation_ledger is not None or self._pending_operation_ledger is not None:
                raise NativeBoundaryRefusal('Original scope release reservation unavailable')
            return _OperationRelease(self,token,self._ownership,replace(self._ownership,operation=None))

    def release_operation(self, token, *, original_release=None):
        with self._lock:
            self._release_operation_locked(token, original_release=original_release)

    def _release_operation_locked(self, token, *, original_release=None, original_control=None):
        if token is not self._operation or token is None or self._calling or self._quarantined or self._operation_ledger is not None or self._pending_operation_ledger is not None:
            raise NativeBoundaryRefusal('Original operation cannot be released')
        pending = self._host_control_pending
        if pending is not None and (original_control is None or pending.completion is not original_control
                or not pending.result_custody.detached or pending.original_root is not self._ownership):
            raise NativeBoundaryRefusal('Original sealed control completion required')
        if original_release is None:
            self._operation=None
            return
        if (type(original_release) is not _OperationRelease or original_release.owner is not self
            or original_release.token is not token or original_release.before is not self._ownership
            or original_release.after.operation is not None or original_release.published):
            raise NativeBoundaryRefusal('Original release transition correspondence unavailable')
        try:
            self._publish_ownership(original_release.after)
        except BaseException:
            if self._ownership is original_release.after:
                self._host_control_pending = None
                original_release.published=True
            raise
        self._host_control_pending = None
        original_release.published=True

    def _call(self, invoke, token=None, *, closing=False, preflight=None, lifecycle=None, on_complete=None, resource=None, on_settled=None, cleanup=None):
        with self._lock:
            if (self._quarantined or self._calling or
                    (self._operation is not None and token is not self._operation) or
                    (token is not None and token is not self._operation)):
                raise NativeBoundaryRefusal('Native boundary unavailable or busy')
            if (self._host_control_pending is not None
                    and self._operation_ledger is not self._host_control_pending):
                raise NativeBoundaryRefusal('Original host control remains unresolved')
            if (self._pending_operation_ledger is not None
                    and self._operation_ledger is not self._pending_operation_ledger):
                raise NativeBoundaryRefusal('Original native binding remains unresolved')
            if self._revision >= 18446744073709551615:
                raise NativeBoundaryRefusal('Native coordination revision exhausted')
            if self._operation_ledger is not None:
                self._operation_ledger._check_call(self, token, cleanup)
            if self._transaction_tracker is not None:
                self._transaction_tracker._before(lifecycle)
            if preflight is not None:
                preflight()
            call_entry = None
            if self._operation_ledger is not None:
                call_entry = self._operation_ledger._reserve_call(self, token, resource, lifecycle, cleanup)
            self._revision += 1
            self._active_control = lifecycle
            self._active_resource = resource
            self._calling = True
            self._ready_error = None
            self._events, self._bytes, self._complete = [], 0, True
        result = None
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
                self.last_call = NativeCall(events, raised, complete, self._connection._transaction_status, self._active_control, self._revision, self._active_resource, cleanup)
                if call_entry is not None:
                    call_entry.native_call = self.last_call
                if any(e.code == b'C' and e.payload.split(b' ')[0].rstrip(b'\0') in
                       (b'PREPARE', b'DECLARE', b'DEALLOCATE', b'CLOSE') for e in events):
                    self._resource_baseline = None
                if closing or not complete:
                    self._quarantined = True
                try:
                    if self._transaction_tracker is not None:
                        self._transaction_tracker._after(lifecycle, self.last_call)
                    if on_settled is not None:
                        on_settled(self.last_call, result)
                    if on_complete is not None and not raised:
                        on_complete(self.last_call, result)
                except BaseException:
                    self._quarantined = True
                    raise
                finally:
                    self._calling = False

    def _run_simple(self, sql):
        # Only fixed native control/observation producers use this entry.
        ledger = self._operation_ledger
        if ledger is not None and getattr(ledger, 'simple_query', None) is not None:
            return ledger.simple_query(sql)
        return self._connection.run(sql)

    def run(self, sql, *, token=None, cleanup=None, **params):
        """Trusted host SQL; lifecycle classification is not provided here."""
        return self._call(lambda: self._connection.run(sql, **params), token, cleanup=cleanup)

    def prepare(self, sql, *, token=None):
        prepared = _Prepared(self)
        descriptor = ('prepare', prepared._resource)
        def reserve():
            if len(self._resources) >= self._prepared_limit:
                raise NativeBoundaryRefusal('Prepared custody exhausted')
            self._resources = (*self._resources, prepared)
        def invoke():
            prepared._original = self._connection.prepare(sql)
            return prepared._original
        try:
            self._call(invoke, token, preflight=reserve, resource=descriptor,
                       on_settled=prepared._created)
            return prepared
        except BaseException:
            with self._lock:
                if prepared in self._resources and prepared._resource.phase == 'reserved':
                    prepared._resource.phase = 'unknown'
                    self._quarantined = True
            raise

    def close(self, *, token=None):
        return self._call(self._connection.close, token, closing=True)


@dataclass
class _PreparedResource:
    name: bytes | None = None
    phase: str = 'reserved'
    create_call: NativeCall | None = None
    close_call: NativeCall | None = None
    native_created: bool = False
    native_closed: bool = False
    close_attempt: object = None


class _Prepared:
    def __init__(self, boundary):
        self._boundary = boundary
        self._original = None
        self._resource = _PreparedResource()
        self._closed = False

    def _created(self, call, result):
        resource = self._resource
        resource.create_call = call
        parsed = [e for e in call.events if e.code == b'1']
        resource.native_created = len(parsed) == 1 and parsed[0].payload == b'' and resource.name is not None
        if (call.capture_complete and not call.driver_raised and resource.native_created
                and result is self._original and self._original is not None
                and self._original.name_bin == resource.name):
            try:
                self._publish_live()
            except BaseException:
                resource.phase = 'unknown'
                raise
        else:
            resource.phase = 'unknown'
            session = self._boundary._operation_ledger
            gate = getattr(session, 'result_custody', None)
            if gate is None or not gate.normal_native_error(call):
                self._boundary._quarantined = True

    def _publish_live(self):
        self._resource.phase = 'live'

    def _open(self):
        if self._resource.phase != 'live' or self._closed:
            raise NativeBoundaryRefusal('Original prepared statement unavailable')

    def run(self, *, token=None, **params):
        return self._boundary._call(lambda: self._original.run(**params), token,
                                    preflight=self._open, resource=('execute', self._resource))

    def _closing(self, descriptor):
        self._open()
        self._resource.close_attempt = descriptor
        self._resource.phase = 'closing'

    def _close_settled(self, call, result):
        resource = self._resource
        resource.close_call = call
        closed = [e for e in call.events if e.code == b'3']
        resource.native_closed = len(closed) == 1 and closed[0].payload == b''
        if call.capture_complete and not call.driver_raised and resource.native_closed:
            self._closed = True
            resource.phase = 'closed'
        else:
            resource.phase = 'unknown'
            self._boundary._quarantined = True

    def close(self, *, token=None, cleanup=None):
        descriptor = ('close', self._resource)
        try:
            return self._boundary._call(self._original.close, token,
                                        preflight=lambda: self._closing(descriptor), resource=descriptor,
                                        on_settled=self._close_settled, cleanup=cleanup)
        except BaseException:
            with self._boundary._lock:
                if self._resource.phase == 'closing' and self._resource.close_attempt is descriptor:
                    self._resource.phase = 'unknown'
                    self._boundary._quarantined = True
            raise
