# SPDX-License-Identifier: MIT OR Apache-2.0
"""Component intake source/refusal controls; no installed native owner emulation."""
from hashlib import sha256
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('component_intake',ROOT/'scripts/prepare-temporal-component-intake.py')
intake=importlib.util.module_from_spec(spec);spec.loader.exec_module(intake)


class TemporalComponentIntakeTests(unittest.TestCase):
    def test_real_enrollment_corresponds_to_source_and_component_scope_seal(self):
        bundle=ROOT/'packages/python/src/truss/_temporal_owner'
        archive=ROOT/'docs/helix/04-build/evidence/temporal-native/component-intake-source/d526-reference-only'
        core=json.loads((archive/'manifest.json').read_bytes());weft=json.loads((archive/'compiler.json').read_bytes())
        native_path=ROOT/'packages/python/src/truss/_catalog_runtime/manifest.json';native=json.loads(native_path.read_bytes())
        seal=json.loads((ROOT/'scripts/truss-release-cohort.json').read_bytes())['qualified']
        self.assertEqual(core['sourceCommit'],'e3f38ef6f05ae636d2837f9d69f8d6805222664b')
        self.assertEqual(weft['sourceCommit'],'d52644f4b2fb5579f9a303012cfc3a98ac6c174e')
        self.assertEqual(core['sourceSha256'],sha256((bundle/'source.json').read_bytes()).hexdigest())
        self.assertEqual(core['installedFiles']['_rust_core.abi3.so'],'7716d79ae0c85ac92ba679d531c213811fe66501397b0ec0f78e8bad53c296da')
        self.assertEqual(weft['installedFiles']['weft.abi3.so'],'adbb4e4b76ea346d1e4ee8201caf845dbcd04894675159cd85a3a88a34652f2c')
        self.assertEqual(len(core['installedFiles']),72);self.assertEqual(len(weft['installedFiles']),2)
        self.assertIsNone(seal)
        self.assertFalse((bundle/'manifest.json').exists());self.assertFalse((bundle/'compiler.json').exists())
        self.assertNotIn('../_temporal_owner/manifest.json',native['files'])
        self.assertNotIn('../_temporal_owner/compiler.json',native['files'])

    def test_deferred_or_wrong_schema_input_refuses_before_build_or_output(self):
        for ready,schema in ((False,'truss-temporal-component-intake/1'),(True,'truss-temporal-hosted-input/1')):
            with self.subTest(ready=ready,schema=schema),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);archive=root/'input.zip'
                with ZipFile(archive,'w') as z:z.writestr('component-input.json',json.dumps({'schema':schema,'ready':ready}))
                with patch.object(intake,'run',side_effect=AssertionError('unexpected build/install')):
                    with self.assertRaises(ValueError):intake.extract(archive,sha256(archive.read_bytes()).hexdigest(),root/'output')
                self.assertFalse((root/'output').exists())

    def test_non_linux_execution_refuses_before_build_install_or_extract(self):
        with patch.object(intake.sys,'platform','darwin'),patch.object(intake,'extract',side_effect=AssertionError('unexpected extract')),patch.object(intake,'run',side_effect=AssertionError('unexpected subprocess')):
            with self.assertRaisesRegex(ValueError,'hosted Linux'):intake.execute(None,None,None)

    def test_intake_does_not_relax_pg_admission_or_start_a_native_database(self):
        source=(ROOT/'scripts/prepare-temporal-component-intake.py').read_text();tree=ast.parse(source)
        names={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertNotIn('LocalPostgres',names)
        self.assertIn('load_cohort(require_qualified=True)',source)
        self.assertIn("'--only-binary=:all:'",source);self.assertIn("'-m','pip','check'",source)
        for forbidden in ('--no-deps','--force-reinstall','--ignore-installed','--no-build-isolation','capture-temporal-native-inventory.py','qualify-temporal-native.py'):
            self.assertNotIn(forbidden,source)
        self.assertIn("ready=False,phase='inventory'",source)
        with self.assertRaises(ValueError):intake.hosted_module().prepare(None,None,None,'intake')

    def test_known_superseded_producer_cannot_prepare_final_enrollment(self):
        spec=importlib.util.spec_from_file_location('enrollment',ROOT/'scripts/prepare-temporal-binary-enrollment.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'output'
            with self.assertRaisesRegex(ValueError,'Known superseded d526'):
                module.prepare(None,None,None,None,module.SUPERSEDED_WEFT,output,weft_lock=None)
            self.assertFalse(output.exists())
        for value in (None,'main','0'*40,'A'*40,True):
            with self.subTest(value=value),self.assertRaises(ValueError):module.exact(value,40)

    def test_actual_original_native_capture_validates_before_any_owner_call(self):
        probe,raw,capture=intake.original_capture()
        self.assertEqual(capture['truss']['version'],'0.0.54')
        self.assertEqual(capture['weft']['version'],'0.4.51')
        self.assertEqual(capture['compilerCall']['arguments'][0],capture['compilerCall']['request'])
        self.assertGreater(probe.validate_payloads(capture),9)
        self.assertEqual(json.loads(raw)['enginePage']['checkerCall']['program'],capture['enginePage']['program'])
