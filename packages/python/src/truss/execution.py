"""Python execution outcome contracts; ports are trusted host integrations.

This executor never begins, commits, rolls back or closes a caller transaction.
Native driver ports must independently qualify their original transaction identity,
status and command completion. This module does not grant graph capabilities.
"""
from dataclasses import dataclass, field
from typing import Generic, Literal, Protocol, TypeVar

T = TypeVar('T')
Isolation = Literal['read_committed', 'repeatable_read', 'serializable']
AccessMode = Literal['read_only', 'read_write']

@dataclass(frozen=True)
class ExecutionFailure:
    code: Literal['invalid_transaction', 'retry', 'transaction_unusable',
                  'commit_unknown', 'execution_obligation', 'cancelled']
    message: str
    retry_scope: Literal['none', 'whole_transaction', 'qualified_request_lookup'] = 'none'
    sql_state: str | None = None

    def __post_init__(self):
        scopes = {'retry': {'whole_transaction'},
                  'commit_unknown': {'none', 'qualified_request_lookup'}}
        if self.code not in {'invalid_transaction', 'retry', 'transaction_unusable',
                             'commit_unknown', 'execution_obligation', 'cancelled'}:
            raise ValueError('Unknown execution failure')
        if self.retry_scope not in scopes.get(self.code, {'none'}):
            raise ValueError('Invalid execution retry scope')

@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T
    status: Literal['ok'] = field(default='ok', init=False)

@dataclass(frozen=True)
class Error:
    error: ExecutionFailure
    status: Literal['error'] = field(default='error', init=False)

Outcome = Ok[T] | Error

@dataclass(frozen=True)
class TransactionObservation:
    """Original native identity supplied by a registered trusted driver port."""
    connection_identity: str
    transaction_identity: str
    isolation: Isolation
    access_mode: AccessMode
    state: Literal['active', 'failed', 'idle', 'unknown']

class HostTransactionPort(Protocol):
    def observe(self) -> TransactionObservation:
        """No begin/retry/commit. Observe the same original native connection."""
        ...
    def control(self, sql: str) -> None:
        """Complete the supplied savepoint command or raise; no implicit retry."""
        ...

