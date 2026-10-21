# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public person-scoped catalog results and exact accepted source bytes."""
from dataclasses import dataclass, field
from typing import Literal, Any

@dataclass(frozen=True, slots=True)
class CatalogRefused:
    code: Literal['unauthorized'] = 'unauthorized'
    outcome: Literal['refused'] = field(default='refused', init=False)

@dataclass(frozen=True, slots=True)
class CatalogInvalid:
    code: Literal['selection', 'limits']
    outcome: Literal['invalid'] = field(default='invalid', init=False)

@dataclass(frozen=True, slots=True)
class CatalogUnavailable:
    code: Literal['profile', 'resource', 'observation', 'installation']
    outcome: Literal['unavailable'] = field(default='unavailable', init=False)

@dataclass(frozen=True, slots=True)
class ReaderCatalog:
    catalog_revision: int
    layout_profile: dict[str, str]
    modules: tuple[dict[str, Any], ...]
    interface_version: str = 'truss-reader-catalog/0.1'

@dataclass(frozen=True, slots=True)
class ReaderCatalogSnapshot:
    catalog: ReaderCatalog
    validator: str

    def __post_init__(self):
        if type(self.catalog) is not ReaderCatalog:
            raise ValueError('Reader catalog snapshot required')
        _validate_validator(self.validator)

@dataclass(frozen=True, slots=True)
class ReaderCatalogUnchanged:
    validator: str

    def __post_init__(self):
        _validate_validator(self.validator)

def _validate_validator(value):
    try:valid=type(value) is str and 1<=len(value.encode('utf8'))<=4096 and '\0' not in value
    except UnicodeError:valid=False
    if not valid:raise ValueError('Bounded opaque reader validator required')

@dataclass(frozen=True, slots=True)
class AcceptedDocument:
    document_id: str
    document_revision: str
    artifact_identity: str
    content: bytes
    sha256: str
    catalog_revision: int
    registration_id: str
    source_catalog_revision: int
    validation_bytes: bytes | None = None
    ddd_profile_bytes: bytes | None = None
    ddd_validation_bytes: bytes | None = None
