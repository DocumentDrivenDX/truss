# SPDX-License-Identifier: MIT OR Apache-2.0
"""Current UMF 0.10 source retention and explicit native storage refusal."""
import json
import unittest

from truss import Error, Ok
import test_catalog_runtime_native as catalog
from test_catalog_relational_support import relational_document


class DeclarativeCatalogNativeTests(catalog.PublicCatalogRuntimeTests):
    for name in tuple(n for n in dir(catalog.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[name] = None

    def test_semantic_type_source_is_retained_and_uuid_storage_refuses(self):
        self.install()
        connection, host, assembly, tx = self.consumer()

        unsupported = relational_document()
        unsupported['id'] = 'uuid-domain'
        unsupported['vocabularies'] = {'example.identity': {'version': '1.0.0'}}
        uuid_field = next(e for e in unsupported['modules'][0]['elements'] if e['id'] == 'A-label')
        uuid_field['scalarType'] = 'uuid'
        uuid_field['examples'] = [{'uuid': '01234567-89ab-cdef-8123-456789abcdef'}]
        uuid_field['semanticTypes'] = [
            {'vocabulary': 'example.identity', 'version': '1.0.0', 'term': 'external-id'}
        ]
        refused = assembly.prepare_catalog((catalog.CatalogDocument('uuid-domain', 'r1', json.dumps(unsupported).encode()),),
            bun_executable=__import__('os').environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        result = assembly.accept_in_transaction(tx, refused, request_key='unsupported-uuid-storage')
        self.assertIsInstance(result, Error)
        self.assertEqual(result.error.catalog_code, 'unsupported_profile')

        source = relational_document()
        source['id'] = 'semantic-domain'
        source['vocabularies'] = {'example.identity': {'version': '1.0.0'}}
        label = next(e for e in source['modules'][0]['elements'] if e['id'] == 'A-label')
        semantic_types = [
            {'vocabulary': 'example.identity', 'version': '1.0.0', 'term': 'external-id'}
        ]
        label['semanticTypes'] = semantic_types
        document = catalog.CatalogDocument('semantic-domain', 'r1', json.dumps(source).encode())
        prepared = assembly.prepare_catalog((document,), bun_executable=__import__('os').environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        accepted = assembly.accept_in_transaction(tx, prepared, request_key='retain-semantic-types')
        self.assertIsInstance(accepted, Ok, str(host._custody.last_attempt.error))
        host.detach(); connection.commit()

        connection, host, assembly, tx = self.consumer()
        view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request())
        self.assertIsInstance(view, Ok, str(host._custody.last_attempt.error))
        retained = []
        import base64
        for entry in view.value.view.definitions:
            try:
                definition = json.loads(base64.b64decode(entry.definition.bytes_base64))
            except (ValueError, json.JSONDecodeError):
                continue
            if definition.get('semanticTypes'):
                retained.append(definition['semanticTypes'])
        self.assertIn(semantic_types, retained)
        host.detach(); connection.commit()
