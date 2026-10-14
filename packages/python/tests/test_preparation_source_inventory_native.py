"""Independent original native routine inventory refusal witnesses."""
import unittest
from psycopg import sql
import test_group_create_native as base
from truss._preparation_source_epoch import _runtime_inventory
from truss.catalog_runtime import _release

class SourceInventoryNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

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
