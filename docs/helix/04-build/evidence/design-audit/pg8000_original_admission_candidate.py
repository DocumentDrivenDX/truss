"""Original one-use/native admission composition candidate; not a public engine.

Only selected original four-family procedures are invoked. Artifact meaning,
current security authority, complete account/native work and installation remain
unqualified; synthetic fixture bytes cannot establish those responsibilities.
"""
from dataclasses import dataclass
from pg8000.exceptions import DatabaseError
from truss._operation_admission import AdmissionCustody, AdmissionRefusal
from pg8000_original_control_candidate import OriginalControlProducer, _frame

FUNCTIONS = {
    'base': 'runtime_admit_operation',
    'asserted': 'runtime_admit_operation_with_asserted_origin',
    'epoch': 'runtime_admit_operation_with_epoch_context',
    'configuration': 'runtime_admit_operation_with_configuration_context',
}


@dataclass(frozen=True, slots=True, eq=False)
class NativeAdmissionInput:
    family: str
    kind: str
    artifacts: tuple
    asserted: bytes | None = None
    capture_profile: bytes | None = None
    installation: str | None = None
    source_epoch: str | None = None
    incarnation: str | None = None
    configuration_profile: bytes | None = None


@dataclass(frozen=True, slots=True)
class NativeAdmissionObservation:
    writer_xid: str
    ordinal: str
    original_context_hex: str


@dataclass(frozen=True, slots=True)
class ContainedNativeRejection:
    original_error: DatabaseError
    # Protocol/local containment observation only, not a business code, current
    # authority, whole-transaction retry permit or complete healthy-scope claim.


def _shape(value):
    if type(value) is not NativeAdmissionInput or type(value.family) is not str or value.family not in FUNCTIONS:
        raise AdmissionRefusal('Original registered admission family required')
    if type(value.kind) is not str or not 1 <= len(value.kind) <= 4096:
        raise AdmissionRefusal('Bounded exact kind text required')
    if type(value.artifacts) is not tuple or len(value.artifacts) != 6:
        raise AdmissionRefusal('Complete six original artifacts required')
    binary = list(value.artifacts)
    text = [value.kind]
    if value.family != 'base':
        binary.extend((value.asserted, value.capture_profile))
    elif value.asserted is not None or value.capture_profile is not None:
        raise AdmissionRefusal('Unexpected asserted context')
    if value.family in ('epoch', 'configuration'):
        text.extend((value.installation, value.source_epoch, value.incarnation))
    elif any(v is not None for v in (value.installation, value.source_epoch, value.incarnation)):
        raise AdmissionRefusal('Unexpected epoch context')
    if value.family == 'configuration':
        binary.append(value.configuration_profile)
    elif value.configuration_profile is not None:
        raise AdmissionRefusal('Unexpected configuration context')
    if any(type(v) is not bytes or not 1 <= len(v) <= 1048576 for v in binary):
        raise AdmissionRefusal('Bounded original immutable artifact bytes required')
    if any(type(v) is not str or not 1 <= len(v) <= 4096 or '\0' in v for v in text):
        raise AdmissionRefusal('Bounded exact original context text required')
    if any(any(0xD800 <= ord(c) <= 0xDFFF for c in v) for v in text):
        raise AdmissionRefusal('Lossless Unicode text required')
    # Reserve encoding/hex/SQL payload before materializing them. These charges
    # are conservative payload custody, not a complete object/native-work meter.
    return tuple(binary), tuple(text), 1024 + 4 * sum(len(v) for v in binary) + 16 * sum(len(v) for v in text)


