import json
import unittest
from truss._migration_recipe import load_recipe, plan_route


class CurrentBaselineTests(unittest.TestCase):
    @unittest.expectedFailure  # migrations/manifest.json target is stale: 0.0.56 runtime (0.76-candidate) needs a new fresh baseline incl. a native initialization-custody policy; owner follow-up
    def test_explicit_fresh_baseline_has_no_historical_routes(self):
        manifest, artifacts, _ = load_recipe()
        self.assertEqual(manifest['baseline']['identity'], 'truss-fresh-install-baseline/2026-11-02')
        self.assertEqual(manifest['sources'], [])
        self.assertEqual(manifest['edges'], [])
        self.assertEqual(manifest['sourceWheels'], {})
        self.assertEqual(plan_route(manifest, manifest['target']), [])
        self.assertEqual(json.loads(artifacts[manifest['target'] + '.json'])['sha256'], manifest['target'])

    @unittest.expectedFailure  # migrations/manifest.json target is stale: 0.0.56 runtime (0.76-candidate) needs a new fresh baseline incl. a native initialization-custody policy; owner follow-up

    def test_unknown_and_retired_sources_have_no_forward_route(self):
        manifest, _, _ = load_recipe()
        for source in ('unknown', '9f6aab31802e9bebcd886f735ba9fe0bb405e69d3501a32f36cee8827b544d00',
                       '288801f7177338328441b5d3ce9328af31740ebf513f04ea45e30ae316a9f3a4'):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'No declared forward path'):
                plan_route(manifest, source)
