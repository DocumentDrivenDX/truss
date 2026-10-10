"""Actual four-family original confirmation/admission, not a complete engine."""
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
from truss._accounted_receive import AccountedReceiver
from truss._operation_admission import AdmissionRefusal
from truss._operation_registry import COLUMNS,decode_operation_registry
from truss._resource_account import BytePermitAccount
from pg8000_accounted_instance_candidate import AccountedSocket
from pg8000_original_control_candidate import OriginalControlConnection,OriginalControlProducer
from pg8000_original_admission_candidate import OriginalAdmissionProducer,NativeAdmissionInput,NativeAdmissionObservation,ContainedNativeRejection

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):
    raise SystemExit('Supply fresh receipt basename')
destination=HERE/sys.argv[1]
if destination.exists():raise SystemExit('Original receipt exists')
CORE_SHA='cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
if importlib.metadata.version('pg8000')!='1.31.5' or hashlib.sha256(Path(pg8000.core.__file__).read_bytes()).hexdigest()!=CORE_SHA:
    raise SystemExit('Original pinned driver required')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15':raise SystemExit('Corrected pgserver required')
paths=['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
 'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql',
 'packages/postgresql/native/source-epoch-lock.sql',
 'docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql',
 'docs/helix/02-design/contracts/row-operation-registry-observation-v0.1.proposal.sql']
paths+=['packages/postgresql/native/issued-operation-admission/'+n for n in ['operation-admission.sql','operation-asserted-origin-admission.sql','operation-epoch-context-admission.sql','operation-configuration-context-admission.sql']]
originals={p:(ROOT/p).read_bytes() for p in paths}
registry_text=originals[paths[4]].decode('utf8')
registry_sql=registry_text[registry_text.index('SELECT\n'):]
observations=[];families=[];owned=[]
def expect(family,name,expected,observed):
    if expected!=observed:raise ValueError(family+'/'+name+': independent expectation mismatch')
    observations.append({'family':family,'id':name,'expected':expected,'observed':observed})
