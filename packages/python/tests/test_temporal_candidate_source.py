# SPDX-License-Identifier: MIT OR Apache-2.0
"""Source identity only; native inventory/initializer qualification is separate."""
from hashlib import sha256
from importlib.resources import files
import json
import unittest
from truss.catalog_runtime import _release
from truss._runtime_admission import person_entrypoints


class TemporalCandidateSourceTests(unittest.TestCase):
    def test_fresh076_sources_keep_original_abi12_and_hash_actual_abi13(self):
        manifest, digest, sources = _release()
        root = files('truss').joinpath('_catalog_runtime')
        self.assertEqual(manifest['releaseId'], 'truss-catalog-runtime/0.76-temporal-candidate')
        self.assertEqual(manifest['version'], '0.76')
        self.assertEqual(digest, sha256(root.joinpath('manifest.json').read_bytes()).hexdigest())
        self.assertEqual(sha256(root.joinpath('query-abi.json').read_bytes()).hexdigest(),
                         '8266c19d6f1bc4e816d5981cd594b224f09bafd4975e1c851610fa94d1f75f96')
        descriptor = root.joinpath('query-temporal-abi.json').read_bytes()
        pin = {'identity': 'truss-postgresql-logical-query', 'version': '1.3', 'sha256': sha256(descriptor).hexdigest()}
        self.assertIn(json.dumps(pin, separators=(',', ':')), root.joinpath('query-temporal-abi.sql').read_text())
        for name in ('query-temporal.sql', 'query-temporal-sources.sql', 'query-temporal-entrypoints.sql',
                     'temporal-preparation.sql', 'temporal-cells.sql', 'temporal-storage.sql'):
            raw = root.joinpath(name).read_bytes()
            self.assertEqual(manifest['files'][name], sha256(raw).hexdigest())
            self.assertIn(raw.decode(), sources)
        # Exact helper bytes qualified by F7 Linux41550448558; new enrollment
        # still requires independent installed proof for its actual owner/ACL.
        self.assertEqual(manifest['files']['query-temporal.sql'],
                         '6b3154ba72ae0445e6c1d3d27ae0e526393ea91138782a52fc229b5af0044b90')

    def test_declared_person_sources_are_additive_and_stable(self):
        root = files('truss').joinpath('_catalog_runtime')
        ordinary = json.loads(root.joinpath('person-entrypoints.json').read_bytes())['functions']
        complete = person_entrypoints()
        self.assertEqual(list(complete[:len(ordinary)]), ordinary)
        temporal = complete[len(ordinary):]
        required={'query_temporal_binding','query_temporal_objects','query_temporal_page_objects','temporal_group_context',
                  'apply_temporal_group','apply_temporal_group_prepared','temporal_import_context','temporal_import_key_selection',
                  'temporal_import_object_identity','temporal_writer_schema_basis','get_temporal_object','page_temporal_objects'}
        self.assertTrue(required<={e['name'] for e in temporal})
        self.assertEqual({e['name']: e['volatility'] for e in temporal if e['name'].startswith('query_temporal_')}, {
            'query_temporal_binding': 'v', 'query_temporal_objects': 's', 'query_temporal_page_objects': 's'})
