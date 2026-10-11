#!/usr/bin/env python3
"""Record the selected embedded PostgreSQL 17 component qualification lane."""
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import os
import argparse
import re
import time
from concurrent.futures import ThreadPoolExecutor
from native_fixture import WorkerCluster

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/helix/04-build/evidence/design-audit'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('wheel', type=Path)
parser.add_argument('--run-id', required=True)
parser.add_argument('--workers', type=int, default=1)
args = parser.parse_args()
if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', args.run_id) or not 1 <= args.workers <= 8:
    raise SystemExit('Use a fresh run id and one to eight workers')
wheel = args.wheel.resolve()
if importlib.metadata.version('pgserver') != '0.1.4+truss.pg17.11':
    raise SystemExit('Install the pinned PostgreSQL 17.11 wheel first')
EVIDENCE = EVIDENCE / args.run_id
EVIDENCE.mkdir()  # Exclusive run directory; preserves every previous receipt.
destination = EVIDENCE / 'pgserver-pg17.11-qualification.json'
commands = [
    ('installed-suite', ['scripts/check-python-installed-suite.py', str(wheel),
                         '--corrected-pgserver', 'python-pg17.11-installed-suite.json'],
     'python-pg17.11-installed-suite.json'),
    ('cli-signals', ['scripts/check-python-installed-cli-signals.py', '--corrected-pgserver'],
     'python-pg17.11-runtime-cli-signals.json'),
    ('caller-reset', ['scripts/check-pgserver-caller-reset.py', '--require-matches',
                      '--receipt', 'pgserver-pg17.11-caller-reset.json'],
     'pgserver-pg17.11-caller-reset.json'),
    ('isolation', ['scripts/check-corrected-pgserver-isolation.py'], 'pgserver-pg17.11-isolation.json'),
    ('origin', ['scripts/check-corrected-pgserver-origin.py'], 'pgserver-pg17.11-origin.json'),
    ('structure', ['scripts/check-pgserver-umf-structure.py', '--corrected-pgserver'],
     'pgserver-pg17.11-umf-structural-correspondence.json'),
    ('populated-guards', ['scripts/check-pgserver-populated-guards.py', '--corrected-pgserver'],
     'pgserver-pg17.11-populated-guard-component.json'),
    ('transaction-timeout', ['scripts/check-pg17-transaction-timeout.py'],
     'pgserver-pg17.11-transaction-timeout.json'),
]
for family in ('base', 'asserted', 'epoch', 'configuration'):
    receipt = f'pgserver-pg17.11-issued-{family}-native.json'
    commands.append(('issued-' + family,
                     ['scripts/check-issued-operation-ordinal.py', family, receipt], receipt))
for label, producer in [('four-family-driver', 'check_pg8000_four_family_admission_native.py'),
                        ('private-callable-inventory', 'check_private_callable_inventory_native.py'),
                        ('elevation', 'check_four_family_elevation_native.py')]:
    receipt = f'pgserver-pg17.11-{label}-native.json'
    commands.append((label, [str((ROOT / 'docs/helix/04-build/evidence/design-audit' / producer).relative_to(ROOT)), receipt], receipt))
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
inputs = {arguments[0]: digest(ROOT / arguments[0]) for _, arguments, _ in commands}
inputs['scripts/native_fixture.py'] = digest(ROOT / 'scripts/native_fixture.py')
worker_results = []
base_environment = os.environ.copy()
base_environment.pop('TRUSS_NATIVE_WORKER', None)
base_environment['TRUSS_NATIVE_EVIDENCE_DIR'] = str(EVIDENCE)
base_environment['PYTHONPATH'] = str(ROOT / 'scripts')

def execute(case, environment, worker=None):
    label, arguments, receipt_name = case
    print('Running ' + label, flush=True)
    command = [sys.executable, *arguments]
    started = time.perf_counter()
    try:
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=(int(environment.get('TRUSS_INSTALLED_SUITE_TIMEOUT', '600')) + 30 if label == 'installed-suite' else 240))
        code, log = result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as error:
        code, log = None, (error.stdout or b'') + (error.stderr or b'') + b'\nQualification timeout\n'
    cleanup = True
    if worker is not None:
        try:
            worker.verify_clean()
        except Exception as error:
            cleanup = False
            log += ('\nWorker cleanup failure: ' + str(error)).encode()
    log_path = EVIDENCE / f'pgserver-pg17.11-{label}.log.gz'
    with log_path.open('xb') as output:
        output.write(gzip.compress(log, mtime=0))
    receipt_path = EVIDENCE / receipt_name
    outcome = {'case': label, 'command': command, 'returncode': code,
               'passed': code == 0 and receipt_path.is_file() and cleanup,
               'elapsedSeconds': time.perf_counter() - started,
               'lane': 'isolated-lifecycle' if worker is None else 'shared-worker',
               'workerBaselineRestored': cleanup if worker is not None else None,
               'producerSha256': inputs[arguments[0]],
               'log': str(log_path.relative_to(ROOT)), 'logSha256': digest(log_path)}
    if receipt_path.is_file():
        outcome.update(receipt=str(receipt_path.relative_to(ROOT)), receiptSha256=digest(receipt_path))
    print(json.dumps({'case': label, 'passed': outcome['passed'], 'returncode': code}), flush=True)
    return outcome

isolated = {'installed-suite', 'cli-signals', 'transaction-timeout'}
outcomes = [execute(case, base_environment) for case in commands if case[0] in isolated]
shared = [case for case in commands if case[0] not in isolated]

def run_worker(index):
    result = {'worker': index, 'outcomes': [], 'stopped': False}
    worker = WorkerCluster()
    started = time.perf_counter()
    try:
        with worker:
            result.update(readySeconds=time.perf_counter() - started, settings=worker.settings,
                          uri=worker.uri, postmasterPid=worker.server.get_pid())
            environment = {**base_environment, **worker.environment()}
            for case in shared[index::args.workers]:
                outcome = execute(case, environment, worker)
                result['outcomes'].append(outcome)
                if not outcome['passed']:
                    break  # Discard this worker on any test or cleanup failure.
            events = worker.root / 'fixtures.jsonl'
            result['fixtures'] = [json.loads(line) for line in events.read_text().splitlines()] if events.exists() else []
        result['stopped'] = True
    except Exception as error:
        result['error'] = str(error)
    return result

with ThreadPoolExecutor(max_workers=args.workers) as pool:
    worker_results = list(pool.map(run_worker, range(args.workers)))
for worker_result in worker_results:
    outcomes.extend(worker_result['outcomes'])
unchanged = all(digest(ROOT / path) == sha for path, sha in inputs.items())
complete = len(outcomes) == len(commands)
receipt = {'scope': 'Shared owned Unix-socket workers with fresh database/role fixtures; isolated lifecycle checks; selected local PostgreSQL17.11 components only',
           'pgserver': importlib.metadata.version('pgserver'), 'postgresqlVersion': '17.11',
           'python': sys.version, 'trussWheelSha256': digest(wheel), 'outcomes': outcomes,
           'workers': worker_results, 'expectedCaseCount': len(commands),
           'producerInputsUnchanged': unchanged,
           'passed': complete and unchanged and all(item['passed'] for item in outcomes)
                     and all(item['stopped'] and 'error' not in item for item in worker_results),
           'producerSha256': digest(Path(__file__)), 'fixtureSha256': inputs['scripts/native_fixture.py'],
           'completeRuntimeQualified': False, 'lakebaseQualified': False, 'published': False}
with destination.open('x') as output:
    output.write(json.dumps(receipt, indent=2) + '\n')
raise SystemExit(0 if receipt['passed'] else 1)
