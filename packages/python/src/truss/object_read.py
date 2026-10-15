"""Public rootless logical identity reads with exact scalars and flat containers."""
from dataclasses import dataclass, field
from typing import Literal
from .contracts import SequenceValue, MapValue, TextValue, TypedIdentity, QualifiedOwner
from .groups import RootlessOwnership

@dataclass(frozen=True, slots=True, kw_only=True)
class ScalarObject:
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
    values: tuple[tuple[str, str | bool | TextValue | SequenceValue | MapValue | None], ...]
    retained: tuple[tuple[str, str | bool | TextValue | SequenceValue | MapValue | None], ...]
    profile: Literal['truss-python-scalar-object/0.4'] = field(default='truss-python-scalar-object/0.4', init=False)

    @property
    def ownership(self) -> RootlessOwnership:
        """Ownership guaranteed by this rootless native read profile."""
        return RootlessOwnership()

    @property
    def identity(self) -> TypedIdentity:
        """Current document-qualified identity usable by object and edge operations."""
        return TypedIdentity(id=str(self.id), type_id=str(self.type_id),
            definition_pin=self.definition_pin,
            owner=QualifiedOwner(document_id=self.document_id, module_id=self.module_id))

@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectFound:
    object: ScalarObject
    outcome: Literal['found'] = field(default='found', init=False)

@dataclass(frozen=True, slots=True)
class ObjectNotFound:
    outcome: Literal['not_found'] = field(default='not_found', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectReadInvalid:
    code: str
    outcome: Literal['invalid'] = field(default='invalid', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectReadUnavailable:
    reason: Literal['profile','resource','observation','context']
    outcome: Literal['unavailable'] = field(default='unavailable', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectPageCursor:
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
    profile: Literal['truss-python-object-page/0.1'] = field(default='truss-python-object-page/0.1', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectPage:
    objects: tuple[ScalarObject, ...]
    catalog_revision: int
    continuation: ObjectPageCursor | None
    outcome: Literal['page'] = field(default='page', init=False)
    consistency: Literal['live'] = field(default='live', init=False)
