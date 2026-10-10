#!/usr/bin/env python3
"""Rollback-only admission probe of original generated review DDL on pgserver."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import re
import subprocess
import tempfile

import pgserver

root = Path(__file__).resolve().parents[1]
source = root / 'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql'
original = source.read_bytes()
expected = re.findall(r'CREATE TABLE truss\.([a-z_]+)\s*\(', original.decode('utf-8'))
assert expected and len(set(expected)) == len(expected)
if importlib.metadata.version('pgserver') != '0.1.4':
    raise SystemExit('Expected pinned pgserver0.1.4')
psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'
with tempfile.TemporaryDirectory(prefix='truss-pgserver-layout-') as directory:
    server = pgserver.get_server(Path(directory) / 'data', cleanup_mode='stop')
    def query(sql):
        return subprocess.check_output(
            [str(psql), server.get_uri(), '-X', '-q', '-A', '-t', '-v', 'ON_ERROR_STOP=1'],
            input=sql, text=True, timeout=60).strip()
    try:
        # No schema replacement, substituted SQL or installed publication.
        probe = '''
SELECT json_build_object(
 'tables',(SELECT json_agg(c.relname ORDER BY c.relname) FROM pg_class c
 JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relkind IN ('r','p')),
 'serverVersion',current_setting('server_version'),
 'sha256',to_regprocedure('pg_catalog.sha256(bytea)') IS NOT NULL,
 'xactStatus',to_regprocedure('pg_catalog.pg_xact_status(xid8)') IS NOT NULL,
 'currentXid',to_regprocedure('pg_catalog.pg_current_xact_id_if_assigned()') IS NOT NULL,
 'uuidIssuer',to_regprocedure('pg_catalog.gen_random_uuid()') IS NOT NULL,
 'transactionTimeout',current_setting('transaction_timeout',true));
ROLLBACK;
'''
        observed = json.loads(query('BEGIN;\n' + original.decode('utf-8') + ';\n' + probe))
        assert observed['tables'] == sorted(expected), (observed['tables'], expected)
        assert all(observed[k] for k in ['sha256', 'xactStatus', 'currentXid', 'uuidIssuer'])
        assert query("SELECT to_regnamespace('truss') IS NULL;") == 't'
    finally:
        server.cleanup()
receipt = {'scope': 'Original generated review DDL execution and table-name correspondence under rollback only; no complete installer, routine/grant inventory, accepted catalog or migration qualification',
           'pgserverVersion': '0.1.4', 'source': str(source.relative_to(root)),
           'sourceSha256': hashlib.sha256(original).hexdigest(), 'observation': observed,
           'rollbackRemovedNamespace': True,
           'limitation': 'PostgreSQL16.2 lacks transaction_timeout; any selected profile requiring that setting must refuse or use a separately admitted bounded alternative',
           'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(root / 'docs/helix/04-build/evidence/design-audit/pgserver-generated-layout-component.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'serverVersion': observed['serverVersion'], 'tables': len(expected),
                  'rollbackRemovedNamespace': True, 'transactionTimeout': observed['transactionTimeout']}))
