"""Public outcomes from accepted native UMF catalog operations."""
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True,slots=True)
class CatalogRegistration:
    revision: int
    registration_id: str
    report_bytes: bytes
    replayed: bool
    status: str = 'pending_commit'

@dataclass(frozen=True,slots=True)
class CatalogUnchanged:
    revision: int
    registration_id: str
    report_bytes: bytes
    replayed: bool
    request_key: str
    asserted_origin_bytes: bytes
    actor: str
    outcome: str = 'unchanged'
    status: str = 'pending_commit'

@dataclass(frozen=True,slots=True)
class CatalogCompatibilityViolation:
    document_id: str
    module_id: str
    record_id: str
    field_module_id: str
    field_id: str
    rule: Literal['property.required','property.scalar_type','property.facets','property.retained_name_collision']
    affected_object_count: int

@dataclass(frozen=True,slots=True)
class CatalogAcceptanceRefused:
    revision: int
    violations: tuple[CatalogCompatibilityViolation,...]
    outcome: Literal['refused'] = 'refused'
    code: Literal['incompatible'] = 'incompatible'

@dataclass(frozen=True,slots=True)
class CatalogReport:
    revision: int
    original_bytes: bytes
