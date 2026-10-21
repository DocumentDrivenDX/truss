# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public outcomes from accepted native UMF catalog operations."""
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True, slots=True)
class CatalogDocumentExpectation:
    """Expected accepted-source revision for one document; zero means absent."""
    document_id: str
    source_catalog_revision: int

    def __post_init__(self):
        try:valid_document=type(self.document_id) is str and 1<=len(self.document_id.encode('utf8'))<=4096 and '\0' not in self.document_id
        except UnicodeError:valid_document=False
        if not valid_document:
            raise ValueError('Valid document identity required')
        if type(self.source_catalog_revision) is not int or not 0 <= self.source_catalog_revision <= 2147483647:
            raise ValueError('Bounded source catalog revision required')

@dataclass(frozen=True, slots=True)
class RegistrarStatus:
    """Advisory current registration capability; admission always reauthorizes."""
    can_register: bool

    def __post_init__(self):
        if type(self.can_register) is not bool:
            raise ValueError('Boolean registrar status required')

@dataclass(frozen=True, slots=True)
class ModuleAccessError:
    """Index-only diagnostic for one rejected module-policy selection."""
    index: int
    code: Literal['duplicate_selection','unknown_module','unknown_role','unsafe_role']

    def __post_init__(self):
        if type(self.index) is not int or not 0 <= self.index < 512:
            raise ValueError('Bounded original module grant index required')
        if self.code not in ('duplicate_selection','unknown_module','unknown_role','unsafe_role'):
            raise ValueError('Selected module grant diagnostic required')

@dataclass(frozen=True, slots=True)
class ModuleAccessBatchRefused:
    errors: tuple[ModuleAccessError,...]
    outcome: Literal['refused'] = 'refused'

    def __post_init__(self):
        if (type(self.errors) is not tuple or not self.errors
                or any(type(error) is not ModuleAccessError for error in self.errors)
                or tuple(sorted(self.errors,key=lambda error:(error.index,error.code))) != self.errors):
            raise ValueError('Ordered nonempty indexed module access errors required')

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
class CatalogStoredViolator:
    object_id: str
    text: str

@dataclass(frozen=True,slots=True)
class CatalogCompatibilityViolation:
    document_id: str
    module_id: str
    record_id: str
    field_module_id: str
    field_id: str
    rule: Literal['property.required','property.scalar_type','property.facets','property.retained_name_collision','property.rebind_value']
    affected_object_count: int
    stored_values: tuple[CatalogStoredViolator, ...] = ()

@dataclass(frozen=True,slots=True)
class CatalogRelationshipCompatibilityViolation:
    document_id: str
    module_id: str
    relationship_id: str
    side: Literal['source','target']
    rule: Literal['relationship.min','relationship.max']
    affected_object_count: int

@dataclass(frozen=True,slots=True)
class CatalogKeyCompatibilityViolation:
    document_id: str
    module_id: str
    record_id: str
    key_id: str
    rule: Literal['key.duplicate']
    affected_object_count: int

@dataclass(frozen=True,slots=True)
class CatalogAcceptanceRefused:
    revision: int
    violations: tuple[CatalogCompatibilityViolation | CatalogRelationshipCompatibilityViolation | CatalogKeyCompatibilityViolation,...]
    outcome: Literal['refused'] = 'refused'
    code: Literal['incompatible'] = 'incompatible'

@dataclass(frozen=True,slots=True)
class CatalogCASConflict:
    """Expected accepted-source basis changed before publication."""
    code: Literal['revision_conflict'] = 'revision_conflict'
    outcome: Literal['conflict'] = 'conflict'

@dataclass(frozen=True,slots=True)
class CatalogReport:
    revision: int
    original_bytes: bytes
