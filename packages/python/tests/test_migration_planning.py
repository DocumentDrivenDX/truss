import json
from dataclasses import asdict, FrozenInstanceError
from pathlib import Path
import unittest
from truss.migration_planning import plan_layout_migration, Plan

ROOT = Path(__file__).resolve().parents[3]


class MigrationPlanningTests(unittest.TestCase):
    def test_shared_original_expected_results(self):
        corpus = json.loads((ROOT / 'tests/fixtures/layout-migration-planning.json').read_text())
        for vector in corpus['cases']:
            with self.subTest(case=vector['id']):
                result = plan_layout_migration(vector['manifestText'].encode(), vector['observationText'].encode(), vector['targetVersion'])
                actual = asdict(result)
                if isinstance(result, Plan):
                    actual['steps'] = list(actual['steps'])
                    for step in actual['steps']:
                        step['from'] = step.pop('from_version')
                        step['to'] = step.pop('to_version')
                self.assertEqual(actual, vector['expected'])
                with self.assertRaises(FrozenInstanceError):
                    result.scope = 'changed'
                if isinstance(result, Plan):
                    self.assertIsInstance(result.steps, tuple)
                    with self.assertRaises(FrozenInstanceError):
                        result.steps[0].recipe.identity = 'changed'

    def test_direct_input_refusals(self):
        vector = json.loads((ROOT / 'tests/fixtures/layout-migration-planning.json').read_text())['cases'][0]
        manifest, observation = vector['manifestText'].encode(), vector['observationText'].encode()
        for target in ('1' * 1048577, 'é' * 129, '\0', '\ud800', True, 1, None):
            with self.subTest(target_type=type(target)):
                self.assertEqual(plan_layout_migration(manifest, observation, target).reason, 'invalid_input')
        for original in (bytearray(manifest), memoryview(manifest), None, bytes(1048577)):
            self.assertEqual(plan_layout_migration(original, observation, '2.0.0').reason, 'invalid_input')


if __name__ == '__main__':
    unittest.main()
