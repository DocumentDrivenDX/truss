# SPDX-License-Identifier: MIT OR Apache-2.0
"""Destructive cleanup refusal controls only; no native server is started."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('temporal_enrollment_probe',ROOT/'scripts/probe-temporal-native-enrollment.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


class TemporalEnrollmentProbeTests(unittest.TestCase):
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
