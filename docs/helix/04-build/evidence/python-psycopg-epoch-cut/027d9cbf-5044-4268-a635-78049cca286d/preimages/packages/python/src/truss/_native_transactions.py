"""Private coordinated native lifecycle; not public E06/protected admission.

Install before host BEGIN. Typed controls retain original generation and ordered
savepoint custody. A port requires an explicit original operation token held
through the COMPLETE HostExecutor call, including its Python publication.
Ordinary SQL is a trusted non-lifecycle assertion; unexpected native lifecycle
completion quarantines after effects. No SQL parser or raw-alias safety claim.
"""
from dataclasses import dataclass, replace
import re
from uuid import uuid4
from .execution import TransactionObservation
from ._native_pg8000 import NativeBoundary, NativeBoundaryRefusal


@dataclass(eq=False)
class _Generation:
    identity: str
    ended: bool = False
    adoption: object = None
    namespaces: tuple = ()


@dataclass(eq=False)
class _SavepointNamespace:
    executor: object
    value: str
    next_counter: int = 1
    issued: tuple = ()


@dataclass(eq=False)
class _IssuedSavepoint:
    name: str
    submitted: bool = False


@dataclass(frozen=True)
class _NativeObservation:
    observation: TransactionObservation
    port: object
    generation: _Generation
    token: object
    call: object
    revision: int
    person: str
    role: str
    xid: str | None


@dataclass(frozen=True, eq=False)
class _Savepoint:
    name: str
    generation: _Generation


@dataclass(frozen=True)
class _State:
    generation: _Generation | None = None
    status: bytes = b'I'
    savepoints: tuple = ()


@dataclass(frozen=True)
class _Control:
    kind: str
    expected: _State
    candidate: _Generation | None = None
    savepoint: _Savepoint | None = None
    chain: bool = False


@dataclass(frozen=True, eq=False)
class _ControlInvocation:
    tracker: object
    control: _Control
    invoke: object
    sql: str


@dataclass(eq=False)
class _ControlInvocationSlot:
    tracker: object
    kind: str
    invocation: object = None
    retired: bool = False


@dataclass(eq=False)
class _ControlRetention:
    controls: object
    records: tuple
    slots: tuple

    def ready(self):
        port = self.controls.port
        return (self.controls.session._reserved_controls is self.controls
                and self.controls.attempt.controls is self.controls
                and all(any(item is record for item in port._control_records) for record in self.records)
                and all(any(item is slot for item in port._tracker._control_invocations) for slot in self.slots))

    def select(self, permit):
        controls = self.controls
        permits = (controls.savepoint_permit, controls.rollback_permit, controls.release_permit)
        index = next((i for i, item in enumerate(permits) if item is permit), None)
        if index is None or not self.ready():
            raise NativeBoundaryRefusal('Original joint control retention required')
        return self.records[index], self.slots[index]


