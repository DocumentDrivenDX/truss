#!/usr/bin/env python3
"""Rollback-only composition probe of original base, adjunct DDL and immutable guards on pgserver."""
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
paths = [
 'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
 'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql',
 'docs/helix/04-build/evidence/layout-migration-storage.owner-export.sql',
 'packages/postgresql/native/operation-configuration-immutability.sql',
 'packages/postgresql/native/layout-migration-receipt-immutability.sql',
]
originals = [(root / path).read_bytes() for path in paths]
original = b';\n'.join(originals)
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
DO $$
DECLARE mode text; relation text;
BEGIN
 FOREACH mode IN ARRAY ARRAY['origin','replica'] LOOP
  PERFORM set_config('session_replication_role',mode,true);
  FOREACH relation IN ARRAY ARRAY['operation_configuration','layout_migration_receipt'] LOOP
   BEGIN
    EXECUTE format('TRUNCATE truss.%I',relation);
    RAISE EXCEPTION 'immutable truncate did not refuse' USING ERRCODE='P0001';
   EXCEPTION WHEN SQLSTATE '55000' THEN NULL;
   END;
  END LOOP;
 END LOOP;
 PERFORM set_config('session_replication_role','origin',true);
END $$;
SELECT json_build_object(
 'tables',(SELECT json_agg(c.relname ORDER BY c.relname) FROM pg_class c
 JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relkind IN ('r','p')),
 'serverVersion',current_setting('server_version'),
 'sha256',to_regprocedure('pg_catalog.sha256(bytea)') IS NOT NULL,
 'xactStatus',to_regprocedure('pg_catalog.pg_xact_status(xid8)') IS NOT NULL,
 'currentXid',to_regprocedure('pg_catalog.pg_current_xact_id_if_assigned()') IS NOT NULL,
 'uuidIssuer',to_regprocedure('pg_catalog.gen_random_uuid()') IS NOT NULL,
 'adjuncts',(SELECT json_object_agg(c.relname,json_build_object(
  'columns',(SELECT count(*) FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped),
  'foreignKeys',(SELECT count(*) FROM pg_constraint k WHERE k.conrelid=c.oid AND k.contype='f'),
  'generatedHashes',(SELECT count(*) FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attgenerated='s'),
  'alwaysGuards',(SELECT count(*) FROM pg_trigger t WHERE t.tgrelid=c.oid AND NOT t.tgisinternal AND t.tgenabled='A'),
  'publicInsert',has_table_privilege('public',c.oid,'INSERT')))
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'
  AND c.relname IN ('operation_configuration','layout_migration_receipt')),
 'transactionTimeout',current_setting('transaction_timeout',true));
ROLLBACK;
'''
        observed = json.loads(query('BEGIN;\n' + original.decode('utf-8') + ';\n' + probe))
        assert observed['tables'] == sorted(expected), (observed['tables'], expected)
        assert all(observed[k] for k in ['sha256', 'xactStatus', 'currentXid', 'uuidIssuer'])
        assert observed['adjuncts'] == {
            'operation_configuration': {'columns': 16, 'foreignKeys': 2, 'generatedHashes': 3, 'alwaysGuards': 2, 'publicInsert': False},
            'layout_migration_receipt': {'columns': 11, 'foreignKeys': 1, 'generatedHashes': 3, 'alwaysGuards': 2, 'publicInsert': False},
        }, observed['adjuncts']
        assert query("SELECT to_regnamespace('truss') IS NULL;") == 't'
    finally:
        server.cleanup()
receipt = {'scope': 'Original generated base/adjunct DDL and immutable guard composition, declared table names and independent adjunct catalog expectations under rollback only; no complete installer, routine/grant inventory, accepted catalog or migration qualification',
           'pgserverVersion': '0.1.4', 'sources': [{'path': path, 'sha256': hashlib.sha256(value).hexdigest()} for path, value in zip(paths, originals)], 'observation': observed,
           'rollbackRemovedNamespace': True, 'truncateRefusals': 4, 'truncateModes': ['origin', 'replica'],
           'limitation': 'PostgreSQL16.2 lacks transaction_timeout; any selected profile requiring that setting must refuse or use a separately admitted bounded alternative',
           'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(root / 'docs/helix/04-build/evidence/design-audit/pgserver-composed-adjunct-component.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'serverVersion': observed['serverVersion'], 'tables': len(expected),
                  'rollbackRemovedNamespace': True, 'truncateRefusals': 4, 'truncateModes': ['origin', 'replica'], 'transactionTimeout': observed['transactionTimeout']}))
