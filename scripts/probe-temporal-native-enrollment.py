#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Exactly four component cases on one owned worker; no dependency adoption."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

from pgserver._commands import POSTGRES_BIN_PATH
from native_fixture import WorkerCluster, evidence_directory


class ObservedWorker(WorkerCluster):
    """Keep existing fixture/inventory policy, strengthen stop-before-delete proof."""
    def __enter__(self):
        super().__enter__()
        self.original_pid=int((self.root/'data/postmaster.pid').read_text().splitlines()[0])
        if self.original_pid<=0:raise RuntimeError('Original running worker PID required')
        return self

    def close(self):
        root=getattr(self,'root',None)
        if root is None or not root.exists():return
        proof={'directory':str(root),'confirmed':False,'dataDeleted':False}
        try:
            pid=getattr(self,'original_pid',None)
            # Startup failures may reach WorkerCluster's cleanup before our
            # __enter__ returns. Capture a still-running original PID BEFORE
            # asking pgserver to stop, never infer it from file disappearance.
            if pid is None and (root/'data/postmaster.pid').is_file():
                pid=int((root/'data/postmaster.pid').read_text().splitlines()[0])
                self.original_pid=pid
            if type(pid) is not int or pid<=0:
                raise RuntimeError('Original worker PID unavailable; retain owned data')
            if self.server is not None:self.server.cleanup()
            status=subprocess.run([str(Path(POSTGRES_BIN_PATH)/'pg_ctl'),'-D',str(root/'data'),'status'],
                                  capture_output=True,text=True,timeout=15,check=False)
            absent=False
            try:os.kill(pid,0)
            except ProcessLookupError:absent=True
            except PermissionError:pass
            proof.update(originalPostmasterPid=pid,originalPostmasterPidAbsent=absent,
                         pgCtlStatus=status.returncode,pgCtlStdout=status.stdout,pgCtlStderr=status.stderr)
            if status.returncode!=3 or not absent:
                raise RuntimeError('Worker stop uncertain; retain owned data')
            proof['confirmed']=True
            leases=root/'fixtures.jsonl'
            if leases.is_file():
                shutil.copyfile(leases,evidence_directory()/'shared-worker-fixtures.jsonl')
            shutil.rmtree(root)
            proof['dataDeleted']=not root.exists()
            self.cleanup_confirmed=proof['dataDeleted']
            self.server=None
        finally:
            print('temporal-shared-worker-cleanup '+json.dumps(proof,sort_keys=True),flush=True)
            evidence_directory().joinpath('shared-worker-cleanup.json').write_text(json.dumps(proof,indent=2)+'\n')


def main():
    evidence=evidence_directory()
    selection=('test_temporal_enrollment_native.TemporalEnrollmentNativeTests.test_fresh_installer_enrolls_original_sources_and_additive_abi',
               'test_temporal_transport_component_native')
    loader=unittest.TestLoader();suite=loader.loadTestsFromNames(selection)
    if loader.errors or suite.countTestCases()!=4:
        raise RuntimeError('Exactly four real component cases must collect: '+repr(loader.errors))
    previous=os.environ.get('TRUSS_NATIVE_WORKER')
    if previous is not None:raise RuntimeError('Probe requires its own single worker lease')
    worker=ObservedWorker()
    result=None
    inventory_verified=False
    try:
        with worker:
            os.environ.update(worker.environment())
            try:
                result=unittest.TextTestRunner(verbosity=2).run(suite)
                worker.verify_clean()
                inventory_verified=True
                evidence.joinpath('shared-worker-inventory.json').write_text(json.dumps({
                    'verifiedClean':True,'settings':worker.settings,'baseline':worker.baseline,
                    'originalPostmasterPid':worker.original_pid},indent=2)+'\n')
            finally:
                os.environ.pop('TRUSS_NATIVE_WORKER',None)
    finally:
        evidence.joinpath('selected-result.json').write_text(json.dumps({
            'selection':selection,'expectedCases':4,'testsRun':None if result is None else result.testsRun,
            'passed':bool(result is not None and result.wasSuccessful() and inventory_verified and getattr(worker,'cleanup_confirmed',False)),
            'inventoryVerified':inventory_verified,'cleanupConfirmed':getattr(worker,'cleanup_confirmed',False),
            'failures':None if result is None else len(result.failures),'errors':None if result is None else len(result.errors),
            'scope':'fresh installer and structural components ONLY; native public composition/cohort qualification OPEN'},indent=2)+'\n')
    return 0 if result is not None and result.wasSuccessful() and inventory_verified and getattr(worker,'cleanup_confirmed',False) else 1


if __name__=='__main__':raise SystemExit(main())
