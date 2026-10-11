"""Private selected pg8000 frame/context/result custody, not a heap bound.

Gate/core/decode payload charges never rewind. Connection-owned buffering,
notices and notifications are preserved; no empty-socket claim is produced.
"""
from dataclasses import dataclass
import struct
from ._accounted_receive import AccountedReceiver
from ._resource_account import BytePermitAccount
from ._native_pg8000 import NativeBoundaryRefusal

@dataclass(frozen=True)
class NativeTextLimits:
    frame_bytes: int = 65536
    wire_bytes: int = 1048576
    messages: int = 2048
    reads: int = 4096
    payload_capacity: int = 8388608
    cumulative_payload: int = 33554432
    account_records: int = 32768
    contexts: int = 64
    rows: int = 256
    columns: int = 32
    cell_bytes: int = 8192
    result_bytes: int = 65536
    sql_bytes: int = 16384
    parameters: int = 128
    parameter_bytes: int = 65536
    def __post_init__(self):
        if any(type(x) is not int or x < 1 for x in self.__dict__.values()):
            raise ValueError('Positive exact text-operation limits required')

@dataclass(eq=False)
class NativeResultOwner:
    rows: object = None
    transferred: bool = False

class _BufferedIngress:
    def __init__(self, original): self.original = original
    def recv_into(self, view): return self.original.readinto(view)

