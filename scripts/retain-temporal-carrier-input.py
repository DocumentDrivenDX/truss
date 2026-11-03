#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Retain authenticated owned DRAFT carrier bytes; no runtime code is imported."""
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile

REPO='DocumentDrivenDX/truss'
MAX_BUNDLE=67108864
MAX_MANIFEST=65536


def exact_int(value,limit=18446744073709551615):
    if type(value) is not str or re.fullmatch('[1-9][0-9]{0,19}',value) is None or int(value)>limit:
        raise ValueError('Exact positive bounded decimal required')
    return int(value)


def exact_sha(value,length=64):
    if type(value) is not str or re.fullmatch('[0-9a-f]{%d}'%length,value) is None or set(value)=={'0'}:
        raise ValueError('Exact source/digest required')
    return value


def safe(name):
    if type(name) is not str or not name or name.startswith('/') or '\\' in name or '\n' in name or any(x in ('','.','..') for x in name.split('/')):
        raise ValueError('Exact relative regular entry required')
    return name


def unique(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('Duplicate JSON member')
        result[key]=value
    return result


def parsed(raw):return json.loads(raw,object_pairs_hook=unique)


def file_sha(path):return sha256(Path(path).read_bytes()).hexdigest()


def source():
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],text=True).strip()
    if os.environ['GITHUB_SHA']!=commit or subprocess.check_output(['git','status','--porcelain','--untracked-files=all']).strip():
        raise ValueError('Actual clean controller commit/tree required')
    return {'commit':exact_sha(commit,40),'tree':exact_sha(tree,40)}



def require_action_token():
    # GH_TOKEN is injected only in the reviewed authentication/download step.
    # Never let gh silently fall back to an ambient local credential store.
    if os.environ.get('GITHUB_ACTIONS')!='true' or not os.environ.get('GH_TOKEN'):
        raise ValueError('Only explicit action-scoped github.token authentication permitted')


def get_command(endpoint):
    require_action_token()
    # A job token with draft-read capability must never become a general API
    # transport. Keep the original repository and exact GET endpoints closed.
    if type(endpoint) is not str:raise ValueError('Only closed carrier GET endpoints permitted')
    match=re.fullmatch(r'releases/([1-9][0-9]{0,19})(?:/assets\?per_page=100)?|releases/assets/([1-9][0-9]{0,19})',endpoint)
    if match is None:raise ValueError('Only closed carrier GET endpoints permitted')
    exact_int(match.group(1) or match.group(2))
    return ['gh','api','--method','GET',f'repos/{REPO}/'+endpoint]


def api(endpoint,target):
    # Host and repository are closed, credentials remain in GH_TOKEN only.
    command=get_command(endpoint)
    with Path(target).open('wb') as stream:
        subprocess.run(command,stdout=stream,check=True,timeout=180)
    return parsed(Path(target).read_bytes())


def download(asset,target,size,digest):
    if asset.get('state')!='uploaded' or type(asset.get('size')) is not int or asset['size']!=size or asset.get('digest')!='sha256:'+digest:
        raise ValueError('Original asset metadata size/digest differs')
    command=get_command(f'releases/assets/{asset["id"]}')
    with Path(target).open('wb') as stream:
        subprocess.run(command+['-H','Accept: application/octet-stream'],stdout=stream,check=True,timeout=180)
    if Path(target).stat().st_size!=size or file_sha(target)!=digest:raise ValueError('Actual carrier asset bytes differ')


def validate_bundle(archive,manifest):
    bundle=manifest['bundle'];rows=bundle['entries']
    if type(rows) is not list or len(rows)!=17 or len({r['path'] for r in rows})!=17:raise ValueError('Exact complete17 roster required')
    roster={safe(r['path']):r for r in rows}
    if sum(r['size'] for r in rows)>MAX_BUNDLE:raise ValueError('Bounded complete payload required')
    with ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=17 or set(names)!=set(roster) or len(set(names))!=len(names):raise ValueError('Complete original roster differs')
        for info in z.infolist():
            row=roster[safe(info.filename)];kind=(info.external_attr>>16)&0o170000
            if info.is_dir() or kind not in (0,0o100000) or type(row['size']) is not int or row['size']<0 or info.file_size!=row['size']:
                raise ValueError('Original regular member size/type required')
            if sha256(z.read(info)).hexdigest()!=exact_sha(row['sha256']):raise ValueError('Original roster bytes differ')
        intake=parsed(z.read('component-input.json'))
        if (type(manifest.get('expectedInputReady')) is not bool or intake.get('schema')!='truss-temporal-component-intake/1'
            or type(intake.get('ready')) is not bool or intake['ready'] is not manifest['expectedInputReady']):
            raise ValueError('Exact separately reviewed readiness bytes required; transport never promotes readiness')
        if {'commit':intake['sourceCommit'],'tree':intake['sourceTree']}!=manifest['bundleSource']:raise ValueError('Original bundle source differs')
        expected=intake['files']
        if set(expected)!=(set(roster)-{'component-input.json'}) or any(roster[n]['sha256']!=v for n,v in expected.items()):
            raise ValueError('Original complete intake inventory differs')
    return roster


