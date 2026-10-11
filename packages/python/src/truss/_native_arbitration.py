"""Original native operation ledger composed with private arbitration.

Successful release requires the exact registered original completion producer.
Without one, native facts and locators cannot establish resource restoration.
"""
from dataclasses import dataclass
from uuid import uuid4
from threading import Lock
from ._host_execution import HostExecutor
from ._native_transactions import NativeTransactionPort, _Control, _ControlInvocation, _ControlInvocationSlot, _ControlRetention, _PortControl
from ._native_pg8000 import NativeBoundaryRefusal, NativeCancellationAdmission
from ._operation_arbitration import OperationArbitration, Admitted, Refused, Unresolved

@dataclass
class _OperationCall:
    revision: int
    resource: object
    lifecycle: object
    cleanup: object = None
    native_call: object = None

@dataclass(frozen=True, eq=False)
class _OperationCallRoot:
    calls: tuple = ()
    cleanup_calls: tuple = ()
    rollback_entry: object = None
    release_entry: object = None
    rollback_root: tuple = ()
    rollback_release_root: tuple = ()
    release_root: tuple = ()
    rollback_state: object = None
    rollback_release_state: object = None
    release_state: object = None
    retirement_state: object = None

    @classmethod
    def build(cls, calls, cleanup_calls, rollback_entry=None, release_entry=None):
        # Allocate every possible containment publication before native send.
        rollback_root = ((*cleanup_calls, rollback_entry)
                         if rollback_entry is not None else ())
        rollback_release_root = ((*rollback_root, release_entry)
                                 if rollback_entry is not None and release_entry is not None else ())
        release_root = ((*cleanup_calls, release_entry)
                        if release_entry is not None else ())
        release_retired = cls(calls, release_root) if release_entry is not None else None
        release_state = (cls(calls, release_root, rollback_entry,
                             retirement_state=release_retired)
                         if release_entry is not None else None)
        rollback_release_retired = (cls(calls, rollback_release_root)
                                   if rollback_entry is not None and release_entry is not None else None)
        rollback_release_state = (cls(calls, rollback_release_root,
                                      retirement_state=rollback_release_retired)
                                  if rollback_release_retired is not None else None)
        rollback_state = (cls(calls, rollback_root, None, release_entry,
                              release_root=rollback_release_root,
                              release_state=rollback_release_state)
                          if rollback_entry is not None else None)
        return cls(calls, cleanup_calls, rollback_entry, release_entry,
                   rollback_root, rollback_release_root, release_root,
                   rollback_state, rollback_release_state, release_state)

    @property
    def held_cleanup(self):
        return int(self.rollback_entry is not None) + int(self.release_entry is not None)

@dataclass(eq=False)
class _ReservedControlPermit:
    controls: object
    kind: str
    entry: object
    invoke: object = None
    control: object = None

