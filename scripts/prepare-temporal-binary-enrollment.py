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


def record(path,digest):
    raw=Path(path).read_bytes()
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


def prepare(core_path,core_sha,weft_path,weft_sha,weft_source,output,*,weft_lock):
    source=exact(weft_source,40)
    if source==SUPERSEDED_WEFT:raise ValueError('Known superseded d526 cannot select final main-R intake; no wasted resolver/captures')
    output=Path(output)
    if output.exists():raise ValueError('Refuse existing enrollment review output')
    h=record(core_path,core_sha);w=record(weft_path,weft_sha)
    if w['artifactSource']!=source or w['canonicalUMF']!=h['sourceS']:raise ValueError('Actual final source closure differs')
    exact(h['sourceS'],40);exact(h['sourceTree'],40)
    if w['frozenLockSHA256']!=exact(weft_lock,64):raise ValueError('Final reviewed canonical lock closure differs')
    if (w['temporalCasesPassed']!=14 or w['routingControlsPassed']!=5 or w['SDKSmokeControlsPassed']!=42 or w['normalInstall'] is not True or w['pipCheckPassed'] is not True):raise ValueError('Actual installed W Linux component controls required')
    q=h['actualComponentQualification']
    if (q['inspectionCases']!=17 or q['inspectionCalls']!=51 or q['Saga']['cases']!=19 or q['Saga']['passed']!=19 or q['lifecycle']['tests']!=2 or q['lifecycle']['passed']!=2):raise ValueError('Exact actual Core installed component controls required')
    selected=h['artifacts']['repairedCoreWheel'];core_files=wheel_payload(selected,'umf');weft_files=wheel_payload(w['wheel'],'weft')
    actual={name[len('umf/'):]:entry['sha256'] for name,entry in h['actualInstalledFileRoster'].items() if name.startswith('umf/')}
    if actual!=core_files:raise ValueError('Actual Core installed roster and wheel differ')
    if core_files.get('_rust_core.abi3.so')!=h['nativeMembers']['umf/_rust_core.abi3.so']['sha256']:raise ValueError('Core actual loaded module correspondence differs')
    if weft_files.get('weft.abi3.so')!=w['nativeModule']['sha256']:raise ValueError('W actual loaded module correspondence differs')
    # The original component report hashes the SDK receipt, including before/
    # after wheel, native and shim correspondence. Re-read those actual bytes.
    sdk_path=Path(w['SDKSmokeReport']);sdk_row=next(row for row in w['allFiles'] if row['path']==str(sdk_path));sdk=record(sdk_path,sdk_row['sha256']);pins=sdk['pinsBeforeAfter']
    if (sdk['controls']!=42 or pins['wheelSha256']!=w['wheel']['sha256'] or pins['nativeModuleSha256']!=weft_files['weft.abi3.so'] or pins['shimSha256']!=weft_files['__init__.py']):raise ValueError('Actual installed SDK/native/shim custody differs')
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
    cohort['qualified']={'evidenceScope':'Complete actual installed-Linux component identity seal for inventory observation ONLY; NOT full runtime/cohort/release qualification','coreSourceRevision':h['sourceS'],'weftSourceRevision':source,'nativeManifestSha256':native_sha,'compilerCohorts':[{'platform':'linux-x86_64','sourceRevision':source,'wheelFilename':Path(w['wheel']['path']).name,'wheelSha256':w['wheel']['sha256'],'nativeModuleSha256':w['nativeModule']['sha256']}],'remainingGates':['Core3.13/rebuilt and Weft WASM/browser receipts require separate full-cohort reconciliation','Truss combined311 resolver/intake','reviewed original2TZ inventories/fresh baseline','full-cohort119/HF62/ordinaryABI1.2/current6','exact-tag/public bytes/fresh consumers/release']}
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
