"""Private original fixed constructor custody; never proves idle or authority."""
from dataclasses import dataclass
from threading import Lock
from importlib.metadata import version
import io
import socket
from pg8000 import core, native
from ._native_driver_profile import original_simple_source_profile
from ._native_deadline import NativeOperationDeadline

class StartupRefusal(RuntimeError):pass
class StartupFailure(StartupRefusal):
    def __init__(self,record):
        super().__init__('Original constructor unavailable; retained creation custody')
        self.record=record

_CONNECTION=native.Connection
_SOCKET=socket.socket
_CONTEXT=core.Context
_SHUTDOWN=socket.socket.shutdown
_SOURCE=((native.Connection,'__init__',native.Connection.__init__),
         (core.CoreConnection,'__init__',core.CoreConnection.__init__),
         (core.CoreConnection,'close',core.CoreConnection.close),
         *((core,name,getattr(core,name)) for name in ('_make_socket','_read','_write','_flush')),
         *((core.CoreConnection,name,getattr(core.CoreConnection,name)) for name in
           ('handle_AUTHENTICATION_REQUEST','handle_READY_FOR_QUERY','handle_ERROR_RESPONSE',
            'handle_BACKEND_KEY_DATA','handle_PARAMETER_STATUS','handle_NOTICE_RESPONSE',
            'send_QUERY','_send_message','handle_messages','execute_simple',
            'handle_COMMAND_COMPLETE','handle_ROW_DESCRIPTION','handle_DATA_ROW',
            'handle_EMPTY_QUERY_RESPONSE','handle_NOTIFICATION_RESPONSE')),
         (core.Context,'__init__',core.Context.__init__),
         (native.Connection,'run',native.Connection.run))
_CLOSE=core.CoreConnection.close
SHOW='SHOW transaction_isolation'

def _source_profile():
    return (version('pg8000')=='1.31.5' and native.Connection is _CONNECTION
            and core.Context is _CONTEXT and socket.socket is _SOCKET and _CONNECTION.__mro__==(_CONNECTION,core.CoreConnection,object)
            and all(getattr(owner,name) is original for owner,name,original in _SOURCE))

@dataclass(eq=False)
class _Creation:
    owner: object
    connection: object
    deadline: object
    token: object
    kind: str = 'bootstrap'
    witness: object = None
    stream: object = None
    socket: object = None
    close_attempted: bool = False
    cleanup_attempts: int = 0
    closed: bool = False
    disconnected: bool = False
    cleanup_failures: tuple = ()
    ledger: object = None
    release: object = None
    completion: object = None
    phase: str = 'creating'
    exposed: bool = False
    constructor_completed: bool = False

    def close_owned(self, *, recovery=False):
        if self.exposed:raise StartupRefusal('Factory no longer owns connection lifetime')
        if self.close_attempted and not recovery:return
        if self.cleanup_attempts>=4:raise StartupRefusal("Original cleanup attempt allowance exhausted")
        self.cleanup_attempts+=1
        self.close_attempted=True
        if self.stream is None:self.stream=getattr(self.connection,'_sock',None)
        if self.socket is None:self.socket=getattr(self.connection,'_usock',None)
        failures=[];fatal=None;disconnected=self.disconnected
        if type(self.socket) is _SOCKET and not disconnected:
            try:
                _SHUTDOWN(self.socket,socket.SHUT_RDWR);disconnected=True;self.disconnected=True
            except BaseException as error:
                failures.append(type(error).__name__)
                if not isinstance(error,Exception):fatal=error
        if type(self.stream) is io.BufferedRWPair:
            if disconnected:
                try:io.BufferedRWPair.close(self.stream)
                except BaseException as error:
                    failures.append(type(error).__name__)
                    if not isinstance(error,Exception):fatal=error
            else:failures.append('stream_retained_after_unconfirmed_shutdown')
        if type(self.socket) is _SOCKET and disconnected:
            try:_SOCKET.close(self.socket)
            except BaseException as error:
                failures.append(type(error).__name__)
                if not isinstance(error,Exception):fatal=error
        self.cleanup_failures=(*self.cleanup_failures,*failures)
        self.closed=(type(self.stream) is io.BufferedRWPair and self.stream.closed
                     and type(self.socket) is _SOCKET and self.socket.fileno()==-1)
        if fatal is not None:raise fatal

