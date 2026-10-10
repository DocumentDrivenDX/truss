#!/usr/bin/env python3
"""Real Python issuance/native rollback component; not a qualified driver port."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import pgserver

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'packages/python/src'))
from truss._operation_ordinal import OperationOrdinalRegistry
from truss._operation_registry import COLUMNS, decode_operation_registry
family = sys.argv[1] if len(sys.argv) >= 2 else 'base'
assert len(sys.argv) <= 3
receipt_name = sys.argv[2] if len(sys.argv) == 3 else 'issued-operation-ordinal-' + family + '-native.json'
assert Path(receipt_name).name == receipt_name and receipt_name.endswith('.json')
destination = root / 'docs/helix/04-build/evidence/design-audit' / receipt_name
if destination.exists():
    raise SystemExit('refusing to replace an existing receipt')
configurations = []
decoded_registries = []
assert family in ('base', 'asserted', 'epoch', 'configuration')
filename = {'base':'operation-admission.sql','asserted':'operation-asserted-origin-admission.sql','epoch':'operation-epoch-context-admission.sql','configuration':'operation-configuration-context-admission.sql'}[family]
function = {'base':'runtime_admit_operation','asserted':'runtime_admit_operation_with_asserted_origin','epoch':'runtime_admit_operation_with_epoch_context','configuration':'runtime_admit_operation_with_configuration_context'}[family]
paths = ['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
         'packages/postgresql/native/issued-operation-admission/' + filename,
         'packages/python/src/truss/_operation_ordinal.py',
         'packages/python/src/truss/_operation_registry.py',
         'docs/helix/02-design/contracts/row-operation-registry-observation-v0.1.proposal.sql']

extras = []
if family in ('epoch', 'configuration'):
    extras.append('packages/postgresql/native/source-epoch-lock.sql')
    if family == 'configuration':
        extras.append('docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql')
    extras.append('docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql')
paths += extras

originals = [(root / p).read_bytes() for p in paths]
assert importlib.metadata.version('pgserver') == '0.1.4+truss.pg16.15'
psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'
custody = object()
producer = object()
issuer = None
with tempfile.TemporaryDirectory(prefix='truss-issued-ordinal-') as directory:
    server = pgserver.get_server(Path(directory) / 'data', cleanup_mode='stop')
    def query(sql):
        return subprocess.check_output([str(psql), server.get_uri(), '-X', '-qAt', '-v', 'ON_ERROR_STOP=1'],
                                       input=sql, text=True, timeout=30).strip()
    process = None
    try:
        version = query('SHOW server_version;')
        assert version.startswith('16.15')
        with tempfile.TemporaryFile(mode='w+t') as errors:
            process = subprocess.Popen([str(psql), server.get_uri(), '-X', '-qAt', '-v', 'ON_ERROR_STOP=1'],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, text=True)
            registry = OperationOrdinalRegistry(producer, process, 1, 9223372036854775807)
            issuer = registry.bind(producer, process, custody)
            def send(sql):
                process.stdin.write(sql + '\n')
                process.stdin.flush()
            def observe():
                if not select.select([process.stdout], [], [], 30)[0]:
                    raise RuntimeError('bounded fixture observation unavailable')
                line = process.stdout.readline()
                if not line:
                    errors.seek(0)
                    raise RuntimeError(errors.read())
                return json.loads(line)
            projection = originals[4].decode().split('SELECT\n', 1)[1].split(';', 1)[0]
            registry_observation_sql = (
                "SELECT json_build_object('xid',pg_current_xact_id_if_assigned()::text,'rows',"
                "COALESCE((SELECT json_agg(json_build_array(" +
                ','.join('r.' + name for name in COLUMNS) +
                ")) FROM (SELECT\n" + projection + ") r),'[]'::json));")
            def decode_current_registry(label, expected_ordinals):
                send(registry_observation_sql)
                raw = observe()
                rows = decode_operation_registry(raw['xid'], COLUMNS, raw['rows'],
                    'SELECT', str(len(raw['rows'])), 8, 65536)
                assert sorted(row[1] for row in rows) == expected_ordinals
                assert all(row[0] == raw['xid'] and row[2:5] == ('mutation','admitted','0') for row in rows)
                decoded_registries.append({'boundary': label, 'actualXid': raw['xid'],
                    'originalRows': raw['rows'], 'decodedRows': [list(row) for row in rows]})
            tail = ''
            if family != 'base':
                tail += ",convert_to('original asserted fixture','UTF8'),convert_to('original capture profile fixture','UTF8')"
            if family in ('epoch', 'configuration'):
                tail += ",'guard-fixture','guard-fixture-epoch','guard-fixture-incarnation'"
            if family == 'configuration':
                tail += ",convert_to('configuration admission fixture','UTF8')"
            def admit(issued):
                assert issued.outcome == 'issued'
                send("SELECT json_build_object('writerXid',writer_xid,'ordinal',ordinal,'contextHex',context_hex,'context',convert_from(decode(context_hex,'hex'),'UTF8')::jsonb) FROM truss." + function + "(" +
                     issued.ordinal + ", 'mutation',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex')" + tail + ");" )
                actual = observe()
                assert actual['ordinal'] == issued.ordinal
                if family == 'configuration':
                    send("SELECT json_build_object('ordinal',operation_ordinal::text,'configurationGeneration',configuration_generation::text,'keyReuse',key_reuse,'journalMode',journal_mode,'contextDigest',encode(original_context_sha256,'hex'),'profileHex',encode(admission_profile_bytes,'hex'),'configurationHex',encode(configuration_bytes,'hex'),'bindingHex',encode(selected_binding_bytes,'hex'),'inventoryHex',encode(installed_inventory_bytes,'hex')) FROM truss.operation_configuration;")
                    configuration = observe()
                    assert configuration['ordinal'] == issued.ordinal
                    assert configuration['configurationGeneration'] == '7'
                    assert configuration['keyReuse'] == 'forbid' and configuration['journalMode'] == 'engine'
                    for key, expected in [('profileHex', b'configuration admission fixture'),
                                          ('configurationHex', bytes.fromhex('0001ff')),
                                          ('bindingHex', b'binding fixture'), ('inventoryHex', b'inventory fixture')]:
                        assert bytes.fromhex(configuration[key]) == expected
                    assert configuration['contextDigest'] == hashlib.sha256(bytes.fromhex(actual['contextHex'])).hexdigest()
                    configurations.append(configuration)
                return actual
            setup = originals[0].decode() + ';\n'
            for path in extras:
                if path.endswith('pgserver-populated-guard-fixture.sql'):
                    setup += (root / path).read_text().split('INSERT INTO truss.row_home_operation')[0]
                else:
                    setup += (root / path).read_text() + ';\n'
            if family in ('epoch', 'configuration'):
                setup += "INSERT INTO truss.source_epoch_current VALUES (1,'guard-fixture','guard-fixture-epoch');"
            if family == 'configuration':
                setup += "INSERT INTO truss.installation_admission (head_id,installation_id_utf8,source_epoch_utf8,configuration_generation,key_reuse,journal_mode,configuration_bytes,selected_binding_bytes,installed_inventory_bytes) VALUES (1,convert_to('guard-fixture','UTF8'),convert_to('guard-fixture-epoch','UTF8'),7,'forbid','engine',decode('0001ff','hex'),convert_to('binding fixture','UTF8'),convert_to('inventory fixture','UTF8'));"
            send('BEGIN;\n' + setup + ';\n' + originals[1].decode() + '\n')
            issued_first = issuer.reserve(custody)
            send('SAVEPOINT operation_probe;')
            first = admit(issued_first)
            decode_current_registry('first-admission', ['0'])
            snapshot_sql = "SELECT json_build_object('registry',(SELECT jsonb_agg(to_jsonb(o) ORDER BY operation_ordinal) FROM truss.row_home_operation o)"
            if family == 'configuration':
                snapshot_sql += ",'configuration',(SELECT jsonb_agg(to_jsonb(c) ORDER BY operation_ordinal) FROM truss.operation_configuration c)"
            snapshot_sql += ");"
            send(snapshot_sql)
            before_refusals = observe()
            native_controls = []
            for value, state, message in [('NULL', '22023', 'invalid host-issued operation ordinal'),
                                           ('-1', '22023', 'invalid host-issued operation ordinal'),
                                           ('0', '55000', 'unfinished operation'),
                                           ('9', '55000', 'unfinished operation')]:
                probe = "PERFORM * FROM truss." + function + "(" + value + ", 'mutation',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex')" + tail + ");"
                send("DO $$ BEGIN " + probe + " RAISE EXCEPTION 'expected native refusal'; EXCEPTION WHEN SQLSTATE '" + state + "' THEN IF SQLERRM <> '" + message + "' THEN RAISE; END IF; END $$; " + snapshot_sql)
                after_refusal = observe()
                assert after_refusal == before_refusals
                native_controls.append({'ordinalInput': value, 'sqlstate': state, 'message': message,
                                        'completeObservedStoresUnchanged': True})
            send("ROLLBACK TO SAVEPOINT operation_probe; SELECT json_build_object('surviving',count(*)) FROM truss.row_home_operation;")
            assert observe() == {'surviving': 0}
            decode_current_registry('first-savepoint-rollback', [])
            if family == 'configuration':
                send("SELECT json_build_object('survivingConfigurations',count(*)) FROM truss.operation_configuration;")
                assert observe() == {'survivingConfigurations': 0}
            second_facade_issuer = registry.bind(producer, process, custody)
            assert second_facade_issuer is issuer
            issued_second = second_facade_issuer.reserve(custody)
            send('SAVEPOINT operation_second;')
            second = admit(issued_second)
            decode_current_registry('second-admission', ['1'])
            assert first['writerXid'] == second['writerXid']
            assert [first['ordinal'], second['ordinal']] == ['0', '1']
            for observation in (first, second):
                context = observation['context']
                assert context['xid'] == observation['writerXid'] and context['ordinal'] == observation['ordinal']
                if family != 'base':
                    assert bytes.fromhex(context['assertedOriginUtf8Hex']) == b'original asserted fixture'
                    assert bytes.fromhex(context['assertedOriginCaptureProfileHex']) == b'original capture profile fixture'
                if family in ('epoch', 'configuration'):
                    assert context['installationId'] == 'guard-fixture' and context['sourceEpoch'] == 'guard-fixture-epoch'
                    assert context['targetIncarnation'] == 'guard-fixture-incarnation'
                    assert bytes.fromhex(context['sourceEpochProfileHex']) == b'fixture-profile'
                    assert bytes.fromhex(context['sourceEpochEvidenceHex']) == b'fixture-evidence'

            failed_issued = issuer.reserve(custody)
            assert failed_issued.ordinal == '2'
            send('SAVEPOINT refused_attempt;')
            refusal_call = "PERFORM * FROM truss." + function + "(" + failed_issued.ordinal + ", 'invalid-kind',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex')" + tail + ");"
            send("DO $$ BEGIN " + refusal_call + " RAISE EXCEPTION 'expected invalid-kind refusal'; EXCEPTION WHEN SQLSTATE '22023' THEN NULL; END $$; SELECT json_build_object('surviving',count(*),'ordinal',min(operation_ordinal)::text) FROM truss.row_home_operation;")
            assert observe() == {'surviving': 1, 'ordinal': '1'}
            send("ROLLBACK TO SAVEPOINT operation_second; SELECT json_build_object('surviving',count(*)) FROM truss.row_home_operation;")
            assert observe() == {'surviving': 0}
            decode_current_registry('second-savepoint-rollback', [])
            issued_third = issuer.reserve(custody)
            assert issued_third.ordinal == '3'
            send('SAVEPOINT operation_third;')
            third = admit(issued_third)
            decode_current_registry('third-admission', ['3'])
            assert third['writerXid'] == first['writerXid']
            assert third['ordinal'] == '3'
            send('ROLLBACK;')
            process.stdin.close()
            assert process.wait(timeout=30) == 0
            assert query("SELECT to_regnamespace('truss') IS NULL;") == 't'
    finally:
        if issuer is not None:
            registry.close(producer)
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        server.cleanup()
receipt = {'scope': 'Selected admission family with actual source Python counter and native savepoint rollback only; synthetic artifact inputs, administrative local-trust fixture, no original driver/security/resource/finalizer qualification',
           'registryDecoderObservations': decoded_registries,
           'registryObservationSql': registry_observation_sql,
           'nativeInputControls': native_controls, 'originalSurvivingSnapshot': before_refusals,
           'family': family, 'pgserver': importlib.metadata.version('pgserver'), 'serverVersion': version,
           'observations': [first, second, third], 'refusedIssuedOrdinal': '2', 'nativeRefusalSqlstate': '22023', 'configurationObservations': configurations, 'rollbackRegistryRows': 0, 'rollbackRemovedNamespace': True,
           'sources': [{'path': p, 'sha256': hashlib.sha256(b).hexdigest()} for p, b in zip(paths, originals)],
           'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'psqlSha256': hashlib.sha256(psql.read_bytes()).hexdigest(),
           'completeDriverQualified': False, 'allFourFamiliesQualified': False, 'readyInstallation': False}
with destination.open('x') as stream:
    stream.write(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'family': family, 'ordinals': ['0', '1', '3'], 'sameNativeTransaction': True, 'readyInstallation': False}))
