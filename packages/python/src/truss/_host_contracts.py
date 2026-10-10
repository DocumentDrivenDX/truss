"""Private inert caller-lifetime contracts; no native or executor dependencies."""
from dataclasses import dataclass
from .execution import HostTransactionPort, TransactionObservation

class TransactionHandle:
    """Issuer-bound opaque lifetime handle. Public properties are descriptive."""
    def __init__(self, issuer, key, isolation, access_mode):
        self._issuer, self._key = issuer, key
        self.isolation, self.access_mode = isolation, access_mode
        self.ownership = 'caller'

@dataclass
class _Adoption:
    port: HostTransactionPort
    observation: TransactionObservation
    handle: TransactionHandle
    usable: bool = True
    refusal_code: str = "transaction_unusable"
