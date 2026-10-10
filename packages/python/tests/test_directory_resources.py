import os
import tempfile
from pathlib import Path
import unittest
from truss._directory_resources import DirectoryResourceResolver
from truss._installation_resources import ResourceEntry


class DirectoryResourceTests(unittest.TestCase):
    def entry(self, path):
        return ResourceEntry('test', path, 'test-role', 0, '0'*64)

    def test_original_root_survives_path_replacement_and_close_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory); root = parent/'root'; root.mkdir()
            (root/'file').write_bytes(b'original')
            resolver = DirectoryResourceResolver()
            handle = resolver.resolve(self.entry('file'))
            with self.assertRaises(ValueError): handle.open('rb')
            resolver.start(root)
            try:
                root.rename(parent/'original-root'); root.mkdir()
                (root/'file').write_bytes(b'replacement')
                with handle.open('rb') as stream: self.assertEqual(stream.read(), b'original')
            finally: resolver.close()
            with self.assertRaises(ValueError): handle.open('rb')
            with self.assertRaises(ValueError): resolver.start(root)

    def test_symlink_parent_leaf_and_nonregular_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory); root = parent/'root'; root.mkdir()
            outside = parent/'outside'; outside.mkdir(); (outside/'file').write_bytes(b'outside')
            (root/'leaf').symlink_to(outside/'file')
            (root/'parent').symlink_to(outside, target_is_directory=True)
            (root/'folder').mkdir()
            os.link(outside/'file', root/'hardlink')
            resolver = DirectoryResourceResolver(); resolver.start(root)
            try:
                for path in ('leaf', 'parent/file', 'folder', 'hardlink'):
                    with self.subTest(path=path):
                        with self.assertRaises((OSError, ValueError)): resolver.resolve(self.entry(path)).open('rb')
                for path in ('../outside/file', '/absolute', 'a//file', 'a/./file'):
                    with self.assertRaises(ValueError): resolver.resolve(self.entry(path))
            finally: resolver.close()

    def test_descriptor_resolver_composes_with_pinned_bundle_capture(self):
        import json
        from hashlib import sha256
        from truss._installation_resources import capture_resource_bundle
        from truss._resource_account import BytePermitAccount
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'resources').mkdir()
            payload = b'SELECT 1;\n'; (root/'resources/storage.sql').write_bytes(payload)
            entry = ResourceEntry('storage', 'resources/storage.sql', 'generated-storage', len(payload), sha256(payload).hexdigest())
            index = json.dumps({'interface':'truss-python-resources/0.1.0','releaseId':'test-release',
                                'entries':[{'id':entry.id,'path':entry.path,'role':entry.role,'byteLength':entry.byte_length,'sha256':entry.sha256}]}).encode()
            (root/'index.json').write_bytes(index)
            index_entry = ResourceEntry('index', 'index.json', 'index', len(index), sha256(index).hexdigest())
            resolver = DirectoryResourceResolver(); producer = object()
            resolver.start(root)
            try:
                account = BytePermitAccount(producer, 8192, 8192, 20)
                bundle = capture_resource_bundle(resolver.resolve(index_entry), len(index), sha256(index).hexdigest(),
                                                 'test-release', (entry,), resolver.resolve, 4096, 1, 1024, account, producer)
                self.assertEqual(bundle.index.original, index)
                self.assertEqual(bundle.resources[0].original, payload)
                self.assertIs(bundle.resources[0].account, account)
                (root/'resources/storage.sql').unlink()
                (root/'resources/storage.sql').symlink_to(root/'index.json')
                failed = BytePermitAccount(producer, 8192, 8192, 20)
                with self.assertRaises(OSError):
                    capture_resource_bundle(resolver.resolve(index_entry), len(index), sha256(index).hexdigest(),
                                            'test-release', (entry,), resolver.resolve, 4096, 1, 1024, failed, producer)
                self.assertTrue(failed.snapshot(producer)[3])
                self.assertEqual(bundle.resources[0].original, payload)
            finally: resolver.close()
