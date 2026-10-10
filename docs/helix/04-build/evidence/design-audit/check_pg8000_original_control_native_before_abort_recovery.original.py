"""Native original control/ordinal composition, not full driver qualification."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from urllib.parse import urlparse, parse_qs
import pg8000.core
import pgserver
from pg8000_original_control_candidate import OriginalControlConnection, OriginalControlProducer, ConfirmedSavepoint
from pg8000_accounted_instance_candidate import AccountedSocket
from truss._resource_account import BytePermitAccount

HERE = Path(__file__).resolve().parent
CORE_SHA = 'cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
if len(sys.argv) != 2 or Path(sys.argv[1]).name != sys.argv[1] or not sys.argv[1].endswith('.json'):
    raise SystemExit('Supply fresh receipt basename')
destination = HERE / sys.argv[1]
if destination.exists(): raise SystemExit('Original receipt exists')
if importlib.metadata.version('pg8000') != '1.31.5' or hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest() != CORE_SHA:
    raise SystemExit('Original pinned driver required')
if importlib.metadata.version('pgserver') != '0.1.4+truss.pg16.15': raise SystemExit('Corrected pgserver required')
observations = []

def expect(identifier, expected, observed):
    if expected != observed: raise ValueError(identifier + ': independent expectation mismatch')
    observations.append({'id':identifier, 'expected':expected, 'observed':observed})

with tempfile.TemporaryDirectory(prefix='truss-original-control-') as directory:
    server = pgserver.get_server(Path(directory)/'data', cleanup_mode='stop')
    connections = []
    try:
        def connect():
            uri = urlparse(server.get_uri()); options = parse_qs(uri.query)
            host = options.get('host',[uri.hostname])[0]; port = int(options.get('port',[uri.port or 5432])[0])
            transport = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            transport.settimeout(10); transport.connect(str(Path(host)/f'.s.PGSQL.{port}'))
            producer = object(); account = BytePermitAccount(producer,134217728,268435456,1024)
            supplied = AccountedSocket(transport,account,producer)
            connection = OriginalControlConnection(user='postgres',database='postgres',sock=supplied,ssl_context=False,startup_params={'client_encoding':'UTF8'})
            connections.append(connection)
            connection.execute_simple('BEGIN')
            connection.execute_simple('SELECT pg_catalog.pg_current_xact_id()::text')
            return connection,account,producer
        connection,account,producer = connect()
        version = connection.parameter_statuses['server_version']
        if not version.startswith('16.15'): raise ValueError('Actual corrected server required')
        connection.execute_simple('CREATE TEMP TABLE sentinel(value integer)')
        connection.execute_simple('INSERT INTO sentinel VALUES (7)')
        port = OriginalControlProducer(connection,account,producer)
        first = port.confirm_savepoint()
        connection.execute_simple('UPDATE sentinel SET value=9')
        port.rollback_savepoint(first)
        expect('caller-work-preserved', [(b'7',)], connection.execute_simple('SELECT value::text FROM sentinel').rows)
        second = port.confirm_savepoint()
        expect('nonrewinding-original-ordinals', ['0','1'], [first.ordinal,second.ordinal])
        expect('same-actual-transaction', True, first.actual_xid == second.actual_xid)
        expect('rolled-back-attempt-retained', ['0','rolled_back','1','confirmed'], [port.retained_attempts(producer)[0][0],port.retained_attempts(producer)[0][3],port.retained_attempts(producer)[1][0],port.retained_attempts(producer)[1][3]])
        before = len(connection.original_controls)
        forged = ConfirmedSavepoint(second.ordinal, second.actual_xid)
        try: port.rollback_savepoint(forged)
        except ValueError: pass
        else: raise ValueError('Copied confirmation admitted')
        expect('copied-confirmation-no-submission', before, len(connection.original_controls))
        expect('copied-confirmation-closes-account', True, account.snapshot(producer)[3])
        try: port.confirm_savepoint()
        except ValueError: pass
        else: raise ValueError('Closed port reopened')
        expect('closed-port-no-submission', before, len(connection.original_controls))
        connection.close()

        connection,account,producer = connect()
        port = OriginalControlProducer(connection,account,producer,maximum_ordinal=0)
        first = port.confirm_savepoint(); port.rollback_savepoint(first)
        before = sum(frame == b'C\0\0\0\x0eSAVEPOINT\0' for frame in connection.original_controls)
        try: port.confirm_savepoint()
        except ValueError: pass
        else: raise ValueError('Exhausted original ordinal admitted')
        after = sum(frame == b'C\0\0\0\x0eSAVEPOINT\0' for frame in connection.original_controls)
        expect('exhaustion-no-new-savepoint', before, after)
        expect('exhaustion-closes-account', True, account.snapshot(producer)[3])
        connection.close()

        connection,account,producer = connect()
        port = OriginalControlProducer(connection,account,producer)
        connection.execute_simple('ROLLBACK'); connection.execute_simple('BEGIN')
        connection.execute_simple('SELECT pg_catalog.pg_current_xact_id()::text')
        before = len(connection.original_controls)
        try: port.confirm_savepoint()
        except ValueError: pass
        else: raise ValueError('Changed native transaction admitted')
        expect('changed-transaction-only-identity-observation', 2, len(connection.original_controls)-before)
        expect('changed-transaction-closes-account', True, account.snapshot(producer)[3])
        connection.close()

        connection,account,producer = connect()
        port = OriginalControlProducer(connection,account,producer)
        original_execute = connection.execute_simple
        def fail_after_savepoint(sql):
            result = original_execute(sql)
            if sql.startswith('SAVEPOINT '): raise RuntimeError('Original response handoff unavailable')
            return result
        connection.execute_simple = fail_after_savepoint
        try: port.confirm_savepoint()
        except RuntimeError: pass
        else: raise ValueError('Uncertain handoff admitted')
        before = len(connection.original_controls)
        try: port.confirm_savepoint()
        except ValueError: pass
        else: raise ValueError('Unknown attempt retried')
        expect('uncertain-control-no-retry', before, len(connection.original_controls))
        expect('uncertain-control-closes-account', True, account.snapshot(producer)[3])
        retained = port.retained_attempts(producer)
        expect('unknown-original-attempt-retained', [('0',port._xid,'SAVEPOINT truss_original_0','completion_unknown')], list(retained))
        # Observe actual backend state separately; quarantine is not termination.
        pid = int.from_bytes(connection._backend_key_data[:4], 'big') if type(connection._backend_key_data) is bytes and len(connection._backend_key_data) == 8 else None
        # Original pid comes from the actual socket's backend key, not a caller field.
        if pid is None: raise ValueError('Original backend pid unavailable')
        psql = Path(pgserver.__file__).parent/'pginstall/bin/psql'
        state = subprocess.check_output([str(psql),server.get_uri(),'-X','-qAt','-v','ON_ERROR_STOP=1','-c',f'SELECT state FROM pg_catalog.pg_stat_activity WHERE pid={pid}'],text=True,timeout=10).strip()
        expect('quarantine-is-not-native-termination', 'idle in transaction', state)
        connection.close()
    finally:
        for connection in connections:
            try: connection.close()
            except Exception: pass
        server.cleanup()

# JSON receipts retain bytes as explicit hex; expectation source remains original.
def transport(value):
    if type(value) is bytes: return {'bytesHex':value.hex()}
    if type(value) in (tuple,list): return [transport(v) for v in value]
    if type(value) is dict: return {k:transport(v) for k,v in value.items()}
    return value
files = [Path(__file__), HERE/'pg8000_original_control_candidate.py', HERE/'pg8000_instance_candidate.py',HERE/'pg8000_accounted_instance_candidate.py']
receipt = {'scope':'Trusted original physical connection, assigned xid and confirmed fixed control frames with permanent host ordinal custody; administrative local fixture only',
 'serverVersion':version,'driverCoreSha256':CORE_SHA,'observations':transport(observations),
 'sourceSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
 'installedModuleSha256':{name:hashlib.sha256((Path(__import__('truss').__file__).parent/name).read_bytes()).hexdigest() for name in ['_operation_ordinal.py','_resource_account.py','_accounted_receive.py']},
 'historicalInitialCandidate':{'receipt':'pg8000-original-control-native.json','originalSourceArchives':['pg8000_original_control_candidate_before_attempt_custody.original.py','check_pg8000_original_control_native_before_attempt_custody.original.py']},
 'driverPortQualified':False,'limitations':['Exclusive trusted host custody is a premise, no malicious-host sandbox','No actual operation admission/artifact/security or ready installer','No complete native work/object/parser/containment account','Post-execution response handoff injection is not arbitrary network loss','No cancellation, commit_unknown or reconciliation qualification']}
with destination.open('x') as output: output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(observations),'driverPortQualified':False}))
