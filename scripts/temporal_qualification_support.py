# SPDX-License-Identifier: MIT OR Apache-2.0
"""Qualification-only exact-case results and stop-before-delete custody.

No application runtime, admission, codec or dependency-selection behavior lives
here. Existing test methods and native initializer bytes execute unchanged.
"""
from contextlib import ExitStack
from pathlib import Path
import json
import os
import shutil
import subprocess
import unittest
from unittest.mock import patch


def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from flatten(item)
        else:yield item


def collect_exact(selectors):
    if type(selectors) is not list or not selectors or len(set(selectors))!=len(selectors):
        raise ValueError('Nonempty unique exact case IDs required')
    loader=unittest.TestLoader();cases=[]
    for selector in selectors:
        suite=loader.loadTestsFromName(selector);loaded=list(flatten(suite))
        if loader.errors or len(loaded)!=1 or loaded[0].id()!=selector:
            raise ValueError('Exactly the named real case must collect: '+selector+' '+repr(loader.errors))
        cases.extend(loaded)
    return unittest.TestSuite(cases)


def strict_result(result,expected,observed,*,inventory_verified,cleanup_confirmed):
    counts={'testsRun':0 if result is None else result.testsRun,
        'skips':0 if result is None else len(result.skipped),
        'expectedFailures':0 if result is None else len(result.expectedFailures),
        'unexpectedSuccesses':0 if result is None else len(result.unexpectedSuccesses),
        'failures':0 if result is None else len(result.failures),'errors':0 if result is None else len(result.errors),
        'wasSuccessful':False if result is None else result.wasSuccessful(),
        'inventoryVerified':inventory_verified,'cleanupConfirmed':cleanup_confirmed}
    counts['passed']=bool(expected and len(set(expected))==len(expected) and observed==expected
        and counts['testsRun']==len(expected) and counts['wasSuccessful']
        and not any(counts[k] for k in ('skips','expectedFailures','unexpectedSuccesses','failures','errors'))
        and inventory_verified is True and cleanup_confirmed is True)
    return counts


