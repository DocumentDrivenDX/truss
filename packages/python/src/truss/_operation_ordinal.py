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


class OperationOrdinalIssuer:
    def __init__(self, custody: object, maximum: int = 9223372036854775807):
        if custody is None or type(maximum) is not int or not 0 <= maximum <= 9223372036854775807:
            raise ValueError('Invalid original issuer component')
        self._custody = custody
        self._maximum = maximum
        self._next = 0
        self._closed = False
        self._lock = Lock()

    def reserve(self, original: object) -> OrdinalResult:
        with self._lock:
            if original is not self._custody:
                return OrdinalResult('refused', reason='custody')
            if self._closed:
                return OrdinalResult('refused', reason='closed')
            if self._next > self._maximum:
                return OrdinalResult('refused', reason='exhausted')
            ordinal = str(self._next)
            self._next += 1
            return OrdinalResult('issued', ordinal=ordinal)

    def close(self, original: object):
        with self._lock:
            if original is not self._custody:
                raise ValueError('Original issuer custody required')
            self._closed = True
