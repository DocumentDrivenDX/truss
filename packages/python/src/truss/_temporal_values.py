# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit selected temporal transport; ordinary ExactValue stays unchanged."""
from .contracts import LocalTimestampValue, validate_local_timestamp_text
from ._record_schema import _wire_cell

PROFILE = 'truss-exact-value-temporal/0.1'


def wire_temporal_cell(value):
    if type(value) is LocalTimestampValue:
        return {'kind': 'localTimestamp', 'text': validate_local_timestamp_text(value.text)}
    result = _wire_cell(value)
    if result is None:
        raise ValueError('Selected scalar temporal transport required')
    if result['kind'] in ('sequence', 'map'):
        raise ValueError('Temporal container transport is outside selected profile')
    return result


def local_timestamp_cell(cell):
    if type(cell) is not dict or set(cell) != {'kind', 'text'} or cell['kind'] != 'localTimestamp':
        raise ValueError('Closed native local timestamp cell required')
    return LocalTimestampValue(text=cell['text'])
