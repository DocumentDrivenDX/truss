"""Small local lifecycle timing sample; no general performance claim."""
import hashlib, importlib.metadata, json, platform, statistics, subprocess, tempfile, time
from pathlib import Path
from truss import LocalPostgres
HERE=Path(__file__).resolve().parent
out=HERE/'pgserver-pg17.11-lifecycle-timing.json'
if out.exists():raise SystemExit('Receipt exists')
samples=[]
for sample in range(3):
 with tempfile.TemporaryDirectory(prefix='truss-pg17-timing-') as parent:
  directory=Path(parent)/'data'
  for mode in ('fresh','retained-restart'):
   runtime=LocalPostgres(directory)
   begin=time.perf_counter();runtime.__enter__();ready=time.perf_counter()
   try:
    calls=[]
    for _ in range(3):
     before=time.perf_counter()
     result=subprocess.check_output([str(runtime.psql_path),runtime.info.connection_uri,'-X','-qAt','-c','SELECT 1'],text=True,timeout=10)
     if result.strip()!='1':raise ValueError('Native query failed')
     calls.append(time.perf_counter()-before)
    version=runtime.info.server_version
   finally:
    before_stop=time.perf_counter();runtime.close();stopped=time.perf_counter()
   if (directory/'postmaster.pid').exists():raise ValueError('Stop unconfirmed')
   samples.append({'sample':sample,'mode':mode,'serverVersion':version,'readySeconds':ready-begin,'stopSeconds':stopped-before_stop,'psqlProcessConnectQuerySeconds':calls})
   print(json.dumps(samples[-1]),flush=True)
receipt={'scope':'Three sequential fresh clusters and retained restarts on this host; startup includes readiness/version query; shutdown confirms postmaster marker absent','pgserver':importlib.metadata.version('pgserver'),'platform':platform.platform(),'samples':samples,'medians':{mode:{'readySeconds':statistics.median(s['readySeconds'] for s in samples if s['mode']==mode),'stopSeconds':statistics.median(s['stopSeconds'] for s in samples if s['mode']==mode)} for mode in ('fresh','retained-restart')},'sampleCount':3,'limitations':['Concurrent qualification may affect timings','No static-server database provisioning comparison measured','No CI or cross-platform performance claim'],'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
