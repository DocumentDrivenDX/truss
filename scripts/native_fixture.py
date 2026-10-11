"""Test-only owned pgserver workers and disposable database/role fixtures.

No application connection is accepted here. Workers own fresh local clusters;
fixtures serialize cluster-wide role changes and refuse a poisoned worker.
"""
import json
import os
import shutil
from pathlib import Path
import tempfile
import threading
from urllib.parse import parse_qs, urlparse, urlunparse, urlencode
import uuid

import fasteners
import pg8000.native
import pgserver


_lifecycle_lock = threading.RLock()
_fixture_thread_locks = {}


def evidence_directory():
    root = Path(__file__).resolve().parents[1] / 'docs/helix/04-build/evidence/design-audit'
    directory = Path(os.environ.get('TRUSS_NATIVE_EVIDENCE_DIR', str(root))).resolve()
    if not directory.is_relative_to(root.resolve()) or not directory.is_dir():
        raise RuntimeError('Native evidence destination must exist under design-audit')
    return directory


def connect(uri, *, timeout=10):
    parsed = urlparse(uri)
    options = parse_qs(parsed.query)
    host = options.get('host', [None])[0]
    if not host or not Path(host).is_absolute():
        raise RuntimeError('Native test workers require an explicit Unix socket directory')
    port = int(options.get('port', [parsed.port or 5432])[0])
    return pg8000.native.Connection(user=parsed.username or 'postgres',
        database=parsed.path.lstrip('/'), unix_sock=str(Path(host) / f'.s.PGSQL.{port}'),
        ssl_context=False, timeout=timeout)


def inventory(connection):
    return {'databases': connection.run('SELECT datname, datdba::text, datistemplate, datallowconn, datconnlimit FROM pg_database ORDER BY datname'),
            'roles': connection.run('SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolreplication, rolbypassrls, rolconnlimit, rolconfig FROM pg_roles ORDER BY rolname'),
            'memberships': connection.run('SELECT roleid::text, member::text, grantor::text, admin_option, inherit_option, set_option FROM pg_auth_members ORDER BY roleid,member,grantor')}


class WorkerCluster:
    """One short-path, socket-only cluster per suite/worker, explicitly stopped."""
    def __enter__(self):
        self.root = Path(tempfile.mkdtemp(prefix='truss-nw-', dir='/tmp')).resolve()
        self.server = None
        try:
            with _lifecycle_lock:
                self.server = pgserver.get_server(self.root / 'data', cleanup_mode='stop')
            parsed = urlparse(self.server.get_uri())
            options = parse_qs(parsed.query)
            options['port'] = [str(self.server.get_postmaster_info().port)]
            self.uri = urlunparse(parsed._replace(query=urlencode(options, doseq=True)))
            admin = connect(self.uri)
            try:
                self.baseline = inventory(admin)
                self.settings = dict(admin.run("SELECT name, setting FROM pg_settings WHERE name IN ('listen_addresses','port','unix_socket_directories','server_version')"))
                if self.settings['listen_addresses'] != '' or self.settings['server_version'] != '17.11':
                    raise RuntimeError('Expected socket-only PostgreSQL17.11 worker')
                socket_directory = Path(self.settings['unix_socket_directories']).resolve()
                if socket_directory != self.root / 'data':
                    raise RuntimeError('Worker socket directory must belong to its short owned path')
                if not (socket_directory / ('.s.PGSQL.' + self.settings['port'])).is_socket():
                    raise RuntimeError('Owned worker socket not observed')
            finally:
                admin.close()
            (self.root / 'owner.json').write_text(json.dumps({'uri': self.uri, 'baseline': self.baseline}))
            return self
        except BaseException as original:
            try:
                self.close()
            except Exception as cleanup:
                raise RuntimeError(f'Worker startup failed: {original}; cleanup failed: {cleanup}; retained {self.root}') from original
            raise

    def environment(self):
        return {'TRUSS_NATIVE_WORKER': str(self.root)}

    def verify_clean(self):
        if (self.root / 'poisoned').exists():
            raise RuntimeError('Worker invalidated by fixture cleanup failure')
        admin = connect(self.uri)
        try:
            if inventory(admin) != self.baseline:
                (self.root / 'poisoned').write_text('Worker inventory drift')
                raise RuntimeError('Worker database/role inventory did not return to baseline')
        finally:
            admin.close()

    def close(self):
        if not self.root.exists():
            return
        if self.server is not None:
            with _lifecycle_lock:
                self.server.cleanup()
            if (self.root / 'data/postmaster.pid').exists():
                raise RuntimeError('Worker shutdown unconfirmed; directory retained')
            self.server = None
        if (self.root / 'data/postmaster.pid').exists():
            raise RuntimeError('Possible startup process remains; directory retained')
        shutil.rmtree(self.root)

    def __exit__(self, *args):
        self.close()


