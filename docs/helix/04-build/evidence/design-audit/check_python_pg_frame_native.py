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

if len(sys.argv) != 1:
    raise SystemExit('No arguments admitted')

HERE = Path(__file__).resolve().parent
QUERY = "BEGIN READ ONLY; SELECT NULL::text AS n, ''::text AS empty, 9007199254740993.0000000000000000001::numeric AS exact, 'é𐀀'::text AS unicode, current_setting('server_version_num')::text AS server; ROLLBACK;"
EXPECTED_CELLS = (None, b'', b'9007199254740993.0000000000000000001',
                  'é𐀀'.encode('utf8'), b'170009')
EXPECTED_COLUMNS = [(b'n', 25), (b'empty', 25), (b'exact', 1700),
                    (b'unicode', 25), (b'server', 25)]
frames = []
total = 0


def read_exact(connection, count):
    chunks = []
    remaining = count
    while remaining:
        value = connection.recv(remaining)
        if not value:
            raise ValueError('Incomplete native response')
        chunks.append(value)
        remaining -= len(value)
    return b''.join(chunks)


def receive(connection):
    global total
    header = read_exact(connection, 5)
    size = struct.unpack('!i', header[1:])[0]
    if size < 4 or size + 1 > MAX_FRAME or total + size + 1 > 2097152:
        raise ValueError('Probe receive capacity')
    source = header + read_exact(connection, size - 4)
    total += len(source)
    frames.append(source)
    if len(frames) > 100:
        raise ValueError('Probe message capacity')
    return source


with socket.create_connection(('127.0.0.1', 15434), timeout=10) as connection:
    connection.settimeout(10)
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
            row = data_row(source, len(description))
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
if commands != [b'BEGIN\0', b'SELECT 1\0', b'ROLLBACK\0']:
    raise ValueError('Incomplete native command sequence')

receipt = {
    'status': 'passed_read_only_native_frame_candidate',
    'serverVersionNum': '170009', 'query': QUERY,
    'framesHex': [value.hex() for value in frames if value[:1] in (b'T', b'D', b'C', b'Z')],
    'orderedTypeOids': [c.type_oid for c in description],
    'rawCellsHex': [None if value is None else value.hex() for value in row],
    'sourceSha256': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                     for name in ['python_pg_frame_candidate.py', Path(__file__).name]},
    'scope': 'Administrative local trust-auth probe, BEGIN READ ONLY/ROLLBACK; exact native result syntax/metadata/cells only. No installed changes, supported driver, ingress/account/TLS/native containment, current security or publication qualification.'}
(HERE / 'python-pg-frame-native.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Native ordered metadata and five exact raw cells match independent expectations')
