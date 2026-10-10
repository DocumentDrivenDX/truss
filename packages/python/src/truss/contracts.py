"""Public draft data contracts; shapes confer no registration/native authority.

Exact token/source spelling is retained. Value-domain interpretation belongs to
UMF and the admitted value profile. These constructors do not verify artifacts,
qualify database identities or manufacture accepted/committed evidence.
"""
from dataclasses import dataclass, field, fields
from enum import Enum
from types import UnionType
from typing import Generic, Literal, TypeAlias, TypeVar, Union, Unpack, get_args, get_origin, get_type_hints

class Absent(Enum):
    """Optional omission; distinct from both present null and an empty string."""
    ABSENT = 'absent'

ABSENT = Absent.ABSENT

def _annotations(cls: type) -> dict[str, object]:
    return get_type_hints(cls)

def _shape(value: object, annotation: object) -> bool:
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, UnionType):
        return any(_shape(value, member) for member in args)
    if origin is Literal:
        return any(type(value) is type(member) and value == member for member in args)
    if origin is tuple:
        if type(value) is not tuple:
            return False
        if len(args) == 2 and get_origin(args[1]) is Unpack:
            return bool(value) and _shape(value[0], args[0]) and _shape(value[1:], get_args(args[1])[0])
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_shape(item, args[0]) for item in value)
        return len(value) == len(args) and all(_shape(item, kind) for item, kind in zip(value, args))
    if isinstance(annotation, TypeVar):
        return _shape(value, annotation.__bound__)
    if origin is not None:
        return type(value) is origin
    return type(value) is annotation

class _Carrier:
    __slots__ = ()
    def __post_init__(self) -> None:
        annotations = _annotations(type(self))
        for member in fields(self):  # type: ignore[arg-type]
            if not _shape(getattr(self, member.name), annotations[member.name]):
                raise ValueError('Invalid contract field shape')

@dataclass(frozen=True, slots=True, kw_only=True)
class ProfilePin(_Carrier):
    identity: str
    version: str
    sha256: str

@dataclass(frozen=True, slots=True, kw_only=True)
class ExactArtifact(_Carrier):
    identity: str
    bytes_base64: str
    sha256: str

@dataclass(frozen=True, slots=True, kw_only=True)
class QualifiedOwner(_Carrier):
    document_id: str
    module_id: str

@dataclass(frozen=True, slots=True, kw_only=True)
class TypedIdentity(_Carrier):
    id: str
    type_id: str
    definition_pin: str
    owner: QualifiedOwner

@dataclass(frozen=True, slots=True, kw_only=True)
class NullValue(_Carrier):
    kind: Literal['null'] = field(default='null', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class BooleanValue(_Carrier):
    value: bool
    kind: Literal['boolean'] = field(default='boolean', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class TextValue(_Carrier):
    kind: Literal['string', 'integer', 'decimal', 'binary', 'timestamp']
    text: str

@dataclass(frozen=True, slots=True, kw_only=True)
class SequenceValue(_Carrier):
    items: tuple['ExactValue', ...]
    kind: Literal['sequence'] = field(default='sequence', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class MapEntry(_Carrier):
    key: str
    value: 'ExactValue'

@dataclass(frozen=True, slots=True, kw_only=True)
class MapValue(_Carrier):
    entries: tuple[MapEntry, ...]
    kind: Literal['map'] = field(default='map', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class RecordField(_Carrier):
    field_id: str
    value: 'ExactValue'

@dataclass(frozen=True, slots=True, kw_only=True)
class RecordValue(_Carrier):
    definition_pin: str
    fields: tuple[RecordField, ...]
    kind: Literal['record'] = field(default='record', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class OpaqueValue(_Carrier):
    format: str
    source_text: str
    sha256: str
    kind: Literal['opaque'] = field(default='opaque', init=False)

ExactValue: TypeAlias = NullValue | BooleanValue | TextValue | SequenceValue | MapValue | RecordValue | OpaqueValue

@dataclass(frozen=True, slots=True, kw_only=True)
class AbsentPresence(_Carrier):
    present: Literal[False] = field(default=False, init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class PresentValue(_Carrier):
    value: ExactValue
    present: Literal[True] = field(default=True, init=False)

Presence: TypeAlias = AbsentPresence | PresentValue
CapabilityFamily: TypeAlias = Literal['catalog', 'mutation', 'group', 'import', 'direct_read', 'history', 'feed', 'weft_execution', 'bootstrap', 'physical_optimization', 'conformance']
Family = TypeVar('Family', bound=CapabilityFamily, covariant=True)

@dataclass(frozen=True, slots=True, kw_only=True)
class CapabilitySelection(_Carrier, Generic[Family]):
    family: Family
    capability_profile: ProfilePin
    layout_profile: ProfilePin
    adapter_profile: ProfilePin
    value_profile: ProfilePin
    policy_profile: ProfilePin

__all__ = [
    'ABSENT', 'Absent', 'ProfilePin', 'ExactArtifact', 'QualifiedOwner', 'TypedIdentity',
    'NullValue', 'BooleanValue', 'TextValue', 'SequenceValue', 'MapEntry', 'MapValue',
    'RecordField', 'RecordValue', 'OpaqueValue', 'ExactValue', 'AbsentPresence',
    'PresentValue', 'Presence', 'CapabilityFamily', 'CapabilitySelection',
]

@dataclass(frozen=True, slots=True, kw_only=True)
class ReadTypeReference(_Carrier):
    type_id: str
    definition_pin: str
    owner: QualifiedOwner

@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectKeyComponent(_Carrier):
    property_id: str
    definition_pin: str
    value: ExactValue

@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectKeySelection(_Carrier):
    type: ReadTypeReference
    key_number: str
    key_definition_pin: str
    key_encoding_profile: ProfilePin
    components: tuple[ObjectKeyComponent, *tuple[ObjectKeyComponent, ...]]
    operation: Literal['object_key'] = field(default='object_key', init=False)

@dataclass(frozen=True, slots=True, kw_only=True)
class SelectedMutationConfiguration(_Carrier):
    source_epoch: str
    installation_id: str
    generation: str
    key_reuse: Literal['forbid', 'allow']
    journal_mode: Literal['engine', 'trigger']
    configuration_profile: ProfilePin
    installed_producer_inventory_sha256: str

__all__ += ['ReadTypeReference', 'ObjectKeyComponent', 'ObjectKeySelection', 'SelectedMutationConfiguration']
