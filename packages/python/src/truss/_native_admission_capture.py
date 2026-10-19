# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private bounded admission result capture; never artifact authority or readiness."""
from dataclasses import dataclass
import struct
import re
from ._native_result_custody import NativeResultCustody, NativeTextLimits
from ._native_pg8000 import NativeBoundaryRefusal, NativeCall

_NAMES = (b'writer_xid', b'ordinal', b'context_hex', b'actual_writer_xid')

@dataclass(frozen=True, slots=True)
class NativeAdmissionObservation:
    original_call: NativeCall
    writer_xid: str
    ordinal: str
    original_context: bytes
    scope: str = 'native_response_only'

class NativeAdmissionCapture(NativeResultCustody):
    NAMES = _NAMES
    def __init__(self, session, limits, *, maximum_context_bytes=4096, entry=None):
        if (type(limits) is not NativeTextLimits or limits.columns != len(self.NAMES) or limits.rows != 1
                or type(maximum_context_bytes) is not int
                or not 1 <= maximum_context_bytes <= 1048576
                or 2*maximum_context_bytes > limits.cell_bytes):
            raise NativeBoundaryRefusal('Exact bounded admission result profile required')
        self.entry = entry
        self.admission_context = None
        self.response_stage = 0
        self.maximum_context_bytes = maximum_context_bytes
        super().__init__(session, limits)
        self.expected_command = 'SELECT'

    def retain_context_before_send(self, context, entry):
        with self.boundary._lock:
            if (getattr(context, 'stream', None) is not None
                    or not self.boundary._calling or self.entry is not entry
                    or entry.native_call is not None or self.admission_context is not None
                    or not self.session.calls or self.session.calls[-1] is not entry
                    or self.context_count >= len(self.contexts)):
                raise NativeBoundaryRefusal('Original pre-send admission Context required')
            self.admission_context = context
            self.contexts[self.context_count] = context
            self.context_count += 1

    def _messages(self, context):
        if not self._cleanup_mode() and self.boundary._active_control is None:
            entry = self.session.calls[-1] if self.session.calls else None
            if entry is None or (self.entry is not None and self.entry is not entry):
                raise NativeBoundaryRefusal('Original admission entry required before response')
            if self.admission_context is not None and self.admission_context is not context:
                raise NativeBoundaryRefusal('One original admission Context required')
            self.entry = entry
            self.admission_context = context
        if (not self._cleanup_mode() and self.boundary._active_control is None
                and any(item is context for item in self.contexts[:self.context_count])):
            if getattr(context, 'stream', None) is not None:
                raise NativeBoundaryRefusal('External admission stream unavailable')
            return self.original_handle_messages(context)
        return super()._messages(context)

    def _validate(self, code, data, context):
        super()._validate(code, data, context)
        if self._cleanup_mode() or self.boundary._active_control is not None:
            return
        if context is not self.admission_context:
            raise NativeBoundaryRefusal('Original admission Context correspondence required')
        if code in (b'N', b'S', b'A'):
            if self.response_stage in (4, 6):
                raise NativeBoundaryRefusal('Admission response already terminal')
            return
        expected = {b'T':0, b'D':1, b'C':2, b'Z':3}
        if code == b'E':
            if self.response_stage not in (0, 1, 2):
                raise NativeBoundaryRefusal('Unexpected admission error position')
            self.response_stage = 5
            return
        if code == b'Z' and self.response_stage == 5:
            if data != b'E':
                raise NativeBoundaryRefusal('Original failed transaction Ready required')
            self.response_stage = 6
            return
        if code not in expected or self.response_stage != expected[code]:
            raise NativeBoundaryRefusal('Exact admission response order required')
        if code == b'Z' and data != b'T':
            raise NativeBoundaryRefusal('Original active transaction Ready required')
        self.response_stage += 1
        if code == b'T':
            if struct.unpack_from('!H', data)[0] != len(self.NAMES):
                raise NativeBoundaryRefusal('Complete selected admission description required')
            offset = 2
            for name in self.NAMES:
                end = data.find(b'\0', offset)
                if data[offset:end] != name:
                    raise NativeBoundaryRefusal('Original ordered admission columns required')
                offset = end + 19
        elif code == b'C' and data != b'SELECT 1\0':
            raise NativeBoundaryRefusal('Exactly one admitted response row required')

    def observe(self, rows, call, issued_ordinal):
        # The enclosing original dispatcher must additionally bind this call to
        # its retained request/entry; this capture does not register any authority.
        if (type(call) is not NativeCall or call is not self.boundary.last_call
                or not call.capture_complete or call.driver_raised
                or call.final_status != b'T' or self.failed or self.response_stage != 4
                or self.entry is None or self.entry.native_call is not call
                or self.entry.revision != call.revision
                or not any(item is self.entry for item in self.session.calls)
                or self.admission_context is None or rows is not self.admission_context.rows
                or call.original_control is not self.entry.lifecycle
                or call.original_resource is not self.entry.resource
                or call.original_cleanup is not self.entry.cleanup
                or not any(event.code == b'C' and event.payload == b'SELECT 1\0' for event in call.events)
                or type(issued_ordinal) is not str
                or re.fullmatch(r'0|[1-9][0-9]{0,18}', issued_ordinal) is None
                or int(issued_ordinal) > 9223372036854775807):
            raise NativeBoundaryRefusal('Complete original admission response required')
        frozen = self.transfer(rows)
        if len(frozen) != 1 or len(frozen[0]) != len(self.NAMES):
            raise NativeBoundaryRefusal('Complete original admission row required')
        writer, ordinal, context_hex = frozen[0][:3]
        actual_writer = frozen[0][-1]
        if (type(writer) is not str or re.fullmatch(r'[1-9][0-9]{0,19}', writer) is None
                or int(writer) > 18446744073709551615 or writer != actual_writer
                or ordinal != issued_ordinal or type(context_hex) is not str
                or not 2 <= len(context_hex) <= 2*self.maximum_context_bytes
                or len(context_hex) % 2 or re.fullmatch(r'[0-9a-f]+', context_hex) is None):
            raise NativeBoundaryRefusal('Exact original issuer/context response required')
        return self._produce_observation(call, writer, ordinal, bytes.fromhex(context_hex), frozen[0])

    def _produce_observation(self, call, writer, ordinal, context, row):
        return NativeAdmissionObservation(call, writer, ordinal, context)