def cells(result):return [[None if v is None else v.decode('ascii') for v in row] for row in result.rows]
with tempfile.TemporaryDirectory(prefix='truss-four-family-admission-') as directory:
    server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
    try:
        psql=Path(pgserver.__file__).parent/'pginstall/bin/psql'
        setup=originals[paths[0]].decode()+';\n'+originals[paths[1]].decode()+';\n'+originals[paths[2]].decode()+';\n'
        setup+=originals[paths[3]].decode().split('INSERT INTO truss.row_home_operation')[0]
        setup+="INSERT INTO truss.source_epoch_current VALUES (1,'guard-fixture','guard-fixture-epoch');\n"
        setup+="INSERT INTO truss.installation_admission (head_id,installation_id_utf8,source_epoch_utf8,configuration_generation,key_reuse,journal_mode,configuration_bytes,selected_binding_bytes,installed_inventory_bytes) VALUES (1,convert_to('guard-fixture','UTF8'),convert_to('guard-fixture-epoch','UTF8'),7,'forbid','engine',decode('0001ff','hex'),convert_to('binding fixture','UTF8'),convert_to('inventory fixture','UTF8'));\n"
        setup+=';\n'.join(originals[p].decode() for p in paths[5:])
        subprocess.run([str(psql),server.get_uri(),'-X','-qAt','-v','ON_ERROR_STOP=1'],input=setup,text=True,stdout=subprocess.DEVNULL,check=True,timeout=30)
        for family in ('base','asserted','epoch','configuration'):
            uri=urlparse(server.get_uri());options=parse_qs(uri.query)
            host=options.get('host',[uri.hostname])[0];port=int(options.get('port',[uri.port or 5432])[0])
            transport=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);transport.settimeout(10)
            transport.connect(str(Path(host)/f'.s.PGSQL.{port}'))
            producer=object();account=BytePermitAccount(producer,134217728,268435456,16384)
            supplied=AccountedSocket(transport,account,producer);owned.append(supplied)
            # Select finite instance limits before makefile/startup/any ingress;
            # no counters/account are replaced after native work begins.
            supplied.file.receiver=AccountedReceiver(transport,account,producer,
                frame_bytes=1048576,total_bytes=33554432,messages=512,reads=50000)
            supplied.file.remaining_writes=512;supplied.file.remaining_send_bytes=16777216
            connection=OriginalControlConnection(user='postgres',database='postgres',sock=supplied,ssl_context=False,startup_params={'client_encoding':'UTF8'})
            version=connection.parameter_statuses['server_version']
            if not version.startswith('16.15'):raise ValueError('Actual corrected native version required')
            connection.execute_simple('BEGIN')
            actual=cells(connection.execute_simple("SELECT pg_catalog.pg_current_xact_id()::text,current_user::text,session_user::text,current_database()::text,pg_backend_pid()::text,(SELECT oid::text FROM pg_catalog.pg_roles WHERE rolname=current_user),(SELECT oid::text FROM pg_catalog.pg_roles WHERE rolname=session_user)"))[0]
            xid,actor,session_actor,database,pid,actor_oid,session_oid=actual
            connection.execute_simple('CREATE TEMP TABLE caller_sentinel(value integer)')
            connection.execute_simple('INSERT INTO caller_sentinel VALUES (7)')
            controls=OriginalControlProducer(connection,account,producer)
            admission=OriginalAdmissionProducer(controls)
            arguments={'family':family,'kind':'mutation','artifacts':tuple(bytes([i]) for i in range(1,7))}
            if family!='base':arguments.update(asserted=b'original asserted fixture',capture_profile=b'original capture profile fixture')
            if family in ('epoch','configuration'):arguments.update(installation='guard-fixture',source_epoch='guard-fixture-epoch',incarnation='guard-fixture-incarnation')
            if family=='configuration':arguments.update(configuration_profile=b'configuration admission fixture')
            value=NativeAdmissionInput(**arguments)
            captures=[]
            def observe_registry(expected_ordinal,context_hex=None):
                result=connection.execute_simple(registry_sql)
                raw=cells(result)
                decoded=decode_operation_registry(xid,tuple(c.name.decode('ascii') for c in result.columns),raw,'SELECT',str(result.row_count),8,65536)
                expected=[] if expected_ordinal is None else [(xid,expected_ordinal,'mutation','admitted','0',None,None,None,context_hex,'01','02','03','04','05','06',None)]
                expect(family,'complete-registry-'+('empty' if expected_ordinal is None else expected_ordinal),[list(row) for row in expected],[list(row) for row in decoded])
                config=cells(connection.execute_simple("SELECT original_writer_xid::text,operation_ordinal::text,installation_id,source_epoch,target_incarnation,configuration_generation::text,key_reuse,journal_mode,encode(original_context_sha256,'hex'),encode(admission_profile_bytes,'hex'),encode(configuration_bytes,'hex'),encode(selected_binding_bytes,'hex'),encode(installed_inventory_bytes,'hex') FROM truss.operation_configuration WHERE original_writer_xid=pg_catalog.pg_current_xact_id_if_assigned()"))
                wanted=[]
                if family=='configuration' and expected_ordinal is not None:
                    wanted=[[xid,expected_ordinal,'guard-fixture','guard-fixture-epoch','guard-fixture-incarnation','7','forbid','engine',hashlib.sha256(bytes.fromhex(context_hex)).hexdigest(),b'configuration admission fixture'.hex(),'0001ff',b'binding fixture'.hex(),b'inventory fixture'.hex()]]
                expect(family,'complete-configuration-'+('empty' if expected_ordinal is None else expected_ordinal),wanted,config)
            def verify_context(observed,ordinal):
                expect(family,'original-native-result-'+ordinal,True,type(observed) is NativeAdmissionObservation)
                expect(family,'native-issued-identity-'+ordinal,[xid,ordinal],[observed.writer_xid,observed.ordinal])
                expected={'interfaceVersion':{'base':'truss-native-operation-context/0.2','asserted':'truss-native-operation-context/0.3','epoch':'truss-native-operation-context/0.4','configuration':'truss-native-operation-context/0.4'}[family],
                  'xid':xid,'ordinal':ordinal,'sessionUser':session_actor,'actingUser':actor,'actorRoleOid':actor_oid,'sessionRoleOid':session_oid,'database':database,'backendPid':pid}
                if family!='base':expected.update(assertedOriginUtf8Hex=b'original asserted fixture'.hex(),assertedOriginCaptureProfileHex=b'original capture profile fixture'.hex())
                if family in ('epoch','configuration'):expected.update(installationId='guard-fixture',sourceEpoch='guard-fixture-epoch',targetIncarnation='guard-fixture-incarnation',sourceEpochProfileHex=b'fixture-profile'.hex(),sourceEpochEvidenceHex=b'fixture-evidence'.hex())
                actual_context=json.loads(bytes.fromhex(observed.original_context_hex).decode('utf8'))
                expect(family,'complete-original-context-'+ordinal,expected,actual_context)
                captures.append({'ordinal':ordinal,'originalContextHex':observed.original_context_hex,'context':actual_context})
            first=controls.confirm_savepoint();first_ticket=admission.register(first)
            observed=admission.submit(first_ticket,value);verify_context(observed,'0')
            observe_registry('0',observed.original_context_hex)
            before=len(connection.original_controls)
            try:admission.submit(first_ticket,value)
            except AdmissionRefusal:pass
            else:raise ValueError('Original confirmation reused')
            expect(family,'one-use-no-second-submission',before,len(connection.original_controls))
            controls.rollback_savepoint(first);observe_registry(None)
            peer_controls=OriginalControlProducer(connection,account,producer)
            peer_admission=OriginalAdmissionProducer(peer_controls)
            rejected=peer_controls.confirm_savepoint();rejected_ticket=peer_admission.register(rejected)
            invalid=NativeAdmissionInput(**{**arguments,'kind':'invalid-kind'})
            observed=peer_admission.submit(rejected_ticket,invalid)
            expect(family,'actual-native-rejection-contained',True,type(observed) is ContainedNativeRejection)
            expect(family,'original-rejection-code','22023',observed.original_error.args[0]['C'])
            expect(family,'restored-native-ready','54',connection._ready_status.hex())
            observe_registry(None)
            third=peer_controls.confirm_savepoint();third_ticket=peer_admission.register(third)
            observed=peer_admission.submit(third_ticket,value);verify_context(observed,'2')
            observe_registry('2',observed.original_context_hex)
            peer_controls.rollback_savepoint(third);observe_registry(None)
            expect(family,'caller-work-preserved', [['7']],cells(connection.execute_simple('SELECT value::text FROM caller_sentinel')))
            expect(family,'three-original-attempts-retained',['0','1','2'],[a[0] for a in controls.retained_attempts(producer)])
            expect(family,'three-local-boundaries-settled',['rolled_back']*3,[a[3] for a in controls.retained_attempts(producer)])
            families.append({'family':family,'actualNativeFacts':actual,'originalContextCaptures':captures,'payloadAccountBeforeOwnedFixtureCleanup':list(account.snapshot(producer))})
            supplied.close()
    finally:
        for supplied in owned:supplied.close()
        server.cleanup()
