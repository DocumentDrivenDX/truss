"""Revision initialization compiles schema once; record work keeps authority live."""
import json
import psycopg
from truss.groups import GroupSuccess
import test_group_create_native as base


class SchemaCacheTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def test_record_work_reuses_immutable_compiled_schema(self):
        c, h, a, t = self.ready(document_ids=('adoc',))
        def snapshot():
            return self.admin.execute('SELECT rev,type_id,metadata,value_readers,valid_properties,ctid::text FROM truss.runtime_type_schema ORDER BY rev,type_id').fetchall()
        original = snapshot()
        self.assertEqual(len(original), len(self.types))
        for revision, type_id, metadata, readers, valid, _ in original:
            self.assertNotIn('properties', metadata)
            self.assertNotIn('queryRecord', metadata)
            self.assertTrue(valid)
            self.assertEqual(readers, [{'documentId': 'adoc', 'moduleId': 'm'}])
            expected = self.admin.execute('SELECT prop_id::text FROM truss.prop_def WHERE type_id=%s AND retired_rev IS NULL ORDER BY prop_id', (type_id,)).fetchall()
            self.assertEqual(metadata['propertyOrder'], [row[0] for row in expected])
            self.assertEqual(set(metadata['propertyAccess']), set(metadata['propertyOrder']))
            self.assertTrue(all(access == {'itemsValid': True, 'readers': readers}
                                for access in metadata['propertyAccess'].values()))
        operations = tuple(self.create(label='label-'+str(i), value='value-'+str(i), alias='item-'+str(i)) for i in range(32))
        result = self.apply(a, t, *self.input(a, t, operations))
        self.assertIsInstance(result, GroupSuccess)
        h.detach(); c.commit()
        self.assertEqual(snapshot(), original)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0], 32)
        for statement in ('UPDATE truss.runtime_type_schema SET metadata=metadata', 'DELETE FROM truss.runtime_type_schema', 'TRUNCATE truss.runtime_type_schema'):
            with self.assertRaises(psycopg.Error):
                with self.admin.transaction():
                    self.admin.execute(statement)

    def test_cached_query_schema_cannot_cache_permission_grants(self):
        c, h, a, t = self.ready(document_ids=('adoc',))
        from truss.catalog_runtime import _release
        manifest, digest, _ = _release()
        raw = c.execute('SELECT truss.query_binding(%s::jsonb,10000,100,16777216,%s,%s)',
            ('["adoc"]', manifest['releaseId'], digest)).fetchone()[0]
        binding = json.loads(bytes(raw))['binding']
        c.execute('SELECT truss.query_scope(%s::jsonb)', (json.dumps(binding),))
        h.detach(); c.rollback()
        self.admin.execute('REVOKE group_writer FROM consumer')
        c, h, a, t = self.consumer()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with c.transaction():
                c.execute('SELECT truss.query_scope(%s::jsonb)', (json.dumps(binding),))
        h.detach(); c.rollback()
