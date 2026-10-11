"""Private original-census response custody, not provider/authority admission.

Cooperative host and exact pg8000 driver ownership remain premises. This capture
uses one materialized observation; it does not establish the application cut.
"""
from dataclasses import dataclass
import hashlib
import re
import struct
from ._native_pg8000 import NativeBoundaryRefusal, NativeCall, NativeEvent
from ._native_arbitration import NativeOperationSession
from ._native_result_custody import NativeResultCustody, NativeTextLimits
from ._native_driver_profile import original_control_profile
from ._native_deadline import NativeOperationDeadline

MAXIMUM_IMAGE=16777216
CHUNK_BYTES=4096
SOURCE_SHA256='9c805b87f4eb631cbfa250d877e826484e5797795b5ae824b3a4b2cade524bfb'
# Separate explicit observer profile, never the ordinary/default text profile.
# Conservative retained payload charges are not measurements of the whole heap.
CENSUS_LIMITS=NativeTextLimits(columns=3,rows=4096,cell_bytes=8192,
    result_bytes=41943040,wire_bytes=41943040,messages=8192,reads=32768,
    sql_bytes=32768,payload_capacity=1073741824,
    cumulative_payload=1073741824,account_records=131072)
NAMES=(b'ordinal',b'total_bytes',b'chunk_hex')

@dataclass(frozen=True,slots=True,eq=False)
class NativeSourceCensusObservation:
    original_call: NativeCall
    original_image: bytes
    original_request: bytes
    original_frames: tuple
    scope: str='native_response_only'

