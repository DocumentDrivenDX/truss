#!/usr/bin/env python3
"""Focused installed-wheel consumer checks; not the full Truss semantic corpus."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import zipfile
import pgserver
import truss
from psycopg import pq
from native_fixture import WorkerCluster
from truss._runtime_profile import RUNTIME_DISTRIBUTION, RUNTIME_VERSION, SERVER_VERSION

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('runtime_wheel', type=Path)
parser.add_argument('truss_wheel', type=Path)
parser.add_argument('--run-id', required=True)
args = parser.parse_args()
if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', args.run_id):
    raise SystemExit('Supply a fresh run id')
destination = ROOT / 'docs/helix/04-build/evidence/design-audit' / args.run_id
destination.mkdir()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

payloads = {}
for wheel, package in [(args.runtime_wheel, pgserver), (args.truss_wheel, truss)]:
    loaded = Path(package.__file__).resolve().parent
    if loaded.is_relative_to(ROOT / 'packages'):
        raise RuntimeError('Smoke checks must load installed wheel packages')
    with zipfile.ZipFile(wheel) as archive:
        members = [name for name in archive.namelist() if name.startswith(package.__name__ + '/') and not name.endswith('/')]
        for name in members:
            local = loaded.parent / name
            if not local.is_file() or local.read_bytes() != archive.read(name):
                raise RuntimeError('Installed wheel payload mismatch: ' + name)
        payloads[package.__name__] = {'wheelSha256': digest(wheel), 'members': len(members), 'loaded': str(loaded)}
if importlib.metadata.version(RUNTIME_DISTRIBUTION) != RUNTIME_VERSION:
    raise RuntimeError('Selected runtime distribution mismatch')
version = subprocess.check_output([str(Path(pgserver.__file__).parent / 'pginstall/bin/postgres'), '--version'], text=True).strip()
if version != 'postgres (PostgreSQL) ' + SERVER_VERSION:
    raise RuntimeError('Selected native server mismatch')
env = {**os.environ, 'PYTHONPATH': os.pathsep.join([str(ROOT / 'scripts'), str(ROOT / 'packages/python/tests')]),
       'TRUSS_NATIVE_EVIDENCE_DIR': str(destination),
       'TRUSS_CENSUS_POSTGRES_BIN': str(Path(pgserver.__file__).parent / 'pginstall/bin')}
env.pop('TRUSS_NATIVE_WORKER', None)
outcomes = []
started = time.perf_counter()

def execute(name, arguments, environment=env):
    begin = time.perf_counter()
    result = subprocess.run([sys.executable, *arguments], env=environment, cwd=sys.prefix, capture_output=True, timeout=120)
    log = destination / (name + '.log')
    log.write_bytes(result.stdout + result.stderr)
    outcome = {'case': name, 'passed': result.returncode == 0, 'returncode': result.returncode,
               'elapsedSeconds': time.perf_counter() - begin, 'log': log.name, 'logSha256': digest(log)}
    outcomes.append(outcome)
    print(json.dumps(outcome), flush=True)
    if result.returncode:
        raise RuntimeError(name + ' failed; see ' + str(log))

execute('owned-lifecycle', [str(ROOT / 'scripts/run-python-test-module.py'), 'test_local_runtime', '-v'])
with WorkerCluster() as worker:
    execute('supported-driver', [str(ROOT / 'scripts/run-python-test-module.py'), 'test_psycopg_host_native', '-v'], {**env, **worker.environment()})
    worker.verify_clean()
execute('worker-cleanup-collisions', [str(ROOT / 'scripts/check-native-worker-fixtures.py'), 'worker-controls.json'])
execute('module-interruption', [str(ROOT / 'scripts/check-native-module-interruption.py'), 'module-interruption.json'])
execute('cli-signals', [str(ROOT / 'scripts/check-python-installed-cli-signals.py')])
execute('transaction-timeout', [str(ROOT / 'scripts/check-pg17-transaction-timeout.py')])
inputs = [Path(__file__), ROOT / 'scripts/native_fixture.py', ROOT / 'scripts/run-python-test-module.py',
          ROOT / 'scripts/check-native-worker-fixtures.py', ROOT / 'scripts/check-native-module-interruption.py',
          ROOT / 'scripts/check-python-installed-cli-signals.py', ROOT / 'scripts/check-pg17-transaction-timeout.py',
          ROOT / 'packages/python/tests/test_local_runtime.py', ROOT / 'packages/python/tests/test_psycopg_host_native.py']
receipt = {'passed': True, 'scope': 'Focused installed consumer, supported-driver adoption, retained restart, isolated lifecycle, shared fresh database/role cleanup, Unix socket/TCP collision, signals and transaction timeout; no full engine or Lakebase acceptance',
           'runtimeDistribution': RUNTIME_DISTRIBUTION, 'runtimeVersion': RUNTIME_VERSION, 'postgresql': SERVER_VERSION,
           'python': sys.version, 'platform': platform.platform(), 'libpq': pq.version(), 'payloads': payloads,
           'outcomes': outcomes, 'elapsedSeconds': time.perf_counter() - started,
           'sourceSha256': {str(path.relative_to(ROOT)): digest(path) for path in inputs},
           'completeRuntimeQualified': False, 'lakebaseQualified': False}
(destination / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
