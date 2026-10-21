# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit chunked imports; legacy import settlement remains unchanged."""
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal, TypeAlias
from .contracts import ProfilePin, MapValue, TypedIdentity, ExactArtifact, _Carrier
from .imports import ImportCatalogPin, ImportRecordInput
from .groups import AuthoredValue, OrderKey
from .import_runtime import ImportRuntimeContext

BATCH_IMPORT_DEFINITION = ('Batched scalar imports v1: 1024 original records; 128 records per chunk; '
    'whole-input object-before-edge order; per-record containment and original indices; '
    'skip before payload decoding; caller pending or explicit engine chunk settlement; '
    'exact source and current whole-report authority; bounded input report and transaction work.')
BATCH_IMPORT_PROFILE = ProfilePin(identity='truss-batched-scalar-import', version='0.1',
    sha256=sha256(BATCH_IMPORT_DEFINITION.encode('utf8')).hexdigest())


@dataclass(frozen=True, slots=True, kw_only=True)
class BatchedImportInput(_Carrier):
    layout_profile: ProfilePin
    import_profile: ProfilePin
    value_profile: ProfilePin
    catalog: ImportCatalogPin
    load_id: str
    asserted_origin: MapValue
    records: tuple[ImportRecordInput, ...]
    chunk_size: str = '128'
    interface_version: Literal['truss-batched-import-input/0.1.0'] = field(
        default='truss-batched-import-input/0.1.0', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class BatchedImportRuntimeContext:
    layout_profile: ProfilePin
    import_profile: ProfilePin
    value_profile: ProfilePin
    payload_profile: ProfilePin
    catalog: ImportCatalogPin

    def input(self, records: tuple[ImportRecordInput, ...], *, load_id: str,
              asserted_origin: MapValue, chunk_size: int = 128) -> BatchedImportInput:
        if type(chunk_size) is not int or not 1 <= chunk_size <= 128:
            raise ValueError('Chunk size must be an integer from 1 to 128')
        return BatchedImportInput(layout_profile=self.layout_profile, import_profile=self.import_profile,
            value_profile=self.value_profile, catalog=self.catalog, load_id=load_id,
            asserted_origin=asserted_origin, records=records, chunk_size=str(chunk_size))

    def _payloads(self) -> ImportRuntimeContext:
        return ImportRuntimeContext(layout_profile=self.layout_profile, import_profile=self.import_profile,
            value_profile=self.value_profile, payload_profile=self.payload_profile, catalog=self.catalog)

    def object_payload(self, values: tuple[AuthoredValue, ...], *, source: MapValue | None = None) -> ExactArtifact:
        return self._payloads().object_payload(values, source=source)

    def edge_payload(self, values: tuple[AuthoredValue, ...], order_key: OrderKey, *, source: MapValue | None = None) -> ExactArtifact:
        return self._payloads().edge_payload(values, order_key, source=source)


@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectImportDraft(_Carrier):
    document_id: str
    module_id: str
    record_id: str
    values: tuple[AuthoredValue, ...]
    source: MapValue | None = None
    kind: Literal['object'] = field(default='object', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class EdgeImportDraft(_Carrier):
    document_id: str
    module_id: str
    relationship_id: str
    source_endpoint: TypedIdentity
    target_endpoint: TypedIdentity
    values: tuple[AuthoredValue, ...]
    order_key: OrderKey
    source: MapValue | None = None
    kind: Literal['edge'] = field(default='edge', init=False)


ImportRecordDraft: TypeAlias = ObjectImportDraft | EdgeImportDraft

@dataclass(frozen=True, slots=True, kw_only=True)
class BuiltImportRecords(_Carrier):
    context: BatchedImportRuntimeContext
    records: tuple[ImportRecordInput, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class EmptyLoadDisposition(_Carrier):
    """Settlement of an admitted zero-record load, never a fabricated record batch."""
    load_attempt_id: str
    disposition: Literal['pending','committed','rolled_back','commit_unknown','transaction_unresolved']
    evidence: str


@dataclass(frozen=True, slots=True, kw_only=True)
class BatchedImportExecutionResult:
    # Composition preserves the complete legacy tagged result and report contract.
    result: 'ImportExecutionResult'
    empty_load_settlement: EmptyLoadDisposition | None = None

from .imports import ImportExecutionResult
