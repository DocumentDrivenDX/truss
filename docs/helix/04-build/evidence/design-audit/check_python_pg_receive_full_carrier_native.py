"""Read-only local protocol probe; no driver/security/resource qualification.

Requires the existing owned truss-runtime-admission container on 127.0.0.1:15434.
Only AuthenticationOk is admitted; no password or other authentication flow.
"""
import hashlib
import json
from pathlib import Path
import socket
import struct
import sys
from python_pg_frame_candidate import row_description, data_row, MAX_FRAME
from python_pg_receive_candidate import Receiver

if len(sys.argv) != 1:
    raise SystemExit('No arguments admitted')

HERE = Path(__file__).resolve().parent
QUERY = "BEGIN READ ONLY; SET LOCAL bytea_output = 'hex'; SELECT repeat('a', 4194304)::bytea AS carrier; ROLLBACK;"
EXPECTED_CELLS = (b'\\x' + b'61' * 4194304,)
EXPECTED_COLUMNS = [(b'carrier', 17)]
frames = []
receiver = None


def receive(connection):
    if receiver is None or receiver.transport is not connection:
        raise ValueError('Original receiver/connection correspondence required')
    source = receiver.receive()
    frames.append(source)
    return source


with socket.create_connection(('127.0.0.1', 15434), timeout=10) as connection:
    connection.settimeout(10)
    receiver = Receiver(connection, frame_bytes=8388621, total_bytes=16777216,
                        messages=100, reads=10000)
    startup = struct.pack('!i', 196608) + b'user\0postgres\0database\0postgres\0client_encoding\0UTF8\0\0'
    connection.sendall(struct.pack('!i', len(startup) + 4) + startup)
    authenticated = False
    while True:
        source = receive(connection)
        kind, body = source[:1], source[5:]
        if kind == b'R':
            if authenticated or body != b'\0\0\0\0':
                raise ValueError('Unsupported probe authentication')
            authenticated = True
        elif kind == b'Z':
            if not authenticated or body != b'I':
                raise ValueError('Unexpected startup state')
            break
        elif kind not in (b'S', b'K', b'N'):
            raise ValueError('Unexpected startup response')

    query = QUERY.encode('utf8') + b'\0'
    connection.sendall(b'Q' + struct.pack('!i', len(query) + 4) + query)
    description = row = None
    commands = []
    decoder_refused = False
    while True:
        source = receive(connection)
        kind, body = source[:1], source[5:]
        if kind == b'T':
            if description is not None:
                raise ValueError('Duplicate native description')
            description = row_description(source)
        elif kind == b'D':
            if description is None or row is not None:
                raise ValueError('Unexpected native row')
            if len(description) != 1 or source[5:11] != b'\0\1' + struct.pack('!i', 8388610):
                raise ValueError('Independent carrier framing mismatch')
            try:
                data_row(source, 1)
            except ValueError as error:
                if 'capacity' not in str(error):
                    raise
                decoder_refused = True
            else:
                raise ValueError('Unexpected fixed-limit decoder admission')
            row = (source[11:],)
        elif kind == b'C':
            commands.append(body)
        elif kind == b'Z':
            if body != b'I':
                raise ValueError('Probe transaction did not end idle')
            break
        else:
            raise ValueError('Unexpected query response')
    connection.sendall(b'X\0\0\0\4')

if row != EXPECTED_CELLS or description is None:
    raise ValueError('Independent native cell mismatch')
if [(c.name, c.type_oid) for c in description] != EXPECTED_COLUMNS:
    raise ValueError('Independent native column mismatch')
if any((c.table_oid, c.attribute, c.type_size, c.modifier, c.format) !=
       (0, 0, -1, -1, 0) for c in description):
    raise ValueError('Independent native descriptor mismatch')
if commands != [b'BEGIN\0', b'SET\0', b'SELECT 1\0', b'ROLLBACK\0']:
    raise ValueError('Incomplete native command sequence')

if [len(value) for value in frames if value[:1] == b'D'] != [8388621]:
    raise ValueError('Unexpected full carrier frame size')

receipt = {
    'status': 'passed_read_only_native_receive_full_carrier_size_candidate',
    'query': QUERY,
    'expectedPayloadBytes': 4194304,
    'observedCellBytes': len(row[0]),
    'observedDataRowBytes': [len(value) for value in frames if value[:1] == b'D'],
    'completeCellEqualsIndependentLiteral': row == EXPECTED_CELLS,
    'fixedOneMiBDecoderRefused': decoder_refused,
    'framesHex': [value.hex() for value in frames if value[:1] in (b'T', b'C', b'Z')],
    'orderedTypeOids': [c.type_oid for c in description],
    'rawCellsSha256': [hashlib.sha256(value).hexdigest() for value in row],
    'sourceSha256': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                     for name in ['python_pg_frame_candidate.py', 'python_pg_receive_candidate.py', Path(__file__).name]},
    'remainingRawBounds': {'bytes': receiver.remaining_bytes,
                           'messages': receiver.remaining_messages,
                           'readCalls': receiver.remaining_reads},
    'scope': 'Administrative local trust-auth probe, BEGIN READ ONLY/ROLLBACK; raw recv_into framing and independent complete carrier-byte comparison only; fixed-one-MiB decoder refused as expected. No installed changes, supported driver, ingress/account/TLS/native containment, current security or publication qualification.'}
(HERE / 'python-pg-receive-full-carrier-native.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Complete four-MiB bytea text carrier matches independent bytes; DataRow is 8388621 bytes')
