# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit ordinary-role cursor streams and host-owned connection leases.

This profile is synchronous, RC module ACL only; it grants no protected policy
or SDK temporal authority. The lease excludes all raw aliases for its lifetime.
"""
from contextlib import contextmanager
from datetime import timedelta
from dataclasses import dataclass
from math import floor
from .execution import Ok
from .psycopg_host import adopt_psycopg_host

class QueryStreamHandle:
    """Opaque original portal custody; constructing one issues no native rights."""
    __slots__ = ('__weakref__',)

@dataclass(frozen=True,slots=True)
class QueryStreamBatch:
    items: tuple
    exhausted: bool

class QueryStreamTimedOut(TimeoutError):
    def __init__(self,original):
        self.original=original
        super().__init__('Original stream deadline expired with native containment')

class QueryStreamRefused(ValueError):
    def __init__(self, original):
        self.original = original
        super().__init__('Original Truss stream refused; inspect original outcome')

def _success(result):
    if not isinstance(result, Ok):
        raise QueryStreamRefused(result)
    return result.value

def owned_stream_operation(connection_lease, *, configuration=None):
    """Build an explicit stream operation from an exclusive host connection lease.

    connection_lease() must retain exclusive ownership through context exit,
    including time spent by the consumer between yielded pages. A borrowed active
    transaction refuses without SQL or rollback. Unknown cleanup closes the
    connection so the host cannot return it for reuse. No connection is opened.
    """
    if not callable(connection_lease):
        raise TypeError('Exclusive host connection lease required')
    @contextmanager
    def operation(budget):
        import psycopg
        from .catalog_runtime import CatalogRuntimeConfiguration
        from .assembly import create_reference_assembly
        if type(budget) is not timedelta or budget.total_seconds() <= 0:
            raise ValueError('Positive per-page budget required')
        milliseconds = min(60000, max(1, floor(budget.total_seconds()*1000)))
        with connection_lease() as connection:
            if type(connection) is not psycopg.Connection or connection.info.transaction_status != psycopg.pq.TransactionStatus.IDLE:
                raise ValueError('Stream requires an exclusively leased idle connection')
            # Attach first, so an existing original host/quarantine refuses before
            # any BEGIN; the transaction belongs only to this stream context.
            host = adopt_psycopg_host(connection, statement_timeout_ms=milliseconds, operation_timeout_ms=milliseconds)
            entered = False
            try:
                with connection.transaction(force_rollback=True):
                    entered = True
                    connection.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY')
                    transaction = _success(host.adopt_transaction(access_mode='read_only'))
                    assembly = _success(create_reference_assembly(CatalogRuntimeConfiguration() if configuration is None else configuration, host))
                    try:
                        yield assembly, transaction
                    finally:
                        assembly.dispose()
                # Positive rollback and IDLE precede final page publication.
                if connection.info.transaction_status != psycopg.pq.TransactionStatus.IDLE:
                    raise ValueError('Owned stream rollback did not settle')
            except BaseException:
                if entered and (connection.closed or connection.broken or connection.info.transaction_status != psycopg.pq.TransactionStatus.IDLE):
                    connection.close()
                raise
            finally:
                if not host.detach():
                    connection.close()
                    raise ValueError('Stream host quarantined after unresolved operation cleanup')
    return operation
