"""Private original-generation operation issuance; no native authority grant.

Retained attempt capacity precedes issuance. Actual artifact admission and the
complete installation/finalizer composition remain separate obligations.
"""
from dataclasses import dataclass
from ._operation_ordinal import OperationOrdinalRegistry,OrdinalReservation
from ._native_pg8000 import NativeBoundaryRefusal

@dataclass(slots=True,eq=False)
class IssuedOperationAttempt:
    owner: object
    session: object
    generation: object
    reservation: OrdinalReservation
    issuer: object = None

    @property
    def ordinal(self):
        value=self.reservation.result
        return value.ordinal if value is not None else None

class NativeOperationOrdinals:
    def __init__(self,tracker,*,maximum_attempts=256,maximum_ordinal=9223372036854775807):
        if type(maximum_attempts) is not int or not 1<=maximum_attempts<=4096:
            raise ValueError('Finite original attempt capacity required')
        self.tracker=tracker
        self.boundary=tracker._boundary
        self.maximum_attempts=maximum_attempts
        self.registry=OperationOrdinalRegistry(self,self.boundary,tracker._adoption_limit,maximum_ordinal)
        self.attempts=()
        self.closed=False

    def issue(self,session):
        from ._native_adoption import is_published
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
            try:result=issuer.reserve_into(generation,reservation)
            except BaseException:
                issuer.close(generation)
                session.admission_closed=True
                raise
            if result.outcome!='issued':
                raise NativeBoundaryRefusal('Original operation ordinal unavailable')
            return attempt

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