@dataclass(eq=False)
class _ReservedOperationControls:
    session: object
    port: object
    savepoint_name: str
    savepoint_entry: object
    admission_entry: object
    rollback_entry: object
    release_entry: object
    initial_root: object
    savepoint_root: object
    admission_root: object
    forward_ready: bool = False
    attempt: object = None
    savepoint_permit: object = None
    rollback_permit: object = None
    release_permit: object = None
    retention: object = None

    def run_control(self, kind):
        if type(kind) is not str or kind not in ('savepoint', 'rollback_to', 'release'):
            raise NativeBoundaryRefusal('Fixed reserved control kind required')
        permit = {'savepoint': self.savepoint_permit, 'rollback_to': self.rollback_permit,
                  'release': self.release_permit}[kind]
        command = {'savepoint': 'SAVEPOINT ', 'rollback_to': 'ROLLBACK TO SAVEPOINT ',
                   'release': 'RELEASE SAVEPOINT '}[kind] + self.savepoint_name
        cleanup = None if kind == 'savepoint' else self.session.cleanup_permit
        self.port.control(command, cleanup=cleanup, call_permit=permit)
        with self.session.boundary._lock:
            session = self.session
            entry = permit.entry
            call = entry.native_call
            tracker = self.port._tracker
            expected = {'savepoint': b'SAVEPOINT\0', 'rollback_to': b'ROLLBACK\0',
                        'release': b'RELEASE\0'}[kind]
            if (call is None or not call.capture_complete or call.driver_raised
                    or call.final_status != b'T' or call.original_control is not permit.control
                    or not any(event.code == b'C' and event.payload == expected for event in call.events)
                    or tracker._state.generation is not session.generation):
                session.admission_closed = True
                raise NativeBoundaryRefusal('Reserved control settlement unavailable')
            handle = permit.control.savepoint
            if kind == 'release':
                if tracker._live(handle) or session._call_root.retirement_state is None:
                    raise NativeBoundaryRefusal('Original release retirement unavailable')
                try:
                    session._publish_call_root(session._call_root.retirement_state)
                    record, slot = self.retention.select(self.rollback_permit)
                    if slot.invocation is None:
                        slot.retired = True
                        record.phase = 'retired_unsubmitted'
                except BaseException:
                    session.admission_closed = True
                    raise
            elif not tracker._live(handle):
                raise NativeBoundaryRefusal('Original reserved savepoint publication unavailable')
        return call

@dataclass(frozen=True, eq=False)
class _CleanupPermit:
    session: object

