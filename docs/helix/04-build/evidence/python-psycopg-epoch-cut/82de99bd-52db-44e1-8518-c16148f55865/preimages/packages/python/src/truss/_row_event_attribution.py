"""Private complete image correspondence/attribution; no original event authority."""
from dataclasses import dataclass
import struct
from ._row_image import NativeRowImage


@dataclass(frozen=True)
class OwnerProperty:
    kind: str
    owner_id: str
    discriminator_id: str
    property_owner_type_id: str
    property_id: str


@dataclass(frozen=True)
class EventAttribution:
    old_image: NativeRowImage | None
    new_image: NativeRowImage | None
    old_owner: OwnerProperty | None
    new_owner: OwnerProperty | None
    touch_owners: tuple[OwnerProperty, ...]


def _integer(image, index, width):
    value = image.payload(index)
    if value is None or len(value) != width:
        raise ValueError('Original native attribution integer required')
    return struct.unpack('!q' if width == 8 else '!i', value)[0]


def _key(image):
    if type(image) is not NativeRowImage or image.kind not in ('state','node','scalar'):
        raise ValueError('Original native attribution image required')
    state = _integer(image, 0, 8)
    if state <= 0:
        raise ValueError('Original positive native state identity required')
    if image.kind == 'state':
        return ('state', state)
    node = _integer(image, 1, 8)
    if node <= 0:
        raise ValueError('Original positive native node identity required')
    return (image.kind, state, node)


def _index(images):
    result, node_states = {}, {}
    for image in images:
        key = _key(image)
        if key in result:
            raise ValueError('Original attribution image identity ambiguous')
        if image.kind != 'state':
            previous = node_states.setdefault(key[2], key[1])
            if previous != key[1]:
                raise ValueError('Original node/state association conflicting')
        result[key] = image
    return result


def _attribute(image, originals):
    key = _key(image)
    retained = originals.get(key)
    if retained is None or retained.original != image.original:
        raise ValueError('Original event image correspondence missing')
    state = image if image.kind == 'state' else originals.get(('state', key[1]))
    if state is None:
        raise ValueError('Original state association missing')
    if image.kind == 'scalar' and ('node', key[1], key[2]) not in originals:
        raise ValueError('Original node association missing')
    kind = bytes(state.payload(1)).decode('utf8')
    if kind == 'object':
        owner, discriminator = _integer(state, 2, 8), _integer(state, 3, 4)
        if state.payload(4) is not None or state.payload(5) is not None:
            raise ValueError('Original object association mixed')
    elif kind == 'edge':
        owner, discriminator = _integer(state, 4, 8), _integer(state, 5, 4)
        if state.payload(2) is not None or state.payload(3) is not None:
            raise ValueError('Original edge association mixed')
    else:
        raise ValueError('Original owner kind refused')
    property_owner, property_id = _integer(state, 6, 4), _integer(state, 7, 4)
    if kind == 'object' and property_owner != discriminator:
        raise ValueError('Original object property owner mismatch')
    # Preserve signed native owner/catalog identities. Edge association meaning
    # is independently admitted; its property owner is not its discriminator.
    return OwnerProperty(kind,str(owner),str(discriminator),str(property_owner),str(property_id))


def attribute_row_event(event, old_image, new_image, prestate, candidate,
                        maximum_images, maximum_bytes):
    """Match complete supplied side images, then project event-local touch owners.

    Original relation/event/cut/prestate/candidate/allocation completeness, scope,
    current authority and held guards must be admitted independently before use.
    A matching projection grants no semantic contribution permission. Bounds cover
    supplied count/bytes, not full host/native allocation/work/deadline accounting.
    """
    if type(event) is not str or event not in ('INSERT','UPDATE','DELETE'):
        raise ValueError('Original row event required')
    for bound in (maximum_images, maximum_bytes):
        if type(bound) is not int or not 0 <= bound <= 9007199254740991:
            raise ValueError('Original finite image bound required')
    if type(prestate) is not tuple or type(candidate) is not tuple:
        raise ValueError('Original immutable side image collections required')
    if len(prestate) + len(candidate) > maximum_images:
        raise ValueError('Original attribution image count bound')
    total = 0
    for side in (prestate, candidate):
        for image in side:
            if type(image) is not NativeRowImage or len(image.original) > maximum_bytes - total:
                raise ValueError('Original attribution image byte bound')
            total += len(image.original)
    if ((event == 'INSERT' and (old_image is not None or new_image is None))
            or (event == 'DELETE' and (old_image is None or new_image is not None))
            or (event == 'UPDATE' and (old_image is None or new_image is None))):
        raise ValueError('Original event side availability mismatch')
    if any(image is not None and type(image) is not NativeRowImage for image in (old_image,new_image)):
        raise ValueError('Original native event images required')
    if old_image is not None and new_image is not None and old_image.kind != new_image.kind:
        raise ValueError('Original event relation-kind mismatch')
    before, after = _index(prestate), _index(candidate)
    old = _attribute(old_image, before) if old_image is not None else None
    new = _attribute(new_image, after) if new_image is not None else None
    owners = tuple(dict.fromkeys(owner for owner in (old, new) if owner is not None))
    return EventAttribution(old_image,new_image,old,new,owners)
