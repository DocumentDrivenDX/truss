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
        # Catalog extraction remains a registrar operation. Load once under
        # that authority; ordinary writes subsequently reuse the immutable data.
        from psycopg import sql
        self.admin.execute(sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(sql.Identifier(self.installation.registrar_role)))
        observed = a.catalog_view_in_transaction(t, a.catalog_view_request())
        self.assertIsInstance(observed, base.Ok, repr(observed))
        view = observed.value.view
        from unittest.mock import patch
        with patch('truss._catalog_view_build.decode_catalog_source_json', side_effect=AssertionError('Warm schema must not parse again')):
            again = a.catalog_view_in_transaction(t, a.catalog_view_request()).value.view
        self.admin.execute(sql.SQL('REVOKE {} FROM consumer').format(sql.Identifier(self.installation.registrar_role)))
        self.assertIs(again, view)
        self.assertIs(again.schema, view.schema)
        self.assertEqual(len(view.schema.types_by_identity), len(self.types))
        for (document, module, record), entry in view.schema.types_by_identity.items():
            self.assertEqual(entry.reference, self.types[(document, record)])
            properties = view.schema.properties_by_type[entry.reference.type_id]
            self.assertEqual(len(properties), 2)
            for property in properties.values():
                declaration = view.schema.declarations_by_pin[property.reference.definition_pin]
                self.assertEqual(declaration['kind'], 'field')
                with self.assertRaises(TypeError):
                    declaration['scalarType'] = 'wrong'
        with self.assertRaises(TypeError):
            view.schema.types_by_identity[('changed','m','A')] = None
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
            # Key compilation keeps the complete authored field meaning and
            # ordered native facets, independently of the cached lookup path.
            document_id, module_id = self.admin.execute(
                'SELECT document_id,module FROM truss.type_def WHERE type_id=%s', (type_id,)).fetchone()
            source_text, umf_version = self.admin.execute(
                'SELECT document,umf_version FROM truss.schema_doc WHERE doc_id=%s AND rev<=%s ORDER BY rev DESC LIMIT 1',
                (document_id, revision)).fetchone()
            source = json.loads(source_text)
            fields = {(module['id'], field['id']): field for module in source['modules']
                      for field in module['elements']}
            expected_codecs = {}
            for number, property_ids in self.admin.execute(
                    'SELECT key_num,prop_ids FROM truss.key_def WHERE type_id=%s AND retired_rev IS NULL ORDER BY key_num',
                    (type_id,)).fetchall():
                components = [self.admin.execute(
                    'SELECT declaration_module,element,facets FROM truss.prop_def WHERE prop_id=%s',
                    (property_id,)).fetchone() for property_id in property_ids]
                expected_codecs[str(number)] = {
                    'profile': 'truss-native-key-codec-metadata/0.1',
                    'typeId': str(type_id), 'keyNumber': str(number),
                    'fields': [fields[(module, element)] for module, element, _ in components],
                    'facets': [facets or {} for _, _, facets in components], 'umfVersion': umf_version}
            self.assertEqual(metadata['keyCodecs'], expected_codecs)
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
        from truss.catalog_view import CatalogViewAvailable
        observed = a.catalog_view_in_transaction(t, a.catalog_view_request())
        self.assertFalse(isinstance(observed, base.Ok) and isinstance(observed.value, CatalogViewAvailable))
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with c.transaction():
                c.execute('SELECT truss.query_scope(%s::jsonb)', (json.dumps(binding),))
        h.detach(); c.rollback()
