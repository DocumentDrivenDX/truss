"""Private local-trust driver seam experiment; no original port/account authority."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket
import sys
from pg8000.core import CoreConnection
import pg8000.core
from python_pg_receive_candidate import Receiver
from python_pg_frame_candidate import row_description, data_row

if len(sys.argv) != 1:
    raise SystemExit('No arguments admitted')
HERE = Path(__file__).resolve().parent
CORE_SHA = 'cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
if importlib.metadata.version('pg8000') != '1.31.5' or hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest() != CORE_SHA:
    raise SystemExit('Original driver source required before connection')


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


query = "BEGIN READ ONLY; SELECT NULL::text AS n, ''::text AS empty, 9007199254740993.0000000000000000001::numeric AS exact, 'é𐀀'::text AS unicode, current_setting('server_version_num') AS server; ROLLBACK;"
expected = [(None, b'', b'9007199254740993.0000000000000000001', 'é𐀀'.encode(), b'170009')]
with socket.create_connection(('127.0.0.1', 15434), timeout=10) as transport:
    supplied = SuppliedSocket(transport)
    connection = RawConnection(user='postgres', database='postgres', sock=supplied,
                               ssl_context=False, startup_params={'client_encoding':'UTF8'})
    try:
        context = connection.execute_simple(query)
        if context.rows != expected or [(c.name,c.type_oid,c.format) for c in context.columns] != [(b'n',25,0),(b'empty',25,0),(b'exact',1700,0),(b'unicode',25,0),(b'server',25,0)]:
            raise ValueError('Independent original metadata/cell mismatch')
        if connection.experiment_commands != [b'BEGIN\0', b'SELECT 1\0', b'ROLLBACK\0']:
            raise ValueError('Independent command inventory mismatch')
        if connection._transaction_status != b'I':
            raise ValueError('Original probe cycle did not return idle')
        remaining = {'bytes':supplied.file.receiver.remaining_bytes,
                     'messages':supplied.file.receiver.remaining_messages,
                     'readCalls':supplied.file.receiver.remaining_reads}
    finally:
        connection.close()
receipt = {'status':'passed_local_read_only_pg8000_instance_hooks','python':sys.version,
           'orderedCommandTags':[value.decode('ascii') for value in connection.experiment_commands],
           'dependencies':{name:importlib.metadata.version(name) for name in ['pg8000','scramp','asn1crypto','python-dateutil','six']},
           'driverCoreSha256':CORE_SHA,'querySha256':hashlib.sha256(query.encode()).hexdigest(),
           'rawCellsHex':[[None if cell is None else cell.hex() for cell in row] for row in context.rows],
           'orderedTypeOids':[c.type_oid for c in context.columns],
           'messageKindsAndSizes':supplied.file.message_sizes,'remainingRawBounds':remaining,
           'sourceSha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in [Path(__file__).name,'python_pg_receive_candidate.py','python_pg_frame_candidate.py']},
           'driverPortQualified':False,
           'scope':'Supplied local trust socket and instance-bound raw handlers only. BEGIN READ ONLY/ROLLBACK fixed query. No TLS/authenticated-person, stock helper/copy/row heap accounting, cancellation/cleanup/commit correlation, public package or native authority qualification. No authentication or backend-key bodies retained in evidence.'}
(HERE/'pg8000-instance-native.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Original pg8000 instance hooks retain independent raw cells and metadata')
