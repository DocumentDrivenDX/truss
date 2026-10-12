"""Private inert caller-lifetime contracts; no native or executor dependencies."""
from dataclasses import dataclass
from .execution import HostTransactionPort, TransactionObservation, TransactionHandle

@dataclass
class _Adoption:
    port: HostTransactionPort
    observation: TransactionObservation
    handle: TransactionHandle
    usable: bool = True
    refusal_code: str = "transaction_unusable"
    cancellation: object = None
