"""Selected idle connection attachment; never creates or settles a connection."""
from importlib.metadata import version
from ._native_attachment import DriverAttachment
from .host import HostConnection,HostSession



class BorrowedHostAttachmentFailure(RuntimeError):
    """Construction failed; attachment retains original cleanup custody.

    restored means driver hooks were restored, never that a transaction settled.
    A false value requires exclusive host recovery before reusing the connection.
    """
    def __init__(self,primary,attachment,restored,cleanup=None):
        super().__init__('Borrowed host composition failed')
        self.primary_failure=primary
        self.cleanup_failure=cleanup
        self.restored=restored
        self.attachment=attachment


class _BorrowedFactory:
    def close_host(self,boundary,*,retry=False):
        from ._native_pg8000 import NativeBoundaryRefusal
        raise NativeBoundaryRefusal('Borrowed connection remains caller-owned; use host.detach()')


class BorrowedHost:
    """Caller-owned pg8000 connection and mediated host transaction session.

    Retained raw aliases must remain unused while attached. Dispose closes Truss
    admission; detach restores the driver only after confirmed idle containment.
    Neither method closes, commits, rolls back or resets the caller connection.
    """
    def __init__(self,attachment,session):
        self._attachment=attachment
        self.session: HostSession=session
        self._session=session
        self.connection=HostConnection(attachment.boundary,_BorrowedFactory())
        self._detach_started=False
        self.detach_failure=None

    def dispose(self) -> None:
        self.session.dispose()

    def detach(self) -> bool:
        from ._native_pg8000 import _attachment_lock
        from ._native_driver_profile import original_control_profile
        attachment=self._attachment
        if attachment.phase=='detached':return True
        boundary=attachment.boundary
        session=self._session
        if not session._lock.acquire(blocking=False):return False
        try:
            if not self._detach_started and not original_control_profile(boundary):return False
            with _attachment_lock, boundary._lock:
                if ((boundary._quarantined and not self._detach_started) or boundary._calling
                    or boundary._connection._transaction_status!=b'I'
                    or boundary._connection._sock is not boundary._original_stream
                    or boundary._connection._usock is not boundary._original_socket
                    or not _selected_transport(boundary._connection)
                    or boundary._connection._sock.closed or boundary._connection._usock.fileno()<0
                    or boundary._operation is not None or boundary._operation_ledger is not None
                    or boundary._pending_operation_ledger is not None
                    or boundary._host_control_pending is not None or boundary._cancel_pending is not None
                    or boundary._active_cancellation is not None
                    or any(p._resource.phase!='closed' for p in boundary._resources)
                    or (not self._detach_started and not original_control_profile_unlocked(boundary))):
                    return False
                self._detach_started=True
                session.dispose()
                session._closed=True
                boundary._quarantined=True
                boundary._transaction_tracker._operation_ordinals.close_locked()
                try:
                    restored=attachment.restore()
                except BaseException as error:
                    self.detach_failure=error
                    raise
                if restored:self.detach_failure=None
                return restored
        finally:
            session._lock.release()


def original_control_profile_unlocked(boundary):
    # The profile acquires boundary._lock. Detach already holds that lock, so
    # verify the exact retained driver pointers here without nested acquisition.
    con=boundary._connection
    return (con._sock is boundary._original_stream and con._usock is boundary._original_socket
        and set(con.message_types)==set(boundary._original_handlers)
        and all(con.message_types[code] is handler for code,handler in boundary._original_handlers.items())
        and con.send_PARSE is boundary._parse_entry
        and con.close_prepared_statement is boundary._close_entry
        and con.send_BIND is boundary._bind_entry
        and _selected_transport(con) and not con._sock.closed and con._usock.fileno()>=0
        and getattr(con,'_truss_native_boundary',None) is boundary)


def _selected_transport(connection):
    import io
    import socket
    return (type(connection._sock) is io.BufferedRWPair and type(connection._usock) is socket.socket
        and connection._usock.family==socket.AF_UNIX
        and (connection._usock.gettimeout() is None or connection._usock.gettimeout()>0))


