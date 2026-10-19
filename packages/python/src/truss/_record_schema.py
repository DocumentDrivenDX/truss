# SPDX-License-Identifier: MIT OR Apache-2.0
"""Immutable application-side value schemas compiled from native definitions.

For an exact selected definition pin, the compiled subset validates authored
known fields and recursively checks retained cells, then prepares canonical
property and retained-field patches. Unsupported or invalid input stays on the
legacy native validation path. Native checks still govern schema freshness,
write authority, and physical write integrity.
"""
from dataclasses import dataclass
from datetime import date
import base64
import json
import re
from collections.abc import Mapping
from types import MappingProxyType

from .contracts import BooleanValue, MapEntry, MapValue, NullValue, SequenceValue, TextValue

_TOKEN_LIMIT = 1_048_576
_VALUE_NODE_LIMIT = 4096
_VALUE_DEPTH_LIMIT = 32
_MAP_KEY_LIMIT = 4096
_PROPERTY_NAME_LIMIT = 4096
_AUTHORED_VALUE_LIMIT = 1024
_SCHEMA_DEFINITION_LIMIT = 65_536
_INTEGER_TOKEN = re.compile(r"-?(0|[1-9][0-9]*)\Z")
_DECIMAL_TOKEN = re.compile(r"-?(0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")
_TIMESTAMP_TOKEN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})\Z"
)


class SchemaCompilationError(ValueError):
    """The native declaration is outside this fast validator's exact subset."""


@dataclass(frozen=True, slots=True)
class ValueViolation:
    property_name: str
    code: str
    path: tuple[str | int, ...] = ()


@dataclass(frozen=True, slots=True)
class ValueValidationResult:
    valid: bool
    violations: tuple[ValueViolation, ...]


@dataclass(frozen=True, slots=True)
class PreparedRecordPatch:
    """Safe-to-use projected write values; ``eligible`` gates the fast path."""
    eligible: bool
    type_id: str
    definition_pin: str
    props_set: object
    retained_set: object
    props_unset: tuple[str, ...]
    retained_unset: tuple[str, ...]
    violations: tuple[ValueViolation, ...]

    def wire_payload(self):
        """Return an isolated native-wire copy, never the validated stored tree."""
        return {
            'propsSet': _thaw_json(self.props_set),
            'retainedSet': _thaw_json(self.retained_set),
            'propsUnset': list(self.props_unset),
            'retainedUnset': list(self.retained_unset),
        }


@dataclass(frozen=True, slots=True)
class PropertySchema:
    name: str
    property_id: str
    family: str | None
    cardinality: str
    nullability: str
    facets: object
    item_chain: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class RecordSchema:
    type_id: str
    definition_pin: str
    properties_by_name: object
    properties_by_id: object


def _positive_id(value, label):
    if type(value) is int and value > 0:
        return str(value)
    if type(value) is str and value.isascii() and value.isdecimal() and value and value[0] != '0':
        return value
    raise SchemaCompilationError(f"Canonical positive {label} required")


def _int_facet(value, label):
    if type(value) is not int or value < 0:
        raise SchemaCompilationError(f"Supported exact {label} required")
    return value


