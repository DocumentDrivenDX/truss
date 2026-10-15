"""Basic original compiler -> private native registration/commit/retry workflow."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

try:
    from weft import MutationCompiler
except ImportError:
    MutationCompiler = None

_ROOT = Path(__file__).resolve().parents[3]


@unittest.skipIf(MutationCompiler is None, 'Requires the original Weft mutation Python bridge')
class PreparationProgramNativeTests(unittest.TestCase):
    def test_original_compile_commit_readback_and_retry(self):
        spec = importlib.util.spec_from_file_location(
            'products_program_workflow', _ROOT / 'scripts/export-products-native-binding.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        model = _ROOT / 'docs/helix/04-build/evidence/preparation-program-20261015/original-demo-model.json'
        with tempfile.TemporaryDirectory(prefix='truss-preparation-program-') as directory:
            output = Path(directory) / 'products'
            with contextlib.redirect_stdout(io.StringIO()):
                module.run(model, output, shutil.which('bun') or 'bun',
                           bootstrap_source_epoch=True, register_action_store=True,
                           register_preparation_program=True)
            registration = json.loads((output / 'program-registration.json').read_bytes())
            self.assertFalse(registration['authority'])
            response = json.loads((output / 'program-compile-response.json').read_bytes())
            plan = json.loads(response['plan']['utf8'])
            invocation = json.loads((output / 'program-lowering-invocation.json').read_bytes())
            lowered = json.loads(invocation['response'])
            self.assertEqual(json.loads(invocation['loweringRequest'])['maxItems'], plan['limits']['maxItems'])
            self.assertEqual(lowered['bounds'], {'maxItems': 10000, 'fetchLimit': 10001})
            self.assertNotEqual(registration['programIdentity'], json.loads((output / 'receipt.json').read_bytes())['metadataSourceEpoch']['installation'])