class NativeTransactions:
    def __init__(self, boundary, *, savepoint_limit=256, adoption_limit=256, mediated_namespace=False):
        if type(boundary) is not NativeBoundary or type(savepoint_limit) is not int or savepoint_limit < 1:
            raise ValueError('Original boundary and positive exact limit required')
        if type(adoption_limit) is not int or adoption_limit < 1:
            raise ValueError('Positive exact adoption retention limit required')
        if type(mediated_namespace) is not bool:raise ValueError('Exact namespace selection required')
        self._mediated_namespace=mediated_namespace
        self._adoption_limit = adoption_limit
        self._adoption_custody = ()
        self._boundary = boundary
        self._identity = uuid4().hex
        self._state = _State()
        self._control_invocations = ()
        self._limit = savepoint_limit
        self._cached = None
        self._next_epoch = 1
        from ._native_operation_ordinals import NativeOperationOrdinals
        self._operation_ordinals=NativeOperationOrdinals(self)
        from ._native_epoch_acquisitions import NativeEpochAcquisitions
        self._epoch_acquisitions=NativeEpochAcquisitions(self)
        with boundary._lock:
            if (boundary._transaction_tracker is not None or boundary._calling or
                    boundary._operation is not None or boundary._quarantined or
                    boundary._connection._transaction_status != b'I'):
                raise NativeBoundaryRefusal('Requires original idle unattached lifecycle')
            boundary._transaction_tracker = self

    def _before(self, control):
        if control is not None and (type(control) is not _Control or control.expected is not self._state):
            self._epoch_acquisitions.invalidate('original-lifecycle-preflight-lost')
            raise NativeBoundaryRefusal('Original lifecycle changed before admission')
        self._epoch_acquisitions.before(control)

    def _after(self, control, call):
        before=self._state
        try:
            result=self._after_original(control,call)
            self._epoch_acquisitions.after(control,call,before)
            return result
        except BaseException:
            self._epoch_acquisitions.invalidate('uncertain-native-completion')
            self._operation_ordinals.close_locked()
            raise

    def _after_original(self, control, call):
        # Called with the shared native guard held, before releasing call custody.
        if not call.capture_complete:
            self._boundary._quarantined = True
            self._operation_ordinals.close_locked()
            return
        tags = tuple(e.payload.rstrip(b'\0') for e in call.events if e.code == b'C')
        lifecycle_tags = {b'BEGIN', b'COMMIT', b'ROLLBACK', b'SAVEPOINT', b'RELEASE'}
        state = self._state
        status = call.final_status
        if status not in (b'I', b'T', b'E'):
            raise NativeBoundaryRefusal('Unknown native lifecycle state')
        if control is None:
            if any(tag in lifecycle_tags for tag in tags) or (state.generation is None and status != b'I'):
                raise NativeBoundaryRefusal('Unasserted native lifecycle completion')
            if any(tag == b'SET' for tag in tags):
                self._cached = None
            if state.generation is not None and status == b'I':
                self._operation_ordinals.end_locked(state.generation)
                state.generation.ended = True
                self._state, self._cached = _State(), None
            else:
                self._state = replace(state, status=status)
            return
        if not tags:
            # A native error can terminate the transaction (e.g. deferred COMMIT
            # failure), or retain the failed original generation. It creates no
            # successful savepoint/lifecycle transition.
            if not any(e.code == b'E' for e in call.events):
                raise NativeBoundaryRefusal('Missing original control completion')
            if status == b'I':
                if state.generation is not None:
                    self._operation_ordinals.end_locked(state.generation)
                    state.generation.ended = True
                self._state, self._cached = _State(), None
            elif state.generation is not None:
                self._state = replace(state, status=status)
            else:
                raise NativeBoundaryRefusal('Unrecognized original error generation')
            return
        expected = {'begin': (b'BEGIN',), 'commit': (b'COMMIT', b'ROLLBACK'),
                    'rollback': (b'ROLLBACK',), 'savepoint': (b'SAVEPOINT',),
                    'rollback_to': (b'ROLLBACK',), 'release': (b'RELEASE',)}[control.kind]
        if len(tags) != 1 or tags[0] not in expected:
            raise NativeBoundaryRefusal('Unexpected original control completion')
        if control.kind == 'begin':
            if status != b'T': raise NativeBoundaryRefusal('BEGIN did not preserve active state')
            if state.generation is None:
                self._state = _State(control.candidate, b'T')
                self._cached = None
        elif control.kind in ('commit', 'rollback'):
            if status != (b'T' if control.chain else b'I'):
                raise NativeBoundaryRefusal('End completion did not match original chain selection')
            if state.generation is not None:
                self._operation_ordinals.end_locked(state.generation)
                state.generation.ended = True
            self._state = _State(control.candidate if control.chain else None, status)
            self._cached = None
        else:
            if status != b'T' or state.generation is None:
                raise NativeBoundaryRefusal('Savepoint did not preserve original transaction')
            if control.kind == 'savepoint':
                self._state = replace(state, status=b'T', savepoints=state.savepoints + (control.savepoint,))
            else:
                index = next(i for i, item in enumerate(state.savepoints) if item is control.savepoint)
                keep = index + (1 if control.kind == 'rollback_to' else 0)
                self._state = replace(state, status=b'T', savepoints=state.savepoints[:keep])

    def _control(self, kind, sql, *, token=None, savepoint=None, chain=False, cleanup=None, prepared_savepoint=None, call_permit=None):
        with self._boundary._lock:
            state = self._state
            if kind in ('commit', 'rollback') and state.generation is None:
                raise NativeBoundaryRefusal('No original transaction to end')
            if kind == 'savepoint':
                if state.status != b'T' or len(state.savepoints) >= self._limit:
                    raise NativeBoundaryRefusal('Savepoint unavailable or capacity exhausted')
                if prepared_savepoint is None:
                    savepoint = _Savepoint(savepoint, state.generation)
                elif (type(prepared_savepoint) is _Savepoint and prepared_savepoint.generation is state.generation and prepared_savepoint.name==savepoint):
                    savepoint = prepared_savepoint
                else: raise NativeBoundaryRefusal('Original preallocated savepoint required')
            if kind in ('rollback_to', 'release') and not self._live(savepoint):
                raise NativeBoundaryRefusal('Original savepoint absent or shadowed')
            candidate = None
            if (kind == 'begin' and state.generation is None) or chain:
                if self._next_epoch > 18446744073709551615:
                    raise NativeBoundaryRefusal('Original positive uint64 epoch capacity exhausted')
                epoch = self._next_epoch
                self._next_epoch += 1  # Reservations never rewind on refusal/uncertainty.
                candidate = _Generation(str(epoch))
            control = _Control(kind, state, candidate, savepoint, chain)
            if call_permit is not None:
                if kind not in ('savepoint', 'rollback_to', 'release') or type(savepoint) is not _Savepoint:
                    raise NativeBoundaryRefusal('Fixed reserved control kind required')
                prefix = {'savepoint': 'SAVEPOINT ', 'rollback_to': 'ROLLBACK TO SAVEPOINT ',
                          'release': 'RELEASE SAVEPOINT '}[kind]
                fixed_sql = prefix + self._name(savepoint.name)
                if type(sql) is not str or sql != fixed_sql:
                    raise NativeBoundaryRefusal('Fixed original control SQL required')
                sql = fixed_sql
            invoke = lambda: self._boundary._run_simple(sql)
            if call_permit is not None:
                ledger = self._boundary._operation_ledger
                if (ledger is None or self._boundary._pending_operation_ledger is not ledger
                        or not any(item is ledger for item in self._boundary._native_arbitration_sessions)):
                    raise NativeBoundaryRefusal('Original reserved control session required')
                record, slot = ledger._select_control_retention(call_permit, claimed=True)
                if slot.tracker is not self or slot.kind != kind or slot.invocation is not None or slot.retired:
                    raise NativeBoundaryRefusal('One-use original invocation slot required')
                invocation = _ControlInvocation(self, control, invoke, sql)
                try:
                    self._publish_control_invocation(slot, invocation)
                except BaseException:
                    call_permit.controls.session.admission_closed = True
                    raise
                ledger = self._boundary._operation_ledger
                if (ledger is None or self._boundary._pending_operation_ledger is not ledger
                        or not any(item is ledger for item in self._boundary._native_arbitration_sessions)):
                    raise NativeBoundaryRefusal('Original reserved control session required')
                ledger._bind_reserved_control(call_permit, invocation)
        self._boundary._call(invoke, token, lifecycle=control, cleanup=cleanup, call_permit=call_permit)
        return savepoint if kind == 'savepoint' else None

    def _publish_control_invocation(self, slot, invocation):
        slot.invocation = invocation

    def _publish_invocation_retention(self, candidate):
        self._control_invocations = candidate

    @staticmethod
    def _name(name):
        if type(name) is not str or re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,62}', name) is None:
            raise NativeBoundaryRefusal('Exact untruncated ASCII identifier required')
        return '"' + name + '"'

    def _live(self, savepoint):
        if type(savepoint) is not _Savepoint or savepoint.generation is not self._state.generation:
            return False
        visible = next((item for item in reversed(self._state.savepoints) if item.name == savepoint.name), None)
        return visible is savepoint

    def begin(self, *, isolation='read_committed', access_mode='read_write', token=None):
        isolation_sql = {'read_committed': 'READ COMMITTED', 'repeatable_read': 'REPEATABLE READ', 'serializable': 'SERIALIZABLE'}
        access_sql = {'read_only': 'READ ONLY', 'read_write': 'READ WRITE'}
        if isolation not in isolation_sql or access_mode not in access_sql:
            raise NativeBoundaryRefusal('Unsupported transaction profile')
        return self._control('begin', 'BEGIN ISOLATION LEVEL ' + isolation_sql[isolation] + ' ' + access_sql[access_mode], token=token)

    def commit(self, *, chain=False, token=None):
        if type(chain) is not bool: raise NativeBoundaryRefusal('Exact chain selection required')
        return self._control('commit', 'COMMIT' + (' AND CHAIN' if chain else ''), token=token, chain=chain)

    def rollback(self, *, chain=False, token=None):
        if type(chain) is not bool: raise NativeBoundaryRefusal('Exact chain selection required')
        return self._control('rollback', 'ROLLBACK' + (' AND CHAIN' if chain else ''), token=token, chain=chain)

    def savepoint(self, name, *, token=None):
        if self._mediated_namespace and type(name) is str and name.startswith('truss_sp_'):
            raise NativeBoundaryRefusal('Reserved Truss savepoint namespace')
        return self._control('savepoint', 'SAVEPOINT ' + self._name(name), token=token, savepoint=name)

    def rollback_to(self, savepoint, *, token=None, cleanup=None, call_permit=None):
        if type(savepoint) is not _Savepoint: raise NativeBoundaryRefusal('Original savepoint required')
        return self._control('rollback_to', 'ROLLBACK TO SAVEPOINT ' + self._name(savepoint.name), token=token, savepoint=savepoint, cleanup=cleanup, call_permit=call_permit)

    def release(self, savepoint, *, token=None, cleanup=None, call_permit=None):
        if type(savepoint) is not _Savepoint: raise NativeBoundaryRefusal('Original savepoint required')
        return self._control('release', 'RELEASE SAVEPOINT ' + self._name(savepoint.name), token=token, savepoint=savepoint, cleanup=cleanup, call_permit=call_permit)

    def port(self, token):
        with self._boundary._lock:
            if token is None or token is not self._boundary._operation or self._state.generation is None:
                raise NativeBoundaryRefusal('Original coordinated active operation required')
            return NativeTransactionPort(self, self._state.generation, token)


