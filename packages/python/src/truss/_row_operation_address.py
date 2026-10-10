"""Private candidate address codec/correspondence; never transaction authority."""
from dataclasses import dataclass
import json
from ._acceptance_json import decode_row_operation_json
from ._row_operation_custody import CustodyBody

DOMAIN = 'truss-row-operation-address/0.1.0'
MAXIMUM_BYTES = 8_388_608


@dataclass(frozen=True)
class OperationAddress:
    original: bytes
    installation: str
    writer_xid: str
    operation_ordinal: str


def _integer(value, maximum):
    if (type(value) is not str or not value or len(value) > 20
            or any(c not in '0123456789' for c in value)
            or (len(value) > 1 and value[0] == '0') or int(value) > maximum):
        raise ValueError('Original native integer string required')
    return value


def encode_row_operation_address(installation, writer_xid, operation_ordinal):
    """Candidate scalar spelling: literal UTF-8, compact JSON, standard escapes.

    Identical to the existing Python receipt codec's JSON string recipe. No
    unpaired surrogate, BOM, whitespace or newline outside strings is emitted.
    Logical bounds do not qualify serializer/allocator or original account work.
    """
    if type(installation) is not str or not installation or len(installation) > MAXIMUM_BYTES:
        raise ValueError('Original installation string required')
    _integer(writer_xid, 18446744073709551615)
    _integer(operation_ordinal, 9223372036854775807)
    try:
        original = json.dumps([DOMAIN, installation, writer_xid, operation_ordinal],
                              ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    except UnicodeError:
        raise ValueError('Original scalar Unicode required') from None
    if len(original) > MAXIMUM_BYTES:
        raise ValueError('Original address byte bound')
    return original


def decode_row_operation_address(original):
    value = decode_row_operation_json(original)
    if type(value) is not list or len(value) != 4 or value[0] != DOMAIN:
        raise ValueError('Original address domain/arity required')
    encoded = encode_row_operation_address(value[1], value[2], value[3])
    if encoded != original:
        raise ValueError('Original address spelling mismatch')
    return OperationAddress(original, value[1], value[2], value[3])


def check_custody_addresses(body, installation, actual_xid):
    """Pure correspondence against already admitted original scope projections.

    Caller strings/decoded data do not authenticate installation, transaction or
    original registry rows. Full scope admission precedes this component; native
    context/artifact/readiness/contributor checks remain separate obligations.
    """
    if type(body) is not CustodyBody:
        raise ValueError('Original custody projection required')
    _integer(actual_xid, 18446744073709551615)
    if type(installation) is not str or not installation:
        raise ValueError('Original installation projection required')
    output, previous = [], -1
    for operation in body.operations:
        if operation.identity != operation.group_identity:
            raise ValueError('Original operation/group address mismatch')
        address = decode_row_operation_address(operation.identity.encode('utf-8'))
        ordinal = int(address.operation_ordinal)
        if address.installation != installation or address.writer_xid != actual_xid or ordinal <= previous:
            raise ValueError('Original address scope/order mismatch')
        output.append(address)
        previous = ordinal
    return tuple(output)
