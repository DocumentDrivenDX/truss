"""Private factory bootstrap; startup/auth accounting and public C02 remain open.

Creation cleanup owns only unexposed resources. Successful exposure transfers
lifetime to the host; later transaction failures cannot invoke factory cleanup.
"""
from dataclasses import replace
from ._native_pg8000 import NativeBoundary, NativeBoundaryRefusal
from ._host_control_custody import _Ledger, _ControlGate
from ._native_result_custody import NativeTextLimits
from ._native_deadline import NativeOperationDeadline
from ._startup_custody import StartupProducer, StartupRefusal, StartupFailure, _source_profile, SHOW

class BootstrapFailure(NativeBoundaryRefusal):
    def __init__(self,record):
        super().__init__('Original factory bootstrap unavailable; retained creation custody')
        self.record=record

class _BootstrapLedger(_Ledger):
    def _check_call(self,boundary,token,cleanup=None,*,admission=True):
        super()._check_call(boundary,token,cleanup,admission=admission)
        if self.calls or self.record.witness.phase!='attached':
            raise NativeBoundaryRefusal('Original single bootstrap call required')
    def _reserve_call(self,boundary,token,resource,lifecycle,cleanup=None):
        if resource is not None or lifecycle is not None or cleanup is not None:
            raise NativeBoundaryRefusal('Original fixed bootstrap observation required')
        entry=super()._reserve_call(boundary,token,resource,lifecycle,cleanup)
        self.record.witness.phase='consumed'
        return entry
    def simple_query(self,sql):
        if not _source_profile():raise NativeBoundaryRefusal('Original bootstrap source changed')
        if sql!=SHOW:raise NativeBoundaryRefusal('Original fixed bootstrap SHOW required')
        return super().simple_query(sql)

def _text_option(value,limit):
    if type(value) is not str or not value or len(value)>limit or '\0' in value:return False
    try:return len(value.encode('utf8'))<=limit
    except UnicodeError:return False

class NativeConnectionFactory:
    def __init__(self,*,retained_connections=256):
        if type(retained_connections) is not int or not 1<=retained_connections<=256:
            raise ValueError('Bounded exact creation retention required')
        self._producer=StartupProducer(retained_connections)
    @property
    def _records(self):return self._producer._records
    def connect(self,*,user,database,unix_sock,timeout=2.0,limits=None):
        limits=NativeTextLimits(contexts=8,rows=8,columns=5) if limits is None else limits
        if (type(limits) is not NativeTextLimits or limits.contexts<8
                or any(not _text_option(v,n) for v,n in ((user,128),(database,128),(unix_sock,4096)))
                or not unix_sock.startswith('/')
                or type(timeout) not in (int,float) or not 0<timeout<=2
                or not _source_profile()):
            raise NativeBoundaryRefusal('Selected exact fresh-connection profile required')
        deadline=NativeOperationDeadline(limits.ordinary_ms,limits.settlement_ms)
        try:
            record=self._producer.create(user=user,database=database,unix_sock=unix_sock,
                                         timeout=timeout,deadline=deadline)
        except StartupFailure as error:raise BootstrapFailure(error.record) from None
        except StartupRefusal:raise NativeBoundaryRefusal('Original constructor refused') from None
        connection=record.connection
        try:
            deadline.check()
            boundary=NativeBoundary(connection,startup=record.witness)
            self._bootstrap(record,boundary,limits)
            self._publish(record,boundary)
            return boundary
        except BaseException as error:
            if record.exposed:
                if not isinstance(error,Exception):raise
                raise BootstrapFailure(record) from None
            record.phase='unresolved';record.close_owned()
            if not isinstance(error,Exception):raise
            raise BootstrapFailure(record) from None
    def _bootstrap(self,record,boundary,limits):
        deadline=record.deadline;deadline.check()
        boundary.acquire_operation(original_token=record.token)
        record.release=boundary.reserve_operation_release(record.token)
        ledger=_BootstrapLedger(self,boundary,record,record.release.before,deadline=deadline)
        ledger.attached_root=replace(ledger.original_root,ledger=ledger,pending=ledger)
        record.ledger=ledger
        with boundary._lock:boundary._publish_ownership(ledger.attached_root)
        gate=_ControlGate(ledger,limits);ledger.result_custody=gate;gate.install()
        rows=boundary._call(lambda:boundary._run_simple(SHOW),record.token)
        call=boundary.last_call;barrier=gate.outbound.barrier
        if (len(ledger.calls)!=1 or ledger.calls[0].native_call is not call
                or not call.capture_complete or call.driver_raised or call.final_status!=b'I'
                or rows not in ([['read committed']],[['repeatable read']],[['serializable']])
                or tuple(e.payload for e in call.events if e.code==b'C')!=(b'SHOW\0',)
                or sum(e.code==b'Z' for e in call.events)!=1 or barrier is None
                or not barrier.writes or not all(w.native_returned and w.settled for w in barrier.writes)):
            raise NativeBoundaryRefusal('Original complete bootstrap SHOW required')
        ledger.admission_closed=True;deadline.check();gate.detach()
        if not _source_profile():raise NativeBoundaryRefusal('Original source changed before exposure')
        from ._native_driver_profile import original_control_profile
        if not original_control_profile(boundary):raise NativeBoundaryRefusal('Original restored driver required')
        record.completion=(call,barrier,deadline.seal())
        with boundary._lock:
            if boundary._ownership is not ledger.attached_root:raise NativeBoundaryRefusal('Original bootstrap custody changed')
            boundary._publish_ownership(ledger.original_root)
        boundary.release_operation(record.token,original_release=record.release)
        record.phase='ready'
    def recover(self,record):
        if not any(item is record for item in self._records) or not record.exposed:
            raise NativeBoundaryRefusal('Original exposed bootstrap receipt required')
        return record.witness.boundary

    def _publish(self,record,boundary):
        if record.phase!='ready' or not record.release.published or boundary._operation is not None:
            raise NativeBoundaryRefusal('Original bootstrap publication unavailable')
        record.exposed=True;record.phase='exposed'

