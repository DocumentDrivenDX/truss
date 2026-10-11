"""Private cooperative automatic-call scope; not public C02 qualification.

Native generation/adoption custody stays authoritative. The shared arbitration
service is retained for eventual assembled operations; these control calls do
not fabricate leases or completion artifacts. Caller owns settlement/connection.
"""
from dataclasses import dataclass
from threading import Lock
from ._host_execution import HostExecutor
from ._native_transactions import NativeTransactions, NativeTransactionPort, _Control
from ._native_arbitration import NativeArbitration
from ._native_pg8000 import NativeBoundaryRefusal
from .execution import Ok, Error, ExecutionFailure

@dataclass(eq=False)
class _ControlEvidence:
    sql_state: str | None = None

@dataclass(frozen=True)
class HostControlResult:
    state: str
    evidence: _ControlEvidence
    handback: str = 'released'

    @property
    def sql_state(self):
        return self.evidence.sql_state

_CONTROL_RESULT_TYPE=HostControlResult

@dataclass(eq=False)
class _Call:
    kind: str
    token: object = None
    before: object = None
    generation: object = None
    original: object = None
    result: object = None
    release: object = None
    original_frozen: bool = False
    port_control: object = None
    settlements: object = None
    evidence: object = None
    control_ledger: object = None
    phase: str = 'reserved'
    recovery_entry: object = None
    acquired: bool = False
    control_type: object = None
    failures: object = None

