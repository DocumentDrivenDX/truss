"""Private complete touch projection; supplied native cells are not authority."""
from dataclasses import dataclass
from ._operation_registry import _integer
from ._row_operation_address import MAXIMUM_BYTES, check_custody_addresses
from ._row_operation_custody import CustodyBody, decode_row_operation_custody

COLUMNS = ('transaction_id','owner_kind','owner_id','owner_discriminator_id',
           'property_owner_type_id','property_id','dirty_generation','sealed_generation',
           'original_layout_bytes_hex','original_home_bytes_hex',
           'original_owner_property_bytes_hex','original_operation_bytes_hex')

@dataclass(frozen=True)
class RegistryTouch:
    cells: tuple[str | None, ...]
    custody: CustodyBody


def _signed(value, bits):
    if type(value) is not str or not value or len(value)>20:
        raise ValueError('touch-registry:unavailable')
    digits=value[1:] if value.startswith('-') else value
    if (not digits or any(c not in '0123456789' for c in digits)
            or len(digits)>1 and digits[0]=='0' or value=='-0'
            or not -(1 << (bits-1)) <= int(value) < (1 << (bits-1))):
        raise ValueError('touch-registry:unavailable')


def decode_touch_registry(installation, actual_xid, columns, rows, command,
                          affected_rows, maximum_rows, maximum_bytes):
    """Retain the complete supplied multiset and original manifest correspondence.

    Original native descriptor/cycle/capture completeness, same cut, resource
    accounting, installed authority and owner-property semantic admission are
    external. A retained seal may precede dirty generation; this does not declare
    readiness, select an operation, advance a generation or perform any DML.
    """
    def refuse(): raise ValueError('touch-registry:unavailable')
    _integer(actual_xid,18446744073709551615)
    for bound in (maximum_rows,maximum_bytes):
        if type(bound) is not int or not 0<=bound<=9007199254740991:refuse()
    if (type(columns) not in (tuple,list) or tuple(columns)!=COLUMNS
            or type(rows) not in (tuple,list) or len(rows)>maximum_rows
            or command!='SELECT' or type(affected_rows) is not str
            or affected_rows!=str(len(rows))):refuse()
    output=[];seen=set();total=0
    for row in rows:
        if type(row) not in (tuple,list) or len(row)!=12:refuse()
        cells=tuple(row)
        for index,value in enumerate(cells):
            if value is None:
                if index!=7:refuse()
            else:
                if type(value) is not str or len(value)>maximum_bytes-total or not value.isascii():refuse()
                total+=len(value)
        if cells[0]!=actual_xid or cells[1] not in ('object','edge'):refuse()
        for index in range(2,6):_signed(cells[index],64 if index==2 else 32)
        key=cells[:6]
        if key in seen:refuse()
        seen.add(key)
        _integer(cells[6],9223372036854775807)
        if cells[6]=='0':refuse()
        if cells[7] is not None:
            _integer(cells[7],9223372036854775807)
            if cells[7]=='0' or int(cells[7])>int(cells[6]):refuse()
        for value in cells[8:]:
            if (not value or len(value)>2*MAXIMUM_BYTES or len(value)%2
                    or any(c not in '0123456789abcdef' for c in value)):refuse()
        originals=tuple(bytes.fromhex(value) for value in cells[8:])
        body=decode_row_operation_custody(originals[3])
        if originals[:3]!=(body.layout.original,body.home.original,body.owner_property.original):refuse()
        check_custody_addresses(body,installation,actual_xid)
        output.append(RegistryTouch(cells,body))
    return tuple(output)
