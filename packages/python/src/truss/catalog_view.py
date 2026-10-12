"""Catalog view request contracts; shapes alone confer no catalog authority."""
from dataclasses import dataclass, field
from typing import Literal
from .contracts import ProfilePin, QualifiedOwner, ExactArtifact, _Carrier


@dataclass(frozen=True,slots=True,kw_only=True)
class CurrentCatalogSelection(_Carrier):
    kind: Literal['current'] = field(default='current',init=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class HistoricalCatalogSelection(_Carrier):
    catalog_revision: str
    kind: Literal['historical'] = field(default='historical',init=False)

    def __post_init__(self) -> None:
        super(HistoricalCatalogSelection,self).__post_init__()
        value=self.catalog_revision
        if not value or (len(value)>1 and value[0]=='0') or any(ch not in '0123456789' for ch in value):
            raise ValueError('Canonical nonnegative catalog revision text required')


@dataclass(frozen=True,slots=True,kw_only=True)
class CompleteCatalogScope(_Carrier):
    kind: Literal['complete'] = field(default='complete',init=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class ProjectedCatalogScope(_Carrier):
    owners: tuple[QualifiedOwner,...]
    kind: Literal['authorized_projection'] = field(default='authorized_projection',init=False)

    def __post_init__(self) -> None:
        super(ProjectedCatalogScope,self).__post_init__()
        if not self.owners or len(set(self.owners))!=len(self.owners):
            raise ValueError('A nonempty unique owner selection is required')


@dataclass(frozen=True,slots=True,kw_only=True)
class CatalogViewLimits(_Carrier):
    definition_count: str
    encoded_bytes: str

    def __post_init__(self) -> None:
        super(CatalogViewLimits,self).__post_init__()
        for value in (self.definition_count,self.encoded_bytes):
            if not value or value[0]=='0' or any(ch not in '0123456789' for ch in value):
                raise ValueError('Positive exact decimal-text limits are required')


@dataclass(frozen=True,slots=True,kw_only=True)
class CatalogViewRequest(_Carrier):
    layout_profile: ProfilePin
    view_profile: ProfilePin
    selection: CurrentCatalogSelection | HistoricalCatalogSelection
    scope: CompleteCatalogScope | ProjectedCatalogScope
    limits: CatalogViewLimits
    interface_version: Literal['truss-catalog-view-request/0.1.0'] = field(
        default='truss-catalog-view-request/0.1.0',init=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class CatalogDefinitionReference(_Carrier):
    kind: Literal['type','property','key','relationship']
    definition_pin: str
    owner: QualifiedOwner
    authored_identity: str
    type_id: str | None = None
    property_id: str | None = None
    key_number: str | None = None
    relationship_id: str | None = None

    def __post_init__(self) -> None:
        super(CatalogDefinitionReference,self).__post_init__()
        required={'type':{'type_id'},'property':{'type_id','property_id'},
            'key':{'type_id','key_number'},'relationship':{'relationship_id'}}[self.kind]
        actual={name for name in ('type_id','property_id','key_number','relationship_id') if getattr(self,name) is not None}
        if actual!=required:raise ValueError('Exact catalog reference identity fields required')
        for name in actual:
            value=getattr(self,name)
            if not value or value[0]=='0' or any(ch not in '0123456789' for ch in value):
                raise ValueError('Positive exact native identity text required')


@dataclass(frozen=True,slots=True,kw_only=True)
class CatalogDocumentProvenance(_Carrier):
    accepted_catalog_revision: str
    document_ordinal: str
    document_revision: str
    accepted_document_sha256: str
    authored_pointer: str
    extraction_profile: ProfilePin
    kind: Literal['accepted_document'] = field(default='accepted_document',init=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class CatalogDefinitionEntry(_Carrier):
    reference: CatalogDefinitionReference
    lifecycle: Literal['active','retired']
    resolution: Literal['defined','provisional']
    definition: ExactArtifact
    provenance: CatalogDocumentProvenance
    dependencies: tuple[CatalogDefinitionReference,...]


@dataclass(frozen=True,slots=True,kw_only=True)
class CatalogView(_Carrier):
    catalog_revision: str
    layout_profile: ProfilePin
    view_profile: ProfilePin
    consistency_evidence_sha256: str
    definitions: tuple[CatalogDefinitionEntry,...]
    inventory_sha256: str
    original_bytes: bytes
    scope: CompleteCatalogScope = field(default_factory=CompleteCatalogScope)
    interface_version: Literal['truss-catalog-view/0.1.0'] = field(default='truss-catalog-view/0.1.0',init=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class CatalogViewAvailable(_Carrier):
    view: CatalogView
    outcome: Literal['available'] = field(default='available',init=False)


@dataclass(frozen=True,slots=True,kw_only=True)
class CatalogViewUnavailable(_Carrier):
    reason: Literal['context','closure','definition','profile','resource']
    outcome: Literal['unavailable'] = field(default='unavailable',init=False)