def _compile_chain(item):
    if not isinstance(item, Mapping) or not isinstance(item.get('declaration'), Mapping):
        raise SchemaCompilationError('Complete native item declaration chain required')
    descendants = item.get('descendants', ())
    if type(descendants) not in (list, tuple) or len(descendants) > _VALUE_DEPTH_LIMIT - 1:
        raise SchemaCompilationError('Bounded native item chain required')
    nodes = (item, *descendants)
    chain = []
    seen = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, Mapping) or not isinstance(node.get('declaration'), Mapping):
            raise SchemaCompilationError('Complete native item declaration chain required')
        reference = node.get('reference')
        if not isinstance(reference, Mapping):
            raise SchemaCompilationError('Exact item field reference required')
        identity = (reference.get('module'), reference.get('element'))
        if any(type(part) is not str or not part for part in identity) or identity in seen:
            raise SchemaCompilationError('Acyclic qualified item field chain required')
        seen.add(identity)
        declaration = node['declaration']
        cardinality = declaration.get('cardinality')
        family = declaration.get('scalarType')
        facets = declaration.get('facets') or {}
        if declaration.get('kind') != 'field' or declaration.get('nullability') != 'required':
            raise SchemaCompilationError('Required item Field declaration required')
        if index == len(nodes) - 1:
            if cardinality != 'one' or family not in ('string', 'integer', 'decimal', 'boolean', 'timestamp', 'binary', 'date'):
                raise SchemaCompilationError('Supported scalar item leaf required')
            facets = _check_facets(family, facets, item=True)
        else:
            if cardinality not in ('array', 'map') or family is not None or facets != {}:
                raise SchemaCompilationError('Unfaceted container item Field required')
            facets = MappingProxyType({})
            if declaration.get('itemType') != {'module': nodes[index + 1]['reference'].get('module'),
                                                'element': nodes[index + 1]['reference'].get('element')}:
                raise SchemaCompilationError('Exact linked item Field chain required')
        chain.append((cardinality, family, facets))
    return tuple(chain)


def _check_facets(family, facets, *, item=False):
    if not isinstance(facets, Mapping):
        raise SchemaCompilationError('Exact property facets required')
    if not facets:
        return MappingProxyType({})
    if family == 'integer' and facets == {'integerWidth': {'bits': 64, 'signed': True}}:
        return MappingProxyType({'integerWidth': MappingProxyType({'bits': 64, 'signed': True})})
    if family == 'decimal' and set(facets) == {'precision', 'scale'}:
        precision, scale = facets['precision'], facets['scale']
        if (type(precision) is int and 1 <= precision <= 2_147_483_647
                and type(scale) is int and 0 <= scale <= precision):
            return MappingProxyType({'precision': precision, 'scale': scale})
    if family in ('string', 'binary') and set(facets) == {'length'}:
        length = facets['length']
        if (isinstance(length, Mapping) and set(length) == {'max', 'unit'}
                and type(length['max']) is int and 0 <= length['max'] <= 9_007_199_254_740_991
                and length['unit'] == ('unicode-scalar' if family == 'string' else 'byte')):
            return MappingProxyType({'length': MappingProxyType(dict(length))})
    raise SchemaCompilationError('Property facets outside the current native exact-value subset')


def _compile_property(prop):
    if not isinstance(prop, Mapping):
        raise SchemaCompilationError('Native property definition required')
    name = prop.get('name')
    if type(name) is not str or not name or '\x00' in name:
        raise SchemaCompilationError('Exact native property name required')
    property_id = _positive_id(prop.get('prop_id', prop.get('propertyId')), 'property id')
    cardinality = prop.get('cardinality')
    nullability = prop.get('nullability')
    family = prop.get('scalar_type', prop.get('scalarType'))
    if prop.get('home', 'json') != 'json' or nullability not in ('required', 'absent-allowed'):
        raise SchemaCompilationError('Property outside selected JSON value subset')
    facets = prop.get('facets') or {}
    if cardinality == 'one':
        if family not in ('string', 'integer', 'decimal', 'boolean', 'timestamp', 'binary', 'date') or prop.get('item') is not None:
            raise SchemaCompilationError('Supported singular scalar property required')
        compiled_facets = _check_facets(family, facets)
        chain = ()
    elif cardinality in ('array', 'map'):
        if family is not None or facets != {}:
            raise SchemaCompilationError('Unfaceted container property required')
        chain = _compile_chain(prop.get('item'))
        compiled_facets = MappingProxyType({})
    else:
        raise SchemaCompilationError('Supported property cardinality required')
    return PropertySchema(name, property_id, family, cardinality, nullability, compiled_facets, chain)


