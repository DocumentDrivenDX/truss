"""Original capacity ledger/exclusion observation; not reservation or installation."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlparse, parse_qs
import pg8000.native
import pgserver

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):
    raise SystemExit('Supply fresh receipt basename')
destination=HERE/sys.argv[1]
if destination.exists():raise SystemExit('Receipt already exists')
if importlib.metadata.version('pgserver')!='0.1.4+truss.pg16.15' or importlib.metadata.version('pg8000')!='1.31.5':
    raise SystemExit('Original selected local runtime/driver required')
paths=['docs/helix/02-design/contracts/row-home-capacity-v0.1.proposal.sql',
 'docs/helix/02-design/contracts/row-home-capacity-initialization-v0.1.proposal.sql',
 'docs/helix/02-design/contracts/bindings/truss-row-touch-retention-resource-v0.1.proposal.json',
 'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
 'docs/helix/02-design/contracts/CONTRACT-009-group-planning-and-locks.md']
originals={p:(ROOT/p).read_bytes() for p in paths}
observations=[]
def expect(name,expected,observed):
    if expected!=observed:raise ValueError(name+': native expectation mismatch')
    observations.append({'id':name,'expected':expected,'observed':observed})
with tempfile.TemporaryDirectory(prefix='truss-capacity-ledger-') as directory:
    server=pgserver.get_server(Path(directory)/'data',cleanup_mode='stop')
    connections=[]
    try:
        uri=urlparse(server.get_uri());options=parse_qs(uri.query)
        host=options.get('host',[uri.hostname])[0];port=int(options.get('port',[uri.port or 5432])[0])
        def connect():
            value=pg8000.native.Connection(user='postgres',database='postgres',unix_sock=str(Path(host)/f'.s.PGSQL.{port}'),ssl_context=False,timeout=5)
            connections.append(value);return value
        owner=connect(); contender=connect()
        version=owner.run('SHOW server_version')[0][0]
        if not version.startswith('16.15'):raise ValueError('Actual native version differs')
        owner.run('CREATE SCHEMA truss')
        owner.run(originals[paths[0]].decode('utf8'))
        # Parameterized original fresh initialization, using full original bytes.
        # The isolated ledger does not prove installation/admitted touch emptiness.
        initialization=originals[paths[1]].decode('utf8').replace('$1::bytea',':layout').replace('$2::bytea',':profile')
        initial=owner.run(initialization,layout=originals[paths[3]],profile=originals[paths[2]])
        expect('original-full-byte-initialization', [1,0,0,0,0,originals[paths[3]].hex(),originals[paths[2]].hex()],
               [*initial[0][:5],initial[0][5].hex(),initial[0][6].hex()])
        owner.run('BEGIN')
        owner.run('SAVEPOINT held_before_child')
        expect('original-owner-singleton-lock',[[1]],owner.run('SELECT singleton_id FROM truss.row_home_capacity WHERE singleton_id=1 FOR UPDATE'))
        owner.run('SAVEPOINT child')
        owner.run('ROLLBACK TO SAVEPOINT child')
        contender.run('BEGIN')
        contender.run("SET LOCAL lock_timeout='250ms'")
        contender.run("SET LOCAL statement_timeout='2s'")
        contender.run('SAVEPOINT refusal')
        try:contender.run('SELECT singleton_id FROM truss.row_home_capacity WHERE singleton_id=1 FOR UPDATE')
        except pg8000.exceptions.DatabaseError as error:
            expect('bounded-original-lock-refusal','55P03',error.args[0]['C'])
        else:raise ValueError('Original owner lock did not exclude contender')
        contender.run('ROLLBACK TO SAVEPOINT refusal')
        expect('contender-restored-without-retry',[[0,0,0,0]],contender.run('SELECT retained_rows,retained_custody_bytes,reserved_rows,reserved_custody_bytes FROM truss.row_home_capacity'))
        owner.run('ROLLBACK')
        expect('host-rollback-releases-ledger',[[1]],contender.run('SELECT singleton_id FROM truss.row_home_capacity WHERE singleton_id=1 FOR UPDATE'))
        contender.run('ROLLBACK')
        actual=owner.run('SELECT singleton_id,retained_rows,retained_custody_bytes,reserved_rows,reserved_custody_bytes,original_layout_bytes,original_resource_profile_bytes FROM truss.row_home_capacity')
        expect('complete-original-ledger-unchanged',[*initial[0][:5],initial[0][5].hex(),initial[0][6].hex()],
               [*actual[0][:5],actual[0][5].hex(),actual[0][6].hex()])
    finally:
        for connection in connections:
            connection.close()
        server.cleanup()
for path,raw in originals.items():
    if (ROOT/path).read_bytes()!=raw:raise ValueError('Original source changed during execution')
receipt={'scope':'Original native singleton ledger full-byte fresh initialization and transaction exclusion across child rollback; no reservation procedure or protected installation',
 'serverVersion':version,'observations':observations,'sourceSha256':{p:hashlib.sha256(b).hexdigest() for p,b in originals.items()},
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'nativeReservationQualified':False,'installerReady':False,
 'acceptanceCasesPromoted':[], 'limitations':['Administrative isolated ledger only; no protected installer freshness proof or ordinary roles','No reservation registry, operation attribution, consumption, finalization or counter settlement','No host account, cancellation, complete work/dependency or full concurrent-writer throughput qualification','Lock timeout bounds this statement wait; host transaction lifetime remains host-owned']}
with destination.open('x') as output:output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'observations':len(observations),'nativeReservationQualified':False,'installerReady':False}))
