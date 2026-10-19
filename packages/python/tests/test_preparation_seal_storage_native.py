# SPDX-License-Identifier: MIT OR Apache-2.0
"""One basic committed private storage/products workflow on actual PG18.6."""
import contextlib
from hashlib import sha256
import importlib.util
import importlib.resources
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from truss.catalog_runtime import _release

_ROOT = Path(__file__).resolve().parents[3]


class PreparationSealStorageNativeTests(unittest.TestCase):
    def test_install_commit_private_storage_and_public_products_workflow(self):
        spec=importlib.util.spec_from_file_location('products_seal_storage_workflow',_ROOT/'scripts/export-products-native-binding.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        model=_ROOT/'packages/browser/fixtures/local-products-model.json'
        with tempfile.TemporaryDirectory(prefix='truss-preparation-seal-') as directory:
            output=Path(directory)/'products'
            with contextlib.redirect_stdout(io.StringIO()):
                module.run(model,output,shutil.which('bun') or 'bun',bootstrap_source_epoch=True,install_seal_storage=True)
            report=json.loads((output/'receipt.json').read_bytes())
            self.assertEqual(report['runtime'],_release()[0]['releaseId'])
            self.assertEqual(report['nativeObjectIds'],['1','2'])
            self.assertEqual(report['metadataSourceEpoch']['installation'],report['sealStorage']['installation'])
            seal_source=importlib.resources.files('truss').joinpath('_security_bootstrap/preparation-seal-storage.sql').read_bytes()
            self.assertEqual(report['sealStorage']['sourceSha256'],sha256(seal_source).hexdigest())
            self.assertFalse(report['sealStorage']['securityReady'])
