#!/usr/bin/env python3
"""Disposable caller-reset compatibility experiment, not R4/R5 qualification."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import subprocess
import tempfile
import argparse
import pgserver

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--receipt', default='pgserver-caller-reset.json')
parser.add_argument('--require-matches', action='store_true')
arguments = parser.parse_args()
if Path(arguments.receipt).name != arguments.receipt or not arguments.receipt.endswith('.json'):
    raise RuntimeError('Receipt must be a JSON filename in the design-audit directory')
psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'

def observation(label):
    return ("SELECT json_build_object('case','" + label + "','session',session_user,"
            "'current',current_user,'role',current_setting('role'));\n")

steps = [
    ('role_a', 'SET ROLE truss_probe_a', 'initial', 'truss_probe_a', 'truss_probe_a'),
    ('session_b', 'SET SESSION AUTHORIZATION truss_probe_b', 'truss_probe_b', 'truss_probe_b', 'none'),
    ('reset_session', 'RESET SESSION AUTHORIZATION', 'initial', 'initial', 'none'),
    ('reset_role', 'RESET ROLE', 'initial', 'initial', 'none'),
    ('role_a_again', 'SET ROLE truss_probe_a', 'initial', 'truss_probe_a', 'truss_probe_a'),
    ('session_b_again', 'SET SESSION AUTHORIZATION truss_probe_b', 'truss_probe_b', 'truss_probe_b', 'none'),
    ('reset_all', 'RESET ALL', 'truss_probe_b', 'truss_probe_b', 'none'),
    ('reset_session_again', 'RESET SESSION AUTHORIZATION', 'initial', 'initial', 'none'),
    ('reset_role_again', 'RESET ROLE', 'initial', 'initial', 'none'),
    ('role_before_rollback', 'SET ROLE truss_probe_a', 'initial', 'truss_probe_a', 'truss_probe_a'),
    ('session_in_transaction', 'BEGIN; SET SESSION AUTHORIZATION truss_probe_b', 'truss_probe_b', 'truss_probe_b', 'none'),
    ('after_transaction_rollback', 'ROLLBACK', 'initial', 'truss_probe_a', 'truss_probe_a'),
    ('reset_after_rollback', 'RESET ROLE', 'initial', 'initial', 'none'),
    ('role_before_savepoint', 'SET ROLE truss_probe_a', 'initial', 'truss_probe_a', 'truss_probe_a'),
    ('session_in_savepoint', 'BEGIN; SAVEPOINT caller_capture; SET SESSION AUTHORIZATION truss_probe_b', 'truss_probe_b', 'truss_probe_b', 'none'),
    ('after_savepoint_rollback', 'ROLLBACK TO SAVEPOINT caller_capture', 'initial', 'truss_probe_a', 'truss_probe_a'),
    ('after_outer_rollback', 'ROLLBACK', 'initial', 'truss_probe_a', 'truss_probe_a'),
    ('final_reset', 'RESET ROLE', 'initial', 'initial', 'none'),
]
with tempfile.TemporaryDirectory(prefix='truss-caller-reset-') as directory:
    server = pgserver.get_server(Path(directory) / 'data', cleanup_mode='stop')
    try:
        def query(sql):
            return subprocess.check_output([str(psql), server.get_uri(), '-X', '-q', '-A', '-t',
                '-v', 'ON_ERROR_STOP=1'], input=sql, text=True, timeout=45).strip()
        version = query('SHOW server_version;')
        sql = 'CREATE ROLE truss_probe_a; CREATE ROLE truss_probe_b;\n' + observation('initial')
        sql += ''.join(command + ';\n' + observation(label) for label, command, *_ in steps)
        observed = [json.loads(line) for line in query(sql).splitlines()]
        if len(observed) != len(steps) + 1 or observed[0]['role'] != 'none' or observed[0]['session'] != observed[0]['current']:
            raise RuntimeError('Unexpected initial fixture or observation membership')
        initial = observed[0]['session']
        comparisons = []
        for actual, (label, _, session, current, role) in zip(observed[1:], steps):
            expected = {'case': label, 'session': initial if session == 'initial' else session,
                'current': initial if current == 'initial' else current, 'role': role}
            comparisons.append({'expected': expected, 'actual': actual, 'matches': actual == expected})
    finally:
        server.cleanup()

receipt = {'scope': 'Role/session reset observations on disposable pgserver; no installed isolation or origin profile',
    'pgserver': importlib.metadata.version('pgserver'), 'serverVersion': version,
    'advisory': 'https://www.postgresql.org/support/security/CVE-2024-10978/',
    'binaryHashes': {name: hashlib.sha256((psql.parent / name).read_bytes()).hexdigest()
        for name in ('psql', 'postgres')},
    'expectedSource': 'https://www.postgresql.org/docs/16/release-16-5.html',
    'comparisons': comparisons, 'mismatches': sum(not item['matches'] for item in comparisons),
    'callerResetSchedulePassed': all(item['matches'] for item in comparisons),
    'correctedBuildProvenanceVerified': False, 'r4Qualified': False, 'r5Qualified': False,
    'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(root / 'docs/helix/04-build/evidence/design-audit' / arguments.receipt).write_text(
    json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'serverVersion': version, 'observations': len(comparisons),
    'mismatches': receipt['mismatches'], 'r4Qualified': False, 'r5Qualified': False}))
if arguments.require_matches and receipt['mismatches']:
    raise SystemExit('Caller-reset schedule failed; corrected candidate not qualified')
