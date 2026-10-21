# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private adapter for the installed read-only condition preview routine."""
from __future__ import annotations

import json
import re
from typing import Any

from .contracts import ProfilePin
from .execution import Error, Ok
from .preview import (GroupConditionPreviewInput, PreviewConditionResult,
                      PreviewObservationBasis, PreviewObserved,
                      PreviewRefused)

_RULES = frozenset(('object_exists', 'key_absent', 'property_equals',
                    'relationship_absent', 'relationship_count'))
_REVISION = re.compile(r'(?:0|[1-9][0-9]{0,9})\Z')


def _wire(value: Any) -> Any:
    from dataclasses import fields, is_dataclass
    if is_dataclass(value):
        result = {}
        for member in fields(value):
            child = getattr(value, member.name)
            name = member.name.split('_')[0] + ''.join(
                part.title() for part in member.name.split('_')[1:])
            result[name] = _wire(child)
        return result
    if type(value) is tuple:
        return [_wire(child) for child in value]
    return value


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf8')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate native preview member')
        result[key] = value
    return result


def _no_numbers(_token):
    raise ValueError('Numeric native preview token')


def _decode_preview_result(raw: bytes, expected: GroupConditionPreviewInput) -> PreviewObserved:
    if type(raw) is not bytes or not 1 <= len(raw) <= 1_048_576:
        raise ValueError('Bounded native preview response required')
    value = json.loads(raw, object_pairs_hook=_unique_object, parse_int=_no_numbers,
                       parse_float=_no_numbers, parse_constant=_no_numbers)
    if type(value) is not dict or set(value) != {'outcome', 'conditions', 'basis'} or value['outcome'] != 'observed':
        raise ValueError('Exact native observed-preview response required')
    if type(value['basis']) is not dict or set(value['basis']) != {
            'catalogRevision', 'snapshot', 'sourceEpoch', 'releaseId',
            'releaseSha256', 'layoutProfile'}:
        raise ValueError('Complete original preview basis required')
    basis = value['basis']
    if (type(basis['catalogRevision']) is not str or not _REVISION.fullmatch(basis['catalogRevision'])
            or int(basis['catalogRevision']) < 1
            or type(basis['snapshot']) is not str or not basis['snapshot']
            or len(basis['snapshot'].encode('utf8')) > 4096
            or type(basis['sourceEpoch']) is not str or not basis['sourceEpoch']
            or len(basis['sourceEpoch'].encode('utf8')) > 128
            or type(basis['releaseId']) is not str or not basis['releaseId']
            or type(basis['releaseSha256']) is not str
            or re.fullmatch('[0-9a-f]{64}', basis['releaseSha256']) is None
            or type(basis['layoutProfile']) is not dict
            or set(basis['layoutProfile']) != {'identity', 'version', 'sha256'}):
        raise ValueError('Canonical observed preview basis required')
    layout = ProfilePin(**basis['layoutProfile'])
    if layout != expected.layout_profile:
        raise ValueError('Observed layout profile must match the original preview input')
    if type(value['conditions']) is not list or len(value['conditions']) != len(expected.preconditions):
        raise ValueError('Complete original condition preview required')
    decoded = []
    for condition, original in zip(value['conditions'], expected.preconditions, strict=True):
        if type(condition) is not dict or set(condition) != {'conditionId', 'rule', 'passed'}:
            raise ValueError('Closed original condition preview entry required')
        if (condition['conditionId'] != original.id or condition['rule'] != original.condition
                or condition['rule'] not in _RULES or type(condition['passed']) is not bool):
            raise ValueError('Original ordered condition preview correspondence required')
        decoded.append(PreviewConditionResult(condition_id=condition['conditionId'],
            rule=condition['rule'], passed=condition['passed']))
    return PreviewObserved(basis=PreviewObservationBasis(
        catalog_revision=basis['catalogRevision'], snapshot=basis['snapshot'],
        source_epoch=basis['sourceEpoch'], release_id=basis['releaseId'],
        release_sha256=basis['releaseSha256'], layout_profile=layout),
        conditions=tuple(decoded))


def preview_group_conditions(host, transaction, input, documents, manifest, digest, pin_cursor):
    """Issue one advisory native statement; never begin or settle the host transaction."""
    from .preparation import CatalogDocument
    from .psycopg_host import PsycopgHost
    if (type(host) is not PsycopgHost or type(input) is not GroupConditionPreviewInput
            or type(documents) is not tuple or not 1 <= len(documents) <= 512
            or any(type(item) is not CatalogDocument for item in documents)):
        return Ok(PreviewRefused(reason='invalid_input'))
    try:
        original_input = _json_bytes(_wire(input))
        original_documents = _json_bytes([{'documentId': item.document_id,
                                           'sourceText': item.content.decode('utf8')}
                                          for item in documents])
    except (UnicodeError, ValueError, TypeError):
        return Ok(PreviewRefused(reason='invalid_input'))
    if len(original_input) > 1_048_576 or len(original_documents) > 4_194_304:
        return Ok(PreviewRefused(reason='resource'))

    def observe(cursor, _observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.preview_group_conditions(%s,%s,%s,%s)',
            (original_input, original_documents, manifest['releaseId'], digest), prepare=False)
        raw = bytes(cursor.fetchone()[0])
        return _decode_preview_result(raw, input)

    result = host._run_operation(transaction, observe, function_call=True)
    if isinstance(result, Error) and result.error.code == 'execution_obligation':
        if result.error.sql_state == '42501':
            return Ok(PreviewRefused(reason='unauthorized'))
        if result.error.sql_state == '54000':
            return Ok(PreviewRefused(reason='resource'))
        if result.error.sql_state == '0A000':
            return Ok(PreviewRefused(reason='profile'))
        if result.error.sql_state == '55P03':
            return Ok(PreviewRefused(reason='observation'))
        if result.error.sql_state == '22023':
            return Ok(PreviewRefused(reason='invalid_input'))
    return result
