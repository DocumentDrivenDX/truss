# SPDX-License-Identifier: MIT OR Apache-2.0
"""Destructive cleanup refusal controls only; no native server is started."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock,Mock,patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('temporal_enrollment_probe',ROOT/'scripts/probe-temporal-native-enrollment.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


class TemporalEnrollmentProbeTests(unittest.TestCase):
    def result(self,tests=4):
        result=unittest.TestResult();result.testsRun=tests
        return result

    def test_qualification_requires_exact_four_with_no_skips_or_expected_failures(self):
        self.assertTrue(probe.qualification_result(self.result(),inventory_verified=True,cleanup_confirmed=True)['passed'])
        for field in ('skipped','expectedFailures','unexpectedSuccesses','failures','errors'):
            result=self.result();getattr(result,field).append(('case','detail'))
            report=probe.qualification_result(result,inventory_verified=True,cleanup_confirmed=True)
            with self.subTest(field=field):
                self.assertFalse(report['passed'])
                self.assertEqual(report['skips' if field=='skipped' else field],1)
        for count in (0,3,5):
            with self.subTest(count=count):
                self.assertFalse(probe.qualification_result(self.result(count),inventory_verified=True,cleanup_confirmed=True)['passed'])

    def test_qualification_requires_result_inventory_and_confirmed_cleanup(self):
        for result,inventory,cleanup in ((None,True,True),(self.result(),False,True),(self.result(),True,False)):
            with self.subTest(result=result,inventory=inventory,cleanup=cleanup):
                self.assertFalse(probe.qualification_result(result,inventory_verified=inventory,cleanup_confirmed=cleanup)['passed'])

    def test_report_and_exit_use_the_same_qualification_predicate(self):
        for skipped in (False,True):
            with self.subTest(skipped=skipped),tempfile.TemporaryDirectory() as directory:
                result=self.result()
                if skipped:result.skipped.append(('deliberate skipped case','reason'))
                self.assertTrue(result.wasSuccessful(),'Sensitivity control: unittest allows skips')
                worker=MagicMock();worker.__enter__.return_value=worker
                worker.environment.return_value={'TRUSS_NATIVE_WORKER':'/nonexistent/unit-worker'}
                worker.settings={};worker.baseline={};worker.original_pid=42;worker.cleanup_confirmed=True
                with patch.object(probe,'evidence_directory',return_value=Path(directory)), \
                     patch.object(probe,'ObservedWorker',return_value=worker), \
                     patch.object(probe.unittest,'TextTestRunner') as runner,patch.dict(probe.os.environ,{},clear=True):
                    runner.return_value.run.return_value=result
                    exit_code=probe.main()
                report=json.loads((Path(directory)/'selected-result.json').read_bytes())
                self.assertEqual(exit_code,1 if skipped else 0)
                self.assertEqual(report['passed'],not skipped)
                self.assertEqual(report['skips'],int(skipped))
                self.assertEqual(report['testsRun'],4)
                worker.verify_clean.assert_called_once()

    def worker(self,root):
        worker=probe.ObservedWorker();worker.root=root;worker.original_pid=42
        worker.server=Mock();(root/'data').mkdir();(root/'data/retained').write_bytes(b'original')
        return worker

    def test_delete_requires_observed_status3_and_original_pid_absence(self):
        with tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as evidence:
            root=Path(directory)/'owned';root.mkdir();worker=self.worker(root);events=[]
            worker.server.cleanup.side_effect=lambda:events.append('stop')
            def status(*args,**kwargs):
                events.append('status');self.assertTrue(root.exists())
                return subprocess.CompletedProcess(args[0],3,stdout='not running',stderr='')
            def pid(*args):
                events.append('original-pid');self.assertTrue(root.exists());raise ProcessLookupError()
            leases=b'{"baselineRestored":true}\n';(root/'fixtures.jsonl').write_bytes(leases)
            with patch.object(probe,'evidence_directory',return_value=Path(evidence)), \
                 patch.object(probe.subprocess,'run',side_effect=status),patch.object(probe.os,'kill',side_effect=pid):
                worker.close()
            self.assertEqual(events,['stop','status','original-pid'])
            self.assertFalse(root.exists());self.assertTrue(worker.cleanup_confirmed)
            proof=json.loads((Path(evidence)/'shared-worker-cleanup.json').read_bytes())
            self.assertEqual((proof['pgCtlStatus'],proof['originalPostmasterPidAbsent'],proof['confirmed'],proof['dataDeleted']),(3,True,True,True))
            self.assertEqual((Path(evidence)/'shared-worker-fixtures.jsonl').read_bytes(),leases)

    def test_uncertain_status_or_live_original_pid_retains_data(self):
        for status,pid_error in ((0,ProcessLookupError()),(3,None),(3,PermissionError())):
            with self.subTest(status=status,pid_error=type(pid_error).__name__), \
                 tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as evidence:
                root=Path(directory)/'owned';root.mkdir();worker=self.worker(root)
                with patch.object(probe,'evidence_directory',return_value=Path(evidence)), \
                     patch.object(probe.subprocess,'run',return_value=subprocess.CompletedProcess([],status,'','')), \
                     patch.object(probe.os,'kill',side_effect=pid_error),self.assertRaises(RuntimeError):
                    worker.close()
                self.assertEqual((root/'data/retained').read_bytes(),b'original')
                proof=json.loads((Path(evidence)/'shared-worker-cleanup.json').read_bytes())
                self.assertFalse(proof['confirmed']);self.assertFalse(proof['dataDeleted'])

    def test_missing_original_pid_retains_data_before_attempting_stop(self):
        with tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as evidence:
            root=Path(directory)/'owned';root.mkdir();worker=self.worker(root);del worker.original_pid
            with patch.object(probe,'evidence_directory',return_value=Path(evidence)), \
                 patch.object(probe.subprocess,'run') as status,self.assertRaises(RuntimeError):
                worker.close()
            worker.server.cleanup.assert_not_called();status.assert_not_called()
            self.assertTrue((root/'data/retained').exists())
