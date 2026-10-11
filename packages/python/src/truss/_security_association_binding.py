"""Private original-source correspondence only; no authority or UMF semantics.

The caller still needs genuine UMF/ontology owner validation, authenticated
artifact/cut admission, native observations and complete protected publication.
This module neither compiles predicates nor executes database operations.
"""
from dataclasses import dataclass
from hashlib import sha256
import json


class AssociationBindingError(ValueError):
    pass


def _fail(reason):
    raise AssociationBindingError(reason)


@dataclass(frozen=True)
class _OriginalNumber:
    # Preserve uninterpreted JSON number spelling; do not impose Decimal/int ranges.
    text: str


def _json(original):
    if type(original) is not bytes or not 0 < len(original) <= 1_048_576:
        _fail('original_bytes')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail('duplicate_member')
            result[key] = value
        return result
    try:
        value = json.loads(original.decode('utf-8'), object_pairs_hook=pairs,
                           parse_float=_OriginalNumber, parse_int=_OriginalNumber, parse_constant=lambda _: _fail('non_json_number'))
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, AssociationBindingError):
            raise
        _fail('original_json')
    pending = [(value, 0)]; count = 0
    while pending:
        item, depth = pending.pop(); count += 1
        if count > 16384 or depth > 32:
            _fail('source_resource')
        if isinstance(item, str):
            try: item.encode('utf-8')
            except UnicodeError: _fail('source_unicode')
        elif isinstance(item, dict):
            pending.extend((part, depth + 1) for pair in item.items() for part in pair)
        elif isinstance(item, list):
            if len(item) > 4096: _fail('source_resource')
            pending.extend((part, depth + 1) for part in item)
    if type(value) is not dict: _fail('source_object')
    return value



def _mapping_fragments(original, count):
    """Exact JSON value slices after full source validation; never reserialize.

    Decoded member names locate the original mappings array, including escaped
    names. raw_decode supplies character boundaries; UTF-8 re-encoding the
    original slice preserves its bytes, escapes, whitespace and member order.
    The caller has already rejected duplicates, invalid Unicode and resources.
    """
    text = original.decode('utf-8')
    decoder = json.JSONDecoder(parse_float=_OriginalNumber, parse_int=_OriginalNumber)
    def whitespace(position):
        while position < len(text) and text[position] in ' \t\r\n':
            position += 1
        return position
    position = whitespace(0) + 1
    while True:
        position = whitespace(position)
        name, end = decoder.raw_decode(text, position)
        position = whitespace(whitespace(end) + 1)
        if name == 'mappings':
            position = whitespace(position + 1)
            fragments = []
            for index in range(count):
                start = position
                _, end = decoder.raw_decode(text, start)
                fragments.append(text[start:end].encode('utf-8'))
                position = whitespace(end)
                if index + 1 < count:
                    position = whitespace(position + 1)
            if text[position] != ']':
                _fail('original_mapping_extraction')
            return tuple(fragments)
        _, end = decoder.raw_decode(text, position)
        position = whitespace(end)
        if text[position] == '}':
            _fail('original_mapping_extraction')
        position += 1


def _closed(value, keys):
    if type(value) is not dict or set(value) != set(keys): _fail('closed_binding')
    return value


def _text(value):
    if type(value) is not str or not 0 < len(value.encode('utf-8')) <= 4096:
        _fail('source_identity')
    return value


def _array(value):
    if type(value) is not list or not 0 < len(value) <= 4096: _fail('source_array')
    return value


def _ref(value):
    _closed(value, ('documentId', 'moduleId', 'elementId'))
    return tuple(_text(value[name]) for name in ('documentId', 'moduleId', 'elementId'))


def _refs(value):
    result = tuple(_ref(item) for item in _array(value))
    if len(set(result)) != len(result): _fail('duplicate_reference')
    return result


@dataclass(frozen=True)
class AssociationRoleBasis:
    role: str
    association_fields: tuple
    target: tuple
    target_key_id: str
    target_fields: tuple


@dataclass(frozen=True)
class AssociationStorageBasis:
    source_min: str
    source_max: str
    target_min: str
    target_max: str
    directed: bool
    lifecycle: str
    composition: bool
    inverse: None
    source_pointer: str


@dataclass(frozen=True)
class AssociationBasis:
    association: tuple
    instance_key_id: str
    instance_key_fields: tuple
    source_role: str
    target_role: str
    roles: tuple[AssociationRoleBasis, ...]
    all_member_fields: tuple
    storage: AssociationStorageBasis
    source_pointer: str
    definition_bytes: bytes


@dataclass(frozen=True)
class AssociationBindingBasis:
    core_bytes: bytes
    ontology_bytes: bytes
    binding_bytes: bytes
    associations: tuple[AssociationBasis, ...]
    scope: str = 'original_source_correspondence_only'
    extraction_profile: str = 'truss-original-association-json-candidate/0.1.0'


