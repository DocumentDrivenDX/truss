"""Verify v0.0.47 package-only quickstart away from the source checkout."""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import shlex
import signal
import subprocess
import sys
import tempfile

import psycopg

repository = Path(__file__).resolve().parents[5]
evidence = Path(__file__).resolve().parent / 'published-0.0.47'
evidence.mkdir(exist_ok=True)
assets = Path(sys.argv[1]).resolve()
checksums = dict(line.split(maxsplit=1)[::-1] for line in (assets / 'SHA256SUMS').read_text().splitlines())
for name, digest in checksums.items():
    assert hashlib.sha256((assets / name).read_bytes()).hexdigest() == digest, name
pins = json.loads((assets / 'release-pins.json').read_text())
assert pins['version'] == '0.0.47'
assert pins['localRuntimeConstraintsSha256'] == checksums['isolated-runtime-constraints.txt']
command = re.search(r'```sh\n(.*?)\n```', (repository / 'README.md').read_text(), re.S).group(1)
arguments = shlex.split(command.replace('\\\n', ''))
assert arguments[arguments.index('--from') + 1] == 'truss-toolkit[local,native]==0.0.47'
fixture = Path(tempfile.mkdtemp(prefix='truss-published-uvx-', dir='/tmp'))
environment = dict(os.environ)
environment.pop('PYTHONPATH', None)
environment.pop('PYTHONHOME', None)
processes = []

def start(name):
    selected = arguments.copy()
    selected[selected.index('--data-dir') + 1] = str(fixture / name)
    log = (evidence / (name + '.stderr.log')).open('a')
    process = subprocess.Popen(selected, cwd=fixture, env=environment,
                               stdout=subprocess.PIPE, stderr=log, text=True)
    processes.append((process, log))
    return process

def ready(process):
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        if not selector.select(60):
            raise RuntimeError('No launcher readiness; inspect retained logs')
        line = process.stdout.readline()
    if not line:
        raise RuntimeError('Launcher exited; inspect retained logs')
    return json.loads(line)

def stop(process):
    process.send_signal(signal.SIGTERM)
    assert process.wait(timeout=75) == 0

try:
    first, second = start('first'), start('second')
    original = [ready(first), ready(second)]
    assert original[0]['socketDirectory'] != original[1]['socketDirectory']
    assert original[0]['installation']['installationId'] != original[1]['installation']['installationId']
    assert all(report['installation']['action'] == 'created' for report in original)
    for index, report in enumerate(original):
        with psycopg.connect(report['connectionUri']) as connection:
            assert connection.execute('SHOW listen_addresses').fetchone()[0] == ''
            connection.execute('CREATE TABLE published_probe(value text)')
            connection.execute('INSERT INTO published_probe VALUES (%s)', ('instance-' + str(index),))
    stop(first)
    with psycopg.connect(original[1]['connectionUri']) as connection:
        assert connection.execute('SELECT value FROM published_probe').fetchone()[0] == 'instance-1'
    stop(second)
    restarted_processes = [start('first'), start('second')]
    restarted = [ready(process) for process in restarted_processes]
    for index, report in enumerate(restarted):
        assert report['installation']['action'] == 'status_confirmed'
        assert report['installation']['installationId'] == original[index]['installation']['installationId']
        with psycopg.connect(report['connectionUri']) as connection:
            assert connection.execute('SELECT value FROM published_probe').fetchone()[0] == 'instance-' + str(index)
    for process in restarted_processes:
        stop(process)
    prefix = arguments[:arguments.index('truss-local-postgres')]
    observed = subprocess.run(prefix + ['python', '-c',
        'import json,sys,truss,importlib.metadata as m; print(json.dumps(dict(python=sys.version,version=m.version("truss-toolkit"),loaded=truss.__file__)))'],
        cwd=fixture, env=environment, check=True, capture_output=True, text=True, timeout=90)
    loaded = json.loads(observed.stdout)
    assert loaded['version'] == '0.0.47'
    assert not Path(loaded['loaded']).resolve().is_relative_to(repository)
    (evidence / 'receipt.json').write_text(json.dumps(dict(passed=True, platform=platform.platform(),
        sourceCheckoutRequired=False, workingDirectory=str(fixture), command=arguments,
        package=loaded, original=original, restarted=restarted, releasePins=pins,
        verifiedAssets=checksums), indent=2) + '\n')
    print('PASS: published package-only uvx; two independent instances; retained data and installation identities')
finally:
    cleanup_errors = []
    for process, log in processes:
        try:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=75)
        except Exception as error:
            cleanup_errors.append(f'Owned launcher {process.pid}: {error!r}')
        finally:
            log.close()
    if cleanup_errors:
        raise RuntimeError('Unconfirmed cleanup; retain ' + str(fixture) + ': ' + '; '.join(cleanup_errors))
