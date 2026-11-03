# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public, explicitly selected temporal value contracts.

These immutable DTOs do not select or qualify a native temporal provider. The
ordinary contracts remain closed; callers must use the temporal assembly route
for any future execution of these values.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias

from .contracts import (
    ABSENT,
    Absent,
    ExactValue,
    LocalTimestampValue,
    MapValue,
    SequenceValue,
    ProfilePin,
    QualifiedOwner,
    TypedIdentity,
    _Carrier,
)
from .groups import (
    AuthoredValue as OrdinaryAuthoredValue,
    AliasObjectReference,
    CurrentCatalog,
    OwnershipSelection,
    OwnedOwnership,
    GroupOperation as OrdinaryGroupOperation,
    GroupPrecondition as OrdinaryGroupPrecondition,
    GroupApplicationResult,
    RequestFreeGroupApplicationResult,
    UnauthorizedPerson,
    FrozenGroupRequest,
    InvalidGroupInput,
    ObjectReference,
    PinnedCatalog,
    RequestNone,
    RootlessOwnership,
    StoredObjectReference,
)
from .preparation import CatalogDocument, PreparedAcceptance
from .catalog_results import (
    CatalogAcceptanceRefused, CatalogCASConflict, CatalogDocumentExpectation,
    CatalogRegistration, CatalogUnchanged,
)
from .execution import Outcome, TransactionHandle
from .imports import (
    ImportCatalogPin,
    ImportExecutionResult,
    ObjectImportRecord,
    OwnedObjectImportRecord,
)
from .contracts import BooleanValue, ObjectKeySelection, TextValue
from .object_read import ObjectNotFound, ObjectReadInvalid, ObjectReadRefused, ObjectReadUnavailable
from .history import HistoricalDeleted, HistoricalRecord, HistoryCursor, HistoryEntity, HistoryPage, HistoryUnavailable
from ._group_runtime import _artifact, _bytes, _wire

