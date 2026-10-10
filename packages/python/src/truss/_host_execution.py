"""Private adoption candidate; E06 native arbitration is not yet integrated.

Unit-test ports provide component evidence only. Never advertise these handles
as admitted protected transactions or expose this executor as a public capability.
"""
from dataclasses import dataclass, replace
from uuid import uuid4
from threading import Lock
from .execution import HostTransactionPort, TransactionObservation, Isolation, AccessMode, Outcome, Ok, Error, ExecutionFailure

class TransactionHandle:
    """Issuer-bound opaque lifetime handle. Public properties are descriptive."""
    def __init__(self, issuer, key, isolation, access_mode):
        self._issuer, self._key = issuer, key
        self.isolation, self.access_mode = isolation, access_mode
        self.ownership = 'caller'

class SavepointHandle:
    def __init__(self, issuer, key):
        self._issuer, self._key = issuer, key

@dataclass
class _Adoption:
    port: HostTransactionPort
    observation: TransactionObservation
    handle: TransactionHandle
    usable: bool = True
    refusal_code: str = "transaction_unusable"

class HostExecutor:
    """One synchronous executor over explicit trusted ports; no connection pool."""
    def __init__(self):
        self._issuer = object()
        self._transactions = {}
        self._savepoints = {}
        self._closed = False
        self._ordinal = 0
        self._arbitration_service = None
        self._arbitration_registration_lock = Lock()

    @staticmethod
    def _error(code, message):
        return Error(ExecutionFailure(code, message))

    def adopt_transaction(self, port: HostTransactionPort, *, isolation: Isolation,
                          access_mode: AccessMode) -> Outcome[TransactionHandle]:
        if self._closed:
            return self._error('invalid_transaction', 'Executor disposed')
        if isolation not in ('read_committed', 'repeatable_read', 'serializable') or access_mode not in ('read_only', 'read_write'):
            return self._error('invalid_transaction', 'Unsupported requested transaction profile')
        try:
            observed = port.observe()
        except Exception:
            return self._error('transaction_unusable', 'Original transaction observation unavailable')
        if (type(observed) is not TransactionObservation or observed.state != 'active'
                or type(observed.connection_identity) is not str or not observed.connection_identity
                or type(observed.transaction_identity) is not str or not observed.transaction_identity
                or observed.isolation != isolation or observed.access_mode != access_mode):
            return self._error('invalid_transaction', 'Actual transaction profile does not match')
        if any(a.observation.connection_identity == observed.connection_identity
               for a in self._transactions.values()):
            return self._error('invalid_transaction', 'Connection already adopted')
        key = uuid4().hex
        handle = TransactionHandle(self._issuer, key, isolation, access_mode)
        self._transactions[key] = _Adoption(port, observed, handle)
        return Ok(handle)

    def _original_custody(self, handle):
        """Pure issuer lookup for private preparation/recovery, never admission.

        Retained entries remain recognizable after quarantine/disposal. This does
        not observe native state, acquire exclusion or grant command authority.
        """
        if type(handle) is not TransactionHandle or handle._issuer is not self._issuer:
            return None
        a = self._transactions.get(handle._key)
        return a if a is not None and a.handle is handle else None

    def _admission(self, handle, allow_failed=False):
        a = self._original_custody(handle)
        if self._closed or a is None or not a.usable:
            return None
        try:
            observed = a.port.observe()
            if allow_failed and observed.state == 'failed':
                observed = replace(observed, state='active')
            if observed != a.observation:
                a.usable = False
                if type(observed) is TransactionObservation and (observed.state == 'idle'
                        or observed.connection_identity != a.observation.connection_identity
                        or observed.transaction_identity != a.observation.transaction_identity):
                    a.refusal_code = 'invalid_transaction'
                return None
        except Exception:
            a.usable = False
            return None
        return a

    def _admission_error(self, handle):
        if not self._closed and type(handle) is TransactionHandle and handle._issuer is self._issuer:
            a = self._transactions.get(handle._key)
            if a is not None and a.handle is handle and not a.usable:
                return self._error(a.refusal_code, 'Original transaction observation or completion unresolved')
        return self._error('invalid_transaction', 'Original adopted transaction unavailable')

    def _command(self, a, sql):
        try:
            a.port.control(sql)
            if a.port.observe() != a.observation:
                raise ValueError('Original transaction changed')
        except Exception:
            a.usable = False
            return self._error('transaction_unusable', 'Savepoint completion or original transaction unresolved')
        return Ok(None)

    def savepoint(self, transaction: TransactionHandle) -> Outcome[SavepointHandle]:
        a = self._admission(transaction)
        if a is None:
            return self._admission_error(transaction)
        key = 'truss_' + uuid4().hex
        result = self._command(a, 'SAVEPOINT ' + key)
        if isinstance(result, Error):
            return result
        handle = SavepointHandle(self._issuer, key)
        self._savepoints[key] = (handle, transaction, self._ordinal)
        self._ordinal += 1
        return Ok(handle)

    def _savepoint_command(self, transaction, savepoint, rollback):
        a = self._admission(transaction, allow_failed=rollback)
        if a is None:
            return self._admission_error(transaction)
        if type(savepoint) is not SavepointHandle:
            return self._error('invalid_transaction', 'Savepoint unavailable')
        entry = self._savepoints.get(savepoint._key)
        if savepoint._issuer is not self._issuer or entry is None or entry[0] is not savepoint or entry[1] is not transaction:
            return self._error('invalid_transaction', 'Foreign or released savepoint')
        result = self._command(a, ('ROLLBACK TO SAVEPOINT ' if rollback else 'RELEASE SAVEPOINT ') + savepoint._key)
        if isinstance(result, Ok):
            for key, candidate in list(self._savepoints.items()):
                if candidate[1] is transaction and (candidate[2] > entry[2] or (not rollback and key == savepoint._key)):
                    del self._savepoints[key]
        return result

    def rollback_to_savepoint(self, transaction, savepoint) -> Outcome[None]:
        return self._savepoint_command(transaction, savepoint, True)

    def release_savepoint(self, transaction, savepoint) -> Outcome[None]:
        return self._savepoint_command(transaction, savepoint, False)

    def dispose(self) -> None:
        """Close admission; retain original custody, including unresolved commands."""
        self._closed = True
