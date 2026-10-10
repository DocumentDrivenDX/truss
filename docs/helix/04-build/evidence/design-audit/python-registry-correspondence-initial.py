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


def check_registry_correspondence(body, installation, actual_xid, rows, maximum_rows, maximum_bytes):
    """Match all manifest contributors, retaining every supplied registry operation.

    The original descriptor/cycle/completion/row visibility/account and native
    installation/current subject authority must be admitted externally. Supplied
    rows or labels cannot prove that a database capture was complete. Noncontributors
    remain in the returned cohort for independent readiness/finalization/settlement;
    this check never selects a newest operation or treats a phase as admission.
    """
    if type(body) is not CustodyBody:
        raise ValueError('Original manifest projection required')
    addresses = check_custody_addresses(body, installation, actual_xid)
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
                or context.profile != body.profile or context.profile != group.profile
                or context.address.original != group.address.original or group.kind != row[2]
                or context.artifacts[1] != body.layout
                or context.artifacts[3].original != _original(row[9])
                or context.artifacts[8] != group.admission):
            raise ValueError('Original registry context/group mismatch')
        operation = RegistryOperation(row, context, group)
        cohort.append(operation)
        by_ordinal[row[1]] = operation
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
