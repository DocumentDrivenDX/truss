"""Private adoption candidate; E06 native arbitration is not yet integrated.

Unit-test ports provide component evidence only. Never advertise these handles
as admitted protected transactions or expose this executor as a public capability.
"""
from dataclasses import dataclass, replace
from uuid import uuid4
from threading import Lock
from ._host_contracts import TransactionHandle, _Adoption
from .execution import HostTransactionPort, TransactionObservation, Isolation, AccessMode, Outcome, Ok, Error, ExecutionFailure

class SavepointHandle:
    def __init__(self, issuer, key):
        self._issuer, self._key = issuer, key

@dataclass(eq=False)
class _SavepointPublication:
    handle: object
    transaction: object
    candidate: dict
    ordinal: int
    success: object
    phase: str = 'prepared'

class HostExecutor:
    """One synchronous executor over explicit trusted ports; no connection pool."""
    def __init__(self):
        self._issuer = object()
        self._transactions = {}
        self._savepoints = {}
        self._savepoint_publications = ()
        self._savepoint_publication_limit = 4096
        self._savepoint_publication_lock = Lock()
        self._closed = False
        self._ordinal = 0
        self._arbitration_service = None
        self._arbitration_registration_lock = Lock()
        self._lifecycle_lock = Lock()
        self._native_claims = ()
        self._native_claim_limit = 4096

    @staticmethod
    def _error(code, message):
        return Error(ExecutionFailure(code, message))

    def adopt_transaction(self, port: HostTransactionPort, *, isolation: Isolation,
                          access_mode: AccessMode) -> Outcome[TransactionHandle]:
        if self._closed:
            return self._error('invalid_transaction', 'Executor disposed')
        if isolation not in ('read_committed', 'repeatable_read', 'serializable') or access_mode not in ('read_only', 'read_write'):
            return self._error('invalid_transaction', 'Unsupported requested transaction profile')
        from ._native_transactions import NativeTransactionPort
        if type(port) is NativeTransactionPort:
            from ._native_adoption import adopt
            return adopt(self, port, isolation=isolation, access_mode=access_mode)
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
               and not self._confirmed_ended(a) for a in self._transactions.values()):
            return self._error('invalid_transaction', 'Connection already adopted')
        key = uuid4().hex
        handle = TransactionHandle(self._issuer, key, isolation, access_mode)
        self._transactions[key] = _Adoption(port, observed, handle)
        return Ok(handle)

    @staticmethod
    def _confirmed_ended(adoption):
        """Native port history only; quarantine/disposal never means ended."""
        check = getattr(adoption.port, '_original_generation_ended', None)
        try:
            return callable(check) and check(adoption.observation.transaction_identity) is True
        except Exception:
            return False

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
        published = getattr(a.port, '_adoption_is_published', None)
        if callable(published) and not published(a):
            a.usable = False
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
        if not self._savepoint_publication_lock.acquire(blocking=False):
            return self._error('execution_obligation','Original executor savepoint publication busy')
        try:
            return self._savepoint(transaction)
        finally:
            self._savepoint_publication_lock.release()

    def _savepoint(self, transaction: TransactionHandle) -> Outcome[SavepointHandle]:
        a = self._admission(transaction)
        if a is None:
            return self._admission_error(transaction)
        if len(self._savepoint_publications)>=self._savepoint_publication_limit:
            return self._error('execution_obligation', 'Savepoint publication retention exhausted')
        preflight=getattr(a.port,'_preflight_control',None)
        if callable(preflight) and not preflight('savepoint'):
            return self._error('execution_obligation','Original native savepoint capacity unavailable')
        key = 'truss_' + uuid4().hex
        handle = SavepointHandle(self._issuer, key)
        candidate = dict(self._savepoints)
        candidate[key] = (handle, transaction, self._ordinal)
        success = Ok(handle)
        publication = _SavepointPublication(handle,transaction,candidate,self._ordinal,success)
        # All handle/map/success custody exists before the first SAVEPOINT.
        self._savepoint_publications = (*self._savepoint_publications,publication)
        self._ordinal += 1
        try:
            result = self._command(a, 'SAVEPOINT ' + key)
        except BaseException:
            publication.phase = 'unresolved'
            a.usable = False
            raise
        if isinstance(result, Error):
            publication.phase = 'unresolved'
            return result
        try:
            self._publish_savepoint_map(candidate)
        except Exception:
            if self._savepoints is not candidate:
                publication.phase = 'unresolved'
                a.usable = False
                return self._error('transaction_unusable', 'Original savepoint publication unresolved')
        except BaseException:
            publication.phase = 'unresolved'
            a.usable = False
            raise
        publication.phase = 'published'
        return success

    def _publish_savepoint_map(self, candidate):
        self._savepoints = candidate

    def _savepoint_command(self, transaction, savepoint, rollback):
        if not self._savepoint_publication_lock.acquire(blocking=False):
            return self._error('execution_obligation','Original executor savepoint publication busy')
        try:
            return self._savepoint_command_locked(transaction,savepoint,rollback)
        finally:
            self._savepoint_publication_lock.release()

    def _savepoint_command_locked(self, transaction, savepoint, rollback):
        a = self._admission(transaction, allow_failed=rollback)
        if a is None:
            return self._admission_error(transaction)
        if type(savepoint) is not SavepointHandle:
            return self._error('invalid_transaction', 'Savepoint unavailable')
        entry = self._savepoints.get(savepoint._key)
        if savepoint._issuer is not self._issuer or entry is None or entry[0] is not savepoint or entry[1] is not transaction:
            return self._error('invalid_transaction', 'Foreign or released savepoint')
        native_live = getattr(a.port, '_savepoint_is_live', None)
        if callable(native_live):
            try:
                live = native_live(savepoint._key) is True
            except Exception:
                return self._error('transaction_unusable', 'Original savepoint observation unavailable')
            if not live:
                return self._error('invalid_transaction', 'Original native savepoint absent or shadowed')
        if len(self._savepoint_publications)>=self._savepoint_publication_limit:
            return self._error('execution_obligation','Savepoint publication retention exhausted')
        preflight=getattr(a.port,'_preflight_control',None)
        if callable(preflight) and not preflight('rollback_to' if rollback else 'release'):
            return self._error('execution_obligation','Original native control capacity unavailable')
        candidate={key:item for key,item in self._savepoints.items()
                   if not (item[1] is transaction and (item[2]>entry[2] or (not rollback and key==savepoint._key)))}
        success=Ok(None)
        publication=_SavepointPublication(savepoint,transaction,candidate,entry[2],success)
        self._savepoint_publications=(*self._savepoint_publications,publication)
        try:
            result=self._command(a,('ROLLBACK TO SAVEPOINT ' if rollback else 'RELEASE SAVEPOINT ')+savepoint._key)
            if isinstance(result,Error):
                publication.phase='unresolved'
                return result
            try:
                self._publish_savepoint_map(candidate)
            except Exception:
                if self._savepoints is not candidate: raise
            publication.phase='published'
            return success
        except BaseException as error:
            publication.phase='unresolved'
            a.usable=False
            if not isinstance(error,Exception): raise
            return self._error('transaction_unusable','Original savepoint publication unresolved')

    def rollback_to_savepoint(self, transaction, savepoint) -> Outcome[None]:
        return self._savepoint_command(transaction, savepoint, True)

    def release_savepoint(self, transaction, savepoint) -> Outcome[None]:
        return self._savepoint_command(transaction, savepoint, False)

    def dispose(self) -> None:
        """Close admission; retain original custody, including unresolved commands."""
        with self._lifecycle_lock:
            self._closed = True