@dataclass(eq=False)
class NativeOperationSession:
    owner: object
    context: object
    boundary: object
    generation: object
    token: object
    locator: bytes
    call_limit: int
    _call_root: object = None
    admission_closed: bool = False
    cleanup_limit: int = 16
    cleanup_permit: object = None
    cleanup_closed: bool = False
    result_custody: object = None
    completion: object = None
    released: bool = False
    cancellation: object = None
    deadline: object = None
    _reserved_controls: object = None

    def __post_init__(self):
        self._call_root = _OperationCallRoot.build((), ())

    @property
    def calls(self):
        return self._call_root.calls

    @property
    def cleanup_calls(self):
        return self._call_root.cleanup_calls

    def _publish_call_root(self, root):
        self._call_root = root

    def _check_call(self, boundary, token, cleanup=None, *, admission=True):
        if admission and self.deadline is not None:
            self.deadline.check()
        if (boundary is not self.boundary or token is not self.token
                or boundary._operation is not self.token
                or boundary._operation_ledger is not self
                or self.generation.ended
                or boundary._transaction_tracker._state.generation is not self.generation):
            raise NativeBoundaryRefusal('Original native operation correspondence lost')
        if self._call_root.retirement_state is not None:
            raise NativeBoundaryRefusal('Reserved release settlement remains unavailable')
        if self._reserved_controls is not None and not self._reserved_controls.forward_ready:
            raise NativeBoundaryRefusal('Reserved original admission remains unavailable')
        if cleanup is not None:
            if (type(cleanup) is not _CleanupPermit or cleanup is not self.cleanup_permit
                    or cleanup.session is not self or self.cleanup_closed):
                raise NativeBoundaryRefusal('Original cleanup permit required')
            if len(self.cleanup_calls) + self._call_root.held_cleanup >= self.cleanup_limit:
                raise NativeBoundaryRefusal('Reserved native cleanup capacity exhausted')
        else:
            if (self.admission_closed or self.owner._executor._closed
                    or not self.context.custody.usable):
                raise NativeBoundaryRefusal('Ordinary native admission closed')
            if admission and self.context.custody.cancellation is not None and self.context.custody.cancellation.requested():
                raise NativeCancellationAdmission('Original adoption cancellation latched')
            if len(self.calls) >= self.call_limit:
                raise NativeBoundaryRefusal('Native operation call custody exhausted')

    def _prepare_reserved_controls(self, attempt):
        # Called by the original issuer under the shared native guard, before
        # ordinal publication. No native invocation permit is supplied here.
        port = self.context.custody.port
        if (type(port) is not NativeTransactionPort or port._tracker._boundary is not self.boundary
                or port._generation is not self.generation or port._token is not self.token
                or self._reserved_controls is not None or self.calls or self.cleanup_calls
                or self._call_root.held_cleanup or self.call_limit < 2 or self.cleanup_limit < 2):
            raise NativeBoundaryRefusal('Original finite operation controls unavailable')
        tracker = port._tracker
        if len(port._control_records) + 3 > 4096 or len(tracker._control_invocations) + 3 > 4096:
            raise NativeBoundaryRefusal('Original joint control retention exhausted')
        name = port._reserve_savepoint_name_locked(self.owner._executor)
        if name is None:
            raise NativeBoundaryRefusal('Original mediated savepoint namespace required')
        savepoint = _OperationCall(0, None, None)
        admission = _OperationCall(0, None, None)
        rollback = _OperationCall(0, None, None, self.cleanup_permit)
        release = _OperationCall(0, None, None, self.cleanup_permit)
        initial = _OperationCallRoot.build((), (), rollback, release)
        savepoint_root = _OperationCallRoot.build((savepoint,), (), rollback, release)
        admission_root = _OperationCallRoot.build((savepoint, admission), (), rollback, release)
        controls = _ReservedOperationControls(self, port, name, savepoint, admission,
                                              rollback, release, initial,
                                              savepoint_root, admission_root)
        controls.attempt = attempt
        controls.savepoint_permit = _ReservedControlPermit(controls, 'savepoint', savepoint)
        controls.rollback_permit = _ReservedControlPermit(controls, 'rollback_to', rollback)
        controls.release_permit = _ReservedControlPermit(controls, 'release', release)
        records = tuple(_PortControl(kind, phase='reserved') for kind in
                        ('SAVEPOINT', 'ROLLBACK TO SAVEPOINT', 'RELEASE SAVEPOINT'))
        slots = tuple(_ControlInvocationSlot(tracker, kind) for kind in
                      ('savepoint', 'rollback_to', 'release'))
        controls.retention = _ControlRetention(controls, records, slots)
        port_root = (*port._control_records, *records)
        tracker_root = (*tracker._control_invocations, *slots)
        self._reserved_controls = controls
        attempt.controls = controls
        try:
            port._publish_control_retention(port_root)
            tracker._publish_invocation_retention(tracker_root)
            self._publish_call_root(initial)
            if not controls.retention.ready() or self._call_root is not initial:
                raise NativeBoundaryRefusal('Original joint retention publication incomplete')
        except BaseException:
            self.admission_closed = True
            raise
        return controls

    def _select_control_retention(self, permit, *, claimed=False):
        controls = self._reserved_controls
        if (type(permit) is not _ReservedControlPermit or controls is None
                or permit.controls is not controls
                or not any(permit is item for item in (controls.savepoint_permit,
                                                       controls.rollback_permit, controls.release_permit))):
            raise NativeBoundaryRefusal('Original retained control permit required')
        record, slot = controls.retention.select(permit)
        if claimed and (record.phase != 'prepared' or controls.port._last_control is not record):
            raise NativeBoundaryRefusal('Original claimed port control required')
        return record, slot

    def _bind_reserved_control(self, permit, invocation):
        tracker = self.boundary._transaction_tracker
        if (type(invocation) is not _ControlInvocation or invocation.tracker is not tracker
                or not any(type(item) is _ControlInvocationSlot and item.invocation is invocation
                           for item in tracker._control_invocations)):
            raise NativeBoundaryRefusal('Original tracker control invocation required')
        control, invoke, sql = invocation.control, invocation.invoke, invocation.sql
        controls = self._reserved_controls
        if (type(permit) is not _ReservedControlPermit or controls is None
                or permit.controls is not controls
                or not any(permit is item for item in (controls.savepoint_permit,
                                                       controls.rollback_permit, controls.release_permit))
                or type(control) is not _Control or permit.invoke is not None
                or control.kind != permit.kind or control.chain
                or control.expected is not self.boundary._transaction_tracker._state
                or control.savepoint is None or control.savepoint.name != controls.savepoint_name
                or control.savepoint.generation is not self.generation):
            raise NativeBoundaryRefusal('Original reserved control binding required')
        port = controls.port
        if permit.kind == 'savepoint':
            pending = port._pending_savepoint
            issued = next((item for namespace in self.generation.namespaces
                           for item in namespace.issued if item.name == controls.savepoint_name), None)
            if (pending is None or pending[0] is not control.savepoint
                    or issued is None or not issued.submitted):
                raise NativeBoundaryRefusal('Original issued port savepoint required')
        elif port._savepoints.get(controls.savepoint_name) is not control.savepoint:
            raise NativeBoundaryRefusal('Original retained port savepoint required')
        prefix = {'savepoint': 'SAVEPOINT ', 'rollback_to': 'ROLLBACK TO SAVEPOINT ',
                  'release': 'RELEASE SAVEPOINT '}[permit.kind]
        if sql != prefix + self.port_name_sql(controls.savepoint_name):
            raise NativeBoundaryRefusal('Fixed original control SQL required')
        permit.control = control
        permit.invoke = invoke
        permit.entry.lifecycle = control

    @staticmethod
    def port_name_sql(name):
        return '"' + name + '"'

    def _check_call_permit(self, boundary, token, invoke, resource, lifecycle, cleanup, permit):
        from ._native_operation_ordinals import NativeAdmissionInvocation
        if type(permit) is NativeAdmissionInvocation:
            return self.boundary._transaction_tracker._operation_ordinals._check_admission_call_locked(
                self, boundary, token, invoke, resource, lifecycle, cleanup, permit)
        if self.deadline is not None:
            self.deadline.check()
        controls = self._reserved_controls
        tracker = boundary._transaction_tracker
        if (type(permit) is not _ReservedControlPermit or controls is None
                or permit.controls is not controls or controls.session is not self
                or not any(permit is item for item in (controls.savepoint_permit,
                                                       controls.rollback_permit, controls.release_permit))
                or controls.attempt.controls is not controls or controls.attempt.ordinal is None
                or controls.retention is None or not controls.retention.ready()
                or boundary is not self.boundary or token is not self.token
                or tracker._state.generation is not self.generation or self.generation.ended
                or lifecycle is not permit.control or invoke is not permit.invoke
                or permit.control is None or permit.control.expected is not tracker._state
                or resource is not None):
            raise NativeBoundaryRefusal('Original invocation-bound control required')
        entry = permit.entry
        if any(item is entry for item in (*self.calls, *self.cleanup_calls)):
            raise NativeBoundaryRefusal('Original reserved control already consumed')
        if permit.kind == 'savepoint':
            if (cleanup is not None or self._call_root is not controls.initial_root
                    or self.admission_closed or self.owner._executor._closed
                    or not self.context.custody.usable or tracker._state.status != b'T'):
                raise NativeBoundaryRefusal('Original forward control unavailable')
            cancellation = self.context.custody.cancellation
            if cancellation is not None and cancellation.requested():
                raise NativeCancellationAdmission('Original adoption cancellation latched')
        else:
            if (cleanup is not self.cleanup_permit or self.cleanup_closed
                    or not tracker._live(permit.control.savepoint)
                    or self._call_root.retirement_state is not None):
                raise NativeBoundaryRefusal('Original containment control unavailable')
            if permit.kind == 'rollback_to' and self._call_root.rollback_entry is not entry:
                raise NativeBoundaryRefusal('Original rollback reservation unavailable')
            if permit.kind == 'release' and (self._call_root.release_entry is not entry
                                             or tracker._state.status != b'T'):
                raise NativeBoundaryRefusal('Original release reservation unavailable')

    def _reserve_call_permit(self, boundary, token, invoke, resource, lifecycle, cleanup, permit):
        from ._native_operation_ordinals import NativeAdmissionInvocation
        if type(permit) is NativeAdmissionInvocation:
            return self.boundary._transaction_tracker._operation_ordinals._reserve_admission_call_locked(
                self, boundary, token, invoke, resource, lifecycle, cleanup, permit)
        self._check_call_permit(boundary, token, invoke, resource, lifecycle, cleanup, permit)
        controls = self._reserved_controls
        candidate = (controls.savepoint_root if permit.kind == 'savepoint' else
                     self._call_root.rollback_state if permit.kind == 'rollback_to' else
                     self._call_root.release_state)
        if candidate is None:
            raise NativeBoundaryRefusal('Original complete branch state unavailable')
        permit.entry.revision = boundary._revision + 1
        self._publish_call_root(candidate)
        return permit.entry

    def _reserve_containment(self, rollback_entry, release_entry):
        # Original enclosing producer must hold the boundary guard. These
        # descriptors do not independently authorize native controls.
        previous = self._call_root
        if (type(rollback_entry) is not _OperationCall or type(release_entry) is not _OperationCall
                or rollback_entry is release_entry or previous.held_cleanup
                or rollback_entry.native_call is not None or release_entry.native_call is not None
                or len(previous.cleanup_calls) + 2 > self.cleanup_limit):
            raise NativeBoundaryRefusal('Original finite containment reservation unavailable')
        candidate = _OperationCallRoot.build(previous.calls, previous.cleanup_calls,
                                            rollback_entry, release_entry)
        self._publish_call_root(candidate)
        return candidate

    def _reserve_call(self, boundary, token, resource, lifecycle, cleanup=None):
        self._check_call(boundary, token, cleanup, admission=False)
        entry = _OperationCall(boundary._revision + 1, resource, lifecycle, cleanup)
        previous = self._call_root
        calls = (*previous.calls, entry) if cleanup is None else previous.calls
        cleanup_calls = previous.cleanup_calls if cleanup is None else (*previous.cleanup_calls, entry)
        candidate = _OperationCallRoot.build(calls, cleanup_calls,
                                            previous.rollback_entry, previous.release_entry)
        self._publish_call_root(candidate)
        return entry

