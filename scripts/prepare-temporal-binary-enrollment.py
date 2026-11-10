#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Prepare genuine final-main-R binary enrollment for review, never apply or execute.

Original d526 Linux evidence is preserved but cannot select this final intake.
No binary imports, resolver, build, source mutation or database execution occurs.
"""
import argparse
from hashlib import sha256
from email.parser import BytesParser
import json
from pathlib import Path
import re
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
SUPERSEDED_WEFT='d52644f4b2fb5579f9a303012cfc3a98ac6c174e'


def exact(value,length):
    if type(value) is not str or re.fullmatch('[0-9a-f]{%d}'%length,value) is None or set(value)=={'0'}:raise ValueError('Actual immutable source/digest required')
    return value


def record(path,digest,*,reader=None):
    raw=reader({'path':path,'sha256':digest}) if reader is not None else Path(path).read_bytes()
    if type(raw) is not bytes:raise ValueError('Original handoff reader must return authenticated bytes')
    if sha256(raw).hexdigest()!=exact(digest,64):raise ValueError('Original handoff digest differs')
    return json.loads(raw)


def wheel_payload(entry,package):
    path=Path(entry['path']);raw=path.read_bytes()
    if sha256(raw).hexdigest()!=exact(entry['sha256'],64):raise ValueError('Original actual wheel digest differs')
    with ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate original wheel member')
        metadata=[name for name in names if name.endswith('.dist-info/METADATA')]
        if len(metadata)!=1:raise ValueError('One original owner distribution metadata required')
        selected=BytesParser().parsebytes(z.read(metadata[0]))
        distribution,version=('umf-core','0.10.8') if package=='umf' else ('umf-weft','0.4.57')
        if str(selected['Name']).lower().replace('_','-')!=distribution or selected['Version']!=version:raise ValueError('Actual selected distribution/version differs')
        payload={name[len(package)+1:]:sha256(z.read(name)).hexdigest() for name in names if name.startswith(package+'/') and not name.endswith('/')}
    if not payload:raise ValueError('Original owner wheel payload required')
    return payload



def final_weft_component(w,source,canonical_source,lock,*,record_reader=None):
    """Authenticate original final-R component records; never upgrade scope."""
    if (w.get('schema')!='weft-final-R-linux-x86-component-handoff/1'
        or w.get('sourceCommit')!=source or w.get('actualJobConclusion')!='success'
        or w.get('originalAttempt')!=1):raise ValueError('Actual original final-R Linux job required')
    exact(w['sourceTree'],40)
    component=record(w['component']['path'],w['component']['sha256'],reader=record_reader)
    sdk=record(w['sdk42']['path'],w['sdk42']['sha256'],reader=record_reader)
    packaging=record(w['installedPackaging']['path'],w['installedPackaging']['sha256'],reader=record_reader)
    if (component['status']!='passed' or component['sourceCommit']!=source
        or component['sourceTree']!=w['sourceTree'] or component['canonicalUmf']!=canonical_source
        or component['cargoLockSha256']!=exact(lock,64)
        or component['target']!='x86_64-unknown-linux-gnu'
        or component['workflowCommit']!=source
        or component['producerRunId']!=w['runID']
        or str(component['producerRunAttempt'])!=str(w['originalAttempt'])):
        raise ValueError('Original component source/tree/producer/lock differs')
    expected={'temporal':14,'ordinaryPaddedRouting':5,'SDK':42}
    if (w['actualControls']!=expected or component['temporalCases']!=14
        or component['routingControls']!=5 or component['sdkControls']!=42):
        raise ValueError('Exact installed component counts required')
    stages=component['stageResults']
    if len({r['name'] for r in stages})!=len(stages) or any(type(r['exitCode']) is not int or r['exitCode']!=0 for r in stages):
        raise ValueError('Original installed stage failure or duplication')
    if not {'normal-install','pip-check','packaging','native-origin','temporal14','routing5','sdk42'}<={r['name'] for r in stages}:
        raise ValueError('Missing actual installed component stages')
    pins={'wheelSha256':w['wheel']['sha256'],'nativeModuleSha256':w['nativeModule']['sha256'],'shimSha256':w['shimSha256']}
    if (any(component[k]!=v for k,v in pins.items())
        or sdk['sourceCommit']!=source or sdk['version']!='0.4.57' or sdk['controls']!=42
        or sdk['pinsBeforeAfter']!=pins
        or component['sdkReportSha256']!=w['sdk42']['sha256']
        or component['packagingReportSha256']!=w['installedPackaging']['sha256']
        or packaging['status']!='passed' or packaging['version']!='0.4.57'
        or any(packaging[k]!=pins[k] for k in ('wheelSha256','nativeModuleSha256'))):
        raise ValueError('Actual SDK/packaging/native/shim correspondence differs')
    from component_prerequisite_validators import validate_weft_existing_sdk_checks
    validate_weft_existing_sdk_checks(sdk,source_commit=source,pins_before_after=pins)
    return sdk


def prepare(core_path,core_sha,weft_path,weft_sha,weft_source,output,*,weft_lock):
    source=exact(weft_source,40)
    if source==SUPERSEDED_WEFT:raise ValueError('Known superseded d526 cannot select final main-R intake; no wasted resolver/captures')
    output=Path(output)
    if output.exists():raise ValueError('Refuse existing enrollment review output')
    h=record(core_path,core_sha);w=record(weft_path,weft_sha)
    exact(h['sourceS'],40);exact(h['sourceTree'],40)
    final_weft_component(w,source,h['sourceS'],weft_lock)
    q=h['actualComponentQualification']
    if (q['inspectionCases']!=17 or q['inspectionCalls']!=51 or q['Saga']['cases']!=19 or q['Saga']['passed']!=19 or q['lifecycle']['tests']!=2 or q['lifecycle']['passed']!=2):raise ValueError('Exact actual Core installed component controls required')
    selected=h['artifacts']['repairedCoreWheel'];core_files=wheel_payload(selected,'umf');weft_files=wheel_payload(w['wheel'],'weft')
    actual={name[len('umf/'):]:entry['sha256'] for name,entry in h['actualInstalledFileRoster'].items() if name.startswith('umf/')}
    if actual!=core_files:raise ValueError('Actual Core installed roster and wheel differ')
    if core_files.get('_rust_core.abi3.so')!=h['nativeMembers']['umf/_rust_core.abi3.so']['sha256']:raise ValueError('Core actual loaded module correspondence differs')
    if weft_files.get('weft.abi3.so')!=w['nativeModule']['sha256']:raise ValueError('W actual loaded module correspondence differs')
    if weft_files.get('__init__.py')!=w['shimSha256']:raise ValueError('W actual installed shim correspondence differs')
    bundle=ROOT/'packages/python/src/truss/_temporal_owner';source_raw=(bundle/'source.json').read_bytes();resources=json.loads(source_raw)
    if resources['sourceCommit']!=h['sourceS']:raise ValueError('Truss canonical resource source differs')
    for entry in resources['resources'].values():
        member='umf/action_runtime_'+entry['file']
        if h['resources'][member]['sha256']!=entry['sha256'] or core_files.get(member[len('umf/'):])!=entry['sha256']:raise ValueError('Exact canonical resource correspondence differs')
    inspector={'distribution':'umf-core','version':'0.10.8','sourceSha256':sha256(source_raw).hexdigest(),'sourceCommit':h['sourceS'],'installedFiles':core_files,'maximumWork':1000000}
    compiler={'distribution':'umf-weft','version':'0.4.57','sourceCommit':source,'installedFiles':weft_files,'checkers':['check_engine_temporal_read_shape_json','check_engine_temporal_page_shape_json','check_engine_temporal_read_json','check_engine_temporal_page_json']}
    manifest=json.loads((ROOT/'packages/python/src/truss/_catalog_runtime/manifest.json').read_bytes())
    outputs={'manifest.json':json.dumps(inspector,indent=2)+'\n','compiler.json':json.dumps(compiler,indent=2)+'\n'}
    for filename,raw in outputs.items():manifest['files']['../_temporal_owner/'+filename]=sha256(raw.encode()).hexdigest()
    native_raw=json.dumps(manifest,indent=2)+'\n';native_sha=sha256(native_raw.encode()).hexdigest()
    cohort=json.loads((ROOT/'scripts/truss-release-cohort.json').read_bytes())
    if cohort['qualified'] is not None:raise ValueError('Unexpected active identity seal; review intervening source instead of overwriting')
    cohort['qualified']={'evidenceScope':'Complete actual installed-Linux component identity seal for inventory observation ONLY; NOT full runtime/cohort/release qualification','coreSourceRevision':h['sourceS'],'weftSourceRevision':source,'nativeManifestSha256':native_sha,'compilerCohorts':[{'platform':'linux-x86_64','sourceRevision':source,'wheelFilename':Path(w['wheel']['path']).name,'wheelSha256':w['wheel']['sha256'],'nativeModuleSha256':w['nativeModule']['sha256']}],'remainingGates':['Complete three-platform Weft final-R and full owner cohort reconciliation','Truss combined311 resolver/intake','reviewed original2TZ inventories/fresh baseline','original119 plus closedJH10/HF62/ordinaryABI1.2/current6','exact-tag/public bytes/fresh consumers/release']}
    # Writes ONLY a new review directory. Nothing here enrolls production bytes.
    output.mkdir(parents=True,exist_ok=False)
    for name,raw in outputs.items():(output/name).write_text(raw)
    (output/'native-manifest.json').write_text(native_raw)
    (output/'cohort-seal.json').write_text(json.dumps(cohort,indent=2)+'\n')
    receipt={'scope':'PROPOSED exact final-main-R enrollment bytes ONLY; NOT APPLIED/ADMITTED','ready':False,'sourceS':h['sourceS'],'weftSource':source,'coreHandoffSha256':core_sha,'weftHandoffSha256':weft_sha,'nativeManifestSha256':native_sha,'coreMaximumWork':1000000,'maximumWorkScope':'Truss explicit inspection work ceiling, not an upstream capability claim','next':'Review/apply these exact outputs; commit clean final source/tree; prepare actual owner input bundle; separately approve hosted no-PG intake; review actual resolver/Truss wheel before any inventory phase'}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('core-manifest','core-sha256','weft-manifest','weft-sha256','weft-source','weft-lock-sha256','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.core_manifest,a.core_sha256,a.weft_manifest,a.weft_sha256,a.weft_source,a.output,weft_lock=a.weft_lock_sha256),indent=2))


if __name__=='__main__':main()
