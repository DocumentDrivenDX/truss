# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fixed private pending writer input; no registered family or authority."""
from dataclasses import dataclass
import re
from ._native_pg8000 import NativeBoundaryRefusal

@dataclass(frozen=True, slots=True)
class NativeStringReplacementInput:
    state_id: str
    expected_version: str
    replacement: str
    original_token: bytes

@dataclass(frozen=True, slots=True)
class EncodedStringReplacement:
    original_input: NativeStringReplacementInput
    ordinal: str
    sql: str
    encoded_bytes: int

def encode_string_replacement(value, ordinal):
    if type(value) is not NativeStringReplacementInput:
        raise NativeBoundaryRefusal('Closed pending string input required')
    for number, minimum, maximum in ((ordinal,0,9223372036854775807),
        (value.state_id,1,9223372036854775807),(value.expected_version,1,9223372036854775806)):
        if (type(number) is not str or len(number)>19
            or re.fullmatch(r'0|[1-9][0-9]*',number) is None or not minimum<=int(number)<=maximum):
            raise NativeBoundaryRefusal('Canonical native integer required')
    if type(value.replacement) is not str or len(value.replacement)>65536 or '\0' in value.replacement:
        raise NativeBoundaryRefusal('Exact native string required')
    try: text=value.replacement.encode('utf8')
    except UnicodeError: raise NativeBoundaryRefusal('Lossless native string required') from None
    if (len(text)>65536 or type(value.original_token) is not bytes
        or not 1<=len(value.original_token)<=262144):
        raise NativeBoundaryRefusal('Pending input byte capacity exhausted')
    # Account for every fixed delimiter, casts, wrapper and Q framing before
    # allocating hexadecimal copies. No arbitrary SQL is admitted.
    fixed=("SELECT writer_xid, ordinal, context_hex FROM truss.runtime_write_existing_string_pending("
           +ordinal+'::pg_catalog.int8,'+value.state_id+'::pg_catalog.int8,'
           +value.expected_version+"::pg_catalog.int8,pg_catalog.convert_from(pg_catalog.decode('"
           +"','hex'),'UTF8'),pg_catalog.decode('"+"','hex'))")
    encoded_size=len(fixed)+2*len(text)+2*len(value.original_token)
    wrapper_size=len('SELECT admitted.writer_xid, admitted.ordinal, admitted.context_hex, '
        'pg_catalog.pg_current_xact_id()::pg_catalog.text AS actual_writer_xid FROM (')+len(') AS admitted')
    if encoded_size+wrapper_size+6>1048576:
        raise NativeBoundaryRefusal('Full original writer SQL capacity exhausted')
    sql=("SELECT writer_xid, ordinal, context_hex FROM truss.runtime_write_existing_string_pending("
         +ordinal+'::pg_catalog.int8,'+value.state_id+'::pg_catalog.int8,'
         +value.expected_version+"::pg_catalog.int8,pg_catalog.convert_from(pg_catalog.decode('"
         +text.hex()+"','hex'),'UTF8'),pg_catalog.decode('"+value.original_token.hex()+"','hex'))")
    return EncodedStringReplacement(value,ordinal,sql,encoded_size)
