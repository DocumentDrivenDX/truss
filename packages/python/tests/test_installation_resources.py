# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pinned resource capture against real files; no native install qualification."""
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from truss._installation_resources import capture_resource


class ResourceCaptureTests(unittest.TestCase):
    def test_capture_preserves_original_and_rejects_changed_files(self):
        original = b'SELECT 1;\n'
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / 'input'
            resource.write_bytes(original)
            captured = capture_resource(resource, len(original), sha256(original).hexdigest(), 100)
            for replacement in (original[:-1], b'x' * len(original), original + b'x'):
                resource.write_bytes(replacement)
                with self.assertRaises(ValueError):
                    capture_resource(resource, len(original), sha256(original).hexdigest(), 100)
                self.assertEqual(captured.original, original)
    def test_invalid_limit_and_digest_do_not_open(self):
        class Unopened:
            def open(self, mode): raise AssertionError('opened')
        for length, digest in ((True, '0'*64), (101, '0'*64), (0, 'bad')):
            with self.assertRaises(ValueError):
                capture_resource(Unopened(), length, digest, 100)


class ResourceIndexTests(unittest.TestCase):
    ORIGINAL = (b'{"interface":"truss-python-resources/0.1.0","releaseId":"release-1",'
                b'"entries":[{"id":"storage","path":"resources/storage.sql","role":"generated-storage",'
                b'"byteLength":10,"sha256":"' + b'0'*64 + b'"}]}')

    def decode(self, original, **options):
        from truss._installation_resources import decode_resource_index, ResourceEntry
        arguments = dict(expected_sha256=sha256(original).hexdigest(), expected_release='release-1',
                         expected_entries=(ResourceEntry('storage', 'resources/storage.sql', 'generated-storage', 10, '0'*64),),
                         maximum_index_bytes=1024, maximum_entries=1, maximum_total_bytes=10)
        arguments.update(options)
        return decode_resource_index(original, **arguments)

    def test_original_closed_membership_and_independent_pin(self):
        entries = self.decode(self.ORIGINAL)
        self.assertEqual(entries[0].path, 'resources/storage.sql')
        with self.assertRaises(AttributeError): entries[0].path = 'changed'
        with self.assertRaises(ValueError): self.decode(self.ORIGINAL, expected_sha256='f'*64)
        with self.assertRaises(ValueError): self.decode(self.ORIGINAL, expected_entries=())
        with self.assertRaises(ValueError): self.decode(self.ORIGINAL.replace(b'release-1', b'release-2'))

    def test_registered_length_cannot_alias_boolean_or_float(self):
        from truss._installation_resources import ResourceEntry
        original = self.ORIGINAL.replace(b'"byteLength":10', b'"byteLength":1')
        for length in (True, 1.0):
            with self.subTest(length=length):
                expected = (ResourceEntry('storage', 'resources/storage.sql',
                                         'generated-storage', length, '0'*64),)
                with self.assertRaisesRegex(ValueError, 'Exact registered resource length'):
                    self.decode(original, expected_entries=expected)
        exact = (ResourceEntry('storage', 'resources/storage.sql',
                               'generated-storage', 1, '0'*64),)
        self.assertEqual(self.decode(original, expected_entries=exact), exact)

    def test_duplicate_and_unsafe_closed_entries(self):
        mutations = [self.ORIGINAL.replace(b'"releaseId":"release-1"', b'"releaseId":"release-1","releaseId":"release-1"'),
                     self.ORIGINAL.replace(b'"byteLength":10', b'"byteLength":true'),
                     self.ORIGINAL.replace(b'"byteLength":10', b'"byteLength":10.0'),
                     self.ORIGINAL.replace(b'"byteLength":10', b'"byteLength":NaN'),
                     self.ORIGINAL.replace(b'"byteLength":10', b'"byteLength":-1'),
                     self.ORIGINAL.replace(b'"byteLength":10', b'"byteLength":11'),
                     self.ORIGINAL.replace(b'"role":"generated-storage"', b'"role":"foreign-role"'),
                     self.ORIGINAL.replace(b'"entries":', b'"unknown":false,"entries":')]
        for path in (b'/absolute', b'../parent', b'a/../b', b'a//b', b'a/./b', b'a\\\\b', b'C:/file', b'a/\\u0000'):
            mutations.append(self.ORIGINAL.replace(b'resources/storage.sql', path))
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError): self.decode(mutation)

    def test_original_bounds_and_duplicate_membership(self):
        for options in ({'maximum_index_bytes':len(self.ORIGINAL)-1}, {'maximum_entries':0},
                        {'maximum_total_bytes':9}, {'maximum_total_bytes':True}):
            with self.assertRaises(ValueError): self.decode(self.ORIGINAL, **options)
        entry = self.ORIGINAL[self.ORIGINAL.index(b'[{')+1:-2]
        duplicate = self.ORIGINAL[:-2]+b','+entry+b']}'
        with self.assertRaises(ValueError): self.decode(duplicate, maximum_entries=2, maximum_total_bytes=20)


class ResourceBundleTests(unittest.TestCase):
    def test_complete_bundle_retains_originals_and_refuses_late_failure(self):
        import json
        from truss._installation_resources import ResourceEntry, capture_resource_bundle
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = b'first'; b = b'second'
            entries = (ResourceEntry('a', 'resources/a', 'storage', len(a), sha256(a).hexdigest()),
                       ResourceEntry('b', 'resources/b', 'verifier', len(b), sha256(b).hexdigest()))
            index = json.dumps({'interface':'truss-python-resources/0.1.0','releaseId':'test-release',
                                'entries':[{'id':e.id,'path':e.path,'role':e.role,'byteLength':e.byte_length,'sha256':e.sha256} for e in entries]}).encode()
            (root/'index').write_bytes(index); (root/'a').write_bytes(a); (root/'b').write_bytes(b)
            calls = []
            def resolve(entry):
                calls.append(entry.id)
                return {'a':root/'a', 'b':root/'b'}[entry.id]
            def run(expected=entries):
                return capture_resource_bundle(root/'index', len(index), sha256(index).hexdigest(),
                                               'test-release', expected, resolve, 4096, 2, 100)
            captured = run()
            self.assertEqual([r.original for r in captured.resources], [a,b])
            (root/'b').write_bytes(b'changed')
            self.assertEqual(captured.resources[1].original, b)
            with self.assertRaises(ValueError): run()
            self.assertEqual(calls, ['a','b','a','b'])
            calls.clear()
            with self.assertRaises(ValueError): run(entries[:1])
            self.assertEqual(calls, [])
