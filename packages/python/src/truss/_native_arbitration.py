"""Original native operation ledger composed with private arbitration.

Successful release requires the exact registered original completion producer.
Without one, native facts and locators cannot establish resource restoration.
"""
from dataclasses import dataclass
from uuid import uuid4
from threading import Lock
from ._host_execution import HostExecutor
from ._native_transactions import NativeTransactionPort
from ._native_pg8000 import NativeBoundaryRefusal
from ._operation_arbitration import OperationArbitration, Admitted, Refused, Unresolved

@dataclass
class _OperationCall:
    revision: int
    resource: object
    lifecycle: object
    cleanup: object = None
    native_call: object = None

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
    calls: tuple = ()
    admission_closed: bool = False
    cleanup_limit: int = 16
    cleanup_calls: tuple = ()
    cleanup_permit: object = None
    cleanup_closed: bool = False
    result_custody: object = None
    completion: object = None
    released: bool = False

    def _check_call(self, boundary, token, cleanup=None):
        if (boundary is not self.boundary or token is not self.token
                or boundary._operation is not self.token
                or boundary._operation_ledger is not self
                or self.generation.ended
                or boundary._transaction_tracker._state.generation is not self.generation):
            raise NativeBoundaryRefusal('Original native operation correspondence lost')
        if cleanup is not None:
            if (type(cleanup) is not _CleanupPermit or cleanup is not self.cleanup_permit
                    or cleanup.session is not self or self.cleanup_closed):
                raise NativeBoundaryRefusal('Original cleanup permit required')
            if len(self.cleanup_calls) >= self.cleanup_limit:
                raise NativeBoundaryRefusal('Reserved native cleanup capacity exhausted')
        else:
            if (self.admission_closed or self.owner._executor._closed
                    or not self.context.custody.usable):
                raise NativeBoundaryRefusal('Ordinary native admission closed')
            if len(self.calls) >= self.call_limit:
                raise NativeBoundaryRefusal('Native operation call custody exhausted')

    def _reserve_call(self, boundary, token, resource, lifecycle, cleanup=None):
        self._check_call(boundary, token, cleanup)
        entry = _OperationCall(boundary._revision + 1, resource, lifecycle, cleanup)
        if cleanup is None:
            self.calls = (*self.calls, entry)
        else:
            self.cleanup_calls = (*self.cleanup_calls, entry)
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