class OriginalAdmissionProducer:
    def __init__(self, controls, maximum_confirmations=64):
        if type(controls) is not OriginalControlProducer or type(maximum_confirmations) is not int or not 1 <= maximum_confirmations <= 8192:
            raise AdmissionRefusal('Original control producer and finite capacity required')
        self.controls = controls
        self.connection = controls._connection
        self._original_input = None
        self._registered = {}
        if not controls._lock.acquire(blocking=False):
            raise AdmissionRefusal('Original control invocation active')
        try:
            if controls._closed or self.connection._control_closed:
                raise AdmissionRefusal('Original open control lifetime required')
            binding = getattr(self.connection, '_admission_binding', None)
            if binding is None:
                custody = AdmissionCustody(controls._producer, maximum_confirmations, self._verify, self._admit)
                binding = (maximum_confirmations, self, custody)
                self.connection._admission_binding = binding
            elif binding[0] != maximum_confirmations:
                raise AdmissionRefusal('Original admission capacity profile changed')
            self._owner, self._custody = binding[1], binding[2]
        finally:
            controls._lock.release()

    def _verify(self, original, original_input):
        controls = self.controls
        entry = controls._tickets.get(id(original))
        if (controls._closed or self.connection._control_closed or entry is None
                or entry[0] is not original or entry[1]
                or controls._attempts[entry[3]][3] != 'confirmed'):
            raise AdmissionRefusal('Original live confirmed savepoint required')
        # It must remain the original top registered boundary; a later live
        # boundary cannot silently acquire an earlier operation's effects.
        if any(not e[1] and int(e[3]) > int(entry[3]) for e in controls._tickets.values()):
            raise AdmissionRefusal('Original savepoint is no longer the active boundary')
        if (self.connection._boundary_generation != controls._boundary_generation
                or self.connection._ready_status != b'T'
                or controls._observe_xid() != controls._xid):
            raise AdmissionRefusal('Original native transaction unavailable or changed')
        if original_input is not self._original_input:
            raise AdmissionRefusal('Original captured input custody required')

    def _admit(self, original, original_input):
        controls = self.controls
        entry = controls._tickets[id(original)]
        ordinal = entry[3]
        binary, text, allowance = _shape(original_input)
        account, producer = controls._account, controls._producer
        permit = account.reserve(producer, allowance)
        account.allocate(producer, permit, allowance)
        account.terminate(producer, permit)
        def bytea(value):
            return "pg_catalog.decode('" + value.hex() + "','hex')"
        def native_text(value):
            return 'pg_catalog.convert_from(' + bytea(value.encode('utf-8', errors='strict')) + ",'UTF8')"
        arguments = [ordinal, native_text(text[0])] + [bytea(v) for v in original_input.artifacts]
        if original_input.family != 'base':
            arguments.extend((bytea(original_input.asserted), bytea(original_input.capture_profile)))
        if original_input.family in ('epoch', 'configuration'):
            arguments.extend(native_text(v) for v in text[1:])
        if original_input.family == 'configuration':
            arguments.append(bytea(original_input.configuration_profile))
        sql = 'SELECT writer_xid, ordinal, context_hex FROM truss.' + FUNCTIONS[original_input.family] + '(' + ','.join(arguments) + ')'
        start = len(self.connection.original_controls)
        try:
            result = controls._submit(sql)
        except DatabaseError as error:
            abort = self.connection._abort_custody
            if type(error) is not DatabaseError or abort is None or abort[1] is not error:
                raise
            controls._rollback_savepoint_locked(original)
            return ContainedNativeRejection(error)
        if (self.connection.original_controls[start:] != [_frame(b'C', b'SELECT 1\0'), _frame(b'Z', b'T')]
                or tuple(c.name for c in result.columns) != (b'writer_xid', b'ordinal', b'context_hex')
                or any(c.type_oid != 25 or c.format != 0 for c in result.columns)
                or result.row_count != 1 or len(result.rows) != 1 or len(result.rows[0]) != 3):
            raise AdmissionRefusal('Complete original native admission result required')
        writer_xid, actual_ordinal, context_hex = result.rows[0]
        if (writer_xid != controls._xid.encode('ascii') or actual_ordinal != ordinal.encode('ascii')
                or type(context_hex) is not bytes or not context_hex or len(context_hex) % 2
                or any(c not in b'0123456789abcdef' for c in context_hex)):
            raise AdmissionRefusal('Original issuer/context correspondence required')
        if controls._observe_xid() != controls._xid:
            raise AdmissionRefusal('Original native transaction changed after admission')
        return NativeAdmissionObservation(controls._xid, ordinal, context_hex.decode('ascii'))

    def register(self, original):
        controls = self.controls
        if not controls._lock.acquire(blocking=False):
            raise AdmissionRefusal('Original control invocation active')
        try:
            entry = controls._tickets.get(id(original))
            if (controls._closed or self.connection._control_closed or entry is None
                    or entry[0] is not original or entry[1]):
                raise AdmissionRefusal('Original confirmed producer object required')
            ticket = self._custody.register_confirmed(controls._producer, original)
            self._owner._registered[id(ticket)] = ticket
            return ticket
        finally:
            controls._lock.release()

    def submit(self, ticket, original_input):
        _shape(original_input)
        controls = self.controls
        if not controls._lock.acquire(blocking=False):
            raise AdmissionRefusal('Original control invocation active')
        try:
            if controls._closed or self.connection._control_closed or self._owner._registered.get(id(ticket)) is not ticket:
                raise AdmissionRefusal('Original open admission custody required')
            self._owner._original_input = original_input
            return self._custody.admit_once(ticket, original_input)
        except BaseException:
            # Reusing a consumed ticket is a pre-submission refusal, not proof of
            # native uncertainty. Escaped new dispatch failures close the shared
            # admission registry itself; original containment stays with controls.
            raise
        finally:
            self._owner._original_input = None
            controls._lock.release()
