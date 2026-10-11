"""Private original acquisition lifecycle; not source/authority admission.

Only mediated native controls preserve this state. Any ordinary subsequent
call closes it before invocation until a protected dispatcher is qualified.
"""
from dataclasses import dataclass
from ._native_pg8000 import NativeBoundaryRefusal,NativeCall

@dataclass(frozen=True,slots=True,eq=False)
class NativeFreshEpochObservation:
    original_call: NativeCall
    original_row: tuple
    original_request: bytes
    original_frames: tuple
    scope: str='original_epoch_response_only'

@dataclass(slots=True,eq=False)
class NativeEpochAcquisition:
    owner: object
    session: object
    observation: object
    generation: object
    scopes: tuple
    capture: object=None
    valid: bool=True
    reason: str=''
    scope: str='original_acquisition_lifecycle_only'

    def live(self):
        b=self.owner.tracker._boundary
        with b._lock:
            state=self.owner.tracker._state
            return (self.valid and any(r is self for r in self.owner.records)
                and self.owner.tracker._epoch_acquisitions is self.owner
                and b._transaction_tracker is self.owner.tracker and not b._quarantined and not b._calling
                and state.generation is self.generation and not self.generation.ended
                and state.status==b'T' and b._connection._transaction_status==b'T'
                and b._connection._usock is b._original_socket
                and b._original_socket.fileno()>=0 and not b._original_stream.closed
                and (b._connection._sock is b._original_stream or b._connection._sock is self.capture)
                and not self.session.released and not self.session.owner._executor._closed
                and self.session.context.custody.usable
                and b._operation is self.session.token and b._operation_ledger is self.session
                and b._pending_operation_ledger is self.session
                and len(state.savepoints)>=len(self.scopes)
                and all(a is c for a,c in zip(self.scopes,state.savepoints)))

class NativeEpochAcquisitions:
    def __init__(self,tracker,maximum=256):
        if type(maximum) is not int or not 1<=maximum<=4096:raise ValueError('Finite acquisition capacity required')
        self.tracker=tracker;self.maximum=maximum;self.records=()
    def invalidate(self,reason):
        for r in self.records:
            if r.valid:r.valid=False;r.reason=reason
    def retain(self,gate,observation):
        b=self.tracker._boundary
        with b._lock:
            state=self.tracker._state;session=gate.session
            if len(self.records)>=self.maximum:
                raise NativeBoundaryRefusal('Original acquisition capacity exhausted')
            if (session.result_custody is not gate or type(observation) is not NativeFreshEpochObservation
                    or self.tracker._epoch_acquisitions is not self or b._transaction_tracker is not self.tracker
                    or b._calling or b._quarantined or b._connection._transaction_status!=b'T'
                    or b._pending_operation_ledger is not session
                    or not any(s is session for s in b._native_arbitration_sessions)
                    or state.generation is None or state.status!=b'T'
                    or session.generation is not state.generation or session.released
                    or gate.original_acquisition is not None or gate.original_observation is not None
                    or type(observation.original_call) is not NativeCall
                    or observation.original_call is not b.last_call or not observation.original_call.capture_complete
                    or observation.original_call.driver_raised or observation.original_call.final_status!=b'T'
                    or gate.entry is None or gate.entry.native_call is not observation.original_call
                    or gate.failed or gate.response_stage!=4 or gate.detached):
                raise NativeBoundaryRefusal('Original complete acquisition custody required')
            session._check_call(b,session.token)
            profile=gate._check_recipe().profile
            if (type(observation.scope) is not str or type(observation.original_row) is not tuple
                    or any(type(v) is not str for v in observation.original_row)
                    or observation.scope!=profile[2] or len(observation.original_row)!=12
                    or observation.original_row[-1]!=profile[1]):
                raise NativeBoundaryRefusal('Original epoch response/lifecycle scope required')
            record=NativeEpochAcquisition(self,session,observation,state.generation,state.savepoints,capture=gate,scope=profile[3])
            self.records=(*self.records,record);gate.original_acquisition=record
            return record
    def before(self,control):
        # No arbitrary SQL can change source while retaining a live record.
        if control is None:self.invalidate('unqualified-ordinary-call')
    def after(self,control,call,before):
        if (not call.capture_complete or call.driver_raised or call.final_status!=b'T'
                or control is None or control.expected is not before):
            self.invalidate('uncertain-or-ended-native-lifecycle');return
        if control.kind in ('begin','commit','rollback'):
            self.invalidate('native-generation-transition');return
        if control.kind=='savepoint':return
        target=next((i for i,s in enumerate(before.savepoints) if s is control.savepoint),None)
        if target is None:
            self.invalidate('unknown-original-scope');return
        for r in self.records:
            if not r.valid:continue
            if r.generation is not before.generation:
                r.valid=False;r.reason='original-generation-lost';continue
            if control.kind=='rollback_to' and target<len(r.scopes):
                r.valid=False;r.reason='rollback-across-original-acquisition'
            elif control.kind=='release' and target<len(r.scopes):
                r.scopes=r.scopes[:target]
            elif control.kind not in ('rollback_to','release'):
                r.valid=False;r.reason='unknown-original-control'
