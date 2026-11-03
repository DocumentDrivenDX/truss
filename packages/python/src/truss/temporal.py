# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public, explicitly selected temporal value contracts.

These immutable DTOs do not select or qualify a native temporal provider. The
ordinary contracts remain closed; callers must use the temporal assembly route
for any future execution of these values.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from .contracts import (
    ABSENT,
    Absent,
    ExactValue,
    LocalTimestampValue,
    ProfilePin,
    TypedIdentity,
    _Carrier,
)
from .groups import (
    AuthoredValue as OrdinaryAuthoredValue,
    AliasObjectReference,
    CurrentCatalog,
    OwnershipSelection,
    GroupOperation as OrdinaryGroupOperation,
    GroupPrecondition as OrdinaryGroupPrecondition,
    ObjectReference,
    PinnedCatalog,
    StoredObjectReference,
)

Value: TypeAlias = ExactValue | LocalTimestampValue


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


# Public convenience reexports for signatures and annotations.
__all__ = [
    "ABSENT", "Absent", "AliasObjectReference", "AuthoredValue", "CreateObject",
    "CurrentCatalog", "GroupOperation", "GroupPrecondition", "GroupSemanticInput",
    "LocalTimestampValue", "OwnershipSelection", "ObjectReference", "PinnedCatalog",
    "ProfilePin", "PropertyEquals", "RequestIdentity", "RequestPresent",
    "StoredObjectReference", "UpdateObject", "Value",
]
