"""Private complete-frame syntax candidate, not a driver or custody issuer.

Only immutable already-retained bytes are accepted. These candidate limits do
not qualify ingress, allocation accounting, command cycles or publication.
"""
from dataclasses import dataclass
import struct

MAX_FRAME = 1048576
MAX_COLUMNS = 4096


@dataclass(frozen=True)
class Column:
    name: bytes
    table_oid: int
    attribute: int
    type_oid: int
    type_size: int
    modifier: int
    format: int


class Frame:
    def __init__(self, source: bytes, kind: bytes):
        if type(source) is not bytes:
            raise ValueError('Immutable frame bytes required')
        if len(source) > MAX_FRAME or len(source) < 7:
            raise ValueError('Frame capacity or header')
        length = struct.unpack_from('!i', source, 1)[0]
        if source[:1] != kind or length < 6 or length + 1 != len(source):
            raise ValueError('Incomplete or wrong frame')
        self.source = source
        self.offset = 5

    def take(self, size: int) -> bytes:
        if size < 0 or size > len(self.source) - self.offset:
            raise ValueError('Truncated frame member')
        start = self.offset
        self.offset += size
        return self.source[start:self.offset]

    def count(self) -> int:
        count = struct.unpack('!H', self.take(2))[0]
        if count > MAX_COLUMNS:
            raise ValueError('Column capacity')
        return count

    def finish(self):
        if self.offset != len(self.source):
            raise ValueError('Trailing frame bytes')


def row_description(source: bytes) -> tuple[Column, ...]:
    frame = Frame(source, b'T')
    columns = []
    for _ in range(frame.count()):
        end = source.find(b'\0', frame.offset)
        if end < 0:
            raise ValueError('Unterminated column name')
        name = frame.take(end - frame.offset)
        name.decode('utf8', errors='strict')
        frame.take(1)
        metadata = struct.unpack('!IhIhih', frame.take(18))
        if metadata[-1] not in (0, 1):
            raise ValueError('Unsupported field format')
        columns.append(Column(name, *metadata))
    frame.finish()
    return tuple(columns)


def data_row(source: bytes, expected_columns: int) -> tuple[bytes | None, ...]:
    if type(expected_columns) is not int or not 0 <= expected_columns <= MAX_COLUMNS:
        raise ValueError('Invalid expected column count')
    frame = Frame(source, b'D')
    count = frame.count()
    if count != expected_columns:
        raise ValueError('Column count mismatch')
    cells = []
    for _ in range(count):
        size = struct.unpack('!i', frame.take(4))[0]
        if size < -1:
            raise ValueError('Invalid cell length')
        cells.append(None if size == -1 else frame.take(size))
    frame.finish()
    return tuple(cells)
