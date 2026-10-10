"""Private native scalar carrier shape; codec/domain/native value meaning external."""
from ._row_image import NativeRowImage

# Original scalar columns 3..10; timestamp instant is the sole optional payload.
FAMILIES = {
    b'string': ({3}, set()),
    b'boolean': ({4}, set()),
    b'integer': ({5, 6}, set()),
    b'decimal': ({5, 6}, set()),
    b'binary': ({7}, set()),
    b'timestamp': ({8}, {9}),
    b'opaque': ({10}, set()),
}


def check_scalar_shape(image):
    """Retain original image after checking family-exclusive physical carriers.

    Does not parse numeric cells/tokens, compare timestamp projections, infer
    authored definitions or grant original capture/authority correspondence.
    """
    def refuse(): raise ValueError('row-image-scalar-shape:unavailable')
    if type(image) is not NativeRowImage or image.kind != 'scalar': refuse()
    try:
        family = FAMILIES.get(bytes(image.payload(2)))
        if family is None: refuse()
        required, optional = family
        present = {i for i in range(3, 11) if image.payload(i) is not None}
        if not required <= present or not present <= required | optional: refuse()
        if any(not len(image.payload(i)) for i in (11, 12)): refuse()
        if 6 in required and not len(image.payload(6)): refuse()
    except (TypeError, ValueError, IndexError):
        refuse()
    return image
