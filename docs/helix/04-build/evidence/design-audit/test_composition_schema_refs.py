import unittest
from composition_schema_refs import static_refs


class SchemaReferenceTests(unittest.TestCase):
    def test_original_references_and_literal_payload_remain_separate(self):
        schema = {'$id': 'urn:root', 'properties': {'$id': {'type': 'string'},
            'child': {'$ref': 'urn:child#/properties/x'}},
            '$defs': {'local': {'anyOf': [{'$ref': '#/$defs/local'}, {'$ref': 'urn:leaf'}]}},
            'const': {'$ref': 'urn:literal', '$id': 'literal'},
            'examples': [{'$ref': 'urn:example'}]}
        self.assertEqual(set(static_refs(schema)), {'urn:child', 'urn:leaf'})

    def test_unresolved_scope_refuses_instead_of_flattening(self):
        for schema in [{'properties': {'child': {'$id': 'urn:nested', '$ref': '#/x'}}},
                       {'$dynamicRef': '#anchor'}, {'$recursiveRef': '#'},
                       {'items': {'$ref': False}}, {'oneOf': {}}, {'properties': []}]:
            with self.subTest(schema=schema), self.assertRaises(ValueError):
                list(static_refs(schema))

    def test_conditional_array_and_content_schema_references(self):
        self.assertEqual(set(static_refs({'if': {'$ref': 'urn:condition'},
            'then': {'prefixItems': [{'$ref': 'urn:item'}]},
            'else': {'contentSchema': {'$ref': 'urn:content'}},
            'additionalProperties': False})), {'urn:condition', 'urn:item', 'urn:content'})
