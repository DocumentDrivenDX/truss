#!/usr/bin/env python3
"""Installed test modules on owned socket workers; lifecycle fixtures stay isolated."""
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from native_fixture import WorkerCluster, evidence_directory

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = evidence_directory() / 'python-workers'
DESTINATION.mkdir()
COUNT = int(os.environ.get('TRUSS_INSTALLED_SUITE_WORKERS', '2'))
if not 1 <= COUNT <= 8:
    raise SystemExit('Installed suite workers must be between1 and8')
MODULES = sorted((ROOT / 'packages/python/tests').glob('test_*.py'))
TIMEOUT = int(os.environ.get('TRUSS_INSTALLED_SUITE_TIMEOUT', '1800'))
progress_lock = threading.Lock()

def progress(value):
    with progress_lock:
        with (DESTINATION / 'progress.jsonl').open('a') as output:
            output.write(json.dumps(value) + '\n')
        print(json.dumps(value), flush=True)

def lane(index):
    directory = DESTINATION / str(index)
    directory.mkdir()
    result = {'worker': index, 'modules': [], 'stopped': False}
    worker = WorkerCluster()
    started = time.perf_counter()
    try:
        with worker:
            result['startupSeconds'] = time.perf_counter() - started
            env = {**os.environ, **worker.environment()}
            env.pop('TRUSS_NATIVE_TEST_SOCKET', None)
            env['PYTHONPATH'] = str(ROOT / 'scripts')
            for module in MODULES[index::COUNT]:
                command = [sys.executable, '-W', 'error', str(ROOT / 'scripts/run-python-test-module.py'), 'discover',
                           '-s', str(ROOT / 'packages/python/tests'), '-p', module.name, '-v']
                started = time.perf_counter()
                try:
                    child = subprocess.run(command, cwd=Path(sys.prefix), env=env,
                                           capture_output=True, timeout=TIMEOUT)
                    code, log = child.returncode, child.stdout + child.stderr
                except subprocess.TimeoutExpired as error:
                    code, log = None, (error.stdout or b'') + (error.stderr or b'') + b'\nModule timeout\n'
                restored = False
                try:
                    worker.verify_clean()
                    restored = True
                except Exception as error:
                    log += ('\nWorker cleanup failure: ' + str(error)).encode()
                match = re.search(rb'Ran (\d+) tests? in ', log)
                tests = int(match.group(1)) if match else None
                skips = [{'test': test.decode(), 'reason': reason.decode()} for test, reason in re.findall(rb"^(.+?) \.\.\. skipped '([^']+)'$", log, re.MULTILINE)]
                declared_skips = all(item['reason'] == 'Selected local PostgreSQL build lacks ICU' for item in skips)
                terminal = re.search(rb'\nOK(?: \(skipped=(\d+)\))?\s*$', log)
                skip_count = int(terminal.group(1) or 0) if terminal else None
                passed = code == 0 and restored and tests is not None and terminal is not None and declared_skips and skip_count == len(skips)
                log_path = directory / (module.stem + '.log.gz')
                log_path.write_bytes(gzip.compress(log, mtime=0))
                outcome = {'module': module.name, 'tests': tests, 'returncode': code,
                           'passed': passed, 'baselineRestored': restored,
                           'elapsedSeconds': time.perf_counter() - started,
                           'log': str(log_path.relative_to(ROOT)),
                           'logSha256': hashlib.sha256(log_path.read_bytes()).hexdigest(), 'skippedTests': skips}
                result['modules'].append(outcome)
                progress({'worker': index, **outcome})
                if not passed:
                    break  # Stop and discard the worker after any failed module.
            fixture_log = worker.root / 'fixtures.jsonl'
            result['fixtures'] = [json.loads(line) for line in fixture_log.read_text().splitlines()] if fixture_log.exists() else []
            started = time.perf_counter()
        result['shutdownSeconds'] = time.perf_counter() - started
        result['stopped'] = True
    except Exception as error:
        result['error'] = str(error)
    return result

started = time.perf_counter()
with ThreadPoolExecutor(max_workers=COUNT) as pool:
    workers = list(pool.map(lane, range(COUNT)))
outcomes = [item for worker in workers for item in worker['modules']]
complete = {item['module'] for item in outcomes} == {module.name for module in MODULES}
passed = complete and all(item['passed'] for item in outcomes) and all(worker['stopped'] and 'error' not in worker for worker in workers)
tests = sum(item['tests'] or 0 for item in outcomes)
receipt = {'passed': passed, 'complete': complete, 'tests': tests, 'workers': workers,
           'elapsedSeconds': time.perf_counter() - started,
           'skippedTests': [skip for outcome in outcomes for skip in outcome['skippedTests']],
           'sourceSha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in [Path(__file__), ROOT / 'scripts/native_fixture.py', ROOT / 'scripts/run-python-test-module.py', *MODULES]},
           'expectedModuleCount': len(MODULES), 'postgresqlVersion': '17.11',
           'lifecycleIsolation': 'Direct LocalPostgres and raw startup/shutdown fixtures retain separate owned clusters'}
(DESTINATION / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(f'Ran {tests} tests across installed module workers', file=sys.stderr)
print('OK' if passed else 'FAILED', file=sys.stderr)
raise SystemExit(0 if passed else 1)
