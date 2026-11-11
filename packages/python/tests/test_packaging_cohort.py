# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure packaging admission controls; synthetic bytes do not qualify a compiler."""
import ast
import hashlib
import importlib.metadata
import json
import io
import runpy
from contextlib import redirect_stdout
from zipfile import ZipFile
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import release_cohort as cohort
import publish_pypi_release as publisher
import test_verify_weft_release_wheel as historical


class PackagingCohortTests(unittest.TestCase):
    def selection(self):
        return json.loads((ROOT / 'scripts/truss-release-cohort.json').read_text())

    def qualified(self):
        row = self.selection()
        row['qualified'] = {
            'coreSourceRevision': 'a' * 40, 'weftSourceRevision': 'b' * 40,
            'nativeManifestSha256': 'c' * 64,
            'compilerCohorts': [{'platform': 'linux-x86_64', 'sourceRevision': 'b' * 40,
                                'wheelFilename': 'umf_weft-0.4.57-py3-none-any.whl',
                                'wheelSha256': 'd' * 64, 'nativeModuleSha256': 'e' * 64}],
        }
        return row

    def load(self, selection, qualified=True):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.json'
            path.write_text(json.dumps(selection))
            return cohort.load_cohort(path, require_qualified=qualified)

    def test_project_selects_exact_approved_tuple(self):
        self.assertEqual(cohort.check_project()['weft'], {'distribution': 'umf-weft', 'version': '0.4.57'})

    def test_missing_real_qualified_identity_refuses(self):
        selection=self.selection();selection['qualified']=None
        with self.assertRaisesRegex(ValueError, 'deferred'):
            self.load(selection)

    def test_current_cohort_without_c1_source_refs_refuses_specific_route(self):
        with self.assertRaisesRegex(ValueError,'Missing trusted component source refs: core'):
            cohort.component_source_refs((ROOT/'scripts/truss-release-cohort.json').read_bytes())
        for section, message in (({'weft':None},'core'),({'core':None,'weft':{}},'core'),
                                 ({'core':{},'weft':None},'weft')):
            with self.subTest(section=section), self.assertRaisesRegex(ValueError,message):
                cohort.component_source_refs(json.dumps({'componentPrerequisiteSourceRefs':section}).encode())

    def test_stage_admission_is_phase_specific_and_keeps_future_outputs_pending(self):
        from component_prerequisite_validators import REQUIRED,WEFT_ORIGINAL_CHECK_CALLS
        component={'coreC1':{name:{'validated':True} for name in REQUIRED},
            'weftSDK42':WEFT_ORIGINAL_CHECK_CALLS,
            'stagePrerequisites':{'historyDisposition':{'syntheticSourceContext':True},
                                  'lifecycle2':{'syntheticSourceContext':True},
                                  'weftOwnerSource':{'sourceCommit':'6'*40,'sourceTree':'7'*40,
                                      'canonicalCoreSourceCommit':'e'*40,'cargoLockSha256':'f'*64}}}
        inventory={'sourceIdentity':{'commit':'a'*40,'tree':'b'*40},
            'ownerClosure':{'synthetic':'owner closure'},'resourceClosure':{'synthetic':'nine source resources'},
            'weftClosure':WEFT_ORIGINAL_CHECK_CALLS}
        self.assertEqual(cohort.require_stage_admission('inventory-observation',component=component,
            records=inventory)['stage'],'inventory-observation')
        native={**inventory,'inventories':[{'zone':'UTC'},{'zone':'America/New_York'}],
            'freshBaseline':{'source':'synthetic reviewed baseline'},'campaignInputs':{'candidate':'synthetic'}}
        self.assertEqual(cohort.require_stage_admission('native-campaign',component=component,
            records=native)['stage'],'native-campaign')
        from component_prerequisite_validators import CORE_CELLS,CORE_PLATFORMS,CORE_SDK_CHECKS
        selected_core={'sourceCommit':'1'*40,'version':'0.10.10','wheelSha256':'4'*64,
            'nativeSha256':'5'*64,'qualification':{'authorityCommit':'3'*40,
                'authorityTree':'a'*40,'registrySha256':'b'*64,'admissionId':'synthetic-source-fixture'}}
        core_readiness={'profile':'core-selected-owner-readiness/1','sourceCommit':selected_core['sourceCommit'],
            'version':selected_core['version'],'wheelSha256':selected_core['wheelSha256'],
            'nativeSha256':selected_core['nativeSha256'],'authorityCommit':'3'*40,
            'platforms':CORE_PLATFORMS,'sdkChecks':CORE_SDK_CHECKS,'cells':CORE_CELLS}
        weft_readiness={'profile':'weft-0457-published-owner-proof/1','sourceCommit':'6'*40,
            'sourceTree':'7'*40,'platforms':('linux-aarch64','linux-x86_64','macos-arm64'),
            'nodeCases':14,'chromiumCases':14,'browserCases':9,
            'sourceDependencyClosure':'cargo-package-lists-and-local-dependency-bound'}
        publication={**native,'campaign130':{'expectedTotal':130,'passed':True},
            'exactTagProofs':{'runId':'7','attempt':'1','sourceCommit':'a'*40,'tag':'v0.0.56',
                'jobs':('native','package','publish'),
                'jobStepEvidence':{'native (ubuntu-24.04)':('synthetic native proof',),
                    'package':('synthetic package proof',),'publish':('synthetic exact-tag proof',)},
                'nestedReusableWorkflows':(),'releaseId':'8',
                'ownerReadiness':{'core':core_readiness,'weft':weft_readiness}},
            'selectedCore':selected_core}
        self.assertEqual(cohort.require_stage_admission('prepublication',component=component,
            records=publication)['stage'],'prepublication')
        with self.assertRaisesRegex(ValueError,'Weft owner readiness source/tree'):
            cohort.require_stage_admission('prepublication',component=component,
                records={**publication,'exactTagProofs':{**publication['exactTagProofs'],
                    'ownerReadiness':{**publication['exactTagProofs']['ownerReadiness'],
                        'weft':{**weft_readiness,'sourceCommit':'a'*40}}}})
        for key,value in (('sourceCommit','a'*40),('version','0.10.8'),('wheelSha256','e'*64),
                          ('authorityCommit','8'*40)):
            bad={**publication,'exactTagProofs':{**publication['exactTagProofs'],
                'ownerReadiness':{**publication['exactTagProofs']['ownerReadiness'],
                    'core':{**core_readiness,key:value}}}}
            with self.subTest(core_owner_key=key),self.assertRaises(ValueError):
                cohort.require_stage_admission('prepublication',component=component,records=bad)
        with self.assertRaisesRegex(ValueError,'Missing applicable native-campaign evidence: .*campaignInputs'):
            cohort.require_stage_admission('native-campaign',component=component,records=inventory)
        with self.assertRaisesRegex(ValueError,'Missing applicable prepublication evidence: .*exactTagProofs'):
            cohort.require_stage_admission('prepublication',component=component,records=native)
        for proof in ({'release':{'tag_name':'synthetic'},'ownerReadiness':publication['exactTagProofs']['ownerReadiness']},
                      {'runId':'7','attempt':'1','sourceCommit':'a'*40,'tag':'v0.0.56',
                       'jobs':('native','package','publish'),
                       'jobStepEvidence':publication['exactTagProofs']['jobStepEvidence'],
                       'nestedReusableWorkflows':(),'releaseId':'8','producerRun':None,
                       'ownerReadiness':publication['exactTagProofs']['ownerReadiness']},
                      {'runId':'7','attempt':'1','sourceCommit':'a'*40,'tag':'v0.0.56',
                       'jobs':('native','package'),'jobStepEvidence':publication['exactTagProofs']['jobStepEvidence'],
                       'nestedReusableWorkflows':(),'releaseId':'8',
                       'ownerReadiness':publication['exactTagProofs']['ownerReadiness']}):
            with self.subTest(proof=proof),self.assertRaisesRegex(ValueError,'Missing validated exact-tag'):
                cohort.require_stage_admission('prepublication',component=component,
                    records={**publication,'exactTagProofs':proof,'selectedCore':selected_core})
        with self.assertRaisesRegex(ValueError,'Unknown temporal admission stage'):
            cohort.require_stage_admission('public-consumer',component=component,records=publication)

    def test_original_cancelled_weft_run_accepts_only_pinned_successful_selected_job(self):
        cohort._require_weft_overall_outcome('41686658658','1','126094501575','cancelled')
        cohort._require_weft_overall_outcome('41686658658','1','126094501575','success')
        for run,attempt,job,conclusion in (
            ('41686658659','1','126094501575','cancelled'),
            ('41686658658','2','126094501575','cancelled'),
            ('41686658658','1','126094501576','cancelled'),
            ('41686658658','1','126094501575','failure')):
            with self.subTest(run=run,attempt=attempt,job=job,conclusion=conclusion), \
                    self.assertRaisesRegex(ValueError,'pinned cancelled overall run'):
                cohort._require_weft_overall_outcome(run,attempt,job,conclusion)

    def test_old_distribution_or_unselected_version_refuses(self):
        for key, field, value in [('weft', 'distribution', 'weft-sql'),
                                  ('weft', 'version', '0.4.56'), ('core', 'version', '0.10.7'),
                                  ('access', 'version', '0.1.0.dev9'), ('truss', 'version', '0.0.55')]:
            with self.subTest(key=key, field=field):
                selection = self.selection(); selection[key][field] = value
                with self.assertRaisesRegex(ValueError, 'identity differs'):
                    self.load(selection, qualified=False)

    def test_malformed_or_zero_source_and_hash_refuse(self):
        for field in ('coreSourceRevision', 'weftSourceRevision', 'nativeManifestSha256'):
            for value in (None, 'main', '0' * (64 if 'Sha' in field else 40)):
                row = self.qualified(); row['qualified'][field] = value
                with self.assertRaisesRegex(ValueError, 'identity required'):
                    self.load(row)

    def test_ambiguous_or_wrong_source_compiler_refuses(self):
        row = self.qualified(); row['qualified']['compilerCohorts'] *= 2
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            self.load(row)
        row = self.qualified(); row['qualified']['compilerCohorts'][0]['sourceRevision'] = 'f' * 40
        with self.assertRaisesRegex(ValueError, 'source required'):
            self.load(row)

    def test_legacy_installed_distribution_refuses(self):
        with patch.object(importlib.metadata, 'distribution', return_value=object()):
            with self.assertRaisesRegex(ValueError, 'conflicts'):
                cohort.refuse_legacy_weft()
        with patch.object(importlib.metadata, 'distribution', side_effect=importlib.metadata.PackageNotFoundError):
            cohort.refuse_legacy_weft()

    def metadata(self, query='umf-weft==0.4.57', access='umf_access==0.1.0.dev10', extra=''):
        return (f'Metadata-Version: 2.4\nName: umf-truss\nVersion: 0.0.56\n'
                f'Requires-Dist: {query}; extra == "query"\n'
                f'Requires-Dist: {access}; extra == "typed-sdk"\n{extra}\n').encode()

    def test_publisher_accepts_selected_normal_dependencies(self):
        publisher._metadata(self.metadata(), 'umf-truss', '0.0.56')

    def test_publisher_refuses_wrong_missing_duplicate_and_legacy_extras(self):
        cases = [self.metadata(query='weft-sql==0.4.51'),
                 self.metadata(access='umf_access==0.1.0.dev5'),
                 self.metadata(extra='Requires-Dist: umf-weft==0.4.56; extra == "query"\n'),
                 self.metadata(extra='Requires-Dist: weft-sql==0.4.51\n'),
                 b'Metadata-Version: 2.4\nName: umf-truss\nVersion: 0.0.56\n']
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(publisher.ReleaseError):
                publisher._metadata(raw, 'umf-truss', '0.0.56')

    def test_qualified_wheel_requires_metadata_archive_and_native_pair(self):
        verify = historical.VERIFY
        fixture = historical.VerifyWeftReleaseWheelTests()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); wheel = root / 'umf_weft-0.4.57-py3-none-any.whl'
            fixture.record_name = 'umf_weft-0.4.57.dist-info/RECORD'
            native = b'explicit synthetic compiler, not executable'
            members = {key.replace('weft_sql-0.4.48.dist-info', 'umf_weft-0.4.57.dist-info'): value
                       for key, value in fixture._members(native).items()}
            # Existing frozen test utility creates RECORD; metadata content is independently checked.
            key = 'umf_weft-0.4.57.dist-info/METADATA'
            members[key] = b'Metadata-Version: 2.4\nName: umf-weft\nVersion: 0.4.57\n'
            fixture._zip(wheel, members)
            row = self.qualified(); compiler = row['qualified']['compilerCohorts'][0]
            compiler.update(wheelSha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
                            nativeModuleSha256=hashlib.sha256(native).hexdigest())
            selection = root / 'synthetic.json'; selection.write_text(json.dumps(row))
            self.assertEqual(verify.verify_wheel(wheel, root / 'unused', selection)['status'], 'verified')
            renamed = root / 'umf_weft-0.4.57-renamed.whl'
            renamed.write_bytes(wheel.read_bytes())
            with self.assertRaisesRegex(ValueError, 'filename'):
                verify.verify_wheel(renamed, root / 'unused', selection)
            members[key] = b'Metadata-Version: 2.4\nName: weft-sql\nVersion: 0.4.57\n'
            fixture._zip(wheel, members)
            compiler['wheelSha256'] = hashlib.sha256(wheel.read_bytes()).hexdigest()
            selection.write_text(json.dumps(row))
            with self.assertRaisesRegex(ValueError, 'metadata differs'):
                verify.verify_wheel(wheel, root / 'unused', selection)
            deferred=self.selection();deferred['qualified']=None
            selection.write_text(json.dumps(deferred))
            with self.assertRaisesRegex(ValueError, 'deferred'):
                verify.verify_wheel(wheel, root / 'unused', selection)

    def test_ordinary_query_publisher_admits_only_selected_nonconflicting_distribution(self):
        # Execute just the actual admission function, without importing runtime/native modules.
        tree = ast.parse((ROOT / 'packages/python/src/truss/_query_runtime.py').read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'compiler')
        scope = {'importlib': __import__('importlib')}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<publisher-admission>', 'exec'), scope)
        native = SimpleNamespace(__version__='0.4.57', compile_truss_runtime_json=lambda: None,
                                 check_engine_read_json=lambda: None, check_engine_page_json=lambda: None)
        with patch.dict(sys.modules, {'weft': native}), patch.object(importlib.metadata, 'version', return_value='0.4.57'), patch.object(importlib.metadata, 'distribution', side_effect=importlib.metadata.PackageNotFoundError):
            self.assertIs(scope['compiler'](engine_catalog=True, engine_pages=True), native.compile_truss_runtime_json)
            with patch.object(importlib.metadata, 'distribution', return_value=object()):
                self.assertIsNone(scope['compiler']())
            with patch.object(importlib.metadata, 'version', return_value='0.4.51'):
                self.assertIsNone(scope['compiler']())
            with patch.object(importlib.metadata, 'version', side_effect=importlib.metadata.PackageNotFoundError):
                self.assertIsNone(scope['compiler']())
            native.__version__ = '0.4.51'
            self.assertIsNone(scope['compiler']())

    def test_hf_overlay_preserves_frozen_assertions_and_checks_installed_manifest(self):
        frozen = json.loads((ROOT / 'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json').read_bytes())
        selection = self.qualified()
        native_root = ROOT / 'packages/python/src/truss'
        selection['qualified']['nativeManifestSha256'] = hashlib.sha256((native_root / '_catalog_runtime/manifest.json').read_bytes()).hexdigest()
        with patch.object(cohort, 'load_cohort', return_value=selection):
            active = cohort.hf_profile(ROOT)
            with patch('importlib.resources.files', return_value=native_root):
                installed = cohort.hf_profile(ROOT, installed=True)
            self.assertEqual(active, installed)
            self.assertEqual(active['cases'], frozen['cases'])
            self.assertEqual(active['producers'], frozen['producers'])
            self.assertEqual(active['limits'], frozen['limits'])
            self.assertEqual(active['toolkitVersion'], '0.0.56')
            selection['qualified']['nativeManifestSha256'] = 'f' * 64
            with self.assertRaisesRegex(ValueError, 'native manifest differs'):
                cohort.hf_profile(ROOT)

    def test_archive_contains_selected_reader_and_identity_without_rewriting_corpus(self):
        # Synthetic identity overlay only exercises archive structure, never runs
        # the native suite or claims these compiler bytes are qualified.
        profile = json.loads((ROOT / 'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json').read_bytes())
        profile.update(toolkitVersion='0.0.56', compilerVersion='0.4.57')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'synthetic-archive.zip'
            with patch.object(cohort, 'hf_profile', return_value=profile), patch.object(sys, 'argv',
                    ['build-hf-conformance-archive.py', '--output', str(output)]), redirect_stdout(io.StringIO()):
                runpy.run_path(str(ROOT / 'scripts/build-hf-conformance-archive.py'), run_name='__main__')
            with ZipFile(output) as archive:
                for name in ('scripts/release_cohort.py', 'scripts/truss-release-cohort.json',
                             'scripts/run-hf-conformance.py', 'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json'):
                    self.assertEqual(archive.read(name), (ROOT / name).read_bytes())
                manifest = json.loads(archive.read('conformance-manifest.json'))
                self.assertEqual(manifest['toolkitVersion'], '0.0.56')
                self.assertEqual(manifest['cohortSha256'], hashlib.sha256((ROOT / 'scripts/truss-release-cohort.json').read_bytes()).hexdigest())
                self.assertIn('installed=a.installed_package', archive.read('scripts/run-hf-conformance.py').decode())

    def test_successor_postflight_preserves_ordinary_refusal_controls(self):
        text = (ROOT / '.github/workflows/publish-pypi.yml').read_text()
        self.assertIn("if tuple(map(int, record['truss_version'].split('.'))) >= (0, 0, 54):", text)
        for assertion in ("assert _wire_cell(local) is None", "lambda: PresentValue(value=local)",
                          "lambda: SequenceValue(items=(local,))", "lambda: MapEntry(key='local',value=local)",
                          "lambda: TextValue(kind='localTimestamp',text=token)", "lambda: _cell(asdict(local))",
                          "lambda: logical_object_cell(asdict(local))"):
            self.assertIn(assertion, text)
        self.assertIn("if tuple(map(int, record['truss_version'].split('.'))) < (0, 0, 56):", text)

    def test_active_release_workflow_checks_deferred_identity_before_build(self):
        text = (ROOT / '.github/workflows/release.yml').read_text()
        self.assertLess(text.index('python scripts/release_cohort.py --qualified'), text.index('python -m build'))
        self.assertNotIn("removeprefix('weft-sql==')", text)
        self.assertIn('--cohort scripts/truss-release-cohort.json', text)
        installer = (ROOT / 'scripts/install-local-runtime.py').read_text()
        self.assertIn('[local,native,query,typed-sdk,experimental-pg8000]', installer)
        self.assertNotIn('--force-reinstall', installer)


if __name__ == '__main__':
    unittest.main()
