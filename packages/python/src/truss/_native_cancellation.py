"""Private one-use prepared-Execute cancellation; not public adoption.

Cancel transport completion is distinct from the original native response and
operation savepoint containment. Only the selected original Unix peer is used.
"""
import socket
import struct
from threading import Event, Lock
from time import monotonic


class CancellationUnavailable(RuntimeError):
    pass


def _new_channel():
    return socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)


class _Dispatch:
    def __init__(self, boundary, revision, call, resource):
        self.boundary, self.revision = boundary, revision
        self.call, self.resource = call, resource
        self.submitted = False
        self.reserved = False
        self.eof = False
        self.failed = False
        self.native = None
        self.deadline = None
        self.finished = Event()


class NativeCancellation:
    def __init__(self, owner):
        self._owner = owner
        self._lock = Lock()
        self._requested = False
        self._bound = False
        self._ended = False
        self._admitted = False
        self._channel_closed = False
        self._closure_failed = False
        self._boundary = None
        self._session = None
        self._entry = None
        self._channel = None
        self._peer = None
        self._packet = None

    def request(self):
        with self._lock:
            ended = self._ended
            if not ended:
                self._requested = True
            boundary = self._boundary
        if boundary is None:
            return 'settled' if ended else 'latched'
        with boundary._lock:
            entry = self._entry
            if ended:
                unresolved = self._closure_failed or entry is not None and (
                    entry.failed or entry.reserved and not entry.eof
                    or entry.native is None or not entry.native.capture_complete)
                return 'unresolved' if unresolved else 'settled'
            if entry is None or not entry.submitted:
                return 'latched'
            if entry.native is not None:
                return 'retained' if entry.reserved and not entry.eof else 'settled'
            if entry.reserved:
                return 'retained'
            self._reserve_dispatch(entry)
        self._dispatch(entry)
        return 'dispatch_finished' if entry.eof else 'unresolved'

    def _claim(self, owner):
        with self._lock:
            if self._owner is not owner or self._bound or self._ended:
                return False
            self._bound = True
            return True

    def _bind(self, owner, boundary):
        with self._lock:
            if self._owner is not owner or not self._bound or self._boundary is not None or self._ended:
                raise CancellationUnavailable('Original unused cancellation handle required')
            self._boundary = boundary
            if self._requested:
                return True
            con = boundary._connection
            native = con._usock
            key = con._backend_key_data
            if (type(native) is not socket.socket or native.family != socket.AF_UNIX
                    or type(key) is not bytes or len(key) != 8
                    or type(native.gettimeout()) not in (int, float)
                    or not 0 < native.gettimeout() <= 2):
                self._ended = True
                raise CancellationUnavailable('Selected original Unix cancellation profile required')
            try:
                self._peer = native.getpeername()
                self._packet = struct.pack('!II', 16, 80877102) + key
                self._channel = _new_channel()
            except BaseException:
                self._ended = True
                raise
            return self._requested

    def _admit(self):
        # Single pre-effect admission/intent arbitration. Request after this
        # point is active cancellation, even before physical token acquisition.
        with self._boundary._lock:
            with self._lock:
                if self._requested:
                    return False
                self._admitted = True
                return True

    def _attach(self, session):
        self._session = session
        session.cancellation = self

    def _reserve_call(self, boundary, revision, call, resource):
        # Caller holds the original boundary lock, before native invocation.
        if (boundary is not self._boundary or boundary._operation_ledger is not self._session
                or self._entry is not None or resource[0] != 'execute'):
            raise CancellationUnavailable('Original cancellation execution correspondence required')
        entry = _Dispatch(boundary, revision, call, resource)
        self._entry = entry
        return entry

    def _reserve_dispatch(self, entry):
        # Publication precedes connect/send. No other call may use this backend.
        entry.deadline = monotonic() + 2.0
        entry.reserved = True
        entry.boundary._cancel_pending = entry

    def _submitted(self):
        boundary = self._boundary
        with boundary._lock:
            entry = self._entry
            if (entry is None or not boundary._calling or boundary._revision != entry.revision
                    or boundary._active_resource is not entry.resource
                    or boundary._operation_ledger is not self._session
                    or not any(call is entry.call for call in self._session.calls) or entry.native is not None):
                raise CancellationUnavailable('Original submitted Execute required')
            gate = self._session.result_custody
            outbound = gate.outbound
            barrier = outbound.barrier
            if (barrier is None or barrier.owner is not outbound
                    or barrier.call is not entry.call or barrier.resource is not entry.resource
                    or barrier.revision != entry.revision
                    or not any(b is barrier for b in outbound.barriers)
                    or barrier.writes[-1].data != b'S\x00\x00\x00\x04'
                    or not any(w.data[:1] == b'E' for w in barrier.writes)):
                raise CancellationUnavailable('Original Execute and Sync sends required')
            entry.submitted = True
            with self._lock:
                requested = self._requested
            dispatch = requested and not entry.reserved
            if dispatch:
                self._reserve_dispatch(entry)
        if dispatch:
            self._dispatch(entry)

    def _remaining(self, entry):
        remaining = entry.deadline - monotonic()
        if remaining <= 0:
            raise CancellationUnavailable('Original cancellation deadline exhausted')
        self._channel.settimeout(remaining)

    def _send(self, entry):
        self._remaining(entry)
        self._channel.connect(self._peer)
        self._remaining(entry)
        self._channel.sendall(self._packet)
        self._remaining(entry)
        if self._channel.recv(1) != b'':
            raise CancellationUnavailable('Original cancellation EOF unavailable')

    def _dispatch(self, entry):
        eof = False
        closed = False
        try:
            self._send(entry)
            eof = True
        except BaseException as error:
            # No secret-bearing exception/transport object crosses this boundary.
            if not isinstance(error, Exception):
                raise
        finally:
            try:
                self._channel.close()
                closed = True
            except BaseException:
                eof = False
            with entry.boundary._lock:
                self._channel_closed = closed
                self._closure_failed = not closed
                entry.eof = eof
                entry.failed = not eof
                if entry.native is not None:
                    self._reconcile(entry)
            entry.finished.set()

    def _drained(self, entry, native):
        # Original call finalizer holds boundary lock. Preserve native facts even
        # when dispatch fails; cancellation does not manufacture a native error.
        entry.native = native
        if not entry.reserved or entry.eof or entry.failed:
            self._reconcile(entry)

    def _reconcile(self, entry):
        boundary = entry.boundary
        if entry.native is None:
            return
        if not entry.native.capture_complete or entry.failed:
            boundary._quarantined = True
        if entry.native.capture_complete and (not entry.reserved or entry.eof):
            if boundary._cancel_pending is entry:
                boundary._cancel_pending = None

    def _settle(self):
        entry = self._entry
        if entry is None:
            return
        if entry.reserved and not entry.eof and not entry.finished.is_set():
            remaining = max(0.0, entry.deadline - monotonic())
            entry.finished.wait(remaining)
        with entry.boundary._lock:
            if (entry.native is None or not entry.native.capture_complete
                    or (entry.reserved and not entry.eof)):
                entry.boundary._quarantined = True
                raise CancellationUnavailable('Original cancellation/drain remains unresolved')
            self._reconcile(entry)

    def _is_requested(self):
        with self._lock:
            return self._requested

    def _close_channel(self):
        if self._channel is None or self._channel_closed:
            return True
        if self._entry is not None and self._entry.reserved:
            return self._channel_closed and self._entry.eof
        try:
            self._channel.close()
            with self._boundary._lock:
                self._channel_closed = True
            return True
        except BaseException:
            with self._boundary._lock:
                self._closure_failed = True
            return False

    def _finish(self):
        # No native/transport effects after original handback.
        with self._lock:
            self._ended = True