local=[Path(__file__),HERE/'pg8000_original_admission_candidate.py',HERE/'pg8000_original_control_candidate.py',HERE/'pg8000_instance_candidate.py',HERE/'pg8000_accounted_instance_candidate.py']
for path,raw in originals.items():
    if (ROOT/path).read_bytes()!=raw:raise ValueError('Original native source changed during run')
receipt={'scope':'Four actual issued native admission families consume original confirmed controls through one-use shared custody; exact fixture artifacts/actor/epoch/configuration and real native rejection containment, not a protected engine',
 'serverVersion':version,'driverCoreSha256':CORE_SHA,'observations':observations,'families':families,
 'nativeSourcePins':{p:hashlib.sha256(b).hexdigest() for p,b in originals.items()},'sourceSha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in local},
 'installedModuleSha256':{name:hashlib.sha256((Path(__import__('truss').__file__).parent/name).read_bytes()).hexdigest() for name in ['_operation_admission.py','_operation_ordinal.py','_resource_account.py','_accounted_receive.py','_operation_registry.py']},
 'instanceLimits':{'frameBytes':1048576,'totalIngressBytes':33554432,'messages':512,'reads':50000,'writes':512,'outgoingBytes':16777216},
 'driverPortQualified':False,'installerReady':False,'acceptanceCasesPromoted':[],
 'limitations':['Administrative local trust; no ordinary-person R4/R5/security readiness','Six synthetic artifact bytes do not establish artifact meaning, acceptance or mutations','No seven bodies, finalization, commit cohort, journal/feed/receipt or ready publication','No complete allocator/native work or pre-reserved cleanup/containment profile','One original epoch per candidate connection; full reusable driver unqualified','No network loss/cancellation/commit_unknown/reconciliation evidence']}
with destination.open('x') as output:output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'families':len(families),'observations':len(observations),'driverPortQualified':False,'installerReady':False}))
