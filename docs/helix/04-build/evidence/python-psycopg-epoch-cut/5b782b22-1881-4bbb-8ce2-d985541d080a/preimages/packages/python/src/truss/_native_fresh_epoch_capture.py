"""Private original fresh-epoch response custody; never a held-cut capability.

The observed row is historical after return. Autocommit, savepoint rollback,
same-writer issuance or transaction completion can end/change its lock scope.
"""
from ._native_epoch_acquisitions import NativeFreshEpochObservation
from dataclasses import dataclass
import hashlib,re,struct
from ._native_admission_capture import NativeAdmissionCapture
from ._native_result_custody import NativeTextLimits
from ._native_pg8000 import NativeBoundaryRefusal,NativeCall,NativeEvent
from ._native_arbitration import NativeOperationSession
from ._native_driver_profile import original_control_profile
from ._native_deadline import NativeOperationDeadline

FRESH_EPOCH_LIMITS=NativeTextLimits(columns=12,rows=1,cell_bytes=2097152,
    result_bytes=2359296,frame_bytes=2621440,wire_bytes=8388608,
    sql_bytes=32768,payload_capacity=268435456,cumulative_payload=268435456)


def _literal(value,maximum):
    if type(value) is not str or not 1<=len(value)<=maximum:
        raise NativeBoundaryRefusal('Bounded exact epoch comparison text required')
    try:raw=value.encode('utf8')
    except UnicodeError as error:raise NativeBoundaryRefusal('Lossless epoch comparison required') from error
    if not 1<=len(raw)<=maximum or b'\0' in raw:
        raise NativeBoundaryRefusal('Bounded native epoch comparison required')
    return "pg_catalog.convert_from(pg_catalog.decode('"+raw.hex()+"','hex'),'UTF8')"


def _validate_epoch_row(row,expected,scope):
    if type(row) is not tuple or len(row)!=12 or any(type(v) is not str for v in row):
        raise NativeBoundaryRefusal('Exact original epoch text tuple required')
    if row[:3]!=expected or row[-1]!=scope:
        raise NativeBoundaryRefusal('Original epoch comparison/scope required')
    for value,maximum in ((row[3],131072),(row[4],2097152)):
        if not 2<=len(value)<=maximum or len(value)%2 or re.fullmatch(r'[0-9a-f]+',value) is None:
            raise NativeBoundaryRefusal('Bounded exact original epoch bytes required')
    if row[5]!=hashlib.sha256(bytes.fromhex(row[4])).hexdigest():
        raise NativeBoundaryRefusal('Original evidence digest correspondence required')
    for value,maximum in ((row[6],18446744073709551615),(row[7],4294967295),(row[8],2147483647)):
        if len(value)>20 or re.fullmatch(r'[1-9][0-9]*',value) is None or int(value)>maximum:
            raise NativeBoundaryRefusal('Exact native transaction/database/backend identity required')
    try: actors=tuple(v.encode('utf8') for v in row[9:11])
    except UnicodeError as error:raise NativeBoundaryRefusal('Lossless native actor required') from error
    if any(not 1<=len(v)<=63 or b'\0' in v for v in actors):
        raise NativeBoundaryRefusal('Bounded native actor names required')
    return row


def validate_epoch_row(row,expected):
    return _validate_epoch_row(row,expected,'transaction_source_epoch_lock_only')


def validate_fenced_epoch_row(row,expected):
    return _validate_epoch_row(row,expected,'transaction_epoch_state_fence_only')


_ROW_PROFILE=('runtime_lock_fresh_source_epoch','transaction_source_epoch_lock_only',
              'original_epoch_response_only','original_acquisition_lifecycle_only')
_FENCED_PROFILE=('runtime_lock_fenced_fresh_source_epoch','transaction_epoch_state_fence_only',
                 'original_epoch_state_fence_response_only','original_epoch_state_fence_lifecycle_only')


@dataclass(frozen=True,slots=True,eq=False)
class _EpochRequest:
    owner: object
    session: object
    profile: tuple
    expected: tuple
    sql: str


def _capture_profile(gate):
    # Concrete implementation choice, never a caller-provided authority/profile.
    if type(gate) is NativeFreshEpochCapture:return _ROW_PROFILE
    if type(gate) is NativeFencedFreshEpochCapture:return _FENCED_PROFILE
    raise NativeBoundaryRefusal('Original concrete epoch capture required')