def compile_records(records):
    """Compile native prop_def dictionaries once into immutable indexed records.

    Each record has ``typeId``, ``definitionPin`` and ``properties``. The input
    may be a tuple/list; no original dictionaries are retained or mutated.
    """
    if type(records) not in (tuple, list):
        raise SchemaCompilationError('A bounded record definition sequence is required')
    if len(records) > _SCHEMA_DEFINITION_LIMIT:
        raise SchemaCompilationError('Schema definition count limit exceeded')
    result = {}; by_pin = {}
    for record in records:
        if not isinstance(record, Mapping) or type(record.get('properties')) not in (tuple, list):
            raise SchemaCompilationError('Native record with property definitions required')
        type_id = _positive_id(record.get('typeId', record.get('type_id')), 'type id')
        pin = record.get('definitionPin', record.get('definition_pin'))
        if type(pin) is not str or not re.fullmatch(r'[0-9a-f]{64}', pin):
            raise SchemaCompilationError('Exact selected record definition pin required')
        by_name = {}; by_id = {}
        if len(record['properties']) > _SCHEMA_DEFINITION_LIMIT:
            raise SchemaCompilationError('Record property count limit exceeded')
        for raw_prop in record['properties']:
            field = _compile_property(raw_prop)
            if field.name in by_name or field.property_id in by_id:
                raise SchemaCompilationError('Unique native property identity required')
            by_name[field.name] = field
            by_id[field.property_id] = field
        if type_id in result:
            raise SchemaCompilationError('Unique native record identity required')
        schema = RecordSchema(type_id, pin, MappingProxyType(by_name), MappingProxyType(by_id))
        if pin in by_pin:
            raise SchemaCompilationError('Unique native record definition pin required')
        result[type_id] = schema
        by_pin[pin] = schema
    return CompiledRecordSchemas(MappingProxyType(result), MappingProxyType(by_pin))


