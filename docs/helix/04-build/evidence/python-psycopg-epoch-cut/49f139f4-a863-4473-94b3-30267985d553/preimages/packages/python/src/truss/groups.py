"""Public draft grouped-operation contracts, not callable mutation support.

All facade calls are synchronous. The host transaction owns durability; creating
these values never proves application, namespace authority, replay or commit.
"""
from dataclasses import dataclass, field
from typing import Generic, Literal, Protocol, TypeAlias, TypeVar, overload
from .contracts import ABSENT, Absent, CapabilitySelection, ExactArtifact, ExactValue, ProfilePin, TypedIdentity, _Carrier
from .execution import Outcome, TransactionHandle

@dataclass(frozen=True, slots=True, kw_only=True)
class StoredObjectReference(_Carrier):
    identity: TypedIdentity
    state: Literal['stored'] = field(default='stored', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class AliasObjectReference(_Carrier):
    alias: str
    state: Literal['alias'] = field(default='alias', init=False)

ObjectReference: TypeAlias = StoredObjectReference | AliasObjectReference

@dataclass(frozen=True, slots=True, kw_only=True)
class AuthoredValue(_Carrier):
    name: str
    value: ExactValue

@dataclass(frozen=True, slots=True, kw_only=True)
class RootlessOwnership(_Carrier):
    state: Literal['rootless'] = field(default='rootless', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class OwnedOwnership(_Carrier):
    root: ObjectReference
    state: Literal['owned'] = field(default='owned', init=False)

OwnershipSelection: TypeAlias = RootlessOwnership | OwnedOwnership

@dataclass(frozen=True, slots=True, kw_only=True)
class NullOrderKey(_Carrier):
    state: Literal['null'] = field(default='null', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class TextOrderKey(_Carrier):
    text: str
    state: Literal['text'] = field(default='text', init=False)

OrderKey: TypeAlias = NullOrderKey | TextOrderKey

@dataclass(frozen=True, slots=True, kw_only=True)
class CreateObject(_Carrier):
    type_definition_pin: str
    values: tuple[AuthoredValue, ...]
    ownership: OwnershipSelection
    alias: str | Absent = ABSENT
    operation: Literal['create_object'] = field(default='create_object', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class CreateEdge(_Carrier):
    relationship_definition_pin: str
    source: ObjectReference
    target: ObjectReference
    values: tuple[AuthoredValue, ...]
    order_key: OrderKey
    alias: str | Absent = ABSENT
    operation: Literal['create_edge'] = field(default='create_edge', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateObject(_Carrier):
    target: ObjectReference
    set: tuple[AuthoredValue, ...]
    unset: tuple[str, ...]
    expected_version: str | Absent = ABSENT
    ownership_change: OwnershipSelection | Absent = ABSENT
    operation: Literal['update_object'] = field(default='update_object', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class EndpointChange(_Carrier):
    source: ObjectReference
    target: ObjectReference

@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateEdge(_Carrier):
    target: ObjectReference
    set: tuple[AuthoredValue, ...]
    unset: tuple[str, ...]
    expected_version: str | Absent = ABSENT
    endpoint_change: EndpointChange | Absent = ABSENT
    order_key_change: OrderKey | Absent = ABSENT
    operation: Literal['update_edge'] = field(default='update_edge', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class Delete(_Carrier):
    operation: Literal['delete_object', 'delete_edge']
    target: ObjectReference
    expected_version: str | Absent = ABSENT

GroupOperation: TypeAlias = CreateObject | CreateEdge | UpdateObject | UpdateEdge | Delete

@dataclass(frozen=True, slots=True, kw_only=True)
class CurrentCatalog(_Carrier):
    selection: Literal['current'] = field(default='current', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class PinnedCatalog(_Carrier):
    revision: str
    model_bundle_sha256: str
    selection: Literal['pinned'] = field(default='pinned', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class GroupSemanticInput(_Carrier):
    layout_profile: ProfilePin
    mutation_profile: ProfilePin
    value_profile: ProfilePin
    catalog: CurrentCatalog | PinnedCatalog
    operations: tuple[GroupOperation, *tuple[GroupOperation, ...]]
    asserted_origin: ExactValue
    interface_version: Literal['truss-group-input/0.1.0'] = field(default='truss-group-input/0.1.0', init=False)

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if not self.operations:
            raise ValueError('Nonempty original operation order required')

@dataclass(frozen=True, slots=True, kw_only=True)
class RequestIdentity(_Carrier):
    authorized_scope_identity: str
    request_id: str
    claimed_sha256: str | Absent = ABSENT
    input_profile: Literal['truss-group-input/0.1.0'] = field(default='truss-group-input/0.1.0', init=False)
    interface_version: Literal['truss-request-identity/0.1.0'] = field(default='truss-request-identity/0.1.0', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class RequestNone(_Carrier):
    state: Literal['none'] = field(default='none', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class RequestPresent(_Carrier):
    identity: RequestIdentity
    state: Literal['present'] = field(default='present', init=False)

GroupRequestSelection: TypeAlias = RequestNone | RequestPresent

@dataclass(frozen=True, slots=True, kw_only=True)
class JournalEventReference(_Carrier):
    source_epoch: str
    history_profile: str
    xid: str
    seq: str

@dataclass(frozen=True, slots=True, kw_only=True)
class Created(_Carrier):
    operation: Literal['create_object', 'create_edge']
    identity: TypedIdentity
    version: str
    events: tuple[JournalEventReference, *tuple[JournalEventReference, ...]]
    alias: str | Absent = ABSENT
    outcome: Literal['created'] = field(default='created', init=False)

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if not self.events: raise ValueError('Original events required')

@dataclass(frozen=True, slots=True, kw_only=True)
class Changed(_Carrier):
    operation: Literal['update_object', 'update_edge']
    identity: TypedIdentity
    version: str
    events: tuple[JournalEventReference, *tuple[JournalEventReference, ...]]
    outcome: Literal['changed'] = field(default='changed', init=False)

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if not self.events: raise ValueError('Original events required')

@dataclass(frozen=True, slots=True, kw_only=True)
class Unchanged(_Carrier):
    operation: Literal['update_object', 'update_edge']
    identity: TypedIdentity
    version: str
    events: tuple[()] = field(default=(), init=False)
    outcome: Literal['unchanged'] = field(default='unchanged', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class DeletedIdentity(_Carrier):
    identity: TypedIdentity
    deletion_version: str

@dataclass(frozen=True, slots=True, kw_only=True)
class Deleted(_Carrier):
    operation: Literal['delete_object', 'delete_edge']
    identity: TypedIdentity
    deletion_version: str
    deleted: tuple[DeletedIdentity, ...]
    events: tuple[JournalEventReference, *tuple[JournalEventReference, ...]]
    outcome: Literal['deleted'] = field(default='deleted', init=False)

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if not self.events: raise ValueError('Original events required')

OperationResult: TypeAlias = Created | Changed | Unchanged | Deleted

@dataclass(frozen=True, slots=True, kw_only=True)
class AliasIdentity(_Carrier):
    alias: str
    identity: TypedIdentity

@dataclass(frozen=True, slots=True, kw_only=True)
class GroupSemanticResult(_Carrier):
    executed_catalog_revision: str
    layout_profile: ProfilePin
    mutation_profile: ProfilePin
    results: tuple[OperationResult, *tuple[OperationResult, ...]]
    aliases: tuple[AliasIdentity, ...]
    interface_version: Literal['truss-group-result/0.1.0'] = field(default='truss-group-result/0.1.0', init=False)

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if not self.results: raise ValueError('Complete nonempty ordered result required')

@dataclass(frozen=True, slots=True, kw_only=True)
class AppliedPending(_Carrier):
    semantic: GroupSemanticResult
    disposition: Literal['applied'] = field(default='applied', init=False)
    durability: Literal['pending'] = field(default='pending', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class AppliedCommitted(_Carrier):
    semantic: GroupSemanticResult
    disposition: Literal['applied'] = field(default='applied', init=False)
    durability: Literal['committed'] = field(default='committed', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class SameTransactionReplayEvidence(_Carrier):
    observation_profile: ProfilePin
    evidence: ExactArtifact
    basis: Literal['same_transaction'] = field(default='same_transaction', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class CommittedReceiptReplayEvidence(_Carrier):
    observation_profile: ProfilePin
    evidence: ExactArtifact
    basis: Literal['committed_receipt'] = field(default='committed_receipt', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class SameTransactionReplay(_Carrier):
    semantic: GroupSemanticResult
    replay: SameTransactionReplayEvidence
    disposition: Literal['replayed'] = field(default='replayed', init=False)
    durability: Literal['pending'] = field(default='pending', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class CommittedReceiptReplay(_Carrier):
    semantic: GroupSemanticResult
    replay: CommittedReceiptReplayEvidence
    disposition: Literal['replayed'] = field(default='replayed', init=False)
    durability: Literal['committed'] = field(default='committed', init=False)

InTransactionGroupResponse: TypeAlias = AppliedPending | SameTransactionReplay | CommittedReceiptReplay
GroupResponse: TypeAlias = InTransactionGroupResponse | AppliedCommitted
CommittedGroupResponse: TypeAlias = AppliedCommitted | CommittedReceiptReplay
Response = TypeVar('Response', bound=InTransactionGroupResponse, covariant=True)

@dataclass(frozen=True, slots=True, kw_only=True)
class GroupSuccess(_Carrier, Generic[Response]):
    response: Response
    outcome: Literal['success'] = field(default='success', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class GroupOperationFailure(_Carrier):
    operation_index: str
    error_profile: ProfilePin
    inner_error: ExactArtifact
    code: Literal['group_failed'] = field(default='group_failed', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class InvalidGroupInput(_Carrier):
    diagnostic_profile: ProfilePin
    diagnostic: ExactArtifact
    code: Literal['invalid'] = field(default='invalid', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class RequestConflict(_Carrier):
    diagnostic_profile: ProfilePin
    diagnostic: ExactArtifact
    code: Literal['request_conflict'] = field(default='request_conflict', init=False)

Failure = TypeVar('Failure', bound=GroupOperationFailure | InvalidGroupInput | RequestConflict, covariant=True)

@dataclass(frozen=True, slots=True, kw_only=True)
class GroupFailed(_Carrier, Generic[Failure]):
    failure: Failure
    outcome: Literal['failed'] = field(default='failed', init=False)

GroupUnavailableReason: TypeAlias = Literal['profile', 'receipt', 'receipt_expired', 'observation', 'resource']
Reason = TypeVar('Reason', bound=GroupUnavailableReason, covariant=True)

@dataclass(frozen=True, slots=True, kw_only=True)
class GroupUnavailable(_Carrier, Generic[Reason]):
    reason: Reason
    outcome: Literal['unavailable'] = field(default='unavailable', init=False)

RequestFreeGroupApplicationResult: TypeAlias = GroupSuccess[AppliedPending] | GroupFailed[GroupOperationFailure | InvalidGroupInput] | GroupUnavailable[Literal['profile', 'observation', 'resource']]
GroupApplicationResult: TypeAlias = GroupSuccess[InTransactionGroupResponse] | GroupFailed[GroupOperationFailure | InvalidGroupInput | RequestConflict] | GroupUnavailable[GroupUnavailableReason]

class GroupCapability(Protocol):
    """Contract only; providers require separate protected runtime qualification."""
    @property
    def selection(self) -> CapabilitySelection[Literal['group']]: ...

    @overload
    def apply_in_transaction(self, transaction: TransactionHandle, input: GroupSemanticInput,
        request: RequestNone) -> Outcome[RequestFreeGroupApplicationResult]: ...
    @overload
    def apply_in_transaction(self, transaction: TransactionHandle, input: GroupSemanticInput,
        request: RequestPresent) -> Outcome[GroupApplicationResult]: ...
    @overload
    def apply_in_transaction(self, transaction: TransactionHandle, input: GroupSemanticInput,
        request: GroupRequestSelection) -> Outcome[GroupApplicationResult]: ...


def validate_request_result(request: GroupRequestSelection, result: GroupApplicationResult) -> None:
    """Check request/result shape compatibility; never verifies replay authority.

    Capability admission must still verify actual original namespace, input,
    receipt and pending/committed evidence. No lookup or retry is performed here.
    """
    if type(request) not in (RequestNone, RequestPresent) or type(result) not in (GroupSuccess, GroupFailed, GroupUnavailable):
        raise ValueError('Original contract variants required')
    if type(request) is RequestNone:
        if (type(result) is GroupSuccess and type(result.response) is not AppliedPending
            or type(result) is GroupFailed and type(result.failure) is RequestConflict
            or type(result) is GroupUnavailable and result.reason in ('receipt', 'receipt_expired')):
            raise ValueError('Request-free result cannot claim receipt or replay')

__all__ = [
    'StoredObjectReference', 'AliasObjectReference', 'ObjectReference', 'AuthoredValue',
    'RootlessOwnership', 'OwnedOwnership', 'OwnershipSelection', 'NullOrderKey',
    'TextOrderKey', 'OrderKey', 'CreateObject', 'CreateEdge', 'UpdateObject', 'EndpointChange',
    'UpdateEdge', 'Delete', 'GroupOperation', 'CurrentCatalog', 'PinnedCatalog',
    'GroupSemanticInput', 'RequestIdentity', 'RequestNone', 'RequestPresent',
    'GroupRequestSelection', 'JournalEventReference', 'Created', 'Changed', 'Unchanged',
    'DeletedIdentity', 'Deleted', 'OperationResult', 'AliasIdentity', 'GroupSemanticResult',
    'AppliedPending', 'AppliedCommitted', 'SameTransactionReplay', 'CommittedReceiptReplay',
    'SameTransactionReplayEvidence', 'CommittedReceiptReplayEvidence',
    'InTransactionGroupResponse', 'GroupResponse', 'CommittedGroupResponse', 'GroupSuccess',
    'GroupOperationFailure', 'InvalidGroupInput', 'RequestConflict', 'GroupFailed',
    'GroupUnavailable', 'GroupUnavailableReason', 'RequestFreeGroupApplicationResult',
    'GroupApplicationResult', 'GroupCapability', 'validate_request_result',
]
