# SPDX-License-Identifier: MIT OR Apache-2.0
"""Trusted engine preparation over an immutable, revision-bound value schema.

Only closed object create/update groups select this route. The original native
writer remains the fallback and owns diagnostic/condition precedence. Warm
preparation performs no database query; native admission checks its basis again.
"""
from hashlib import sha256
import json

from .contracts import ABSENT
from .groups import CreateObject, RootlessOwnership, StoredObjectReference, UpdateObject
from ._record_schema import SchemaCompilationError
from ._schema_memory import record_schemas


PROFILE = 'truss-application-record-preparation/0.1'


def prepare_records(cursor, state, input, original_input, original_documents, release, digest, *, _refresh=True):
    operations = input.operations
    creates = all(type(op) is CreateObject and type(op.ownership) is RootlessOwnership for op in operations)
    updates = all(type(op) is UpdateObject and type(op.target) is StoredObjectReference
                  and op.ownership_change is ABSENT for op in operations)
    if not (creates or updates):
        return None
    if updates and len({(op.target.identity.type_id, op.target.identity.id) for op in operations}) != len(operations):
        return None
    documents_digest = sha256(original_documents).hexdigest()
    source_key = (release, digest, documents_digest)
    cached = record_schemas(state['key']) if state.get('source') == source_key and 'key' in state else None
    warm = cached is not None
    if cached is None:
        cursor.execute('SELECT truss.person_writer_schema_basis(%s,%s,%s,%s)',
                       (original_input, original_documents, release, digest), prepare=False)
        raw = cursor.fetchone()[0]
        if raw is None:
            return None
        basis = json.loads(bytes(raw))
        identity = basis['basis']
        # The native basis binds exact supplied documents before its metadata is
        # compiled. Installation identity separates databases sharing revisions.
        if identity['documentsSha256'] != documents_digest or identity['releaseSha256'] != digest:
            raise ValueError('Exact native writer schema source identity required')
        records = basis.get('records', basis.get('schemas'))
        if type(records) is dict:
            records = list(records.values())
        # A basis can expose different authorized Record subsets to different
        # actors. Cache immutable meaning for the exact returned subset, never
        # treat one actor's partial index as a complete revision for another.
        selection = sorted((str(r['typeId']), r['definitionPin']) for r in records)
        key = sha256(json.dumps([identity, selection], sort_keys=True,
                               separators=(',', ':')).encode('utf8')).digest()
        try:
            cached = record_schemas(key, records, identity)
        except SchemaCompilationError:
            return None
        if cached is None:
            return None
        state.update(source=source_key, key=key)
    patches = []
    selected_schemas = {}
    for index, operation in enumerate(operations):
        if creates:
            pin = operation.type_definition_pin
            type_id = cached.types_by_pin.get(pin)
            values = operation.values
            unset = ()
        else:
            type_id = operation.target.identity.type_id
            pin = operation.target.identity.definition_pin
            values = operation.set
            unset = operation.unset
        if type_id is None or cached.pins_by_type.get(str(type_id)) != pin:
            if warm and _refresh:
                # A newly granted type can be absent from a previously loaded
                # subset. Refresh metadata once before any write is dispatched.
                state.clear()
                return prepare_records(cursor, state, input, original_input, original_documents,
                                       release, digest, _refresh=False)
            return None
        patch = cached.compiled.prepare_patch(str(type_id), pin, values, unset=unset,
                                              mode='create' if creates else 'update')
        if not patch.eligible:
            return None
        patches.append({'operationIndex': index, 'typeId': str(type_id), **patch.wire_payload()})
        selected_schemas[str(type_id)] = {'definitionPin': pin}
    return {'profile': PROFILE, 'basis': dict(cached.basis),
            'inputSha256': sha256(original_input).hexdigest(),
            'schemas': selected_schemas, 'operations': patches}
