# SPDX-License-Identifier: MIT OR Apache-2.0
"""Source-only permission/GET guard controls. No live credentials or API calls."""
import ast
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import yaml

HERE=Path(__file__).resolve().parent
# Same file can run in its proposed scripts/ target or this external review dir.
WORKFLOW=(HERE/'temporal-input-retention.yml') if (HERE/'temporal-input-retention.yml').exists() else HERE.parent/'.github/workflows/temporal-input-retention.yml'
HELPER=HERE/'retain-temporal-carrier-input.py'
spec=importlib.util.spec_from_file_location('retention_get_guard',HELPER)
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
TEST_TOKEN='source-test-placeholder-not-a-credential'


class TemporalCarrierPermissionsTests(unittest.TestCase):
    def setUp(self):
        self.auth=patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GH_TOKEN':TEST_TOKEN})
        self.auth.start();self.addCleanup(self.auth.stop)

    def test_only_one_manual_default_off_job_has_draft_read_permission(self):
        w=yaml.load(WORKFLOW.read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(w['permissions'],{'contents':'read'})
        self.assertEqual(set(w['jobs']),{'retain-only'})
        job=w['jobs']['retain-only'];self.assertEqual(job['permissions'],{'contents':'write'})
        self.assertEqual(set(w['on']),{'workflow_dispatch'})
        self.assertEqual(w['on']['workflow_dispatch']['inputs']['retain_only']['default'],'false')
        self.assertEqual(job['if'],'inputs.retain_only == true')
        self.assertEqual(job['runs-on'],'ubuntu-24.04');self.assertNotIn('strategy',job)

    def test_token_exposed_only_in_authentication_download_step_and_not_persisted(self):
        w=yaml.load(WORKFLOW.read_text(),Loader=yaml.BaseLoader);job=w['jobs']['retain-only']
        self.assertNotIn('GH_TOKEN',w.get('env',{}));self.assertNotIn('GH_TOKEN',job.get('env',{}))
        found=[]
        for step in job['steps']:
            env=step.get('env',{})
            self.assertNotIn('GITHUB_TOKEN',env)
            if 'GH_TOKEN' in env:
                found.append(step['name']);self.assertEqual(env['GH_TOKEN'],'${{ github.token }}')
            if step.get('uses','').startswith('actions/checkout@'):
                self.assertEqual(step['with']['persist-credentials'],'false')
        self.assertEqual(found,['Authenticate exact owned carrier and retain original17 entries'])
        self.assertNotIn('secrets.',WORKFLOW.read_text())

    def test_only_the_three_existing_closed_GET_endpoint_forms_are_allowed(self):
        for suffix in ('releases/433138947','releases/433138947/assets?per_page=100','releases/assets/706851888'):
            with self.subTest(endpoint=suffix):
                self.assertEqual(helper.get_command(suffix),['gh','api','--method','GET','repos/DocumentDrivenDX/truss/'+suffix])

    def test_mutation_foreign_path_query_injection_and_noncanonical_ids_refuse(self):
        bad=(None,True,'https://api.github.com/repos/foreign/repo/releases/1',
            'repos/foreign/repo/releases/1','../releases/1','git/refs/tags/test','releases',
            'releases/0','releases/01','releases/+1','releases/1.0','releases/ 1',
            'releases/18446744073709551616','releases/1/assets?per_page=101',
            'releases/1/assets?per_page=100&method=DELETE','releases/assets/1?name=payload',
            'releases/1\n--method POST','releases/1/../2','releases/latest')
        with tempfile.TemporaryDirectory() as directory:
            for suffix in bad:
                target=Path(directory)/'must-not-exist'
                with self.subTest(endpoint=suffix),patch.object(helper.subprocess,'run') as called,self.assertRaises(ValueError):
                    helper.api(suffix,target)
                called.assert_not_called();self.assertFalse(target.exists())

    def test_no_action_token_never_falls_back_to_ambient_gh_auth(self):
        for action,token in ((None,TEST_TOKEN),('false',TEST_TOKEN),('true',None),('true','')):
            env={};
            if action is not None:env['GITHUB_ACTIONS']=action
            if token is not None:env['GH_TOKEN']=token
            with self.subTest(action=action,tokenPresent=bool(token)),patch.dict(os.environ,env,clear=True),patch.object(helper.subprocess,'run') as called,self.assertRaises(ValueError):
                helper.get_command('releases/433138947')
            called.assert_not_called()

    def test_metadata_download_is_explicit_GET_only(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'original.json'
            def result(command,**kwargs):
                self.assertEqual(command,['gh','api','--method','GET','repos/DocumentDrivenDX/truss/releases/433138947'])
                kwargs['stdout'].write(b'{"scope":"source-test-only"}')
            with patch.object(helper.subprocess,'run',side_effect=result):
                self.assertEqual(helper.api('releases/433138947',target),{'scope':'source-test-only'})

    def test_binary_download_is_explicit_GET_and_keeps_original_byte_checks(self):
        body=b'source-only transport fixture';digest=sha256(body).hexdigest()
        asset={'id':706851888,'state':'uploaded','size':len(body),'digest':'sha256:'+digest}
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'original-bytes'
            def result(command,**kwargs):
                self.assertEqual(command,['gh','api','--method','GET','repos/DocumentDrivenDX/truss/releases/assets/706851888','-H','Accept: application/octet-stream'])
                kwargs['stdout'].write(body)
            with patch.object(helper.subprocess,'run',side_effect=result):helper.download(asset,target,len(body),digest)
            self.assertEqual(target.read_bytes(),body)
            with patch.object(helper.subprocess,'run') as called,self.assertRaises(ValueError):
                helper.download({**asset,'digest':'sha256:'+'f'*64},target,len(body),digest)
            called.assert_not_called()

    def test_all_controller_network_calls_route_through_closed_GET_builder(self):
        tree=ast.parse(HELPER.read_text())
        network=[]
        for fn in tree.body:
            if not isinstance(fn,ast.FunctionDef):continue
            for call in ast.walk(fn):
                if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id=='subprocess' and call.func.attr=='run':
                    network.append(fn.name)
                    arg=call.args[0]
                    self.assertTrue(isinstance(arg,ast.Name) and arg.id=='command' or isinstance(arg,ast.BinOp) and isinstance(arg.left,ast.Name) and arg.left.id=='command')
                    self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='get_command' for n in ast.walk(fn)))
        self.assertEqual(sorted(network),['api','download'])
        self.assertNotIn('gh auth',HELPER.read_text())


if __name__=='__main__':unittest.main(verbosity=2)
