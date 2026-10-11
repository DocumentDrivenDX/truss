"""Private original-call observations; no retry, cleanup or public recovery API.

Original executor and boundary custody survives facade collection. Preallocated
fact slots preserve native outcomes if snapshot projection/publication fails.
Count limits do not establish a total Python heap bound.
"""
from dataclasses import dataclass
from threading import Lock
from .execution import Ok, Error, ExecutionFailure

class _CallReference:
    def __init__(self,issuer,ordinal):
        self._issuer,self._ordinal=issuer,ordinal

@dataclass(frozen=True)
class CallOutcome:
    status: str
    kind: str | None = None
    code: str | None = None
    retry_scope: str | None = None
    sql_state: str | None = None
    settlement: str | None = None
    handback: str | None = None

@dataclass(frozen=True)
class CallObservation:
    kind: str
    phase: str
    custody: str
    outcome: CallOutcome | None = None
    native_complete: bool | None = None
    native_revision: int | None = None

@dataclass(eq=False)
class _Facts:
    phase: str = 'prepared'
    acquired: bool = False
    result: object = None
    settlement: str | None = None
    sql_state: str | None = None
    native_complete: bool | None = None
    native_revision: int | None = None
    release: object = None

@dataclass(eq=False)
class _Entry:
    owner: object
    reference: object
    boundary: object
    record: object
    slots: tuple
    published: object
    frozen: object
    next_slot: int = 1

_RESULT_KINDS={'adopt':'transaction_adopted','savepoint':'savepoint_created','host_baseline':'resource_baseline'}

class HostCallRecovery:
    def __init__(self,executor,*,retained_calls=4096):
        if type(retained_calls) is not int or not 1<=retained_calls<=4096:
            raise ValueError('Bounded original call retention required')
        self._executor=executor
        self._issuer=object()
        self._limit=retained_calls
        self._entries=()
        self._lock=Lock()
        self._errors={code:Error(ExecutionFailure(code,'Original host call observation unavailable'))
            for code in ('execution_obligation','invalid_transaction')}

    def reserve(self,boundary,record):
        if not self._lock.acquire(blocking=False):return self._errors['execution_obligation']
        try:
            with boundary._lock, self._executor._lifecycle_lock:
                if self._executor._closed and record.kind not in ('begin','commit','rollback'):
                    return self._errors['invalid_transaction']
                if len(self._entries)>=self._limit or len(boundary._host_call_records)>=4096:
                    return self._errors['execution_obligation']
                reference=_CallReference(self._issuer,len(self._entries)+1)
                slots=tuple(_Facts() for _ in range(9))
                entry=_Entry(self,reference,boundary,record,slots,slots[0],slots[0])
                retained=(*self._entries,entry)
                native_retained=(*boundary._host_call_records,entry)
                # Both owners retain every preallocated fact slot before acquisition.
                self._entries=retained
                boundary._host_call_records=native_retained
                record.recovery_entry=entry
                return Ok(reference)
        finally:self._lock.release()

    def freeze(self,record,phase):
        entry=record.recovery_entry
        if entry is None:return
        with self._lock:
            if type(entry) is not _Entry or entry.owner is not self or entry.record is not record:
                raise RuntimeError('Original retained call required')
            if entry.next_slot>=len(entry.slots):
                raise RuntimeError('Original fact reservation exhausted')
            facts=entry.slots[entry.next_slot]
            entry.next_slot+=1
            facts.phase=phase
            facts.acquired=record.acquired
            facts.result=record.result
            facts.release=record.release
            native=record.original if record.original is not record.before else None
            if native is not None:
                facts.native_complete=native.capture_complete
                facts.native_revision=native.revision
            if type(record.result) is Ok and type(record.result.value) is record.control_type:
                facts.settlement=record.result.value.state
                facts.sql_state=record.result.value.evidence.sql_state
            # No summary/snapshot construction after native effects. Inspection
            # projects this sealed slot; failed publication cannot erase it.
            entry.frozen=facts

    def publish(self,record,phase):
        self.freeze(record,phase)
        entry=record.recovery_entry
        if entry is not None:
            with self._lock:self._publish_snapshot(entry,entry.frozen)

    @staticmethod
    def _publish_snapshot(entry,facts):entry.published=facts

    def references(self,boundary):
        with self._lock:return tuple(e.reference for e in self._entries if e.boundary is boundary)

    def observe(self,reference):
        if type(reference) is not _CallReference or reference._issuer is not self._issuer:
            return self._errors['invalid_transaction']
        if not self._lock.acquire(blocking=False):return self._errors['execution_obligation']
        boundary=None
        try:
            entry=next((e for e in self._entries if e.reference is reference),None)
            if entry is None:return self._errors['invalid_transaction']
            boundary=entry.boundary
            if not boundary._lock.acquire(blocking=False):
                boundary=None
                return self._errors['execution_obligation']
            facts=entry.frozen
            # The same original boundary lock synchronizes this historical receipt.
            released=facts.release is not None and facts.release.published
            phase='settled' if released else facts.phase
            custody='released' if released else 'unresolved' if phase=='acquiring' else 'not_acquired' if not facts.acquired else 'held' if phase=='in_flight' else 'unresolved'
            result=facts.result
            outcome=None
            if type(result) is Error:
                failure=result.error
                outcome=CallOutcome('error',code=failure.code,retry_scope=failure.retry_scope,sql_state=failure.sql_state)
            elif type(result) is Ok:
                outcome=CallOutcome('ok','host_control' if facts.settlement is not None else _RESULT_KINDS.get(entry.record.kind,'completed'),
                    sql_state=facts.sql_state,settlement=facts.settlement,
                    handback=('released' if released else 'unresolved') if facts.settlement is not None else None)
            return Ok(CallObservation(entry.record.kind,phase,custody,outcome,facts.native_complete,facts.native_revision))
        except Exception:
            # Failed diagnostic allocation/projection changes no native facts.
            return self._errors['execution_obligation']
        finally:
            if boundary is not None:boundary._lock.release()
            self._lock.release()