def _text_option(value,limit):
    if type(value) is not str or not value or len(value)>limit or '\0' in value:return False
    try:return len(value.encode('utf8'))<=limit
    except UnicodeError:return False

_producers=()
_producer_lock=Lock()

@dataclass(eq=False)
class StartupWitness:
    issuer: object
    record: object
    connection: object
    boundary: object = None
    phase: str = 'creating'

class StartupProducer:
    def __init__(self,limit):
        global _producers
        if type(limit) is not int or not 1<=limit<=256:
            raise StartupRefusal('Original bounded producer required')
        self._limit=limit;self._records=();self._lock=Lock()
        with _producer_lock:
            if len(_producers)>=256:raise StartupRefusal('Original producer retention exhausted')
            _producers=(*_producers,self)
    def create(self,*,user,database,unix_sock,timeout,deadline):
        if (not any(item is self for item in _producers) or not _source_profile()
                or type(deadline) is not NativeOperationDeadline
                or any(not _text_option(v,n) for v,n in ((user,128),(database,128),(unix_sock,4096)))
                or not unix_sock.startswith('/') or type(timeout) not in (int,float) or not 0<timeout<=2):
            raise StartupRefusal('Original producer required')
        deadline.check()
        with self._lock:
            deadline.check()
            if len(self._records)>=self._limit:raise StartupRefusal('Original creation retention exhausted')
            connection=object.__new__(_CONNECTION)
            record=_Creation(self,connection,deadline,object())
            self._records=(*self._records,record)
            record.witness=StartupWitness(self,record,connection)
        # Exact private instance hook; the module/class dispatch is untouched.
        connection.close=record.close_owned
        try:
            deadline.check()
            _CONNECTION.__init__(connection,user=user,database=database,unix_sock=unix_sock,
                                 timeout=timeout,ssl_context=False)
            record.stream=connection._sock;record.socket=connection._usock
            if (not _source_profile() or type(record.stream) is not io.BufferedRWPair
                    or type(record.socket) is not _SOCKET or record.socket.family!=socket.AF_UNIX
                    or record.close_attempted or connection._transaction_status is not None):
                raise StartupRefusal('Original constructor profile changed')
            connection.close=_CLOSE.__get__(connection,_CONNECTION)
            record.constructor_completed=True
            record.witness.phase='created'
            return record
        except BaseException as error:
            record.phase='unresolved';record.close_owned()
            if not isinstance(error,Exception):raise
            raise StartupFailure(record) from None

def original(witness,connection):
    if type(witness) is not StartupWitness or type(witness.issuer) is not StartupProducer:return False
    producer=witness.issuer;record=witness.record
    return (any(item is producer for item in _producers)
            and type(record) is _Creation and record.owner is producer
            and any(item is record for item in producer._records)
            and record.constructor_completed and record.witness is witness
            and witness.connection is connection and record.connection is connection
            and not record.exposed and not record.close_attempted and _source_profile())

def attach_startup(witness,connection,boundary):
    if (not original(witness,connection) or witness.phase!='created'
            or witness.boundary is not None or connection._transaction_status is not None
            or connection._sock is not witness.record.stream or connection._usock is not witness.record.socket):
        raise ValueError('Original fresh factory startup witness required')
    witness.boundary=boundary;witness.phase='attached'

def startup_outbound_basis(boundary):
    witness=getattr(boundary,'_startup_witness',None)
    if (not original(witness,boundary._connection) or witness.boundary is not boundary
            or witness.phase!='attached' or boundary._revision!=0 or boundary.last_call is not None
            or boundary._calling or boundary._quarantined):return False
    record=witness.record;ledger=record.ledger
    return (ledger is not None and boundary._operation_ledger is ledger
            and boundary._pending_operation_ledger is ledger and ledger.record is record
            and boundary._operation is record.token and not ledger.calls
            and original_simple_source_profile(boundary))
