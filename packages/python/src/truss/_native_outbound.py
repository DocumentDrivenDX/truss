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

def successful_outbound_basis(boundary):
    basis = boundary.last_call
    return (type(basis) is NativeCall and basis.capture_complete and not basis.driver_raised
            and basis.final_status in (b'I', b'T') and basis.revision == boundary._revision
            and not boundary._calling)

@dataclass(frozen=True, eq=False)
class ControlOutboundWitness:
    ledger: object
    completion: object

def confirmed_control_outbound_basis(boundary):
    witness = getattr(boundary, '_control_outbound_witness', None)
    if type(witness) is not ControlOutboundWitness or boundary._calling or boundary._quarantined or boundary._host_control_pending is not None:
        return False
    ledger = witness.ledger
    completion = witness.completion
    if (ledger.boundary is not boundary or ledger.completion is not completion
            or not any(item is ledger for item in boundary._host_control_records)):
        return False
    gate = ledger.result_custody
    basis = boundary.last_call
    if (completion.ledger is not ledger or completion.deadline_basis is not ledger.deadline.accepted_basis
            or not ledger.record.release.published or ledger.record.original is not basis
            or not gate.detached or gate.failed or not ledger.calls
            or type(basis) is not NativeCall or not basis.capture_complete
            or basis.final_status not in (b'I', b'E') or basis.revision != boundary._revision
            or boundary._connection._transaction_status != basis.final_status):
        return False
    entry = ledger.calls[-1]
    outbound = gate.outbound
    barrier = outbound.barrier if outbound is not None else None
    return (entry.native_call is basis and barrier is not None and barrier.owner is outbound
            and barrier.call is entry and barrier.revision == basis.revision
            and any(item is barrier for item in outbound.barriers)
            and bool(barrier.writes) and all(w.call is entry and w.native_returned and w.settled
                and type(w.data) is bytes and w.data[:1] == b'Q' and w.data[-1:] == b'\0'
                for w in barrier.writes))

def admitted_outbound_basis(boundary):
    return successful_outbound_basis(boundary) or confirmed_control_outbound_basis(boundary)

class NativeOutbound:
    def __init__(self, gate, guard, limits):
        self.gate, self.guard = gate, guard
        self.boundary = gate.boundary
        basis = self.boundary.last_call
        if not admitted_outbound_basis(self.boundary):
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
