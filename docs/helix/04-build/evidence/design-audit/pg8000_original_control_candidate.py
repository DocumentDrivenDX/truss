"""Trusted original-connection control producer candidate; not a public driver.

Host exclusivity is a premise. This does not authenticate arbitrary Python code,
qualify security/current authority, meter native work, or settle unknown outcomes.
"""
from dataclasses import dataclass
from threading import Lock
from truss._operation_ordinal import OperationOrdinalRegistry
from pg8000_instance_candidate import RawConnection


class OriginalControlConnection(RawConnection):
    def __init__(self, *args, **kwargs):
        self.original_controls = []
        super().__init__(*args, **kwargs)

    def handle_COMMAND_COMPLETE(self, data, context):
        self.original_controls.append(self.original_frame(b'C', data))
        super().handle_COMMAND_COMPLETE(data, context)

    def handle_READY_FOR_QUERY(self, data, context):
        self.original_controls.append(self.original_frame(b'Z', data))
        super().handle_READY_FOR_QUERY(data, context)


@dataclass(frozen=True, slots=True, eq=False)
class ConfirmedSavepoint:
    ordinal: str
    actual_xid: str


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
        self._connection, self._account, self._producer = connection, account, producer
        self._transaction = object()
        self._registry = OperationOrdinalRegistry(producer, connection, 1, maximum_ordinal)
        self._issuer = self._registry.bind(producer, connection, self._transaction)
        self._tickets = {}
        self._attempts = {}
        self._closed = False
        self._lock = Lock()
        try:
            self._xid = self._observe_xid()
            if self._xid is None:
                raise ValueError('Original assigned transaction required')
        except BaseException:
            self._close()
            raise

    def _close(self):
        self._closed = True
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
        self._submit(sql)
        if self._connection.original_controls[start:] != [_frame(b'C', tag + b'\0'), _frame(b'Z', b'T')]:
            raise ValueError('Original command and ready completion required')

    def confirm_savepoint(self):
        if not self._lock.acquire(blocking=False):
            raise ValueError('Original control invocation active')
        try:
            if self._closed:
                raise ValueError('Original control producer closed')
            if self._observe_xid() != self._xid:
                raise ValueError('Original transaction changed')
            # Reserve outgoing savepoint capacity before irreversible issuance.
            permit = self._account.reserve(self._producer, len('SAVEPOINT truss_original_9223372036854775807'))
            issued = self._issuer.reserve(self._transaction)
            if issued.outcome != 'issued':
                self._account.terminate(self._producer, permit)
                raise ValueError('Original ordinal exhausted')
            sql = 'SAVEPOINT truss_original_' + issued.ordinal
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
            ticket = ConfirmedSavepoint(issued.ordinal, self._xid)
            self._tickets[id(ticket)] = [ticket, False]
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
            if self._closed or entry is None or entry[0] is not ticket or entry[1]:
                raise ValueError('Original unconsumed savepoint required')
            entry[1] = True
            if self._observe_xid() != self._xid:
                raise ValueError('Original transaction changed')
            attempt = self._attempts[ticket.ordinal]
            attempt[3] = 'rollback_pending'
            self._control('ROLLBACK TO SAVEPOINT truss_original_' + ticket.ordinal, b'ROLLBACK')
            self._control('RELEASE SAVEPOINT truss_original_' + ticket.ordinal, b'RELEASE')
            if self._observe_xid() != self._xid:
                raise ValueError('Original transaction changed after rollback')
            attempt[3] = 'rolled_back'
        except BaseException:
            if 'attempt' in locals() and attempt[3] == 'rollback_pending':
                attempt[3] = 'rollback_unknown'
            self._close()
            raise
        finally:
            self._lock.release()
