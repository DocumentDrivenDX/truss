"""Owned PostgreSQL authentication spike; not a production credential provider."""
from pathlib import Path
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import psycopg
from psycopg import sql, pq


def main():
    root = Path(__file__).resolve().parent.parent
    source = Path(__file__).read_bytes()
    assert (psycopg.__version__, pq.__impl__, pq.version()) == ('3.3.6', 'binary', 180006)
    pgbin = Path(os.environ['TRUSS_CENSUS_POSTGRES_BIN']).resolve()
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in pgbin.parent.rglob('*') if p.is_file()}
    out = root / 'docs/helix/04-build/evidence/security-native-authentication' / str(uuid.uuid4())
    out.mkdir(parents=True)
    (out / 'preimage.py').write_bytes(source)
    observations = []
    secret = secrets.token_urlsafe(32)
    wrong = secrets.token_urlsafe(32)
    result = {'status': 'component-failed'}
    started = False
    cleanup = None
    directory = tempfile.mkdtemp(prefix='truss-auth-', dir='/tmp')
    owned = Path(directory).resolve()
    data, socket = owned / 'data', owned / 'socket'
    socket.mkdir(mode=0o700)

    def pg(command, *args):
        return subprocess.run([str(pgbin / command), *map(str, args)],
                              capture_output=True, text=True, timeout=30)

    def connect(user, password=None):
        return psycopg.connect(host=str(socket), dbname='postgres', user=user,
                               password=password, autocommit=True, connect_timeout=2)

    def identity(connection):
        row = connection.execute('SELECT system_user, session_user::pg_catalog.text, current_user::pg_catalog.text').fetchone()
        assert row is not None and len(row) == 3
        return list(row)

    def install(admin, authentication):
        hba = 'local all postgres trust\nlocal all all ' + authentication + '\n'
        (data / 'pg_hba.conf').write_text(hba)
        assert admin.execute('SELECT pg_reload_conf()').fetchone() == (True,)
        deadline = time.monotonic() + 3
        while True:
            with connect('auth_actor', secret) as probe:
                observed = identity(probe)
            if observed[0] == (None if authentication == 'trust' else 'scram-sha-256:auth_actor'):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned authentication reload observation deadline')
            time.sleep(0.02)
        rows = admin.execute('SELECT type, database, user_name, auth_method, error FROM pg_hba_file_rules ORDER BY rule_number').fetchall()
        assert rows == [('local', ['all'], ['postgres'], 'trust', None),
                        ('local', ['all'], ['all'], authentication, None)]
        observations.append({'id': 'actual-hba-' + authentication, 'rules': rows})

    try:
        assert pg('initdb', '-D', data, '-U', 'postgres', '--auth=trust', '--encoding=UTF8').returncode == 0
        start = pg('pg_ctl', '-D', data, '-l', owned / 'server.log', '-w', '-o',
                   "-k " + str(socket) + " -c listen_addresses='' -c autovacuum=off", 'start')
        started = start.returncode == 0
        assert started
        with connect('postgres') as admin:
            assert admin.execute('SHOW server_version_num').fetchone() == ('180006',)
            assert admin.execute('SHOW listen_addresses').fetchone() == ('',)
            admin.execute("SET password_encryption='scram-sha-256'")
            admin.execute(sql.SQL('CREATE ROLE auth_actor LOGIN NOSUPERUSER NOCREATEROLE NOBYPASSRLS PASSWORD {}').format(sql.Literal(secret)))
            admin.execute('CREATE ROLE auth_borrowed NOLOGIN; GRANT auth_borrowed TO auth_actor')
            with connect('auth_actor', wrong) as trusted:
                before = identity(trusted)
                assert before == [None, 'auth_actor', 'auth_actor']
                observations.append({'id': 'trust-accepts-wrong-credential', 'identity': before})
            install(admin, 'scram-sha-256')
            for label, password in [('wrong-password', wrong), ('missing-password', None)]:
                try:
                    unexpected = connect('auth_actor', password)
                except psycopg.OperationalError as error:
                    category = 'password authentication failed' if label == 'wrong-password' else 'no password supplied'
                    assert category in str(error)
                    observations.append({'id': label, 'connectionRefused': True, 'nativeErrorCategory': category})
                else:
                    unexpected.close()
                    raise RuntimeError('Unqualified authentication success')
            with connect('auth_actor', secret) as authenticated:
                original = identity(authenticated)
                assert original == ['scram-sha-256:auth_actor', 'auth_actor', 'auth_actor']
                observations.append({'id': 'scram-authenticated-original', 'identity': original})
                authenticated.execute('SET ROLE auth_borrowed')
                borrowed = identity(authenticated)
                assert borrowed == ['scram-sha-256:auth_actor', 'auth_actor', 'auth_borrowed']
                observations.append({'id': 'acting-role-does-not-replace-authentication', 'identity': borrowed})
                for command in ('SET SESSION AUTHORIZATION postgres', 'SET ROLE postgres'):
                    try:
                        authenticated.execute(command)
                    except psycopg.Error as error:
                        assert error.sqlstate == '42501'
                        observations.append({'id': command, 'sqlstate': error.sqlstate})
                    else:
                        raise RuntimeError('Unqualified administrative identity change')
                authenticated.execute('RESET ROLE')
                install(admin, 'trust')
                assert identity(authenticated) == original
                with connect('auth_actor', wrong) as bypass:
                    weakened = identity(bypass)
                    assert weakened == [None, 'auth_actor', 'auth_actor']
                observations.append({'id': 'session-authentication-does-not-pin-endpoint-policy',
                                     'originalSession': original, 'newSession': weakened})
                install(admin, 'scram-sha-256')
                assert identity(authenticated) == original
            result = {'status': 'authentication-component-passed'}
    except BaseException as error:
        # Retain failure kind only; native messages/SQL may contain credentials.
        result = {'status': 'component-failed', 'failureType': type(error).__name__}
    finally:
        before_cleanup = pg('pg_ctl', '-D', data, 'status')
        stop = pg('pg_ctl', '-D', data, '-w', '-m', 'immediate', 'stop') if started or before_cleanup.returncode == 0 else None
        status = pg('pg_ctl', '-D', data, 'status')
        cleanup = {'stopExitCode': None if stop is None else stop.returncode,
                   'statusExitCode': status.returncode,
                   'socketAbsent': not (socket / '.s.PGSQL.5432').exists()}
        if cleanup != {'stopExitCode': 0, 'statusExitCode': 3, 'socketAbsent': True}:
            result['status'] = 'component-failed'
            result['unconfirmedOwnedFixture'] = str(owned)
        else:
            shutil.rmtree(owned)
    assert Path(__file__).read_bytes() == source
    assert all(hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest for name, digest in pins.items())
    result.update({'sourceSha256': hashlib.sha256(source).hexdigest(), 'nativeBinaryDigests': pins,
                   'psycopg': psycopg.__version__, 'implementation': pq.__impl__, 'libpq': pq.version(),
                   'server': '18.6', 'observations': observations, 'cleanup': cleanup,
                   'references': ['https://www.postgresql.org/docs/18/functions-info.html',
                                  'https://www.postgresql.org/docs/18/auth-password.html'],
                   'acceptancePrerequisites': ['TD-056 C01/C02/C04', 'STP-056 B05/B10/B11/B12'],
                   'limitations': ['Owned socket fixture and excluded trust-authenticated administrator only',
                                   'SCRAM proves a credential holder, not an end-user ontology subject or target-server authentication',
                                   'Session system_user does not pin authentication policy for future sessions',
                                   'No production routing/credential/issuer/mapping closure or admitted backend profile']})
    encoded = json.dumps(result, indent=2) + '\n'
    assert secret not in encoded and wrong not in encoded
    (out / 'receipt.json').write_text(encoded)
    print(json.dumps({'status': result['status'], 'observations': len(observations), 'evidence': str(out)}))
    return 0 if result['status'] == 'authentication-component-passed' else 1


if __name__ == '__main__':
    sys.exit(main())
