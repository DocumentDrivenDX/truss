"""Private physical row-home forest check; original scope/meaning/authority external."""
from ._row_image_capture import RowImageCapture
from ._row_event_attribution import _index, _integer


def check_row_image_tree(capture):
    """Check all retained nodes/payloads; never infer authorized logical absence.

    Consumes a bounded capture. Definition/member/scalar codec meaning, original
    capture/context, current authority and native publication remain independent.
    Iterative reachability avoids recursion and walks each node/edge once.
    """
    def refuse(): raise ValueError('row-image-tree:unavailable')
    if type(capture) is not RowImageCapture: refuse()
    # Constructor equality is not original custody; correspondence precedes use.
    try:
        index = _index(capture.images)
        states = {key[1]: image for key, image in index.items() if key[0] == 'state'}
        nodes = {(key[1], key[2]): image for key, image in index.items() if key[0] == 'node'}
        scalars = {(key[1], key[2]): image for key, image in index.items() if key[0] == 'scalar'}
        children = {}; slots = {}; sequences = {}; roots = []
        for state, image in states.items():
            root = (state, _integer(image, 8, 8))
            if root not in nodes: refuse()
            roots.append(root)
        root_set = set(roots)
        for identity, node in nodes.items():
            state, node_id = identity
            if state not in states: refuse()
            kind = bytes(node.payload(7))
            if kind not in (b'scalar', b'null', b'sequence', b'map', b'record', b'structured'): refuse()
            slot = bytes(node.payload(3))
            parent_raw = node.payload(2)
            ordinal, map_key, field = node.payload(4), node.payload(5), node.payload(6)
            if parent_raw is None:
                if identity not in root_set or slot != b'root' or any(v is not None for v in (ordinal, map_key, field)): refuse()
            else:
                parent = (state, _integer(node, 2, 8))
                if parent not in nodes or parent == identity or identity in root_set: refuse()
                parent_kind = bytes(nodes[parent].payload(7))
                if slot == b'sequence':
                    if parent_kind != b'sequence' or ordinal is None or map_key is not None or field is not None: refuse()
                    value = _integer(node, 4, 8)
                    if value < 0: refuse()
                    sequences.setdefault(parent, []).append(value)
                    child_slot = value
                elif slot == b'map':
                    if parent_kind != b'map' or map_key is None or ordinal is not None or field is not None: refuse()
                    child_slot = bytes(map_key)
                elif slot == b'record':
                    if parent_kind not in (b'record', b'structured') or field is None or not len(field) or ordinal is not None or map_key is not None: refuse()
                    child_slot = bytes(field)
                else: refuse()
                occupied = slots.setdefault(parent, set())
                if child_slot in occupied: refuse()
                occupied.add(child_slot)
                children.setdefault(parent, []).append(identity)
            if (identity in scalars) != (kind == b'scalar'): refuse()
        if any(identity not in nodes for identity in scalars): refuse()
        for values in sequences.values():
            # Nonnegative unique n slots are contiguous iff each is less than n.
            if any(value >= len(values) for value in values): refuse()
        pending = list(roots); seen = set()
        while pending:
            identity = pending.pop()
            if identity in seen: refuse()
            seen.add(identity)
            pending.extend(children.get(identity, ()))
        if len(seen) != len(nodes): refuse()
    except (ValueError, TypeError):
        refuse()
    return capture