class DatabaseFixture:
    def __init__(self, root):
        self.root = root
        self.owner = json.loads((root / 'owner.json').read_text())
        with _lifecycle_lock:
            self.thread_lock = _fixture_thread_locks.setdefault(root, threading.Lock())
        if not self.thread_lock.acquire(blocking=False):
            raise RuntimeError('Worker fixture already leased')
        self.lock = fasteners.InterProcessLock(str(root / 'fixture.lock'))
        try:
            if not self.lock.acquire(blocking=False):
                raise RuntimeError('Worker fixture already leased')
        except BaseException:
            self.thread_lock.release()
            raise
        self.admin = None
        self.database = 'truss_test_' + uuid.uuid4().hex
        self.role = 'truss_owner_' + uuid.uuid4().hex
        try:
            if (root / 'poisoned').exists():
                raise RuntimeError('Worker invalidated by fixture cleanup failure')
            self.admin = connect(self.owner['uri'], timeout=60)
            self.admin.run('SET statement_timeout=45000; SET lock_timeout=5000')
            self.before = inventory(self.admin)
            if self.before != self.owner['baseline']:
                (root / 'poisoned').write_text('Worker baseline drift')
                raise RuntimeError('Worker baseline drift; refuse fixture')
            self.admin.run(f'CREATE ROLE "{self.role}" NOLOGIN')
            self.admin.run(f'CREATE DATABASE "{self.database}" OWNER "{self.role}"')
            parsed = urlparse(self.owner['uri'])
            self.uri = urlunparse(parsed._replace(path='/' + self.database))
        except BaseException:
            if self.admin is not None and hasattr(self, 'before'):
                self.cleanup()
            else:
                try:
                    if self.admin is not None:
                        self.admin.close()
                finally:
                    self.lock.release()
                    self.thread_lock.release()
            raise

    def get_uri(self):
        return self.uri

    def cleanup(self):
        if self.admin is None:
            return
        try:
            # FORCE terminates only sessions attached to this owned fixture DB.
            self.admin.run(f'DROP DATABASE IF EXISTS "{self.database}" WITH (FORCE)')
            old_roles = {row[0] for row in self.before['roles']}
            roles = [row[0] for row in self.admin.run('SELECT rolname FROM pg_roles ORDER BY rolname') if row[0] not in old_roles]
            for role in roles:
                quoted = '"' + role.replace('"', '""') + '"'
                self.admin.run(f'DROP OWNED BY {quoted}')
                self.admin.run(f'DROP ROLE {quoted}')
            after = inventory(self.admin)
            if after != self.before:
                raise RuntimeError('Fixture database/role cleanup incomplete')
            with (self.root / 'fixtures.jsonl').open('a') as output:
                output.write(json.dumps({'database': self.database, 'ownerRole': self.role,
                    'removedRoles': roles, 'baselineRestored': True}) + '\n')
        except BaseException as error:
            (self.root / 'poisoned').write_text(str(error))
            raise
        finally:
            try:
                self.admin.close()
            except BaseException as error:
                (self.root / 'poisoned').write_text('Administrative connection cleanup failed: ' + str(error))
                raise
            finally:
                self.admin = None
                self.lock.release()
                self.thread_lock.release()


def get_server(data_directory, *, cleanup_mode='stop'):
    """Shared fresh database when run by the suite; isolated server otherwise."""
    worker = os.environ.get('TRUSS_NATIVE_WORKER')
    if worker:
        return DatabaseFixture(Path(worker))
    return pgserver.get_server(data_directory, cleanup_mode=cleanup_mode)