class NativeFreshEpochCapture(NativeAdmissionCapture):
    NAMES=tuple(n.encode() for n in ('installation_id','source_epoch','target_incarnation',
        'profile_hex','evidence_hex','evidence_sha256','actual_writer_xid',
        'actual_database_oid','actual_backend_pid','original_actor','effective_actor','cut_scope'))
    def __init__(self,session,installation,epoch,incarnation):
        profile=_capture_profile(self)
        args=tuple(_literal(v,n) for v,n in zip((installation,epoch,incarnation),(1024,256,1024)))
        if type(session) is not NativeOperationSession:raise NativeBoundaryRefusal('Original epoch session required')
        b=session.boundary
        if (not any(s is session for s in b._native_arbitration_sessions)
                or b._operation is not session.token or b._operation_ledger is not session
                or b._pending_operation_ledger is not session or b._calling or b._quarantined
                or session.admission_closed or session.released or session.calls
                or session.cleanup_calls or session.result_custody is not None or session._epoch_request is not None
                or not original_control_profile(b)):
            raise NativeBoundaryRefusal('Fresh original epoch operation required')
        with b._lock:session._check_call(b,session.token)
        if session.deadline is None:
            session.deadline=NativeOperationDeadline(FRESH_EPOCH_LIMITS.ordinary_ms,FRESH_EPOCH_LIMITS.settlement_ms)
        if type(session.deadline) is not NativeOperationDeadline:raise NativeBoundaryRefusal('Original epoch deadline required')
        session.deadline.check()
        self.sql='SELECT * FROM truss.'+profile[0]+'('+','.join(args)+')'
        if len(self.sql.encode())>FRESH_EPOCH_LIMITS.sql_bytes:raise NativeBoundaryRefusal('Epoch request bound')
        self.expected=(installation,epoch,incarnation);self.started=False;self.original_observation=None;self.frames=[];self.original_acquisition=None
        self._request_profile=profile
        super().__init__(session,FRESH_EPOCH_LIMITS,maximum_context_bytes=1048576)
        request=_EpochRequest(self,session,profile,self.expected,self.sql)
        with b._lock:
            session._check_call(b,session.token)
            if session._epoch_request is not None:
                raise NativeBoundaryRefusal('One original epoch request per session required')
            self._request=request;session._epoch_request=request
    def _check_recipe(self):
        request=self._request
        if (type(request) is not _EpochRequest or request.owner is not self
                or type(self.session) is not NativeOperationSession or request.session is not self.session
                or self.session._epoch_request is not request
                or self._request_profile is not request.profile or request.profile is not _capture_profile(self)
                or type(self.sql) is not str or type(self.expected) is not tuple
                or any(type(v) is not str for v in self.expected)
                or self.sql!=request.sql or self.expected!=request.expected):
            raise NativeBoundaryRefusal('Original fixed epoch request/comparison required')
        return request
    def _validate(self,code,data,context):
        super()._validate(code,data,context)
        if self._cleanup_mode() or self.boundary._active_control is not None:return
        if context is not self.admission_context:
            raise NativeBoundaryRefusal('Original epoch context required')
        if len(self.frames)>=self.limits.messages:
            raise NativeBoundaryRefusal('Epoch frame journal bound')
        charge=2*len(data)+5
        permit=self.account.reserve(self,charge)
        self.account.allocate(self,permit,charge)
        self.account.terminate(self,permit)
        self.frames.append(NativeEvent(code,bytes(data)))
    def _publish(self,observation):self.original_observation=observation
    def capture(self):
        if self.started:raise NativeBoundaryRefusal('Retain original epoch observation; never replay')
        self.started=True
        try:
            original_request=self._check_recipe()
            self.install();rows=self.boundary.run(original_request.sql,token=self.session.token);call=self.boundary.last_call
            if (type(call) is not NativeCall or not call.capture_complete or call.driver_raised
                    or call.final_status!=b'T' or self.failed or self.response_stage!=4
                    or self.entry is None or self.entry.native_call is not call
                    or self.entry.revision!=call.revision or self.entry.cleanup is not None
                    or rows is not self.admission_context.rows
                    or call.original_control is not self.entry.lifecycle
                    or call.original_resource is not self.entry.resource
                    or call.original_cleanup is not self.entry.cleanup):
                raise NativeBoundaryRefusal('Complete original epoch call required')
            # Reserve bounded validation/copy work before temporary hex decoding
            # and retained request assembly. This is payload bookkeeping only.
            charge=6*FRESH_EPOCH_LIMITS.result_bytes+2*(len(self.sql.encode())+6)
            permit=self.account.reserve(self,charge)
            self.account.allocate(self,permit,charge)
            self.account.terminate(self,permit)
            frozen=self.transfer(rows)
            if len(frozen)!=1:raise NativeBoundaryRefusal('Single original epoch row required')
            if self._check_recipe() is not original_request:
                raise NativeBoundaryRefusal('Same original epoch request through capture required')
            row=_validate_epoch_row(frozen[0],original_request.expected,original_request.profile[1])
            barrier=self.outbound.barrier if self.outbound is not None else None
            if (barrier is None or barrier.owner is not self.outbound or barrier.call is not self.entry
                    or barrier.revision!=call.revision or not barrier.writes
                    or not any(v is barrier for v in self.outbound.barriers)
                    or any(w.call is not self.entry or not w.native_returned or not w.settled for w in barrier.writes)):
                raise NativeBoundaryRefusal('Original epoch outbound barrier required')
            request=b''.join(w.data for w in barrier.writes);payload=original_request.sql.encode()+b'\0'
            if request!=b'Q'+struct.pack('!I',len(payload)+4)+payload:
                raise NativeBoundaryRefusal('Exact original epoch request required')
            observation=NativeFreshEpochObservation(call,row,request,tuple(self.frames),scope=original_request.profile[2])
            self.boundary._transaction_tracker._epoch_acquisitions.retain(self,observation)
            self._publish(observation);return observation
        finally:
            request=self._request
            if (type(request) is _EpochRequest and type(request.session) is NativeOperationSession
                    and request.session._epoch_request is request):
                request.session.admission_closed=True
            if type(self.session) is NativeOperationSession:self.session.admission_closed=True


class NativeFencedFreshEpochCapture(NativeFreshEpochCapture):
    """Private epoch-state fence response/lifecycle; no protected-use permit.

    The original installed administrative helper/guards and ordinary executor
    qualification are separate. Any later ordinary call still invalidates the
    lifecycle record before invocation, even when native table locks remain.
    """