def _prepare_association_binding(core_bytes: bytes, ontology_bytes: bytes,
                                binding_bytes: bytes) -> AssociationBindingBasis:
    core, ontology, binding = map(_json, (core_bytes, ontology_bytes, binding_bytes))
    _closed(binding, ('profile', 'coreSha256', 'ontologySha256', 'modelRevision', 'ontologyRevision', 'mappings'))
    if binding['profile'] != 'truss-binary-association-candidate/0.1.0': _fail('binding_profile')
    if binding['coreSha256'] != sha256(core_bytes).hexdigest() or binding['ontologySha256'] != sha256(ontology_bytes).hexdigest(): _fail('source_digest')
    if core.get('umf') != '0.8.0' or ontology.get('version') != '0.1.0': _fail('source_version')
    document = _text(core.get('id'))
    if ontology.get('documents') != [{'documentId': document, 'revision': binding['modelRevision']}]: _fail('model_revision')
    _text(binding['modelRevision']); _text(binding['ontologyRevision'])
    if ontology.get('documentId') != document or ontology.get('revision') != binding['ontologyRevision']: _fail('ontology_revision')
    elements = {}
    for module in _array(core.get('modules')):
        module_id = _text(module.get('id'))
        for element in _array(module.get('elements')):
            identity = (document, module_id, _text(element.get('id')))
            if identity in elements: _fail('duplicate_element')
            elements[identity] = element
    def record(identity):
        result = elements.get(identity)
        if not result or result.get('kind') != 'record': _fail('original_record')
        return result
    def field_refs(owner, items):
        result = tuple((owner[0], _text(item.get('module')), _text(item.get('element'))) for item in _array(items))
        if len(set(result)) != len(result): _fail('duplicate_reference')
        return result
    def members(identity): return field_refs(identity, record(identity).get('members'))
    def key(identity, key_id):
        keys = [item for item in _array(record(identity).get('keys')) if item.get('id') == key_id]
        if len(keys) != 1: _fail('original_key')
        fields = field_refs(identity, keys[0].get('fields'))
        if not set(fields) <= set(members(identity)): _fail('key_owner')
        return fields
    authored = {}
    for item in _array(ontology.get('associations')):
        identity = _ref(item.get('type'))
        if identity in authored: _fail('duplicate_association')
        authored[identity] = item
    entities = {}
    for item in _array(ontology.get('entities')):
        identity = _ref(item.get('type'))
        if identity in entities: _fail('duplicate_entity')
        entities[identity] = item
    mappings = _array(binding.get('mappings'))
    fragments = _mapping_fragments(binding_bytes, len(mappings))
    results = []; seen = set()
    for mapping_index, mapping in enumerate(mappings):
        _closed(mapping, ('association', 'instanceKeyId', 'sourceRole', 'targetRole', 'roles', 'storage'))
        identity = _ref(mapping['association']); original = authored.get(identity)
        if identity in seen or original is None: _fail('association_coverage')
        seen.add(identity); own_members = members(identity)
        key_id = _text(mapping['instanceKeyId'])
        if key_id != original.get('keyId'): _fail('instance_key')
        own_key = key(identity, key_id)
        endpoint_roles = {}
        for endpoint in _array(original.get('endpoints')):
            role = _text(endpoint.get('role'))
            if role in endpoint_roles: _fail('duplicate_role')
            endpoint_roles[role] = endpoint
        if len(endpoint_roles) != 2: _fail('binary_profile')
        source, target = _text(mapping['sourceRole']), _text(mapping['targetRole'])
        if source == target or {source, target} != set(endpoint_roles): _fail('role_orientation')
        roles = []; selected = set(); endpoint_fields = set()
        for choice in _array(mapping['roles']):
            _closed(choice, ('role', 'associationFields', 'target', 'targetKeyId', 'targetFields'))
            role = _text(choice['role']); endpoint = endpoint_roles.get(role)
            if role in selected or endpoint is None: _fail('role_coverage')
            selected.add(role); fields = _refs(choice['associationFields'])
            if fields != _refs(endpoint.get('fields')) or not set(fields) <= set(own_members): _fail('endpoint_fields')
            target_ref = _ref(choice['target'])
            if target_ref != _ref(endpoint.get('target')) or target_ref not in entities: _fail('endpoint_target')
            target_key = _text(choice['targetKeyId'])
            if target_key != entities[target_ref].get('keyId'): _fail('target_key')
            target_fields = key(target_ref, target_key)
            if _refs(choice['targetFields']) != target_fields or len(fields) != len(target_fields): _fail('ordered_target_key')
            for field in (*fields, *target_fields):
                declaration = elements.get(field, {})
                if any(declaration.get(name) != value for name, value in [('kind', 'field'), ('scalarType', 'string'), ('nullability', 'required'), ('cardinality', 'one')]): _fail('endpoint_string_subset')
            endpoint_fields.update(fields)
            roles.append(AssociationRoleBasis(role, fields, target_ref, target_key, target_fields))
        if selected != set(endpoint_roles): _fail('role_coverage')
        if not set(own_key) <= endpoint_fields: _fail('parallel_instance_storage_loss')
        storage = _closed(mapping['storage'], ('sourceMin', 'sourceMax', 'targetMin', 'targetMax', 'directed', 'lifecycle', 'composition', 'inverse'))
        expected = {'sourceMin':'0','sourceMax':'*','targetMin':'0','targetMax':'*','directed':True,'lifecycle':'independent','composition':False,'inverse':None}
        if storage != expected or type(storage['directed']) is not bool or type(storage['composition']) is not bool: _fail('storage_subset')
        results.append(AssociationBasis(identity, key_id, own_key, source, target, tuple(roles), own_members,
            AssociationStorageBasis(storage['sourceMin'], storage['sourceMax'],
                storage['targetMin'], storage['targetMax'], storage['directed'],
                storage['lifecycle'], storage['composition'], storage['inverse'],
                f'/mappings/{mapping_index}/storage'),
            f'/mappings/{mapping_index}', fragments[mapping_index]))
    if seen != set(authored): _fail('association_coverage')
    return AssociationBindingBasis(core_bytes, ontology_bytes, binding_bytes, tuple(results))


def prepare_association_binding(core_bytes: bytes, ontology_bytes: bytes,
                                binding_bytes: bytes) -> AssociationBindingBasis:
    try:
        return _prepare_association_binding(core_bytes, ontology_bytes, binding_bytes)
    except (AttributeError, KeyError, TypeError):
        _fail('source_shape')
