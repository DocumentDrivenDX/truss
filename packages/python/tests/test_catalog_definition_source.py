import unittest
from truss._catalog_definition_source import extract_definition


class CatalogDefinitionSourceTests(unittest.TestCase):
    def test_preserves_exact_source_spelling_and_unknown_content(self):
        source=b' { "modules" : [ {"elements": [ { "id":"a", "x-unknown":1.2300, "name":"\\u00e9" } ]} ] } '
        self.assertEqual(extract_definition(source,'/modules/0/elements/0'),
            b'{ "id":"a", "x-unknown":1.2300, "name":"\\u00e9" }')

    def test_pointer_escapes_and_unicode_offsets(self):
        source='{"前":"文", "a/b":{"~key" : [ "✓" ]}}'.encode()
        self.assertEqual(extract_definition(source,'/a~1b/~0key/0'),'"✓"'.encode())

    def test_missing_or_noncanonical_pointer_refuses(self):
        for pointer in ('a','/absent','/items/01','/items/-','/bad~2'):
            with self.subTest(pointer=pointer),self.assertRaises(ValueError):
                extract_definition(b'{"items":[1]}',pointer)

    def test_invalid_or_duplicate_archive_refuses(self):
        for source in (b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":1} trailing'):
            with self.assertRaises(ValueError):extract_definition(source,'/a')


if __name__=='__main__':unittest.main()
