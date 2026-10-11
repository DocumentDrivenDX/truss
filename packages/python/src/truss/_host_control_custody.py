"""Private original simple-query control ledger; no public adoption claim.

Explicit host baseline observation may retire prior unnamed resources. Subsequent
host SQL is cooperative resource-free work; opaque resource-producing functions,
untracked raw aliases and arbitrary server-side prepared/cursor creation are not
qualified. Accounting covers controlled frame/decode payloads, not total heap.
"""
from dataclasses import dataclass, replace
from threading import Lock
from ._native_pg8000 import NativeBoundaryRefusal
from ._native_transactions import _Control
from ._native_result_custody import NativeResultCustody, NativeTextLimits
from ._native_driver_profile import original_control_profile
from .execution import Ok, Error, ExecutionFailure
from ._native_ingress_deadline import original_ingress_profile
from ._native_outbound import admitted_outbound_basis, ControlOutboundWitness

BASELINE_SQL = "SELECT (SELECT pg_catalog.count(*) FROM pg_catalog.pg_prepared_statements)::pg_catalog.text, (SELECT pg_catalog.count(*) FROM pg_catalog.pg_cursors WHERE name OPERATOR(pg_catalog.<>) ''::pg_catalog.text)::pg_catalog.text"
PROFILE_SQL = "SELECT pg_catalog.current_setting('transaction_isolation'), pg_catalog.current_setting('transaction_read_only'), session_user::pg_catalog.text, current_user::pg_catalog.text, pg_catalog.pg_current_xact_id_if_assigned()::pg_catalog.text"

@dataclass(eq=False)
class _Entry:
    revision: int
    resource: object
    lifecycle: object
    cleanup: object = None
    native_call: object = None
    context: object = None
    columns: int = 0
    rows: int = 0
    descriptions: int = 0
    commands: int = 0
    errors: int = 0
    terminal: bool = False
    sql: str | None = None

@dataclass(frozen=True,eq=False)
class _Baseline:
    producer: object
    boundary: object
    record: object
    call: object
    counts: tuple

@dataclass(frozen=True,eq=False)
class _Completion:
    producer: object
    ledger: object
    calls: tuple
    generation: object
    savepoints: tuple
    publication: object
    deadline_basis: tuple

class _ControlGate(NativeResultCustody):
    def _messages(self,context):
        entry=self.session.calls[-1]
        if (entry.context is not context or context.stream is not None
                or not any(c is context for c in self.contexts[:self.context_count])):
            self.failed=True;self.boundary._quarantined=True
            raise NativeBoundaryRefusal('Original preregistered control Context required')
        return self.original_handle_messages(context)

    def _control_tags(self,control):
        if type(control) is not _Control or control.chain:return ()
        return {'begin':(b'BEGIN',),'commit':(b'COMMIT',b'ROLLBACK'),
            'rollback':(b'ROLLBACK',),'savepoint':(b'SAVEPOINT',),
            'rollback_to':(b'ROLLBACK',),'release':(b'RELEASE',)}.get(control.kind,())

    def _command_pattern(self,command):
        return {'SHOW':rb'SHOW','SELECT':rb'SELECT 1'}.get(command)

    def _validate(self,code,data,context):
        entry=self.session.calls[-1]
        if entry.context is not context:
            raise NativeBoundaryRefusal('Foreign native control Context')
        if code not in (b'T',b'D',b'C',b'E',b'Z',b'N',b'S',b'A'):
            raise NativeBoundaryRefusal('Foreign response outside simple-query grammar')
        if entry.terminal and code not in (b'Z',b'N',b'S',b'A'):
            raise NativeBoundaryRefusal('Response after original terminal control message')
        if code==b'T':
            if entry.descriptions or entry.columns==0 or len(data)<2 or int.from_bytes(data[:2],'big')!=entry.columns:
                raise NativeBoundaryRefusal('Exact original control column shape required')
            entry.descriptions+=1
        elif code==b'D':
            if entry.descriptions!=1 or entry.columns==0 or entry.rows>=1 or len(data)<2 or int.from_bytes(data[:2],'big')!=entry.columns:
                raise NativeBoundaryRefusal('Exact original control row shape required')
            entry.rows+=1
        elif code==b'C':
            entry.commands+=1
            if entry.commands!=1 or entry.errors or entry.rows!=(1 if entry.columns else 0) or entry.descriptions!=(1 if entry.columns else 0):
                raise NativeBoundaryRefusal('Exact original control result count required')
            entry.terminal=True
        elif code==b'E':
            entry.errors+=1
            if entry.commands or entry.errors!=1:
                raise NativeBoundaryRefusal('Duplicate original terminal control message')
            entry.terminal=True
        elif code==b'Z' and not entry.terminal:
            raise NativeBoundaryRefusal('Original terminal control message absent')
        return super()._validate(code,data,context)

