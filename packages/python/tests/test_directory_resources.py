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
