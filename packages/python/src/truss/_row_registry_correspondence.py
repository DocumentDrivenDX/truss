"""Private complete-cohort projection matching; supplied rows are not authority."""
from dataclasses import dataclass
from ._operation_registry import COLUMNS, decode_operation_registry
from ._row_operation_address import MAXIMUM_BYTES, check_custody_addresses
from ._row_operation_context import OperationContext, decode_row_operation_context, check_context_group_manifest
from ._row_group_custody import GroupCustody, decode_row_group_custody
from ._row_operation_custody import CustodyBody


@dataclass(frozen=True)
class RegistryOperation:
    cells: tuple[str | None, ...]
    context: OperationContext
    group: GroupCustody


@dataclass(frozen=True)
class RegistryCorrespondence:
    cohort: tuple[RegistryOperation, ...]
    contributors: tuple[RegistryOperation, ...]


def _original(hex_cell):
    # Structural registry decoding checks ASCII, even length and hex spelling.
    # Refuse before allocating a body exceeding the independent syntax ceiling.
    if len(hex_cell) > 2 * MAXIMUM_BYTES:
        raise ValueError('Original registry carrier bound')
    return bytes.fromhex(hex_cell)


def _decode_cohort(installation, actual_xid, profile, layout, rows, maximum_rows, maximum_bytes):
    if type(rows) not in (tuple, list):
        raise ValueError('Original registry rows required')
    cells = decode_operation_registry(actual_xid, COLUMNS, rows, 'SELECT', str(len(rows)),
                                      maximum_rows, maximum_bytes)
    cohort, by_ordinal = [], {}
    for row in cells:
        context = decode_row_operation_context(_original(row[8]))
        group = decode_row_group_custody(_original(row[14]))
        if (context.address.installation != installation or context.address.writer_xid != row[0]
                or context.address.operation_ordinal != row[1]
                or context.profile != profile or context.profile != group.profile
                or context.address.original != group.address.original or group.kind != row[2]
                or context.artifacts[1] != layout
                or context.artifacts[3].original != _original(row[9])
                or context.artifacts[8] != group.admission):
            raise ValueError('Original registry context/group mismatch')
        operation = RegistryOperation(row, context, group)
        cohort.append(operation)
        by_ordinal[row[1]] = operation
    return tuple(cohort), by_ordinal


def _match_manifest(body, installation, actual_xid, cohort, by_ordinal):
    if type(body) is not CustodyBody:
        raise ValueError('Original manifest projection required')
    addresses = check_custody_addresses(body, installation, actual_xid)
    contributors = []
    for position, address in enumerate(addresses):
        original = by_ordinal.get(address.operation_ordinal)
        if original is None:
            raise ValueError('Original registry contributor missing')
        check_context_group_manifest(original.context, original.group, body, position)
        entry = body.operations[position]
        for artifact, column in ((entry.definition,9),(entry.input,10),(entry.prestate,11),
                                 (entry.candidate,12),(entry.obligation,13)):
            if artifact.original != _original(original.cells[column]):
                raise ValueError('Original registry contributor artifact mismatch')
        contributors.append(original)
    return RegistryCorrespondence(tuple(cohort),tuple(contributors))



def check_registry_correspondence(body, installation, actual_xid, rows, maximum_rows, maximum_bytes):
    """Complete supplied cohort and one manifest; native capture/authority external."""
    if type(body) is not CustodyBody:
        raise ValueError('Original manifest projection required')
    cohort, index = _decode_cohort(installation, actual_xid, body.profile, body.layout,
                                  rows, maximum_rows, maximum_bytes)
    return _match_manifest(body, installation, actual_xid, cohort, index)


@dataclass(frozen=True)
class TouchOperationCorrespondence:
    cohort: tuple[RegistryOperation, ...]
    touches: tuple[tuple[object, RegistryCorrespondence], ...]


def check_touch_operation_correspondence(touches, installation, actual_xid, profile, layout,
                                         rows, maximum_touches, maximum_rows, maximum_bytes):
    """Decode all supplied operations once, including when no touch exists.

    Profile/layout are independently supplied projections, not authenticated
    installation evidence. Complete native touch/operation visibility and same cut,
    authority, owner codec, resource accounting and readiness are external.
    Returned touch contributors share retained original cohort objects; no phase
    or noncontributor is discarded and this performs no mutation or finalization.
    """
    from ._row_touch_registry import RegistryTouch
    from ._row_operation_custody import Profile, Artifact
    if (type(profile) is not Profile or type(layout) is not Artifact
            or type(maximum_touches) is not int or not 0<=maximum_touches<=9007199254740991
            or type(touches) not in (tuple,list) or len(touches)>maximum_touches):
        raise ValueError('Original touch cohort/profile required')
    cohort, index = _decode_cohort(installation, actual_xid, profile, layout,
                                  rows, maximum_rows, maximum_bytes)
    output=[];seen=set()
    for touch in touches:
        if (type(touch) is not RegistryTouch or type(touch.cells) is not tuple
                or len(touch.cells)!=12 or type(touch.custody) is not CustodyBody
                or touch.cells[0]!=actual_xid
                or touch.cells[8:12]!=tuple(v.hex() for v in
                    (touch.custody.layout.original,touch.custody.home.original,
                     touch.custody.owner_property.original,touch.custody.original))
                or touch.cells[:6] in seen or touch.custody.profile!=profile
                or touch.custody.layout!=layout):
            raise ValueError('Original touch cohort correspondence mismatch')
        seen.add(touch.cells[:6])
        matched = _match_manifest(touch.custody,installation,actual_xid,cohort,index)
        output.append((touch,matched))
    return TouchOperationCorrespondence(cohort,tuple(output))


def resolve_unfinished_operation(correspondence):
    """OC02 selection from an independently admitted complete captured cohort.

    Commit uses the entire cohort instead; it must not call this observer selector.
    Native custody/current authority and liveness remain external, and neither
    this projection type nor a phase label grants permission to produce effects.
    """
    if type(correspondence) is not RegistryCorrespondence:
        raise ValueError('Original complete registry correspondence required')
    selected = None
    for operation in correspondence.cohort:
        if operation.cells[3] != 'application_finalized':
            if selected is not None:
                raise ValueError('Original unfinished operation is ambiguous')
            selected = operation
    if selected is None:
        raise ValueError('Original unfinished operation is missing')
    return selected
