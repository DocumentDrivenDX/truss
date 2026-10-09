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
from python_report_frame_candidate import report_cell
from check_report_response_boundary import build, check, CONTRACTS
from python_report_response_candidate import ReportResponseCandidate

if len(sys.argv) != 1:
    raise SystemExit('No arguments admitted')

HERE = Path(__file__).resolve().parent
check()
EXPECTED_REPORT, EXPECTED_SOURCE = build(4194304)
QUERY = "BEGIN READ ONLY; SELECT '" + EXPECTED_SOURCE.decode('utf8').replace("'", "''") + "'::text AS carrier; ROLLBACK;"
EXPECTED_CELLS = (EXPECTED_SOURCE,)
EXPECTED_COLUMNS = [(b'carrier', 25)]
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
    receiver = Receiver(connection, frame_bytes=4194315, total_bytes=16777216,
                        messages=100, reads=10000)
    startup = struct.pack('!i', 196608) + b'user\0postgres\0database\0postgres\0client_encoding\0UTF8\0\0'
    connection.sendall(struct.pack('!i', len(startup) + 4) + startup)
    authenticated = False
    encodings = {}
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
        elif kind == b'S':
            fields = body.split(b'\0')
            if len(fields) != 3 or fields[-1] != b'':
                raise ValueError('Malformed startup parameter')
            if fields[0] in (b'server_encoding', b'client_encoding'):
                if fields[0] in encodings:
                    raise ValueError('Duplicate encoding observation')
                encodings[fields[0]] = fields[1]
        elif kind not in (b'K', b'N'):
            raise ValueError('Unexpected startup response')

    if encodings != {b'server_encoding': b'UTF8', b'client_encoding': b'UTF8'}:
        raise ValueError('Original UTF8 server/client admission required')
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
            if len(description) != 1 or source[5:11] != b'\0\1' + struct.pack('!i', 4194304):
                raise ValueError('Independent carrier framing mismatch')
            try:
                data_row(source, 1)
            except ValueError as error:
                if 'capacity' not in str(error):
                    raise
                decoder_refused = True
            else:
                raise ValueError('Unexpected fixed-limit decoder admission')
            row = (report_cell(source),)
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

if [len(value) for value in frames if value[:1] == b'D'] != [4194315]:
    raise ValueError('Unexpected full carrier frame size')

admitted = ReportResponseCandidate(CONTRACTS).prepare(row[0])
if admitted.original.source_bytes != EXPECTED_SOURCE or len(admitted.original.value.entries) != 19:
    raise ValueError('Complete response codec correspondence failed')

receipt = {
    'status': 'passed_read_only_native_full_report_echo_response_candidate',
    'queryTemplate': 'BEGIN READ ONLY; SELECT <independently frozen report literal>::text AS carrier; ROLLBACK',
    'querySha256': hashlib.sha256(QUERY.encode('utf8')).hexdigest(),
    'expectedReportSha256': hashlib.sha256(EXPECTED_SOURCE).hexdigest(),
    'observedReportFields': len(admitted.original.value.entries),
    'responseScope': admitted.scope,
    'observedEncodings': {key.decode('ascii'): value.decode('ascii')
                          for key, value in encodings.items()},
    'expectedPayloadBytes': 4194304,
    'observedCellBytes': len(row[0]),
    'observedDataRowBytes': [len(value) for value in frames if value[:1] == b'D'],
    'completeCellEqualsIndependentLiteral': row == EXPECTED_CELLS,
    'fixedOneMiBDecoderRefused': decoder_refused,
    'responseFrameDecoderAdmitted': True,
    'framesHex': [value.hex() for value in frames if value[:1] in (b'T', b'C', b'Z')],
    'orderedTypeOids': [c.type_oid for c in description],
    'rawCellsSha256': [hashlib.sha256(value).hexdigest() for value in row],
    'sourceSha256': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                     for name in ['python_pg_frame_candidate.py', 'python_pg_receive_candidate.py',
                                  'python_report_frame_candidate.py',
                                  'python_report_response_candidate.py', 'python_report_wire_candidate.py',
                                  'python_raw_json_candidate.py', 'check_report_response_boundary.py', Path(__file__).name]},
    'remainingRawBounds': {'bytes': receiver.remaining_bytes,
                           'messages': receiver.remaining_messages,
                           'readCalls': receiver.remaining_reads},
    'scope': 'Administrative local trust-auth probe, BEGIN READ ONLY/ROLLBACK; raw recv_into framing, response-only complete single-cell frame syntax, complete frozen synthetic nineteen-field report byte comparison and response-schema candidate only; fixed-one-MiB decoder refused as expected. No genuine diagnostic/report producer or committed report persistence. No installed changes, supported driver, ingress/account/TLS/native containment, current security or publication qualification.'}
(HERE / 'python-report-response-native-echo.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Complete frozen nineteen-field native echo matches original bytes and response schema')
