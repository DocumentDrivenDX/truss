"""Explicit fresh native host composition; no graph capability or installation.

The selected adapter is pinned pg8000 over a Unix socket. The returned boundary
is owned by the host. Session disposal closes Truss admission, never settles or
closes the host connection. General Executor.execute/with_transaction and
adoption of arbitrary drivers or connections already in a transaction remain
unfinished. adopt_pg8000_host separately supports existing idle selected
connections while preserving caller ownership.
"""
from dataclasses import dataclass
from typing import Protocol,Literal
from .execution import Outcome,TransactionHandle,Isolation,AccessMode
from ._host_call_recovery import CallObservation,CallOutcome

class HostControlObservation(Protocol):
    @property
    def state(self) -> Literal['active','committed','rolled_back','commit_failed']: ...
    @property
    def handback(self) -> Literal['released','quarantined']: ...
    @property
    def sql_state(self) -> str | None: ...

class HostRecovery(Protocol):
    def observe(self, reference: object) -> Outcome[CallObservation]: ...

class _Boundary(Protocol):
    def run(self, sql: str, **parameters: object) -> object: ...

class _Factory(Protocol):
    def close_host(self, boundary: _Boundary, *, retry: bool = False) -> bool: ...

class HostSession(Protocol):
    """Selected host lifecycle surface; this is not the complete Executor."""
    @property
    def recovery(self) -> HostRecovery: ...
    @property
    def last_call_reference(self) -> object | None: ...
    def observe_host_resource_baseline(self) -> Outcome[object]: ...
    def begin(self, *, isolation: Isolation = 'read_committed', access_mode: AccessMode = 'read_write') -> Outcome[HostControlObservation]: ...
    def commit(self) -> Outcome[HostControlObservation]: ...
    def rollback(self) -> Outcome[HostControlObservation]: ...
    def adopt_transaction(self, *, isolation: Isolation = 'read_committed', access_mode: AccessMode = 'read_write', cancellation: object = None) -> Outcome[TransactionHandle]: ...
    def host_savepoint(self, name: str) -> Outcome[object]: ...
    def host_rollback_to_savepoint(self, savepoint: object) -> Outcome[None]: ...
    def host_release_savepoint(self, savepoint: object) -> Outcome[None]: ...
    def savepoint(self, transaction: TransactionHandle) -> Outcome[object]: ...
    def rollback_to_savepoint(self, transaction: TransactionHandle, savepoint: object) -> Outcome[None]: ...
    def release_savepoint(self, transaction: TransactionHandle, savepoint: object) -> Outcome[None]: ...
    def dispose(self) -> None: ...

class HostConnection:
    """Mediated host lifetime; statements assert no lifecycle mutation.

    Raw/dynamic transaction or savepoint SQL violates the coordination contract.
    This is not a SQL parser: unexpected native lifecycle completion quarantines
    after its effects. Use the session's fixed host controls for lifecycle work.
    """
    def __init__(self,boundary: _Boundary,factory: _Factory) -> None:
        self._boundary,self._factory=boundary,factory

    def run_non_lifecycle(self,sql: str,**parameters: object) -> object:
        return self._boundary.run(sql,**parameters)

    def close(self,*,retry: bool = False) -> bool:
        return self._factory.close_host(self._boundary,retry=retry)


@dataclass(frozen=True, slots=True)
class ConnectedHost:
    """Host-owned native connection boundary and complete-call session.

    Call session.observe_host_resource_baseline explicitly before begin. Adoption
    retains caller ownership; commit/rollback belong to the host session. This
    carrier grants no catalog, mutation or query authority.
    """
    connection: HostConnection
    session: HostSession
    _factory: _Factory

    def close(self, *, retry: bool = False) -> bool:
        """Explicit host discard; true means original stream/socket closed."""
        return self.connection.close(retry=retry)


def connect_pg8000_host(*, user: str, database: str, unix_sock: str,
                       timeout: float = 2.0) -> ConnectedHost:
    """Explicit I/O; create one fresh selected connection, never install Truss."""
    from ._native_bootstrap import NativeConnectionFactory
    from ._host_execution import HostExecutor
    from ._native_transactions import NativeTransactions
    from ._native_arbitration import NativeArbitration
    from ._host_control_custody import HostControlCustody
    from ._host_session import NativeHostSession
    factory=NativeConnectionFactory()
    executor=HostExecutor()
    arbitration=NativeArbitration(executor)
    control=HostControlCustody(executor)
    try:
        boundary=factory.connect(user=user,database=database,unix_sock=unix_sock,timeout=timeout)
    except BaseException as primary:
        record=next((r for r in factory._records if r.exposed and r.witness.boundary is not None),None)
        if record is None:raise
        boundary=factory.recover(record)
        try:
            if not factory.close_host(boundary):raise RuntimeError('Original outer construction cleanup unconfirmed')
        except BaseException as cleanup:
            raise HostCompositionFailure(primary,cleanup,boundary,factory) from primary
        raise
    try:
        tracker=NativeTransactions(boundary,mediated_namespace=True)
        session=NativeHostSession(executor,tracker,arbitration,control_producer=control)
        return ConnectedHost(HostConnection(boundary,factory),session,factory)
    except BaseException as primary:
        try:
            if not factory.close_host(boundary):raise RuntimeError('Original host resource cleanup unconfirmed')
        except BaseException as cleanup:
            raise HostCompositionFailure(primary,cleanup,boundary,factory) from primary
        raise

class HostCompositionFailure(RuntimeError):
    """Construction and cleanup failed; original host resource is retained."""
    def __init__(self,primary: BaseException,cleanup: BaseException,connection: _Boundary,factory: _Factory) -> None:
        super().__init__('Host composition failed; connection cleanup unconfirmed')
        self.primary_failure=primary
        self.cleanup_failure=cleanup
        self.connection=connection
        self._factory=factory