def _preflight(connection):
    from ._native_pg8000 import NativeBoundaryRefusal
    from pg8000.native import Connection
    from pg8000.core import CoreConnection
    from pg8000.converters import string_in,string_out,null_out
    if version('pg8000')!='1.31.5' or type(connection) is not Connection:
        raise NativeBoundaryRefusal('Selected pg8000 native connection required')
    con=connection
    if (hasattr(con,'_truss_native_boundary') or con._transaction_status!=b'I'
        or not _selected_transport(con) or con._sock.closed
        or con._usock.fileno()<0 or con._statement_nums or con._client_encoding!='utf8'
        or con.pg_types[25] is not string_in or con.py_types[str] is not string_out
        or con.py_types[type(None)] is not null_out):
        raise NativeBoundaryRefusal('Live idle unattached resource-free connection required')
    methods=('send_PARSE','send_BIND','close_prepared_statement','execute_simple','send_QUERY',
             '_send_message','handle_messages')
    for name in methods:
        method=getattr(con,name)
        if getattr(method,'__func__',None) is not getattr(CoreConnection,name) or method.__self__ is not con:
            raise NativeBoundaryRefusal('Original driver methods required')
    if getattr(con.run,'__func__',None) is not Connection.run or con.run.__self__ is not con:
        raise NativeBoundaryRefusal('Original driver run required')
    handlers={b'T':'handle_ROW_DESCRIPTION',b'D':'handle_DATA_ROW',b't':'handle_PARAMETER_DESCRIPTION',
              b'C':'handle_COMMAND_COMPLETE',b'E':'handle_ERROR_RESPONSE',b'Z':'handle_READY_FOR_QUERY',
              b'S':'handle_PARAMETER_STATUS',b'N':'handle_NOTICE_RESPONSE',b'A':'handle_NOTIFICATION_RESPONSE',
              b'R':'handle_AUTHENTICATION_REQUEST',b'K':'handle_BACKEND_KEY_DATA',b'I':'handle_EMPTY_QUERY_RESPONSE',
              b'1':'handle_PARSE_COMPLETE',b'2':'handle_BIND_COMPLETE',b'3':'handle_CLOSE_COMPLETE',
              b's':'handle_PORTAL_SUSPENDED',b'n':'handle_NO_DATA',b'c':'handle_COPY_DONE',
              b'd':'handle_COPY_DATA',b'G':'handle_COPY_IN_RESPONSE',b'H':'handle_COPY_OUT_RESPONSE'}
    if type(con.message_types) is not dict or set(con.message_types)!=set(handlers):
        raise NativeBoundaryRefusal('Original complete message dispatch required')
    for code,name in handlers.items():
        method=con.message_types.get(code)
        if getattr(method,'__func__',None) is not getattr(CoreConnection,name) or method.__self__ is not con:
            raise NativeBoundaryRefusal('Original driver handlers required')


def adopt_pg8000_host(connection: object) -> BorrowedHost:
    """Attach an idle pg8000.native.Connection1.31.5 over Unix socket, without I/O.

    The host must have observed an actual idle driver completion before calling.
    Fresh startup status alone and active transactions are unsupported. Use the
    mediator for a successful idle observation (for example SELECT 1), then the
    returned session's explicit baseline, begin and adopt_transaction controls.
    """
    from ._native_pg8000 import NativeBoundary,NativeBoundaryRefusal,_attachment_lock
    from ._native_driver_profile import original_control_profile
    from ._host_execution import HostExecutor
    from ._native_transactions import NativeTransactions
    from ._native_arbitration import NativeArbitration
    from ._host_control_custody import HostControlCustody
    from ._host_session import NativeHostSession
    _preflight(connection)
    attachment=DriverAttachment()
    failure=BorrowedHostAttachmentFailure(None,attachment,False)
    try:
        boundary=NativeBoundary(connection,attachment=attachment)
        if not original_control_profile(boundary):
            raise NativeBoundaryRefusal('Original selected driver profile required')
        executor=HostExecutor()
        tracker=NativeTransactions(boundary,mediated_namespace=True)
        arbitration=NativeArbitration(executor)
        session=NativeHostSession(executor,tracker,arbitration,
                                  control_producer=HostControlCustody(executor))
        return BorrowedHost(attachment,session)
    except BaseException as primary:
        cleanup=None
        try:
            with _attachment_lock:restored=attachment.restore()
        except BaseException as error:
            cleanup=error;restored=False
        if not restored and attachment.boundary is not None:
            attachment.boundary._quarantined=True
        failure.primary_failure=primary
        failure.cleanup_failure=cleanup
        failure.restored=restored
        raise failure from primary