def retain():
    temporary=Path(os.environ['RUNNER_TEMP']);proof=temporary/'carrier-proof';proof.mkdir(exist_ok=False)
    output=temporary/'temporal-input-retained'
    if output.exists():raise ValueError('Refuse stale retained output')
    require_action_token()
    controller=source();release_id=exact_int(os.environ['TN_RELEASE_ID']);bundle_id=exact_int(os.environ['TN_BUNDLE_ASSET_ID']);manifest_id=exact_int(os.environ['TN_MANIFEST_ASSET_ID'])
    bundle_size=exact_int(os.environ['TN_BUNDLE_SIZE'],MAX_BUNDLE);manifest_size=exact_int(os.environ['TN_MANIFEST_SIZE'],MAX_MANIFEST)
    bundle_sha=exact_sha(os.environ['TN_BUNDLE_SHA256']);manifest_sha=exact_sha(os.environ['TN_MANIFEST_SHA256'])
    marker=os.environ['TN_OWNERSHIP_MARKER']
    if re.fullmatch('TRUSS_QUALIFICATION_CARRIER:[A-Za-z0-9_-]{1,96}',marker) is None:raise ValueError('Exact owned carrier marker required')
    release=api(f'releases/{release_id}',proof/'original-release.json')
    if release.get('id')!=release_id or release.get('draft') is not True or release.get('published_at') is not None or release.get('prerelease') is not True:
        raise ValueError('Owned unpublished DRAFT release required')
    assets=api(f'releases/{release_id}/assets?per_page=100',proof/'original-assets.json')
    if type(assets) is not list or len(assets)!=2 or {r['id'] for r in assets}!={bundle_id,manifest_id}:raise ValueError('Only exact two reviewed carrier assets permitted')
    assets={r['id']:r for r in assets}
    download(assets[manifest_id],proof/'original-transport-manifest.json',manifest_size,manifest_sha)
    manifest=parsed((proof/'original-transport-manifest.json').read_bytes())
    if manifest.get('schema')!='truss-temporal-input-carrier/1' or manifest.get('ready') is not False or manifest['controllerSource']!=controller:
        raise ValueError('Exact reviewed controller identity and transport-only manifest required')
    carrier=manifest['carrier'];bundle=manifest['bundle']
    if (carrier['repository']!=REPO or release['author']['login']!=carrier['authorLogin']
        or release['tag_name']!=carrier['tagName'] or release['name']!=carrier['name'] or release['body']!=carrier['body']
        or carrier['body'].splitlines()[0]!=marker or release['target_commitish']!=controller['commit']
        or assets[bundle_id]['name']!=carrier['bundleAssetName'] or assets[manifest_id]['name']!=carrier['manifestAssetName']
        or any(r['uploader']['login']!=carrier['authorLogin'] for r in assets.values())
        or bundle['filename']!=carrier['bundleAssetName'] or bundle['size']!=bundle_size or bundle['sha256']!=bundle_sha):
        raise ValueError('Original carrier ownership/name/source/asset binding differs')
    for identity in (manifest['bundleSource'],manifest['controllerSource']):
        exact_sha(identity['commit'],40);exact_sha(identity['tree'],40)
    archive=proof/'original-bundle.zip';download(assets[bundle_id],archive,bundle_size,bundle_sha)
    roster=validate_bundle(archive,manifest)
    source()  # No source mutation while obtaining carrier bytes.
    output.mkdir()
    with ZipFile(archive) as z:
        for name in sorted(roster):
            target=output/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    if any(file_sha(output/name)!=row['sha256'] for name,row in roster.items()):raise ValueError('Retained original payload differs')
    result={'scope':'Byte retention ONLY; no qualification/publication/resolver/build/PG','ready':False,'carrierRepository':REPO,'releaseID':release_id,'bundleAssetID':bundle_id,'manifestAssetID':manifest_id,'bundleSHA256':bundle_sha,'manifestSHA256':manifest_sha,'bundleSource':manifest['bundleSource'],'controllerSource':controller,'entries':17,'runID':os.environ['GITHUB_RUN_ID'],'attempt':os.environ['GITHUB_RUN_ATTEMPT'],'jobName':os.environ['GITHUB_JOB'],'workflowRef':os.environ['GITHUB_WORKFLOW_REF'],'cleanupPerformed':False}
    (proof/'retention-result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    try:retain()
    except BaseException as error:
        proof=Path(os.environ['RUNNER_TEMP'])/'carrier-proof';proof.mkdir(exist_ok=True)
        (proof/'failure.json').write_text(json.dumps({'scope':'Transport failure; no acceptance','errorClass':type(error).__name__,'message':str(error)},indent=2)+'\n')
        raise
