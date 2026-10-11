"""Private original-generation operation issuance; no native authority grant.

Retained attempt capacity precedes issuance. Actual artifact admission and the
complete installation/finalizer composition remain separate obligations.
"""
from dataclasses import dataclass
from ._operation_ordinal import OperationOrdinalRegistry,OrdinalReservation
from ._native_pg8000 import NativeBoundaryRefusal, NativeCall
from ._native_admission_request import encode_admission_request
from ._native_admission_capture import NativeAdmissionCapture
from ._native_result_custody import NativeTextLimits
from ._native_deadline import NativeOperationDeadline
from ._native_driver_profile import original_control_profile, original_admission_snapshot, admission_snapshot_unchanged

@dataclass(slots=True,eq=False)
class IssuedOperationAttempt:
    owner: object
    session: object
    generation: object
    reservation: OrdinalReservation
    issuer: object = None
    controls: object = None
    deadline: object = None

    @property
    def admission_request(self):
        return next((request for request in self.owner.requests if request.attempt is self), None)

    @property
    def ordinal(self):
        value=self.reservation.result
        return value.ordinal if value is not None else None

@dataclass(frozen=True, slots=True, eq=False)
class PreparedNativeAdmission:
    attempt: IssuedOperationAttempt
    encoded: object
    entry: object
    scope: str = 'original_attempt_request_only'

@dataclass(frozen=True, slots=True, eq=False)
class NativeAdmissionInvocation:
    owner: object
    request: PreparedNativeAdmission
    sql: str
    invoke: object
    gate: object
    context: object
    sender: object
    context_type: object
    flush: object
    symbols: object

