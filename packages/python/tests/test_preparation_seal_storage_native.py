"""One basic committed private storage/products workflow on actual PG18.6."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

_ROOT = Path(__file__).resolve().parents[3]


class PreparationSealStorageNativeTests(unittest.TestCase):
    def test_install_commit_private_storage_and_public_products_workflow(self):
        spec=importlib.util.spec_from_file_location('products_seal_storage_workflow',_ROOT/'scripts/export-products-native-binding.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        model=_ROOT/'docs/helix/04-build/evidence/products-native-binding-20261014/original-demo-model.json'
        with tempfile.TemporaryDirectory(prefix='truss-preparation-seal-') as directory:
            output=Path(directory)/'products'
            with contextlib.redirect_stdout(io.StringIO()):
                module.run(model,output,shutil.which('bun') or 'bun',bootstrap_source_epoch=True,install_seal_storage=True)
            report=json.loads((output/'receipt.json').read_bytes())
            self.assertEqual(report['runtime'],'truss-catalog-runtime/0.66-candidate')
            self.assertEqual(report['nativeObjectIds'],['1','2'])
            self.assertEqual(report['metadataSourceEpoch']['installation'],report['sealStorage']['installation'])
            self.assertEqual(report['sealStorage']['sourceSha256'],'235f2ce982eeda53eaee09f7608a388f96a815cde5354f4ce6db9bb3091422fe')
            self.assertFalse(report['sealStorage']['securityReady'])
