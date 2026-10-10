"""Native aborted-transaction control observation; no public driver qualification."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from urllib.parse import urlparse,parse_qs
import pg8000.core
import pgserver
from pg8000.exceptions import DatabaseError
from pg8000_original_control_candidate import OriginalControlConnection,OriginalControlProducer
from pg8000_accounted_instance_candidate import AccountedSocket
from truss._resource_account import BytePermitAccount

HERE=Path(__file__).resolve().parent
if len(sys.argv)!=3 or sys.argv[1] not in ('counterexample','recovery') or Path(sys.argv[2]).name!=sys.argv[2] or not sys.argv[2].endswith('.json'):
    raise SystemExit('Supply counterexample|recovery and fresh receipt basename')
mode=sys.argv[1]; destination=HERE/sys.argv[2]
if destination.exists():raise SystemExit('Original receipt exists')
CORE_SHA='cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
if importlib.metadata.version('pg8000')!='1.31.5' or hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest()!=CORE_SHA:
    raise SystemExit('Pinned original driver required')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15':raise SystemExit('Corrected pgserver required')
observations=[]
def expect(name,expected,observed):
    if expected!=observed:raise ValueError(name+': independent native expectation mismatch')
    observations.append({'id':name,'expected':expected,'observed':observed})
with tempfile.TemporaryDirectory(prefix='truss-aborted-control-') as directory:
    server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
    supplied=None
    try:
        uri=urlparse(server.get_uri()); options=parse_qs(uri.query)
        host=options.get('host',[uri.hostname])[0]; port=int(options.get('port',[uri.port or 5432])[0])
        transport=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);transport.settimeout(10)
        transport.connect(str(Path(host)/f'.s.PGSQL.{port}'))
        producer=object();account=BytePermitAccount(producer,134217728,268435456,2048)
        supplied=AccountedSocket(transport,account,producer)
        connection=OriginalControlConnection(user='postgres',database='postgres',sock=supplied,ssl_context=False,startup_params={'client_encoding':'UTF8'})
        version=connection.parameter_statuses['server_version']
        if not version.startswith('16.15'):raise ValueError('Actual corrected native version required')
        connection.execute_simple('BEGIN');connection.execute_simple('SELECT pg_catalog.pg_current_xact_id()::text')
        connection.execute_simple('CREATE TEMP TABLE caller_sentinel(value integer)')
        connection.execute_simple('INSERT INTO caller_sentinel VALUES (7)')
        control=OriginalControlProducer(connection,account,producer)
        ticket=control.confirm_savepoint()
        connection.execute_simple('UPDATE caller_sentinel SET value=9')
        try:connection.execute_simple('SELECT 1/0')
        except DatabaseError as error:state=error.args[0]['C']
        else:raise ValueError('Expected original native error')
        expect('original-native-error', '22012',state)
        expect('original-ready-aborted', '5a0000000545',connection.original_controls[-1].hex())
        expect('payload-account-closed-after-complete-native-error',mode=='counterexample',account.snapshot(producer)[3])
        before_writes=supplied.file.remaining_writes
        if mode=='counterexample':
            try:control.rollback_savepoint(ticket)
            except ValueError:refused=True
            else:refused=False
            expect('local-rollback-unavailable',True,refused)
            expect('failed-rollback-submits-no-control',before_writes,supplied.file.remaining_writes)
            pid=int.from_bytes(connection._backend_key_data[:4],'big')
            psql=Path(pgserver.__file__).parent/'pginstall/bin/psql'
            observed=subprocess.check_output([str(psql),server.get_uri(),'-X','-qAt','-v','ON_ERROR_STOP=1','-c',f'SELECT state FROM pg_catalog.pg_stat_activity WHERE pid={pid}'],text=True,timeout=10).strip()
            expect('backend-still-aborted', 'idle in transaction (aborted)',observed)
        else:
            start=len(connection.original_controls)
            control.rollback_savepoint(ticket)
            expect('rollback-is-first-native-submission', '430000000d524f4c4c4241434b00',connection.original_controls[start].hex())
            expect('ready-restored-before-release', '5a0000000554',connection.original_controls[start+1].hex())
            expect('caller-work-preserved', [[b'7'.hex()]],[[cell.hex() for cell in row] for row in connection.execute_simple('SELECT value::text FROM caller_sentinel').rows])
            expect('original-attempt-settled', 'rolled_back',control.retained_attempts(producer)[0][3])
            next_ticket=control.confirm_savepoint()
            expect('failed-attempt-ordinal-not-reused','1',next_ticket.ordinal)
            expect('actual-xid-preserved',True,ticket.actual_xid==next_ticket.actual_xid)
            control.rollback_savepoint(next_ticket)
            control.close()
        retained=control.retained_attempts(producer)
    finally:
        if supplied is not None:supplied.close()
        server.cleanup()
files=[Path(__file__),HERE/'pg8000_original_control_candidate.py',HERE/'pg8000_instance_candidate.py',HERE/'pg8000_accounted_instance_candidate.py']
receipt={'mode':mode,'scope':'Actual completed native ErrorResponse/ReadyForQuery E followed by original local savepoint recovery or retained pre-fix counterexample; administrative fixture only',
 'serverVersion':version,'driverCoreSha256':CORE_SHA,'observations':observations,'retainedAttempts':[list(a) for a in retained],
 'sourceSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'driverPortQualified':False,
 'limitations':['No original security admission or operation artifacts','No complete resource/cleanup reservation or native containment profile','No transport loss or cancellation qualification','Host exclusivity remains a premise; no installed/public API']}
with destination.open('x') as output:output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'mode':mode,'observations':len(observations),'driverPortQualified':False}))
