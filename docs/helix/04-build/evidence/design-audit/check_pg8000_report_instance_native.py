"""Fixed local read-only full-report echo through actual pg8000; no authority claim."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket
import sys
import pg8000.core
from pg8000_report_instance_candidate import ReportSocket, ReportConnection
from check_report_response_boundary import build, check, CONTRACTS
from python_report_response_candidate import ReportResponseCandidate

if len(sys.argv) != 1:
    raise SystemExit('No arguments admitted')
HERE = Path(__file__).resolve().parent
CORE_SHA = 'cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
if importlib.metadata.version('pg8000') != '1.31.5' or hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest() != CORE_SHA:
    raise SystemExit('Original driver required before connection')
check()
_, source = build(4194304)
query = "BEGIN READ ONLY; SELECT '" + source.decode('utf8').replace("'", "''") + "'::text AS carrier; ROLLBACK;"
with socket.create_connection(('127.0.0.1',15434),timeout=10) as transport:
    supplied = ReportSocket(transport)
    connection = ReportConnection(user='postgres',database='postgres',sock=supplied,
                                  ssl_context=False,startup_params={'client_encoding':'UTF8'})
    try:
        encodings = {name:connection.parameter_statuses.get(name) for name in ['client_encoding','server_encoding']}
        if encodings != {'client_encoding':'UTF8','server_encoding':'UTF8'}:
            raise ValueError('Original UTF8 observations required')
        context = connection.execute_simple(query)
        if context.rows != [(source,)] or [(c.name,c.type_oid,c.format) for c in context.columns] != [(b'carrier',25,0)]:
            raise ValueError('Independent complete report carrier mismatch')
        if connection.experiment_commands != [b'BEGIN\0',b'SELECT 1\0',b'ROLLBACK\0'] or connection._transaction_status != b'I':
            raise ValueError('Original fixed cycle mismatch')
        result = ReportResponseCandidate(CONTRACTS).prepare(context.rows[0][0])
        if result.original.source_bytes != source or len(result.original.value.entries) != 19:
            raise ValueError('Complete response schema/bytes mismatch')
    finally:
        connection.close()
names = [Path(__file__).name,'pg8000_report_instance_candidate.py','pg8000_instance_candidate.py',
         'python_pg_receive_candidate.py','python_pg_frame_candidate.py','python_report_frame_candidate.py',
         'python_report_response_candidate.py','python_report_wire_candidate.py','python_raw_json_candidate.py',
         'check_report_response_boundary.py']
receipt = {'status':'passed_local_read_only_pg8000_full_report_echo','python':sys.version,
           'driverCoreSha256':CORE_SHA,'querySha256':hashlib.sha256(query.encode()).hexdigest(),
           'originalReportSha256':hashlib.sha256(source).hexdigest(),'observedReportSha256':hashlib.sha256(context.rows[0][0]).hexdigest(),
           'observedBytes':len(context.rows[0][0]),'observedFields':len(result.original.value.entries),
           'observedEncodings':encodings,'orderedCommandTags':[v.decode('ascii') for v in connection.experiment_commands],
           'messageKindsAndSizes':supplied.file.message_sizes,
           'dependencies':{n:importlib.metadata.version(n) for n in ['pg8000','scramp','asn1crypto','python-dateutil','six','jsonschema','referencing','rpds-py','attrs','jsonschema-specifications']},
           'sourceSha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names},
           'driverPortQualified':False,
           'scope':'Actual installed driver, separate report-only raw bounds, original text descriptor/frame and full synthetic nineteen-field response schema. Fixed local trust read-only echo only. No genuine report producer/persistence, original account/authority, TLS/person, cancellation/termination/commit/publication or managed target qualification.'}
(HERE/'pg8000-report-instance-native.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Actual pg8000 report path preserves all four-MiB original bytes and nineteen fields')
