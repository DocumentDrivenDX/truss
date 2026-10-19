# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic original compiler -> private native registration/commit/retry workflow."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

_ROOT = Path(__file__).resolve().parents[3]


class PreparationProgramNativeTests(unittest.TestCase):
    def test_current_010_source_refuses_missing_compiler_request(self):
        spec = importlib.util.spec_from_file_location(
            'products_program_workflow', _ROOT / 'scripts/export-products-native-binding.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        model = _ROOT / 'packages/browser/fixtures/local-products-model.json'
        with tempfile.TemporaryDirectory(prefix='truss-preparation-program-') as directory:
            output = Path(directory) / 'products'
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, 'separately supplied current compiler request'):
                    module.run(model, output, 'bun', register_preparation_program=True)
            self.assertFalse(output.exists())

    def test_legacy_models_never_reach_the_configured_compiler(self):
        from hashlib import sha256
        from truss._preparation_program import compile_preparation_program
        def artifact(value):
            raw=json.dumps(value,separators=(',',':'))
            return {'mediaType':'application/json','utf8':raw,'sha256':sha256(raw.encode()).hexdigest()}
        calls=[]
        class Compiler:
            def __init__(self,configuration):calls.append(configuration)
            def compile_json(self,request):return '{"status":"refused"}'
        for source_version,pin_version in (('0.7.0','0.7.0'),('0.8.0','0.8.0'),('0.9.0','0.9.0'),('0.8.0','0.10.0'),('0.10.0','0.10.0')):
            request={'interfaceVersion':'weft-mutation-compile/0.1.0','dialect':'weft-mutation/0.1.0',
                     'model':artifact({'umf':source_version}),'modelPin':{'umfVersion':pin_version}}
            calls.clear()
            with self.subTest(source=source_version,pin=pin_version):
                with self.assertRaisesRegex(ValueError,'compiler refused' if source_version==pin_version=='0.10.0' else 'Only current UMF'):
                    compile_preparation_program(Compiler,compiler_source_pin='a'*40,configuration=b'{}',
                        request=json.dumps(request).encode(),binding_artifact=json.dumps(artifact({})).encode(),evidence=('test',))
                self.assertEqual(len(calls),int(source_version==pin_version=='0.10.0'))