class NativeHostSession:
    def __init__(self, executor, tracker, service, *, retained_calls=4096, control_producer=None):
        if (type(executor) is not HostExecutor or type(tracker) is not NativeTransactions
            or type(service) is not NativeArbitration or service._executor is not executor
            or executor._arbitration_service is not service.registry
            or type(retained_calls) is not int or not 1<=retained_calls<=4096):
            raise ValueError('Original shared native host composition required')
        from ._host_control_custody import HostControlCustody
        if control_producer is not None and (type(control_producer) is not HostControlCustody or control_producer.executor is not executor):
            raise ValueError('Original control producer required')
        self._control_producer=control_producer
        self.executor,self.tracker,self.service=executor,tracker,service
        self._boundary=tracker._boundary
        self._limit=retained_calls
        self._calls=()
        self._lock=Lock()
        self._closed=False

    @staticmethod
    def _error(code):
        return Error(ExecutionFailure(code,'Original host call unavailable'))

    @property
    def recovery(self):return self.executor._host_call_recovery

    @property
    def last_call_reference(self):
        if not self._calls or self._calls[-1].recovery_entry is None:return None
        return self._calls[-1].recovery_entry.reference

    def _freeze(self,record,phase):
        self.recovery.freeze(record,phase)

    def _finish(self,record,phase,result):
        record.result=result
        record.phase=phase
        self.recovery.publish(record,phase)
        return result

    def _invoke(self,kind,callback,*,port=None):
        # Cooperative serialized handback; busy never waits or retries.
        if not self._lock.acquire(blocking=False): return self._error('execution_obligation')
        record=None
        try:
            if self._closed: return self._error('transaction_unusable')
            if len(self._calls)>=self._limit: return self._error('execution_obligation')
            with self.executor._lifecycle_lock:
                if self.executor._closed and kind not in ('begin','commit','rollback'):
                    return self._error('invalid_transaction')
            record=_Call(kind,token=object(),control_type=_CONTROL_RESULT_TYPE)
            record.failures={code:self._error(code) for code in ('transaction_unusable','execution_obligation','commit_unknown')}
            record.before=self._boundary.last_call
            if kind in ('begin','commit','rollback'):
                record.evidence=_ControlEvidence()
                record.settlements={state:(Ok(HostControlResult(state,record.evidence)),Ok(HostControlResult(state,record.evidence,'quarantined')))
                                    for state in ('active','committed','rolled_back','commit_failed')}
            self._calls=(*self._calls,record)
            reserved=self.recovery.reserve(self._boundary,record)
            if type(reserved) is Error:
                self._calls=self._calls[:-1]
                return reserved
            try:
                self.recovery.publish(record,'acquiring')
                self._boundary.acquire_operation(original_token=record.token)
                record.acquired=True
                self.recovery.publish(record,'in_flight')
            except BaseException as error:
                if self._boundary._operation is record.token:
                    record.acquired=True
                    record.phase='unresolved';self._closed=True
                    result=self._finish(record,'unresolved',record.failures['transaction_unusable'])
                    if not isinstance(error,Exception): raise
                    return result
                result=self._finish(record,'refused',record.failures['execution_obligation'])
                if not isinstance(error,Exception): raise
                return result
            record.before=self._boundary.last_call
            record.generation=self.tracker._state.generation
            try:
                record.release=self._boundary.reserve_operation_release(record.token)
                if self._control_producer is not None:
                    if not self._control_producer.preflight(self._boundary,kind):
                        record.result=self._error('execution_obligation')
                        record.original=record.before
                        record.original_frozen=True
                        self._freeze(record,'refused')
                        self._boundary.release_operation(record.token,original_release=record.release)
                        return self._finish(record,'refused',record.result)
                    if self._control_producer.attach(self._boundary,record) is None:
                        record.result=self._error('execution_obligation')
                        record.original=record.before
                        record.original_frozen=True
                        self._freeze(record,'refused')
                        self._boundary.release_operation(record.token,original_release=record.release)
                        return self._finish(record,'refused',record.result)
                record.result=callback(record.token,record)
                record.original=self._boundary.last_call
                record.original_frozen=True
                record.port_control=port._last_control if port is not None else None
                if port is not None and (port._pending_savepoint is not None or record.port_control is not None and record.port_control.phase!='published'):
                    raise NativeBoundaryRefusal('Original port publication unresolved')
                if (type(record.result) is Error and record.result.error.code=='transaction_unusable'):
                    raise NativeBoundaryRefusal('Original Python publication unresolved')
                if (self._boundary._quarantined or self._boundary._calling
                    or record.token is not self._boundary._operation):
                    raise NativeBoundaryRefusal('Original native scope unsettled')
                self._freeze(record,'in_flight')
                if self._control_producer is None:
                    self._boundary.release_operation(record.token,original_release=record.release)
                else:
                    self._control_producer.handback(record.control_ledger)
                return self._finish(record,'settled',record.result)
            except BaseException as error:
                if not record.original_frozen:
                    record.original=self._boundary.last_call
                    record.port_control=port._last_control if port is not None else None
                # A lost release reply can reconcile only the exact known handback.
                if record.release is not None and record.release.published and record.result is not None:
                    self._finish(record,'settled',record.result)
                    if not isinstance(error,Exception): raise
                    return record.result
                record.phase='unresolved'
                if record.control_ledger is not None:record.control_ledger.admission_closed=True
                self._closed=True
                # Never release original token after an unknown Python/native window.
                known=None
                if type(record.result) is Ok and type(record.result.value) is _CONTROL_RESULT_TYPE:
                    known=record.result.value.state
                elif record.settlements is not None and record.original is not record.before :
                    call=record.original
                    control=call.original_control
                    tags=tuple(e.payload for e in call.events if e.code==b'C')
                    acknowledged=(record.control_ledger is None or record.control_ledger.calls[-1].commands==1)
                    if (type(control) is _Control and control.kind==kind
                        and control.expected.generation is record.generation and control.chain is False):
                        if acknowledged and kind=='commit' and tags==(b'COMMIT\0',): known='committed'
                        elif acknowledged and kind in ('commit','rollback') and tags==(b'ROLLBACK\0',): known='rolled_back'
                        elif call.capture_complete and kind=='commit' and call.final_status==b'I' and any(e.code==b'E' for e in call.events): known='rolled_back'
                        elif call.capture_complete and kind=='commit' and call.final_status in (b'T',b'E') and any(e.code==b'E' for e in call.events): known='commit_failed'
                if known is not None:
                    result=self._finish(record,'unresolved',record.settlements[known][1])
                    if not isinstance(error,Exception): raise
                    return result
                submitted=record.original is not record.before
                known_end=(submitted and record.original.capture_complete and record.original.final_status==b'I'
                           and any(e.code in (b'C',b'E') for e in record.original.events))
                result=self._finish(record,'unresolved',record.failures['commit_unknown' if kind=='commit' and submitted and not known_end else 'transaction_unusable'])
                if not isinstance(error,Exception): raise
                return result
        except BaseException:
            if record is not None and record.token is self._boundary._operation:
                record.phase='unresolved';self._closed=True
            raise
        finally:
            self._lock.release()

    def _control(self,kind,token,record,**options):
        before=self._boundary.last_call
        try:
            getattr(self.tracker,kind)(token=token,**options)
        except Exception:
            call=self._boundary.last_call
            if call is before:
                return self._error('invalid_transaction')
            if not call.capture_complete or call.final_status not in (b'I',b'T',b'E'):
                raise
            tags=tuple(e.payload.rstrip(b'\0') for e in call.events if e.code==b'C')
            if kind=='commit' and call.final_status==b'I' and tags in ((b'COMMIT',),(b'ROLLBACK',)):
                return self._settlement_result(record,'committed' if tags==(b'COMMIT',) else 'rolled_back')
            state=next((f[1:].decode('ascii') for e in call.events if e.code==b'E'
                        for f in e.payload.split(b'\0') if f[:1]==b'C'),None)
            record.evidence.sql_state=state
            if kind=='commit' and call.final_status==b'I' and state is not None:
                return self._settlement_result(record,'rolled_back')
            if kind=='commit' and call.final_status in (b'T',b'E') and state is not None and call.original_control is not None and call.original_control.kind=='commit':
                return self._settlement_result(record,'commit_failed')
            raise
        call=self._boundary.last_call
        if call is before or not call.capture_complete: raise NativeBoundaryRefusal('Original control completion absent')
        tags=tuple(e.payload.rstrip(b'\0') for e in call.events if e.code==b'C')
        if kind=='begin' and tags==(b'BEGIN',) and call.final_status==b'T':
            return self._settlement_result(record,'active')
        if kind=='commit' and tags==(b'COMMIT',) and call.final_status==b'I':
            return self._settlement_result(record,'committed')
        if kind in ('commit','rollback') and tags==(b'ROLLBACK',) and call.final_status==b'I':
            return self._settlement_result(record,'rolled_back')
        raise NativeBoundaryRefusal('Original control meaning unresolved')

    @staticmethod
    def _settlement_result(record,state):
        return record.settlements[state][0]

    def observe_host_resource_baseline(self):
        # Explicit host-owned idle observation, never implicit adoption repair.
        if self._control_producer is None:return self._error('execution_obligation')
        return self._invoke('host_baseline',lambda token,record:
            self._control_producer.observe_baseline(self._boundary,record))

    def begin(self,*,isolation='read_committed',access_mode='read_write'):
        if type(isolation) is not str or type(access_mode) is not str:
            return self._error('invalid_transaction')
        return self._invoke('begin',lambda token,record:self._control('begin',token,record,isolation=isolation,access_mode=access_mode))

    def commit(self):
        return self._invoke('commit',lambda token,record:self._control('commit',token,record))

    def rollback(self):
        return self._invoke('rollback',lambda token,record:self._control('rollback',token,record))

    def adopt_transaction(self,*,isolation='read_committed',access_mode='read_write'):
        if type(isolation) is not str or type(access_mode) is not str:
            return self._error('invalid_transaction')
        def adopt(token,record):
            if self.tracker._state.generation is None: return self._error('invalid_transaction')
            return self.executor.adopt_transaction(self.tracker.port(token),isolation=isolation,access_mode=access_mode)
        return self._invoke('adopt',adopt)

    def _transaction_call(self,kind,transaction,savepoint=None):
        custody=self.executor._original_custody(transaction)
        if custody is None or type(custody.port) is not NativeTransactionPort or custody.port._tracker is not self.tracker:
            return self._error('invalid_transaction')
        def invoke(token,record):
            custody.port.bind_operation(token)
            method=getattr(self.executor,kind)
            return method(transaction) if kind=='savepoint' else method(transaction,savepoint)
        return self._invoke(kind,invoke,port=custody.port)

    def savepoint(self,transaction):
        return self._transaction_call('savepoint',transaction)

    def rollback_to_savepoint(self,transaction,savepoint):
        return self._transaction_call('rollback_to_savepoint',transaction,savepoint)

    def release_savepoint(self,transaction,savepoint):
        return self._transaction_call('release_savepoint',transaction,savepoint)

    def dispose(self):
        # Closes executor admission, never commits/rolls back/closes caller resources.
        self.executor.dispose()
