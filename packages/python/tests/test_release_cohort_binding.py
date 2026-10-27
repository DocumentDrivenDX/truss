# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure controls binding the active HF corpus to the package source cohort."""

import hashlib
import json
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / 'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json'
PROJECT = ROOT / 'packages/python/pyproject.toml'
NATIVE_MANIFEST = ROOT / 'packages/python/src/truss/_catalog_runtime/manifest.json'


class ReleaseCohortBindingTests(unittest.TestCase):
    def test_hf_cohort_matches_active_package_and_native_source(self):
        cohort = json.loads(CORPUS.read_bytes())
        project = tomllib.loads(PROJECT.read_text())
        query_requirement = project['project']['optional-dependencies']['query'][0]
        self.assertTrue(query_requirement.startswith('umf-weft=='))
        compiler_version = query_requirement.removeprefix('umf-weft==')

        self.assertEqual(cohort['toolkitVersion'], project['project']['version'])
        self.assertEqual(cohort['compilerVersion'], compiler_version)
        self.assertEqual(
            cohort['nativeManifestSha256'],
            hashlib.sha256(NATIVE_MANIFEST.read_bytes()).hexdigest(),
        )


if __name__ == '__main__':
    unittest.main()
