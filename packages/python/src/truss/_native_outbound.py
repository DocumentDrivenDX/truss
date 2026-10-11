"""Private original direct-send ledger; trusted successful empty-writer baseline."""
from dataclasses import dataclass
from ._native_pg8000 import NativeBoundaryRefusal, NativeCall
from ._resource_account import BytePermitAccount

@dataclass(eq=False)
class OutboundWrite:
    call: object
    revision: int
    resource: object
    data: bytes
    native_returned: bool = False
    settled: bool = False

@dataclass(frozen=True, eq=False)
class OutboundBarrier:
    owner: object
    call: object
    revision: int
    resource: object
    writes: tuple

class NativeOutbound:
    def __init__(self, gate, guard, limits):
        self.gate, self.guard = gate, guard
        self.boundary = gate.boundary
        basis = self.boundary.last_call
        if (type(basis) is not NativeCall or not basis.capture_complete
                or basis.driver_raised or basis.final_status != b'T'
                or basis.revision != self.boundary._revision or self.boundary._calling):
            raise NativeBoundaryRefusal('Original successful final-flush baseline required')
        # Selected successful driver paths return after their final original
        # flush/response. Native-error Ready alone cannot establish this basis.
        self.baseline = basis
        self.ordinary = [None] * limits.outbound_records
        self.cleanup = [None] * 128
        self.ordinary_count = self.cleanup_count = 0
        self.accounts = tuple(BytePermitAccount(self, 2 * limits.outbound_bytes,
            2 * limits.outbound_bytes, 4 * limits.outbound_records) for _ in range(2))
        self.barriers = [None] * (limits.outbound_records + 128)
        self.barrier_count = 0
        self.barrier = None

    def _call(self):
        session = self.gate.session
        calls = session.cleanup_calls if self.gate._cleanup_mode() else session.calls
        if (not calls or calls[-1].native_call is not None or not self.boundary._calling
                or self.boundary._operation_ledger is not session):
            raise NativeBoundaryRefusal('Original outbound native call required')
        return calls[-1]

    def write(self, data):
        try:
            call = self._call()
            cleanup = self.gate._cleanup_mode()
            slots = self.cleanup if cleanup else self.ordinary
            count = self.cleanup_count if cleanup else self.ordinary_count
            account = self.accounts[int(cleanup)]
            if type(data) is not bytes or count >= len(slots):
                raise NativeBoundaryRefusal('Bounded exact outbound bytes required')
            size = len(data)
            permit = account.reserve(self, 2 * size)
            account.allocate(self, permit, 2 * size); account.terminate(self, permit)
            payload = data
            entry = OutboundWrite(call, self.boundary._revision, self.boundary._active_resource, payload)
            slots[count] = entry
            if cleanup: self.cleanup_count += 1
            else: self.ordinary_count += 1
            self.guard.send(self.gate.original_sock, payload, entry)
            entry.settled = True
            return len(payload)
        except BaseException:
            self.gate.failed = True
            self.boundary._quarantined = True
            raise

    def flush(self):
        try:
            self.guard.checkpoint()
            call = self._call()
            if self.barrier_count >= len(self.barriers):
                raise NativeBoundaryRefusal('Original outbound barrier capacity exhausted')
            writes = tuple(e for slots in (self.ordinary,self.cleanup) for e in slots
                           if e is not None and e.call is call)
            if not writes or any(not e.native_returned or not e.settled for e in writes):
                raise NativeBoundaryRefusal('Original outbound writes unresolved')
            barrier = OutboundBarrier(self, call, self.boundary._revision,
                                      self.boundary._active_resource, writes)
            self.barriers[self.barrier_count] = barrier
            self.barrier_count += 1
            self.barrier = barrier
            return None
        except BaseException:
            self.gate.failed = True
            self.boundary._quarantined = True
            raise
