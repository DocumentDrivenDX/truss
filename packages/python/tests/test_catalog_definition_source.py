# SPDX-License-Identifier: MIT OR Apache-2.0
import unittest
from truss._catalog_definition_source import extract_definition,extract_definitions


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

    def test_batch_exact_overlapping_unicode_and_escaped_slices(self):
        record='{"id":"R", "kind":"record", "keys":[{"id":"k", "unknown":{"雪":"✓"}}], "extensions":{"raw":1.2300e+2}}'.encode()
        field=br'{"id":"F", "kind":"field", "text":"escaped \\\" quote"}'
        original=(b' { "modules" : [ {"id":"m", "elements":['+record+b','+field+
                  b'], "relationships":[]}], "a/b":{"~key":["'+ '✓'.encode()+b'",null,true,-0.00]} } ')
        expected={'':original.strip(),'/modules/0/elements/0':record,
                  '/modules/0/elements/0/keys/0':'{"id":"k", "unknown":{"雪":"✓"}}'.encode(),
                  '/modules/0/elements/1':field,'/a~1b/~0key/0':'"✓"'.encode(),
                  '/a~1b/~0key/3':b'-0.00'}
        self.assertEqual(extract_definitions(original,tuple(expected)),expected)

    def test_batch_duplicate_requests_and_empty_collections(self):
        self.assertEqual(extract_definitions(b'{"a": []}',('/a','/a')),{'/a':b'[]'})
        self.assertEqual(extract_definitions(b'{}',()),{})

    def test_batch_invalid_archive_and_pointer_refuse(self):
        for original,pointers in ((b'{"a":1,"a":2}',('/a',)),(b'{"a":[0]}',('/a/00',)),
                                  (b'{"a":0}',('/b',)),(b'{"a":0}',('/a~2',))):
            with self.subTest(original=original,pointers=pointers):
                with self.assertRaises(ValueError):extract_definitions(original,pointers)


if __name__=='__main__':unittest.main()