class NativeSourceCensusCapture(NativeResultCustody):
    def __init__(self,session,source_sql):
        if (type(session) is not NativeOperationSession or type(source_sql) is not str
                or len(source_sql)>CENSUS_LIMITS.sql_bytes
                or hashlib.sha256(source_sql.encode()).hexdigest()!=SOURCE_SHA256):
            raise NativeBoundaryRefusal('Original selected census source/session required')
        b=session.boundary
        if (not any(s is session for s in b._native_arbitration_sessions)
                or b._operation is not session.token or b._operation_ledger is not session
                or b._pending_operation_ledger is not session or b._calling
                or b._quarantined or session.admission_closed or session.released
                or session.calls or session.cleanup_calls or session.result_custody is not None
                or not original_control_profile(b)):
            raise NativeBoundaryRefusal('Fresh original census operation required')
        with b._lock:
            session._check_call(b,session.token)
        if session.deadline is None:
            session.deadline=NativeOperationDeadline(CENSUS_LIMITS.ordinary_ms,CENSUS_LIMITS.settlement_ms)
        if type(session.deadline) is not NativeOperationDeadline:
            raise NativeBoundaryRefusal('Original deadline required')
        session.deadline.check()
        source=source_sql.strip().removesuffix(';')
        self.sql=("WITH image AS MATERIALIZED (SELECT pg_catalog.convert_to(census,'UTF8') AS body FROM ("+source+") AS native_census) "
            "SELECT part::pg_catalog.text AS ordinal,pg_catalog.octet_length(body)::pg_catalog.text AS total_bytes,"
            "pg_catalog.encode(pg_catalog.substring(body,part*4096+1,4096),'hex') AS chunk_hex "
            "FROM image LEFT JOIN LATERAL pg_catalog.generate_series(0,(pg_catalog.octet_length(body)-1)/4096) AS part ON true ORDER BY part")
        if len(self.sql.encode())>CENSUS_LIMITS.sql_bytes:
            raise NativeBoundaryRefusal('Census SQL bound')
        self.stage=0;self.chunk_count=0;self.image=None;self.offset=0
        self.unavailable=False;self.frames=[];self.census_context=None;self.entry=None
        self.original_observation=None;self.started=False
        super().__init__(session,CENSUS_LIMITS)
        self.expected_command='SELECT'

    def _messages(self,context):
        if not self._cleanup_mode() and self.boundary._active_control is None:
            if self.census_context is not None:
                raise NativeBoundaryRefusal('One original census response required')
            self.entry=self.session.calls[-1]
            self.census_context=context
        return super()._messages(context)

    def _charge(self,amount):
        permit=self.account.reserve(self,amount)
        self.account.allocate(self,permit,amount)
        self.account.terminate(self,permit)

    def _validate(self,code,data,context):
        super()._validate(code,data,context)
        if self._cleanup_mode() or self.boundary._active_control is not None:return
        if context is not self.census_context:
            raise NativeBoundaryRefusal('Original census context required')
        if len(self.frames)>=CENSUS_LIMITS.messages:
            raise NativeBoundaryRefusal('Census frame bound')
        self._charge(2*len(data)+5)
        self.frames.append(NativeEvent(code,bytes(data)))
        if code==b'T':
            if self.stage!=0 or struct.unpack_from('!H',data)[0]!=3:
                raise NativeBoundaryRefusal('Single exact census descriptor required')
            offset=2
            for name in NAMES:
                end=data.find(b'\0',offset)
                fields=struct.unpack_from('!IhIhih',data,end+1)
                if data[offset:end]!=name or fields[3:5]!=(-1,-1):raise NativeBoundaryRefusal('Ordered census columns required')
                offset=end+19
            self.stage=1
        elif code==b'D':
            if self.stage!=1 or struct.unpack_from('!H',data)[0]!=3 or self.unavailable:
                raise NativeBoundaryRefusal('Ordered census rows required')
            offset=2;cells=[]
            for _ in NAMES:
                size=struct.unpack_from('!i',data,offset)[0];offset+=4
                cells.append(None if size==-1 else data[offset:offset+size]);offset+=max(0,size)
            if cells==[None,None,None] and self.chunk_count==0:
                self.unavailable=True;return
            ordinal,total,encoded=cells
            if (ordinal!=str(self.chunk_count).encode() or type(total) is not bytes
                    or re.fullmatch(rb'[1-9][0-9]{0,7}',total) is None
                    or not 1<=int(total)<=MAXIMUM_IMAGE):
                raise NativeBoundaryRefusal('Contiguous bounded census chunks required')
            size=int(total)
            if (type(encoded) is not bytes or re.fullmatch(rb'(?:[0-9a-f]{2})+',encoded) is None
                    or len(encoded)!=2*min(CHUNK_BYTES,size-self.offset)):
                raise NativeBoundaryRefusal('Exact native chunk width required')
            if self.image is None:
                # Buffer + immutable original publication + conservative UTF8 work.
                self._charge(6*size);self.image=bytearray(size)
            if len(self.image)!=size or self.offset>=size:
                raise NativeBoundaryRefusal('Consistent complete census size required')
            chunk=bytes.fromhex(encoded.decode('ascii'))
            self.image[self.offset:self.offset+len(chunk)]=chunk
            self.offset+=len(chunk);self.chunk_count+=1
        elif code==b'C':
            expected=1 if self.unavailable else self.chunk_count
            if self.stage!=1 or expected==0 or data!=b'SELECT '+str(expected).encode()+b'\0':
                raise NativeBoundaryRefusal('Complete original census count required')
            if not self.unavailable and (self.image is None or self.offset!=len(self.image)):
                raise NativeBoundaryRefusal('No census prefix publication')
            self.stage=2
        elif code==b'Z':
            if self.stage!=2 or data!=b'T':raise NativeBoundaryRefusal('Original active census completion required')
            self.stage=3
        else:
            raise NativeBoundaryRefusal('Closed census response inventory required')

    def _publish(self,observation):
        self.original_observation=observation

    def capture(self):
        if self.started:raise NativeBoundaryRefusal('Observe retained census; never replay')
        self.started=True
        try:
            self.install()
            rows=self.boundary.run(self.sql,token=self.session.token)
            call=self.boundary.last_call
            if (type(call) is not NativeCall or not call.capture_complete or call.driver_raised
                    or call.final_status!=b'T' or self.stage!=3 or self.failed
                    or self.entry is None or self.entry.native_call is not call
                    or self.entry.revision!=call.revision or self.entry.cleanup is not None
                    or rows is not self.census_context.rows
                    or not any(e.code==b'C' and e.payload==b'SELECT '+str(1 if self.unavailable else self.chunk_count).encode()+b'\0' for e in call.events)):
                raise NativeBoundaryRefusal('Original complete census call required')
            if self.unavailable:raise NativeBoundaryRefusal('Native census unavailable')
            barrier=self.outbound.barrier if self.outbound is not None else None
            if (barrier is None or barrier.owner is not self.outbound or barrier.call is not self.entry
                    or barrier.revision!=call.revision or not barrier.writes
                    or not any(item is barrier for item in self.outbound.barriers)
                    or any(w.call is not self.entry or not w.native_returned or not w.settled for w in barrier.writes)):
                raise NativeBoundaryRefusal('Original outbound census barrier required')
            self._charge(2*(len(self.sql.encode())+6))
            request=b''.join(w.data for w in barrier.writes)
            payload=self.sql.encode()+b'\0'
            if request!=b'Q'+struct.pack('!I',len(payload)+4)+payload:
                raise NativeBoundaryRefusal('Exact original census request required')
            image=bytes(self.image)
            image.decode('utf-8','strict')
            observation=NativeSourceCensusObservation(call,image,request,tuple(self.frames))
            # Retain before a reply can be lost; one original capture cannot replay.
            self._publish(observation)
            self.image=None
            return observation
        finally:
            self.session.admission_closed=True
