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
from truss._operation_ordinal import OperationOrdinalIssuer
paths = ['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
         'packages/postgresql/native/issued-operation-admission/operation-admission.sql',
         'packages/python/src/truss/_operation_ordinal.py']
originals = [(root / p).read_bytes() for p in paths]
assert importlib.metadata.version('pgserver') == '0.1.4+truss.pg16.15'
psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'
custody = object()
issuer = OperationOrdinalIssuer(custody)
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
            def admit(issued):
                assert issued.outcome == 'issued'
                send("SELECT json_build_object('writerXid',writer_xid,'ordinal',ordinal) FROM truss.runtime_admit_operation(" +
                     issued.ordinal + ", 'mutation',decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'),decode('05','hex'),decode('06','hex'));" )
                actual = observe()
                assert actual['ordinal'] == issued.ordinal
                return actual
            send('BEGIN;\n' + originals[0].decode() + ';\n' + originals[1].decode() + '\n')
            issued_first = issuer.reserve(custody)
            send('SAVEPOINT operation_probe;')
            first = admit(issued_first)
            send("ROLLBACK TO SAVEPOINT operation_probe; SELECT json_build_object('surviving',count(*)) FROM truss.row_home_operation;")
            assert observe() == {'surviving': 0}
            issued_second = issuer.reserve(custody)
            send('SAVEPOINT operation_second;')
            second = admit(issued_second)
            assert first['writerXid'] == second['writerXid']
            assert [first['ordinal'], second['ordinal']] == ['0', '1']
            send('ROLLBACK;')
            process.stdin.close()
            assert process.wait(timeout=30) == 0
            assert query("SELECT to_regnamespace('truss') IS NULL;") == 't'
    finally:
        issuer.close(custody)
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        server.cleanup()
receipt = {'scope': 'Base admission with actual source Python counter and native savepoint rollback only; synthetic artifact inputs, administrative local-trust fixture, no original driver/security/resource/finalizer qualification',
           'pgserver': importlib.metadata.version('pgserver'), 'serverVersion': version,
           'observations': [first, second], 'rollbackRegistryRows': 0, 'rollbackRemovedNamespace': True,
           'sources': [{'path': p, 'sha256': hashlib.sha256(b).hexdigest()} for p, b in zip(paths, originals)],
           'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'psqlSha256': hashlib.sha256(psql.read_bytes()).hexdigest(),
           'completeDriverQualified': False, 'allFourFamiliesQualified': False, 'readyInstallation': False}
destination = root / 'docs/helix/04-build/evidence/design-audit/issued-operation-ordinal-native.json'
with destination.open('x') as stream:
    stream.write(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'ordinals': ['0', '1'], 'sameNativeTransaction': True, 'readyInstallation': False}))