@dataclass(eq=False)
class _PortControl:
    kind: str
    native_call: object = None
    phase: str = 'prepared'

class NativeTransactionPort:
    def __init__(self, tracker, generation, token):
        self._tracker, self._generation, self._token = tracker, generation, token
        self._savepoints = {}
        self._last_observation = None
        self._last_native_observation = None
        self._pending_savepoint = None
        self._control_records = ()
        self._last_control = None

    def bind_operation(self, token):
        with self._tracker._boundary._lock:
            if token is None or token is not self._tracker._boundary._operation:
                raise NativeBoundaryRefusal('Original operation token required')
            self._token = token

    def _require_scope(self):
        b = self._tracker._boundary
        if b._quarantined or self._token is None or self._token is not b._operation:
            raise NativeBoundaryRefusal('Port requires complete coordinated executor scope')

    def _original_generation_ended(self, identity):
        return identity == self._generation.identity and self._generation.ended

    def _savepoint_is_live(self, name):
        with self._tracker._boundary._lock:
            self._require_scope()
            return self._tracker._live(self._savepoints.get(name))

    def observe(self):
        return self._observe()

    def _observe_for_adoption(self, claim):
        from ._native_adoption import profile_precheck
        refusal = profile_precheck(claim, self)
        return refusal if refusal is not None else self._observe(claim)

    def _observe(self, claim=None):
        t = self._tracker
        with t._boundary._lock:
            self._require_scope()
            state = t._state
            if self._generation.ended:
                original = self._last_observation
                if original is None:
                    return TransactionObservation(t._identity, self._generation.identity, 'read_committed', 'read_write', 'idle')
                return replace(original, state='idle')
            if self._generation is not state.generation:
                raise NativeBoundaryRefusal('Original port generation no longer recognized')
            if state.generation is None:
                return TransactionObservation(t._identity, '', 'read_committed', 'read_write', 'idle')
            if state.status == b'E':
                if t._cached is None or t._cached.transaction_identity != state.generation.identity:
                    raise NativeBoundaryRefusal('Original cleanup observation unavailable')
                return replace(t._cached, state='failed')
        completed = []
        def capture(call, rows):
            if not call.capture_complete or call.final_status != b'T' or state.generation is not t._state.generation:
                raise NativeBoundaryRefusal('Original native observation unsettled')
            if len(rows) != 1 or len(rows[0]) != 5:
                raise NativeBoundaryRefusal('Actual transaction observation unavailable')
            isolation, readonly, person, role, xid = rows[0]
            if isolation not in ('read committed', 'repeatable read', 'serializable') or readonly not in ('on', 'off'):
                raise NativeBoundaryRefusal('Actual profile unsupported')
            observation = TransactionObservation(t._identity, state.generation.identity, isolation.replace(' ', '_'), 'read_only' if readonly == 'on' else 'read_write', 'active')
            record = _NativeObservation(observation, self, state.generation, self._token, call, call.revision, person, role, xid)
            completed.append(record)
            self.person, self.role, self.xid = person, role, xid
            t._cached = observation
            self._last_observation = observation
            self._last_native_observation = record
            from ._native_adoption import capture_original
            if claim is not None:
                capture_original(claim, self, record)
        sql = "SELECT pg_catalog.current_setting('transaction_isolation'), pg_catalog.current_setting('transaction_read_only'), session_user::pg_catalog.text, current_user::pg_catalog.text, pg_catalog.pg_current_xact_id_if_assigned()::pg_catalog.text"
        from ._native_adoption import start_probe
        preflight = (lambda: start_probe(claim, self)) if claim is not None else None
        t._boundary._call(lambda: t._boundary._run_simple(sql), self._token, on_complete=capture, preflight=preflight)
        return completed[0].observation

    def _reserve_savepoint_name(self,executor):
        with self._tracker._boundary._lock:
            return self._reserve_savepoint_name_locked(executor)

    def _reserve_savepoint_name_locked(self,executor):
        # Original enclosing producer already holds the native guard.
        t=self._tracker
        if not t._mediated_namespace:return None
        self._require_scope()
        generation=self._generation
        root=generation.adoption
        if root is None or root.current is None or root.current.claim.executor is not executor:
            raise NativeBoundaryRefusal('Original adopted namespace owner required')
        reservation=next((n for n in generation.namespaces if n.executor is executor),None)
        if reservation is None:
            if len(generation.namespaces)>=256:raise NativeBoundaryRefusal('Namespace retention exhausted')
            namespace=uuid4().hex
            if re.fullmatch('[0-9a-f]{32}',namespace) is None or any(n.value==namespace for n in generation.namespaces):
                raise NativeBoundaryRefusal('Unique original namespace required')
            reservation=_SavepointNamespace(executor,namespace)
            generation.namespaces=(*generation.namespaces,reservation)
        if not 1<=reservation.next_counter<=18446744073709551615:
            raise NativeBoundaryRefusal('Savepoint namespace counter exhausted')
        if len(reservation.issued)>=4096:raise NativeBoundaryRefusal('Savepoint name retention exhausted')
        counter=reservation.next_counter
        name='truss_sp_'+reservation.value+'_'+str(counter)
        issued=_IssuedSavepoint(name)
        reservation.issued=(*reservation.issued,issued)
        reservation.next_counter+=1
        return name

    def _adoption_is_published(self, adoption):
        from ._native_adoption import is_published
        with self._tracker._boundary._lock:
            return is_published(self._generation, adoption)

    def _preflight_control(self, kind):
        with self._tracker._boundary._lock:
            self._require_scope()
            if len(self._control_records)>=4096: return False
            if kind=='savepoint' and (self._tracker._state.status!=b'T' or len(self._tracker._state.savepoints)>=self._tracker._limit): return False
            return True

    def _publish_control_retention(self, candidate):
        self._control_records = candidate

    def _publish_savepoint_map(self, candidate):
        self._savepoints = candidate

    def control(self, sql, *, cleanup=None, call_permit=None):
        with self._tracker._boundary._lock:
            self._require_scope()
            if self._generation is not self._tracker._state.generation or self._generation.ended:
                raise NativeBoundaryRefusal('Original port generation ended')
        match = re.fullmatch(r'(SAVEPOINT|ROLLBACK TO SAVEPOINT|RELEASE SAVEPOINT) (truss_[0-9a-f]{32}|truss_sp_[0-9a-f]{32}_[1-9][0-9]{0,19})', sql)
        if match is None: raise NativeBoundaryRefusal('Only exact executor savepoint controls accepted')
        kind, name = match.groups()
        t = self._tracker
        with t._boundary._lock:
            self._require_scope()
            record = None
            if call_permit is not None:
                ledger=t._boundary._operation_ledger
                if (ledger is None or ledger is not t._boundary._pending_operation_ledger
                        or not any(item is ledger for item in t._boundary._native_arbitration_sessions)):
                    raise NativeBoundaryRefusal('Original reserved control session required')
                record, slot = ledger._select_control_retention(call_permit)
                if record.kind != kind or record.phase != 'reserved':
                    raise NativeBoundaryRefusal('One-use original port control required')
            elif len(self._control_records)>=4096:
                raise NativeBoundaryRefusal('Original control retention exhausted')
            if t._mediated_namespace:
                namespace_match=re.fullmatch(r'truss_sp_([0-9a-f]{32})_([1-9][0-9]{0,19})',name)
                if namespace_match is None:
                    raise NativeBoundaryRefusal('Original reserved namespace name required')
                value,counter=namespace_match.groups()
                reservation=next((n for n in self._generation.namespaces if n.value==value),None)
                if reservation is None or not 1<=int(counter)<reservation.next_counter or int(counter)>18446744073709551615:
                    raise NativeBoundaryRefusal('Original consumed namespace counter required')
                if kind=='SAVEPOINT':
                    issued=next((r for r in reservation.issued if r.name==name),None)
                    if issued is None or issued.submitted:
                        raise NativeBoundaryRefusal('One-use original savepoint issuance required')
                    issued.submitted=True

            if record is None:
                record=_PortControl(kind)
                self._publish_control_retention((*self._control_records,record))
            else:
                record.phase='prepared'
            self._last_control=record
        before=t._boundary.last_call
        try:
            if kind=='SAVEPOINT':
                original=_Savepoint(name,t._state.generation)
                candidate=dict(self._savepoints)
                candidate[name]=original
                self._pending_savepoint=(original,candidate)
                t._control('savepoint','SAVEPOINT '+t._name(name),token=self._token,
                           savepoint=name,prepared_savepoint=original,cleanup=cleanup,call_permit=call_permit)
                record.native_call=t._boundary.last_call
                try:
                    self._publish_savepoint_map(candidate)
                except Exception:
                    if self._savepoints is not candidate: raise
                self._pending_savepoint=None
            else:
                handle=self._savepoints.get(name)
                if kind=='ROLLBACK TO SAVEPOINT': t.rollback_to(handle,token=self._token,cleanup=cleanup,call_permit=call_permit)
                else: t.release(handle,token=self._token,cleanup=cleanup,call_permit=call_permit)
                record.native_call=t._boundary.last_call
            record.phase='published'
        except BaseException:
            if t._boundary.last_call is not before: record.native_call=t._boundary.last_call
            record.phase='unresolved'
            raise
