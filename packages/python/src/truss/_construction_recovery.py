"""Process-lifetime original construction custody; not qualified bootstrap recovery.

The trusted caller owns the administrative connection exclusively. Calls retained
here are driver facts, not wire-completion proofs. There is no replay, eviction,
weak retention, COMMIT, durable registry or installation-readiness claim.
"""
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, slots=True, eq=False)
class ConstructionReference:
    _issuer: object
    _ordinal: int


@dataclass(frozen=True, slots=True)
class ConstructionOriginal:
    connection: object
    statements: bytes
    target: bytes
    definition_baseline: bytes


@dataclass(frozen=True, slots=True)
class ConstructionCallObservation:
    sql: str
    entered: bool
    returned: bool
    exception: object
    status: bytes | None
    observation_failure: object


@dataclass(frozen=True, slots=True)
class ConstructionObservation:
    original: ConstructionOriginal
    phase: str
    calls: tuple[ConstructionCallObservation, ...]
    rollback_confirmed: bool
    primary_failure: object
    cleanup_failure: object
    observation_failure: object


@dataclass(slots=True)
class _Call:
    sql: str = ''
    entered: bool = False
    returned: bool = False
    result: object = None
    exception: object = None
    status: bytes | None = None
    observation_failure: object = None


@dataclass(slots=True)
class _Attempt:
    reference: ConstructionReference
    original: ConstructionOriginal
    slots: tuple[_Call, ...]
    phase: str = 'prepared'
    ordinary_count: int = 0
    cleanup_count: int = 0
    rollback_confirmed: bool = False
    primary_failure: object = None
    cleanup_failure: object = None
    observation_failure: object = None


class ProvisionalConstructionRecovery:
    def __init__(self, *, retained_attempts=128):
        if type(retained_attempts) is not int or not 1 <= retained_attempts <= 128:
            raise ValueError('Bounded attempt retention required')
        self._limit = retained_attempts
        self._issuer = object()
        self._entries = ()
        self._lock = Lock()

    def _available(self, connection):
        if len(self._entries) >= self._limit:
            raise ValueError('Construction retention exhausted before effects')
        if any(e.original.connection is connection and e.phase not in ('terminated','preflight_terminated') for e in self._entries):
            raise ValueError('Unresolved original construction on connection')

    def check_available(self, connection):
        # Gate before native access; exclusive caller ownership still applies.
        with self._lock:self._available(connection)

    def reserve(self, original):
        if type(original) is not ConstructionOriginal:
            raise ValueError('Original construction custody required')
        if any(type(value) is not bytes for value in (original.statements,original.target,original.definition_baseline)):
            raise ValueError('Exact immutable original bytes required')
        with self._lock:
            self._available(original.connection)
            reference = ConstructionReference(self._issuer, len(self._entries))
            # 128 ordinary calls plus two slots solely for rollback/restoration.
            entry = _Attempt(reference, original, tuple(_Call() for _ in range(130)))
            self._entries = (*self._entries, entry)
            return reference

    def _entry(self, reference):
        if type(reference) is not ConstructionReference or reference._issuer is not self._issuer:
            raise ValueError('Foreign original construction reference')
        if type(reference._ordinal) is not int or not 0 <= reference._ordinal < len(self._entries):
            raise ValueError('Original construction reference required')
        entry = self._entries[reference._ordinal]
        if entry.reference is not reference:
            raise ValueError('Original construction reference required')
        return entry

    def acquire(self, reference):
        with self._lock:
            entry = self._entry(reference)
            if entry.phase != 'prepared':
                raise ValueError('Original construction cannot be executed twice')
            try:port=_ConstructionPort(self, entry)
            except BaseException as error:
                entry.primary_failure=error
                entry.phase='preflight_terminated'
                raise
            entry.phase = 'executing'
            return port

    def references(self):
        with self._lock:
            return tuple(e.reference for e in self._entries)

    def inspect(self, reference):
        """Historical retained facts only; never accesses the connection."""
        with self._lock:
            entry = self._entry(reference)
            slots = (*entry.slots[:entry.ordinary_count], *entry.slots[128:128+entry.cleanup_count])
            calls = tuple(ConstructionCallObservation(s.sql, s.entered, s.returned,
                s.exception, s.status, s.observation_failure) for s in slots)
            return ConstructionObservation(entry.original, entry.phase, calls,
                entry.rollback_confirmed, entry.primary_failure,
                entry.cleanup_failure, entry.observation_failure)

    def fail_preflight(self, reference, error):
        with self._lock:
            entry=self._entry(reference)
            if entry.phase not in ('prepared','executing') or entry.ordinary_count or entry.cleanup_count:
                raise ValueError('Unsubmitted original preflight required')
            entry.primary_failure=error
            entry.phase='preflight_terminated'

    def settle(self, reference, *, rollback_confirmed, primary, cleanup):
        with self._lock:
            entry = self._entry(reference)
            entry.rollback_confirmed = rollback_confirmed
            entry.primary_failure = primary
            entry.cleanup_failure = cleanup
            entry.phase = 'terminated' if rollback_confirmed else 'unresolved'


class _ConstructionPort:
    def __init__(self, owner, entry):
        self._owner, self._entry = owner, entry
        self._cleanup = False

    @property
    def _transaction_status(self):
        return self._entry.original.connection._transaction_status

    def run(self, sql):
        with self._owner._lock:
            entry = self._entry
            if sql == 'ROLLBACK':
                self._cleanup = True
            if self._cleanup:
                if entry.cleanup_count >= 2:
                    raise ValueError('Reserved cleanup call slots exhausted')
                slot = entry.slots[128+entry.cleanup_count]
                entry.cleanup_count += 1
            else:
                if entry.ordinary_count >= 128:
                    raise ValueError('Reserved construction call slots exhausted')
                slot = entry.slots[entry.ordinary_count]
                entry.ordinary_count += 1
            slot.sql = sql
            slot.entered = True
        try:
            result = entry.original.connection.run(sql)
        except BaseException as error:
            with self._owner._lock:
                slot.exception = error
            try:self._status(slot)
            except BaseException:pass  # Preserve the original run failure.
            raise
        # Preserve return facts before any subsequent status/property/projection.
        with self._owner._lock:
            slot.result = result
            slot.returned = True
        self._status(slot)
        return result

    def _status(self, slot):
        try:
            status = self._entry.original.connection._transaction_status
            if type(status) is not bytes or status not in (b'I', b'T', b'E'):
                raise ValueError('Original driver status unavailable')
            with self._owner._lock:
                slot.status = status
        except BaseException as error:
            with self._owner._lock:
                slot.observation_failure = error
                self._entry.observation_failure = error
            if not isinstance(error,Exception):raise
