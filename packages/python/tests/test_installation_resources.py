"""Pinned resource capture against real files; no native install qualification."""
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from truss._installation_resources import capture_resource
from truss._resource_account import BytePermitAccount


class ResourceCaptureTests(unittest.TestCase):
    def test_real_file_capture_retains_verified_bytes_after_change(self):
        producer = object(); account = BytePermitAccount(producer, 100, 100, 10)
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / 'original.sql'
            original = b'SELECT 1;\n'; resource.write_bytes(original)
            captured = capture_resource(resource, len(original), sha256(original).hexdigest(), 100, account, producer)
            resource.write_bytes(b'SELECT 2;\n')
            self.assertEqual(captured.original, original)
            self.assertIs(captured.account, account)
            self.assertEqual(account.snapshot(producer), (len(original)+1, 0, len(original)+1, False))
            allocation = captured.allocation
            del captured
            account.release(producer, allocation)
            self.assertEqual(account.snapshot(producer), (0, 0, len(original)+1, False))

    def test_missing_changed_truncated_appended_resources_quarantine_once(self):
        original = b'original'; digest = sha256(original).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / 'input'
            for replacement in (None, b'origina', b'changed!', b'originalx'):
                with self.subTest(replacement=replacement):
                    if replacement is not None: resource.write_bytes(replacement)
                    producer = object(); account = BytePermitAccount(producer, 100, 100, 10)
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        capture_resource(resource, len(original), digest, 100, account, producer)
                    self.assertEqual(account.snapshot(producer), (9, 0, 9, True))
                    with self.assertRaises(ValueError): account.reserve(producer, 1)

    def test_reservation_refusal_precedes_open_and_invalid_pin_is_inert(self):
        class Unopened:
            def open(self, mode): raise AssertionError('Must not open')
        producer = object(); account = BytePermitAccount(producer, 0, 0, 10)
        with self.assertRaises(ValueError):
            capture_resource(Unopened(), 0, sha256(b'').hexdigest(), 100, account, producer)
        self.assertEqual(account.snapshot(producer), (0, 0, 0, True))
        for length, digest in [(True, sha256(b'').hexdigest()), (0, 'A'*64), (101, '0'*64)]:
            account = BytePermitAccount(producer, 100, 100, 10)
            with self.assertRaises(ValueError):
                capture_resource(Unopened(), length, digest, 100, account, producer)
            self.assertEqual(account.snapshot(producer), (0, 0, 0, False))


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
