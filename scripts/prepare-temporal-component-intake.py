#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit Linux-only owner-byte intake; build a Python Truss wheel, never start PG.

This prepares actual resolver/artifact evidence for a SEPARATE inventory admission.
No owner/native compilation, baseline generation, guard relaxation or publication.
"""
import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import os
import platform
import shutil
import subprocess
import sys
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]

def hosted_module():
    spec=importlib.util.spec_from_file_location('temporal_hosted',ROOT/'scripts/prepare-temporal-hosted-input.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def extract(archive,expected,output):
    helper=hosted_module();archive=Path(archive);output=Path(output)
    if sha256(archive.read_bytes()).hexdigest()!=helper.digest(expected):raise ValueError('Original intake ZIP digest differs')
    if output.exists():raise ValueError('Refuse stale component intake output')
    with ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or 'component-input.json' not in names:raise ValueError('One original component-input manifest required')
        m=json.loads(z.read('component-input.json'))
        if m.get('schema')!='truss-temporal-component-intake/1' or m.get('ready') is not True:raise ValueError('Actual reviewed component input required')
        from temporal_qualification_support import assert_qualification_checkout
        identity=assert_qualification_checkout(ROOT,m.get('sourceCommit'),m.get('sourceTree'))
        entries=m.get('files');wheels=m.get('wheels')
        if type(entries) is not dict or not entries or set(names)!={'component-input.json',*entries}:raise ValueError('Complete original component byte inventory required')
        if m['inventoryIdentity']['ownerIdentities']['weft']['sourceCommit']=='d52644f4b2fb5579f9a303012cfc3a98ac6c174e':raise ValueError('Known superseded d526 cannot select final main-R resolver intake')
        if type(wheels) is not dict or set(wheels)!={'core','access','weft'}:raise ValueError('Three actual selected owner wheels required')
        for name,digest in entries.items():
            helper.relative(name);info=z.getinfo(name)
            if name.endswith('/') or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Original regular intake files only')
            if sha256(z.read(name)).hexdigest()!=helper.digest(digest):raise ValueError('Original component bytes differ:'+name)
        for key,wheel in wheels.items():
            path=helper.relative(wheel.get('path'));digest=helper.digest(wheel.get('sha256'))
            if not path.startswith('wheelhouse/') or not path.endswith('.whl') or entries.get(path)!=digest:raise ValueError('Original selected wheel/inventory correspondence required')
        # Correspond exact retained wheel payloads to the committed binary
        # enrollments before build/install; actual loaded modules rechecked later.
        from io import BytesIO
        for key,package,filename in (('core','umf','manifest.json'),('weft','weft','compiler.json')):
            enrolled=json.loads((ROOT/'packages/python/src/truss/_temporal_owner'/filename).read_bytes())
            with ZipFile(BytesIO(z.read(wheels[key]['path']))) as wheel:
                members=wheel.namelist()
                if len(members)!=len(set(members)):raise ValueError('Duplicate owner wheel member')
                payload={name[len(package)+1:]:sha256(wheel.read(name)).hexdigest() for name in members if name.startswith(package+'/') and not name.endswith('/')}
            if payload!=enrolled['installedFiles']:raise ValueError('Actual owner wheel differs from committed enrollment')
        owners=m['inventoryIdentity']['ownerIdentities']
        if set(owners)!={'core','weft','truss'}:raise ValueError('Complete original owner identity records required')
        for key in ('core','weft'):
            enrolled=json.loads((ROOT/'packages/python/src/truss/_temporal_owner'/('manifest.json' if key=='core' else 'compiler.json')).read_bytes())
            selected=owners[key]
            module=helper.relative(selected['modulePath']);helper.digest(selected['moduleSha256'])
            if (selected['sourceCommit']!=enrolled['sourceCommit'] or selected['wheelSha256']!=wheels[key]['sha256'] or selected['wheelPath']!=wheels[key]['path'] or enrolled['installedFiles'].get(module)!=selected['moduleSha256']):raise ValueError('Actual source/wheel/module enrollment correspondence required')
        package=ROOT/'packages/python/src/truss';source_raw=(package/'_temporal_owner/source.json').read_bytes();source=json.loads(source_raw)
        core=owners['core']
        if core['resourceSourceCommit']!=source['sourceCommit'] or core['resourceManifestSha256']!=sha256(source_raw).hexdigest():raise ValueError('Actual canonical source manifest differs')
        expected_resources={name:{'path':entry['file'],'sha256':entry['sha256']} for name,entry in source['resources'].items()}
        if core['resources']!=expected_resources:raise ValueError('All nine exact canonical resources required')
        if owners['truss']['nativeManifestSha256']!=sha256((package/'_catalog_runtime/manifest.json').read_bytes()).hexdigest():raise ValueError('Actual source native manifest differs')
        # No candidate wheel exists yet: this is a DIFFERENT, owner-only input
        # schema. Inventory's four-wheel admission rules remain unchanged.
        output.mkdir(parents=True,exist_ok=False)
        for name in names:
            target=output/helper.relative(name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    return m,identity


def run(command,log,*,env=None,cwd=None):
    with Path(log).open('w') as stream:
        subprocess.run([str(x) for x in command],stdout=stream,stderr=subprocess.STDOUT,check=True,env=env,cwd=cwd)


def original_capture():
    spec=importlib.util.spec_from_file_location('abi12_probe',ROOT/'scripts/probe-weft-abi12-cohort.py')
    probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
    path=ROOT/'docs/helix/04-build/evidence/temporal-t4a/linux-41547057318-attempt1/evidence/public054-capture.json'
    original=path.read_bytes();capture=json.loads(original);probe.validate_payloads(capture)
    call=capture['compilerCall'];page=capture['enginePage'];checker=page['checkerCall']
    for record in (call['request'],call['arguments'][0],call['response'],call['bindingJson'],page['input'],page['program'],checker['program'],checker['currentRequest'],checker['afterJson'],checker['result']):
        if probe.validate_payloads(record)!=1:raise ValueError('Required original native-capture payload missing')
    if (capture['schema']!='truss.weft-abi12-native-capture/0.1' or capture['truss']['version']!='0.0.54' or call['arguments']!=[call['request'],2,None]
            or json.loads(call['request']['utf8'])['target']['bindingJson']!=call['bindingJson']['utf8']
            or json.loads(page['input']['utf8'])['request']!=json.loads(call['request']['utf8']) or checker['program']!=page['program']):
        raise ValueError('Authentic original request/binding/page/checker custody differs')
    return probe,original,capture


def ordinary_observations(output):
    """Actual new0457 compiler diagnostics; no SQL/native adoption claim."""
    probe,original,capture=original_capture()
    import weft
    import weft.weft as native
    from truss._query_runtime import compiler
    selected=compiler(engine_catalog=True,engine_pages=True)
    if selected is not weft.compile_truss_runtime_json:raise ValueError('Actual selected ordinary compiler unavailable')
    for name in ('compile_truss_runtime_json','compile_truss_runtime_page_json','compile_engine_read_json','compile_engine_page_json','check_engine_read_json','check_engine_page_json'):
        if not callable(getattr(weft,name,None)) or getattr(weft,name) is not getattr(native,name,None):raise ValueError('Original native ordinary callable correspondence differs:'+name)
    call=capture['compilerCall'];request=call['request']['utf8'];engine_input=capture['enginePage']['input']['utf8']
    calls={}
    for name,args in (('compile_truss_runtime_json',(request,)),('compile_truss_runtime_page_json',(request,2,None)),('compile_engine_page_json',(engine_input,))):
        calls[name]=probe.invoke(getattr(weft,name),*args)
    generated=calls['compile_engine_page_json']
    program=generated['raw']['utf8'] if generated.get('kind')=='compiled-or-checked' else capture['enginePage']['program']['utf8']
    checker=capture['enginePage']['checkerCall']
    calls['check_engine_page_json']=probe.invoke(weft.check_engine_page_json,program,checker['currentRequest']['utf8'],checker['afterJson']['utf8'])
    # Known old current-query/disclosure cohorts remain closed. Their refusal
    # is retained separately from raw compiler compatibility, never patched away.
    refusals={}
    from truss._current_query_originals import _actual_consumer
    from truss._current_disclosure_originals import _actual_disclosure_consumer
    for name,operation in (('current-query',_actual_consumer),('current-disclosure',_actual_disclosure_consumer)):
        try:operation()
        except ValueError as error:refusals[name]={'refused':True,'errorClass':type(error).__name__,'message':str(error)}
        else:refusals[name]={'refused':False}
    report={'scope':'Raw0457 ordinary compiler observations ONLY; SQL/native ABI1.2 adoption still requires full119/HF62/current6','originalCaptureSha256':sha256(original).hexdigest(),'originalRequest':call['request'],'originalBinding':call['bindingJson'],'originalEnginePageInput':capture['enginePage']['input'],'checkerInputs':{'origin':'fresh-final0457-program' if generated.get('kind')=='compiled-or-checked' else 'original051-program','program':probe.payload_record(program),'currentRequest':checker['currentRequest'],'afterJson':checker['afterJson']},'calls':calls,'knownOldConsumerGuardObservations':refusals,'nativeDatabaseExecuted':False}
    Path(output).write_text(json.dumps(report,indent=2)+'\n');return report


def execute(archive,expected,output):
    if sys.platform!='linux' or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,11):raise ValueError('Explicit hosted Linux x86_64/Python3.11 intake only')
    output=Path(output).resolve();inputs=output/'inputs'
    if output.exists():raise ValueError('Refuse existing intake root')
    m,identity=extract(archive,expected,inputs)
    from release_cohort import load_cohort
    load_cohort(require_qualified=True)
    env=dict(os.environ);env.pop('PYTHONPATH',None);env['PYTHONDONTWRITEBYTECODE']='1'
    staged=output/'build-source';shutil.copytree(ROOT/'packages/python',staged,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info','build','dist'))
    run([sys.executable,'-m','venv',output/'build-env'],output/'build-venv.log')
    build_python=output/'build-env/bin/python'
    run([build_python,'-m','pip','install','build==1.3.0'],output/'build-tools.log',env=env)
    run([build_python,'-m','build','--wheel','--outdir',output/'dist',staged],output/'build.log',env=env)
    wheels=list((output/'dist').glob('*.whl'))
    if len(wheels)!=1 or wheels[0].name!='umf_truss-0.0.56-py3-none-any.whl':raise ValueError('One actual candidate Python wheel required')
    candidate=wheels[0];wheelhouse=inputs/'wheelhouse';shutil.copyfile(candidate,wheelhouse/candidate.name)
    run([sys.executable,'-m','venv',output/'candidate-env'],output/'candidate-venv.log');python=output/'candidate-env/bin/python'
    selected=[inputs/m['wheels'][key]['path'] for key in ('core','access','weft')]
    # The selected local runtime is released on GitHub, not the package index.
    # Reuse its canonical checksum verifier; the resolver still installs normally.
    run([python,ROOT/'scripts/install-local-runtime.py','--download-only','--wheelhouse',wheelhouse],output/'runtime-download.log',env=env)
    run([python,'-m','pip','install','--only-binary=:all:','--find-links',wheelhouse,'--report',output/'install-report.json',str(candidate)+'[local,native,query,typed-sdk]',*selected,'pg8000==1.31.5','pydantic==2.14.2'],output/'install.log',env=env)
    run([python,'-m','pip','check'],output/'pip-check.log',env=env);run([python,'-m','pip','freeze'],output/'freeze.txt',env=env)
    # Preserve the actual resolved artifacts for the later OFFLINE inventory
    # job. These are original pip-selected bytes, each pinned by its report hash.
    import urllib.request
    from urllib.parse import urlparse,unquote
    resolved=json.loads((output/'install-report.json').read_bytes())
    for entry in resolved['install']:
        d=entry['download_info'];digest=d['archive_info']['hashes']['sha256'];url=d['url'];name=Path(unquote(urlparse(url).path)).name
        if not name.endswith('.whl'):raise ValueError('Normal resolver selected non-wheel dependency')
        target=wheelhouse/name
        if not target.exists():
            with urllib.request.urlopen(url) as response:target.write_bytes(response.read())
        if sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('Original resolver artifact digest differs')
    manifest=m['inventoryIdentity'];manifest.update(schema='truss-temporal-hosted-input/1',ready=False,phase='inventory',sourceCommit=identity['commit'],sourceTree=identity['tree'],candidateWheel='wheelhouse/'+candidate.name,admission=None)
    manifest['wheels']={**m['wheels'],'truss':{'path':manifest['candidateWheel'],'sha256':sha256(candidate.read_bytes()).hexdigest()}}
    manifest['files']={str(p.relative_to(inputs)):sha256(p.read_bytes()).hexdigest() for p in sorted(wheelhouse.iterdir()) if p.is_file()}
    (inputs/'hosted-input.json').write_text(json.dumps(manifest,indent=2)+'\n')
    inventory_bundle=output/'inventory-bundle';inventory_bundle.mkdir()
    shutil.copytree(wheelhouse,inventory_bundle/'wheelhouse')
    shutil.copyfile(inputs/'hosted-input.json',inventory_bundle/'hosted-input.json')
    run([python,ROOT/'scripts/prepare-temporal-hosted-input.py','--verify-installed',inputs],output/'installed-identities.json',env=env)
    run([python,Path(__file__).resolve(),'--ordinary-observations',output/'ordinary0457.json'],output/'ordinary0457.log',env=env)
    from temporal_qualification_support import assert_qualification_checkout
    assert_qualification_checkout(ROOT,identity['commit'],identity['tree'])
    result={'scope':'Hosted installed-Linux component intake ONLY; NO PG/capture/baseline/native119/release','passed':True,'sourceIdentity':identity,'candidateWheelSha256':sha256(candidate.read_bytes()).hexdigest(),'inventoryAdmissionReady':False,'ordinaryNativeAdoptionPassed':False,'next':'Review actual resolver/installed identities/ordinary raw observations and original ready:false manifest before a separately approved inventory dispatch','postgresStarted':False}
    (output/'intake-result.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--archive',type=Path);p.add_argument('--sha256');p.add_argument('--output',type=Path);p.add_argument('--ordinary-observations',type=Path);args=p.parse_args()
    if args.ordinary_observations:
        if sys.platform!='linux' or sys.version_info[:2]!=(3,11):raise ValueError('Actual installed Linux311 observations only')
        result=ordinary_observations(args.ordinary_observations)
    elif args.execute:result=execute(args.archive,args.sha256,args.output)
    else:raise ValueError('No implicit build/install/qualification; explicit reviewed --execute required')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
