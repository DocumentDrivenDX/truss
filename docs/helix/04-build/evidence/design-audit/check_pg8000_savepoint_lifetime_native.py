"""Original shared issuer/namespace/descendant native controls; no released driver."""
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
from pg8000_original_control_candidate import OriginalControlConnection,OriginalControlProducer
from pg8000_accounted_instance_candidate import AccountedSocket
from truss._resource_account import BytePermitAccount

HERE=Path(__file__).resolve().parent
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):
    raise SystemExit('Supply fresh receipt basename')
destination=HERE/sys.argv[1]
if destination.exists():raise SystemExit('Original receipt exists')
CORE_SHA='cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
if importlib.metadata.version('pg8000')!='1.31.5' or hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest()!=CORE_SHA:
    raise SystemExit('Original pinned driver required')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15':raise SystemExit('Corrected pgserver required')
observations=[];owned=[]
def expect(name,expected,observed):
    if expected!=observed:raise ValueError(name+': independent expectation mismatch')
    observations.append({'id':name,'expected':expected,'observed':observed})
with tempfile.TemporaryDirectory(prefix='truss-savepoint-lifetime-') as directory:
    server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
    try:
        def connect():
            uri=urlparse(server.get_uri());options=parse_qs(uri.query)
            host=options.get('host',[uri.hostname])[0];port=int(options.get('port',[uri.port or 5432])[0])
            transport=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);transport.settimeout(10)
            transport.connect(str(Path(host)/f'.s.PGSQL.{port}'))
            producer=object();account=BytePermitAccount(producer,134217728,268435456,4096)
            supplied=AccountedSocket(transport,account,producer);owned.append(supplied)
            connection=OriginalControlConnection(user='postgres',database='postgres',sock=supplied,ssl_context=False,startup_params={'client_encoding':'UTF8'})
            connection.execute_simple('BEGIN');connection.execute_simple('SELECT pg_catalog.pg_current_xact_id()::text')
            return connection,account,producer,supplied
        connection,account,producer,supplied=connect()
        version=connection.parameter_statuses['server_version']
        if not version.startswith('16.15'):raise ValueError('Actual corrected native version required')
        connection.execute_simple('CREATE TEMP TABLE sentinel(value integer)')
        connection.execute_simple('INSERT INTO sentinel VALUES (7)')
        first=OriginalControlProducer(connection,account,producer)
        parent=first.confirm_savepoint()
        connection.execute_simple('UPDATE sentinel SET value=9')
        second=OriginalControlProducer(connection,account,producer)
        child=second.confirm_savepoint()
        connection.execute_simple('UPDATE sentinel SET value=11')
        expect('shared-physical-transaction-issuer',['0','1'],[parent.ordinal,child.ordinal])
        expect('distinct-registered-participant-names',
            ['truss_sp_'+'0'*32+'_1','truss_sp_'+'0'*31+'1'+'_2'],[parent.native_name,child.native_name])
        expect('shared-original-attempt-inventory',True,first.retained_attempts(producer)==second.retained_attempts(producer))
        first.rollback_savepoint(parent)
        expect('ancestor-rollback-preserves-caller-work',[[b'7'.hex()]],[[cell.hex() for cell in row] for row in connection.execute_simple('SELECT value::text FROM sentinel').rows])
        expect('cross-participant-descendant-invalidated',['rolled_back','invalidated_by_ancestor_rollback'],[a[3] for a in second.retained_attempts(producer)])
        next_ticket=second.confirm_savepoint()
        expect('shared-issuer-not-rewound-after-ancestor-rollback','2',next_ticket.ordinal)
        before=len(connection.original_controls)
        try:second.rollback_savepoint(child)
        except ValueError:pass
        else:raise ValueError('Destroyed descendant admitted')
        expect('invalidated-descendant-no-native-submission',before,len(connection.original_controls))
        supplied.close()

        connection,account,producer,supplied=connect()
        foreign_producer=object();foreign_account=BytePermitAccount(foreign_producer,1024,2048,16)
        before=len(connection.original_controls);snapshot=account.snapshot(producer)
        try:OriginalControlProducer(connection,foreign_account,foreign_producer)
        except ValueError:pass
        else:raise ValueError('Foreign connection account admitted')
        expect('foreign-account-no-native-submission',before,len(connection.original_controls))
        expect('original-account-unchanged-by-foreign-construction',list(snapshot),list(account.snapshot(producer)))
        expect('foreign-account-unspent',[0,0,0,False],list(foreign_account.snapshot(foreign_producer)))
        supplied.close()

        connection,account,producer,supplied=connect()
        first=OriginalControlProducer(connection,account,producer);parent=first.confirm_savepoint()
        second=OriginalControlProducer(connection,account,producer);child=second.confirm_savepoint()
        original_execute=connection.execute_simple
        def fail_after_rollback(sql):
            result=original_execute(sql)
            if sql.startswith('ROLLBACK TO SAVEPOINT '):raise RuntimeError('Original rollback handoff unavailable')
            return result
        connection.execute_simple=fail_after_rollback
        try:first.rollback_savepoint(parent)
        except RuntimeError:pass
        else:raise ValueError('Unknown rollback published as confirmed')
        expect('uncertain-ancestor-and-descendant-retained',['rollback_unknown','ancestor_rollback_unknown'],[a[3] for a in second.retained_attempts(producer)])
        before=len(connection.original_controls)
        try:second.rollback_savepoint(child)
        except ValueError:pass
        else:raise ValueError('Unknown descendant admitted')
        expect('peer-facade-cannot-reopen-unknown-custody',before,len(connection.original_controls))
        expect('unknown-original-account-closed',True,account.snapshot(producer)[3])
        pid=int.from_bytes(connection._backend_key_data[:4],'big');psql=Path(pgserver.__file__).parent/'pginstall/bin/psql'
        state=subprocess.check_output([str(psql),server.get_uri(),'-X','-qAt','-v','ON_ERROR_STOP=1','-c',f'SELECT state FROM pg_catalog.pg_stat_activity WHERE pid={pid}'],text=True,timeout=10).strip()
        expect('unknown-rollback-is-not-native-termination','idle in transaction',state)
    finally:
        for supplied in owned:supplied.close()
        server.cleanup()
files=[Path(__file__),HERE/'pg8000_original_control_candidate.py',HERE/'pg8000_instance_candidate.py',HERE/'pg8000_accounted_instance_candidate.py']
receipt={'scope':'Actual native ancestor rollback, shared physical-connection issuer and registered participant namespaces with retained unknown descendants; administrative fixture only',
 'serverVersion':version,'driverCoreSha256':CORE_SHA,'observations':observations,
 'sourceSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
 'installedModuleSha256':{name:hashlib.sha256((Path(__import__('truss').__file__).parent/name).read_bytes()).hexdigest() for name in ['_operation_ordinal.py','_resource_account.py','_accounted_receive.py']},
 'driverPortQualified':False,'limitations':['Host exclusively owns original connection and honors reserved namespaces','One adopted native epoch per candidate connection; full reuse not qualified','No native operation admission/security/ready installer','No complete accounting or earmarked cleanup capacity','Post-command handoff injection is not arbitrary network loss','No cancellation, commit_unknown or reconciliation qualification']}
with destination.open('x') as output:output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(observations),'driverPortQualified':False}))
