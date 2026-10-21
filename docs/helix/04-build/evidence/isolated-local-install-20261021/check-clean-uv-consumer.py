import json, os, pathlib, platform, selectors, signal, subprocess, time, tempfile
import psycopg

repo = pathlib.Path(__file__).resolve().parents[5]
evidence = repo / 'docs/helix/04-build/evidence/isolated-local-install-20261021'
root = pathlib.Path(tempfile.mkdtemp(prefix='truss-one-shot-consumer-', dir='/tmp'))
env = dict(os.environ, TRUSS_PGSERVER_FIND_LINKS=os.environ['TRUSS_PGSERVER_FIND_LINKS'], UV_OFFLINE='1',
           PGSERVICE='nonexistent-host-service', PGHOST='127.0.0.1', PGPORT='1', PGOPTIONS='-c invalid_parameter=on')
env.pop('PYTHONPATH', None)
reports = []
processes = []

def start(name):
    log = (evidence / (name + '.stderr.log')).open('w')
    process = subprocess.Popen([str(repo / 'scripts/truss-local'), '--data-dir', str(root / name), '--install'],
                               cwd=repo, env=env, stdout=subprocess.PIPE, stderr=log, text=True)
    processes.append((process, log))
    return process

def ready(process):
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        if not selector.select(55):
            raise RuntimeError('readiness timeout')
        line = process.stdout.readline()
        if not line:
            raise RuntimeError('launcher exited before readiness; inspect stderr logs')
        return json.loads(line)

def stop(process):
    process.send_signal(signal.SIGTERM)
    if process.wait(timeout=25) != 0:
        raise RuntimeError('launcher shutdown failed')

try:
    first, second = start('first'), start('second')
    original = [ready(first), ready(second)]
    assert original[0]['socketDirectory'] != original[1]['socketDirectory']
    assert all(r['installation']['action'] == 'created' for r in original)
    assert original[0]['installation']['installationId'] != original[1]['installation']['installationId']
    for index, report in enumerate(original):
        with psycopg.connect(report['connectionUri'], options='') as connection:
            connection.execute('CREATE TABLE consumer_probe(value text)')
            connection.execute('INSERT INTO consumer_probe VALUES (%s)', ('instance-' + str(index),))
            assert connection.execute('SHOW listen_addresses').fetchone()[0] == ''
    stop(first)
    with psycopg.connect(original[1]['connectionUri'], options='') as connection:
        assert connection.execute('SELECT value FROM consumer_probe').fetchone()[0] == 'instance-1'
    stop(second)
    restarted = [start('first'), start('second')]
    current = [ready(p) for p in restarted]
    for index, report in enumerate(current):
        assert report['installation']['action'] == 'status_confirmed'
        assert report['installation']['installationId'] == original[index]['installation']['installationId']
        with psycopg.connect(report['connectionUri'], options='') as connection:
            assert connection.execute('SELECT value FROM consumer_probe').fetchone()[0] == 'instance-' + str(index)
    for process in restarted:
        stop(process)
    reports = original + current
    (evidence / 'clean-uv-consumer.json').write_text(json.dumps(dict(passed=True, platform=platform.platform(),
        python=platform.python_version(), offline_cached_dependencies=True, source_checkout=str(repo),
        scope='Clean isolated uv tool environments, simultaneous Unix-only installations, independent writes, SIGTERM, retained restart and installation identities; local macOS only',
        reports=reports, retained_fixture=str(root)), indent=2) + '\n')
    print('PASS: four isolated uv launches; two independent installations and retained data/identities')
finally:
    for process, log in processes:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=25)
        log.close()
