"""Independent original native routine inventory refusal witnesses."""
import unittest
import psycopg
from psycopg import sql
import test_group_create_native as base
from truss._preparation_source_epoch import _runtime_inventory
from truss.catalog_runtime import _release
from truss import Ok, adopt_psycopg_host
from truss._preparation_source_epoch import (
    bootstrap_preparation_source_marker_in_transaction,
    issue_initial_preparation_source_epoch_in_transaction,
)
from truss._security_source_epoch_installation import bootstrap_source_epoch_infrastructure_in_transaction
from truss._preparation_catalog_cut import (
    bootstrap_preparation_catalog_cut_in_transaction,
    acquire_preparation_catalog_cut_with_cursor,
)

class SourceInventoryNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def test_original_genuine_epoch_and_ordinary_rr_metadata_cut(self):
        data, old_host, assembly, old_tx = self.ready(document_ids=('adoc',))
        old_host.detach(); data.commit()
        self.admin.execute('BEGIN')
        host = adopt_psycopg_host(self.admin)
        tx = host.adopt_transaction().value
        def checked(result):
            self.assertIsInstance(result, Ok, str(host._custody.last_attempt.error))
            return result.value
        marker = checked(bootstrap_preparation_source_marker_in_transaction(host, tx))
        infrastructure = checked(bootstrap_source_epoch_infrastructure_in_transaction(host, tx, installation_identity=marker.installation_id.encode()))
        epoch = checked(issue_initial_preparation_source_epoch_in_transaction(host, tx, marker=marker, infrastructure=infrastructure))
        checked(bootstrap_preparation_catalog_cut_in_transaction(host, tx, executor_role='consumer'))
        host.detach(); self.admin.commit()
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        with data.cursor() as cursor:
            acquire_preparation_catalog_cut_with_cursor(cursor)
        before = data.execute('SELECT pg_catalog.pg_current_snapshot()::text').fetchone()
        self.admin.execute("SET lock_timeout='150ms'")
        with self.assertRaises(psycopg.errors.LockNotAvailable):
            self.admin.execute('UPDATE truss.schema_head SET rev=rev WHERE id=1')
        self.assertEqual(data.execute('SELECT pg_catalog.pg_current_snapshot()::text').fetchone(), before)
        self.assertFalse(epoch.security_ready)
        self.assertEqual(data.execute('ROLLBACK').statusmessage, 'ROLLBACK')
        self.admin.execute("SET lock_timeout='0'")

    def test_original_inventory_rejects_native_execution_drift(self):
        data, host, assembly, tx = self.ready(document_ids=('adoc',))
        host.detach(); data.commit()
        owner = self.admin.execute('SELECT owner_oid FROM truss.catalog_runtime_installation WHERE singleton').fetchone()[0]
        with self.admin.cursor() as cursor:
            original = _runtime_inventory(cursor, _release()[2], owner)
        signature = self.admin.execute("SELECT p.oid::regprocedure::text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND p.proname='query_objects'").fetchone()[0]
        # Signature comes only from the original independently inspected native
        # catalog, never a request. Mutation is confined to disposable DB txs.
        changes = (
            ('parallel', sql.SQL('ALTER FUNCTION {} PARALLEL SAFE').format(sql.SQL(signature))),
            ('namespace', sql.SQL('ALTER FUNCTION {} SET search_path=public,pg_catalog').format(sql.SQL(signature))),
            ('public_acl', sql.SQL('GRANT EXECUTE ON FUNCTION {} TO PUBLIC').format(sql.SQL(signature))),
            ('owner', sql.SQL('ALTER FUNCTION {} OWNER TO CURRENT_USER').format(sql.SQL(signature))),
        )
        for label, mutation in changes:
            with self.subTest(label=label):
                self.admin.execute('BEGIN')
                try:
                    self.admin.execute(mutation)
                    with self.admin.cursor() as cursor:
                        with self.assertRaises(ValueError):
                            _runtime_inventory(cursor, _release()[2], owner)
                finally:
                    self.admin.execute('ROLLBACK')
                with self.admin.cursor() as cursor:
                    self.assertEqual(_runtime_inventory(cursor, _release()[2], owner), original)