@dataclass(eq=False)
class _Ledger:
    producer: object
    boundary: object
    record: object
    original_root: object
    attached_root: object = None
    calls: tuple = ()
    cleanup_calls: tuple = ()
    result_custody: object = None
    admission_closed: bool = False
    completion: object = None
    baseline: object = None
    publication_start: int = 0
    deadline: object = None

    @property
    def token(self):return self.record.token

    def _check_call(self,boundary,token,cleanup=None,*,admission=True):
        if (boundary is not self.boundary or token is not self.token
                or boundary._ownership is not self.attached_root or self.admission_closed
                or cleanup is not None or len(self.calls)>=8):
            raise NativeBoundaryRefusal('Original control call admission unavailable')
        if admission:self.deadline.check()

    def _reserve_call(self,boundary,token,resource,lifecycle,cleanup=None):
        self._check_call(boundary,token,cleanup,admission=False)
        if resource is not None or lifecycle is not None and (type(lifecycle) is not _Control or lifecycle.chain):
            raise NativeBoundaryRefusal('Selected simple-query control required')
        entry=_Entry(boundary._revision+1,resource,lifecycle)
        self.calls=(*self.calls,entry)
        return entry

    def simple_query(self,sql):
        from pg8000.core import Context, _flush
        entry=self.calls[-1]
        if entry.native_call is not None or entry.context is not None or not self.boundary._calling:
            raise NativeBoundaryRefusal('Original reserved control call required')
        if entry.lifecycle is None:
            entry.columns=2 if sql==BASELINE_SQL and self.record.kind=='host_baseline' else 5 if sql==PROFILE_SQL else 1 if sql in ('SHOW transaction_isolation','SHOW transaction_read_only') else 0
            if entry.columns==0:raise NativeBoundaryRefusal('Fixed original control observation required')
            self.result_custody.expected_command='SHOW' if sql.startswith('SHOW ') else 'SELECT'
        entry.sql=sql
        context=Context(sql)
        entry.context=context
        gate=self.result_custody
        if gate.context_count>=len(gate.contexts):
            raise NativeBoundaryRefusal('Reserved control Context capacity exhausted')
        gate.contexts[gate.context_count]=context;gate.context_count+=1
        con=self.boundary._connection
        # Original Context is retained before send/flush, including a failed send.
        con.send_QUERY(sql);_flush(con._sock);con.handle_messages(context)
        con._context=context
        return context.rows

