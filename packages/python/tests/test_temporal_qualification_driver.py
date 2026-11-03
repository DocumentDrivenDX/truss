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
        selected=driver.ledger();self.assertEqual(sum(selected['expectedCounts'].values()),119)
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
