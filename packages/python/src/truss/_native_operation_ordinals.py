"""Private original-generation operation issuance; no native authority grant.

Retained attempt capacity precedes issuance. Actual artifact admission and the
complete installation/finalizer composition remain separate obligations.
"""
from dataclasses import dataclass
from ._operation_ordinal import OperationOrdinalRegistry,OrdinalReservation
from ._native_pg8000 import NativeBoundaryRefusal, NativeCall
from ._native_admission_request import encode_admission_request

@dataclass(slots=True,eq=False)
class IssuedOperationAttempt:
    owner: object
    session: object
    generation: object
    reservation: OrdinalReservation
    issuer: object = None
    controls: object = None

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
            attempt=IssuedOperationAttempt(self,session,generation,reservation)
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