@dataclass(eq=False)
class _NativeBinding:
    owner: object
    attempt: object
    boundary: object
    generation: object
    token: object
    session: object = None
    refused: object = None

class NativeArbitration:
    def __init__(self, executor, *, call_limit=256):
        if type(executor) is not HostExecutor or type(call_limit) is not int or call_limit < 1:
            raise ValueError('Original executor and positive exact call limit required')
        self._executor = executor
        self._call_limit = call_limit
        self._sessions = ()
        self._bindings = ()
        self._lock = Lock()
        self.registry = OperationArbitration(executor, self._verify)

    def bind(self, attempt):
        # Service serializes bindings; registry and boundary locks are never
        # held together. Original pending custody precedes registry acquisition.
        with self._lock:
            with self.registry._lock:
                candidate = self.registry._root.entries.get(attempt) if type(attempt) is object else None
                if candidate is None:
                    return Refused('integrity')
                custody = candidate.custody
                port = custody.port
                if type(port) is not NativeTransactionPort:
                    return Refused('unsupported_profile')
            boundary = port._tracker._boundary
            with boundary._lock:
                binding = next((b for b in self._bindings if b.attempt is attempt), None)
                if binding is not None and binding.refused is not None:
                    return binding.refused
                if (binding is not None and binding.session is not None
                        and boundary._operation_ledger is binding.session
                        and boundary._pending_operation_ledger is binding.session):
                    return binding.session
                if binding is None:
                    generation = port._generation
                    if (self._executor._closed or not custody.usable or generation.ended
                            or port._token is None or boundary._operation is not port._token
                            or boundary._calling or boundary._quarantined
                            or boundary._operation_ledger is not None
                            or boundary._pending_operation_ledger is not None
                            or port._tracker._state.generation is not generation):
                        return Refused('invalid_transaction')
                    from ._native_adoption import is_published
                    if not is_published(generation, custody):
                        return Refused('invalid_transaction')
                    binding = _NativeBinding(self, attempt, boundary, generation, port._token)
                    retained = (*self._bindings, binding)
                    original_retained = (*boundary._native_arbitration_bindings, binding)
                    self._bindings = retained
                    boundary._native_arbitration_bindings = original_retained
                    boundary._pending_operation_ledger = binding
                # Root allocation can fail after binding retention. Every retry
                # must re-establish the exact pending guard before admission.
                if binding.session is None:
                    if (boundary._operation is not binding.token or boundary._calling
                            or boundary._quarantined or binding.generation.ended
                            or port._tracker._state.generation is not binding.generation
                            or boundary._operation_ledger is not None
                            or boundary._pending_operation_ledger not in (None, binding)):
                        return Refused('invalid_transaction')
                    boundary._pending_operation_ledger = binding
            # A lost acquire reply or allocation failure leaves the original
            # pending guard held. Retry reconciles this exact original attempt.
            admitted = self.registry.acquire(attempt)
            with self.registry._lock:
                entry = self.registry._root.entries[attempt]
                context = entry.completion_context
                nonacquired = entry.lease is None and entry.phase in ('refused', 'abandoned')
            if type(admitted) is not Admitted:
                if type(admitted) is Refused and nonacquired:
                    with boundary._lock:
                        binding.refused = admitted
                        if boundary._pending_operation_ledger is binding:
                            boundary._pending_operation_ledger = None
                return admitted
            with boundary._lock:
                if (self._executor._closed or not custody.usable or binding.generation.ended
                        or boundary._operation is not binding.token or boundary._calling
                        or boundary._quarantined
                        or port._tracker._state.generation is not binding.generation
                        or not (boundary._pending_operation_ledger is binding
                                or (binding.session is not None
                                    and boundary._pending_operation_ledger is binding.session))):
                    return Unresolved(entry.recovery)
                session = binding.session
                if session is None:
                    session = self._make_session(context, binding)
                    binding.session = session
                if not any(s is session for s in self._sessions):
                    self._sessions = (*self._sessions, session)
                if not any(s is session for s in boundary._native_arbitration_sessions):
                    boundary._native_arbitration_sessions = (*boundary._native_arbitration_sessions, session)
                self._publish_binding(boundary, session)
                return session

    def issue_operation(self,session,*,reserve_controls=False):
        if type(session) is not NativeOperationSession or session.owner is not self:
            raise NativeBoundaryRefusal('Original operation session required')
        return session.boundary._transaction_tracker._operation_ordinals.issue(session,reserve_controls=reserve_controls)

    def _make_session(self, context, binding):
        session = NativeOperationSession(self, context, binding.boundary, binding.generation,
                                      binding.token, uuid4().hex.encode('ascii'), self._call_limit)
        session.cleanup_permit = _CleanupPermit(session)
        return session

    def _publish_binding(self, boundary, session):
        boundary._operation_ledger = session
        boundary._pending_operation_ledger = session

    def _verify(self, evidence, context):
        # A locator identifies original custody, not a completion artifact.
        # Completion attempts freeze ordinary admission even when invalid.
        with self._lock:
            session = next((s for s in self._sessions if s.context is context), None)
            if session is None:
                return None
            with session.boundary._lock:
                session.admission_closed = True
            producer = getattr(self, '_completion_producer', None)
            if producer is None:
                return None
            return producer.verify_completion(session, evidence)

    def release(self, session):
        with self._lock:
            original = (type(session) is NativeOperationSession and session.owner is self
                        and any(s is session for s in self._sessions))
        if not original:
            raise ValueError('Original native operation session required')
        with session.boundary._lock:
            session.admission_closed = True
        completion = session.completion
        evidence = session.locator if completion is None else completion.artifact
        result = self.registry.release(session.context.lease, evidence)
        if result == 'released':
            producer = getattr(self, '_completion_producer', None)
            if producer is None:
                return Unresolved(('arbitration:original-producer-unavailable',))
            return producer.handback(session)
        return result
