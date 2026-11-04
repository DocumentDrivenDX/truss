#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Verify an actual pinned hosted-input archive; deferred templates refuse.

No downloads, builds, installs, baseline generation or native execution here.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path,PurePosixPath
import re
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]


def digest(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}',value) is None or set(value)=={'0'}:
        raise ValueError('Actual nonzero SHA256 required; deferred values cannot execute')
    return value


def relative(value):
    if type(value) is not str:raise ValueError('Actual relative input path required')
    p=PurePosixPath(value)
    if value in ('','.','..') or p.is_absolute() or '..' in p.parts or str(p)!=value or '\\' in value or any(ord(c)<32 or ord(c)==127 for c in value):
        raise ValueError('Closed relative hosted input path required')
    return value


def validate_selector(selected,phase,legacy):
    if selected is not True or phase not in ('intake','inventory','qualify119') or any(value is not False for value in legacy):
        raise ValueError('Select only the explicit candidate phase; all other expensive selectors must be false')
    return phase


def identity_fields(manifest):
    owners=manifest.get('ownerIdentities')
    if type(owners) is not dict or set(owners)!={'core','weft','truss'}:raise ValueError('Actual owner/module/resource identities required')
    for key in ('core','weft'):
        owner=owners[key]
        if type(owner) is not dict:raise ValueError('Actual owner identity object required')
        if type(owner.get('sourceCommit')) is not str or re.fullmatch('[0-9a-f]{40}',owner['sourceCommit']) is None:
            raise ValueError('Actual owner source commit required')
        digest(owner.get('wheelSha256'));relative(owner.get('wheelPath'));digest(owner.get('moduleSha256'));relative(owner.get('modulePath'))
    if type(owners['truss']) is not dict:raise ValueError('Actual Truss identity object required')
    core=owners['core'];digest(core.get('resourceManifestSha256'))
    if type(core.get('resourceSourceCommit')) is not str or re.fullmatch('[0-9a-f]{40}',core['resourceSourceCommit']) is None:
        raise ValueError('Actual canonical resource source required')
    resources=core.get('resources')
    if type(resources) is not dict or set(resources)!={'coreSchema','referenceSchema','packageSchema','constraints','domainPolicy','tablesPackage','actionsPackage','bindingPackage','stableBindingPackage'}:
        raise ValueError('All nine actual canonical resource identities required')
    for entry in resources.values():relative(entry.get('path'));digest(entry.get('sha256'))
    digest(owners['truss'].get('nativeManifestSha256'))
    wheels=manifest.get('wheels')
    if type(wheels) is not dict or set(wheels)!={'truss','core','access','weft'}:raise ValueError('Four actual wheel identities required')
    for selected in wheels.values():relative(selected.get('path'));digest(selected.get('sha256'))
    for key in ('core','weft'):
        if wheels[key]!={'path':owners[key]['wheelPath'],'sha256':owners[key]['wheelSha256']}:raise ValueError('Owner/wheel identity correspondence required')
    if wheels['truss']['path']!=manifest.get('candidateWheel'):raise ValueError('Candidate wheel identity differs')
    return owners


