"""Freeze and execute the private native fresh source-epoch projection on an owned native Unix-socket fixture."""
import hashlib,json,os,secrets,subprocess,tempfile,time,uuid,zipfile,importlib.util,importlib.metadata
from pathlib import Path
root=Path.cwd();run_id=str(uuid.uuid4());name='truss-python-census-'+run_id
folder=root/'docs/helix/04-build/evidence/python-fresh-epoch'/run_id;folder.mkdir(parents=True,mode=0o700)
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
sql_inputs={'layout':'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
 'immutable':'packages/postgresql/native/source-epoch-immutability.sql',
 'lock':'packages/postgresql/native/source-epoch-lock.sql',
 'issue':'packages/postgresql/native/source-epoch-issue.sql',
 'fresh':'packages/postgresql/native/source-epoch-fresh-lock.sql'}
for q in ['scripts/check-python-fresh-epoch-native.py','scripts/python-fresh-epoch-worker.py','scripts/check-module-boundaries.py','packages/python/tests/test_native_fresh_epoch_capture.py',*sql_inputs.values()]:
 p=root/q;inputs[str(p)]=p.read_bytes()
pins={p:sha(b) for p,b in inputs.items()}
with zipfile.ZipFile(folder/'sources.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for p,b in inputs.items():archive.writestr(p.lstrip('/'),b)
POSTGRES_BIN_PATH=Path(os.environ["TRUSS_CENSUS_POSTGRES_BIN"]).resolve()
binaries={str(p):sha(p.read_bytes()) for p in POSTGRES_BIN_PATH.parent.rglob("*") if p.is_file()}
container=None;attempted=False;result=None
captured=tempfile.mkdtemp(prefix='truss-python-census-execution-')
if True:
 captured=Path(captured);modules=captured/'modules'
 for p,b in copied.items():
  q=modules/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 worker=captured/'worker.py';worker.write_bytes(inputs[str(root/'scripts/python-fresh-epoch-worker.py')])
 selected={}
 for name,path in sql_inputs.items():
  target=captured/(name+'.sql');raw=inputs[str(root/path)];target.write_bytes(raw)
  if target.read_bytes()!=raw:raise RuntimeError('Captured SQL bytes differ')
  selected[name]=str(target)
 if any((modules/p).read_bytes()!=b for p,b in copied.items()):raise RuntimeError('Captured execution bytes differ')
 if worker.read_bytes()!=inputs[str(root/'scripts/python-fresh-epoch-worker.py')]:raise RuntimeError('Captured worker bytes differ')
 tests=captured/'tests';tests.mkdir();test=tests/'test_native_fresh_epoch_capture.py'
 test.write_bytes(inputs[str(root/'packages/python/tests/test_native_fresh_epoch_capture.py')])
 if test.read_bytes()!=inputs[str(root/'packages/python/tests/test_native_fresh_epoch_capture.py')]:raise RuntimeError('Captured test bytes differ')
 python=os.sys.executable
 try:
  if any(Path(p).read_bytes()!=b for p,b in inputs.items()):raise RuntimeError('Source changed before execution')
  host=run([python,'-m','unittest','discover','-s',str(tests),'-p','test_native_fresh_epoch_capture.py','-v'],env={**os.environ,'PYTHONPATH':str(modules)})
  (folder/'host.stdout.log').write_text(host.stdout);(folder/'host.stderr.log').write_text(host.stderr);require(host)
  checked=run([python,'scripts/check-module-boundaries.py']);(folder/'boundaries.stdout.log').write_text(checked.stdout);(folder/'boundaries.stderr.log').write_text(checked.stderr);require(checked)
  pgdata=captured/'pgdata';socket_dir=Path(tempfile.mkdtemp(prefix='pc-',dir='/private/tmp'))
  require(run([str(POSTGRES_BIN_PATH/'initdb'),'-D',str(pgdata),'-U','postgres','--auth=trust','--encoding=UTF8'],timeout=60))
  attempted=True
  require(run([str(POSTGRES_BIN_PATH/'pg_ctl'),'-D',str(pgdata),'-l',str(captured/'server.log'),'-w','-o',f"-h '' -k {socket_dir}",'start'],timeout=60))
  native=run([python,str(worker)],input=json.dumps({'capturedModules':str(modules),**selected,'unixSocket':str(socket_dir/'.s.PGSQL.5432'),'password':None,'evidence':str(folder)}),timeout=180)
  (folder/'native.stdout.log').write_text(native.stdout);(folder/'native.stderr.log').write_text(native.stderr);require(native)
  if any(Path(p).read_bytes()!=b for p,b in inputs.items()):raise RuntimeError('Current source pins changed')
  result={'status':'component-passed','runId':run_id,'sourceDigests':pins,'versions':{p:importlib.metadata.version(p) for p in ['pg8000','scramp','asn1crypto']},'python':os.sys.version,'scope':'Exact captured Python modules executed in fresh worker; installed pgserver PostgreSQL16.15 binaries over original AF_UNIX private READ COMMITTED source-epoch projection and native issuer drain only. Not hermetic interpreter/OS, public installed provider qualification, authenticated source/provider/issuer, complete source/authority held cut, complete protected operation handback or backend acceptance.'}
 except BaseException as error:result={'status':'failed','runId':run_id,'sourceDigests':pins,'error':str(error)}
 finally:
  cleanup={'attempted':attempted}
  try:
   if attempted:
    stopped=run([str(POSTGRES_BIN_PATH/'pg_ctl'),'-D',str(pgdata),'-w','-m','immediate','stop'],timeout=30)
    status=run([str(POSTGRES_BIN_PATH/'pg_ctl'),'-D',str(pgdata),'status'])
    cleanup.update({'stopExitCode':stopped.returncode,'statusExitCode':status.returncode,'socketAbsent':not (socket_dir/'.s.PGSQL.5432').exists()})
    (folder/'server.log').write_bytes((captured/'server.log').read_bytes())
    if stopped.returncode or status.returncode!=3 or not cleanup['socketAbsent']:result['status']='failed'
   if any(sha(Path(p).read_bytes())!=digest for p,digest in binaries.items()):result['status']='failed';result['binaryDrift']=True
  except BaseException as error:
   result['status']='failed';cleanup['error']=str(error)
  if attempted and (cleanup.get('statusExitCode')!=3 or not cleanup.get('socketAbsent')):
   cleanup['retainedExecutionDirectory']=str(captured)
  else:
   import shutil
   try:
    shutil.rmtree(captured)
    if 'socket_dir' in globals():shutil.rmtree(socket_dir)
   except BaseException as error:
    result['status']='failed';cleanup['directoryCleanupError']=str(error)
  result['nativeBinaryDigests']=binaries
  result['cleanup']=cleanup;(folder/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'evidence':str(folder)}))
 if result['status']!='component-passed':raise SystemExit(1)
