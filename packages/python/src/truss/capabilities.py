"""Typed providers for the implemented native Python profiles.

These are selected operation surfaces, not authority or readiness credentials.
Calls always return through the owning assembly's protected execution path.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping, Generic, Literal, TypeVar
from .contracts import CapabilitySelection, CapabilityFamily, TypedIdentity, MapValue
from decimal import Decimal
from .query import QueryRows,QueryRefused,QueryUnavailable
from .execution import Outcome, TransactionHandle
from .preparation import CatalogDocument, PreparedAcceptance
from .catalog_view import CatalogViewRequest, CatalogViewAvailable, CatalogViewUnavailable
from .reader_catalog import ReaderCatalog, AcceptedDocument, CatalogInvalid, CatalogRefused, CatalogUnavailable
from .object_read import ObjectFound, ObjectNotFound, ObjectReadInvalid, ObjectReadUnavailable, ObjectPage, ObjectPageCursor
from .edge_read import EdgeFound, EdgeNotFound, EdgePage, EdgePageCursor
from .imports import ImportInput, ObjectImportRecord, ImportExecutionResult
from .import_runtime import ImportRuntimeContext
from .groups import AuthoredValue
from .feed import FeedPage, FeedAcknowledged, FeedUnavailable
from .receipt_visibility import ReceiptIncluded, ReceiptVisibilityUnavailable
from .import_source import ImportSourceFound,ImportSourceAbsent,ImportSourceUnavailable
from .history import HistoryEntity,HistoryCursor,HistoryPage,HistoricalRecord,HistoricalDeleted,HistoryUnavailable

from .catalog_results import (CatalogRegistration, CatalogUnchanged, CatalogAcceptanceRefused, CatalogReport)
from .capability_contracts import NativeRuntimeOperations

Family = TypeVar('Family', bound=CapabilityFamily)
Provider = TypeVar('Provider')


@dataclass(frozen=True, slots=True, kw_only=True)
class CapabilityAvailable(Generic[Provider]):
    capability: Provider
    status: Literal['ok'] = field(default='ok', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class _NativeCapability(Generic[Family]):
    selection: CapabilitySelection[Family]
    _assembly: NativeRuntimeOperations = field(repr=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class NativeCatalogCapability(_NativeCapability[Literal['catalog']]):
    """Actual UMF preparation, acceptance, original reports and reader views."""
    def prepare_catalog(self, documents: tuple[CatalogDocument, ...], *, bun_executable: str='bun') -> PreparedAcceptance:
        return self._assembly.prepare_catalog(documents, bun_executable=bun_executable)

    def accept_in_transaction(self, transaction: TransactionHandle, prepared: PreparedAcceptance, *, request_key: str,
                              origin_bytes: bytes=b'{}') -> Outcome[CatalogRegistration | CatalogUnchanged | CatalogAcceptanceRefused]:
        return self._assembly.accept_in_transaction(transaction,prepared,request_key=request_key,origin_bytes=origin_bytes)

    def report_in_transaction(self, transaction: TransactionHandle, revision: int=1) -> Outcome[CatalogReport]:
        return self._assembly.report_in_transaction(transaction,revision)

    def catalog_view_request(self, *, definition_count: str='65536', encoded_bytes: str='16777216') -> CatalogViewRequest:
        return self._assembly.catalog_view_request(definition_count=definition_count,encoded_bytes=encoded_bytes)

    def catalog_view_in_transaction(self, transaction: TransactionHandle, request: CatalogViewRequest) -> Outcome[CatalogViewAvailable | CatalogViewUnavailable]:
        return self._assembly.catalog_view_in_transaction(transaction,request)

    def reader_catalog_in_transaction(self, transaction: TransactionHandle, *, maximum_count: int=65536,
                                      maximum_bytes: int=1048576) -> Outcome[ReaderCatalog | CatalogInvalid | CatalogRefused | CatalogUnavailable]:
        return self._assembly.reader_catalog_in_transaction(transaction,maximum_count=maximum_count,maximum_bytes=maximum_bytes)

    def accepted_document_in_transaction(self, transaction: TransactionHandle, *, document_id: str,
                                        maximum_bytes: int=1048576) -> Outcome[AcceptedDocument | CatalogInvalid | CatalogRefused | CatalogUnavailable]:
        return self._assembly.accepted_document_in_transaction(transaction,document_id=document_id,maximum_bytes=maximum_bytes)


@dataclass(frozen=True,slots=True,kw_only=True)
class NativeDirectReadCapability(_NativeCapability[Literal['direct_read']]):
    """Logical scalar object/key/page and independent relationship reads."""
    def lookup_import_source_in_transaction(self,transaction: TransactionHandle,*,entity: HistoryEntity,
                                            maximum_bytes: int=1048576) -> Outcome[ImportSourceFound | ImportSourceAbsent | ImportSourceUnavailable]:
        return self._assembly.lookup_import_source_in_transaction(transaction,entity=entity,maximum_bytes=maximum_bytes)

    def get_object_in_transaction(self, transaction: TransactionHandle, *, document_id: str,module_id: str,record_id: str,
                                  object_id: int,maximum_bytes: int=1048576) -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        return self._assembly.get_object_in_transaction(transaction,document_id=document_id,module_id=module_id,record_id=record_id,object_id=object_id,maximum_bytes=maximum_bytes)

    def lookup_key_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str,key_id: str,
                                  values: tuple[str,...],maximum_bytes: int=1048576,original_document: bytes | None=None,
                                  bun_executable: str='bun') -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        return self._assembly.lookup_key_in_transaction(transaction,document_id=document_id,module_id=module_id,record_id=record_id,key_id=key_id,
            values=values,maximum_bytes=maximum_bytes,original_document=original_document,bun_executable=bun_executable)

    def page_objects_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str,
                                    limit: int=100,cursor: ObjectPageCursor | None=None,maximum_bytes: int=1048576) -> Outcome[ObjectPage | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        return self._assembly.page_objects_in_transaction(transaction,document_id=document_id,module_id=module_id,record_id=record_id,limit=limit,cursor=cursor,maximum_bytes=maximum_bytes)

    def get_edge_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,relationship_id: str,
                                edge_id: int,maximum_bytes: int=1048576) -> Outcome[EdgeFound | EdgeNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        return self._assembly.get_edge_in_transaction(transaction,document_id=document_id,module_id=module_id,relationship_id=relationship_id,edge_id=edge_id,maximum_bytes=maximum_bytes)

    def page_edges_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,relationship_id: str,
                                  anchor: TypedIdentity,direction: Literal['outgoing','incoming']='outgoing',limit: int=100,
                                  maximum_bytes: int=1048576,continuation: EdgePageCursor | None=None) -> Outcome[EdgePage | EdgeNotFound | ObjectReadInvalid | ObjectReadUnavailable]:
        return self._assembly.page_edges_in_transaction(transaction,document_id=document_id,module_id=module_id,relationship_id=relationship_id,
            anchor=anchor,direction=direction,limit=limit,maximum_bytes=maximum_bytes,continuation=continuation)

    def reached_in_transaction(self,transaction: TransactionHandle,token: str,*,maximum_token_bytes: int=16384,
                               maximum_evidence_bytes: int=1048576) -> Outcome[ReceiptIncluded | ReceiptVisibilityUnavailable]:
        return self._assembly.reached_in_transaction(transaction,token,maximum_token_bytes=maximum_token_bytes,maximum_evidence_bytes=maximum_evidence_bytes)


@dataclass(frozen=True,slots=True,kw_only=True)
class NativeImportCapability(_NativeCapability[Literal['import']]):
    """Host-adopted imports with explicit immutable original document inputs."""
    _documents: tuple[CatalogDocument,...] = field(repr=False)
    _bun_executable: str = field(repr=False)

    def import_context_in_transaction(self,transaction: TransactionHandle) -> Outcome[ImportRuntimeContext]:
        return self._assembly.import_context_in_transaction(transaction)

    def object_import_record_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str,
                                            values: tuple[AuthoredValue,...],source: MapValue | None=None) -> Outcome[ObjectImportRecord]:
        return self._assembly.object_import_record_in_transaction(transaction,document_id=document_id,module_id=module_id,record_id=record_id,values=values,source=source)

    def import_in_transaction(self,transaction: TransactionHandle,input: ImportInput) -> ImportExecutionResult[Literal['host_adopted']]:
        return self._assembly.import_in_transaction(transaction,input,documents=self._documents,bun_executable=self._bun_executable)


@dataclass(frozen=True,slots=True,kw_only=True)
class NativeFeedCapability(_NativeCapability[Literal['feed']]):
    """Complete authority feed and caller-asserted source acknowledgement."""
    def read_feed_in_transaction(self,transaction: TransactionHandle,*,consumer_id: str,maximum_facts: int=4096,
                                 maximum_bytes: int=8388608) -> Outcome[FeedPage | FeedUnavailable]:
        return self._assembly.read_feed_in_transaction(transaction,consumer_id=consumer_id,maximum_facts=maximum_facts,maximum_bytes=maximum_bytes)

    def reread_feed_in_transaction(self,transaction: TransactionHandle,page: FeedPage,*,maximum_facts: int=4096,
                                   maximum_bytes: int=8388608) -> Outcome[FeedPage | FeedUnavailable]:
        return self._assembly.reread_feed_in_transaction(transaction,page,maximum_facts=maximum_facts,maximum_bytes=maximum_bytes)

    def acknowledge_feed_in_transaction(self,transaction: TransactionHandle,page: FeedPage) -> Outcome[FeedAcknowledged | FeedUnavailable]:
        return self._assembly.acknowledge_feed_in_transaction(transaction,page)


@dataclass(frozen=True,slots=True,kw_only=True)
class NativeHistoryCapability(_NativeCapability[Literal['history']]):
    """Complete retained entity groups and their original version images."""
    def page_history_in_transaction(self,transaction: TransactionHandle,*,entity: HistoryEntity,cursor: HistoryCursor | None=None,
                                    maximum_events: int=4096,maximum_bytes: int=8388608) -> Outcome[HistoryPage | HistoryUnavailable]:
        return self._assembly.page_history_in_transaction(transaction,entity=entity,cursor=cursor,maximum_events=maximum_events,maximum_bytes=maximum_bytes)

    def reconstruct_in_transaction(self,transaction: TransactionHandle,*,entity: HistoryEntity,version: int,
                                   maximum_events: int=4096,maximum_bytes: int=8388608) -> Outcome[HistoricalRecord | HistoricalDeleted | HistoryUnavailable]:
        return self._assembly.reconstruct_in_transaction(transaction,entity=entity,version=version,maximum_events=maximum_events,maximum_bytes=maximum_bytes)


@dataclass(frozen=True,slots=True,kw_only=True)
class NativeCompiledExecutionCapability(_NativeCapability[Literal['weft_execution']]):
    """Compile with Weft and execute authorized logical reads on the host transaction."""
    def query_in_transaction(self,transaction: TransactionHandle,*,sql: str,document_ids: tuple[str,...],parameters: Mapping[str,str|int|bool|Decimal] | None=None,
                             maximum_rows: int=1000,maximum_scan_rows: int=10000,maximum_bytes: int=1048576,
                             read_profile: Literal['entity-page','related-entity-page','count-summary'] | None=None) -> Outcome[QueryRows | QueryRefused | QueryUnavailable]:
        return self._assembly.query_in_transaction(transaction,sql=sql,document_ids=document_ids,parameters=parameters,
            maximum_rows=maximum_rows,maximum_scan_rows=maximum_scan_rows,maximum_bytes=maximum_bytes,read_profile=read_profile)
