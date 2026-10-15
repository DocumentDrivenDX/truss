"""Embedding configuration for current-policy query execution.

The host supplies a separate, fresh privileged transaction dedicated to one
query and keeps administrative runtime DDL quiescent. This initial local PG18
profile does not qualify managed databases or an adversarial administrator.
Neither connection is committed, rolled back or closed by Truss.
"""
from dataclasses import dataclass
from .execution import TransactionHandle
from .psycopg_host import PsycopgHost
from ._current_query_originals import CurrentQueryOriginals, prepare_current_query_originals


@dataclass(frozen=True,slots=True)
class CurrentQuerySubjectRegistration:
    installation_id: str
    source_receipt: str
    original_document: bytes
    identity: tuple[str,str,str]
    helper_source: str
    owner_oid: int
    bindings: tuple[tuple[int,str],...]
    status: str = 'pending_commit'


def register_current_query_sources_in_transaction(host,transaction,*,initialize_bytes,accepted_request_bytes,query_originals=None):
    """Retain original sources through a trusted installer; caller settles."""
    from ._current_query_sources import register_current_query_sources_in_transaction as install
    return install(host,transaction,initialize_bytes=initialize_bytes,
                   accepted_request_bytes=accepted_request_bytes,query_originals=query_originals)


def register_current_query_subjects_in_transaction(host,transaction,*,bindings):
    """Enroll native Subjects through a trusted installer; caller settles."""
    from ._current_query_subjects import register_current_query_subjects_in_transaction as install
    return install(host,transaction,bindings=bindings)


@dataclass(frozen=True,slots=True)
class CurrentQueryExecutor:
    host: PsycopgHost
    transaction: TransactionHandle
    subject_registration: CurrentQuerySubjectRegistration
    bun_executable: str = 'bun'

    def __post_init__(self):
        if (type(self.host) is not PsycopgHost or type(self.transaction) is not TransactionHandle
                or type(self.subject_registration) is not CurrentQuerySubjectRegistration
                or type(self.bun_executable) is not str or not self.bun_executable):
            raise ValueError('Original private host/transaction/Subject configuration required')
