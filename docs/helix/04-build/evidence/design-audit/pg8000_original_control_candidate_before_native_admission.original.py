"""Trusted original-connection control producer candidate; not a public driver.

Host exclusivity is a premise. This does not authenticate arbitrary Python code,
qualify security/current authority, meter native work, or settle unknown outcomes.
"""
from dataclasses import dataclass
from threading import Lock
from truss._operation_ordinal import OperationOrdinalRegistry
from pg8000_instance_candidate import RawConnection
from pg8000.core import CoreConnection
from pg8000.exceptions import DatabaseError
from pg8000_accounted_instance_candidate import AccountedFrameFile


class OriginalControlConnection(RawConnection):
    def __init__(self, *args, **kwargs):
        self.original_controls = []
        self._native_errors = []
        self._ready_captures = []
        self._ready_status = None
        self._boundary_generation = 0
        self._registered_rollback_sql = None
        self._abort_custody = None
        self._control_lock = Lock()
        self._control_closed = False
        self._operation_binding = None
        self._namespace_next = 0
        self._confirmed_savepoints = {}
        self._control_attempts = {}
        super().__init__(*args, **kwargs)

    def handle_COMMAND_COMPLETE(self, data, context):
        self.original_controls.append(self.original_frame(b'C', data))
        if data == b'COMMIT\0' or (data == b'ROLLBACK\0' and context.statement is not self._registered_rollback_sql):
            self._boundary_generation += 1
        super().handle_COMMAND_COMPLETE(data, context)

    def handle_READY_FOR_QUERY(self, data, context):
        frame = self.original_frame(b'Z', data)
        if data not in (b'I', b'T', b'E'):
            raise ValueError('Original native ready state unavailable')
        if data == b'I' and self._ready_status in (b'T', b'E'):
            self._boundary_generation += 1
        self._ready_status = data
        self._ready_captures.append((context, frame))
        self.original_controls.append(frame)
        super().handle_READY_FOR_QUERY(data, context)


    def handle_ERROR_RESPONSE(self, data, context):
        frame = self.original_frame(b'E', data)
        super().handle_ERROR_RESPONSE(data, context)
        self._native_errors.append((context, context.error, frame))

    def handle_messages(self, context):
        errors_start = len(self._native_errors)
        ready_start = len(self._ready_captures)
        self._abort_custody = None
        try:
            # Original pinned loop/handlers; distinguish only completed native
            # rejection from unavailable protocol/transport completion.
            return CoreConnection.handle_messages(self, context)
        except BaseException as error:
            errors = self._native_errors[errors_start:]
            ready = self._ready_captures[ready_start:]
            if (type(error) is DatabaseError and context.error is error
                    and len(errors) == 1 and errors[0][0] is context
                    and errors[0][1] is error and len(ready) == 1
                    and ready[0][0] is context and ready[0][1] == _frame(b'Z', b'E')
                    and not self._sock.closed):
                self._abort_custody = (context, error, errors[0][2], self._boundary_generation)
                # Only original local containment is eligible. This is not a
                # business/refusal/retry or current-authority classification.
                raise
            self._sock.close()
            raise


@dataclass(frozen=True, slots=True, eq=False)
class ConfirmedSavepoint:
    ordinal: str
    actual_xid: str
    native_name: str


def _frame(kind, body):
    return kind + (len(body) + 4).to_bytes(4, 'big') + body


