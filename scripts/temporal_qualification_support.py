# SPDX-License-Identifier: MIT OR Apache-2.0
"""Qualification-only exact-case results and stop-before-delete custody.

No application runtime, admission, codec or dependency-selection behavior lives
here. Existing test methods and native initializer bytes execute unchanged.
"""
from contextlib import ExitStack
from pathlib import Path
from hashlib import sha256
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


# Deliberate parallel planner documents are not executable qualification inputs.
_PLANNER_PATHS={
 'docs/helix/02-design/contracts/CONTRACT-010-exact-value-transport.md',
 'docs/helix/02-design/contracts/CONTRACT-012-weft-storage-handoff.md',
 'docs/helix/03-test/test-plan.md','docs/helix/04-build/temporal-current-baseline-plan.md',
 *('docs/helix/04-build/'+name for name in ('embedder-temporal-delivery-plan.md',
 'temporal-coherent-source-integration-plan.md','temporal-dependency-cohort-plan.md',
 'temporal-interface-freeze.md','temporal-native-qualification-plan.md','temporal-public-values-addendum.md'))}
_JH_INPUTS=(
 'packages/python/src/truss/_initialization_custody.py',
 'packages/python/src/truss/_catalog_runtime/initialization-custody.sql',
 'packages/python/src/truss/_catalog_runtime/initialization-custody.schema.json',
 'packages/python/src/truss/_catalog_runtime/groups.sql',
 'packages/python/src/truss/_catalog_runtime/manifest.json',
 'packages/python/src/truss/catalog_runtime.py',
 'packages/python/src/truss/_installation_privileges.py',
 'packages/python/src/truss/_migration_verify.py','packages/python/src/truss/_migration_recipe.py',
 'packages/python/src/truss/migrations.py',
 'scripts/capture-temporal-native-inventory.py','scripts/assemble-temporal-native-baseline.py',
 'scripts/qualify-temporal-native.py','scripts/temporal-native-case-ledger.json',
 'scripts/temporal_qualification_support.py','scripts/check-module-boundaries.py',
 'packages/python/tests/test_initialization_custody.py',
 'packages/python/tests/test_initialization_custody_native.py',
 'packages/python/tests/test_initialization_custody_derivation_native.py',
 'docs/helix/02-design/contracts/journal-horizon-initialization-custody.md',
 'docs/helix/02-design/contracts/journal-horizon-initialization-custody-0.1.schema.json',
 'docs/helix/04-build/journal-horizon-custody-plan.md',
 'docs/helix/02-design/contracts/CONTRACT-008-layout-bootstrap.md',
 'docs/helix/02-design/contracts/CONTRACT-002-journal.md',
 'docs/helix/03-test/test-plans/STP-045-bootstrap-the-internal-layout-from-umf.md',
 'docs/helix/04-build/temporal-native-qualification-plan.md',
 'docs/helix/04-build/temporal-current-baseline-plan.md')


def journal_custody_inputs(root,commit):
    root=Path(root);result={}
    for name in _JH_INPUTS:
        original=_git(root,'show',commit+':'+name);actual=(root/name).read_bytes()
        if actual!=original:raise ValueError('Custody code/schema/governance differs from actual committed source: '+name)
        result[name]=sha256(original).hexdigest()
    return result


_INPUT_ROOTS=('packages/python/src/truss','packages/python/tests','scripts','.github/workflows','docs/helix/03-test','tests')
_MIGRATIONS='packages/python/src/truss/_migrations/'
_SEAL='scripts/truss-release-cohort.json'


def _git(root,*args):
    return subprocess.check_output(['git',*args],cwd=root)


def commit_tree(root,commit):
    import re
    if type(commit) is not str or re.fullmatch('[0-9a-f]{40}',commit) is None:
        raise ValueError('Exact admitted commit required')
    if _git(root,'rev-parse',commit+'^{commit}').decode().strip()!=commit:
        raise ValueError('Exact original commit required')
    return _git(root,'rev-parse',commit+'^{tree}').decode().strip()


