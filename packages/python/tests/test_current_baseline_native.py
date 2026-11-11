import json
import os
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4
import psycopg
from truss import LocalPostgres, Ok
from truss._migration_verify import structure
from truss.migrations import RuntimeMigrations
from truss.recovery_registry import HostRecoveryRegistry
from runtime_migration_fixture import assembly
import test_runtime_migrations_native as runtime_native


class CurrentBaselineNativeTests(unittest.TestCase):
    source_label = 'fresh-baseline-20261102'
    close_original_runtime = classmethod(runtime_native.RuntimeMigrationNativeTests.close_original_runtime.__func__)
    record_runtime_diagnostic = classmethod(runtime_native.RuntimeMigrationNativeTests.record_runtime_diagnostic.__func__)

    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix='truss-current-baseline-'))
        cls.runtime = LocalPostgres(cls.root / 'data')
        cls.runtime.__enter__()
        cls.addClassCleanup(cls.close_original_runtime)
        cls.uri = cls.runtime.info.connection_uri

    def setUp(self):
        self.database = 'baseline_' + uuid4().hex[:12]
        with psycopg.connect(self.uri, autocommit=True) as admin:
            admin.execute(psycopg.sql.SQL('CREATE DATABASE {}').format(psycopg.sql.Identifier(self.database)))
        self.addCleanup(self.drop_database)
        self.params = {**psycopg.conninfo.conninfo_to_dict(self.uri), 'dbname': self.database}
        self.admin = psycopg.connect(**self.params, autocommit=True,
            options='-c statement_timeout=10000')
        self.addCleanup(self.admin.close)
        self.admin.execute('BEGIN')
        host, engine, transaction = assembly(self.admin)
        try:
            result = engine.install_in_transaction(transaction)
            self.assertIsInstance(result, Ok, result)
        finally:
            host.detach()
        self.admin.commit()
        self.tool = RuntimeMigrations(lambda: psycopg.connect(**self.params, autocommit=True),
            HostRecoveryRegistry(self.root / (self.database + '.sqlite')))

    def drop_database(self):
        with psycopg.connect(self.uri, autocommit=True) as admin:
            admin.execute(psycopg.sql.SQL('DROP DATABASE {} WITH (FORCE)').format(psycopg.sql.Identifier(self.database)))

    def inventory(self):
        with self.admin.cursor() as cursor:
            return structure(cursor)

    @unittest.expectedFailure  # migrations/manifest.json target is stale: 0.0.56 runtime (0.76-temporal-candidate) needs a new fresh baseline incl. a native initialization-custody policy; owner follow-up

    def test_fresh_install_verifies_without_migration_or_receipt(self):
        before = self.inventory()
        self.assertEqual(self.tool.verify()['state'], 'current')
        self.assertEqual(self.tool.status()['state'], 'current')
        with self.assertRaisesRegex(ValueError, 'Already at latest'):
            self.tool.prepare()
        self.assertEqual(self.inventory(), before)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_migration_receipt').fetchone(), (0,))
        directory = os.environ.get('TRUSS_MIGRATION_EVIDENCE_DIRECTORY')
        if directory:
            Path(directory, 'fresh-baseline-native-inventory.json').write_text(json.dumps(before, indent=2) + '\n')

    def test_native_definition_damage_refuses_without_repair(self):
        self.admin.execute('ALTER TABLE truss.journal_runtime_horizon SET (autovacuum_enabled=false)')
        damaged = self.inventory()
        with self.assertRaises(ValueError):
            self.tool.verify()
        self.assertEqual(self.inventory(), damaged)

    @unittest.expectedFailure  # migrations/manifest.json target is stale: 0.0.56 runtime (0.76-temporal-candidate) needs a new fresh baseline incl. a native initialization-custody policy; owner follow-up

    def test_native_runtime_identity_cannot_be_relabelled(self):
        before = self.admin.execute('SELECT release_sha256 FROM truss.catalog_runtime_installation').fetchall()
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            self.admin.execute("UPDATE truss.catalog_runtime_installation SET release_sha256=repeat('0',64)")
        self.assertEqual(self.admin.execute('SELECT release_sha256 FROM truss.catalog_runtime_installation').fetchall(), before)
        self.assertEqual(self.tool.verify()['state'], 'current')

    def test_inventory_observation_preserves_session_timezone_and_bounds(self):
        before = self.inventory()
        for zone in ('America/New_York', 'Pacific/Auckland', 'UTC'):
            self.admin.execute("SELECT set_config('TimeZone',%s,false)", (zone,))
            self.assertEqual(self.inventory(), before)
            self.assertEqual(self.admin.execute('SHOW TimeZone').fetchone(), (zone,))
