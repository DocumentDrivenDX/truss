# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic explicit CLI installation and retained-directory status confirmation."""
import json
import importlib.resources
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class LocalInstallCliTests(unittest.TestCase):
    def test_install_commit_and_restart_status(self):
        parent = Path(tempfile.mkdtemp(prefix='truss-install-cli-', dir='/private/tmp'))
        directory = parent / 'postgres'
        command = [sys.executable, '-m', 'truss.cli', '--data-dir', str(directory),
                   '--install', '--probe']
        reports = []
        for _ in range(2):
            result = subprocess.run(command, check=True, capture_output=True, text=True,
                                    env=dict(os.environ))
            reports.append(json.loads(result.stdout))
            self.assertTrue((directory / 'PG_VERSION').is_file())
            self.assertFalse((directory / 'postmaster.pid').exists())
        first, second = reports
        self.assertEqual(first['scope'], 'local_truss_candidate')
        self.assertEqual(first['trussInstallation'], 'installed')
        self.assertEqual(first['serverVersion'], '18.6')
        self.assertEqual(first['installation']['action'], 'created')
        runtime_manifest=json.loads(importlib.resources.files('truss').joinpath('_catalog_runtime/manifest.json').read_bytes())
        self.assertEqual(first['installation']['releaseId'], runtime_manifest['releaseId'])
        self.assertRegex(first['installation']['releaseSha256'], r'^[0-9a-f]{64}$')
        self.assertEqual(first['installation']['layoutProfile'], runtime_manifest['layoutProfile'])
        self.assertTrue(first['installation']['ownerRole'])
        self.assertTrue(first['installation']['registrarRole'])
        self.assertEqual(second['installation']['action'], 'status_confirmed')
        self.assertEqual(second['installation']['installationId'], first['installation']['installationId'])
        self.assertEqual(second['installation']['catalogRevision'], 0)
        self.assertEqual(second['installation']['releaseId'], first['installation']['releaseId'])
        self.assertEqual(second['installation']['releaseSha256'], first['installation']['releaseSha256'])
        self.assertEqual(second['installation']['layoutProfile'], first['installation']['layoutProfile'])
        self.assertNotIn('ownerRole', second['installation'])
        self.assertNotIn('registrarRole', second['installation'])
        # Preserve source data on subprocess/assertion failures; clean only success.
        shutil.rmtree(parent)
