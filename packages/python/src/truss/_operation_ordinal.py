"""Private counter component; not original transaction/driver/native admission.

One instance belongs to the qualified shared physical-connection/epoch issuer.
Reserve enclosing control/account permits first; submit savepoint after issuance.
"""
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class OrdinalResult:
    outcome: str
    ordinal: str | None = None
    reason: str | None = None


@dataclass(slots=True,eq=False)
class OrdinalReservation:
    candidate: OrdinalResult | None = None
    issuer: object = None

    @property
    def result(self) -> OrdinalResult | None:
        if self.issuer is None:return None
        return self.candidate if any(item is self for item in self.issuer._state[1]) else None


class OperationOrdinalIssuer:
    def __init__(self, custody: object, maximum: int = 9223372036854775807):
        if custody is None or type(maximum) is not int or not 0 <= maximum <= 9223372036854775807:
            raise ValueError('Invalid original issuer component')
        self._custody = custody
        self._maximum = maximum
        self._state = (0,())
        self._closed = False
        self._lock = Lock()

    @property
    def _next(self):return self._state[0]

    def _publish_state(self,state):
        self._state=state

    def reserve(self, original: object) -> OrdinalResult:
        with self._lock:
            if original is not self._custody:
                return OrdinalResult('refused', reason='custody')
            if self._closed:
                return OrdinalResult('refused', reason='closed')
            if self._next > self._maximum:
                return OrdinalResult('refused', reason='exhausted')
            result=OrdinalResult('issued',ordinal=str(self._next))
            next_state=(self._next+1,self._state[1])
            self._publish_state(next_state)
            return result

    def reserve_into(self, original: object, reservation: OrdinalReservation) -> OrdinalResult:
        """Original pre-retained slot preserves issuance after a lost reply."""
        if type(reservation) is not OrdinalReservation:
            raise ValueError('Exact original reservation required')
        with self._lock:
            if original is not self._custody or reservation.issuer is not None:
                return OrdinalResult('refused',reason='custody')
            if self._closed:return OrdinalResult('refused',reason='closed')
            if self._next>self._maximum:return OrdinalResult('refused',reason='exhausted')
            result=OrdinalResult('issued',ordinal=str(self._next))
            next_state=(self._next+1,(*self._state[1],reservation))
            reservation.candidate=result
            reservation.issuer=self
            # One authoritative root simultaneously publishes consumption and issuance.
            self._publish_state(next_state)
            return result

    def close(self, original: object):
        with self._lock:
            if original is not self._custody:
                raise ValueError('Original issuer custody required')
            self._closed = True


class OperationOrdinalRegistry:
    """Trusted adapter registry for original physical connection/transaction tokens.

    Bindings are cumulative and retained, including ended transactions. The host
    must construct one registry per original connection custody; this component
    does not discover native connections, authenticate tokens or reserve accounts.
    """
    def __init__(self, producer, connection, maximum_bindings, maximum_ordinal):
        if producer is None or connection is None or type(maximum_bindings) is not int or maximum_bindings < 1:
            raise ValueError('Original producer, connection and finite binding capacity required')
        if type(maximum_ordinal) is not int or not 0 <= maximum_ordinal <= 9223372036854775807:
            raise ValueError('Native ordinal bound required')
        self._producer = producer
        self._connection = connection
        self._maximum_bindings = maximum_bindings
        self._maximum_ordinal = maximum_ordinal
        self._bindings = {}
        self._closed = False
        self._lock = Lock()

    def bind(self, producer, connection, transaction):
        with self._lock:
            if producer is not self._producer or connection is not self._connection or transaction is None or self._closed:
                raise ValueError('Original open connection/producer custody required')
            existing = self._bindings.get(id(transaction))
            if existing is not None:
                return existing[1]
            if len(self._bindings) >= self._maximum_bindings:
                raise ValueError('Cumulative transaction binding capacity exhausted')
            issuer = OperationOrdinalIssuer(transaction, self._maximum_ordinal)
            self._bindings[id(transaction)] = (transaction, issuer)
            return issuer

    def end(self, producer, connection, transaction):
        with self._lock:
            if producer is not self._producer or connection is not self._connection:
                raise ValueError('Original connection/producer custody required')
            existing = self._bindings.get(id(transaction))
            if existing is None:
                raise ValueError('Original transaction binding required')
            existing[1].close(existing[0])

    def end_if_bound(self, producer, connection, transaction):
        with self._lock:
            if producer is not self._producer or connection is not self._connection:
                raise ValueError('Original connection/producer custody required')
            existing=self._bindings.get(id(transaction))
            if existing is None:return False
            existing[1].close(existing[0])
            return True

    def close(self, producer):
        with self._lock:
            if producer is not self._producer:
                raise ValueError('Original producer custody required')
            self._closed = True
            for transaction, issuer in self._bindings.values():
                issuer.close(transaction)