class RecordedResult(unittest.TextTestResult):
    """Retain exact cases/subcases and original exception class/SQLSTATE."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.started_ids=[];self.observations=[]
    def startTest(self,test):
        self.started_ids.append(test.id());super().startTest(test)
    def event(self,test,status,error=None):
        value={'id':test.id(),'status':status}
        if error is not None:
            value.update(errorClass=error[0].__module__+'.'+error[0].__qualname__,sqlState=getattr(error[1],'sqlstate',None))
        self.observations.append(value)
    def addSuccess(self,test):self.event(test,'passed');super().addSuccess(test)
    def addFailure(self,test,error):self.event(test,'failed',error);super().addFailure(test,error)
    def addError(self,test,error):self.event(test,'error',error);super().addError(test,error)
    def addSkip(self,test,reason):self.event(test,'skipped');super().addSkip(test,reason)
    def addExpectedFailure(self,test,error):self.event(test,'expectedFailure',error);super().addExpectedFailure(test,error)
    def addUnexpectedSuccess(self,test):self.event(test,'unexpectedSuccess');super().addUnexpectedSuccess(test)
    def addSubTest(self,test,subtest,error):
        self.event(subtest,'subcase-passed' if error is None else 'subcase-failed',error)
        super().addSubTest(test,subtest,error)


class OwnedNativeCleanup:
    """Observe existing isolated fixture lifecycle; never change its initializer.

    Class setup/local startup records the ORIGINAL PID before test cleanup. A
    scoped rmtree gate requires pg_ctl==3 and that PID absent BEFORE deletion.
    Unknown PG data is retained. This wrapper adds no permission or data grants.
    """
    def __init__(self,classes,output):
        self.classes=classes;self.output=Path(output);self.records={};self.uncertain=[];self.cleanup_errors=[];self.stack=ExitStack()
    def save(self):
        self.output.write_text(json.dumps({'scope':'Owned isolated test cluster cleanup only; not native profile admission',
            'clusters':list(self.records.values()),'uncertainPaths':self.uncertain,'cleanupErrors':self.cleanup_errors},indent=2)+'\n')
    def capture(self,data,binary):
        if not isinstance(data,Path) or not isinstance(binary,Path):return
        data=data.resolve();pid_file=data/'postmaster.pid'
        if str(data) in self.records or not pid_file.is_file():return
        pid=int(pid_file.read_text().splitlines()[0])
        if pid<=0:raise RuntimeError('Positive original owned postmaster PID required')
        self.records[str(data)]={'dataDirectory':str(data),'pgCtl':str(binary/'pg_ctl'),
            'originalPostmasterPid':pid,'confirmed':False,'dataDeleted':False}
        self.save()
    def capture_class(self,cls):
        runtime=getattr(cls,'runtime',None)
        if runtime is not None:
            self.capture(getattr(runtime,'directory',None),getattr(runtime,'psql_path',Path('/absent')).parent)
        self.capture(getattr(cls,'data',None),getattr(cls,'pgbin',None))
    def confirm(self,record):
        if record['confirmed']:return
        data=Path(record['dataDirectory'])
        if not data.exists():raise RuntimeError('Owned data deleted before native stop proof')
        status=subprocess.run([record['pgCtl'],'-D',str(data),'status'],capture_output=True,text=True,timeout=15)
        absent=False
        try:os.kill(record['originalPostmasterPid'],0)
        except ProcessLookupError:absent=True
        except PermissionError:pass
        record.update(pgCtlStatus=status.returncode,originalPostmasterPidAbsent=absent,
            pgCtlStdout=status.stdout,pgCtlStderr=status.stderr)
        self.save()
        if status.returncode!=3 or not absent:raise RuntimeError('Owned native stop uncertain; retain data')
        record['confirmed']=True;self.save()
    def __enter__(self):
        from truss import LocalPostgres
        original_enter=LocalPostgres.__enter__;original_close=LocalPostgres.close;original_rmtree=shutil.rmtree
        def entered(runtime):
            try:return original_enter(runtime)
            finally:self.capture(runtime.directory,runtime.psql_path.parent)
        def closed(runtime):
            self.capture(runtime.directory,runtime.psql_path.parent)
            result=original_close(runtime)
            record=self.records.get(str(runtime.directory.resolve()))
            if record is not None:self.confirm(record)
            return result
        def removed(path,*args,**kwargs):
            root=Path(path).resolve()
            # Only data directories contained in this requested deletion can
            # be removed. A proof for an ancestor does not authorize a sibling.
            relevant=[r for r in self.records.values() if Path(r['dataDirectory']).is_relative_to(root)]
            unknown=[p.parent for p in root.rglob('PG_VERSION') if str(p.parent.resolve()) not in self.records] if root.is_dir() else []
            if unknown:
                self.uncertain.extend(str(p) for p in unknown);self.save()
                raise RuntimeError('Unobserved PG directory retained: '+repr(unknown))
            for record in relevant:self.confirm(record)
            result=original_rmtree(path,*args,**kwargs)
            for record in relevant:record['dataDeleted']=not Path(record['dataDirectory']).exists()
            self.save();return result
        self.stack.enter_context(patch.object(LocalPostgres,'__enter__',entered))
        self.stack.enter_context(patch.object(LocalPostgres,'close',closed))
        self.stack.enter_context(patch.object(shutil,'rmtree',removed))
        for cls in self.classes:
            original=cls.setUpClass
            def setup(selected,original=original):
                try:return original()
                finally:self.capture_class(selected)
            self.stack.enter_context(patch.object(cls,'setUpClass',classmethod(setup)))
        return self
    def __exit__(self,*args):
        try:
            # Drain every original callback even when a previous one failed;
            # never let an exception skip stopping a known owned postmaster.
            for cls in self.classes:
                try:
                    cls.doClassCleanups()
                    self.cleanup_errors.extend(str(error[1]) for error in cls.tearDown_exceptions)
                except BaseException as error:self.cleanup_errors.append(type(error).__name__+': '+str(error))
            for record in self.records.values():
                if not record['confirmed']:
                    try:
                        status=subprocess.run([record['pgCtl'],'-D',record['dataDirectory'],'-m','fast','-w','-t','30','stop'],
                            capture_output=True,text=True,timeout=35)
                        record['finalStopReturncode']=status.returncode
                        self.confirm(record)
                    except BaseException as error:self.cleanup_errors.append(type(error).__name__+': '+str(error))
            self.save()
            if self.cleanup_errors:raise RuntimeError('Owned native cleanup uncertain: '+repr(self.cleanup_errors))
        finally:self.stack.close()
    @property
    def confirmed(self):
        return not self.uncertain and not self.cleanup_errors and all(r['confirmed'] and r['dataDeleted'] for r in self.records.values())
