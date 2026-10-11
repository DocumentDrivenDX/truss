"""Private, process-lifetime operation registry; no native authority claim.

One registry belongs to one executor and is shared by its assembled protocols.
The lock protects transitions, never native calls. A registered completion
verifier must qualify the complete original native/resource ledger externally.
Byte reservations below cover encoded metadata/evidence, not Python heap usage.
"""
from dataclasses import dataclass, replace
from threading import Lock
from uuid import uuid4
from ._host_execution import HostExecutor

@dataclass(frozen=True)
class ArbitrationLimits:
    assemblies: int = 64
    attempts: int = 4096
    prepared: int = 256
    leases: int = 64
    registry_bytes: int = 8388608
    metadata_bytes: int = 4096
    completion_bytes: int = 65536
    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in self.__dict__.values()):
            raise ValueError('Positive integer limits required')

@dataclass(frozen=True)
class Refused:
    reason: str
    status: str = 'refused'

@dataclass(frozen=True)
class Unresolved:
    recovery_references: tuple[str, ...]
    status: str = 'unresolved'

@dataclass(frozen=True)
class Admitted:
    lease: object
    status: str = 'admitted'

@dataclass(frozen=True)
class Prepared:
    attempt: object
    status: str = 'prepared'

@dataclass(frozen=True)
class CompletionContext:
    registry: object
    assembly: object
    attempt: object
    lease: object
    transaction: object
    custody: object
    generation: str

@dataclass(frozen=True)
class CompletionDecision:
    """Trusted original producer correspondence, not asserted release authority."""
    state: str  # caller_idle or transaction_ended
    original_context: CompletionContext
    resources_closed: bool
    boundary_restored: bool
    recovery_references: tuple[str, ...] = ()

@dataclass
class _Verification:
    observed: object = None
    done: bool = False
    started: bool = False

@dataclass(frozen=True)
class _Entry:
    attempt: object
    assembly: object
    transaction: object
    custody: object
    generation: str
    recovery: tuple[str, ...]
    phase: str = 'prepared'
    decision: object = None
    lease: object = None
    completion_context: CompletionContext | None = None
    completion: bytes | None = None
    release_result: object = None
    verification: _Verification | None = None

@dataclass(frozen=True)
class _Root:
    assemblies: dict
    entries: dict
    leases: dict
    active: dict
    prepared: int = 0
    reserved_bytes: int = 0

