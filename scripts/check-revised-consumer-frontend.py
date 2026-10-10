#!/usr/bin/env python3
"""Prepare/assess original revised consumer SQL using frozen Weft test frontend."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'docs/helix/04-build/evidence/design-audit'
SNAPSHOT = ROOT / 'docs/helix/04-build/evidence/consumer-revision-2026-10-09'
REVISION = 'f05f2df09e9c2494ac8c6d703dfe38413dbc4181'
ARCHIVE_SHA = '1784d4283b4060c39af2dee6a283472cd539eacc119abb8576a57ae106fb51ea'
BLOCKED = {'read.relationship-filter-both-directions:0', 'read.relationship-filter-both-directions:1',
           'read.relationship-filter-both-directions:2', 'read.repeated-relationship-predicates-mean-both:2',
           'read.repeated-relationship-predicates-mean-both:3'}
HARNESS = '''#[test]
fn revised_original_consumer_review() {
 let cases: serde_json::Value = serde_json::from_str(include_str!("../../../truss-consumer-revised-inputs.json")).unwrap();
 let mut results = Vec::new();
 for case in cases.as_array().unwrap() {
  let response: serde_json::Value = serde_json::from_str(&weft_core::frontend_json(&case["request"].to_string())).unwrap();
  results.push(serde_json::json!({"source":case["source"],"variant":case["variant"],"response":response}));
 }
 let output=std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("truss-consumer-revised-results.json");
 std::fs::write(output,serde_json::to_string_pretty(&results).unwrap()).unwrap();
}
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inputs():
    revision = json.loads((AUDIT/'consumer-revision-2026-10-09.json').read_bytes())
    for name,digest in revision['sources'].items():
        assert sha((SNAPSHOT/name).read_bytes())==digest
    old_raw=(AUDIT/'consumer-logical-frontend-inputs.json').read_bytes()
    assert sha(old_raw)==revision['previousInputsSha256']
    old=json.loads(old_raw)
    corpus=json.loads((SNAPSHOT/'corpus.json').read_bytes())
    queries=[(case['id'],i,step) for case in corpus['cases'] for i,step in enumerate(case['steps']) if step['op']=='query']
    assert len(queries)==45
    result=[]
    for filename,suffix in [('module.umf.json','/src/hohfeld/conformance/module.umf.json'),('example.umf.json','/examples/catalog/catalog.umf.json')]:
        original=next(row for row in old if row['source'].endswith(suffix) and row['variant']=='original')
        raw=(SNAPSHOT/filename).read_bytes()
        for case,i,step in queries:
            assert not step.get('params'), 'Parameterized consumer input needs its separately owned admission'
            request=copy.deepcopy(original['request'])
            assert len(request['modules'])==1
            request['modules'][0]['documentJson']=raw.decode('utf-8')
            request['modules'][0]['pin']['sha256']=sha(raw)
            request.update(dialect='weft-sql/0.2.0',sql=step['sql'],parameters={})
            result.append({'source':filename,'variant':f'{case}:{i}','request':request})
    return result


def verify_owner(workspace, repository):
    archive=subprocess.check_output(['git','-C',str(repository),'archive',REVISION])
    assert sha(archive)==ARCHIVE_SHA
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        for member in tree.getmembers():
            if member.isfile():
                assert (workspace/member.name).read_bytes()==tree.extractfile(member).read(), member.name
    return sha(archive)


def main():
    global REVISION, ARCHIVE_SHA
    if len(sys.argv) not in (5,8): raise SystemExit('usage: ACTION WORKSPACE OWNER TOOLCHAIN [COMMIT ARCHIVE_SHA NEW_RECEIPT_NAME]')
    action,workspace,repository,toolchain=sys.argv[1:5]
    receipt_name='consumer-revised-frontend.json'
    if len(sys.argv)==8:
        REVISION,ARCHIVE_SHA,receipt_name=sys.argv[5:]
        assert len(REVISION)==40 and all(c in '0123456789abcdef' for c in REVISION)
        assert len(ARCHIVE_SHA)==64 and all(c in '0123456789abcdef' for c in ARCHIVE_SHA)
    assert Path(receipt_name).name==receipt_name and receipt_name.endswith('.json')
    destination=AUDIT/receipt_name
    if destination.exists(): raise SystemExit('refusing to replace an existing receipt')
    workspace,repository,toolchain=Path(workspace),Path(repository),Path(toolchain)
    environment=dict(os.environ,CARGO_HOME=str(toolchain/'cargo'),RUSTUP_HOME=str(toolchain/'rustup'))
    rust=subprocess.check_output([str(toolchain/'cargo/bin/rustc'),'--version'],env=environment,text=True).strip()
    cargo=subprocess.check_output([str(toolchain/'cargo/bin/cargo'),'--version'],env=environment,text=True).strip()
    assert rust.startswith('rustc 1.90.0 '), 'Unqualified test toolchain' 
    archive=verify_owner(workspace,repository)
    cases=inputs();wire=json.dumps(cases,ensure_ascii=False).encode('utf-8')
    target=workspace/'truss-consumer-revised-inputs.json'
    harness=workspace/'crates/weft-core/tests/truss_consumer_revised.rs'
    if action=='prepare':
        assert not target.exists() and not harness.exists(), 'Fresh owned harness paths required'
        target.write_bytes(wire);harness.write_text(HARNESS)
        print('Prepared90 original revised consumer inputs; no source/name/SQL rewriting')
        return
    assert action in ('run','assess') and target.read_bytes()==wire and harness.read_text()==HARNESS
    output=workspace/'crates/weft-core/truss-consumer-revised-results.json'
    run_path=workspace/'truss-consumer-revised-run.json'
    if action=='run':
        output.unlink(missing_ok=True);run_path.unlink(missing_ok=True)
        started=time.monotonic()
        result=subprocess.run([str(toolchain/'cargo/bin/cargo'),'test','--locked','--offline','-p','weft-core','--test','truss_consumer_revised'],
                              cwd=workspace,env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60)
        assert result.returncode==0 and output.is_file(), 'Actual frontend run failed; no receipt'
        run_path.write_text(json.dumps({'exitStatus':result.returncode,'durationMs':round((time.monotonic()-started)*1000),
                                       'inputsSha256':sha(wire),'harnessSha256':sha(harness.read_bytes()),
                                       'outputSha256':sha(output.read_bytes()),'sourceArchiveSha256':archive,
                                       'rawSubprocessCapture':'disabled; actual process status and structured output checked'}))
    run=json.loads(run_path.read_bytes())
    assert run['exitStatus']==0 and run['inputsSha256']==sha(wire) and run['harnessSha256']==sha(harness.read_bytes()) and run['sourceArchiveSha256']==archive
    raw=(workspace/'crates/weft-core/truss-consumer-revised-results.json').read_bytes()
    assert run['outputSha256']==sha(raw)
    rows=json.loads(raw);assert len(rows)==len(cases)==90
    observations=[]
    for case,row in zip(cases,rows):
        assert (case['source'],case['variant'])==(row['source'],row['variant'])
        response=row['response'];blocked=case['variant'] in BLOCKED
        assert response['status']==('blocked' if blocked else 'resolved')
        assert 'sql' not in response
        assert [d['code'] for d in response['diagnostics']]==(['WFT-NAME-MISSING'] if blocked else [])
        if not blocked:
            assert response['retainedModules']==case['request']['modules']
            assert response['logicalPlan']['modulePins']==[m['pin'] for m in case['request']['modules']]
        observations.append({'source':row['source'],'caseStep':row['variant'],'status':response['status'],
                             'diagnostics':response['diagnostics'],'responseSha256':sha(json.dumps(response,sort_keys=True,separators=(',',':')).encode())})
    receipt={'scope':'Actual frozen Weft test frontend, revised owner-authored model/corpus inputs; no SQL lowering/native/parsed-input ABI qualification',
             'revision':REVISION,'sourceArchiveSha256':archive,'cargoLockSha256':sha((workspace/'Cargo.lock').read_bytes()),
             'rustVersion':rust,'cargoVersion':cargo,'actualRun':run,
             'command':'cargo test --locked --offline -p weft-core --test truss_consumer_revised',
             'inputsSha256':sha(wire),'harnessSha256':sha(harness.read_bytes()),'outputSha256':sha(raw),
             'producerSha256':sha(Path(__file__).read_bytes()),'resolved':80,'blocked':10,'observations':observations,
             'nativeQualified':False,'publicCompilerQualified':False}
    with destination.open('x') as stream: stream.write(json.dumps(receipt,indent=2)+'\n')
    print('90 revised-original query observations:80 resolved,10 original relationship-name refusals')


if __name__=='__main__':
    main()
