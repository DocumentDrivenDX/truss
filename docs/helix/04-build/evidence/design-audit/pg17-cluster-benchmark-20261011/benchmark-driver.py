import json, os, sys, time, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'/Users/erik/Projects/truss/scripts')
from native_fixture import WorkerCluster
root=Path('/Users/erik/Projects/truss')
evidence=root/'docs/helix/04-build/evidence/design-audit'
prior=json.loads((evidence/'pg17-shared-workers-final-20261011/pgserver-pg17.11-qualification.json').read_text())
cases=prior['outcomes']; isolated=[x for x in cases if x['lane']=='isolated-lifecycle']; native=[x for x in cases if x['lane']=='shared-worker']
native.sort(key=lambda x: next(i for i,c in enumerate(['caller-reset','isolation','origin','structure','populated-guards','issued-base','issued-asserted','issued-epoch','issued-configuration','four-family-driver','private-callable-inventory','elevation']) if c==x['case']))
out=evidence/('pg17-cluster-benchmark-'+str(time.time_ns()));out.mkdir()
env=os.environ.copy();env.pop('TRUSS_NATIVE_WORKER',None);env['PYTHONPATH']=str(root/'scripts')
results=[]
def execute(case, folder, worker=None):
    local={**env,'TRUSS_NATIVE_EVIDENCE_DIR':str(folder),'TRUSS_TIMING_FILE':str(folder/(case['case']+'-timing.json'))}
    if worker:local.update(worker.environment())
    command=[sys.executable,*case['command'][1:]]
    if case in native:command.insert(1,str(Path(__file__).with_name('benchmark-child.py')))
    t=time.perf_counter(); p=subprocess.run(command,cwd=root,env=local,capture_output=True,timeout=240)
    if worker:worker.verify_clean()
    elapsed=time.perf_counter()-t
    (folder/(case['case']+'.log')).write_bytes(p.stdout+p.stderr)
    print(case['case'],round(elapsed,3),p.returncode,flush=True)
    if p.returncode:raise RuntimeError(case['case'])
    timing=Path(local['TRUSS_TIMING_FILE'])
    return {'case':case['case'],'elapsedSeconds':elapsed,'events':json.loads(timing.read_text()) if timing.exists() else []}
# Measure lifecycle once: identical isolated lane in both configurations.
f=out/'lifecycle';f.mkdir();t=time.perf_counter(); lifecycle=[execute(c,f) for c in isolated]; lifecycle_wall=time.perf_counter()-t
for mode,count in [('per-experiment',0),('shared-one-worker',1),('shared-two-workers',2)]:
    f=out/mode;f.mkdir(exist_ok=True);t=time.perf_counter(); workers=[]
    if not count: outcomes=[execute(c,f) for c in native]
    else:
        def lane(index):
            worker=WorkerCluster();start=time.perf_counter();worker.__enter__();ready=time.perf_counter()-start
            try: checks=[execute(c,f,worker) for c in native[index::count]]
            finally:
                start=time.perf_counter();worker.close();stop=time.perf_counter()-start
            return {'worker':index,'startupSeconds':ready,'cleanupSeconds':stop,'outcomes':checks}
        with ThreadPoolExecutor(max_workers=count) as pool:workers=list(pool.map(lane,range(count)))
        outcomes=[c for w in workers for c in w['outcomes']]
    result={'mode':mode,'nativeWallSeconds':sum(c['elapsedSeconds'] for c in outcomes) if not count else time.perf_counter()-t,'workers':workers,'outcomes':outcomes}
    results.append(result);print('MODE',mode,result['nativeWallSeconds'],flush=True)
receipt={'postgres':'17.11','samplesPerMode':1,'includes':'Process launch, cluster initialization/readiness, fresh database/role setup, checks, baseline verification, database/role deletion, cluster stop and owned-directory cleanup','lifecycleWallSeconds':lifecycle_wall,'lifecycle':lifecycle,'results':results}
(out/'benchmark.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt),flush=True)
