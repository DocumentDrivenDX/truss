# SPDX-License-Identifier: MIT OR Apache-2.0
"""Preserve published 0.47 and 0.48 receipts while installing the 0.49 head."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import zipfile

import psycopg

from truss._migration_recipe import load_recipe
import test_runtime_migrations_native as fixtures


_PREVIOUS_TOOL = r'''import json,sys,psycopg
from truss.migrations import RuntimeMigrations
from truss.recovery_registry import HostRecoveryRegistry
params=json.loads(sys.argv[1]);tool=RuntimeMigrations(lambda:psycopg.connect(**params,autocommit=True),HostRecoveryRegistry(sys.argv[2]))
request=tool.prepare();result=tool.apply(request.reference)
assert result.outcome=='migrated',result
status=tool.status()
print(json.dumps({'reference':request.reference,'attemptId':request.attempt_id,
 'source':request.source,'target':request.target,'state':status['state'],
 'manifestSha256':status['manifestSha256']}))
'''


class Published48ReceiptTests(fixtures.RuntimeMigrationNativeTests):
    """Use 0.47 then 0.48 tools, then the installed 0.49 tool under test."""
    source_label = 'source44'
    wheel_environment = 'TRUSS_MIGRATION_GATE_SOURCE44'

    # The generic source44 → current tests are covered by the dynamically
    # generated source matrix. This class adds only the historical publication
    # chain that cannot be represented by a fresh direct-to-head installation.
    for _name in tuple(name for name in dir(fixtures.RuntimeMigrationNativeTests)
                       if name.startswith('test_')):
        locals()[_name] = None

    def _ledger(self):
        return dict(self.admin.execute(
            "SELECT attempt_id::text,encode(sha256(convert_to(to_jsonb(r)::text,'UTF8')),'hex') "
            'FROM truss.runtime_migration_receipt r ORDER BY attempt_id').fetchall())

    def _wheel(self, label):
        manifest, _, _ = load_recipe()
        entry = manifest['sourceWheels'][label]
        environment = f'TRUSS_MIGRATION_GATE_{label.upper()}'
        path = Path(os.environ[environment])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'])
        return entry, path

    def _apply_previous_publication(self, label):
        entry, wheel = self._wheel(label)
        old = self.root / f'published-{label}'
        shutil.rmtree(old, ignore_errors=True)
        old.mkdir(exist_ok=False)
        with zipfile.ZipFile(wheel) as archive:
            archive.extractall(old)
        result = subprocess.run(
            [sys.executable, '-c', _PREVIOUS_TOOL, json.dumps(self.params), str(self.registry.path)],
            env={**os.environ, 'PYTHONPATH': str(old)}, capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observation = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(observation['state'], 'current')
        self.assertEqual(observation['manifestSha256'], entry['runtimeManifestSha256'])
        self.assertEqual(self.tool.status()['state'], 'upgrade_required')
        self.assertEqual(self.tool.status()['manifestSha256'], entry['runtimeManifestSha256'])
        return observation

    def _upgrade_to_48(self):
        first = self._apply_previous_publication('source47')
        self.assertEqual(first['manifestSha256'],
                         '7ac989147f22d437b1ce0d814ebbfaa25aa868ab5495de125aa5e2bda7b963ea')
        second = self._apply_previous_publication('source48')
        self.assertEqual(second['manifestSha256'],
                         'c4339ac7f09ab5a004c272ab00962107a970938004c1765ec4163e4d5ca9b6f0')
        self.assertEqual(len(self._ledger()), 2)
        return first, second

    def _latest_receipt(self):
        prepared = self.tool.prepare()
        result = self.tool.apply(prepared.reference)
        self.assertEqual(result.outcome, 'migrated', result)
        self.assertEqual(self.tool.status()['state'], 'current')
        return prepared

    def test_44_to_47_to_48_to_49_preserves_both_published_receipts(self):
        first, second = self._upgrade_to_48()
        before = self._ledger()
        self.assertEqual(len(before), 2)
        latest = self._latest_receipt()
        after = self._ledger()
        self.assertEqual(len(after), 3)
        self.assertEqual({key: after[key] for key in before}, before)
        for historical in (first, second):
            resolved = self.tool.reconcile(historical['reference'])
            self.assertEqual(resolved.outcome, 'already_applied', resolved)
        self.assertEqual(self._ledger(), after, 'Historical reconciliation must not execute an older target')
        receipt = self.tool.receipt(latest.reference)
        self.assertEqual(receipt['attemptId'], latest.attempt_id)

    def test_49_lost_commit_response_preserves_47_and_48_receipts(self):
        first, second = self._upgrade_to_48()
        before = self._ledger()
        prepared = self.tool.prepare()
        from security_commit_loss_proxy import CommitResponseDropProxy
        from truss.migrations import RuntimeMigrations
        proxy = CommitResponseDropProxy(self.params, maximum_backend_frame_bytes=16777216)
        self.addCleanup(proxy.close)
        calls = 0

        def factory():
            nonlocal calls
            calls += 1
            if calls != 2:
                return self.connect()
            connection = psycopg.connect(
                **{**self.params, 'host': '127.0.0.1', 'port': proxy.port,
                   'sslmode': 'disable', 'gssencmode': 'disable'},
                autocommit=True, options='-c statement_timeout=10000')
            proxy.armed.set()
            return connection

        result = RuntimeMigrations(factory, self.registry).apply(prepared.reference)
        self.assertEqual(result.outcome, 'commit_unknown', result)
        self.assertTrue(proxy.dropped.wait(2))
        self.assertEqual(proxy.errors, [])
        resolved = RuntimeMigrations(self.connect, self.registry).reconcile(prepared.reference)
        self.assertEqual(resolved.outcome, 'already_applied', resolved)
        after = self._ledger()
        self.assertEqual(len(after), 3)
        self.assertEqual({key: after[key] for key in before}, before)
        for historical in (first, second):
            self.assertEqual(self.tool.reconcile(historical['reference']).outcome, 'already_applied')
        self.assertEqual(self._ledger(), after)

    def test_49_upgrade_after_dump_restore_preserves_both_published_receipts(self):
        _first, _second = self._upgrade_to_48()
        before = self._ledger()
        self.assertEqual(len(before), 2)
        backup = self.root / 'source48.dump'
        uri = psycopg.conninfo.make_conninfo(**self.params)
        from importlib.resources import files
        binaries = Path(str(files('pgserver'))) / 'pginstall/bin'
        subprocess.run([str(binaries / 'pg_dump'), '--dbname', uri, '--format=custom',
                        '--file', str(backup)], check=True, capture_output=True, timeout=60)
        companion = self.tool.backup_metadata()
        self.admin.close()
        with psycopg.connect(self.uri, autocommit=True) as connection:
            connection.execute(psycopg.sql.SQL('DROP DATABASE {} WITH (FORCE)').format(
                psycopg.sql.Identifier(self.database)))
            connection.execute(psycopg.sql.SQL('CREATE DATABASE {}').format(
                psycopg.sql.Identifier(self.database)))
        subprocess.run([str(binaries / 'pg_restore'), '--dbname', uri, '--exit-on-error',
                        str(backup)], check=True, capture_output=True, timeout=60)
        self.admin = self.connect()
        with self.assertRaisesRegex(ValueError, 'privileges drifted'):
            self.tool.status()
        for statement in companion['rowTypePrivilegeRestoreSql']:
            self.admin.execute(statement)
        restored = self.tool.status()
        self.assertEqual(restored['state'], 'upgrade_required')
        self.assertEqual(restored['manifestSha256'],
                         'c4339ac7f09ab5a004c272ab00962107a970938004c1765ec4163e4d5ca9b6f0')
        latest = self._latest_receipt()
        after = self._ledger()
        self.assertEqual(len(after), 3)
        self.assertEqual({key: after[key] for key in before}, before)
        self.assertEqual(self.tool.receipt(latest.reference)['attemptId'], latest.attempt_id)
