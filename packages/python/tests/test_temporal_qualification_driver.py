# SPDX-License-Identifier: MIT OR Apache-2.0
"""Qualification driver sensitivity only; no native server or build is started."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from temporal_qualification_support import collect_exact,strict_result,RecordedResult,OwnedNativeCleanup

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('temporal_qualification_driver',ROOT/'scripts/qualify-temporal-native.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)


class TemporalQualificationDriverTests(unittest.TestCase):
    def result(self,n=2):
        result=unittest.TestResult();result.testsRun=n;return result

    def test_exact_case_counts_zero_skip_xfail_xpass_and_inventory_cleanup_required(self):
        expected=['one','two'];result=self.result()
        self.assertTrue(strict_result(result,expected,expected,inventory_verified=True,cleanup_confirmed=True)['passed'])
        for name in ('skipped','expectedFailures','unexpectedSuccesses','failures','errors'):
            result=self.result();getattr(result,name).append(('case','detail'))
            with self.subTest(field=name):self.assertFalse(strict_result(result,expected,expected,inventory_verified=True,cleanup_confirmed=True)['passed'])
        for expected,observed,n,inventory,cleanup in ((['one','two'],['two','one'],2,True,True),
                (['one','two'],['one'],1,True,True),(['one','one'],['one','one'],2,True,True),
                ([],[],0,True,True),(['one','two'],['one','two'],2,False,True),(['one','two'],['one','two'],2,True,False)):
            with self.subTest(expected=expected,observed=observed):
                self.assertFalse(strict_result(self.result(n),expected,observed,inventory_verified=inventory,cleanup_confirmed=cleanup)['passed'])

    def test_collection_refuses_module_class_expansion_duplicates_or_missing_case(self):
        name='temporal_driver_unit_fixture';module=types.ModuleType(name)
        class UnitCase(unittest.TestCase):
            def test_one(self):pass
            def test_two(self):pass
        UnitCase.__module__=name;UnitCase.__qualname__='UnitCase';module.UnitCase=UnitCase
        with patch.dict(sys.modules,{name:module}):
            selector=name+'.UnitCase.test_one'
            self.assertEqual(collect_exact([selector]).countTestCases(),1)
            for invalid in ([name],[name+'.UnitCase'],[selector,selector],[name+'.UnitCase.missing']):
                with self.subTest(invalid=invalid),self.assertRaises(ValueError):collect_exact(invalid)

    def test_governed_census_preserves_original_hf_cases_and_ordinary_overlap_only_once(self):
        selected=driver.ledger();self.assertEqual(sum(selected['expectedCounts'].values()),130)
        self.assertEqual(selected['expectedCounts']['journal'],10)
        self.assertEqual(sum(v for k,v in selected['expectedCounts'].items() if k not in ('journal','public55')),119)
        self.assertEqual(selected['expectedCounts']['public55'],1)
        original=json.loads((ROOT/'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json').read_bytes())
        self.assertEqual([(r['id'],r['test']) for r in selected['stages']['hf']],[(r['id'],r['test']) for r in original['cases']])
        self.assertEqual(len(selected['ordinaryCoveredOnceByHF']),3)
        self.assertTrue(set(selected['ordinaryCoveredOnceByHF'])<={r['test'] for r in selected['stages']['hf']})
        self.assertFalse(set(selected['ordinaryCoveredOnceByHF'])&{r['test'] for r in selected['stages']['ordinary']})

    def test_isolated_fixture_delete_requires_status3_and_original_pid_absent_before_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'owned';data=root/'data';data.mkdir(parents=True);(data/'PG_VERSION').write_text('18')
            output=Path(directory)/'cleanup.json';monitor=OwnedNativeCleanup([],output);events=[]
            monitor.records[str(data.resolve())]={'dataDirectory':str(data.resolve()),'pgCtl':'/unit/pg_ctl','originalPostmasterPid':42,'confirmed':False,'dataDeleted':False}
            def status(*args,**kw):events.append('status');self.assertTrue(data.exists());return subprocess.CompletedProcess(args[0],3,'not running','')
            def absent(pid,signal):events.append('original-pid');self.assertTrue(data.exists());raise ProcessLookupError()
            with patch('temporal_qualification_support.subprocess.run',side_effect=status),patch('temporal_qualification_support.os.kill',side_effect=absent),monitor:
                shutil.rmtree(root)
            self.assertEqual(events,['status','original-pid']);self.assertFalse(root.exists());self.assertTrue(monitor.confirmed)
            proof=json.loads(output.read_bytes())['clusters'][0]
            self.assertEqual((proof['pgCtlStatus'],proof['originalPostmasterPidAbsent'],proof['dataDeleted']),(3,True,True))

    def test_unknown_pg_directory_is_retained_without_claiming_observed_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'owned';data=root/'data';data.mkdir(parents=True);(data/'PG_VERSION').write_text('18')
            monitor=OwnedNativeCleanup([],Path(directory)/'cleanup.json')
            with monitor,self.assertRaisesRegex(RuntimeError,'Unobserved PG'):
                shutil.rmtree(root)
            self.assertTrue(data.exists());self.assertFalse(monitor.confirmed)

    def test_live_or_uncertain_original_pid_never_allows_delete(self):
        for code,pid_error in ((0,ProcessLookupError()),(3,None),(3,PermissionError())):
            with self.subTest(code=code,pidError=type(pid_error).__name__),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)/'owned';data=(root/'data').resolve();data.mkdir(parents=True);(data/'PG_VERSION').write_text('18')
                monitor=OwnedNativeCleanup([],Path(directory)/'cleanup.json')
                monitor.records[str(data)]={'dataDirectory':str(data),'pgCtl':'/unit/pg_ctl','originalPostmasterPid':42,'confirmed':False,'dataDeleted':False}
                with patch('temporal_qualification_support.subprocess.run',return_value=subprocess.CompletedProcess([],code,'','')), \
                     patch('temporal_qualification_support.os.kill',side_effect=pid_error),self.assertRaises(RuntimeError):
                    with monitor:shutil.rmtree(root)
                self.assertTrue(data.exists());self.assertFalse(monitor.confirmed)

    def test_missing_actual_artifact_enrollment_refuses_before_runtime_initialization(self):
        import release_cohort
        from truss import LocalPostgres
        selected=release_cohort.load_cohort();selected['qualified']=None
        original=release_cohort.load_cohort
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'unsealed.json';path.write_text(json.dumps(selected))
            def unsealed(*args,**kwargs):return original(path,**kwargs)
            with patch.object(driver,'assert_qualification_checkout',return_value={}),patch.object(release_cohort,'load_cohort',side_effect=unsealed),patch.object(driver.sys,'platform','linux'),patch.object(driver.platform,'machine',return_value='x86_64'), \
                 patch.object(LocalPostgres,'__enter__') as started, \
                 self.assertRaisesRegex(ValueError,'identities deferred'):
                driver.preflight({'schema':'truss-temporal-qualification-input/1'})
            started.assert_not_called()

    def test_public055_fixture_is_bound_to_immutable_publication_and_original_runtime_constraints(self):
        from test_temporal_public055_refusal_native import provenance,PUBLIC055_WHEEL_SHA256,PUBLIC055_NATIVE_SHA256
        selected=provenance()
        publication=json.loads((ROOT/selected['publishedProof']).read_bytes())
        wheel=next(row for row in publication['assets'] if row['name']==selected['wheelFilename'])
        self.assertEqual(wheel['sha256'],PUBLIC055_WHEEL_SHA256)
        self.assertEqual(wheel['bytes'],selected['wheelBytes'])
        self.assertTrue(publication['release']['is_immutable'])
        self.assertEqual(selected['nativeManifestSHA256'],PUBLIC055_NATIVE_SHA256)
        self.assertEqual(selected['requestedExtras'],['local','native'])
        self.assertEqual(selected['constraintsSHA256'],'cbc86dce6b1241d367798d37d5eebfab436b477b5e1c5bc27b12c1bbcdcf2889')
        self.assertEqual(len(selected['dependencyPins311Linux']),13)
        self.assertFalse(set(selected['dependencyPins311Linux'])&set(selected['forbiddenOwnerDistributions']))
        self.assertEqual(selected['dependencyPins311Linux']['mini-racer'],'0.14.1')

    def test_public055_seed_retains_original_api_sequence_except_bounded_install_keyword(self):
        import ast
        import copy
        original=ast.parse((ROOT/'packages/python/tests/runtime_migration_fixture.py').read_text())
        authored=ast.parse((ROOT/'packages/python/tests/public055_seed_fixture.py').read_text())
        before=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='seed')
        after=copy.deepcopy(next(n for n in authored.body if isinstance(n,ast.FunctionDef) and n.name=='seed'))
        installation=[n for n in ast.walk(after) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='install_in_transaction']
        self.assertEqual(len(installation),1)
        self.assertEqual([(k.arg,ast.literal_eval(k.value)) for k in installation[0].keywords],[('operation_timeout_ms',180000)])
        installation[0].keywords=[]
        self.assertEqual(ast.dump(before,include_attributes=False),ast.dump(after,include_attributes=False))

    def test_public055_snapshot_retains_full_acl_names_without_changing_public054(self):
        from unittest.mock import MagicMock
        from test_temporal_public055_refusal_native import TemporalPublic055RefusalTests
        from test_temporal_catalog_transport_native import TemporalCatalogTransportTests
        from truss import _migration_verify
        connection=MagicMock();cursor=connection.cursor.return_value.__enter__.return_value
        prefix='same_native_routine_'+('x'*70)
        full=[['routine',prefix+'(text,integer)','EXECUTE'],['routine',prefix+'(text,bigint)','EXECUTE']]
        original={'tables':{'retained':'exact source'},'acl':[['routine',prefix[:63],'EXECUTE']]}
        case=TemporalPublic055RefusalTests('test_public55_populated_installation_refuses_candidate_without_effects')
        with patch.object(TemporalCatalogTransportTests,'snapshot',return_value=dict(original)),patch.object(_migration_verify,'acl',return_value=full) as observed:
            actual=case.snapshot(connection)
        observed.assert_called_once_with(cursor,full_names=True)
        self.assertEqual(actual['acl'],full);self.assertEqual(actual['tables'],original['tables'])
        before=subprocess.check_output(['git','show','6e2a38e66fd6322bd04a86cb49898b48b9ef5dbf:packages/python/tests/test_temporal_catalog_transport_native.py'],cwd=ROOT)
        self.assertEqual((ROOT/'packages/python/tests/test_temporal_catalog_transport_native.py').read_bytes(),before)
