# SPDX-License-Identifier: MIT OR Apache-2.0
"""F8 original owner-inspection custody and native descriptor correspondence.

This module checks storage references against retained owner output. It never
resolves access extensions or derives temporal meaning from core declarations.
Only the complete native2.1 admission route may publish the resulting packet.
"""
from hashlib import sha256
import json

from .preparation import CatalogDocument, _catalog_declarations
from ._owner_evidence_json import decode_owner_evidence_json, same_owner_evidence

PREPARATION = 'truss-registration-preparation/2.1'
LOCAL_PROFILE = 'truss.local-timestamp/0.1'
MAX_INSPECTION = 4194304


def _reference(value):
    if (type(value) is not dict or set(value) != {'module', 'element'}
            or any(type(v) is not str or not v for v in value.values())):
        raise ValueError('Exact original owner reference required')
    return value['module'], value['element']


def _pointer(source, pointer):
    """Dereference one retained JSON pointer; this performs no UMF resolution."""
    if type(pointer) is not str or not pointer.startswith('/'):
        raise ValueError('Original owner JSON pointer required')
    value = source
    for raw in pointer[1:].split('/'):
        # Reject malformed escapes and noncanonical array positions.
        if '~' in raw.replace('~0', '').replace('~1', ''):
            raise ValueError('Valid JSON pointer escape required')
        key = raw.replace('~1', '/').replace('~0', '~')
        if type(value) is list:
            if not key.isascii() or not key.isdecimal() or str(int(key)) != key:
                raise ValueError('Canonical original array position required')
            value = value[int(key)]
        elif type(value) is dict:
            value = value[key]
        else:
            raise ValueError('Original pointer target required')
    return value


def inspection_packet(document, *, selected, bindings, source_id, owner_profile, result_bytes):
    """Retain one real owner call. Caller supplies the result unchanged as bytes.

    Profile pinning to an installed owner is an admission responsibility; this
    packet records that pin and exact invocation, not an authority credential.
    """
    if type(document) is not CatalogDocument or type(document.content) is not bytes:
        raise ValueError('Original document carrier required')
    if (type(result_bytes) is not bytes or not 1 <= len(result_bytes) <= MAX_INSPECTION
            or type(selected) is not list or not selected or type(bindings) is not list
            or type(source_id) is not str or not source_id
            or type(owner_profile) is not dict or set(owner_profile) != {'identity', 'version', 'sha256'}
            or any(type(v) is not str or not v for v in owner_profile.values())
            or len(owner_profile['sha256']) != 64
            or any(c not in '0123456789abcdef' for c in owner_profile['sha256'])):
        raise ValueError('Complete bounded original inspection invocation required')
    # Retain the exact result text, including diagnostics and unknown members.
    result = decode_owner_evidence_json(result_bytes)
    if type(result) is not dict or type(result.get('records')) is not list or type(result.get('diagnostics')) is not list:
        raise ValueError('Complete original owner result required')
    packet = {'operation': 'inspectAccessViews', 'ownerProfile': owner_profile,
              'documentId': document.document_id, 'revision': document.document_revision,
              'contentSha256': sha256(document.content).hexdigest(),
              'selected': selected, 'bindings': bindings, 'sourceId': source_id,
              'resultJson': result_bytes.decode('utf8'), 'resultSha256': sha256(result_bytes).hexdigest()}
    # Issue only after the original declarations and selected coverage agree.
    temporal_declarations(document, packet)
    return json.loads(json.dumps(packet, ensure_ascii=True))


def temporal_declarations(document, packet):
    """Exact inverse coverage: one original owner member ↔ one descriptor.

    Unknown owner result content remains retained in resultJson. Error/fatal
    diagnostics refuse admission; no diagnostic is removed from the transcript.
    """
    try:
        return _temporal_declarations(document, packet)
    except (KeyError, IndexError, TypeError, UnicodeError, OverflowError) as error:
        raise ValueError('Complete original temporal source custody required') from error


