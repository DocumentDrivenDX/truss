"""Structural operation contract for the implemented native Python profiles.

The protocol describes callable operations, not readiness, native authority,
or conformance to broader historical/verified-application interfaces.
"""
from typing import Protocol, Literal, Mapping
from .contracts import TypedIdentity, MapValue
from decimal import Decimal
from .query import QueryRows,QueryRefused,QueryUnavailable,QueryPage,QueryPageCursor
from .execution import Outcome, TransactionHandle
from .preparation import CatalogDocument, PreparedAcceptance
from .catalog_view import CatalogViewRequest, CatalogViewAvailable, CatalogViewUnavailable
from .reader_catalog import ReaderCatalog, AcceptedDocument, CatalogInvalid, CatalogRefused, CatalogUnavailable
from .object_read import ObjectFound, ObjectNotFound, ObjectReadInvalid, ObjectReadUnavailable, ObjectPage, ObjectPageCursor
from .edge_read import EdgeFound, EdgeNotFound, EdgePage, EdgePageCursor
from .imports import ImportInput, ObjectImportRecord, EdgeImportRecord, ImportExecutionResult
from .import_runtime import ImportRuntimeContext
from .groups import AuthoredValue, OrderKey
from .feed import FeedAckReceipt,FeedReceiptAcknowledged,FeedAckReconciled,FeedPage, FeedAcknowledged, FeedUnavailable
from .receipt_visibility import ReceiptIncluded, ReceiptVisibilityUnavailable
from .import_source import ImportSourceFound,ImportSourceAbsent,ImportSourceUnavailable
from .history import HistoryEntity,HistoryCursor,HistoryPage,HistoricalRecord,HistoricalDeleted,HistoryUnavailable

from .catalog_results import (CatalogRegistration, CatalogUnchanged, CatalogAcceptanceRefused, CatalogReport)


