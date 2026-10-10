"""Private complete result framing; original producer/scope/cut/authority external."""
from dataclasses import dataclass
from ._row_image import decode_row_image
from ._row_event_attribution import _index

COLUMNS = ('image_kind', 'original_image')


@dataclass(frozen=True)
class RowImageCapture:
    columns: tuple
    original_rows: tuple
    images: tuple
    command: str
    affected_rows: str


def decode_row_image_capture(columns, rows, command, affected_rows,
                             maximum_rows, maximum_bytes):
    """Retain exact immutable cells after an independently admitted native read.

    SELECT completion covers this result, not completeness of its selected scope.
    No authority is minted by this object; full original operation/context/capture
    correspondence and descriptor/driver/account admission must precede use.
    Bounds cover retained input cells, not whole interpreter/copy/work allocation.
    """
    def refuse(): raise ValueError('row-image-capture:unavailable')
    for bound in (maximum_rows, maximum_bytes):
        if type(bound) is not int or not 0 <= bound <= 9007199254740991: refuse()
    if (type(columns) not in (tuple, list) or len(columns) != 2
            or any(type(value) is not str for value in columns)
            or tuple(columns) != COLUMNS or type(rows) not in (tuple, list)
            or len(rows) > maximum_rows or type(command) is not str
            or command != 'SELECT' or type(affected_rows) is not str
            or affected_rows != str(len(rows))): refuse()
    # Complete input count/type/byte preflight precedes every image decoder.
    total = 0
    originals = []
    for row in rows:
        if type(row) not in (tuple, list) or len(row) != 2: refuse()
        kind, original = row
        if type(kind) is not str or kind not in ('state', 'node', 'scalar') or type(original) is not bytes: refuse()
        if len(kind) > maximum_bytes - total: refuse()
        total += len(kind)
        if len(original) > maximum_bytes - total: refuse()
        total += len(original)
        originals.append((kind, original))
    images = []
    try:
        for kind, original in originals:
            image = decode_row_image(original)
            if image.kind != kind: refuse()
            images.append(image)
        _index(images)  # Original image keys and node/state correspondence only.
    except ValueError:
        refuse()
    return RowImageCapture(tuple(columns), tuple(originals), tuple(images), command, affected_rows)
