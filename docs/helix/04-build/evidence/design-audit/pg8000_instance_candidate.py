"""Private driver seam; no complete account, authority or settlement issuer."""
from pg8000.core import CoreConnection
from python_pg_receive_candidate import Receiver
from python_pg_frame_candidate import row_description, data_row

class FrameFile:
    def __init__(self, transport):
        self.transport = transport
        self.receiver = Receiver(transport, frame_bytes=1048576, total_bytes=16777216,
                                 messages=100, reads=10000)
        self.pending = None
        self.header = None
        self.closed = False
        self.remaining_writes = 100
        self.remaining_send_bytes = 2097152
        self.message_sizes = []

    def read(self, size):
        if self.closed:
            raise ValueError('Closed experiment file')
        try:
            if self.pending is None:
                if type(size) is not int or size != 5:
                    raise ValueError('Original five-byte header request required')
                self.pending = self.receiver.receive()
                self.header = self.pending[:5]
                self.message_sizes.append([self.header[:1].decode('ascii'), len(self.pending)])
                return self.header
            if type(size) is not int or size != len(self.pending) - 5:
                raise ValueError('Original complete body request required')
            result = self.pending[5:]
            self.pending = None
            return result
        except BaseException:
            self.closed = True
            self.pending = None
            raise

    def write(self, source):
        if self.closed or type(source) not in (bytes, bytearray) or self.remaining_writes == 0 or len(source) > self.remaining_send_bytes:
            self.closed = True
            self.pending = None
            raise ValueError('Experiment send capacity')
        self.remaining_writes -= 1
        self.remaining_send_bytes -= len(source)
        try:
            self.transport.sendall(source)
        except BaseException:
            self.closed = True
            raise
        return len(source)

    def flush(self):
        pass  # write uses sendall; no additional buffered file exists.

    def close(self):
        self.closed = True
        self.pending = None


class SuppliedSocket:
    def __init__(self, transport):
        self.transport = transport
        self.file = FrameFile(transport)
        self.opened = False

    def makefile(self, mode):
        if mode != 'rwb' or self.opened:
            raise ValueError('Single original experiment file required')
        self.opened = True
        return self.file

    def close(self):
        self.transport.close()


class RawConnection(CoreConnection):
    def __init__(self, *args, **kwargs):
        self.experiment_commands = []
        super().__init__(*args, **kwargs)

    def handle_COMMAND_COMPLETE(self, data, context):
        self.experiment_commands.append(data)
        super().handle_COMMAND_COMPLETE(data, context)

    def handle_AUTHENTICATION_REQUEST(self, data, context):
        if data != b'\0\0\0\0':
            raise ValueError('Only local AuthenticationOk admitted')
        super().handle_AUTHENTICATION_REQUEST(data, context)

    def original_frame(self, kind, data):
        header = self._sock.header
        if header is None or header[:1] != kind or self._sock.pending is not None:
            raise ValueError('Original completed frame correspondence required')
        return header + data

    def handle_ROW_DESCRIPTION(self, data, context):
        context.columns = row_description(self.original_frame(b'T', data))
        if any(column.format != 0 for column in context.columns):
            raise ValueError('Only text experiment fields admitted')
        context.input_funcs = []
        if context.rows is None:
            context.rows = []

    def handle_DATA_ROW(self, data, context):
        if context.columns is None:
            raise ValueError('Original description required')
        context.rows.append(data_row(self.original_frame(b'D', data), len(context.columns)))