Value: TypeAlias = ExactValue | LocalTimestampValue
_OrdinaryObjectValue: TypeAlias = str | bool | TextValue | SequenceValue | MapValue | None
_ObjectValue: TypeAlias = _OrdinaryObjectValue | LocalTimestampValue


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthoredValue(_Carrier):
    name: str
    value: Value


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateObject(_Carrier):
    type_definition_pin: str
    values: tuple[AuthoredValue | OrdinaryAuthoredValue, ...]
    ownership: OwnershipSelection
    alias: str | Absent = ABSENT
    operation: Literal["create_object"] = field(default="create_object", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateObject(_Carrier):
    target: ObjectReference
    set: tuple[AuthoredValue | OrdinaryAuthoredValue, ...]
    unset: tuple[str, ...]
    expected_version: str | Absent = ABSENT
    ownership_change: OwnershipSelection | Absent = ABSENT
    operation: Literal["update_object"] = field(default="update_object", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class PropertyEquals(_Carrier):
    id: str
    reason: str
    target: TypedIdentity
    name: str
    value: Value
    condition: Literal["property_equals"] = field(default="property_equals", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class ScalarObject(_Carrier):
    document_id: str
    module_id: str
    record_id: str
    id: int
    type_id: int
    definition_pin: str
    version: int
    catalog_revision: int
    record_revision: int
    created_at: str
    updated_at: str
    values: tuple[tuple[str, _ObjectValue], ...]
    retained: tuple[tuple[str, _OrdinaryObjectValue], ...]
    profile: Literal["truss-python-temporal-scalar-object/0.1"] = field(
        default="truss-python-temporal-scalar-object/0.1", init=False
    )

    @property
    def ownership(self) -> RootlessOwnership:
        return RootlessOwnership()

    @property
    def identity(self) -> TypedIdentity:
        return TypedIdentity(
            id=str(self.id), type_id=str(self.type_id), definition_pin=self.definition_pin,
            owner=QualifiedOwner(document_id=self.document_id, module_id=self.module_id),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class LogicalObject(_Carrier):
    document_id: str
    module_id: str
    record_id: str
    id: int
    type_id: int
    definition_pin: str
    version: int
    catalog_revision: int
    record_revision: int
    created_at: str
    updated_at: str
    values: tuple[tuple[str, _ObjectValue], ...]
    retained: tuple[tuple[str, _OrdinaryObjectValue], ...]
    ownership: OwnedOwnership
    profile: Literal["truss-python-temporal-logical-object/0.1"] = field(
        default="truss-python-temporal-logical-object/0.1", init=False
    )

    @property
    def identity(self) -> TypedIdentity:
        return TypedIdentity(
            id=str(self.id), type_id=str(self.type_id), definition_pin=self.definition_pin,
            owner=QualifiedOwner(document_id=self.document_id, module_id=self.module_id),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectFound(_Carrier):
    object: ScalarObject | LogicalObject
    outcome: Literal["found"] = field(default="found", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectPageCursor(_Carrier):
    original_bytes: bytes = field(repr=False)
    installation_id: str
    source_epoch: str
    release_sha256: str
    document_id: str
    module_id: str
    record_id: str
    type_id: int
    definition_pin: str
    catalog_revision: int
    after_id: int
    value_profile: ProfilePin
    query_abi: ProfilePin
    profile: Literal["truss-python-temporal-object-page/0.1"] = field(
        default="truss-python-temporal-object-page/0.1", init=False
    )


    def __post_init__(self):
        _Carrier.__post_init__(self)
        if type(self.original_bytes) is not bytes or not 1 <= len(self.original_bytes) <= 65536:
            raise ValueError("Original immutable native temporal page cursor bytes required")


@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectPage(_Carrier):
    objects: tuple[ScalarObject | LogicalObject, ...]
    catalog_revision: int
    continuation: ObjectPageCursor | None
    outcome: Literal["page"] = field(default="page", init=False)
    consistency: Literal["live"] = field(default="live", init=False)
    profile: Literal["truss-python-temporal-object-page/0.1"] = field(
        default="truss-python-temporal-object-page/0.1", init=False
    )


GroupOperation: TypeAlias = OrdinaryGroupOperation | CreateObject | UpdateObject
GroupPrecondition: TypeAlias = OrdinaryGroupPrecondition | PropertyEquals


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupSemanticInput(_Carrier):
    layout_profile: ProfilePin
    mutation_profile: ProfilePin
    value_profile: ProfilePin
    catalog: CurrentCatalog | PinnedCatalog
    operations: tuple[GroupOperation, ...]
    asserted_origin: ExactValue
    preconditions: tuple[GroupPrecondition, ...] = ()
    interface_version: Literal["truss-group-temporal-input/0.1.0"] = field(
        default="truss-group-temporal-input/0.1.0", init=False
    )

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if not self.operations:
            raise ValueError("Nonempty original operation order required")


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupRuntimeContext(_Carrier):
    layout_profile: ProfilePin
    mutation_profile: ProfilePin
    value_profile: ProfilePin
    request_fingerprint_profile: ProfilePin
    authorized_scope_identity: str
    source_epoch: str
    history_profile: str
    query_abi: ProfilePin
    release_id: str
    release_sha256: str

    def input(
        self, operations: tuple[GroupOperation, ...], asserted_origin: MapValue, *,
        preconditions: tuple[GroupPrecondition, ...] = (),
    ) -> GroupSemanticInput:
        return GroupSemanticInput(
            layout_profile=self.layout_profile, mutation_profile=self.mutation_profile,
            value_profile=self.value_profile, catalog=CurrentCatalog(), operations=operations,
            asserted_origin=asserted_origin, preconditions=preconditions,
        )

    def request(self, request_id: str) -> RequestPresent:
        return RequestPresent(identity=RequestIdentity(
            authorized_scope_identity=self.authorized_scope_identity, request_id=request_id,
        ))


@dataclass(frozen=True, slots=True, kw_only=True)
class RequestIdentity(_Carrier):
    authorized_scope_identity: str
    request_id: str
    claimed_sha256: str | Absent = ABSENT
    input_profile: Literal["truss-group-temporal-input/0.1.0"] = field(
        default="truss-group-temporal-input/0.1.0", init=False
    )
    interface_version: Literal["truss-request-identity/0.1.0"] = field(
        default="truss-request-identity/0.1.0", init=False
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class RequestPresent(_Carrier):
    identity: RequestIdentity
    state: Literal["present"] = field(default="present", init=False)


GroupRequestSelection: TypeAlias = RequestNone | RequestPresent


@dataclass(frozen=True, slots=True, kw_only=True)
class ImportInput(_Carrier):
    layout_profile: ProfilePin
    import_profile: ProfilePin
    value_profile: ProfilePin
    catalog: ImportCatalogPin
    load_id: str
    asserted_origin: MapValue
    records: tuple[ObjectImportRecord, ...]
    interface_version: Literal["truss-import-temporal-input/0.1.0"] = field(
        default="truss-import-temporal-input/0.1.0", init=False
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class OwnedImportInput(_Carrier):
    layout_profile: ProfilePin
    import_profile: ProfilePin
    value_profile: ProfilePin
    catalog: ImportCatalogPin
    load_id: str
    asserted_origin: MapValue
    records: tuple[OwnedObjectImportRecord, ...]
    interface_version: Literal["truss-owned-import-temporal-input/0.1.0"] = field(
        default="truss-owned-import-temporal-input/0.1.0", init=False
    )


def _validate_object_payload(
    values: tuple[AuthoredValue | OrdinaryAuthoredValue, ...],
    source: MapValue | None,
    root: ObjectKeySelection | None = None,
) -> None:
    if type(values) is not tuple or any(
        type(value) not in (AuthoredValue, OrdinaryAuthoredValue) for value in values
    ):
        raise ValueError("Exact tuple of authored value DTOs required")
    if source is not None and type(source) is not MapValue:
        raise ValueError("Exact source MapValue required")
    if root is not None and type(root) is not ObjectKeySelection:
        raise ValueError("Exact root ObjectKeySelection required")


@dataclass(frozen=True, slots=True, kw_only=True)
class ImportRuntimeContext(_Carrier):
    layout_profile: ProfilePin
    import_profile: ProfilePin
    value_profile: ProfilePin
    payload_profile: ProfilePin
    catalog: ImportCatalogPin
    query_abi: ProfilePin
    release_id: str
    release_sha256: str

    def input(self, records: tuple[ObjectImportRecord, ...], *, load_id: str,
              asserted_origin: MapValue) -> ImportInput:
        return ImportInput(layout_profile=self.layout_profile, import_profile=self.import_profile,
            value_profile=self.value_profile, catalog=self.catalog, load_id=load_id,
            asserted_origin=asserted_origin, records=records)

    def object_payload(self, values: tuple[AuthoredValue | OrdinaryAuthoredValue, ...], *,
                       source: MapValue | None = None) -> ExactArtifact:
        _validate_object_payload(values, source)
        value = {"interfaceVersion": "truss-import-temporal-payload/0.1.0",
                 "kind": "object", "values": _wire(values), "ownership": {"state": "rootless"}}
        if source is not None:
            value["source"] = _wire(source)
        return _artifact(_bytes(value))


@dataclass(frozen=True, slots=True, kw_only=True)
class OwnedImportRuntimeContext(_Carrier):
    layout_profile: ProfilePin
    import_profile: ProfilePin
    value_profile: ProfilePin
    payload_profile: ProfilePin
    catalog: ImportCatalogPin
    query_abi: ProfilePin
    release_id: str
    release_sha256: str

    def input(self, records: tuple[OwnedObjectImportRecord, ...], *, load_id: str,
              asserted_origin: MapValue) -> OwnedImportInput:
        return OwnedImportInput(layout_profile=self.layout_profile, import_profile=self.import_profile,
            value_profile=self.value_profile, catalog=self.catalog, load_id=load_id,
            asserted_origin=asserted_origin, records=records)

    def object_payload(self, values: tuple[AuthoredValue | OrdinaryAuthoredValue, ...], *,
                       root: ObjectKeySelection | None = None,
                       source: MapValue | None = None) -> ExactArtifact:
        _validate_object_payload(values, source, root)
        ownership = {"state": "rootless"} if root is None else {"state": "owned", "root": _wire(root)}
        value = {"interfaceVersion": "truss-owned-import-temporal-payload/0.1.0",
                 "kind": "object", "values": _wire(values), "ownership": ownership}
        if source is not None:
            value["source"] = _wire(source)
        return _artifact(_bytes(value))


class TemporalValues:
    """Inert facade over the temporal operation port owned by the assembly."""

    def __init__(self, assembly: object) -> None:
        self._assembly = assembly

    def _call(self, operation: str, arguments: dict[str, object]) -> Any:
        return self._assembly._temporal_values_operation(operation, arguments)

    def prepare_catalog(
        self, documents: tuple[CatalogDocument, ...], *,
        bun_executable: str = "bun", source_version: str | None = None,
    ) -> PreparedAcceptance:
        return self._call("prepare_catalog", {
            "documents": documents, "bun_executable": bun_executable,
            "source_version": source_version,
        })

    def accept_in_transaction(
        self, transaction: TransactionHandle, prepared: PreparedAcceptance, *,
        request_key: str, origin_bytes: bytes = b"{}", bun_executable: str = "bun",
        expected_revision: int | None = None,
        expected_documents: tuple[CatalogDocumentExpectation, ...] = (),
    ) -> Outcome[CatalogRegistration | CatalogUnchanged | CatalogAcceptanceRefused | CatalogCASConflict]:
        return self._call("accept_in_transaction", {
            "transaction": transaction, "prepared": prepared, "request_key": request_key,
            "origin_bytes": origin_bytes, "bun_executable": bun_executable,
            "expected_revision": expected_revision, "expected_documents": expected_documents,
        })

    def group_context_in_transaction(self, transaction: TransactionHandle) -> Outcome[GroupRuntimeContext | UnauthorizedPerson]:
        return self._call("group_context_in_transaction", {"transaction": transaction})

    def apply_in_transaction(
        self, transaction: TransactionHandle, input: GroupSemanticInput,
        request: GroupRequestSelection, *, documents: tuple[CatalogDocument, ...] = (),
        bun_executable: str = "bun",
    ) -> Outcome[GroupApplicationResult]:
        return self._call("apply_in_transaction", {
            "transaction": transaction, "input": input, "request": request,
            "documents": documents, "bun_executable": bun_executable,
        })

    def dry_run_in_transaction(
        self, transaction: TransactionHandle, input: GroupSemanticInput, *,
        documents: tuple[CatalogDocument, ...] = (),
    ) -> Outcome[RequestFreeGroupApplicationResult]:
        return self._call("dry_run_in_transaction", {
            "transaction": transaction, "input": input, "documents": documents,
        })

    def complete_in_transaction(self, transaction: TransactionHandle) -> object:
        return self._call("complete_in_transaction", {"transaction": transaction})

    def import_context_in_transaction(self, transaction: TransactionHandle) -> Outcome[ImportRuntimeContext | UnauthorizedPerson]:
        return self._call("import_context_in_transaction", {"transaction": transaction})

    def owned_import_context_in_transaction(self, transaction: TransactionHandle) -> Outcome[OwnedImportRuntimeContext]:
        return self._call("owned_import_context_in_transaction", {"transaction": transaction})

    def object_import_record_in_transaction(
        self, transaction: TransactionHandle, *, document_id: str, module_id: str,
        record_id: str, values: tuple[AuthoredValue | OrdinaryAuthoredValue, ...],
        source: MapValue | None = None,
    ) -> Outcome[ObjectImportRecord]:
        return self._call("object_import_record_in_transaction", {
            "transaction": transaction, "document_id": document_id, "module_id": module_id,
            "record_id": record_id, "values": values, "source": source,
        })

    def owned_object_import_record_in_transaction(
        self, transaction: TransactionHandle, *, document_id: str, module_id: str,
        record_id: str, values: tuple[AuthoredValue | OrdinaryAuthoredValue, ...],
        root: ObjectKeySelection | None = None, source: MapValue | None = None,
    ) -> Outcome[OwnedObjectImportRecord]:
        return self._call("owned_object_import_record_in_transaction", {
            "transaction": transaction, "document_id": document_id, "module_id": module_id,
            "record_id": record_id, "values": values, "root": root, "source": source,
        })

    def import_in_transaction(
        self, transaction: TransactionHandle, input: ImportInput | OwnedImportInput, *,
        documents: tuple[CatalogDocument, ...], bun_executable: str = "bun",
    ) -> ImportExecutionResult[Literal["host_adopted"]]:
        return self._call("import_in_transaction", {
            "transaction": transaction, "input": input, "documents": documents,
            "bun_executable": bun_executable,
        })

    def get_object_in_transaction(
        self, transaction: TransactionHandle, *, document_id: str, module_id: str,
        record_id: str, object_id: int, maximum_bytes: int = 1048576,
    ) -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadRefused | ObjectReadUnavailable]:
        return self._call("get_object_in_transaction", {
            "transaction": transaction, "document_id": document_id, "module_id": module_id,
            "record_id": record_id, "object_id": object_id, "maximum_bytes": maximum_bytes,
        })

    def page_objects_in_transaction(
        self, transaction: TransactionHandle, *, document_id: str, module_id: str,
        record_id: str, limit: int = 100, cursor: ObjectPageCursor | None = None,
        maximum_bytes: int = 1048576,
    ) -> Outcome[ObjectPage | ObjectNotFound | ObjectReadInvalid | ObjectReadRefused | ObjectReadUnavailable]:
        return self._call("page_objects_in_transaction", {
            "transaction": transaction, "document_id": document_id, "module_id": module_id,
            "record_id": record_id, "limit": limit, "cursor": cursor,
            "maximum_bytes": maximum_bytes,
        })

    def lookup_key_in_transaction(
        self, transaction: TransactionHandle, *, document_id: str, module_id: str,
        record_id: str, key_id: str, values: tuple[str | TextValue | BooleanValue, ...],
        original_document: bytes | None = None, maximum_bytes: int = 1048576,
        bun_executable: str = "bun",
    ) -> Outcome[ObjectFound | ObjectNotFound | ObjectReadInvalid | ObjectReadRefused | ObjectReadUnavailable]:
        return self._call("lookup_key_in_transaction", {
            "transaction": transaction, "document_id": document_id, "module_id": module_id,
            "record_id": record_id, "key_id": key_id, "values": values,
            "original_document": original_document, "maximum_bytes": maximum_bytes,
            "bun_executable": bun_executable,
        })

    def page_history_in_transaction(
        self, transaction: TransactionHandle, *, entity: HistoryEntity,
        cursor: HistoryCursor | None = None, maximum_events: int = 4096,
        maximum_bytes: int = 8388608,
    ) -> Outcome[HistoryPage | HistoryUnavailable]:
        return self._call("page_history_in_transaction", {
            "transaction": transaction, "entity": entity, "cursor": cursor,
            "maximum_events": maximum_events, "maximum_bytes": maximum_bytes,
        })

    def reconstruct_in_transaction(
        self, transaction: TransactionHandle, *, entity: HistoryEntity, version: int,
        maximum_events: int = 4096, maximum_bytes: int = 8388608,
    ) -> Outcome[HistoricalRecord | HistoricalDeleted | HistoryUnavailable]:
        return self._call("reconstruct_in_transaction", {
            "transaction": transaction, "entity": entity, "version": version,
            "maximum_events": maximum_events, "maximum_bytes": maximum_bytes,
        })

    def recover_group_request_in_transaction(self, transaction: TransactionHandle, frame: FrozenGroupRequest) -> Outcome[GroupApplicationResult]:
        return self._call("recover_group_request_in_transaction", {
            "transaction": transaction, "frame": frame,
        })


def freeze_group_request(
    input: GroupSemanticInput, request: GroupRequestSelection, *,
    documents: tuple[CatalogDocument, ...],
) -> Outcome[FrozenGroupRequest | InvalidGroupInput]:
    """Freeze only temporal group inputs through the temporal wire owner."""
    from ._temporal_runtime import freeze_group_request as freeze_temporal_group_request
    return freeze_temporal_group_request(input, request, documents=documents)


# Public convenience reexports for signatures and annotations.
__all__ = [
    "ABSENT", "Absent", "AliasObjectReference", "AuthoredValue", "CreateObject",
    "CurrentCatalog", "GroupOperation", "GroupPrecondition", "GroupRequestSelection",
    "GroupRuntimeContext", "GroupSemanticInput", "ImportInput", "ImportRuntimeContext",
    "LocalTimestampValue", "LogicalObject", "ObjectFound", "ObjectPage", "ObjectPageCursor",
    "ObjectReference", "OwnedImportInput", "OwnedImportRuntimeContext", "OwnershipSelection",
    "PinnedCatalog", "ScalarObject",
    "ProfilePin", "PropertyEquals", "RequestIdentity", "RequestPresent",
    "RequestNone", "StoredObjectReference", "TemporalValues", "UpdateObject", "Value",
    "freeze_group_request",
]
