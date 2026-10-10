"""Private local-trust driver seam experiment; no original port/account authority."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket
import sys
from pg8000_instance_candidate import SuppliedSocket, RawConnection
import pg8000.core
from python_pg_receive_candidate import Receiver
from python_pg_frame_candidate import row_description, data_row

if len(sys.argv) != 1:
    raise SystemExit('No arguments admitted')
HERE = Path(__file__).resolve().parent
CORE_SHA = 'cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
if importlib.metadata.version('pg8000') != '1.31.5' or hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest() != CORE_SHA:
    raise SystemExit('Original driver source required before connection')




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
           'sourceSha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in [Path(__file__).name,'pg8000_instance_candidate.py','python_pg_receive_candidate.py','python_pg_frame_candidate.py']},
           'driverPortQualified':False,
           'scope':'Supplied local trust socket and instance-bound raw handlers only. BEGIN READ ONLY/ROLLBACK fixed query. No TLS/authenticated-person, stock helper/copy/row heap accounting, cancellation/cleanup/commit correlation, public package or native authority qualification. No authentication or backend-key bodies retained in evidence.'}
(HERE/'pg8000-instance-native.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Original pg8000 instance hooks retain independent raw cells and metadata')
