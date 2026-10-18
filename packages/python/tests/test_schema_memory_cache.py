"""Pure cache identity checks for native catalog revision reuse."""
import json
import unittest
from unittest.mock import patch

from truss.contracts import ProfilePin
from truss.catalog_view import CatalogView
from truss import _schema_memory


class SchemaMemoryCacheTests(unittest.TestCase):
    def setUp(self):
        self.cache = _schema_memory._cache.copy()
        self.cache_bytes = _schema_memory._cache_bytes
        _schema_memory._cache.clear()
        _schema_memory._cache_bytes = 0
        self.addCleanup(self.restore_cache)

    def restore_cache(self):
        _schema_memory._cache.clear()
        _schema_memory._cache.update(self.cache)
        _schema_memory._cache_bytes = self.cache_bytes

    def test_reused_revision_with_different_basis_source_invalidates_view(self):
        layout = ProfilePin(identity='layout', version='1', sha256='a' * 64)
        extraction = ProfilePin(identity='extraction', version='1', sha256='b' * 64)
        calls = []

        def build(basis, selected_layout):
            calls.append(basis)
            view = CatalogView(catalog_revision=basis['revision'],
                layout_profile=selected_layout, view_profile=layout,
                consistency_evidence_sha256='c' * 64, definitions=(),
                inventory_sha256='d' * 64, extraction_profile=extraction)
            return _schema_memory.attach(view, ())

        def raw(revision, source):
            return json.dumps({'releaseId': 'release', 'releaseSha256': 'e' * 64,
                'layoutProfile': {'identity': 'layout', 'version': '1', 'sha256': 'a' * 64},
                'revision': revision, 'source': source}, separators=(',', ':')).encode()

        with patch('truss._catalog_view_build.build_catalog_view', side_effect=build):
            original = _schema_memory.cached_catalog_view(raw('1', 'original'), layout,
                expected_release='release', expected_digest='e' * 64)
            self.assertIs(_schema_memory.cached_catalog_view(raw('1', 'original'), layout,
                expected_release='release', expected_digest='e' * 64), original)

            later = _schema_memory.cached_catalog_view(raw('2', 'later'), layout,
                expected_release='release', expected_digest='e' * 64)
            self.assertIsNot(later, original)

            # A rolled-back revision number can name different source bytes.
            reused = _schema_memory.cached_catalog_view(raw('2', 'rolled-back-replacement'), layout,
                expected_release='release', expected_digest='e' * 64)
            self.assertIsNot(reused, later)
            self.assertEqual([view.catalog_revision for view in (original, later, reused)], ['1', '2', '2'])
            self.assertEqual(len(calls), 3)


if __name__ == '__main__':
    unittest.main()
