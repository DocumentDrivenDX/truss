"""Private retained single-text-report DataRow syntax; no ingress/account authority.

The caller must separately admit original RowDescription OID 25, format 0 and
UTF8 encoding, command settlement, source custody and allocation accounting.
This decoder never interprets a completed cell as commit evidence.
"""
import struct

MAX_REPORT_BYTES = 4194304
MAX_REPORT_FRAME = MAX_REPORT_BYTES + 11


def report_cell(source):
    if type(source) is not bytes:
        raise ValueError('Immutable report frame required')
    if not 11 <= len(source) <= MAX_REPORT_FRAME:
        raise ValueError('Report frame capacity')
    if source[0:1] != b'D':
        raise ValueError('Report DataRow required')
    length, columns, cell_length = struct.unpack_from('!iHi', source, 1)
    if length != len(source) - 1 or columns != 1:
        raise ValueError('Incomplete report frame or column count')
    if cell_length < 0 or cell_length != len(source) - 11:
        raise ValueError('Null or incomplete report cell')
    return source[11:]
