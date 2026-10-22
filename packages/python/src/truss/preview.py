# SPDX-License-Identifier: MIT OR Apache-2.0
"""Read-only advisory group-condition preview carriers.

Preview reports what one native observation saw. It does not reserve graph
state, issue a mutation receipt, or replace apply-time preconditions.
"""
from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from .contracts import ProfilePin, _Carrier
from .groups import (CurrentCatalog, GroupPrecondition, ObjectExists, KeyAbsent,
                     PropertyEquals, RelationshipAbsent, RelationshipCount)

_CONDITION_TYPES = (ObjectExists, KeyAbsent, PropertyEquals,
                    RelationshipAbsent, RelationshipCount)


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupConditionPreviewInput(_Carrier):
    layout_profile: ProfilePin
    mutation_profile: ProfilePin
    value_profile: ProfilePin
    catalog: CurrentCatalog
    preconditions: tuple[GroupPrecondition, ...]
    interface_version: Literal['truss-group-condition-preview/0.1.0'] = field(
        default='truss-group-condition-preview/0.1.0', init=False)

    def __post_init__(self) -> None:
        _Carrier.__post_init__(self)
        if type(self.preconditions) is not tuple or any(
                type(condition) not in _CONDITION_TYPES for condition in self.preconditions):
            raise ValueError('Exact original condition tuple required')
        if not 1 <= len(self.preconditions) <= 3072:
            raise ValueError('Bounded nonempty condition preview required')
        ids = tuple(condition.id for condition in self.preconditions)
        if len(set(ids)) != len(ids):
            raise ValueError('Unique condition identifiers required')


@dataclass(frozen=True, slots=True, kw_only=True)
class PreviewConditionResult(_Carrier):
    condition_id: str
    rule: Literal['object_exists', 'key_absent', 'property_equals',
                  'relationship_absent', 'relationship_count']
    passed: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class PreviewObservationBasis(_Carrier):
    catalog_revision: str
    snapshot: str
    source_epoch: str
    release_id: str
    release_sha256: str
    layout_profile: ProfilePin
    status: Literal['observed'] = field(default='observed', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class PreviewObserved(_Carrier):
    basis: PreviewObservationBasis
    conditions: tuple[PreviewConditionResult, ...]
    outcome: Literal['observed'] = field(default='observed', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class PreviewRefused(_Carrier):
    reason: Literal['unauthorized', 'invalid_input', 'profile', 'resource', 'context', 'observation']
    outcome: Literal['refused'] = field(default='refused', init=False)


ConditionPreviewResult: TypeAlias = PreviewObserved | PreviewRefused


__all__ = ['GroupConditionPreviewInput', 'PreviewConditionResult',
           'PreviewObservationBasis', 'PreviewObserved', 'PreviewRefused',
           'ConditionPreviewResult']


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationObservationBasis(_Carrier):
    catalog_revision: str
    snapshot: str
    source_epoch: str
    release_id: str
    release_sha256: str
    input_sha256: str | None
    documents_sha256: str | None
    durability: Literal['rolled_back'] = field(default='rolled_back', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionObserved(_Carrier):
    basis: ValidationObservationBasis
    outcome: Literal['completion_observed'] = field(default='completion_observed', init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupValidationObserved(_Carrier):
    basis: ValidationObservationBasis
    operation_count: int
    outcome: Literal['validated'] = field(default='validated', init=False)

__all__ += ['ValidationObservationBasis','CompletionObserved','GroupValidationObserved']