def assert_qualification_checkout(root,commit,tree,*,evidence_roots=()):
    """Bind HEAD/TREE and reject staged, unstaged, untracked/ignored inputs.

    Evidence roots are explicit, separate directories below design-audit or
    outside this checkout. They never authorize changes to tracked input bytes.
    """
    root=Path(root).resolve()
    jh=(root/'packages/python/src/truss/_initialization_custody.py').is_file()
    actual=_git(root,'rev-parse','HEAD').decode().strip()
    actual_tree=commit_tree(root,actual)
    if actual!=commit or actual_tree!=tree:raise ValueError('Actual admitted qualification commit/tree differs')
    outputs=[];checkout_outputs=[]
    for selected in evidence_roots:
        # Preserve lexical location BEFORE resolving symlinks. External output
        # roots are recorded but never exempt an input located in this checkout.
        lexical=Path(os.path.abspath(selected));resolved=lexical.resolve()
        for path in (lexical,resolved):
            if root.is_relative_to(path):raise ValueError('Evidence output cannot contain the qualification checkout')
            if path.is_relative_to(root):
                relative=path.relative_to(root)
                base=Path('docs/helix/04-build/evidence/design-audit')
                if relative==base or not relative.is_relative_to(base):
                    raise ValueError('Evidence output must be separately scoped below design-audit')
        if lexical.is_relative_to(root):
            if not resolved.is_relative_to(root/'docs/helix/04-build/evidence/design-audit'):
                raise ValueError('Checkout evidence root must resolve within design-audit')
            checkout_outputs.append((lexical,resolved))
        outputs.append(resolved)
    changed=set(_git(root,'diff','--name-only','-z','HEAD','--').decode().split('\0'))
    changed.update(_git(root,'diff','--cached','--name-only','-z','HEAD','--').decode().split('\0'))
    dirty=sorted(p for p in changed if p and (p not in _PLANNER_PATHS or jh and p in _JH_INPUTS))
    if dirty:raise ValueError('Dirty tracked qualification inputs versus admitted HEAD: '+repr(dirty))
    # All untracked files, plus ignored files under executable/data input roots.
    untracked=set(_git(root,'ls-files','--others','--exclude-standard','-z').decode().split('\0'))
    untracked.update(_git(root,'ls-files','--others','--ignored','--exclude-standard','-z','--',*_INPUT_ROOTS,*(_JH_INPUTS if jh else ())).decode().split('\0'))
    unknown=[]
    for name in sorted(untracked-{''}):
        path=Path(name)
        if (name in _PLANNER_PATHS and not (jh and name in _JH_INPUTS)) or name.startswith('docs/helix/04-build/evidence/temporal-completion-current-owner-audit-20261102/'):continue
        if '__pycache__' in path.parts and path.suffix=='.pyc':continue
        lexical=root/path;resolved=lexical.resolve()
        if any(lexical.is_relative_to(location) and resolved.is_relative_to(target) for location,target in checkout_outputs):continue
        unknown.append(name)
    if unknown:raise ValueError('Uncommitted qualification inputs outside scoped evidence: '+repr(unknown))
    return {'commit':actual,'tree':actual_tree,'qualificationInputsClean':True,'generatedEvidenceRoots':[str(p) for p in outputs]}


def validate_capture_transition(root,receipt,final_commit,final_tree,*,native_digest,nonmigration_payload):
    """Preserve original capture provenance; allow reviewed fresh-artifact descendants only."""
    root=Path(root).resolve();capture=receipt.get('sourceCommit');tree=receipt.get('sourceTree')
    identity=receipt.get('sourceIdentity',{})
    jh=(root/'packages/python/src/truss/_initialization_custody.py').is_file()
    if jh or receipt.get('journalCustodyInputs') is not None:
        original_inputs=journal_custody_inputs(root,capture)
        if receipt.get('journalCustodyInputs')!=original_inputs or journal_custody_inputs(root,final_commit)!=original_inputs:
            raise ValueError('Custody code/schema/plan changes require a new original capture')
    if identity.get('commit')!=capture or identity.get('tree')!=tree or identity.get('qualificationInputsClean') is not True:
        raise ValueError('Original capture must attest clean qualification inputs at its own commit/tree')
    if commit_tree(root,capture)!=tree or commit_tree(root,final_commit)!=final_tree:
        raise ValueError('Original capture/final commit tree correspondence required')
    if receipt.get('runtimeManifestSha256')!=native_digest or receipt.get('nonMigrationPackageFiles')!=nonmigration_payload:
        raise ValueError('Complete non-migration payload and native manifest must equal original capture')
    producer=_git(root,'show',capture+':scripts/capture-temporal-native-inventory.py')
    from hashlib import sha256
    if sha256(producer).hexdigest()!=receipt.get('producerSha256'):
        raise ValueError('Original capture producer commit/blob differs')
    ancestor=subprocess.run(['git','merge-base','--is-ancestor',capture,final_commit],cwd=root,capture_output=True)
    if ancestor.returncode:raise ValueError('Reviewed final commit must descend from original capture')
    # Inspect EVERY intervening commit, including merge-parent diffs, so a
    # non-migration change subsequently reverted cannot masquerade as equality.
    changed=set(_git(root,'log','--format=','--name-only','-m','--full-history',capture+'..'+final_commit,
                     '--','packages/python',_SEAL,*(_JH_INPUTS if jh else ())).decode().splitlines())-{''}
    manifest=json.loads(_git(root,'show',final_commit+':'+_MIGRATIONS+'manifest.json'))
    if (manifest.get('target')!=native_digest or manifest.get('targetRelease')!='truss-catalog-runtime/0.76-temporal-candidate'
            or not manifest.get('baseline') or manifest.get('sources')!=[] or manifest.get('edges')!=[] or manifest.get('sourceWheels')!={}):
        raise ValueError('Reviewed descendant must select genuine fresh-only native baseline')
    allowed={_MIGRATIONS+'manifest.json'}|{_MIGRATIONS+name for name in manifest['files'] if Path(name).name==name and name.endswith('.json')}
    for name in changed:
        if name not in allowed:raise ValueError('Intervening package/enrollment/seal change requires a new source capture: '+name)
        if name!=_MIGRATIONS+'manifest.json':
            exists=subprocess.run(['git','cat-file','-e',capture+':'+name],cwd=root,capture_output=True)
            if exists.returncode==0:raise ValueError('Frozen migration artifact changed after capture: '+name)
            body=_git(root,'show',final_commit+':'+name)
            if sha256(body).hexdigest()!=manifest['files'][name.removeprefix(_MIGRATIONS)]:
                raise ValueError('Fresh descendant artifact differs from reviewed final manifest')
    return {'captureCommit':capture,'captureTree':tree,'finalCommit':final_commit,'finalTree':final_tree,
            'interveningPackagePaths':sorted(changed),'nativeManifestSha256':native_digest,'nonMigrationPayloadEqual':True}
