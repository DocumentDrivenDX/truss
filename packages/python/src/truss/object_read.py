"""Public logical identity reads; scalar-string profile, not historical DirectRecord."""
from dataclasses import dataclass, field
from typing import Literal

@dataclass(frozen=True, slots=True, kw_only=True)
class ScalarObject:
    document_id: str
    module_id: str
    record_id: str
    id: int
    type_id: int
    version: int
    catalog_revision: int
    record_revision: int
    created_at: str
    updated_at: str
    values: tuple[tuple[str, str | None], ...]
    retained: tuple[tuple[str, str | None], ...]
    profile: Literal['truss-python-scalar-object/0.1'] = field(default='truss-python-scalar-object/0.1', init=False)

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
    reason: Literal['profile','resource','observation']
    outcome: Literal['unavailable'] = field(default='unavailable', init=False)
