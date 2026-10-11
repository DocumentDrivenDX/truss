"""Private fixed admission request encoding; supplies no issuance or authority.

Actual dispatch must bind original artifact provenance, the retained issued
attempt and installed family producer. This module never enables admission.
"""
from dataclasses import dataclass
import re
from ._operation_admission import AdmissionRefusal

_FUNCTIONS = {
    'base': 'runtime_admit_operation',
    'asserted': 'runtime_admit_operation_with_asserted_origin',
    'epoch': 'runtime_admit_operation_with_epoch_context',
    'configuration': 'runtime_admit_operation_with_configuration_context',
}

@dataclass(frozen=True, slots=True)
class NativeAdmissionInput:
    family: str
    kind: str
    artifacts: tuple[bytes, ...]
    asserted: bytes | None = None
    capture_profile: bytes | None = None
    installation: str | None = None
    source_epoch: str | None = None
    incarnation: str | None = None
    configuration_profile: bytes | None = None

@dataclass(frozen=True, slots=True)
class EncodedAdmissionRequest:
    original_input: NativeAdmissionInput
    ordinal: str
    sql: str
    encoded_bytes: int
    scope: str = 'request_encoding_only'


def _text(value, maximum):
    if type(value) is not str or not value or '\0' in value or len(value) > maximum:
        raise AdmissionRefusal('Exact bounded native text required')
    try:
        encoded = value.encode('utf8', errors='strict')
    except UnicodeError as error:
        raise AdmissionRefusal('Lossless native text required') from error
    if len(encoded) > maximum:
        raise AdmissionRefusal('Native UTF8 text capacity exhausted')
    return encoded


def _binary(value, maximum):
    if type(value) is not bytes or not 1 <= len(value) <= maximum:
        raise AdmissionRefusal('Exact bounded artifact bytes required')
    return value


def encode_admission_request(value, ordinal, *, maximum_sql_bytes=1_048_576):
    """Encode only; a valid decimal is never an original issuance witness."""
    if (type(value) is not NativeAdmissionInput or type(value.family) is not str
            or value.family not in _FUNCTIONS or type(value.artifacts) is not tuple
            or len(value.artifacts) != 6):
        raise AdmissionRefusal('Closed original family input required')
    if (type(ordinal) is not str or len(ordinal) > 19
            or re.fullmatch(r'0|[1-9][0-9]*', ordinal) is None
            or int(ordinal) > 9223372036854775807):
        raise AdmissionRefusal('Canonical native bigint ordinal required')
    if type(maximum_sql_bytes) is not int or not 1 <= maximum_sql_bytes <= 16_777_216:
        raise AdmissionRefusal('Finite exact SQL encoding capacity required')
    artifacts = tuple(_binary(item, 1_048_576) for item in value.artifacts)
    if sum(map(len, artifacts)) > 4_194_304:
        raise AdmissionRefusal('Aggregate artifact capacity exhausted')
    if type(value.kind) is not str or value.kind not in ('mutation', 'import', 'catalog-transform',
            'catalog-acceptance', 'home-migration', 'administrative-repair'):
        raise AdmissionRefusal('Closed native operation kind required')
    arguments = [('text', _text(value.kind, 4096))]
    arguments.extend(('binary', item) for item in artifacts)
    if value.family != 'base':
        arguments.extend((('binary', _binary(value.asserted, 131072)),
                          ('binary', _binary(value.capture_profile, 65536))))
    elif value.asserted is not None or value.capture_profile is not None:
        raise AdmissionRefusal('Unexpected asserted context')
    if sum(len(data) for kind, data in arguments if kind == 'binary') > 4_194_304:
        raise AdmissionRefusal('Aggregate original admission capacity exhausted')
    if value.family in ('epoch', 'configuration'):
        arguments.extend(('text', _text(item, maximum)) for item, maximum in
                         ((value.installation, 1024), (value.source_epoch, 256),
                          (value.incarnation, 1024)))
    elif any(item is not None for item in (value.installation, value.source_epoch, value.incarnation)):
        raise AdmissionRefusal('Unexpected epoch context')
    if value.family == 'configuration':
        arguments.append(('binary', _binary(value.configuration_profile, 65536)))
    elif value.configuration_profile is not None:
        raise AdmissionRefusal('Unexpected configuration context')
    prefix = ('SELECT writer_xid, ordinal, context_hex FROM truss.'
              + _FUNCTIONS[value.family] + '(')
    ordinal_sql = ordinal + '::pg_catalog.int8'
    def size(kind, data):
        # ASCII grammar and hexadecimal output: exact preflight before hex allocation.
        binary_size = len("pg_catalog.decode('', 'hex')") + 2 * len(data)
        return binary_size if kind == 'binary' else len("pg_catalog.convert_from(, 'UTF8')") + binary_size
    encoded_size = len(prefix) + len(ordinal_sql) + sum(size(k, b) + 2 for k, b in arguments) + 1
    if encoded_size > maximum_sql_bytes:
        raise AdmissionRefusal('Encoded SQL capacity exhausted')
    def encode(kind, data):
        binary = "pg_catalog.decode('" + data.hex() + "', 'hex')"
        return binary if kind == 'binary' else "pg_catalog.convert_from(" + binary + ", 'UTF8')"
    sql = prefix + ', '.join([ordinal_sql, *(encode(k, b) for k, b in arguments)]) + ')'
    if len(sql) != encoded_size:
        raise AssertionError('Fixed encoding size correspondence failed')
    return EncodedAdmissionRequest(value, ordinal, sql, encoded_size)
