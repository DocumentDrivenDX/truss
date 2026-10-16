"""Explicit current disclosure query configuration and tagged V2 results.

This separate local candidate requires its exact reviewed presence wheel. The
ordinary scalar query API and its dependency selection remain unchanged.
"""
from dataclasses import dataclass,field
from typing import Literal
from .execution import TransactionHandle
from .psycopg_host import PsycopgHost
from .current_query import CurrentQuerySubjectRegistration
from ._current_disclosure_originals import CurrentDisclosureOriginals,prepare_current_disclosure_originals


def register_current_disclosure_sources_in_transaction(host,transaction,*,initialize_bytes,accepted_request_bytes,disclosure_originals):
    from ._current_query_sources import register_current_disclosure_sources_in_transaction as install
    return install(host,transaction,initialize_bytes=initialize_bytes,accepted_request_bytes=accepted_request_bytes,
        disclosure_originals=disclosure_originals)



@dataclass(frozen=True,slots=True)
class CurrentDisclosureExecutor:
    host:PsycopgHost
    transaction:TransactionHandle
    subject_registration:CurrentQuerySubjectRegistration
    bun_executable:str='bun'

    def __post_init__(self):
        if (type(self.host) is not PsycopgHost or type(self.transaction) is not TransactionHandle
                or type(self.subject_registration) is not CurrentQuerySubjectRegistration
                or type(self.bun_executable) is not str or not self.bun_executable):
            raise ValueError('Original private host/transaction/Subject configuration required')


@dataclass(frozen=True,slots=True)
class CurrentDisclosureRows:
    """SQL output aliases/positions map into unique columns of the UMF V2 batch.

    batch_json preserves original tagged cells. Private source tuples and the
    structural transport report are never included in this public result.
    """
    columns:tuple[str,...]
    field_indexes:tuple[int,...]
    batch_json:bytes
    catalog_revision:int
    outcome:Literal['disclosure']=field(default='disclosure',init=False)