class OriginalControlProducer:
    """One adopted assigned transaction on one original connection.

    The host must hold exclusive physical connection custody from construction
    through closure. The existing accounted file meters ingress separately.
    This producer charges outgoing SQL UTF-8 payloads before submission; object,
    parser, native work and recovery/containment allocations remain unqualified.
    """
    def __init__(self, connection, account, producer, maximum_ordinal=9223372036854775807):
        if type(connection) is not OriginalControlConnection:
            raise ValueError('Original control connection required')
        if (type(connection._sock) is not AccountedFrameFile
                or connection._sock.account is not account
                or connection._sock.producer is not producer):
            raise ValueError('Original connection/account producer affinity required')
        if type(maximum_ordinal) is not int or not 0 <= maximum_ordinal <= 9223372036854775807:
            raise ValueError('Original exact ordinal profile required')
        self._connection, self._account, self._producer = connection, account, producer
        self._registry = None
        self._tickets = connection._confirmed_savepoints
        self._attempts = connection._control_attempts
        self._closed = False
        self._lock = connection._control_lock
        if not self._lock.acquire(blocking=False):
            raise ValueError('Original control invocation active')
        try:
            if connection._control_closed or connection._ready_status != b'T':
                raise ValueError('Original usable control lifetime required')
            binding = connection._operation_binding
            if binding is None:
                self._xid = self._observe_xid()
                if self._xid is None:
                    raise ValueError('Original assigned transaction required')
                self._boundary_generation = connection._boundary_generation
                self._transaction = object()
                self._registry = OperationOrdinalRegistry(producer, connection, 1, maximum_ordinal)
                self._issuer = self._registry.bind(producer, connection, self._transaction)
                connection._operation_binding = (self._xid, self._boundary_generation,
                    maximum_ordinal, self._transaction, self._registry, self._issuer)
            else:
                if binding[1] != connection._boundary_generation or binding[2] != maximum_ordinal:
                    raise ValueError('Original transaction/profile binding changed')
                (self._xid, self._boundary_generation, _, self._transaction,
                    self._registry, self._issuer) = binding
            if connection._namespace_next > 340282366920938463463374607431768211455:
                raise ValueError('Original participant namespace exhausted')
            # Shared physical-connection participant registry; never random names
            # or a fresh per-facade issuer. Host honors this reserved namespace.
            self._namespace = f'{connection._namespace_next:032x}'
            connection._namespace_next += 1
        except BaseException:
            self._close()
            raise
        finally:
            self._lock.release()

    def _close(self):
        self._closed = True
        self._connection._control_closed = True
        binding = self._connection._operation_binding
        if binding is not None:
            binding[4].close(self._producer)
        elif self._registry is not None:
            self._registry.close(self._producer)
        self._account.close(self._producer)
        # Quarantine admission only; no rollback/termination inferred here.

    def close(self):
        with self._lock:
            self._close()

    def retained_attempts(self, producer):
        with self._lock:
            if producer is not self._producer:
                raise ValueError('Original producer custody required')
            return tuple(tuple(record) for record in self._attempts.values())

    def _submit(self, sql):
        # Maximum fixed statement payload is bounded independently of callers.
        size = len(sql.encode('ascii'))
        permit = self._account.reserve(self._producer, size)
        self._account.allocate(self._producer, permit, size)
        self._account.terminate(self._producer, permit)
        return self._connection.execute_simple(sql)

    def _observe_xid(self):
        start = len(self._connection.original_controls)
        result = self._submit('SELECT pg_catalog.pg_current_xact_id_if_assigned()::text')
        if self._connection.original_controls[start:] != [_frame(b'C', b'SELECT 1\0'), _frame(b'Z', b'T')]:
            raise ValueError('Original transaction control completion required')
        if len(result.rows) != 1 or len(result.rows[0]) != 1:
            raise ValueError('Original transaction cell required')
        value = result.rows[0][0]
        if value is None:
            return None
        if type(value) is not bytes or not value or len(value) > 20 or any(c < 48 or c > 57 for c in value):
            raise ValueError('Exact native xid text required')
        text = value.decode('ascii')
        if (len(text) > 1 and text[0] == '0') or int(text) > 18446744073709551615:
            raise ValueError('Canonical native xid required')
        return text

    def _control(self, sql, tag):
        start = len(self._connection.original_controls)
        if tag == b'ROLLBACK':
            self._connection._registered_rollback_sql = sql
        try:
            self._submit(sql)
        finally:
            self._connection._registered_rollback_sql = None
        if self._connection.original_controls[start:] != [_frame(b'C', tag + b'\0'), _frame(b'Z', b'T')]:
            raise ValueError('Original command and ready completion required')

    def confirm_savepoint(self):
        if not self._lock.acquire(blocking=False):
            raise ValueError('Original control invocation active')
        try:
            if self._closed or self._connection._control_closed:
                raise ValueError('Original control producer closed')
            if (self._connection._boundary_generation != self._boundary_generation
                    or self._connection._ready_status != b'T'):
                raise ValueError('Original usable transaction boundary required')
            if self._observe_xid() != self._xid:
                raise ValueError('Original transaction changed')
            # Reserve outgoing savepoint capacity before irreversible issuance.
            permit = self._account.reserve(self._producer, len('SAVEPOINT truss_sp_' + self._namespace + '_9223372036854775808'))
            issued = self._issuer.reserve(self._transaction)
            if issued.outcome != 'issued':
                self._account.terminate(self._producer, permit)
                raise ValueError('Original ordinal exhausted')
            native_name = 'truss_sp_' + self._namespace + '_' + str(int(issued.ordinal) + 1)
            sql = 'SAVEPOINT ' + native_name
            # Retain original attempt before any control submission can escape.
            attempt = [issued.ordinal, self._xid, sql, 'issued']
            self._attempts[issued.ordinal] = attempt
            self._account.allocate(self._producer, permit, len(sql))
            self._account.terminate(self._producer, permit)
            start = len(self._connection.original_controls)
            attempt[3] = 'submission_pending'
            self._connection.execute_simple(sql)
            if self._connection.original_controls[start:] != [_frame(b'C', b'SAVEPOINT\0'), _frame(b'Z', b'T')]:
                raise ValueError('Original savepoint completion unavailable')
            if self._observe_xid() != self._xid:
                raise ValueError('Original transaction changed after savepoint')
            attempt[3] = 'confirmed'
            ticket = ConfirmedSavepoint(issued.ordinal, self._xid, native_name)
            self._tickets[id(ticket)] = [ticket, False, native_name, issued.ordinal]
            return ticket
        except BaseException:
            if 'attempt' in locals() and attempt[3] == 'submission_pending':
                attempt[3] = 'completion_unknown'
            self._close()
            raise
        finally:
            self._lock.release()

    def rollback_savepoint(self, ticket):
        if not self._lock.acquire(blocking=False):
            raise ValueError('Original control invocation active')
        try:
            entry = self._tickets.get(id(ticket))
            if self._closed or self._connection._control_closed or entry is None or entry[0] is not ticket or entry[1]:
                raise ValueError('Original unconsumed savepoint required')
            entry[1] = True
            if self._connection._boundary_generation != self._boundary_generation:
                raise ValueError('Original transaction boundary changed')
            state = self._connection._ready_status
            if state == b'E':
                abort = self._connection._abort_custody
                if abort is None or abort[3] != self._boundary_generation:
                    raise ValueError('Original completed native rejection required')
                # No identity/restoration/release SQL into the aborted transaction.
            elif state != b'T' or self._observe_xid() != self._xid:
                raise ValueError('Original transaction unavailable or changed')
            ordinal, native_name = entry[3], entry[2]
            attempt = self._attempts[ordinal]
            attempt[3] = 'rollback_pending'
            self._control('ROLLBACK TO SAVEPOINT ' + native_name, b'ROLLBACK')
            if self._observe_xid() != self._xid:
                raise ValueError('Original transaction changed after rollback-to')
            for descendant in self._tickets.values():
                if not descendant[1] and int(descendant[3]) > int(ordinal):
                    descendant[1] = True
                    self._attempts[descendant[3]][3] = 'invalidated_by_ancestor_rollback'
            self._control('RELEASE SAVEPOINT ' + native_name, b'RELEASE')
            if self._observe_xid() != self._xid:
                raise ValueError('Original transaction changed after rollback')
            attempt[3] = 'rolled_back'
        except BaseException:
            if 'attempt' in locals() and attempt[3] == 'rollback_pending':
                attempt[3] = 'rollback_unknown'
                for descendant in self._tickets.values():
                    if not descendant[1] and int(descendant[3]) > int(ordinal):
                        self._attempts[descendant[3]][3] = 'ancestor_rollback_unknown'
            self._close()
            raise
        finally:
            self._lock.release()
