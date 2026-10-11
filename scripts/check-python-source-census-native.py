"""Freeze and execute the private original Python census provider on owned Docker."""
import hashlib,json,os,secrets,subprocess,tempfile,time,uuid,zipfile,importlib.util,importlib.metadata
from pathlib import Path
root=Path.cwd();run_id=str(uuid.uuid4());name='truss-python-census-'+run_id
folder=root/'docs/helix/04-build/evidence/python-source-census'/run_id;folder.mkdir(parents=True,mode=0o700)
os.umask(0o077)
def run(argv,**kw):return subprocess.run(argv,text=True,capture_output=True,timeout=kw.pop('timeout',30),**kw)
def require(r):
 if r.returncode:raise RuntimeError(r.stderr[-3000:])
 return r.stdout.strip()
sha=lambda b:hashlib.sha256(b).hexdigest()
source=root/'packages/python/src/truss';inputs={};copied={}
for p in source.glob('*.py'):inputs[str(p)]=p.read_bytes();copied['truss/'+p.name]=inputs[str(p)]
for package in ['pg8000','scramp','asn1crypto']:
 base=Path(importlib.util.find_spec(package).origin).parent
 for p in base.rglob('*.py'):inputs[str(p)]=p.read_bytes();copied[package+'/'+str(p.relative_to(base))]=inputs[str(p)]
 dist=importlib.metadata.distribution(package)
 for file in dist.files:
  if str(file).endswith('.dist-info/METADATA'):
   p=Path(dist.locate_file(file));inputs[str(p)]=p.read_bytes();copied[str(file)]=inputs[str(p)]
for q in ['scripts/check-python-source-census-native.py','scripts/python-source-census-worker.py','scripts/check-module-boundaries.py','packages/python/tests/test_native_source_census.py','packages/postgresql/native/security-query-source-census-pg16.sql','packages/postgresql/native/security-query-source-census.sql']:
 p=root/q;inputs[str(p)]=p.read_bytes()
pins={p:sha(b) for p,b in inputs.items()}
with zipfile.ZipFile(folder/'sources.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for p,b in inputs.items():archive.writestr(p.lstrip('/'),b)
container=None;attempted=False;result=None
with tempfile.TemporaryDirectory(prefix='truss-python-census-execution-') as captured:
 captured=Path(captured);modules=captured/'modules'
 for p,b in copied.items():
  q=modules/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 worker=captured/'worker.py';worker.write_bytes(inputs[str(root/'scripts/python-source-census-worker.py')])
 selected=captured/'source.sql';selected.write_bytes(inputs[str(root/'packages/postgresql/native/security-query-source-census-pg16.sql')])
 tests=captured/'tests';tests.mkdir();(tests/'test_native_source_census.py').write_bytes(inputs[str(root/'packages/python/tests/test_native_source_census.py')])
 if any((modules/p).read_bytes()!=b for p,b in copied.items()):raise RuntimeError('Captured execution bytes differ')
 python=os.sys.executable
 try:
  if any(Path(p).read_bytes()!=b for p,b in inputs.items()):raise RuntimeError('Source changed before execution')
  host=run([python,'-m','unittest','discover','-s',str(tests),'-p','test_native_source_census.py','-v'],env={**os.environ,'PYTHONPATH':str(modules)})
  (folder/'host.stdout.log').write_text(host.stdout);(folder/'host.stderr.log').write_text(host.stderr);require(host)
  checked=run([python,'scripts/check-module-boundaries.py']);(folder/'boundaries.stdout.log').write_text(checked.stdout);(folder/'boundaries.stderr.log').write_text(checked.stderr);require(checked)
  if name in require(run(['docker','container','ls','-a','--format','{{.Names}}'])).splitlines():raise RuntimeError('Preexisting fixture')
  password=secrets.token_hex(32);attempted=True
  container=require(run(['docker','run','-d','--name',name,'--label','truss.security.run='+run_id,'--publish','127.0.0.1::5432','-e','POSTGRES_PASSWORD','postgres:16.15'],env={**os.environ,'POSTGRES_PASSWORD':password},timeout=120))
  deadline=time.monotonic()+25
  while run(['docker','exec',container,'pg_isready','-h','127.0.0.1','-U','postgres']).returncode:
   if time.monotonic()>deadline:raise TimeoutError('Final server readiness')
   time.sleep(.1)
  details=json.loads(require(run(['docker','inspect',container])))[0]
  if details['Config']['Labels'].get('truss.security.run')!=run_id:raise RuntimeError('Fixture ownership mismatch')
  port=int(details['NetworkSettings']['Ports']['5432/tcp'][0]['HostPort'])
  native=run([python,str(worker)],input=json.dumps({'capturedModules':str(modules),'source':str(selected),'port':port,'password':password,'evidence':str(folder)}),timeout=180)
  (folder/'native.stdout.log').write_text(native.stdout);(folder/'native.stderr.log').write_text(native.stderr);require(native)
  if any(Path(p).read_bytes()!=b for p,b in inputs.items()):raise RuntimeError('Current source pins changed')
  result={'status':'component-passed','runId':run_id,'sourceDigests':pins,'versions':{p:importlib.metadata.version(p) for p in ['pg8000','scramp','asn1crypto']},'python':os.sys.version,'scope':'Exact captured Python modules executed in fresh worker; native PostgreSQL16.15 original census observation only. Not hermetic interpreter/OS, installed pgserver qualification, authenticated source/provider/issuer, held cut, complete protected operation handback or backend acceptance.'}
 except BaseException as error:result={'status':'failed','runId':run_id,'sourceDigests':pins,'error':str(error)}
 finally:
  cleanup={'attempted':attempted}
  if attempted:
   inspected=run(['docker','inspect',container or name]);cleanup['inspectionExitCode']=inspected.returncode
   if inspected.returncode:result['status']='failed';cleanup['stderr']=inspected.stderr
   else:
    found=json.loads(inspected.stdout)[0]
    if found['Config']['Labels'].get('truss.security.run')!=run_id:raise RuntimeError('Cleanup ownership mismatch')
    removed=run(['docker','rm','-f',found['Id']]);remaining=run(['docker','container','ls','-a','--filter','id='+found['Id'],'--format','{{.ID}}'])
    cleanup.update({'container':found['Id'],'exitCode':removed.returncode,'stdout':removed.stdout,'stderr':removed.stderr,'absenceExitCode':remaining.returncode,'remaining':remaining.stdout})
    if removed.returncode or remaining.returncode or remaining.stdout.strip():result['status']='failed'
  result['cleanup']=cleanup;(folder/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'evidence':str(folder)}))
 if result['status']!='component-passed':raise SystemExit(1)