def prepare(archive,expected,output,phase,*,root=ROOT):
    if phase not in ('inventory','qualify119'):raise ValueError('Select one reviewed hosted phase')
    raw=Path(archive).read_bytes()
    if sha256(raw).hexdigest()!=digest(expected):raise ValueError('Actual hosted archive digest differs')
    output=Path(output).resolve()
    if output.exists():raise ValueError('Refuse existing hosted input output')
    with ZipFile(archive) as z:
        names=z.namelist()
        if len(set(names))!=len(names) or 'hosted-input.json' not in names:raise ValueError('One original hosted manifest required')
        manifest=json.loads(z.read('hosted-input.json'))
        if manifest.get('schema')!='truss-temporal-hosted-input/1' or manifest.get('ready') is not True or manifest.get('phase')!=phase:
            raise ValueError('Deferred or wrong-phase hosted input; actual reviewed artifacts required')
        identity_fields(manifest)
        from temporal_qualification_support import assert_qualification_checkout
        identity=assert_qualification_checkout(root,manifest.get('sourceCommit'),manifest.get('sourceTree'))
        entries=manifest.get('files')
        if type(entries) is not dict or not entries or set(names)!={'hosted-input.json',*entries}:
            raise ValueError('Complete original hosted input inventory required')
        for name,expected_file in entries.items():
            relative(name);info=z.getinfo(name)
            if (info.external_attr>>16)&0o170000==0o120000 or name.endswith('/'):
                raise ValueError('Only original regular hosted files accepted')
            if sha256(z.read(name)).hexdigest()!=digest(expected_file):raise ValueError('Original hosted payload differs: '+name)
        selected=relative(manifest.get('candidateWheel'))
        if selected not in entries or not selected.startswith('wheelhouse/') or not selected.endswith('.whl'):
            raise ValueError('Actual candidate wheel in admitted wheelhouse required')
        for selected_wheel in manifest['wheels'].values():
            name=selected_wheel['path']
            if not name.startswith('wheelhouse/') or name not in entries or entries[name]!=selected_wheel['sha256']:
                raise ValueError('Selected wheel must match the complete archive payload')
        if not any(n.startswith('wheelhouse/') and n.endswith('.whl') for n in entries):raise ValueError('Actual normal-resolver wheelhouse required')
        if phase=='qualify119':
            admission=relative(manifest.get('admission'))
            if admission not in entries:raise ValueError('Actual final admission required')
            # No string placeholder substitutions: paths are reviewed runner
            # paths in the actual admission. The original bytes remain intact.
            actual=json.loads(z.read(admission))
            if actual.get('sourceCommit')!=identity['commit'] or actual.get('sourceTree')!=identity['tree']:
                raise ValueError('Final admission and selected checkout identity differ')
        output.mkdir(parents=True,exist_ok=False)
        for name in names:
            target=output/relative(name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    result={'scope':'Verified hosted input bytes only; no qualification','phase':phase,'archiveSha256':expected,
        'sourceIdentity':identity,'candidateWheel':str(output/selected),'candidateWheelSha256':entries[selected],
        'wheelhouse':str(output/'wheelhouse'),'manifest':str(output/'hosted-input.json')}
    if phase=='qualify119':result['admission']=str(output/admission)
    (output/'verified-input.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def verify_installed(input_root):
    from importlib import import_module
    from typed_sdk_cohort import _installed_wheel
    from release_cohort import load_cohort,verify_installed as verify_versions
    root=Path(input_root);manifest=json.loads((root/'hosted-input.json').read_bytes());owners=identity_fields(manifest)
    cohort=load_cohort(require_qualified=True);verify_versions()
    import truss
    package=Path(truss.__file__).resolve().parent
    for key,package_name in (('truss','truss'),('core','umf'),('access','umf_access'),('weft','weft')):
        wheel=manifest['wheels'][key]
        installed=_installed_wheel(root/wheel['path'],wheel['sha256'],package_name,cohort[key]['distribution'])
        if installed['version']!=cohort[key]['version']:raise ValueError('Actual selected wheel version differs')
    from truss._temporal_owner import _inspector
    from truss._temporal_compiler import compiler
    _inspector()
    if compiler() is None:raise ValueError('Actual four-checker native Weft enrollment required')
    from truss.catalog_runtime import _release
    if _release()[1]!=owners['truss']['nativeManifestSha256']:raise ValueError('Actual native manifest differs')
    for key,package_name,native_name,enrollment in (('core','umf','umf._rust','manifest.json'),('weft','weft','weft.weft','compiler.json')):
        selected=owners[key];facade=import_module(package_name);native=import_module(native_name)
        if key=='core':native=native._rust_core
        base=Path(facade.__file__).resolve().parent;module=Path(native.__file__).resolve()
        if not module.is_relative_to(base) or str(module.relative_to(base))!=selected['modulePath'] or sha256(module.read_bytes()).hexdigest()!=selected['moduleSha256']:
            raise ValueError('Actual loaded owner native module differs: '+key)
        issued=json.loads((package/'_temporal_owner'/enrollment).read_bytes())
        if issued['sourceCommit']!=selected['sourceCommit']:raise ValueError('Actual compiled enrollment source differs: '+key)
        wheel=selected.get('wheelPath');relative(wheel)
        _installed_wheel(root/wheel,selected['wheelSha256'],package_name,cohort['core' if key=='core' else 'weft']['distribution'])
    source_raw=(package/'_temporal_owner/source.json').read_bytes();source=json.loads(source_raw)
    if sha256(source_raw).hexdigest()!=owners['core']['resourceManifestSha256'] or source['sourceCommit']!=owners['core']['resourceSourceCommit']:
        raise ValueError('Actual canonical resource manifest differs')
    for name,entry in owners['core']['resources'].items():
        if entry['path']!=source['resources'][name]['file'] or entry['sha256']!=source['resources'][name]['sha256'] or sha256((package/'_temporal_owner'/entry['path']).read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('Actual canonical resource bytes differ: '+name)
    return {'scope':'Actual installed identity correspondence only; not native qualification','verified':True,'ownerIdentities':owners}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verify-installed',type=Path)
    p.add_argument('--archive',type=Path);p.add_argument('--sha256')
    p.add_argument('--output',type=Path);p.add_argument('--phase',choices=('inventory','qualify119'))
    a=p.parse_args()
    if a.verify_installed:result=verify_installed(a.verify_installed)
    else:
        if a.archive is None or a.sha256 is None or a.output is None:raise ValueError('Actual archive/hash/fresh output required')
        result=prepare(a.archive,a.sha256,a.output,a.phase)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
