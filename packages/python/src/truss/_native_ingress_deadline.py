"""Original pending-read timeout custody; buffered outbound remains unqualified."""
import io
import socket
from ._native_pg8000 import NativeBoundaryRefusal
from ._native_deadline import NativeOperationDeadline

def original_ingress_profile(boundary):
    con = boundary._connection
    return (con._sock is boundary._original_stream
            and type(con._sock) is io.BufferedRWPair
            and con._usock is boundary._original_socket
            and type(con._usock) is socket.socket
            and con._usock.family == socket.AF_UNIX
            and (con._usock.gettimeout() is None or con._usock.gettimeout() > 0))

class NativeIngressDeadline:
    def __init__(self, gate, deadline):
        if type(deadline) is not NativeOperationDeadline:
            raise NativeBoundaryRefusal('Original operation deadline required')
        self.gate, self.deadline = gate, deadline
        self.boundary = gate.boundary
        if not original_ingress_profile(self.boundary):
            raise NativeBoundaryRefusal('Original ingress transport required')
        self.stream = self.boundary._original_stream
        self.socket = self.boundary._original_socket
        self.host_timeout = self.socket.gettimeout()
        self.failure = None
        self.restoration_failure = None

    def _visit(self, original, invoke):
        try:
            if self.failure is not None or self.gate.failed:
                raise NativeBoundaryRefusal('Failed original ingress retained')
            if (original is not self.stream or self.gate.original_sock is not self.stream
                    or self.boundary._connection._sock is not self.gate
                    or self.boundary._connection._usock is not self.socket
                    or self.socket.gettimeout() != self.host_timeout):
                raise NativeBoundaryRefusal('Original ingress custody changed')
            remaining = self.deadline.remaining_seconds()
            timeout = remaining if self.host_timeout is None else min(self.host_timeout, remaining)
            # Cover the setter itself: a lost reply may follow its mutation.
            try:
                self.socket.settimeout(timeout)
                count = invoke()
            finally:
                try:
                    self.socket.settimeout(self.host_timeout)
                except BaseException as error:
                    self.restoration_failure = error
                    raise
            self.deadline.check()
            return count
        except BaseException as error:
            if self.failure is None:
                self.failure = error
            self.gate.failed = True
            self.boundary._quarantined = True
            raise

    def receive(self, original, view):
        return self._visit(original, lambda: io.BufferedRWPair.readinto1(self.stream, view))

    def send(self, original, data, entry):
        def submit():
            socket.socket.sendall(self.socket, data)
            entry.native_returned = True
        return self._visit(original, submit)

    def checkpoint(self):
        # No I/O or timeout mutation at the direct sink's flush barrier.
        try:
            if (self.failure is not None or self.gate.failed
                    or self.boundary._connection._sock is not self.gate
                    or self.boundary._connection._usock is not self.socket
                    or self.gate.original_sock is not self.stream
                    or self.socket.gettimeout() != self.host_timeout):
                raise NativeBoundaryRefusal('Original transport barrier unavailable')
            self.deadline.check()
        except BaseException as error:
            if self.failure is None: self.failure = error
            self.gate.failed = True
            self.boundary._quarantined = True
            raise
