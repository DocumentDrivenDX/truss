#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Assemble FRESH0.76 baseline from two real native initializer observations.

Writes a NEW staging directory only. Never edits old profiles, SQL, initializer,
fixtures or admitted historical lineage. Native differences other than the
existing exact horizon bounds require review rather than normalization.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()


def initialization_rules(left,right):
    if left.keys()!=right.keys():raise ValueError('Native inventory category membership differs')
    rules=[]
    for category,rows in left.items():
        other=right[category]
        if rows==other:continue
        if category!='relations' or len(rows)!=len(other):raise ValueError('Unreviewed native initializer definition difference: '+category)
        for before,after in zip(rows,other,strict=True):
            if before==after:continue
            if (len(before)<8 or len(before)!=len(after) or before[0]!='journal_runtime_horizon'
                    or before[:7]+before[8:]!=after[:7]+after[8:]):
                raise ValueError('Unreviewed native initializer difference')
            rules.append({'surface':'relations','identity':['journal_runtime_horizon'],
                'rows':sorted([before,after],key=canonical)})
    if len(rules)>1:raise ValueError('At most the exact observed horizon pair permitted')
    return rules


def assemble(selections,output):
    if len(selections)!=2:raise ValueError('Two exact native initializer receipt pins required')
    output=Path(output).resolve()
    if output.exists():raise ValueError('Refuse existing staged baseline output')
    from temporal_qualification_support import _git,commit_tree,assert_qualification_checkout
    assembly_commit=_git(ROOT,'rev-parse','HEAD').decode().strip()
    assembly_tree=commit_tree(ROOT,assembly_commit)
    assert_qualification_checkout(ROOT,assembly_commit,assembly_tree,
        evidence_roots=[Path(entry['path']).resolve().parent for entry in selections]+[output])
    captures=[];zones=set();selected_files={}
    for entry in selections:
        path=Path(entry['path']).resolve();raw=path.read_bytes()
        if sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Actual capture receipt digest differs')
        receipt=json.loads(raw)
        if (receipt.get('passed') is not True or receipt.get('cleanupConfirmed') is not True
                or receipt.get('historicalProfilesModified') is not False
                or receipt.get('sysPlatform')!='linux' or receipt.get('machine')!='x86_64' or receipt.get('pythonMajorMinor')!=[3,11]
):
            raise ValueError('Successful genuine original-source capture and cleanup proof required')
        from temporal_qualification_support import commit_tree,_git
        if commit_tree(ROOT,receipt.get('sourceCommit'))!=receipt.get('sourceTree'):
            raise ValueError('Original initializer commit/tree required')
        if sha256(_git(ROOT,'show',receipt['sourceCommit']+':scripts/capture-temporal-native-inventory.py')).hexdigest()!=receipt.get('producerSha256'):
            raise ValueError('Original committed capture producer required')
        proof=json.loads(path.with_name('cleanup.json').read_bytes())['clusters']
        if not proof or not all(r.get('confirmed') is True and r.get('dataDeleted') is True and r.get('pgCtlStatus')==3 and r.get('originalPostmasterPidAbsent') is True for r in proof):
            raise ValueError('Original postmaster absence and pg_ctl3 before deletion required')
        body=path.with_name('native-profile-observation.json').read_bytes()
        if sha256(body).hexdigest()!=receipt['profileSha256']:raise ValueError('Original native profile bytes changed')
        profile=json.loads(body)
        if profile['manifest']['releaseId']!='truss-catalog-runtime/0.76-temporal-candidate' or receipt['runtimeManifestSha256']!=profile['sha256']:
            raise ValueError('Fresh actual0.76 target required')
        original_manifest=path.with_name('original-runtime-manifest.json').read_bytes()
        if sha256(original_manifest).hexdigest()!=profile['sha256'] or json.loads(original_manifest)!=profile['manifest']:
            raise ValueError('Original candidate native manifest correspondence required')
        if profile['observationTimeZone']!='UTC' or profile['initializationTimeZone']!=receipt['initializationTimeZone']:
            raise ValueError('Actual initialization and observation zones required')
        zone=profile['initializationTimeZone']
        if zone in zones:raise ValueError('Duplicate native initializer zone')
        zones.add(zone);captures.append((receipt,profile))
        selected_files['native076-capture-'+entry['sha256']+'.json']=raw
    if zones!={'UTC','America/New_York'}:raise ValueError('Both original initializer timezone observations required')
    left,right=captures
    for key in ('sourceCommit','sourceTree','nonMigrationPackageFiles'):
        if not left[0].get(key) or left[0][key]!=right[0].get(key):raise ValueError('Exact initializer source/package closure required')
    for key in ('sha256','manifest','configuration','acl','aclNameProfile'):
        if left[1][key]!=right[1][key]:raise ValueError('Initializer source/configuration/ACL differs: '+key)
    if left[1]['aclNameProfile']!='truss-native-acl-names/0.2':raise ValueError('Complete exact native ACL names required')
    rules=initialization_rules(left[1]['inventory'],right[1]['inventory'])
    target=dict(left[1]);target.pop('rawAcl',None)
    target['definitionAlternatives']=[];target['initializationAlternatives']=rules
    digest=target['sha256'];profile_name=digest+'.json';selected_files[profile_name]=canonical(target)
    proof={'scope':'Exact fresh0.76 initializer observations only; no timezone conversion, widened initializer or historical admission',
        'observationTimeZone':'UTC','qualifiedTimeZones':['America/New_York','UTC'],'rules':rules,
        'captures':selections,'sourceCommit':left[0]['sourceCommit'],'sourceTree':left[0]['sourceTree'],
        'assemblyCommit':assembly_commit,'assemblyTree':assembly_tree,'runtimeManifestSha256':digest,'sourceWheels':{}}
    initialization='native076-initialization-'+sha256(canonical(proof)).hexdigest()[:16]+'.json'
    selected_files[initialization]=canonical(proof)
    original=ROOT/'packages/python/src/truss/_migrations';old=json.loads((original/'manifest.json').read_bytes())
    # Retain the original receipt model and generic deparse rule catalog BYTES.
    # This fresh target admits NO deparse alternatives, old runtime, or edge.
    names=(old['receiptModel']['artifact'],old['receiptModel']['evidence'],old['definitionEquivalence'])
    for name in names:
        body=(original/name).read_bytes()
        if sha256(body).hexdigest()!=old['files'][name]:raise ValueError('Original generic custody artifact changed')
        selected_files[name]=body
    model=json.loads(selected_files[old['receiptModel']['evidence']])
    if model['sourceSha256']!=target['manifest']['files'][old['receiptModel']['sourceFile']]:
        raise ValueError('Actual receipt source changed; explicit new model evidence required')
    manifest={'interfaceVersion':old['interfaceVersion'],'target':digest,'targetRelease':target['manifest']['releaseId'],
        'baseline':{**old['baseline'],'packageVersion':'0.0.56'},'sources':[],'sourceWheels':{},'edges':[],
        'receiptModel':old['receiptModel'],'definitionEquivalence':old['definitionEquivalence'],'initializationProfiles':initialization,
        'exactAclProfiles':{},'immutableFiles':sorted(selected_files),
        'files':{name:sha256(body).hexdigest() for name,body in sorted(selected_files.items())}}
    output.mkdir(parents=True,exist_ok=False)
    for name,body in selected_files.items():(output/name).write_bytes(body)
    (output/'manifest.json').write_bytes(canonical(manifest))
    return {'scope':'Fresh native observed baseline staging ONLY; full candidate campaign and source review remain required',
        'target':digest,'output':str(output),'files':manifest['files'],'historicalProfilesModified':False,'sources':[],'edges':[]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-pins',required=True,type=Path,help='JSON array of actual receipt path/SHA256 pairs')
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(assemble(json.loads(args.capture_pins.read_bytes()),args.output),indent=2))


if __name__=='__main__':main()