class NativeOperationOrdinals:
    def __init__(self,tracker,*,maximum_attempts=256,maximum_ordinal=9223372036854775807):
        if type(maximum_attempts) is not int or not 1<=maximum_attempts<=4096:
            raise ValueError('Finite original attempt capacity required')
        self.tracker=tracker
        self.boundary=tracker._boundary
        self.maximum_attempts=maximum_attempts
        self.registry=OperationOrdinalRegistry(self,self.boundary,tracker._adoption_limit,maximum_ordinal)
        self.attempts=()
        self.requests=()
        self.admission_invocations=()
        self.closed=False

    def issue(self,session,*,reserve_controls=False):
        from ._native_adoption import is_published
        if type(reserve_controls) is not bool:
            raise NativeBoundaryRefusal('Exact control reservation selection required')
        with self.boundary._lock:
            b=self.boundary;generation=self.tracker._state.generation
            if (self.tracker._operation_ordinals is not self
                or b._transaction_tracker is not self.tracker
                or not any(s is session for s in b._native_arbitration_sessions) or self.closed
                or session.boundary is not b or session.generation is not generation
                or generation is None or generation.ended or b._quarantined
                or self.tracker._state.status!=b'T'
                or b._calling or b._operation is not session.token
                or b._operation_ledger is not session or b._pending_operation_ledger is not session
                or session.admission_closed or session.released
                or session.owner._executor._closed or not session.context.custody.usable
                or not is_published(generation,session.context.custody)):
                raise NativeBoundaryRefusal('Original operation issuer lifetime unavailable')
            session._check_call(b,session.token,admission=True)
            if session.calls or session.cleanup_calls:
                raise NativeBoundaryRefusal('Issue before original business control submission')
            if any(a.session is session for a in self.attempts):
                raise NativeBoundaryRefusal('Original operation already reserved; observe retained attempt')
            # Count preflight only: actual attempt-owned call permits remain required.
            if (len(self.attempts)>=self.maximum_attempts
                or session.call_limit-len(session.calls)<2
                or session.cleanup_limit-len(session.cleanup_calls)<2):
                raise NativeBoundaryRefusal('Original operation attempt/control capacity exhausted')
            reservation=OrdinalReservation()
            attempt=IssuedOperationAttempt(self,session,generation,reservation,deadline=session.deadline)
            issuer=self.registry.bind(self,b,generation)
            attempt.issuer=issuer
            self.attempts=(*self.attempts,attempt)
            try:
                if reserve_controls:
                    session._prepare_reserved_controls(attempt)
                result=issuer.reserve_into(generation,reservation)
            except BaseException:
                issuer.close(generation)
                session.admission_closed=True
                raise
            if result.outcome!='issued':
                raise NativeBoundaryRefusal('Original operation ordinal unavailable')
            return attempt

    def _check_request_attempt_locked(self, attempt):
        from ._native_adoption import is_published
        b = self.boundary
        if (type(attempt) is not IssuedOperationAttempt or attempt.owner is not self
                or not any(item is attempt for item in self.attempts)
                or self.tracker._operation_ordinals is not self
                or b._transaction_tracker is not self.tracker or self.closed):
            raise NativeBoundaryRefusal('Original retained issuance required')
        session, controls = attempt.session, attempt.controls
        generation = attempt.generation
        if (controls is None or controls is not session._reserved_controls
                or controls.attempt is not attempt or controls.session is not session
                or attempt.ordinal is None or generation is not self.tracker._state.generation
                or generation.ended or self.tracker._state.status != b'T'
                or session.boundary is not b or session.generation is not generation
                or not any(item is session for item in b._native_arbitration_sessions)
                or b._operation_ledger is not session or b._pending_operation_ledger is not session
                or b._operation is not session.token or b._calling or b._quarantined
                or session.admission_closed or session.released or session.owner._executor._closed
                or not session.context.custody.usable
                or not is_published(generation, session.context.custody)
                or session._call_root is not controls.savepoint_root
                or not controls.retention.ready()):
            raise NativeBoundaryRefusal('Original post-savepoint request lifetime required')
        if session.deadline is not None:
            session.deadline.check()
        cancellation = session.context.custody.cancellation
        if cancellation is not None and cancellation.requested():
            raise NativeBoundaryRefusal('Original request cancellation latched')
        call = controls.savepoint_entry.native_call
        record = controls.retention.records[0]
        control = controls.savepoint_permit.control
        if (type(call) is not NativeCall or not call.capture_complete or call.driver_raised
                or call.final_status != b'T' or call.original_control is not control
                or control is None or control.kind != 'savepoint'
                or not any(event.code == b'C' and event.payload == b'SAVEPOINT\0' for event in call.events)
                or record.phase != 'published' or record.native_call is not call
                or controls.port._token is not session.token
                or controls.port._generation is not generation
                or controls.port._savepoints.get(controls.savepoint_name) is not control.savepoint
                or not self.tracker._live(control.savepoint)):
            raise NativeBoundaryRefusal('Original settled savepoint request custody required')

    def _publish_admission_requests(self, root):
        self.requests = root

    def prepare_admission(self, attempt, original_input):
        with self.boundary._lock:
            self._check_request_attempt_locked(attempt)
            if attempt.admission_request is not None or len(self.requests) >= self.maximum_attempts:
                raise NativeBoundaryRefusal('Original request already retained or capacity exhausted')
            encoded = encode_admission_request(original_input, attempt.ordinal)
            request = PreparedNativeAdmission(attempt, encoded, attempt.controls.admission_entry)
            root = (*self.requests, request)
            self._check_request_attempt_locked(attempt)
            try:
                self._publish_admission_requests(root)
                if self.requests is not root or attempt.admission_request is not request:
                    raise NativeBoundaryRefusal('Original request publication unavailable')
            except BaseException:
                self.closed = True
                attempt.session.admission_closed = True
                raise
            return request

    def _check_admission_call_locked(self, session, boundary, token, invoke, resource, lifecycle, cleanup, invocation):
        if (type(invocation) is not NativeAdmissionInvocation or invocation.owner is not self
                or not any(item is invocation for item in self.admission_invocations)):
            raise NativeBoundaryRefusal('Original retained admission invocation required')
        request = invocation.request
        attempt = request.attempt
        self._check_request_attempt_locked(attempt)
        if (attempt.session is not session or boundary is not self.boundary
                or token is not session.token or invoke is not invocation.invoke
                or resource is not None or lifecycle is not None or cleanup is not None
                or attempt.admission_request is not request
                or request.entry is not attempt.controls.admission_entry
                or session.result_custody is not invocation.gate
                or not invocation.gate.installed or invocation.gate.failed or invocation.gate.detached
                or type(attempt.deadline) is not NativeOperationDeadline or session.deadline is not attempt.deadline
                or invocation.gate.ingress_deadline is None or invocation.gate.outbound is None
                or invocation.sender.__self__ is not boundary._connection
                or not admission_snapshot_unchanged(invocation.symbols)
                or type(invocation.context) is not invocation.context_type
                or invocation.gate.boundary._connection._sock is not invocation.gate
                or boundary._connection.handle_messages is not invocation.gate._original_messages_entry):
            raise NativeBoundaryRefusal('Original request-bound admission call required')

    def _reserve_admission_call_locked(self, session, boundary, token, invoke, resource, lifecycle, cleanup, invocation):
        self._check_admission_call_locked(session, boundary, token, invoke, resource, lifecycle, cleanup, invocation)
        entry = invocation.request.entry
        entry.revision = boundary._revision + 1
        session._publish_call_root(invocation.request.attempt.controls.admission_root)
        return entry

    def _publish_admission_invocations(self, root):
        self.admission_invocations = root

    def _send_admission(self, invocation):
        gate = invocation.gate
        gate.retain_context_before_send(invocation.context, invocation.request.entry)
        invocation.sender(invocation.sql)
        invocation.flush(gate.boundary._connection._sock)
        gate.boundary._connection.handle_messages(invocation.context)
        gate.boundary._connection._context = invocation.context
        return invocation.context.rows

    def dispatch_admission_candidate(self, request):
        # Administrative original-driver composition only. No installed/artifact
        # authority or public capability can be inferred from this result.
        if not original_control_profile(self.boundary):
            raise NativeBoundaryRefusal('Original admission driver profile required')
        symbols = original_admission_snapshot()
        if symbols is None:
            raise NativeBoundaryRefusal('Original admission Context and flush required')
        _, context_type, _, _, flush, _ = symbols
        with self.boundary._lock:
            if (type(request) is not PreparedNativeAdmission
                    or not any(item is request for item in self.requests)):
                raise NativeBoundaryRefusal('Original prepared admission request required')
            attempt = request.attempt
            self._check_request_attempt_locked(attempt)
            if type(attempt.deadline) is not NativeOperationDeadline or attempt.session.deadline is not attempt.deadline:
                raise NativeBoundaryRefusal('Original operation deadline required before admission dispatch')
            if (any(item.request is request for item in self.admission_invocations)
                    or len(self.admission_invocations) >= self.maximum_attempts):
                raise NativeBoundaryRefusal('Original admission already retained or capacity exhausted')
            prefix = ('SELECT admitted.writer_xid, admitted.ordinal, admitted.context_hex, '
                      'pg_catalog.pg_current_xact_id()::pg_catalog.text AS actual_writer_xid FROM (')
            suffix = ') AS admitted'
            if request.encoded.encoded_bytes + len(prefix) + len(suffix) + 6 > 1048576:
                raise NativeBoundaryRefusal('Full original admission SQL capacity exhausted')
            sql = prefix + request.encoded.sql + suffix
            session = attempt.session
            if session.result_custody is not None:
                raise NativeBoundaryRefusal('Original admission capture already retained')
            sender = self.boundary._connection.send_QUERY
            original_input = request.encoded.original_input
            if original_input.family != 'base' and 2*(len(original_input.asserted) + len(original_input.capture_profile)) > 4096:
                raise NativeBoundaryRefusal('Input exceeds selected reduced native context profile')
        gate = NativeAdmissionCapture(session, NativeTextLimits(columns=4, rows=1), entry=request.entry)
        try:
            gate.install()
            with self.boundary._lock:
                self._check_request_attempt_locked(attempt)
                context = context_type(sql)
                invoke = lambda: self._send_admission(invocation)
                invocation = NativeAdmissionInvocation(self, request, sql, invoke, gate, context, sender, context_type, flush, symbols)
                root = (*self.admission_invocations, invocation)
                try:
                    self._publish_admission_invocations(root)
                    if self.admission_invocations is not root:
                        raise NativeBoundaryRefusal('Original admission invocation publication unavailable')
                except BaseException:
                    self.closed = True
                    session.admission_closed = True
                    raise
        except BaseException:
            with self.boundary._lock:
                if session.result_custody is gate:
                    session.admission_closed = True
            raise
        try:
            rows = self.boundary._call(invoke, session.token, call_permit=invocation)
            call = request.entry.native_call
            result = gate.observe(rows, call, attempt.ordinal)
            with self.boundary._lock:
                if (session._call_root is not attempt.controls.admission_root
                        or attempt.admission_request is not request
                        or request.entry.native_call is not result.original_call):
                    raise NativeBoundaryRefusal('Original admission settlement correspondence unavailable')
            return result
        finally:
            with self.boundary._lock:
                session.admission_closed = True

    def observe(self,attempt):
        with self.boundary._lock:
            if type(attempt) is not IssuedOperationAttempt or not any(a is attempt for a in self.attempts):
                raise NativeBoundaryRefusal('Original retained attempt required')
            return attempt.reservation.result

    def end_locked(self,generation):
        # Called only while the original native guard is held.
        self.registry.end_if_bound(self,self.boundary,generation)

    def close_locked(self):
        # Never infer transaction termination from closed admission.
        self.closed=True
        self.registry.close(self)