class HostControlCustody:
    def __init__(self,executor,*,limits=None,retained_ledgers=4096):
        from ._host_execution import HostExecutor
        if type(executor) is not HostExecutor:raise ValueError('Original executor required')
        self.executor=executor
        self.limits=limits or NativeTextLimits(contexts=8,rows=8,columns=5)
        if type(self.limits) is not NativeTextLimits or self.limits.contexts<8:
            raise ValueError('Eight reserved original Context slots required')
        if type(retained_ledgers) is not int or not 1<=retained_ledgers<=4096:
            raise ValueError('Bounded retained ledger capacity required')
        self._limit=retained_ledgers
        self._lock=Lock()
        self._ledgers=()
        with executor._lifecycle_lock:
            if executor._host_control_producer is not None:
                raise ValueError('One original control producer per executor required')
            executor._host_control_producer=self

    def preflight(self,boundary,kind):
        if (not original_control_profile(boundary) or not original_ingress_profile(boundary)
                or not admitted_outbound_basis(boundary)):return False
        with boundary._lock:
            if len(self._ledgers)>=self._limit or len(boundary._host_control_records)>=4096 or boundary._host_control_pending is not None:return False
            if kind=='host_baseline':return boundary._transaction_tracker._state.generation is None and boundary._connection._transaction_status==b'I'
            return selected_resource_entry(boundary)

    def attach(self,boundary,record):
        if not self._lock.acquire(blocking=False):return None
        try:return self._attach_reserved(boundary,record)
        finally:self._lock.release()

    def _attach_reserved(self,boundary,record):
        with boundary._lock:
            if len(self._ledgers)>=self._limit or len(boundary._host_control_records)>=4096:
                return None
            if (boundary._operation is not record.token or boundary._ownership is not record.release.before
                    or boundary._operation_ledger is not None or boundary._pending_operation_ledger is not None):
                raise NativeBoundaryRefusal('Original control scope changed')
            ledger=_Ledger(self,boundary,record,record.release.before,
                           publication_start=len(self.executor._savepoint_publications),deadline=record.deadline)
            ledger.attached_root=replace(ledger.original_root,ledger=ledger,pending=ledger)
            gate=_ControlGate(ledger,self.limits)
            ledger.result_custody=gate
            self._ledgers=(*self._ledgers,ledger)
            boundary._host_control_records=(*boundary._host_control_records,ledger)
            record.control_ledger=ledger
            boundary._host_control_pending=ledger
            boundary._publish_ownership(ledger.attached_root)
        gate.install()
        return ledger

    def observe_baseline(self,boundary,record):
        ledger=record.control_ledger
        rows=boundary._call(lambda:boundary._run_simple(BASELINE_SQL),record.token)
        if rows!=[['0','0']]:
            return Error(ExecutionFailure('invalid_transaction','Host named resources remain outside selected baseline'))
        baseline=_Baseline(self,boundary,record,boundary.last_call,('0','0'))
        ledger.baseline=baseline
        return Ok(baseline)

    def handback(self,ledger):
        b=ledger.boundary
        with b._lock:
            if (ledger.producer is not self or b._ownership is not ledger.attached_root
                    or b._calling or b._quarantined
                    or not ledger.calls and b.last_call is not ledger.record.before
                    or any(e.native_call is None or not e.native_call.capture_complete
                        or e.native_call.revision!=e.revision or e.native_call.original_control is not e.lifecycle
                        or e.native_call.original_resource is not None or e.context is None for e in ledger.calls)):
                raise NativeBoundaryRefusal('Original complete control custody required')
            publications=tuple(p for p in self.executor._savepoint_publications[ledger.publication_start:]
                if getattr(getattr(self.executor._original_custody(p.transaction).port,'_tracker',None),'_boundary',None) is b)
            if any(p.phase!='published' for p in publications):
                raise NativeBoundaryRefusal('Original executor publication unresolved')
            state=b._transaction_tracker._state
            completion=_Completion(self,ledger,ledger.calls,state.generation,state.savepoints,publications,ledger.deadline.seal())
            witness=ControlOutboundWitness(ledger,completion)
            ledger.admission_closed=True
        ledger.result_custody.detach()
        if not original_control_profile(b):raise NativeBoundaryRefusal('Original detached profile changed')
        with b._lock:
            if b._ownership is not ledger.attached_root:raise NativeBoundaryRefusal('Original control root changed')
            ledger.deadline.check()
            ledger.completion=completion
            b._publish_ownership(ledger.original_root)
            # Simple-query Ready confirms this scope's unnamed retirement. The
            # baseline is host-requested inventory, never an implicit repair.
            b._unnamed_pending=False
            if ledger.record.kind=='host_baseline':b._resource_baseline=ledger.baseline
            if ledger.calls:b._control_outbound_witness=witness
            b._release_operation_locked(ledger.token,original_release=ledger.record.release,original_control=completion)
        return completion


def selected_resource_entry(boundary):
    baseline=boundary._resource_baseline
    return (type(baseline) is _Baseline and baseline.boundary is boundary
            and baseline.counts==('0','0') and baseline.record.release.published
            and baseline.record.control_ledger.baseline is baseline
            and not boundary._unnamed_pending)
