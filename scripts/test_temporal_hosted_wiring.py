# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual YAML selection and deferred-input refusal; no native capability fabricated."""
import ast
from hashlib import sha256
import importlib.util
import itertools
import json
from pathlib import Path
import re
import subprocess
import textwrap
import tempfile
import unittest
from zipfile import ZipFile
import yaml

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('temporal_hosted_input',ROOT/'scripts/prepare-temporal-hosted-input.py')
hosted=importlib.util.module_from_spec(spec);spec.loader.exec_module(hosted)
FLAGS=('released_runtime_probe','weft_abi12_probe','temporal_scalar_probe','temporal_native_probe','temporal_candidate_probe')


def condition(expression,flags):
    text=expression.removeprefix('${{').removesuffix('}}').strip()
    text=text.replace('&&',' and ').replace('||',' or ');text=re.sub(r'!(?!=)',' not ',text).strip()
    def value(node):
        if isinstance(node,ast.BoolOp):return all(value(v) for v in node.values) if isinstance(node.op,ast.And) else any(value(v) for v in node.values)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):return not value(node.operand)
        if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='inputs':return flags[node.attr]
        raise AssertionError('Unreviewed selector expression '+ast.dump(node))
    return value(ast.parse(text,mode='eval').body)


class TemporalHostedWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.workflow=yaml.load((ROOT/'.github/workflows/python-runtime.yml').read_text(),Loader=yaml.BaseLoader)
    def test_all_flags_default_false_and_actual_yaml_jobs_are_exclusive(self):
        inputs=self.workflow['on']['workflow_dispatch']['inputs'];jobs=self.workflow['jobs']
        self.assertEqual({name:inputs[name]['default'] for name in FLAGS},{name:'false' for name in FLAGS})
        names=('released-runtime','weft-abi12-probe','temporal-scalar-probe','temporal-native-probe','temporal-candidate')
        for bits in itertools.product((False,True),repeat=len(FLAGS)):
            flags=dict(zip(FLAGS,bits));selected=[name for name in names if condition(jobs[name]['if'],flags)]
            with self.subTest(flags=flags):
                if flags[FLAGS[-1]]:self.assertEqual(selected,['temporal-candidate'])
                elif sum(bits)==1:self.assertEqual(selected,[names[bits.index(True)]])
                else:self.assertEqual(selected,[])
    def test_selected_mixed_or_deferred_phase_is_refused_before_inputs_or_pg(self):
        for phase in ('intake','inventory','qualify119'):
            self.assertEqual(hosted.validate_selector(True,phase,[False]*4),phase)
            for bits in itertools.product((False,True),repeat=4):
                if any(bits):
                    with self.subTest(phase=phase,legacy=bits),self.assertRaises(ValueError):hosted.validate_selector(True,phase,bits)
        for phase in ('none','',None):
            with self.subTest(phase=phase),self.assertRaises(ValueError):hosted.validate_selector(True,phase,[False]*4)
        with self.assertRaises(ValueError):hosted.validate_selector(False,'inventory',[False]*4)
    def test_one_linux_python311_job_no_matrix_serial_inventory_and_always_artifacts(self):
        job=self.workflow['jobs']['temporal-candidate'];self.assertEqual(job['runs-on'],'ubuntu-24.04');self.assertNotIn('strategy',job)
        self.assertTrue(any(step.get('with',{}).get('python-version')=='3.11' for step in job['steps']))
        inventory=next(s for s in job['steps'] if s.get('name','').startswith('Capture exactly two'))
        self.assertIn('for zone in UTC America/New_York',inventory['run']);self.assertNotIn('qualify-temporal-native.py',inventory['run'])
        campaign=next(s for s in job['steps'] if s.get('name','').startswith('Execute only'))
        self.assertIn("'qualify119'",campaign['if']);self.assertIn('--execute --admission',campaign['run'])
        upload=job['steps'][-1];self.assertEqual(upload['if'],'always()');self.assertIn('actions/upload-artifact',upload['uses'])
    def test_unfilled_template_and_unsealed_identities_refuse_without_output(self):
        template=json.loads((ROOT/'docs/helix/04-build/evidence/temporal-native/hosted-admission-templates/hosted-input.deferred.json').read_bytes())
        for ready in (False,True):
            with self.subTest(ready=ready),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);archive=root/'inputs.zip';manifest={**template,'ready':ready,'phase':'inventory'}
                with ZipFile(archive,'w') as z:z.writestr('hosted-input.json',json.dumps(manifest))
                with self.assertRaises(ValueError):hosted.prepare(archive,sha256(archive.read_bytes()).hexdigest(),root/'out','inventory')
                self.assertFalse((root/'out').exists())
    def test_digest_and_path_refusals_do_not_allow_placeholder_or_escape(self):
        for value in (None,'','0'*64,'A'*64,'deferred'):
            with self.subTest(value=value),self.assertRaises(ValueError):hosted.digest(value)
        for value in (None,'.','..','../escape','/absolute','wheelhouse/../escape','wheel\nname','a\\b'):
            with self.subTest(value=value),self.assertRaises(ValueError):hosted.relative(value)

    def test_actual_candidate_shell_and_embedded_python_parse(self):
        parsed_python=0
        for step in self.workflow['jobs']['temporal-candidate']['steps']:
            if 'run' not in step:continue
            with self.subTest(step=step['name']):
                subprocess.run(['bash','-n'],input=step['run'],text=True,check=True,capture_output=True)
                for code in re.findall(r"<<'PYCODE'\n(.*?)\nPYCODE",step['run'],re.S):
                    ast.parse(textwrap.dedent(code));parsed_python+=1
        self.assertEqual(parsed_python,4)
        ast.parse((ROOT/'scripts/prepare-temporal-hosted-input.py').read_text())

    def test_candidate_installs_original_wheels_without_dependency_suppression(self):
        steps=self.workflow['jobs']['temporal-candidate']['steps']
        install=next(s['run'] for s in steps if s.get('name','').startswith('Install one fresh'))
        self.assertIn('--no-index --only-binary=:all:',install)
        self.assertIn('"$TN_CAPTURE_WHEEL[local,native,query,typed-sdk]"',install)
        self.assertIn('--verify-installed',install)
        for forbidden in ('--no-deps','--force-reinstall','--ignore-installed','--no-build-isolation'):
            self.assertNotIn(forbidden,install)
        all_commands='\n'.join(s.get('run','') for s in steps)
        for forbidden in ('cargo build','maturin build','twine upload','gh workflow run','pip wheel'):
            self.assertNotIn(forbidden,all_commands)

    def test_original_runtime_is_dispatch_only_not_an_automatic_gate(self):
        original=subprocess.check_output(['git','show','34a4a4a31ba674438e70df26f39ef9e20255ea0f:.github/workflows/python-runtime.yml'],cwd=ROOT,text=True)
        before=yaml.load(original,Loader=yaml.BaseLoader)
        self.assertEqual(set(before['on']),{'workflow_dispatch'})
        self.assertEqual(set(self.workflow['on']),set(before['on']))

    def test_existing_automatic_boundary_and_publisher_gates_preserved(self):
        for name in ('python-boundaries.yml','pypi-validation.yml'):
            path='.github/workflows/'+name
            with self.subTest(workflow=name):
                original=subprocess.check_output(['git','show','34a4a4a31ba674438e70df26f39ef9e20255ea0f:'+path],cwd=ROOT)
                self.assertEqual((ROOT/path).read_bytes(),original)
                workflow=yaml.load(original,Loader=yaml.BaseLoader)
                self.assertIn('push',workflow['on']);self.assertIn('pull_request',workflow['on'])
                self.assertEqual(workflow['on']['push']['branches'],['main'])
                for job in workflow['jobs'].values():self.assertNotIn('if',job)
                if name=='python-boundaries.yml':
                    commands=[step.get('run') for step in workflow['jobs']['boundaries']['steps']]
                    self.assertIn('python3 scripts/check-module-boundaries.py',commands)
                    self.assertIn('python3 scripts/check-module-boundaries-controls.py',commands)
                    self.assertIn('packages/python/**',workflow['on']['pull_request']['paths'])

    def test_component_intake_is_explicit_and_cannot_fall_through_to_pg(self):
        job=self.workflow['jobs']['temporal-candidate']
        fetch=next(step['run'] for step in job['steps'] if step.get('name','').startswith('Fetch retained'))
        self.assertIn('if [ "$TN_PHASE" = intake ]; then',fetch)
        self.assertIn('prepare-temporal-component-intake.py --execute',fetch)
        self.assertIn('if [ "$TN_PHASE" = intake ]; then exit 0; fi',fetch)
        for step in job['steps']:
            if step.get('name','').startswith(('Capture exactly two','Prepare the separate','Execute only')):
                self.assertIn('if',step)
                self.assertNotIn("'intake'",step['if'])
        install=next(step for step in job['steps'] if step.get('name','').startswith('Install one fresh'))
        self.assertEqual(install['if'],"${{ inputs.temporal_candidate_phase != 'intake' }}")
        self.assertEqual(self.workflow['on']['workflow_dispatch']['inputs']['temporal_candidate_phase']['default'],'none')
