"""Basic original store registration, committed observation and retry on PG18."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

_ROOT = Path(__file__).resolve().parents[3]


class ActionStoreNativeTests(unittest.TestCase):
    def test_register_commit_reopen_retry_and_public_products(self):
        spec = importlib.util.spec_from_file_location(
            'products_action_store_workflow',
            _ROOT / 'scripts/export-products-native-binding.py',
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        model = _ROOT / 'docs/helix/04-build/evidence/products-native-binding-20261014/original-demo-model.json'
        with tempfile.TemporaryDirectory(prefix='truss-action-store-') as directory:
            output = Path(directory) / 'products'
            with contextlib.redirect_stdout(io.StringIO()):
                module.run(model, output, shutil.which('bun') or 'bun',
                           bootstrap_source_epoch=True, register_action_store=True)
            report = json.loads((output / 'receipt.json').read_bytes())
            self.assertEqual(report['nativeObjectIds'], ['1', '2'])
            self.assertEqual(report['actionStore']['bindingCorrespondence'], 'matches')
            self.assertFalse(report['actionStore']['authority'])
            receipt = json.loads(bytes.fromhex(report['actionStore']['receiptHex']))
            self.assertNotEqual(receipt['logicalStoreId'], receipt['installationId'])
            self.assertNotEqual(receipt['logicalStoreId'], receipt['guardEpoch'])
            self.assertEqual(len(receipt['executorOids']), 1)
