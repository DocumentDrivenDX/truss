# SPDX-License-Identifier: MIT OR Apache-2.0
"""Component intake source/refusal controls; no installed native owner emulation."""
from hashlib import sha256
import ast
import copy
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

    def test_final_r_original_component_records_bind_tree_lock_stages_and_sdk(self):
        spec=importlib.util.spec_from_file_location('final_enrollment',ROOT/'scripts/prepare-temporal-binary-enrollment.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        # Transport sensitivity fixture only: no invented module, wheel or
        # installed capability. Actual original receipts are checked separately.
        source='1'*40;tree='2'*40;core='3'*40;lock='4'*64
        pins={'wheelSha256':'5'*64,'nativeModuleSha256':'6'*64,'shimSha256':'7'*64}
        w={'schema':'weft-final-R-linux-x86-component-handoff/1','sourceCommit':source,'sourceTree':tree,
            'actualJobConclusion':'success','originalAttempt':1,'runID':42,
            'component':{'path':'component','sha256':'8'*64},'sdk42':{'path':'sdk','sha256':'9'*64},
            'installedPackaging':{'path':'packaging','sha256':'a'*64},'wheel':{'sha256':pins['wheelSha256']},
            'nativeModule':{'sha256':pins['nativeModuleSha256']},'shimSha256':pins['shimSha256'],
            'actualControls':{'temporal':14,'ordinaryPaddedRouting':5,'SDK':42}}
        component={'status':'passed','sourceCommit':source,'sourceTree':tree,'canonicalUmf':core,
            'cargoLockSha256':lock,'target':'x86_64-unknown-linux-gnu','workflowCommit':source,
            'producerRunId':42,'producerRunAttempt':'1','temporalCases':14,'routingControls':5,'sdkControls':42,
            'sdkReportSha256':'9'*64,'packagingReportSha256':'a'*64,**pins,
            'stageResults':[{'name':n,'exitCode':0} for n in ('normal-install','pip-check','packaging','native-origin','temporal14','routing5','sdk42')]}
        sdk={'sourceCommit':source,'version':'0.4.57','controls':42,'pinsBeforeAfter':pins,
             'checks':[{'id':name,'status':status} for name,status in
                       (('read-check','compiled'),('page-check','compiled'),
                        ('read-context-drift','blocked'),('page-context-drift','blocked'))]}
        packaging={'status':'passed','version':'0.4.57',**pins}
        records={'component':component,'sdk':sdk,'packaging':packaging}
        with patch.object(module,'record',side_effect=lambda path,digest,reader=None:records[path]):
            self.assertEqual(module.final_weft_component(w,source,core,lock),sdk)
        mutations=[('component','sourceTree','f'*40),('component','cargoLockSha256','f'*64),
            ('component','workflowCommit','f'*40),('component','producerRunId',43),
            ('component','routingControls',4),('sdk','controls',41),('packaging','status','failed'),
            ('sdk','pinsBeforeAfter',{**pins,'shimSha256':'f'*64}),
            ('component','stageResults',component['stageResults'][:-1]),
            ('component','stageResults',[{**r,'exitCode':1} for r in component['stageResults']])]
        for report,key,value in mutations:
            altered=copy.deepcopy(records);altered[report][key]=value
            with self.subTest(report=report,key=key),patch.object(module,'record',side_effect=lambda path,digest,reader=None:altered[path]),self.assertRaises(ValueError):
                module.final_weft_component(w,source,core,lock)
        for checks in (sdk['checks'][:-1],
                       [*sdk['checks'],{'id':'read-check','status':'compiled'}],
                       [{**sdk['checks'][0],'status':'blocked'},*sdk['checks'][1:]]):
            altered=copy.deepcopy(records);altered['sdk']['checks']=checks
            with self.subTest(checks=checks),patch.object(module,'record',side_effect=lambda path,digest,reader=None:altered[path]),self.assertRaises(ValueError):
                module.final_weft_component(w,source,core,lock)

    def test_final_r_reader_is_limited_to_closed_authenticated_member_refs(self):
        spec=importlib.util.spec_from_file_location('final_enrollment_reader',ROOT/'scripts/prepare-temporal-binary-enrollment.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        source='1'*40;core='3'*40;lock='4'*64
        pins={'wheelSha256':'5'*64,'nativeModuleSha256':'6'*64,'shimSha256':'7'*64}
        component={'status':'passed','sourceCommit':source,'sourceTree':'2'*40,'canonicalUmf':core,
            'cargoLockSha256':lock,'target':'x86_64-unknown-linux-gnu','workflowCommit':source,
            'producerRunId':42,'producerRunAttempt':'1','temporalCases':14,'routingControls':5,'sdkControls':42,
            'sdkReportSha256':'9'*64,'packagingReportSha256':'a'*64,**pins,
            'stageResults':[{'name':n,'exitCode':0} for n in ('normal-install','pip-check','packaging','native-origin','temporal14','routing5','sdk42')]}
        sdk={'sourceCommit':source,'version':'0.4.57','controls':42,'pinsBeforeAfter':pins,
             'checks':[{'id':name,'status':status} for name,status in
                       (('read-check','compiled'),('page-check','compiled'),
                        ('read-context-drift','blocked'),('page-context-drift','blocked'))]}
        packaging={'status':'passed','version':'0.4.57',**pins}
        payloads={'sdk':json.dumps(sdk).encode(),'packaging':json.dumps(packaging).encode()}
        component['sdkReportSha256']=sha256(payloads['sdk']).hexdigest()
        component['packagingReportSha256']=sha256(payloads['packaging']).hexdigest()
        payloads['component']=json.dumps(component).encode()
        refs={name:{'path':name,'sha256':sha256(raw).hexdigest()} for name,raw in payloads.items()}
        handoff={'schema':'weft-final-R-linux-x86-component-handoff/1','sourceCommit':source,
            'sourceTree':'2'*40,'actualJobConclusion':'success','originalAttempt':1,'runID':42,
            'component':refs['component'],'sdk42':refs['sdk'],'installedPackaging':refs['packaging'],
            'wheel':{'sha256':pins['wheelSha256']},'nativeModule':{'sha256':pins['nativeModuleSha256']},
            'shimSha256':pins['shimSha256'],'actualControls':{'temporal':14,'ordinaryPaddedRouting':5,'SDK':42}}
        seen=[]
        def reader(ref):
            seen.append(ref)
            return payloads[ref['path']]
        checked=module.final_weft_component(handoff,source,core,lock,record_reader=reader)
        self.assertEqual(checked,sdk)
        self.assertEqual(seen,[refs['component'],refs['sdk'],refs['packaging']])
        altered=copy.deepcopy(handoff);altered['sdk42']['sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'Original handoff digest differs'):
            module.final_weft_component(altered,source,core,lock,record_reader=reader)


class TemporalIntakeRuntimeProcurementTests(unittest.TestCase):
    def observe(self, runtime_download_fails):
        import release_cohort
        events=[]
        class StopObservation(RuntimeError): pass
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'intake'
            def extract(*args):
                (output/'inputs/wheelhouse').mkdir(parents=True)
                return {'wheels':{k:{'path':'wheelhouse/'+k+'.whl'} for k in ('core','access','weft')}},{'commit':'source-observation','tree':'tree-observation'}
            def run(command, log, **kwargs):
                command=[str(x) for x in command];events.append((command,Path(log).name))
                if '-m' in command and 'build' in command and '--wheel' in command:
                    (output/'dist').mkdir();(output/'dist/umf_truss-0.0.56-py3-none-any.whl').touch()
                if any(x.endswith('/install-local-runtime.py') for x in command) and runtime_download_fails:
                    raise StopObservation('canonical download/checksum failure')
                if command[1:4]==['-m','pip','install'] and '--report' in command:
                    raise StopObservation('reached normal resolver without installing')
            with patch.object(intake.sys,'platform','linux'),patch.object(intake.platform,'machine',return_value='x86_64'),patch.object(intake.sys,'version_info',(3,11)),patch.object(intake,'extract',side_effect=extract),patch.object(intake.shutil,'copytree'),patch.object(intake,'run',side_effect=run),patch.object(release_cohort,'load_cohort') as cohort:
                with self.assertRaises(StopObservation):intake.execute(None,None,output)
                cohort.assert_called_once_with(require_qualified=True)
        return events

    def test_canonical_runtime_download_precedes_normal_resolver(self):
        events=self.observe(False)
        downloads=[(i,c,log) for i,(c,log) in enumerate(events) if any(x.endswith('/install-local-runtime.py') for x in c)]
        self.assertEqual(len(downloads),1)
        i,c,log=downloads[0]
        self.assertEqual(c[1],str(ROOT/'scripts/install-local-runtime.py'))
        self.assertEqual(c[2:4],['--download-only','--wheelhouse'])
        self.assertTrue(c[4].endswith('/inputs/wheelhouse'))
        self.assertTrue(c[0].endswith('/candidate-env/bin/python'))
        self.assertEqual(log,'runtime-download.log')
        installs=[(n,c) for n,(c,_) in enumerate(events) if '--report' in c]
        self.assertEqual(len(installs),1);self.assertGreater(installs[0][0],i)
        self.assertIn('--only-binary=:all:',installs[0][1])
        self.assertIn('--find-links',installs[0][1]);self.assertNotIn('--no-deps',installs[0][1])

    def test_canonical_download_or_checksum_failure_prevents_resolver(self):
        events=self.observe(True)
        self.assertTrue(any(any(x.endswith('/install-local-runtime.py') for x in c) for c,_ in events))
        self.assertFalse(any('--report' in c for c,_ in events))
