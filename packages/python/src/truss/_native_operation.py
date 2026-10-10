"""Private reusable caller operation for the selected bounded text profile.

Registered physical statements are qualification inputs, not logical SQL
compilation or protected capability admission. No caller callbacks or retries.
"""
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4
from .execution import Ok, Error, ExecutionFailure
from ._native_pg8000 import NativeBoundaryRefusal, _Ownership
from ._native_arbitration import NativeArbitration, NativeOperationSession
from ._operation_arbitration import Prepared, CompletionDecision
from ._native_result_custody import NativeResultCustody, NativeTextLimits

@dataclass(frozen=True, eq=False)
class RegisteredTextStatement:
    owner: object
    sql: str
    command: str

@dataclass(eq=False)
class _Run:
    transaction: object
    statement: object
    attempt: object = None
    token: object = None
    session: object = None
    gate: object = None
    savepoint: object = None
    baseline: object = None
    stack: tuple = ()
    result: object = None
    completion: object = None

@dataclass(frozen=True, eq=False)
class _Completion:
    producer: object
    run: object
    session: object
    context: object
    generation: object
    token: object
    revision: int
    calls: tuple
    prepared: tuple
    native_state: object
    baseline: tuple
    final_state: tuple
    result_owner: object
    artifact: bytes

class NativeOperationRunner:
    # Individually qualified fixture definitions only. Arbitrary registered SQL
    # can change unobserved settings, invoke functions or fire unknown triggers.
    QUALIFIED_STATEMENTS = {
        'SELECT :value::pg_catalog.text': 'SELECT',
    }
    SETTINGS = ('transaction_isolation', 'transaction_read_only', 'search_path',
        'TimeZone', 'DateStyle', 'IntervalStyle', 'application_name',
        'standard_conforming_strings', 'client_encoding', 'row_security')
    STATE_SQL = 'SELECT session_user::pg_catalog.text, current_user::pg_catalog.text, ' + ', '.join(
        "pg_catalog.current_setting('" + name + "')::pg_catalog.text" for name in SETTINGS)

    def __init__(self, service, *, limits=None):
        if type(service) is not NativeArbitration:
            raise ValueError('Original native arbitration required')
        self.service = service
        self.limits = limits or NativeTextLimits()
        if type(self.limits) is not NativeTextLimits:
            raise ValueError('Original text limits required')
        self._assembly = object()
        self._statements = ()
        self._runs = ()
        self._completions = ()
        self._lock = Lock()
        if service.registry.register(self._assembly) != 'registered':
            raise ValueError('Original assembly registration unavailable')
        with service._lock:
            if getattr(service, '_completion_producer', None) is not None:
                raise ValueError('Original completion producer already registered')
            service._completion_producer = self

    def register(self, sql, command):
        # Trusted composition/qualification registration, never a public SQL API.
        if type(sql) is not str or self.QUALIFIED_STATEMENTS.get(sql) != command:
            raise ValueError('Selected physical text statement required')
        if len(sql) > self.limits.sql_bytes or len(sql.encode('utf-8')) > self.limits.sql_bytes:
            raise ValueError('Bounded SQL required')
        statement = RegisteredTextStatement(self, sql, command)
        with self._lock:
            if len(self._statements) >= 256: raise ValueError('Statement registry exhausted')
            self._statements = (*self._statements, statement)
        return statement

    @staticmethod
    def _error(code, message): return Error(ExecutionFailure(code, message))

    def _profile(self, boundary):
        from pg8000.converters import string_in, string_out, null_out
        from pg8000.core import CoreConnection
        from pg8000.native import Connection
        with boundary._lock:
            con = boundary._connection
            handlers = boundary._original_driver_handlers
            methods = ('handle_ROW_DESCRIPTION', 'handle_DATA_ROW', 'handle_PARAMETER_DESCRIPTION',
                'handle_COMMAND_COMPLETE', 'handle_ERROR_RESPONSE', 'handle_READY_FOR_QUERY',
                'handle_PARAMETER_STATUS', 'handle_NOTICE_RESPONSE', 'handle_NOTIFICATION_RESPONSE')
            exact_handlers = all(any(getattr(h, '__func__', None) is getattr(CoreConnection, name)
                and getattr(h, '__self__', None) is con for h in handlers.values()) for name in methods)
            exact_dispatch = all(con.message_types.get(k) is v for k,v in boundary._original_handlers.items())
            exact_methods = all(getattr(getattr(con, name), '__func__', None) is getattr(CoreConnection, name)
                for name in ('handle_messages', 'send_BIND', 'send_EXECUTE', 'send_DESCRIBE_STATEMENT',
                    'execute_unnamed', 'execute_named', 'prepare_statement'))
            if (not exact_handlers or not exact_dispatch or not exact_methods
                    or getattr(con.run, '__func__', None) is not Connection.run
                    or getattr(con.prepare, '__func__', None) is not Connection.prepare
                    or con.send_PARSE is not boundary._parse_entry
                    or con.close_prepared_statement is not boundary._close_entry
                    or getattr(boundary._original_parse, '__func__', None) is not CoreConnection.send_PARSE
                    or getattr(boundary._original_close, '__func__', None) is not CoreConnection.close_prepared_statement
                    or con._statement_nums or any(p._resource.phase != 'closed' for p in boundary._resources)
                    or con._client_encoding != 'utf8'
                    or con.pg_types[25] is not string_in or con.py_types[str] is not string_out
                    or con.py_types[type(None)] is not null_out
                    or getattr(con.send_BIND, '__func__', None) is not CoreConnection.send_BIND):
                return False
            return True

    def execute(self, transaction, statement, params=None):
        params = {} if params is None else params
        with self._lock:
            if not any(s is statement for s in self._statements):
                return self._error('execution_obligation', 'Original registered statement required')
            if len(self._runs) >= self.service.registry._limits.attempts:
                return self._error('execution_obligation', 'Original run custody exhausted')
            if type(params) is not dict or len(params) > self.limits.parameters:
                return self._error('execution_obligation', 'Bounded exact parameters required')
            encoded = 0
            for name, value in params.items():
                if (type(name) is not str or not name.isascii() or not name.isidentifier()
                        or len(name) > 128 or (value is not None and type(value) is not str)):
                    return self._error('execution_obligation', 'Exact text/NULL parameters required')
                if value is not None:
                    if len(value) > self.limits.parameter_bytes:
                        return self._error('execution_obligation', 'Parameter payload exceeds bound')
                    try:
                        encoded += len(value.encode('utf-8', 'strict'))
                    except UnicodeError:
                        return self._error('execution_obligation', 'Lossless Unicode parameters required')
            if encoded > self.limits.parameter_bytes:
                return self._error('execution_obligation', 'Parameter payload exceeds bound')
            params = dict(params)
            run = _Run(transaction, statement)
            self._runs = (*self._runs, run)
        custody = self.service._executor._original_custody(transaction)
        if custody is None or not custody.usable or self.service._executor._closed:
            return self._error('invalid_transaction', 'Original adopted transaction unavailable')
        from ._native_transactions import NativeTransactionPort
        port = custody.port
        if type(port) is not NativeTransactionPort:
            return self._error('execution_obligation', 'Selected original native port required')
        boundary = port._tracker._boundary
        tracker = port._tracker
        try:
            if not self._profile(boundary):
                return self._error('execution_obligation', 'Selected original text/resource profile unavailable')
            prepared = self.service.registry.prepare(self._assembly, transaction)
            if type(prepared) is not Prepared:
                return self._error('invalid_transaction', 'Original operation preparation refused')
            run.attempt = prepared.attempt
            try:
                run.token = boundary.acquire_operation()
            except NativeBoundaryRefusal:
                self.service.registry.abandon_prepared(run.attempt)
                return self._error('execution_obligation', 'Original native boundary busy or unavailable')
            if not self._profile(boundary):
                self.service.registry.abandon_prepared(run.attempt)
                boundary.release_operation(run.token)
                return self._error('execution_obligation', 'Original profile changed before admission')
            with boundary._lock:
                run.stack = tracker._state.savepoints
            port.bind_operation(run.token)
            run.session = self.service.bind(run.attempt)
            if type(run.session) is not NativeOperationSession:
                from ._operation_arbitration import Refused
                if type(run.session) is Refused:
                    boundary.release_operation(run.token)
                    return self._error('execution_obligation', 'Original operation binding refused')
                return self._error('transaction_unusable', 'Original operation binding unavailable')
            session = run.session
            gate = NativeResultCustody(session, self.limits)
            run.gate = gate
            gate.install()
            # Outbound SQL/parameter copies remain conservatively charged;
            # object/driver/server heap is a separate profile qualification.
            permit = gate.account.reserve(gate, 16 * (len(statement.sql.encode('utf-8')) + encoded + 4096))
            gate.account.allocate(gate, permit, 16 * (len(statement.sql.encode('utf-8')) + encoded + 4096))
            gate.account.terminate(gate, permit)
            gate.expected_command = 'SELECT'
            run.baseline = self._state(run, cleanup=False)
            if (run.baseline[2].replace(' ', '_') != transaction.isolation
                    or ('read_only' if run.baseline[3] == 'on' else 'read_write') != transaction.access_mode):
                raise NativeBoundaryRefusal('Actual original profile changed')
            run.savepoint = tracker.savepoint('truss_op_' + uuid4().hex, token=run.token)
            p = None
            failure = None
            before = boundary.last_call
            try:
                gate.expected_command = statement.command
                p = boundary.prepare(statement.sql, token=run.token)
                before = boundary.last_call
                rows = p.run(token=run.token, **params)
                run.result = Ok(gate.transfer(rows))
                rows = None
            except Exception as error:
                call = boundary.last_call
                native = error is boundary._ready_error and gate.normal_native_error(call)
                unsubmitted = (type(error) is NativeBoundaryRefusal and call is before
                               and not boundary._quarantined and not boundary._calling)
                if not native and not unsubmitted: raise
                state = next((field[1:].decode('ascii') for e in call.events if e.code == b'E'
                    for field in e.payload.split(b'\0') if field[:1] == b'C'), None) if native else None
                failure = (Error(ExecutionFailure('retry', 'Caller transaction retry required',
                    'whole_transaction', state)) if state in ('40001', '40P01') else
                    self._error('execution_obligation', 'Original statement failure contained'))
                # Original ErrorResponse bytes remain in bounded native custody.
                error.__traceback__ = None
                error.__cause__ = None
                error.__context__ = None
            with boundary._lock:
                session.admission_closed = True
            cleanup = session.cleanup_permit
            if failure is not None:
                tracker.rollback_to(run.savepoint, token=run.token, cleanup=cleanup)
            inventory = gate.inventory()
            for owned in inventory:
                if any(e.resource is not None and e.resource[0] == 'execute'
                       and e.resource[1] is owned._resource for e in session.calls):
                    self._close_portal(run, owned)
                self._close_named(run, owned)
            tracker.release(run.savepoint, token=run.token, cleanup=cleanup)
            gate.expected_command = 'SELECT'
            final = self._state(run, cleanup=True)
            if final != run.baseline or tracker._state.savepoints != run.stack:
                raise NativeBoundaryRefusal('Original caller boundary not restored')
            gate.detach()
            with boundary._lock:
                session.cleanup_closed = True
            if failure is not None: run.result = failure
            completion = self._produce(run, final)
            run.completion = completion
            session.completion = completion
            if self.service.release(session) != 'released':
                return self._error('transaction_unusable', 'Original completion remains unresolved')
            return run.result
        except BaseException as error:
            with boundary._lock:
                known = run.session is not None and any(s is run.session for s in boundary._ownership.completed)
                original = next((c for c in self._completions if c.run is run and c.session is run.session), None)
                if original is not None:
                    run.completion = original
                    run.session.completion = original
                produced = original is not None
                if not known and not produced:
                    boundary._quarantined = True
                if run.session is not None and type(run.session) is NativeOperationSession:
                    run.session.admission_closed = True
            if not isinstance(error, Exception): raise
            if known: return run.result
            return self._error('transaction_unusable', 'Original operation requires recovery')

    def _state(self, run, *, cleanup):
        session = run.session
        # A dummy unused parameter selects extended protocol for zero-param SQL.
        rows = self._probe(run, self.STATE_SQL, cleanup=cleanup)
        if (type(rows) is not list or len(rows) != 1 or len(rows[0]) != 12
                or any(type(v) is not str for v in rows[0])):
            raise NativeBoundaryRefusal('Complete original caller state required')
        return tuple(rows[0])

    def _probe(self, run, sql, *, cleanup):
        session = run.session
        probe = object()
        con = session.boundary._connection
        rows = session.boundary._call(lambda: con.run(sql, _truss_extended=''),
            run.token, resource=('probe', probe),
            cleanup=session.cleanup_permit if cleanup else None)
        self._close_probe(run, probe)
        return rows

    def _close_probe(self, run, probe):
        from pg8000.core import CLOSE, PORTAL, STATEMENT, SYNC_MSG, _write, _flush, Context
        con = run.session.boundary._connection
        for kind, code in (('probe_portal_close', PORTAL), ('probe_statement_close', STATEMENT)):
            def close():
                con._send_message(CLOSE, code + b'\0')
                _write(con._sock, SYNC_MSG)
                _flush(con._sock)
                con.handle_messages(Context(None))
            run.session.boundary._call(close, run.token, resource=(kind, probe),
                cleanup=run.session.cleanup_permit)

    def _close_portal(self, run, prepared):
        from pg8000.core import CLOSE, PORTAL, SYNC_MSG, _write, _flush, Context
        con = run.session.boundary._connection
        def close():
            con._send_message(CLOSE, PORTAL + b'\0')
            _write(con._sock, SYNC_MSG)
            _flush(con._sock)
            con.handle_messages(Context(None))
        run.session.boundary._call(close, run.token,
            resource=('portal_close', prepared._resource), cleanup=run.session.cleanup_permit)

    def _close_named(self, run, prepared):
        resource = prepared._resource
        descriptor = ('close', resource)
        def preflight():
            if resource.phase not in ('live', 'unknown') or resource.name is None:
                raise NativeBoundaryRefusal('Original named cleanup custody unavailable')
            resource.close_attempt = descriptor
            resource.phase = 'closing'
        run.session.boundary._call(lambda: run.session.boundary._connection.close_prepared_statement(resource.name),
            run.token, preflight=preflight, resource=descriptor,
            cleanup=run.session.cleanup_permit, on_settled=prepared._close_settled)

    def _produce(self, run, final):
        session = run.session
        boundary = session.boundary
        with self._lock, boundary._lock:
            calls = tuple(e.native_call for e in sorted((*session.calls, *session.cleanup_calls), key=lambda e:e.revision))
            if (not run.gate.detached or not session.cleanup_closed or boundary._calling
                    or boundary._quarantined or any(c is None or not c.capture_complete for c in calls)
                    or not calls or boundary.last_call is not calls[-1]):
                raise NativeBoundaryRefusal('Complete original operation inventory required')
            artifact = b'truss-native-completion/1:' + session.locator + b':' + str(boundary._revision).encode('ascii')
            completion = _Completion(self, run, session, session.context, session.generation,
                session.token, boundary._revision, calls, run.gate.inventory(), boundary._transaction_tracker._state,
                run.baseline, final, run.gate.result_owner, artifact)
            self._completions = (*self._completions, completion)
            return completion

    def verify_completion(self, session, evidence):
        with session.boundary._lock:
            return self._verify_locked(session, evidence)

    def _verify_locked(self, session, evidence):
        completion = session.completion
        boundary = session.boundary
        if (type(completion) is not _Completion or completion.producer is not self
                or not any(c is completion for c in self._completions)
                or completion.session is not session or completion.context is not session.context
                or evidence != completion.artifact or completion.generation is not session.generation
                or completion.token is not session.token or not session.admission_closed
                or not session.cleanup_closed or boundary._calling or boundary._quarantined
                or boundary._operation is not session.token or boundary._operation_ledger is not session
                or boundary._revision != completion.revision or boundary.last_call is not completion.calls[-1]
                or boundary._transaction_tracker._state is not completion.native_state
                or completion.native_state.generation is not session.generation
                or completion.native_state.status != b'T' or session.generation.ended
                or completion.baseline != completion.final_state or not completion.run.gate.detached):
            return None
        return CompletionDecision('caller_idle', session.context, True, True)

    def handback(self, session):
        boundary = session.boundary
        with boundary._lock:
            if any(s is session for s in boundary._ownership.completed):
                return 'released'
            completion = session.completion
            if self._verify_locked(session, completion.artifact) is None:
                raise NativeBoundaryRefusal('Original native handback unconfirmed')
            result = completion.run.result
            if type(result) is Error and result.error.code == 'retry':
                # Original disposition precedes atomic handback, including a
                # lost publication reply. Later callers cannot reuse this G.
                session.context.custody.usable = False
            root = _Ownership(None, None, None, (*boundary._ownership.completed, session))
            boundary._publish_ownership(root)
            return 'released'

    def reconcile(self, run):
        # Original terminal observation only; never replay statements or acquire
        # a new token. Caller can identify this retained run through its host.
        if not any(r is run for r in self._runs):
            return self._error('transaction_unusable', 'Original completion unavailable')
        with self._lock:
            original = next((c for c in self._completions if c.run is run and c.session is run.session), None)
            if original is None:
                return self._error('transaction_unusable', 'Original completion unavailable')
            run.completion = original
            run.session.completion = original
        if self.service.release(run.session) != 'released':
            return self._error('transaction_unusable', 'Original completion unresolved')
        return run.result