class NativeRuntimeOperations(Protocol):
    def page_history_in_transaction(self,transaction: TransactionHandle,*,entity: HistoryEntity,cursor: HistoryCursor | None=None,
                                    maximum_events: int=4096,maximum_bytes: int=8388608) -> Outcome[HistoryPage | HistoryUnavailable]: ...

    def reconstruct_in_transaction(self,transaction: TransactionHandle,*,entity: HistoryEntity,version: int,
                                   maximum_events: int=4096,maximum_bytes: int=8388608) -> Outcome[HistoricalRecord | HistoricalDeleted | HistoryUnavailable]: ...

    def prepare_catalog(self, documents: tuple[CatalogDocument, ...], *, bun_executable: str='bun') -> PreparedAcceptance: ...

    def accept_in_transaction(self, transaction: TransactionHandle, prepared: PreparedAcceptance, *, request_key: str,
                                  origin_bytes: bytes=b'{}') -> Outcome[CatalogRegistration | CatalogUnchanged | CatalogAcceptanceRefused]: ...

    def report_in_transaction(self, transaction: TransactionHandle, revision: int=1) -> Outcome[CatalogReport]: ...

    def catalog_view_request(self, *, definition_count: str='65536', encoded_bytes: str='16777216') -> CatalogViewRequest: ...

    def catalog_view_in_transaction(self, transaction: TransactionHandle, request: CatalogViewRequest) -> Outcome[CatalogViewAvailable | CatalogViewUnavailable]: ...

    def reader_catalog_in_transaction(self, transaction: TransactionHandle, *, maximum_count: int=65536,
                                          maximum_bytes: int=1048576) -> Outcome[ReaderCatalog | CatalogInvalid | CatalogRefused | CatalogUnavailable]: ...

    def accepted_document_in_transaction(self, transaction: TransactionHandle, *, document_id: str,
                                            maximum_bytes: int=1048576) -> Outcome[AcceptedDocument | CatalogInvalid | CatalogRefused | CatalogUnavailable]: ...

    def lookup_import_source_in_transaction(self,transaction: TransactionHandle,*,entity: HistoryEntity,
                                            maximum_bytes: int=1048576) -> Outcome[ImportSourceFound | ImportSourceAbsent | ImportSourceUnavailable]: ...

    def get_object_in_transaction(self, transaction: TransactionHandle, *, document_id: str,module_id: str,record_id: str,
                                      object_id: int,maximum_bytes: int=1048576) -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]: ...

    def lookup_key_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str,key_id: str,
                                      values: tuple[str,...],maximum_bytes: int=1048576,original_document: bytes | None=None,
                                      bun_executable: str='bun') -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]: ...

    def page_objects_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str,
                                        limit: int=100,cursor: ObjectPageCursor | None=None,maximum_bytes: int=1048576) -> Outcome[ObjectPage | ObjectNotFound | ObjectReadInvalid | ObjectReadUnavailable]: ...

    def get_edge_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,relationship_id: str,
                                    edge_id: int,maximum_bytes: int=1048576) -> Outcome[EdgeFound | EdgeNotFound | ObjectReadInvalid | ObjectReadUnavailable]: ...

    def page_edges_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,relationship_id: str,
                                      anchor: TypedIdentity,direction: Literal['outgoing','incoming']='outgoing',limit: int=100,
                                      maximum_bytes: int=1048576,continuation: EdgePageCursor | None=None) -> Outcome[EdgePage | EdgeNotFound | ObjectReadInvalid | ObjectReadUnavailable]: ...

    def reached_in_transaction(self,transaction: TransactionHandle,token: str,*,maximum_token_bytes: int=16384,
                                   maximum_evidence_bytes: int=1048576,consumer_id: str | None=None) -> Outcome[ReceiptIncluded | ReceiptVisibilityUnavailable]: ...

    def import_context_in_transaction(self,transaction: TransactionHandle) -> Outcome[ImportRuntimeContext]: ...

    def edge_import_record_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,relationship_id: str,
                                         source_endpoint: TypedIdentity,target_endpoint: TypedIdentity,values: tuple[AuthoredValue,...],
                                         order_key: OrderKey,source: MapValue | None=None) -> Outcome[EdgeImportRecord]: ...

    def object_import_record_in_transaction(self,transaction: TransactionHandle,*,document_id: str,module_id: str,record_id: str,
                                                values: tuple[AuthoredValue,...],source: MapValue | None=None) -> Outcome[ObjectImportRecord]: ...

    def import_in_transaction(self,transaction: TransactionHandle,input: ImportInput,*,documents: tuple[CatalogDocument,...],bun_executable: str='bun') -> ImportExecutionResult[Literal['host_adopted']]: ...

    def read_feed_in_transaction(self,transaction: TransactionHandle,*,consumer_id: str,maximum_facts: int=4096,
                                     maximum_bytes: int=8388608) -> Outcome[FeedPage | FeedUnavailable]: ...

    def reread_feed_in_transaction(self,transaction: TransactionHandle,page: FeedPage,*,maximum_facts: int=4096,
                                   maximum_bytes: int=8388608) -> Outcome[FeedPage | FeedUnavailable]: ...

    def acknowledge_feed_with_receipt_in_transaction(self,transaction: TransactionHandle,page: FeedPage,*,destination_id: str,request_sha256: str,publication_id: str,receipt_bytes: bytes) -> Outcome[FeedReceiptAcknowledged | FeedUnavailable]:
        ...

    def reconcile_feed_ack_in_transaction(self,transaction: TransactionHandle,page: FeedPage,*,destination_id: str,request_sha256: str,publication_id: str,receipt_bytes: bytes) -> Outcome[FeedAckReconciled | FeedUnavailable]:
        ...

    def acknowledge_feed_in_transaction(self,transaction: TransactionHandle,page: FeedPage) -> Outcome[FeedAcknowledged | FeedUnavailable]: ...

    def query_in_transaction(self,transaction: TransactionHandle,*,sql: str,document_ids: tuple[str,...],parameters: Mapping[str,str|int|bool|Decimal] | None=None,
                             maximum_rows: int=1000,maximum_scan_rows: int=10000,maximum_bytes: int=1048576,
                             read_profile: Literal['entity-page','related-entity-page','count-summary','complete-entity'] | None=None) -> Outcome[QueryRows | QueryRefused | QueryUnavailable]: ...

    def query_page_in_transaction(self,transaction: TransactionHandle,*,sql: str,document_ids: tuple[str,...],parameters: Mapping[str,str|int|bool|Decimal] | None=None,
                                  limit: int=100,cursor: QueryPageCursor | None=None,maximum_scan_rows: int=10000,maximum_bytes: int=1048576) -> Outcome[QueryPage | QueryRefused | QueryUnavailable]: ...
