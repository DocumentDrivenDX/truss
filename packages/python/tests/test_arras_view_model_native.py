# SPDX-License-Identifier: MIT OR Apache-2.0
"""Arras view metadata remains source data through native Truss and Weft."""
from hashlib import sha256
import json

from truss import AcceptedDocument, Ok, QueryCatalogRead, QueryRows
from truss.groups import (AliasObjectReference, CreateEdge, GroupSuccess, NullOrderKey)
import test_object_mutations_native as mutation_tests


class ArrasViewModelNativeTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_arras_view_metadata_is_retained_and_current_weft_query_succeeds(self):
        original_source = None
        opaque = {'future': {'nested': ['keep', None, {'text': '雪', 'ordinal': 7}]}}

        def add_arras_view(source):
            nonlocal original_source
            source['vocabularies']['arras.view'] = {'version': '0.1.0'}
            source['vocabularies']['vendor.arras'] = {'version': '1.0.0'}
            module = source['modules'][0]
            module['extensions']['arras.view'] = {
                'title': 'Native catalog',
                'description': 'Arras presentation metadata on an ordinary UMF source.',
            }
            source['extensions']['vendor.arras'] = opaque
            record = next(element for element in module['elements'] if element['id'] == 'A')
            record['extensions'] = {
                'arras.view': {
                    'label': 'Item',
                    'pluralLabel': 'Items',
                    'icon': 'box',
                    'tone': 'teal',
                    'title': 'Catalog item',
                    'summary': 'A native catalog item.',
                    'sections': [{'label': 'Details', 'properties': ['A-value']}],
                    'search': ['A-label'],
                },
            }
            label = next(element for element in module['elements'] if element['id'] == 'A-label')
            label['extensions']['arras.view'] = {'label': 'Display label', 'format': 'text'}
            module['relationships'][0]['extensions'] = {
                'arras.view': {'label': 'Related items', 'hideWhenEmpty': True, 'order': 10},
            }
            original_source = json.dumps(source, indent=2, ensure_ascii=False).encode('utf-8')

        connection, host, assembly, tx = self.ready(add_arras_view, document_ids=('adoc',))
        self.assertEqual(len(self.documents), 1)
        self.assertEqual(self.documents[0].document_id, 'adoc')
        self.assertEqual(self.documents[0].document_revision, 'r1')
        self.assertEqual(self.documents[0].content, original_source)

        sourced = assembly.accepted_document_in_transaction(tx, document_id='adoc')
        self.assertIsInstance(sourced, Ok, repr(sourced))
        self.assertIsInstance(sourced.value, AcceptedDocument, repr(sourced.value))
        accepted = sourced.value
        self.assertEqual(
            (accepted.document_id, accepted.document_revision, accepted.sha256,
             accepted.content, accepted.catalog_revision),
            ('adoc', 'r1', sha256(original_source).hexdigest(), original_source, 1),
        )
        decoded = json.loads(accepted.content)
        self.assertEqual(decoded['umf'], '0.10.0')
        self.assertEqual(decoded['vocabularies']['arras.view'], {'version': '0.1.0'})
        self.assertEqual(decoded['extensions']['vendor.arras'], opaque)

        relationship = assembly.get_relationship_reference_in_transaction(
            tx, document_id='adoc', module_id='m', relationship_id='A-B')
        self.assertIsInstance(relationship, Ok, repr(relationship))
        created, _, _ = self.run_group(assembly, tx, (
            self.create(label='from-arras-view', alias='view-source'),
            self.create(label='related-target', alias='view-target', record='B'),
            CreateEdge(
                relationship_definition_pin=relationship.value.definition_pin,
                source=AliasObjectReference(alias='view-source'),
                target=AliasObjectReference(alias='view-target'),
                values=(), order_key=NullOrderKey()),
        ), 'arras-view-native-query')
        self.assertIsInstance(created, GroupSuccess, repr(created))
        queried = assembly.query_with_catalog_in_transaction(
            tx, sql='SELECT a."A-label" FROM "A" a WHERE HAS_RELATED(a."A-B",KEY(:value,:label))',
            document_ids=('adoc',), parameters={'value': 'value', 'label': 'related-target'})
        self.assertIsInstance(queried, Ok, repr(queried))
        self.assertIsInstance(queried.value, QueryCatalogRead, repr(queried.value))
        self.assertIsInstance(queried.value.result, QueryRows, repr(queried.value.result))
        self.assertEqual(queried.value.result.rows, (('from-arras-view',),))
        self.assertEqual(len(queried.value.documents), 1)
        query_source = queried.value.documents[0]
        self.assertEqual(
            (query_source.document_id, query_source.document_revision, query_source.umf_version,
             query_source.sha256, query_source.content),
            ('adoc', 'r1', '0.10.0', sha256(original_source).hexdigest(), original_source),
        )
