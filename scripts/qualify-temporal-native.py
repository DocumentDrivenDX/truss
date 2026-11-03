#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""TP001 one serial installed-candidate campaign: original119 + closed JH10. Default is collection ONLY.

No installation/build, dependency override, source repair, publish, matrix or
implicit dispatch occurs here. Execute only after exact source/selection review
and genuine artifact/enrollment/fresh-native-inventory admission.
"""
import argparse
from hashlib import sha256
import importlib.metadata
from importlib.resources import files
import json
import os
import platform
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from temporal_qualification_support import collect_exact,flatten,strict_result,RecordedResult,OwnedNativeCleanup,assert_qualification_checkout,validate_capture_transition
ROOT=Path(__file__).resolve().parents[1]
LEDGER=Path(__file__).with_name('temporal-native-case-ledger.json')
EXPECTED={'temporal':39,'public54':1,'ordinary':11,'hf':62,'baseline':6,'journal':10}


def ledger():
    value=json.loads(LEDGER.read_bytes())
    if value.get('schema')!='truss-temporal-case-ledger/1' or value.get('expectedCounts')!=EXPECTED or set(value['stages'])!=set(EXPECTED):
        raise ValueError('Exact reviewed TP001 ledger/counts required')
    all_ids=[]
    for stage,count in EXPECTED.items():
        rows=value['stages'][stage]
        if len(rows)!=count:raise ValueError('Case count drift: '+stage)
        ids=[row['test'] for row in rows]
        if len(set(ids))!=count:raise ValueError('Duplicate selected case: '+stage)
        all_ids.extend(ids)
    if len(set(all_ids))!=sum(EXPECTED.values()):raise ValueError('Cross-stage duplicate execution')
    original=json.loads((ROOT/'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json').read_bytes())['cases']
    if [(c['id'],c['test']) for c in value['stages']['hf']]!=[(c['id'],c['test']) for c in original]:
        raise ValueError('All62 original independent HF cases required in original order')
    return value


def census(value):
    sys.path.insert(0,str(ROOT/'packages/python/tests'))
    result={}
    for stage,rows in value['stages'].items():
        ids=[r['test'] for r in rows];suite=collect_exact(ids)
        result[stage]={'count':suite.countTestCases(),'ids':[t.id() for t in flatten(suite)]}
    inputs=sorted((ROOT/'packages/python/tests').glob('*.py'))+[ROOT/'scripts/native_fixture.py',ROOT/'scripts/temporal_qualification_support.py',Path(__file__).resolve(),LEDGER]
    return {'scope':'SOURCE COLLECTION ONLY; no native execution or capability claim','sourceInputs':{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in inputs},'ledgerSha256':sha256(LEDGER.read_bytes()).hexdigest(),
        'stages':result,'total':sum(r['count'] for r in result.values()),'nativeExecuted':0}


def read_pinned(entry):
    path=Path(entry['path']).resolve();raw=path.read_bytes()
    if sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Original admitted input hash differs: '+str(path))
    return path,raw


def preflight(admission):
    """Read-only checks BEFORE a native process can start."""
    source_identity=assert_qualification_checkout(ROOT,admission.get('sourceCommit'),admission.get('sourceTree'),evidence_roots=admission.get('generatedEvidenceRoots',()))
    if sys.version_info[:2]!=(3,11) or sys.platform!='linux' or platform.machine()!='x86_64':
        raise ValueError('Selected Linux x86_64/Python3.11 qualification scope required')
    import truss
    from release_cohort import load_cohort,verify_installed
    from typed_sdk_cohort import _installed_wheel
    cohort=load_cohort(require_qualified=True);verify_installed()
    if admission.get('schema')!='truss-temporal-qualification-input/1':raise ValueError('Reviewed actual artifact admission required')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if admission['sourceCommit']!=head:raise ValueError('Reviewed qualification source commit differs')
    loaded=Path(truss.__file__).resolve()
    if loaded.is_relative_to(ROOT/'packages/python/src') or not loaded.is_relative_to(Path(sys.prefix).resolve()):
        raise ValueError('Fresh installed candidate environment outside checkout required')
    from truss._runtime_profile import RUNTIME_DISTRIBUTION,RUNTIME_VERSION
    if importlib.metadata.version(RUNTIME_DISTRIBUTION)!=RUNTIME_VERSION or importlib.metadata.version('psycopg')!='3.3.6':
        raise ValueError('Exact selected local/native dependencies required')
    source_package=ROOT/'packages/python/src/truss';installed_package=loaded.parent
    for p in installed_package.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
            source=source_package/p.relative_to(installed_package)
            if not source.is_file() or source.read_bytes()!=p.read_bytes():raise ValueError('Installed candidate differs from reviewed source/generated baseline: '+str(source))
    if {str(p.relative_to(source_package)) for p in source_package.rglob('*.py')}!={str(p.relative_to(installed_package)) for p in installed_package.rglob('*.py')}:
        raise ValueError('Complete reviewed Python module membership required')
    wheelhouse=Path(admission['wheelhouse']).resolve();observed={}
    if set(admission['wheels'])!={'truss','core','access','weft'}:raise ValueError('Exact four-owner wheel closure required')
    for name,package in (('truss','truss'),('core','umf'),('access','umf_access'),('weft','weft')):
        row=admission['wheels'][name];path=Path(row['path']).resolve()
        if not path.is_relative_to(wheelhouse):raise ValueError('Selected wheel outside admitted wheelhouse')
        record=_installed_wheel(path,row['sha256'],package,cohort[name]['distribution'])
        if record['version']!=cohort[name]['version']:raise ValueError('Installed owner candidate version differs')
        observed[name]=record
    checked=subprocess.run([sys.executable,'-m','pip','check'],text=True,capture_output=True,timeout=30)
    if checked.returncode:raise ValueError('Normal-resolver dependency closure is not coherent: '+checked.stdout+checked.stderr)
    from truss.catalog_runtime import _release
    from truss._temporal_owner import _inspector
    from truss._temporal_compiler import compiler
    native,digest,_=_release()
    if (native['releaseId']!='truss-catalog-runtime/0.76-temporal-candidate'
            or digest!=admission['nativeManifestSha256'] or digest!=cohort['qualified']['nativeManifestSha256']):
        raise ValueError('Exact actual native0.76 source required')
    owner,owner_profile=_inspector()
    fixture=json.loads((ROOT/'packages/python/tests/fixtures/temporal/native-guard-owner-inspection.json').read_bytes())['request']
    inspection=owner.inspect_access_views(fixture['document'],fixture['selected'],fixture['bindings'],source_id=fixture['sourceId'])
    from truss import CatalogDocument
    from truss._temporal_preparation import inspection_packet
    original_document=CatalogDocument('adoc','preflight',json.dumps(fixture['document'],ensure_ascii=True).encode())
    inspection_packet(original_document,selected=fixture['selected'],bindings=fixture['bindings'],source_id=fixture['sourceId'],
        owner_profile=owner_profile,result_bytes=json.dumps(inspection,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode())
    if compiler() is None:raise ValueError('Actual four-checker compiled temporal Weft enrollment required')
    for filename,source in (('manifest.json',cohort['qualified']['coreSourceRevision']),('compiler.json',cohort['qualified']['weftSourceRevision'])):
        raw=files('truss').joinpath('_temporal_owner/'+filename).read_bytes();m=json.loads(raw)
        if m['sourceCommit']!=source:raise ValueError('Enrolled actual owner source differs from admitted artifact closure')
    from truss._migration_recipe import load_recipe
    from truss._initialization_custody import static_inventory_matches,validate_observation
    recipe,artifacts,_=load_recipe()
    if (recipe['target']!=digest or recipe['targetRelease']!=native['releaseId'] or not recipe.get('baseline')
            or recipe['sources'] or recipe['edges'] or recipe['sourceWheels']):
        raise ValueError('Fresh actual0.76 baseline inventory required; historical0.75 may not be relabelled')
    profile=json.loads(artifacts[digest+'.json']);zones=set();capture_transitions=[]
    for selected in admission['initializationCaptures']:
        path,raw=read_pinned(selected);receipt=json.loads(raw)
        if (receipt.get('passed') is not True or receipt.get('cleanupConfirmed') is not True
                or receipt.get('runtimeManifestSha256')!=digest
                or receipt.get('historicalProfilesModified') is not False
                or receipt.get('sysPlatform')!='linux' or receipt.get('machine')!='x86_64' or receipt.get('pythonMajorMinor')!=[3,11]):
            raise ValueError('Actual current-source initializer/PID cleanup receipt required')
        package=Path(truss.__file__).resolve().parent
        actual_payload={str(p.relative_to(package)):sha256(p.read_bytes()).hexdigest() for p in sorted(package.rglob('*'))
            if p.is_file() and '_migrations' not in p.relative_to(package).parts and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        capture_transitions.append(validate_capture_transition(ROOT,receipt,head,admission['sourceTree'],native_digest=digest,nonmigration_payload=actual_payload))
        if receipt.get('nonMigrationPackageFiles')!=actual_payload:
            raise ValueError('Captured initializer/package payload differs from final candidate; only fresh baseline artifacts may differ')
        raw_profile=path.with_name('native-profile-observation.json').read_bytes()
        if sha256(raw_profile).hexdigest()!=receipt['profileSha256']:raise ValueError('Original native capture bytes differ')
        captured=json.loads(raw_profile)
        validate_observation(captured)
        if captured['sha256']!=digest or not static_inventory_matches(captured['inventory'],profile):raise ValueError('Fresh observed inventory is not the admitted candidate profile')
        proof=json.loads(path.with_name('cleanup.json').read_bytes())['clusters']
        if not proof or not all(r.get('confirmed') is True and r.get('dataDeleted') is True and r.get('pgCtlStatus')==3 and r.get('originalPostmasterPidAbsent') is True for r in proof):
            raise ValueError('Actual original PID absence and pg_ctl3 BEFORE delete required')
        zones.add(receipt['initializationTimeZone'])
    if len(admission['initializationCaptures'])!=2 or zones!={'UTC','America/New_York'}:
        raise ValueError('Both genuine initializer timezone observations required')
    old_wheel=Path(admission['public054Wheel']).resolve()
    if sha256(old_wheel.read_bytes()).hexdigest()!='4aebc56e92fdbde6714d9b811860707d2ffc9b0edbc63cc91e9dc3488c042b52':
        raise ValueError('Original public54 fixture wheel required')
    old_script='''import importlib.metadata,pathlib,sys,zipfile,truss
assert importlib.metadata.version("umf-truss")=="0.0.54"
assert sys.version_info[:2]==(3,11)
root=pathlib.Path(truss.__file__).resolve().parent
with zipfile.ZipFile(sys.argv[1]) as wheel:
 for name in wheel.namelist():
  if name.startswith("truss/") and not name.endswith("/"):
   assert (root/name.removeprefix("truss/")).read_bytes()==wheel.read(name),name
print("original public54 installed payload verified")
'''
    old=subprocess.run([str(Path(admission['public054Python']).resolve()),'-I','-c',old_script,str(old_wheel)],
        cwd=Path(sys.prefix),capture_output=True,text=True,timeout=30)
    if old.returncode:raise ValueError('Original public54 fixture environment is not ready: '+old.stdout+old.stderr)
    archive,raw=read_pinned(admission['hfArchive']);hfroot=Path(admission['hfRoot']).resolve()
    if hfroot.is_relative_to(ROOT):raise ValueError('HF must execute from independent unpacked archive outside checkout')
    with ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate HF archive member')
        for name in names:
            p=Path(name);info=z.getinfo(name);target=hfroot/p
            if (p.is_absolute() or '..' in p.parts or (info.external_attr>>16)&0o170000==0o120000
                    or target.is_symlink() or not target.resolve().is_relative_to(hfroot)
                    or target.read_bytes()!=z.read(name)):
                raise ValueError('Independent HF archive payload mismatch')
    current_recipe={'baseline':recipe['baseline'],'sources':recipe['sources'],'target':recipe['target']}
    return {'scope':'Read-only artifact/inventory admission, not native qualification','wheels':observed,
        'sourceIdentity':source_identity,'captureTransitions':capture_transitions,'nativeManifestSha256':digest,'coreInspection':{'request':fixture,'owner':owner_profile,'result':inspection},'recipe':current_recipe,'pipCheck':checked.stdout,'ledgerSha256':sha256(LEDGER.read_bytes()).hexdigest()}


def run_child(stage,value,admission,output):
    """One stage process, same admitted interpreter, original test producers."""
    output.mkdir(parents=True,exist_ok=False)
    if os.environ.get('TRUSS_NATIVE_WORKER'):raise ValueError('No borrowed worker allowed')
    root=Path(admission['hfRoot']).resolve() if stage=='hf' else ROOT
    sys.path[:0]=[str(root/'scripts'),str(root/'packages/python/tests')]
    ids=[r['test'] for r in value['stages'][stage]];suite=collect_exact(ids)
    native_evidence=root/'docs/helix/04-build/evidence/design-audit'/('temporal-candidate-'+output.parent.name+'-'+stage)
    native_evidence.mkdir(parents=True,exist_ok=False);os.environ['TRUSS_NATIVE_EVIDENCE_DIR']=str(native_evidence)
    os.environ['TRUSS_PUBLIC054_PYTHON']=str(Path(admission['public054Python']).resolve())
    os.environ['TRUSS_PUBLIC054_WHEEL']=str(Path(admission['public054Wheel']).resolve())
    selected_cases=list(flatten(suite));classes=list(dict.fromkeys(type(test) for test in selected_cases))
    result=None;inventory=False;cleanup=False;error=None;captured=[];created=[]
    class StageResult(RecordedResult):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);created.append(self)
    try:
        if stage in ('temporal','journal'):
            import importlib.util
            spec=importlib.util.spec_from_file_location('temporal_component_probe',ROOT/'scripts/probe-temporal-native-enrollment.py')
            probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
            class CandidateWorker(probe.ObservedWorker):
                def close(self):
                    root=getattr(self,'root',None)
                    if root is not None and (root/'poisoned').exists():
                        # Stop our original worker, but retain poisoned data and
                        # diagnostics; never delete it to manufacture cleanup.
                        proof=OwnedNativeCleanup([],output/'poisoned-worker-cleanup.json')
                        from pgserver._commands import POSTGRES_BIN_PATH
                        proof.capture(root/'data',Path(POSTGRES_BIN_PATH))
                        if self.server is not None:self.server.cleanup()
                        for record in proof.records.values():proof.confirm(record)
                        self.cleanup_confirmed=False
                        return
                    return super().close()
            worker=CandidateWorker()
            try:
                with worker:
                    os.environ.update(worker.environment())
                    try:result=unittest.TextTestRunner(verbosity=2,resultclass=StageResult).run(suite)
                    finally:
                        cleanup_errors=[]
                        for test in selected_cases:
                            try:
                                if test.doCleanups() is False:cleanup_errors.append('Incomplete case cleanup: '+test.id())
                            except BaseException as caught:cleanup_errors.append(type(caught).__name__+': '+str(caught))
                        for cls in classes:
                            try:
                                cls.doClassCleanups();cleanup_errors.extend(str(e[1]) for e in cls.tearDown_exceptions)
                            except BaseException as caught:cleanup_errors.append(type(caught).__name__+': '+str(caught))
                        os.environ.pop('TRUSS_NATIVE_WORKER',None)
                        if cleanup_errors:
                            (worker.root/'poisoned').write_text(json.dumps(cleanup_errors)+'\n')
                            raise RuntimeError('Selected fixture cleanup uncertain: '+repr(cleanup_errors))
                        worker.verify_clean();inventory=True
            finally:cleanup=getattr(worker,'cleanup_confirmed',False)
        else:
            monitor=OwnedNativeCleanup(classes,output/'isolated-cleanup.json')
            with monitor:
                if stage in ('hf','baseline'):
                    original=unittest.TextTestRunner.run
                    def observed(runner,selected):
                        selected_ids=[t.id() for t in flatten(selected)]
                        if selected_ids!=ids:raise ValueError('Original governing runner selected different cases')
                        answer=original(runner,selected);captured.append(answer);return answer
                    with patch.object(unittest,'TextTestResult',StageResult),patch.object(unittest.TextTestRunner,'resultclass',StageResult),patch.object(unittest.TextTestRunner,'run',observed):
                        script=root/'scripts'/('run-hf-conformance.py' if stage=='hf' else 'qualify-runtime-migrations.py')
                        args=[str(script),'--installed-package','--output',str(output/'original-runner-receipt.json')]
                        if stage=='baseline':args+=['--download','--wheelhouse',admission['wheelhouse']]
                        with patch.object(sys,'argv',args):
                            try:runpy.run_path(str(script),run_name='__main__')
                            except SystemExit as stopped:
                                if stopped.code not in (None,0):raise RuntimeError('Original governing runner refused: '+str(stopped.code))
                    if len(captured)!=1:raise ValueError('One original governing suite execution required')
                    result=captured[0]
                    receipt=json.loads((output/'original-runner-receipt.json').read_bytes())
                    if receipt.get('passed') is not True:raise ValueError('Original governing receipt did not pass')
                    if stage=='baseline' and (not receipt.get('baseline') or receipt['sources'] or receipt['tests']!=6):
                        raise ValueError('Only fresh baseline/current six allowed; no old migration suite')
                else:result=unittest.TextTestRunner(verbosity=2,resultclass=StageResult).run(suite)
            cleanup=monitor.confirmed
            # Isolated clusters are not reused: complete removal after native
            # stop proof restores the owned machine footprint, not a claimed
            # shared-cluster role/database inventory comparison.
            inventory=cleanup
    except BaseException as caught:
        error={'class':type(caught).__module__+'.'+type(caught).__qualname__,'message':str(caught)}
        raise
    finally:
        if result is None and created:result=created[-1]
        report=strict_result(result,ids,[] if result is None else result.started_ids,inventory_verified=inventory,cleanup_confirmed=cleanup)
        if error is not None:report['passed']=False
        report.update(stage=stage,expectedIds=ids,expectedCases=len(ids),error=error,
            observations=[] if result is None else result.observations,nativeEvidence=str(native_evidence),
            inventoryScope='shared worker baseline restored' if stage in ('temporal','journal') else 'isolated owned clusters stopped and deleted; no cluster reused')
        (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['passed'] else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--admission',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--stage',choices=tuple(EXPECTED),help=argparse.SUPPRESS)
    parser.add_argument('--admission-sha256',help=argparse.SUPPRESS)
    args=parser.parse_args();value=ledger()
    if args.stage:
        if not args.execute or args.admission is None:raise ValueError('Explicit admitted execution required')
        raw=args.admission.read_bytes()
        if sha256(raw).hexdigest()!=args.admission_sha256:raise ValueError('Unchanged parent admission bytes required')
        admission=json.loads(raw);preflight(admission)
        return run_child(args.stage,value,admission,args.output.resolve())
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    (output/'census.json').write_text(json.dumps(census(value),indent=2)+'\n')
    if not args.execute:return 0
    if args.admission is None:raise ValueError('Actual reviewed artifact admission file required')
    admission=json.loads(args.admission.read_bytes());records=[];error=None
    try:
        admitted=preflight(admission);(output/'admission-result.json').write_text(json.dumps(admitted,indent=2)+'\n')
        for stage in EXPECTED:
            command=[sys.executable,str(Path(__file__).resolve()),'--execute','--admission',str(args.admission.resolve()),'--stage',stage,'--admission-sha256',sha256(args.admission.read_bytes()).hexdigest(),'--output',str(output/stage)]
            with (output/(stage+'.log')).open('w') as log:
                process=subprocess.Popen(command,cwd=Path(sys.prefix),stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
                try:code=process.wait(timeout=1200)
                except subprocess.TimeoutExpired:
                    process.send_signal(signal.SIGINT)
                    try:process.wait(timeout=45)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
                    raise RuntimeError('Stage deadline exceeded; no qualification/cleanup claim: '+stage)
            result_path=output/stage/'result.json'
            if not result_path.is_file():raise RuntimeError('Missing original stage result: '+stage)
            record=json.loads(result_path.read_bytes());records.append(record)
            assert_qualification_checkout(ROOT,admission['sourceCommit'],admission['sourceTree'],evidence_roots=admission.get('generatedEvidenceRoots',()))
            if code or record.get('passed') is not True:raise RuntimeError('Selected stage failed: '+stage)
    except BaseException as caught:
        error={'class':type(caught).__module__+'.'+type(caught).__qualname__,'message':str(caught)}
        raise
    finally:
        passed=error is None and len(records)==len(EXPECTED) and sum(r['testsRun'] for r in records)==sum(EXPECTED.values()) and all(r['passed'] for r in records)
        (output/'campaign-result.json').write_text(json.dumps({'scope':'Private installed coherent candidate campaign only; final exact-tag/public-consumer/owner-browser gates remain required',
            'passed':passed,'expectedCounts':EXPECTED,'expectedTotal':sum(EXPECTED.values()),'stages':records,'error':error,
            'admissionSha256':sha256(args.admission.read_bytes()).hexdigest(),'workflowRunId':os.environ.get('GITHUB_RUN_ID'),'workflowRunAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'ledgerSha256':sha256(LEDGER.read_bytes()).hexdigest(),'sourceCommit':admission.get('sourceCommit')},indent=2)+'\n')
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
