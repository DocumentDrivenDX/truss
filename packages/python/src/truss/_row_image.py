"""Private PostgreSQL16.15 candidate binary image framing; no event authority."""
from dataclasses import dataclass
import struct

MAXIMUM_BYTES = 8_388_608
# Complete original ordered OIDs/nullability, separately checked natively before
# encoding. Payload interpretation and installed profile/current authority remain
# independent; these are PostgreSQL cells, not canonical logical UMF values.
PROFILES = {
    'state': ((20,25,20,23,20,23,23,23,20,17,17,17,17),
              (True,True,False,False,False,False,True,True,True,True,True,True,True)),
    'node': ((20,20,20,25,20,25,17,25,17,17),
             (True,True,False,True,False,False,False,True,True,True)),
    'scalar': ((20,20,25,25,16,1700,25,17,25,1184,17,17,17),
               (True,True,True,False,False,False,False,False,False,False,False,True,True)),
}


@dataclass(frozen=True)
class NativeCell:
    type_oid: int
    offset: int
    length: int | None


@dataclass(frozen=True)
class NativeRowImage:
    original: bytes
    kind: str
    cells: tuple[NativeCell, ...]

    def payload(self, index):
        """Read-only original span; NULL is None, present empty bytes is a view."""
        if type(index) is not int or not 0 <= index < len(self.cells):
            raise ValueError('Original native cell index required')
        cell = self.cells[index]
        if cell.length is None:
            return None
        return memoryview(self.original)[cell.offset:cell.offset + cell.length]


def decode_row_image(original: bytes) -> NativeRowImage:
    """Check complete bounded framing and retain opaque native payloads.

    No numeric/temporal coercion, artifact semantics, native provenance or resource
    authority is inferred. This checks wire structure and primitive widths/UTF8/
    Boolean representation; native numeric and temporal meaning stay external.
    """
    if type(original) is not bytes or not 1 <= len(original) <= MAXIMUM_BYTES:
        raise ValueError('Bounded immutable native row image required')
    kind = next((key for key in PROFILES if original.startswith(
        ('truss.row-image.' + key + '/0.1').encode() + b'\0')), None)
    if kind is None:
        raise ValueError('Original native row image domain required')
    position = len(('truss.row-image.' + kind + '/0.1').encode()) + 1
    oids, required = PROFILES[kind]
    if len(original) - position < 4 or struct.unpack_from('!i', original, position)[0] != len(oids):
        raise ValueError('Complete original native field count required')
    position += 4
    cells = []
    for oid, mandatory in zip(oids, required):
        if len(original) - position < 8:
            raise ValueError('Complete original native cell header required')
        actual_oid, length = struct.unpack_from('!Ii', original, position)
        position += 8
        if actual_oid != oid or length < -1 or (length == -1 and mandatory):
            raise ValueError('Original native type/null profile required')
        if length == -1:
            cells.append(NativeCell(oid, position, None))
            continue
        if length > len(original) - position:
            raise ValueError('Complete original native payload required')
        width = {20:8, 23:4, 16:1, 1184:8}.get(oid)
        if width is not None and length != width:
            raise ValueError('Original native primitive width required')
        if oid == 16 and original[position] not in (0, 1):
            raise ValueError('Original native Boolean representation required')
        if oid == 25:
            # Strict scalar UTF8 validation; the full original bytes stay intact.
            try:
                memoryview(original)[position:position + length].tobytes().decode('utf8')
            except UnicodeError:
                raise ValueError('Original native UTF8 text required') from None
            if original.find(b'\0', position, position + length) != -1:
                raise ValueError('Original native text NUL refused')
        cells.append(NativeCell(oid, position, length))
        position += length
    if position != len(original):
        raise ValueError('Original native trailing bytes refused')
    return NativeRowImage(original, kind, tuple(cells))
