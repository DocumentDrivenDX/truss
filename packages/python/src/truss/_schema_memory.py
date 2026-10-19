# SPDX-License-Identifier: MIT OR Apache-2.0
"""Immutable application schema indexes; no retained authorization decisions."""
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha256
from threading import RLock
from types import MappingProxyType
import json
import sys
import weakref

# At most the current and one other recently used revision. This bounds retained
# Python schema objects, not the process/driver/VM's total memory footprint.
MAX_CACHE_BYTES = 128 * 1024 * 1024
MAX_REVISIONS = 2
_cache = OrderedDict()
_indexes = {}
_record_states = weakref.WeakKeyDictionary()
_lock = RLock()
_cache_bytes = 0

@dataclass(frozen=True, slots=True)
class SchemaIndex:
    by_native_identity: Mapping
    types_by_identity: Mapping
    properties_by_type: Mapping
    declarations_by_pin: Mapping


@dataclass(frozen=True, slots=True)
class RecordSchemaSelection:
    basis: Mapping
    compiled: object
    types_by_pin: Mapping
    pins_by_type: Mapping


def record_state(connection):
    """Keep selection keys across facades without retaining their connection.

    The state contains no schema or authority; the bounded revision cache owns
    schema retention and native write admission owns current authorization.
    """
    with _lock:
        return _record_states.setdefault(connection, {})


def record_schemas(key, records=None, basis=None):
    """Share the bounded revision cache with production record preparation.

    A warm lookup has no native observation or authorization meaning. Admission
    must check the retained installation/revision/source identity on every write.
    """
    global _cache_bytes
    cache_key = ('records', key)
    with _lock:
        existing = _cache.get(cache_key)
        if existing is not None:
            _cache.move_to_end(cache_key)
            return existing[0]
        if records is None:
            return None
        from ._record_schema import compile_records
        compiled = compile_records(records)
        selection = RecordSchemaSelection(_freeze(basis), compiled,
            MappingProxyType({r['definitionPin']: str(r['typeId']) for r in records}),
            MappingProxyType({str(r['typeId']): r['definitionPin'] for r in records}))
        size = _resident_size(selection)
        if size > MAX_CACHE_BYTES:
            return None
        while _cache and (len(_cache) >= MAX_REVISIONS or _cache_bytes + size > MAX_CACHE_BYTES):
            _, (_, removed) = _cache.popitem(last=False)
            _cache_bytes -= removed
        _cache[cache_key] = (selection, size)
        _cache_bytes += size
        return selection


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


def attach(view, sources):
    native = {}; types = {}; properties = {}; declarations = {}
    for entry, source in zip(view.definitions, sources, strict=True):
        ref = entry.reference
        coordinate = (ref.kind, ref.type_id, ref.property_id, ref.key_number, ref.relationship_id)
        if coordinate in native:
            raise ValueError('Unique native schema coordinate required')
        native[coordinate] = entry
        if ref.kind == 'type':
            types[(ref.owner.document_id, ref.owner.module_id, ref.authored_identity)] = entry
        elif ref.kind == 'property':
            properties.setdefault(ref.type_id, {})[ref.property_id] = entry
        if ref.definition_pin not in declarations:
            declarations[ref.definition_pin] = _freeze(source)
    index = SchemaIndex(MappingProxyType(native), MappingProxyType(types),
        MappingProxyType({key: MappingProxyType(value) for key, value in properties.items()}),
        MappingProxyType(declarations))
    identity = id(view)
    with _lock:
        _indexes[identity] = (weakref.ref(view, lambda _: _indexes.pop(identity, None)), index)
    return view


def schema_index(view):
    with _lock:
        item = _indexes.get(id(view))
        if item is None or item[0]() is not view:
            raise ValueError('Loaded application schema required')
        return item[1]


def _resident_size(*roots):
    seen = set(); pending = list(roots); size = 0
    while pending:
        value = pending.pop(); identity = id(value)
        if identity in seen:
            continue
        seen.add(identity); size += sys.getsizeof(value)
        if isinstance(value, Mapping):
            if isinstance(value, MappingProxyType):
                # A proxy's shallow size excludes its backing dict. Account for
                # it conservatively without retaining or cloning another map.
                size += 64 + 72 * len(value)
            pending.extend(value.keys()); pending.extend(value.values())
        elif isinstance(value, (tuple, list)):
            pending.extend(value)
        elif is_dataclass(value):
            pending.extend(getattr(value, field.name) for field in fields(value))
    return size


def cached_catalog_view(raw, layout, *, expected_release, expected_digest):
    """Caller first obtains/authorizes a fresh native basis, including its identity.

    A rolled-back revision reused with different sources has a different basis
    digest. Cache hits never replace native current-context or permission checks.
    """
    global _cache_bytes
    key = (sha256(raw).digest(), layout, expected_release, expected_digest)
    with _lock:
        existing = _cache.get(key)
        if existing is not None:
            _cache.move_to_end(key)
            return existing[0]
        from ._catalog_view_build import build_catalog_view
        from .catalog_view import _definition_sources
        basis = json.loads(raw)
        from ._catalog_view_build import wire
        if (basis['releaseId'] != expected_release or basis['releaseSha256'] != expected_digest
                or basis['layoutProfile'] != wire(layout)):
            raise ValueError('Exact selected installed catalog release required')
        view = build_catalog_view(basis, layout)
        index = schema_index(view)
        source_texts = [item for entry in view.definitions
                        if (item := _definition_sources.get(id(entry.definition))) is not None]
        size = _resident_size(view, index, source_texts)
        if size <= MAX_CACHE_BYTES:
            while _cache and (len(_cache) >= MAX_REVISIONS or _cache_bytes + size > MAX_CACHE_BYTES):
                _, (_, removed) = _cache.popitem(last=False)
                _cache_bytes -= removed
            _cache[key] = (view, size); _cache_bytes += size
        return view