class OperationArbitration:
    """One exact executor registry; trusted completion verification is external.

    State replacements are fully prepared before one root publication. Native
    verifier callbacks run outside the lock while the original slot stays held.
    Encoded-byte reservations are not a whole Python heap qualification.
    """
    def __init__(self, executor, verify_completion, *, limits=None):
        if type(executor) is not HostExecutor or not callable(verify_completion):
            raise ValueError('Original executor and registered verifier required')
        self._executor, self._verify = executor, verify_completion
        self._limits = limits or ArbitrationLimits()
        if type(self._limits) is not ArbitrationLimits:
            raise ValueError('Original limits required')
        self._lock = Lock()
        self._root = _Root({}, {}, {}, {})
        with executor._arbitration_registration_lock:
            if executor._closed:
                raise ValueError('Executor disposed')
            if executor._arbitration_service is not None:
                raise ValueError('Original executor arbitration already registered')
            executor._arbitration_service = self

    def _publish(self, root):
        self._root = root

    def register(self, assembly):
        if type(assembly) is not object:
            return Refused('integrity')
        with self._lock:
            root = self._root
            if assembly in root.assemblies:
                return Refused('already_registered')
            if len(root.assemblies) >= self._limits.assemblies:
                return Refused('resource')
            assemblies = {**root.assemblies, assembly: True}
            self._publish(replace(root, assemblies=assemblies))
            return 'registered'

    def prepare(self, assembly, transaction):
        custody = HostExecutor._original_custody(self._executor, transaction)
        self._executor._refresh_native_liveness(custody)
        if custody is None or not custody.usable or self._executor._closed:
            return Refused('invalid_transaction')
        if custody.cancellation is not None and custody.cancellation.requested():
            return Refused('cancelled')
        generation = custody.observation.transaction_identity
        if type(generation) is not str or len(generation) > self._limits.metadata_bytes:
            return Refused('resource')
        metadata = generation.encode('utf-8')
        if len(metadata) + 128 > self._limits.metadata_bytes:
            return Refused('resource')
        reserve = self._limits.metadata_bytes + self._limits.completion_bytes
        with self._lock:
            root = self._root
            if type(assembly) is not object or not root.assemblies.get(assembly, False):
                return Refused('disposed')
            if (len(root.entries) >= self._limits.attempts or root.prepared >= self._limits.prepared
                    or root.reserved_bytes + reserve > self._limits.registry_bytes):
                return Refused('resource')
            token = object()
            entry = _Entry(token, assembly, transaction, custody, generation, ('arbitration:' + uuid4().hex,))
            result = Prepared(token)
            entries = {**root.entries, token: entry}
            self._publish(replace(root, entries=entries, prepared=root.prepared + 1,
                                  reserved_bytes=root.reserved_bytes + reserve))
            return result

    def acquire(self, attempt):
        with self._lock:
            root = self._root
            entry = root.entries.get(attempt) if type(attempt) is object else None
            if entry is None:
                return Refused('integrity')
            if entry.phase != 'prepared':
                return entry.decision if entry.phase in ('admitted', 'verifying', 'unresolved', 'refused') else Refused('invalid_transaction')
            reason = None
            if not root.assemblies[entry.assembly] or self._executor._closed:
                reason = 'disposed'
            elif not entry.custody.usable:
                reason = 'invalid_transaction'
            elif entry.custody.cancellation is not None and entry.custody.cancellation.requested():
                reason = 'cancelled'
            elif entry.transaction in root.active:
                reason = 'busy'
            elif len(root.active) >= self._limits.leases:
                reason = 'resource'
            if reason:
                changed = replace(entry, phase='refused', decision=Refused(reason))
                next_root = replace(root, entries={**root.entries, attempt: changed}, prepared=root.prepared - 1)
            else:
                lease = object()
                context = CompletionContext(self, entry.assembly, entry.attempt, lease,
                                            entry.transaction, entry.custody, entry.generation)
                changed = replace(entry, lease=lease, phase='admitted', decision=Admitted(lease), completion_context=context)
                next_root = replace(root, entries={**root.entries, attempt: changed},
                                    leases={**root.leases, lease: attempt},
                                    active={**root.active, entry.transaction: attempt}, prepared=root.prepared - 1)
            self._publish(next_root)
            return changed.decision

    def observe(self, attempt):
        with self._lock:
            entry = self._root.entries.get(attempt) if type(attempt) is object else None
            if entry is None:
                return Refused('integrity')
            if entry.phase == 'prepared':
                return Unresolved(entry.recovery)
            if entry.phase in ('closed', 'abandoned'):
                return Refused('invalid_transaction')
            return entry.decision

    def abandon_prepared(self, attempt):
        with self._lock:
            root = self._root
            entry = root.entries.get(attempt) if type(attempt) is object else None
            if entry is None:
                return Refused('integrity')
            if entry.phase == 'abandoned':
                return 'abandoned'
            if entry.phase != 'prepared':
                return Refused('already_decided')
            changed = replace(entry, phase='abandoned')
            self._publish(replace(root, entries={**root.entries, attempt: changed}, prepared=root.prepared - 1))
            return 'abandoned'

    def close_admission(self, assembly):
        with self._lock:
            root = self._root
            if type(assembly) is not object or assembly not in root.assemblies:
                return
            entries = dict(root.entries)
            count = 0
            for token, entry in root.entries.items():
                if entry.assembly is assembly and entry.phase == 'prepared':
                    entries[token] = replace(entry, phase='abandoned')
                    count += 1
            self._publish(replace(root, assemblies={**root.assemblies, assembly: False},
                                  entries=entries, prepared=root.prepared - count))

    def release(self, lease, evidence):
        with self._lock:
            root = self._root
            attempt = root.leases.get(lease) if type(lease) is object else None
            entry = root.entries.get(attempt)
            if entry is None:
                return Unresolved(('arbitration:foreign-lease',))
            if type(evidence) is not bytes or len(evidence) > self._limits.completion_bytes:
                return Unresolved(entry.recovery)
            if entry.completion is not None and evidence != entry.completion:
                return Unresolved(entry.recovery)
            if entry.phase == 'closed':
                return entry.release_result
            if entry.phase == 'verifying':
                if entry.verification.done:
                    return self._finish_verification(root, entry, entry.verification.observed)
                if entry.verification.started:
                    return Unresolved(entry.recovery)
                marker = entry.verification
                verifying = entry
            else:
                if entry.phase not in ('admitted', 'unresolved'):
                    return Unresolved(entry.recovery)
                marker = _Verification()
                verifying = replace(entry, completion=evidence, phase='verifying', verification=marker)
                self._publish(replace(root, entries={**root.entries, attempt: verifying}))
            marker.started = True
        observed = None
        try:
            try:
                observed = self._admit_completion(self._verify(evidence, verifying.completion_context), verifying)
            except Exception:
                observed = None
        finally:
            with self._lock:
                marker.observed = observed
                marker.done = True
        with self._lock:
            root = self._root
            current = root.entries[attempt]
            if current.phase == 'closed':
                return current.release_result
            if current.verification is not marker:
                return current.release_result or Unresolved(current.recovery)
            return self._finish_verification(root, current, observed)

    def _admit_completion(self, observed, entry):
        """Bound verifier output before retaining it; invalid output stays unknown."""
        if (type(observed) is not CompletionDecision or observed.original_context is not entry.completion_context
                or type(observed.state) is not str or observed.state not in ('caller_idle', 'transaction_ended')
                or type(observed.resources_closed) is not bool or type(observed.boundary_restored) is not bool
                or type(observed.recovery_references) is not tuple or len(observed.recovery_references) > 32):
            return None
        refs = observed.recovery_references
        if not all(type(ref) is str and 0 < len(ref) <= 128 for ref in refs):
            return None
        combined = tuple(dict.fromkeys((*entry.recovery, *refs)))
        size = sum(len(ref.encode('utf-8')) for ref in combined)
        if size + len(entry.generation.encode('utf-8')) + 128 > self._limits.metadata_bytes:
            return None
        return observed

    def _finish_verification(self, root, current, observed):
        """Transition-lock only; preserves a completed verifier across faults."""
        qualified = (type(observed) is CompletionDecision
                     and observed.original_context is current.completion_context
                     and type(observed.state) is str and observed.state in ('caller_idle', 'transaction_ended')
                     and observed.resources_closed is True and observed.boundary_restored is True
                     and type(observed.recovery_references) is tuple
                     and (observed.state == 'transaction_ended' or not observed.recovery_references)
                     and (observed.state == 'transaction_ended' or current.custody.usable))
        recovery = current.recovery
        recovery_valid = False
        if (type(observed) is CompletionDecision and observed.original_context is current.completion_context
                and type(observed.recovery_references) is tuple
                and len(observed.recovery_references) <= 32):
            references = observed.recovery_references
            if all(type(ref) is str and 0 < len(ref) <= 128 for ref in references):
                combined = tuple(dict.fromkeys((*recovery, *references)))
                size = sum(len(ref.encode('utf-8')) for ref in combined)
                if size + len(current.generation.encode('utf-8')) + 128 <= self._limits.metadata_bytes:
                    recovery = combined
                    recovery_valid = True
        qualified = qualified and recovery_valid
        if qualified:
            changed = replace(current, phase='closed', release_result='released', recovery=recovery)
            active = dict(root.active)
            if active.get(current.transaction) is current.attempt:
                del active[current.transaction]
            next_root = replace(root, entries={**root.entries, current.attempt: changed}, active=active)
            if observed.state == 'transaction_ended':
                current.custody.usable = False
                current.custody.refusal_code = 'invalid_transaction'
        else:
            result = Unresolved(recovery)
            changed = replace(current, phase='unresolved', decision=result, release_result=result, recovery=recovery)
            next_root = replace(root, entries={**root.entries, current.attempt: changed})
        self._publish(next_root)
        return changed.release_result
