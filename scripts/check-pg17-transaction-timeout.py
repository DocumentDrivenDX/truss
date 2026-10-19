#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native PostgreSQL 17 timeout capability; not a complete deadline profile."""
from truss._runtime_profile import RUNTIME_DISTRIBUTION, RUNTIME_VERSION, SERVER_VERSION, SERVER_VERSION_NUM
from native_fixture import evidence_directory
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import tempfile

from truss import LocalPostgres

root = Path(__file__).resolve().parents[1]
destination = evidence_directory() / f'pgserver-pg{SERVER_VERSION}-transaction-timeout.json'
if destination.exists():
    raise RuntimeError('Receipt exists')
if importlib.metadata.version(RUNTIME_DISTRIBUTION) != RUNTIME_VERSION:
    raise RuntimeError('Pinned PostgreSQL 17 candidate required')
with tempfile.TemporaryDirectory(prefix='truss-pg17-timeout-') as directory:
    with LocalPostgres(Path(directory) / 'data') as runtime:
        command = [str(runtime.psql_path), runtime.info.connection_uri, '-X', '-qAt',
                   '-v', 'ON_ERROR_STOP=1']
        settings = subprocess.check_output(command, input="SELECT name || '=' || setting FROM pg_settings WHERE name IN ('transaction_timeout','statement_timeout','lock_timeout') ORDER BY name;",
                                           text=True, timeout=10).splitlines()
        expected = ['lock_timeout=0', 'statement_timeout=0', 'transaction_timeout=0']
        if settings != expected:
            raise RuntimeError('Native default settings mismatch')
        sql = "SET transaction_timeout='100ms'; BEGIN; SELECT pg_sleep(1); COMMIT;"
        result = subprocess.run(command, input=sql, text=True, capture_output=True, timeout=10)
        if result.returncode == 0 or 'terminating connection due to transaction timeout' not in result.stderr:
            raise RuntimeError('Native transaction termination not observed: ' + result.stderr)
        if subprocess.check_output(command, input='SELECT 1;', text=True, timeout=10).strip() != '1':
            raise RuntimeError('Fresh connection unavailable')
        version = runtime.info.server_version
    stopped = not (Path(directory) / 'data/postmaster.pid').exists()
    if not stopped:
        raise RuntimeError('Owned server stop unconfirmed')
receipt = {'scope': f'Native setting availability and active transaction connection termination on local PostgreSQL {SERVER_VERSION}',
           'serverVersion': version, 'pgserver': importlib.metadata.version(RUNTIME_DISTRIBUTION),
           'expectedDefaults': expected, 'observedDefaults': settings,
           'terminationSql': sql, 'returncode': result.returncode,
           'stdout': result.stdout, 'stderr': result.stderr, 'freshConnectionPassed': True,
           'ownedServerStopped': stopped, 'completeDeadlineProfileQualified': False,
           'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with destination.open('x') as output:
    output.write(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'serverVersion': version, 'transactionTimeoutTerminatesConnection': True}))
