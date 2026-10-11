#!/usr/bin/env python3
"""Native controls for socket collision isolation and fixture cleanup."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import os
import sys
import tempfile
from unittest.mock import patch

import pg8000.exceptions
from native_fixture import WorkerCluster, DatabaseFixture, connect, evidence_directory

if len(sys.argv) != 2 or Path(sys.argv[1]).name != sys.argv[1]:
    raise SystemExit('Supply a fresh receipt basename')
destination = evidence_directory() / sys.argv[1]
if destination.exists():
    raise SystemExit('Receipt exists')
checks = []

def expect(name, expected, observed):
    if expected != observed:
        raise AssertionError((name, expected, observed))
    checks.append({'case': name, 'expected': expected, 'observed': observed})

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    try:
        listener.bind(('127.0.0.1', 5432))
        listener.listen()
        tcp_occupied = 'owned-test-listener'
    except OSError:
        listener.close()
        tcp_occupied = 'already-occupied'
    workers = []
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(WorkerCluster().__enter__) for _ in range(2)]
            # Retain every successfully started worker even if another fails.
            errors = []
            for future in futures:
                try:
                    workers.append(future.result())
                except Exception as error:
                    errors.append(str(error))
            if errors:
                raise RuntimeError(errors)
        expect('two-workers-start-with-tcp5432-occupied', 2, len(workers))
        expect('distinct-worker-socket-directories', 2,
               len({worker.settings['unix_socket_directories'] for worker in workers}))
        expect('tcp-listening-disabled', ['', ''], [worker.settings['listen_addresses'] for worker in workers])
        first, second = [DatabaseFixture(worker.root) for worker in workers]
        try:
            DatabaseFixture(workers[0].root)
        except RuntimeError as error:
            expect('same-worker-overlap-refuses', True, 'already leased' in str(error))
        else:
            raise AssertionError('Overlapping fixture admitted')
        a, b = connect(first.get_uri()), connect(second.get_uri())
        try:
            a.run('CREATE TABLE fixture_marker(value text)')
            a.run('INSERT INTO fixture_marker VALUES (:value)', value='worker-a')
            b.run('CREATE TABLE fixture_marker(value text)')
            b.run('INSERT INTO fixture_marker VALUES (:value)', value='worker-b')
            a.run('CREATE ROLE fixture_actor NOLOGIN')
            b.run('CREATE ROLE fixture_actor NOLOGIN')
            expect('same-table-names-isolated', [['worker-a']], a.run('SELECT value FROM fixture_marker'))
            expect('other-worker-content-isolated', [['worker-b']], b.run('SELECT value FROM fixture_marker'))
            expect('fresh-owner-roles-distinct', True, first.role != second.role)
            a.run('BEGIN')
            first.cleanup()  # Deliberately leave an active fixture session open.
            try:
                a.run('SELECT 1')
            except (pg8000.exceptions.InterfaceError, pg8000.exceptions.DatabaseError):
                terminated = True
            else:
                terminated = False
            expect('leaked-fixture-session-terminated', True, terminated)
            expect('other-worker-session-survives-cleanup', [[1]], b.run('SELECT 1'))
        finally:
            try:
                a.close()
            except pg8000.exceptions.InterfaceError:
                # pg8000 closes the transport in finally after native termination.
                expect('terminated-client-transport-closed', None, a._usock)
            b.close()
            first.cleanup()
            second.cleanup()
        for worker in workers:
            worker.verify_clean()
        expect('both-worker-inventories-restored', True, True)
        fixture = DatabaseFixture(workers[0].root)
        c = connect(fixture.get_uri())
        try:
            expect('next-database-has-no-prior-table', [[None]], c.run("SELECT to_regclass('fixture_marker')"))
            expect('previous-role-removed', [[0]], c.run("SELECT count(*) FROM pg_roles WHERE rolname='fixture_actor'"))
            c.run('CREATE ROLE fixture_actor NOLOGIN')
        finally:
            c.close()
            fixture.cleanup()
        workers[0].verify_clean()
        # A real role was created before the injected database creation failure.
        original = pg8000.native.Connection.run
        def fail_database(connection, sql, *args, **kwargs):
            if sql.startswith('CREATE DATABASE'):
                raise RuntimeError('injected create database failure')
            return original(connection, sql, *args, **kwargs)
        with patch('pg8000.native.Connection.run', fail_database):
            try:
                DatabaseFixture(workers[0].root)
            except RuntimeError as error:
                expect('setup-failure-propagates', 'injected create database failure', str(error))
            else:
                raise AssertionError('Expected setup failure')
        workers[0].verify_clean()
        expect('partial-setup-role-compensated', True, True)
        fixture = DatabaseFixture(workers[0].root)
        original_run = fixture.admin.run
        def fail_drop(sql, *args, **kwargs):
            if sql.startswith('DROP DATABASE'):
                raise RuntimeError('injected drop failure')
            return original_run(sql, *args, **kwargs)
        fixture.admin.run = fail_drop
        try:
            fixture.cleanup()
        except RuntimeError as error:
            expect('cleanup-failure-propagates', 'injected drop failure', str(error))
        else:
            raise AssertionError('Expected cleanup failure')
        try:
            DatabaseFixture(workers[0].root)
        except RuntimeError as error:
            expect('poisoned-worker-refuses-next-fixture', True, 'invalidated' in str(error))
        else:
            raise AssertionError('Poisoned worker reused')
        child_code = 'from pathlib import Path; import os,sys; from native_fixture import DatabaseFixture; DatabaseFixture(Path(sys.argv[1])); os._exit(17)'
        child_environment = os.environ.copy()
        child_environment['PYTHONPATH'] = str(Path(__file__).resolve().parent)
        child = subprocess.run([sys.executable, '-c', child_code, str(workers[1].root)],
                               env=child_environment, capture_output=True, timeout=20)
        expect('fixture-process-exit-injected', 17, child.returncode)
        try:
            workers[1].verify_clean()
        except RuntimeError as error:
            expect('process-death-leak-detected', True, 'inventory' in str(error))
        else:
            raise AssertionError('Leaked database/role inventory accepted')
        try:
            DatabaseFixture(workers[1].root)
        except RuntimeError as error:
            expect('dead-producer-worker-refuses-reuse', True, 'invalidated' in str(error))
        else:
            raise AssertionError('Dead producer worker reused')
        roots = [worker.root for worker in workers]
        pids = [worker.server.get_pid() for worker in workers]
    finally:
        for worker in workers:
            worker.close()
    expect('owned-worker-directories-removed-after-stop', [False, False], [root.exists() for root in roots])
finally:
    listener.close()

receipt = {'scope': 'Two concurrent owned PostgreSQL17.11 Unix-socket workers with TCP5432 occupied; native cleanup and injected failure controls',
           'checks': checks, 'tcp5432': tcp_occupied, 'workerPostmasterPids': pids,
           'passed': True, 'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'fixtureSha256': hashlib.sha256((Path(__file__).parent / 'native_fixture.py').read_bytes()).hexdigest(),
           'completeRuntimeQualified': False}
with destination.open('x') as output:
    output.write(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'checks': len(checks), 'passed': True, 'tcp5432': tcp_occupied}))
