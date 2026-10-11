"""Private original fresh-epoch response custody; never a held-cut capability.

The observed row is historical after return. Autocommit, savepoint rollback,
same-writer issuance or transaction completion can end/change its lock scope.
"""
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

@dataclass(frozen=True,slots=True,eq=False)
class NativeFreshEpochObservation:
    original_call: NativeCall
    original_row: tuple
    original_request: bytes
    original_frames: tuple
    scope: str='original_epoch_response_only'


def _literal(value,maximum):
    if type(value) is not str or not 1<=len(value)<=maximum:
        raise NativeBoundaryRefusal('Bounded exact epoch comparison text required')
    try:raw=value.encode('utf8')
    except UnicodeError as error:raise NativeBoundaryRefusal('Lossless epoch comparison required') from error
    if not 1<=len(raw)<=maximum or b'\0' in raw:
        raise NativeBoundaryRefusal('Bounded native epoch comparison required')
    return "pg_catalog.convert_from(pg_catalog.decode('"+raw.hex()+"','hex'),'UTF8')"


def validate_epoch_row(row,expected):
    if type(row) is not tuple or len(row)!=12 or any(type(v) is not str for v in row):
        raise NativeBoundaryRefusal('Exact original epoch text tuple required')
    if row[:3]!=expected or row[-1]!='transaction_source_epoch_lock_only':
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


class NativeFreshEpochCapture(NativeAdmissionCapture):
    NAMES=tuple(n.encode() for n in ('installation_id','source_epoch','target_incarnation',
        'profile_hex','evidence_hex','evidence_sha256','actual_writer_xid',
        'actual_database_oid','actual_backend_pid','original_actor','effective_actor','cut_scope'))
    def __init__(self,session,installation,epoch,incarnation):
        args=tuple(_literal(v,n) for v,n in zip((installation,epoch,incarnation),(1024,256,1024)))
        if type(session) is not NativeOperationSession:raise NativeBoundaryRefusal('Original epoch session required')
        b=session.boundary
        if (not any(s is session for s in b._native_arbitration_sessions)
                or b._operation is not session.token or b._operation_ledger is not session
                or b._pending_operation_ledger is not session or b._calling or b._quarantined
                or session.admission_closed or session.released or session.calls
                or session.cleanup_calls or session.result_custody is not None
                or not original_control_profile(b)):
            raise NativeBoundaryRefusal('Fresh original epoch operation required')
        with b._lock:session._check_call(b,session.token)
        if session.deadline is None:
            session.deadline=NativeOperationDeadline(FRESH_EPOCH_LIMITS.ordinary_ms,FRESH_EPOCH_LIMITS.settlement_ms)
        if type(session.deadline) is not NativeOperationDeadline:raise NativeBoundaryRefusal('Original epoch deadline required')
        session.deadline.check()
        self.sql='SELECT * FROM truss.runtime_lock_fresh_source_epoch('+','.join(args)+')'
        if len(self.sql.encode())>FRESH_EPOCH_LIMITS.sql_bytes:raise NativeBoundaryRefusal('Epoch request bound')
        self.expected=(installation,epoch,incarnation);self.started=False;self.original_observation=None;self.frames=[]
        super().__init__(session,FRESH_EPOCH_LIMITS,maximum_context_bytes=1048576)
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
            self.install();rows=self.boundary.run(self.sql,token=self.session.token);call=self.boundary.last_call
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
            row=validate_epoch_row(frozen[0],self.expected)
            barrier=self.outbound.barrier if self.outbound is not None else None
            if (barrier is None or barrier.owner is not self.outbound or barrier.call is not self.entry
                    or barrier.revision!=call.revision or not barrier.writes
                    or not any(v is barrier for v in self.outbound.barriers)
                    or any(w.call is not self.entry or not w.native_returned or not w.settled for w in barrier.writes)):
                raise NativeBoundaryRefusal('Original epoch outbound barrier required')
            request=b''.join(w.data for w in barrier.writes);payload=self.sql.encode()+b'\0'
            if request!=b'Q'+struct.pack('!I',len(payload)+4)+payload:
                raise NativeBoundaryRefusal('Exact original epoch request required')
            observation=NativeFreshEpochObservation(call,row,request,tuple(self.frames))
            self._publish(observation);return observation
        finally:self.session.admission_closed=True