@dataclass(frozen=True, slots=True)
class CompiledRecordSchemas:
    _records: object
    _records_by_pin: object

    def validate_values(self, type_id, definition_pin, values, *, mode='update'):
        """Check authored values, including recursively typed retained cells.

        ``mode='create'`` additionally requires all required known properties.
        A false result means this compiled subset does not admit the values.
        """
        record = self._record(type_id, definition_pin)
        return _evaluate_values(record, values, mode)[0]

    def lookup_record(self, type_id, definition_pin):
        """Return the immutable selected record index only for its exact pin."""
        return self._record(type_id, definition_pin)

    def lookup_record_by_pin(self, definition_pin):
        """Resolve create operations that carry the exact type pin but no id."""
        if type(definition_pin) is not str or not re.fullmatch(r'[0-9a-f]{64}', definition_pin):
            raise ValueError('Exact current record definition pin required')
        record = self._records_by_pin.get(definition_pin)
        if record is None:
            raise ValueError('Exact current record schema pin required')
        return record

    def prepare_patch(self, type_id, definition_pin, values, *, unset=(), mode='update'):
        """Validate and project authored names to native property/retained maps.

        Unsupported, malformed or invalid input is marked ineligible so callers
        can retain the native path and its original diagnostic. No partial map
        is returned as eligible.
        """
        record = self._record(type_id, definition_pin)
        checked, encoded_values = _evaluate_values(record, values, mode)
        unset_result = self.validate_unsets(type_id, definition_pin, unset)
        violations = list(checked.violations) + list(unset_result.violations)
        if mode == 'create' and unset:
            violations.append(ValueViolation('', 'create_unset'))
        set_names = {entry.name for entry in values if hasattr(entry, 'name') and type(entry.name) is str}
        unset_names = {name for name in unset if type(name) is str}
        conflicts = set_names.intersection(unset_names)
        if conflicts:
            violations.extend(ValueViolation(name, 'set_and_unset') for name in sorted(conflicts))
        props = {}; retained = {}; props_unset = []; retained_unset = []
        if not violations:
            for entry in values:
                field = record.properties_by_name.get(entry.name)
                cell = encoded_values[entry.name]
                if field is None:
                    retained[entry.name] = cell
                else:
                    props[field.property_id] = cell
            if not violations:
                for name in unset:
                    field = record.properties_by_name.get(name)
                    if field is None:
                        retained_unset.append(name)
                    else:
                        props_unset.append(field.property_id)
        eligible = not violations
        if eligible:
            try:
                encoded = json.dumps([props, retained], ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')
                # Leave headroom for PostgreSQL jsonb's expanded textual form.
                eligible = len(encoded) <= _TOKEN_LIMIT // 2
            except (UnicodeError, TypeError, ValueError):
                eligible = False
            if not eligible:
                violations.append(ValueViolation('', 'patch_resource'))
        return PreparedRecordPatch(eligible, record.type_id, record.definition_pin,
            _freeze_json(props) if eligible else MappingProxyType({}),
            _freeze_json(retained) if eligible else MappingProxyType({}),
            tuple(props_unset) if eligible else (), tuple(retained_unset) if eligible else (),
            tuple(violations))

    def validate_unsets(self, type_id, definition_pin, names):
        """Check named removals; unknown names preserve retained-field behavior."""
        record = self._record(type_id, definition_pin)
        if type(names) not in (tuple, list):
            raise ValueError('Unset name sequence required')
        if len(names) > _AUTHORED_VALUE_LIMIT:
            return ValueValidationResult(False, (ValueViolation('', 'unset_count_limit'),))
        seen = set(); violations = []
        for name in names:
            if not _valid_property_name(name) or name in seen:
                violations.append(ValueViolation(str(name), 'duplicate_or_invalid_name'))
                continue
            seen.add(name)
            field = record.properties_by_name.get(name)
            if field is not None and field.nullability == 'required':
                violations.append(ValueViolation(name, 'required_unset'))
        return ValueValidationResult(not violations, tuple(violations))

    def _record(self, type_id, definition_pin):
        if type_id is None:
            return self.lookup_record_by_pin(definition_pin)
        key = _positive_id(type_id, 'type id')
        record = self._records.get(key)
        if record is None or record.definition_pin != definition_pin:
            raise ValueError('Exact current record schema pin required')
        return record


def _evaluate_values(record, values, mode):
    if mode not in ('create', 'update'):
        raise ValueError('Create or update validation mode required')
    if type(values) not in (tuple, list):
        raise ValueError('Authored value sequence required')
    if len(values) > _AUTHORED_VALUE_LIMIT:
        return (ValueValidationResult(False, (ValueViolation('', 'authored_value_count_limit'),)),
                MappingProxyType({}))
    seen = set(); encoded = {}; violations = []
    for entry in values:
        if not hasattr(entry, 'name') or not hasattr(entry, 'value'):
            raise ValueError('Named authored values required')
        name = entry.name
        if not _valid_property_name(name) or name in seen:
            violations.append(ValueViolation(str(name), 'duplicate_or_invalid_name'))
            continue
        seen.add(name)
        cell = _wire_cell(entry.value)
        if cell is None:
            violations.append(ValueViolation(name, 'unsupported_cell'))
            continue
        encoded[name] = cell
        field = record.properties_by_name.get(name)
        if field is not None:
            violations.extend(_validate_field(field, entry.value))
    if mode == 'create':
        for name, field in record.properties_by_name.items():
            if field.nullability == 'required' and name not in seen:
                violations.append(ValueViolation(name, 'required_missing'))
    return ValueValidationResult(not violations, tuple(violations)), MappingProxyType(encoded)


def _valid_property_name(value):
    if type(value) is not str or not value or '\x00' in value:
        return False
    try:
        encoded = value.encode('utf-8', errors='strict')
    except UnicodeError:
        return False
    return 1 <= len(encoded) <= _PROPERTY_NAME_LIMIT


def _text_bytes(token):
    try:
        return len(token.encode('utf-8', errors='strict'))
    except UnicodeError:
        return None


def _wire_cell(value, *, _depth=0, _count=None):
    """Encode admitted scalar/container carriers without semantic conversion."""
    if _count is None:
        _count = [0]
    _count[0] += 1
    if _depth > _VALUE_DEPTH_LIMIT or _count[0] > _VALUE_NODE_LIMIT:
        return None
    if type(value) is NullValue:
        return {'kind': 'null'} if _scalar(value, 'string', {}, True) else None
    if type(value) in (BooleanValue, TextValue):
        family = 'boolean' if type(value) is BooleanValue else value.kind
        if family not in ('boolean', 'string', 'integer', 'decimal', 'timestamp', 'binary', 'date'):
            return None
        if not _scalar(value, family, {}, False):
            return None
        if family == 'boolean':
            return {'kind': 'boolean', 'value': value.value}
        return {'kind': family, 'text': value.text}
    if type(value) is SequenceValue:
        if type(value.items) is not tuple or len(value.items) > 1024:
            return None
        children = [_wire_cell(item, _depth=_depth + 1, _count=_count) for item in value.items]
        if any(item is None for item in children):
            return None
        result = {'kind': 'sequence', 'items': children}
    elif type(value) is MapValue:
        if type(value.entries) is not tuple or len(value.entries) > 1024 or any(type(entry) is not MapEntry for entry in value.entries):
            return None
        entries = []
        for entry in value.entries:
            if type(entry.key) is not str:
                return None
            key_size = _text_bytes(entry.key)
            child = _wire_cell(entry.value, _depth=_depth + 1, _count=_count)
            if key_size is None or key_size > _MAP_KEY_LIMIT or '\x00' in entry.key or child is None:
                return None
            entries.append({'key': entry.key, 'value': child})
        if len({entry['key'] for entry in entries}) != len(entries):
            return None
        result = {'kind': 'map', 'entries': sorted(entries, key=lambda entry: entry['key'].encode('utf-8'))}
    else:
        return None
    return result


def _freeze_json(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(child) for child in value)
    return value


def _thaw_json(value):
    if isinstance(value, Mapping):
        return {key: _thaw_json(child) for key, child in value.items()}
    if type(value) is tuple:
        return [_thaw_json(child) for child in value]
    return value


def _scalar(value, family, facets, allow_null):
    if type(value) is NullValue:
        return allow_null
    if family == 'boolean':
        return type(value) is BooleanValue and type(value.value) is bool
    if type(value) is not TextValue or value.kind != family or type(value.text) is not str:
        return False
    size = _text_bytes(value.text)
    if size is None or size > _TOKEN_LIMIT:
        return False
    token = value.text
    if family == 'string':
        return '\x00' not in token and ('length' not in facets or len(token) <= facets['length']['max'])
    if family == 'integer':
        if not _INTEGER_TOKEN.fullmatch(token):
            return False
        if 'integerWidth' in facets:
            digits = token[1:] if token.startswith('-') else token
            limit = '9223372036854775808' if token.startswith('-') else '9223372036854775807'
            if len(digits) > len(limit) or len(digits) == len(limit) and digits > limit:
                return False
        return True
    if family == 'decimal':
        if not _DECIMAL_TOKEN.fullmatch(token):
            return False
        if not facets:
            return True
        precision, scale = facets['precision'], facets['scale']
        # Exact coefficient admission: no rounding; exponent expansion is never
        # materialized, so large but bounded source tokens remain bounded work.
        mantissa, _, exponent_text = token.lower().partition('e')
        exponent_digits = exponent_text.lstrip('+-').lstrip('0')
        digits = mantissa.lstrip('-').replace('.', '')
        fractional = len(mantissa.partition('.')[2])
        coefficient = digits.lstrip('0')
        if not coefficient:
            return True
        if len(exponent_digits) > 18:
            return False
        exponent_sign = -1 if exponent_text.startswith('-') else 1
        exponent = exponent_sign * int(exponent_digits or '0')
        shift = scale - fractional + exponent
        trailing_zeros = len(coefficient) - len(coefficient.rstrip('0'))
        return not (shift < 0 and -shift > trailing_zeros) and len(coefficient) + shift <= precision
    if family == 'binary':
        try:
            decoded = base64.b64decode(token, validate=True)
            return (base64.b64encode(decoded).decode('ascii') == token
                    and ('length' not in facets or len(decoded) <= facets['length']['max']))
        except (ValueError, base64.binascii.Error):
            return False
    if family == 'date':
        if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', token):
            return False
        try:
            date.fromisoformat(token)
            return token[:4] != '0000'
        except ValueError:
            return False
    if family == 'timestamp':
        if not _TIMESTAMP_TOKEN.fullmatch(token):
            return False
        if token[11:13] > '23' or token[14:16] > '59' or token[17:19] > '59':
            return False
        try:
            date.fromisoformat(token[:10])
        except ValueError:
            return False
        if token[-1] not in 'Zz':
            offset = token[-6:]
            if offset[1:3] > '23' or offset[4:6] > '59':
                return False
        return token[:4] != '0000'
    return False


def _validate_field(field, value):
    if field.cardinality == 'one':
        if not _scalar(value, field.family, field.facets, field.nullability == 'absent-allowed'):
            return (ValueViolation(field.name, 'value_domain'),)
        return ()
    if type(value) is NullValue:
        return () if field.nullability == 'absent-allowed' else (ValueViolation(field.name, 'null_not_allowed'),)
    root_kind = 'sequence' if field.cardinality == 'array' else 'map'
    if root_kind == 'sequence' and type(value) is not SequenceValue or root_kind == 'map' and type(value) is not MapValue:
        return (ValueViolation(field.name, 'container_kind'),)
    violations = []
    if root_kind == 'sequence':
        members = tuple((index, child) for index, child in enumerate(value.items))
    else:
        keys = [entry.key for entry in value.entries]
        if any(type(key) is not str or _text_bytes(key) is None or _text_bytes(key) > _MAP_KEY_LIMIT for key in keys) or len(set(keys)) != len(keys):
            return (ValueViolation(field.name, 'map_keys'),)
        members = tuple((entry.key, entry.value) for entry in value.entries)
    pending = [(member, value, 0, key) for key, member in members]
    count = 1
    while pending:
        child, parent, chain_index, key = pending.pop()
        count += 1
        if chain_index >= len(field.item_chain) or count > _VALUE_NODE_LIMIT or chain_index + 1 > _VALUE_DEPTH_LIMIT:
            violations.append(ValueViolation(field.name, 'container_limits', (key,)))
            break
        cardinality, family, facets = field.item_chain[chain_index]
        if cardinality == 'one':
            if not _scalar(child, family, facets, False):
                violations.append(ValueViolation(field.name, 'value_domain', (key,)))
        else:
            expected = SequenceValue if cardinality == 'array' else MapValue
            if type(child) is not expected:
                violations.append(ValueViolation(field.name, 'container_kind', (key,)))
                continue
            if cardinality == 'array':
                nested = tuple((index, item) for index, item in enumerate(child.items))
            else:
                nested_keys = [entry.key for entry in child.entries]
                if (any(type(k) is not str or _text_bytes(k) is None or _text_bytes(k) > _MAP_KEY_LIMIT for k in nested_keys)
                        or len(set(nested_keys)) != len(nested_keys)):
                    violations.append(ValueViolation(field.name, 'map_keys', (key,)))
                    continue
                nested = tuple((entry.key, entry.value) for entry in child.entries)
            pending.extend((item, child, chain_index + 1, nested_key) for nested_key, item in nested)
    return tuple(violations)