def _temporal_declarations(document, packet):
    if type(document) is not CatalogDocument or type(packet) is not dict or set(packet) != {
            'operation', 'ownerProfile', 'documentId', 'revision', 'contentSha256',
            'selected', 'bindings', 'sourceId', 'resultJson', 'resultSha256'}:
        raise ValueError('Closed original owner invocation required')
    if (packet['operation'] != 'inspectAccessViews' or packet['documentId'] != document.document_id
            or packet['revision'] != document.document_revision
            or packet['contentSha256'] != sha256(document.content).hexdigest()
            or type(packet['resultJson']) is not str):
        raise ValueError('Original document pin and inspection required')
    raw = packet['resultJson'].encode('utf8')
    if not 1 <= len(raw) <= MAX_INSPECTION or sha256(raw).hexdigest() != packet['resultSha256']:
        raise ValueError('Original complete owner result bytes required')
    owner = decode_owner_evidence_json(raw)
    if type(owner.get('records')) is not list or type(owner.get('diagnostics')) is not list:
        raise ValueError('Complete owner records and diagnostics required')
    if any(type(d) is not dict or d.get('severity') in ('error', 'fatal') for d in owner['diagnostics']):
        raise ValueError('Owner inspection refused selected source')
    source = decode_owner_evidence_json(document.content)
    declarations = _catalog_declarations(document.document_id, source)
    selected = [_reference(ref) for ref in packet['selected']]
    original_records = {(r['moduleId'], r['elementId']): r for r in declarations['records']}
    if not selected or len(set(selected)) != len(selected) or any(ref not in original_records for ref in selected):
        raise ValueError('Exactly-once original Record selection required')
    declarations['records'] = [original_records[ref] for ref in selected]
    records = owner['records']
    if len(records) != len(selected) or [_reference(r['ref']) for r in records] != selected:
        raise ValueError('Complete exactly-once owner Record coverage required')
    for declaration, record in zip(declarations['records'], records, strict=True):
        if _pointer(source, record['pointer']) != declaration['declaration'] or record.get('selected') is not True:
            raise ValueError('Original selected Record pointer required')
        fields = record['fields']
        if (type(fields) is not list or len(fields) != len(declaration['fields'])
                or [_reference(f['ref']) for f in fields] != [_reference(f['reference']) for f in declaration['fields']]):
            raise ValueError('Complete exactly-once original owner Field coverage required')
        for native, field in zip(declaration['fields'], fields, strict=True):
            original = native['declaration']
            if _pointer(source, field['pointer']) != original or field['scalarType'] != original.get('scalarType'):
                raise ValueError('Exact original Field declaration pointer required')
            presence = field['row']
            if type(presence) is not dict or set(presence) != {'missing', 'null'} or any(type(v) is not bool for v in presence.values()):
                raise ValueError('Original owner row presence required')
            if field.get('temporal') != 'local':
                continue
            view = _pointer(source, field['viewPointer'])
            if (original.get('scalarType') != 'timestamp' or original.get('cardinality') != 'one'
                    or view['field'] != field['ref'] or view['row'] != presence):
                raise ValueError('Original local FieldView pointer and row presence required')
            # Core declaration stays timestamp. This sibling selects native storage.
            native['nativeDescriptor'] = {'nativeScalarType': 'localTimestamp', 'nativeTemporal': {
                'profile': LOCAL_PROFILE, 'kind': 'local', 'source': {
                    'documentId': document.document_id, 'sha256': packet['contentSha256'],
                    'record': record['ref'], 'field': field['ref'], 'fieldViewPointer': field['viewPointer']}}}
    return declarations


def validate_temporal_declarations(document, packet, declarations):
    if not same_owner_evidence(declarations, temporal_declarations(document, packet)):
        raise ValueError('Exact inverse native descriptor coverage required')


def support_profile():
    from importlib.resources import files
    raw = files('truss').joinpath('_profiles/fresh-catalog-temporal-support.json').read_bytes()
    value = decode_owner_evidence_json(raw)
    if value['identity'] != 'truss-fresh-catalog-temporal-support' or value['version'] != '0.2':
        raise ValueError('Exact temporal support profile required')
    return {'identity': value['identity'], 'version': value['version'], 'sha256': sha256(raw).hexdigest()}


def retain_temporal_preparation(prepared, packets):
    """Issue noncompact2.1 from genuine preparation plus complete owner calls.

    This retains provenance, not native acceptance. The native route must verify
    the selected installed owner profile and independently enforce inverse
    coverage before accepting any metadata/property/cache effects.
    """
    from .preparation import (PreparedAcceptance, DocumentInterpretation, _json,
                              _require_original_preparation, _retain_original)
    from ._catalog_source_reference import DATE10_PROFILE
    _require_original_preparation(prepared)
    original = prepared.input()
    summary = decode_owner_evidence_json(prepared.report_evidence_bytes)
    if (original['supportProfile'] != DATE10_PROFILE or summary.get('interfaceVersion') != 'truss-registration-preparation/2.0'
            or type(packets) is not tuple or len(packets) != len(prepared.documents)):
        raise ValueError('Original current preparation and complete owner calls required')
    retained = []
    for document, validation, packet in zip(prepared.documents, summary['documents'], packets, strict=True):
        if validation['documentId'] != document.document.document_id:
            raise ValueError('Original document validation order required')
        declarations = temporal_declarations(document.document, packet)
        original_records = _catalog_declarations(document.document.document_id, document.source())['records']
        if [r['declaration'] for r in declarations['records']] != [r['declaration'] for r in original_records]:
            raise ValueError('Complete original accepted Record inspection required')
        retained.append({**validation, 'inspection': packet})
    report_bytes = _json({'interfaceVersion': PREPARATION, 'documents': retained})
    original['supportProfile'] = support_profile()
    return _retain_original(PreparedAcceptance(_json(original),
        tuple(DocumentInterpretation(d.document, report_bytes) for d in prepared.documents),
        prepared.provenance, report_bytes))
