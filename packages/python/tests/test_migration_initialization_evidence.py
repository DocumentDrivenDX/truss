import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('initialization_evidence',
    Path(__file__).resolve().parents[3] / 'scripts/check-migration-initialization-evidence.py')
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


class InitializationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.original = {'relations': [
            ['journal_runtime_horizon', 'r', 'p', False, False, None, True,
             'original bounds', 'heap', None, None]], 'routines': [['original routine']]}
        self.observed = copy.deepcopy(self.original)

    def test_retains_exact_changed_native_bounds(self):
        self.observed['relations'][0][7] = 'November bounds'
        changes = evidence.qualify(self.original, self.observed)
        self.assertEqual(changes[0]['before'][7], 'original bounds')
        self.assertEqual(changes[0]['after'][7], 'November bounds')
        self.assertEqual(self.original['relations'][0][7], 'original bounds')

    def test_unchanged_capture_has_no_fabricated_difference(self):
        self.assertEqual(evidence.qualify(self.original, self.observed), [])

    def test_other_native_changes_refuse(self):
        for surface, field, value in [('relations', 0, 'other_relation'),
                                      ('relations', 3, True),
                                      ('routines', 0, 'changed routine')]:
            with self.subTest(surface=surface, field=field):
                observed = copy.deepcopy(self.original)
                observed[surface][0][field] = value
                with self.assertRaises(ValueError):
                    evidence.qualify(self.original, observed)

    def test_missing_surface_or_row_refuses(self):
        for observed in ({'relations': self.original['relations']},
                         {**self.original, 'relations': []}):
            with self.assertRaises(ValueError):
                evidence.qualify(self.original, observed)
