"""Promote only an immutable tag's fully completed, tested first-run artifact."""
import argparse
from datetime import datetime
from hashlib import sha256
from zipfile import ZipFile
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib


def command(*args):
    return subprocess.check_output(args,text=True)


def api(path):
    return json.loads(command('gh','api',path))


def verify(run_id,tag,provenance,packages=None):
    if re.fullmatch(r'[1-9][0-9]{0,19}',run_id) is None or re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+',tag) is None:
        raise ValueError('Exact run id and release tag required')
    repo=os.environ.get('GITHUB_REPOSITORY','DocumentDrivenDX/truss')
    if repo!='DocumentDrivenDX/truss':raise ValueError('Original Truss repository required')
    commit=command('git','rev-parse',tag+'^{commit}').strip()
    project=tomllib.loads(command('git','show',tag+':packages/python/pyproject.toml'))['project']
    if tag!='v'+project['version']:raise ValueError('Original tagged distribution version required')
    workflow=command('git','show',tag+':.github/workflows/release.yml')
    publisher=workflow.split('      - name: Record exact assets and publish\n',1)[1].split('        run: |\n',1)[1]
    # The recovery publisher below is the reviewed original recipe. A future
    # recipe change must be adopted explicitly rather than using stale pins.
    if sha256(publisher.encode()).hexdigest()!='a739305df2edfb95ee2d6f2269c6d9d15cb91737aa4fb561a90370ee96886754':
        raise ValueError('Exact supported source publisher recipe required')
    native=workflow.split('\n  native:\n',1)[1].split('\n  publish:\n',1)[0]
    required=re.findall(r'^      - name: (.+)$',native,re.M)
    if len(required)<3 or len(required)!=len(set(required)):
        raise ValueError('Original named native gate inventory required')
    prefix='repos/'+repo
    run=api(prefix+'/actions/runs/'+run_id)
    if (run['path']!='.github/workflows/release.yml' or run['event']!='push'
        or run['head_branch']!=tag or run['head_sha']!=commit or run['status']!='completed'
        or run['run_attempt']!=1 or run['repository']['full_name']!=repo or run['conclusion']!='cancelled'):
        raise ValueError('Completed original first-attempt tag workflow required')
    jobs=api(prefix+'/actions/runs/'+run_id+'/attempts/1/jobs?per_page=100')['jobs']
    expected={'package','native (macos-14)','native (ubuntu-24.04)','publish'}
    if len(jobs)!=4 or {j['name'] for j in jobs}!=expected:
        raise ValueError('Exact original release job inventory required')
    by_name={j['name']:j for j in jobs}
    publish=by_name['publish']
    if (publish['head_sha']!=commit or publish['run_attempt']!=1 or publish['status']!='completed'
        or publish['conclusion']!='skipped' or publish['steps']
        or not any(j['conclusion']=='cancelled' for name,j in by_name.items() if name.startswith('native '))):
        raise ValueError('Unpublished cancelled-native timeout recovery required')
    for name in ('package','native (macos-14)','native (ubuntu-24.04)'):
        job=by_name[name]
        if (job['head_sha']!=commit or job['run_attempt']!=1 or job['status']!='completed'
            or not job['steps'] or any(s['status']!='completed' or s['conclusion']!='success' for s in job['steps'])):
            raise ValueError('Every original package/native step must have succeeded: '+name)
        names={s['name'] for s in job['steps']}
        needed=required if name.startswith('native ') else ['Check version and build package']
        if not set(needed)<=names:raise ValueError('Missing required original gate steps: '+name)
        if job['conclusion']=='cancelled' and name.startswith('native '):
            annotations=api(prefix+'/check-runs/'+str(job['id'])+'/annotations?per_page=100')
            if len(annotations)>=100:
                raise ValueError('Complete untruncated timeout annotation inventory required')
            failures=[a['message'] for a in annotations if a['annotation_level']=='failure']
            if failures!=['The job has exceeded the maximum execution time of 15m0s']:
                raise ValueError('Only the post-success job timeout is recoverable')
        elif job['conclusion']!='success':
            raise ValueError('Original gate did not succeed: '+name)
    artifacts=api(prefix+'/actions/runs/'+run_id+'/artifacts?per_page=100')['artifacts']
    if len(artifacts)!=1:raise ValueError('One original package artifact required')
    artifact=artifacts[0];package=by_name['package']
    if (artifact['name']!='python-package' or artifact['expired']
        or artifact['workflow_run']['id']!=int(run_id) or artifact['workflow_run']['head_sha']!=commit
        or re.fullmatch(r'sha256:[0-9a-f]{64}',artifact['digest']) is None
        or not datetime.fromisoformat(package['started_at'].replace('Z','+00:00'))
          <=datetime.fromisoformat(artifact['created_at'].replace('Z','+00:00'))
          <=datetime.fromisoformat(package['completed_at'].replace('Z','+00:00'))):
        raise ValueError('Original unexpired package upload and source correspondence required')
    payloads={}
    if packages is not None:
        packages.mkdir(parents=True,exist_ok=False)
        archive=packages.with_suffix('.zip')
        with archive.open('wb') as target:
            subprocess.run(['gh','api',prefix+'/actions/artifacts/'+str(artifact['id'])+'/zip'],stdout=target,check=True)
        if 'sha256:'+sha256(archive.read_bytes()).hexdigest()!=artifact['digest']:
            raise ValueError('Exact original tested artifact archive digest required')
        with ZipFile(archive) as original:
            names=original.namelist()
            expected={'truss_toolkit-'+project['version']+'-py3-none-any.whl',
                      'truss_toolkit-'+project['version']+'.tar.gz'}
            if len(names)!=2 or set(names)!=expected:
                raise ValueError('Only original tagged wheel and sdist are admitted')
            for name in names:
                raw=original.read(name);(packages/name).write_bytes(raw)
                payloads[name]=sha256(raw).hexdigest()
    record={'sourceRun':int(run_id),'sourceAttempt':1,'tag':tag,'sourceCommit':commit,
        'promotionWorkflowCommit':os.environ.get('GITHUB_SHA'),
        'promotionWorkflowRun':os.environ.get('GITHUB_RUN_ID'),
        'testedPackageSha256':payloads,
        'artifact':{k:artifact[k] for k in ('id','name','digest','size_in_bytes','created_at')},
        'gates':[{k:j[k] for k in ('id','name','conclusion','run_attempt')} for j in jobs],
        'requiredNativeSteps':required,
        'scope':'Original tested wheel/sdist; timeout recovery only after every required step succeeded'}
    provenance.write_text(json.dumps(record,indent=2)+'\n')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as output:
            output.write(f'commit={commit}\nartifact_id={artifact["id"]}\n')
    print(json.dumps({'tag':tag,'commit':commit,'artifactId':artifact['id'],'verified':True}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id');parser.add_argument('tag');parser.add_argument('provenance',type=Path)
    parser.add_argument('--packages',type=Path)
    args=parser.parse_args();verify(args.run_id,args.tag,args.provenance,args.packages)