class NativeResultCustody:
    def __init__(self, session, limits):
        if type(limits) is not NativeTextLimits:
            raise ValueError('Original text limits required')
        self.session, self.boundary, self.limits = session, session.boundary, limits
        con = self.boundary._connection
        self.original_sock = con._sock
        self.original_context = con._context
        self.original_handle_messages = con.handle_messages
        self.original_handlers = dict(con.message_types)
        self.original_ready_error = self.boundary._ready_error
        self.account = BytePermitAccount(self, limits.payload_capacity,
            limits.cumulative_payload, limits.account_records)
        self.receiver = AccountedReceiver(_BufferedIngress(self.original_sock), self.account, self,
            frame_bytes=limits.frame_bytes, total_bytes=limits.wire_bytes,
            messages=limits.messages, reads=limits.reads)
        # Independent preallocated ingress/account/context lanes. Ordinary work
        # cannot consume the budget reserved for original native cleanup.
        self.cleanup_account = BytePermitAccount(self, limits.payload_capacity,
            limits.cumulative_payload, limits.account_records)
        self.cleanup_receiver = AccountedReceiver(_BufferedIngress(self.original_sock), self.cleanup_account, self,
            frame_bytes=limits.frame_bytes, total_bytes=limits.wire_bytes,
            messages=limits.messages, reads=limits.reads)
        self.contexts = [None] * limits.contexts
        self.cleanup_contexts = [None] * 64
        self.cleanup_context_count = 0
        self.cleanup_rows_seen = 0
        self.cleanup_bytes_seen = 0
        self.context_count = 0
        self.pending_body = None
        self.failed = False
        self.installed = False
        self.detached = False
        self.rows_seen = 0
        self.bytes_seen = 0
        self.expected_command = None
        self.result_owner = NativeResultOwner()
        self._original_messages_entry = self._messages
        self.errors = []
        self._handlers = {code:self._handler(code, original)
                          for code, original in self.original_handlers.items()}

    def install(self):
        with self.boundary._lock:
            con = self.boundary._connection
            if self.session.result_custody is not None and self.session.result_custody is not self:
                raise NativeBoundaryRefusal('Original result custody already registered')
            if self.installed:
                if con._sock is self and con.handle_messages is self._original_messages_entry:
                    return
                raise NativeBoundaryRefusal('Original installed custody changed')
            if (self.boundary._calling or con._sock is not self.original_sock
                    or self.boundary._operation_ledger is not self.session):
                raise NativeBoundaryRefusal('Original frame custody changed')
            self.session.result_custody = self
            try:
                con._sock = self
                con.handle_messages = self._original_messages_entry
                con.message_types.update(self._handlers)
                self.installed = True
            except BaseException:
                self.failed = True
                self.boundary._quarantined = True
                raise

    def _cleanup_mode(self):
        calls = self.session.cleanup_calls
        return bool(calls and calls[-1].native_call is None)

    def read(self, size):
        try:
            if self.failed:
                raise NativeBoundaryRefusal('Failed frame gate retained')
            if self.pending_body is None:
                if size != 5:
                    raise NativeBoundaryRefusal('Original header read required')
                cleanup = self._cleanup_mode()
                account = self.cleanup_account if cleanup else self.account
                receiver = self.cleanup_receiver if cleanup else self.receiver
                permit = account.reserve(self, 16 * self.limits.frame_bytes)
                header, body = receiver.receive_core_parts()
                account.allocate(self, permit, 16 * len(body))
                account.terminate(self, permit)
                self.pending_body = body
                return header
            body = self.pending_body
            if type(size) is not int or size != len(body):
                raise NativeBoundaryRefusal('Exact original body read required')
            self.pending_body = None
            return body
        except BaseException:
            self.failed = True
            self.boundary._quarantined = True
            raise

    def write(self, data): return self.original_sock.write(data)
    def flush(self): return self.original_sock.flush()
    def close(self): return self.original_sock.close()

    def _messages(self, context):
        cleanup = self._cleanup_mode()
        slots = self.cleanup_contexts if cleanup else self.contexts
        count = self.cleanup_context_count if cleanup else self.context_count
        if count >= len(slots):
            self.failed = True
            self.boundary._quarantined = True
            raise NativeBoundaryRefusal('Original context custody exhausted')
        slots[count] = context
        if cleanup: self.cleanup_context_count += 1
        else: self.context_count += 1
        if context.stream is not None:
            self.failed = True
            self.boundary._quarantined = True
            raise NativeBoundaryRefusal('External stream is outside selected profile')
        return self.original_handle_messages(context)

    def _handler(self, code, original):
        def handle(data, context):
            try:
                self._validate(code, data, context)
                return original(data, context)
            except BaseException:
                self.failed = True
                self.boundary._quarantined = True
                raise
        return handle

    def _validate(self, code, data, context):
        from pg8000.converters import string_in
        if self.boundary._connection._client_encoding != 'utf8':
            raise NativeBoundaryRefusal('Original UTF8 decoding changed')
        if code in (b'G', b'H', b'W', b'd', b'c', b's'):
            raise NativeBoundaryRefusal('COPY/stream/suspended portal unsupported')
        if code == b'T':
            if len(data) < 2: raise NativeBoundaryRefusal('Incomplete row description')
            count = struct.unpack_from('!H', data)[0]
            if count > self.limits.columns: raise NativeBoundaryRefusal('Column bound exceeded')
            offset = 2
            for _ in range(count):
                end = data.find(b'\0', offset)
                if end < offset or end - offset > self.limits.cell_bytes or end + 19 > len(data):
                    raise NativeBoundaryRefusal('Invalid bounded column metadata')
                data[offset:end].decode('utf-8', 'strict')
                fields = struct.unpack_from('!IhIhih', data, end + 1)
                if fields[2] != 25 or fields[5] != 0:
                    raise NativeBoundaryRefusal('Exact text-format text columns required')
                offset = end + 19
            if offset != len(data): raise NativeBoundaryRefusal('Trailing column metadata')
        elif code == b'D':
            if len(data) < 2: raise NativeBoundaryRefusal('Incomplete data row')
            count = struct.unpack_from('!H', data)[0]
            if (count > self.limits.columns or count != len(context.input_funcs)
                    or any(f is not string_in for f in context.input_funcs)):
                raise NativeBoundaryRefusal('Original text decoder correspondence required')
            cleanup = self._cleanup_mode()
            if (self.cleanup_rows_seen if cleanup else self.rows_seen) >= (64 if cleanup else self.limits.rows):
                raise NativeBoundaryRefusal('Row bound exceeded')
            offset = 2
            for _ in range(count):
                if offset + 4 > len(data): raise NativeBoundaryRefusal('Incomplete cell length')
                size = struct.unpack_from('!i', data, offset)[0]
                offset += 4
                if size == -1: continue
                if size < 0 or size > self.limits.cell_bytes or offset + size > len(data):
                    raise NativeBoundaryRefusal('Invalid bounded cell')
                if cleanup: self.cleanup_bytes_seen += size
                else: self.bytes_seen += size
                if (self.cleanup_bytes_seen if cleanup else self.bytes_seen) > (65536 if cleanup else self.limits.result_bytes):
                    raise NativeBoundaryRefusal('Result payload bound exceeded')
                data[offset:offset+size].decode('utf-8', 'strict')
                offset += size
            if offset != len(data): raise NativeBoundaryRefusal('Trailing data row bytes')
            if cleanup: self.cleanup_rows_seen += 1
            else: self.rows_seen += 1
        elif code == b'Z':
            if data not in (b'I', b'T', b'E'): raise NativeBoundaryRefusal('Invalid native Ready')
        elif code in (b'1', b'2', b'3', b'n'):
            if data != b'': raise NativeBoundaryRefusal('Invalid native acknowledgement')
        elif code == b'C':
            import re
            if not data.endswith(b'\0'): raise NativeBoundaryRefusal('Invalid command completion')
            tag = data[:-1]
            if len(tag) > 128 or any(x > 127 for x in tag):
                raise NativeBoundaryRefusal('Bounded ASCII command tag required')
            for item in tag.split(b' ')[1:]:
                if item.isdigit() and (len(item) > 20 or (len(item) == 20 and item > b'18446744073709551615')):
                    raise NativeBoundaryRefusal('Canonical uint64 command count required')
            control = self.boundary._active_control
            if control is not None:
                valid = tag in self._control_tags(control)
            else:
                pattern = self._command_pattern(self.expected_command)
                valid = pattern is not None and re.fullmatch(pattern, tag) is not None
            if not valid: raise NativeBoundaryRefusal('Unregistered original command completion')
        elif code == b'E':
            # Bounded raw original ErrorResponse stays in NativeCall evidence.
            if not data.endswith(b'\0\0'): raise NativeBoundaryRefusal('Invalid native error frame')
        elif code == b't':
            if len(data) < 2: raise NativeBoundaryRefusal('Invalid parameter description')
            count = struct.unpack_from('!H', data)[0]
            if count > self.limits.parameters or len(data) != 2 + 4*count:
                raise NativeBoundaryRefusal('Invalid bounded parameter description')
        elif code == b'S':
            parts = data.split(b'\0')
            if len(parts) != 3 or parts[-1] != b'':
                raise NativeBoundaryRefusal('Invalid native parameter status')
            if parts[0] == b'client_encoding' and parts[1] != b'UTF8':
                raise NativeBoundaryRefusal('Original UTF8 profile cannot change')
        elif code not in (b'N', b'A'):
            raise NativeBoundaryRefusal('Unsupported original native response')

    def _control_tags(self, control):
        expected = {'savepoint':b'SAVEPOINT', 'rollback_to':b'ROLLBACK', 'release':b'RELEASE'}
        tag = expected.get(control.kind)
        return () if tag is None else (tag,)

    def _command_pattern(self, command):
        return {'SELECT':rb'SELECT (0|[1-9][0-9]*)',
            'INSERT':rb'INSERT 0 (0|[1-9][0-9]*)',
            'UPDATE':rb'UPDATE (0|[1-9][0-9]*)',
            'DELETE':rb'DELETE (0|[1-9][0-9]*)'}.get(command)

    def normal_native_error(self, call):
        return (self.installed and not self.failed and self.session.result_custody is self
                and call.capture_complete and call.driver_raised and call.final_status == b'E'
                and any(e.code == b'E' for e in call.events))

    def transfer(self, rows):
        if type(rows) is not list or not any(c is not None and c.rows is rows for c in self.contexts):
            raise NativeBoundaryRefusal('Original operation result custody required')
        frozen = tuple(tuple(row) for row in rows)
        if any(type(row) is not list or any(v is not None and type(v) is not str for v in row) for row in rows):
            raise NativeBoundaryRefusal('Exact text/NULL result required')
        self.result_owner.rows = frozen
        self.result_owner.transferred = True
        return frozen

    def inventory(self):
        created = []
        entries = (*self.session.calls, *self.session.cleanup_calls)
        for entry in entries:
            if entry.resource is not None and entry.resource[0] == 'prepare':
                resource = entry.resource[1]
                wrapper = next((p for p in self.boundary._resources if p._resource is resource), None)
                if wrapper is None or any(p is wrapper for p in created):
                    raise NativeBoundaryRefusal('Original prepared inventory unavailable')
                created.append(wrapper)
        for entry in entries:
            if entry.resource is not None and entry.resource[0] in ('execute', 'close', 'portal_close'):
                if not any(p._resource is entry.resource[1] for p in created):
                    raise NativeBoundaryRefusal('Unowned operation resource')
        return tuple(created)

    def detach(self):
        # Called after original native restoration, with ordinary admission shut.
        with self.boundary._lock:
            con = self.boundary._connection
            if (self.failed or self.pending_body is not None or self.boundary._calling
                    or self.boundary._quarantined or con._sock is not self
                    or not self.session.admission_closed
                    or self.session.result_custody is not self
                    or self.boundary._operation is not self.session.token
                    or self.boundary._operation_ledger is not self.session
                    or con.handle_messages is not self._original_messages_entry
                    or any(con.message_types.get(k) is not v for k,v in self._handlers.items())):
                raise NativeBoundaryRefusal('Original result ingress is unsettled')
            for entry in (*self.session.calls, *self.session.cleanup_calls):
                if entry.resource is not None and entry.resource[0] == 'probe':
                    for kind in ('probe_portal_close', 'probe_statement_close'):
                        if not any(e.resource is not None and e.resource[0] == kind
                                and e.resource[1] is entry.resource[1] and e.native_call is not None
                                and e.native_call.capture_complete and not e.native_call.driver_raised
                                and sum(x.code == b'3' and x.payload == b'' for x in e.native_call.events) == 1
                                for e in self.session.cleanup_calls):
                            raise NativeBoundaryRefusal('Original probe closure unconfirmed')
            prepared = self.inventory()
            for p in prepared:
                r = p._resource
                if (not r.native_closed or r.phase != 'closed' or r.close_call is None
                        or not r.close_call.capture_complete):
                    raise NativeBoundaryRefusal('Original named resource closure unconfirmed')
                executed = any(e.resource is not None and e.resource[0] == 'execute'
                               and e.resource[1] is r for e in self.session.calls)
                if executed and not any(e.native_call is not None and e.resource is not None
                        and e.resource[0] == 'portal_close' and e.resource[1] is r
                        and e.native_call.capture_complete and not e.native_call.driver_raised
                        and sum(x.code == b'3' and x.payload == b'' for x in e.native_call.events) == 1
                        for e in self.session.cleanup_calls):
                    raise NativeBoundaryRefusal('Original execution portal closure unconfirmed')
            for context in (*self.contexts[:self.context_count], *self.cleanup_contexts[:self.cleanup_context_count]):
                error = context.error
                if error is not None:
                    error.__traceback__ = None
                    error.__cause__ = None
                    error.__context__ = None
                context.rows = None
                context.columns = None
                context.input_funcs = None
                context.stream = None
                context.error = None
                context.statement = None
            for p in prepared:
                if p._original is None: continue
                p._original._context = None
                p._original.cols = None
                p._original.input_funcs = None
                p._original.make_vals = None
                p._original.statement = None
            self.boundary._ready_error = self.original_ready_error
            con._context = self.original_context
            con.handle_messages = self.original_handle_messages
            con.message_types.update(self.original_handlers)
            con._sock = self.original_sock
            # These were restoration custody, not operation result ownership.
            # Retained completed gates must not pin historical host rows/errors.
            self.original_context = None
            self.original_ready_error = None
            self.detached = True
            # Charges stay retained: native evidence and the transferred result
            # have consumers. Permit termination is not allocation release.
            self.account.close(self)
            self.cleanup_account.close(self)
