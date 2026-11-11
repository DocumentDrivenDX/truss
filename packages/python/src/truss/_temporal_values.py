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
    return result


def local_timestamp_cell(cell):
    if type(cell) is not dict or set(cell) != {'kind', 'text'} or cell['kind'] != 'localTimestamp':
        raise ValueError('Closed native local timestamp cell required')
    return LocalTimestampValue(text=cell['text'])


def logical_object_cell(value, *, local=False):
    """Shared direct-read cell decoder with an explicit provider discriminator.

    Local is top-level only. Ordinary container descendants and retained unknown
    content keep their old exact value domain irrespective of installed release.
    """
    if type(value) is not dict:
        if value is None or type(value) in (str,bool):return value
        raise ValueError('Admitted direct object primitive required')
    from .contracts import TextValue,NullValue,BooleanValue,SequenceValue,MapValue,MapEntry
    def exact(cell):
        if type(cell) is not dict:raise ValueError('Exact native cell required')
        if cell.get('kind')=='null' and cell=={'kind':'null'}:return NullValue()
        if cell.get('kind')=='boolean' and set(cell)=={'kind','value'}:return BooleanValue(value=cell['value'])
        if cell.get('kind')=='sequence' and set(cell)=={'kind','items'}:
            return SequenceValue(items=tuple(exact(child) for child in cell['items']))
        if cell.get('kind')=='map' and set(cell)=={'kind','entries'}:
            return MapValue(entries=tuple(MapEntry(key=entry['key'],value=exact(entry['value'])) for entry in cell['entries']))
        if set(cell)!={'kind','text'}:raise ValueError('Closed exact native scalar required')
        return TextValue(kind=cell['kind'],text=cell['text'])
    if value.get('kind')=='localTimestamp':
        if not local:raise ValueError('Local output requires explicit temporal provider')
        return local_timestamp_cell(value)
    return exact(value)
