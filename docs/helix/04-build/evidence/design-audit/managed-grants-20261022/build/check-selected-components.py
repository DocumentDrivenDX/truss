"""Exact selected regression evidence for the managed-grants change, not full suite."""
import argparse,gzip,hashlib,json,os,re,subprocess,sys,time,zipfile
import truss
from pathlib import Path
from native_fixture import WorkerCluster
p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--wheel',required=True,type=Path);a=p.parse_args()
root=Path('/Users/erik/Projects/truss');out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
loaded=Path(truss.__file__).resolve().parent
if not loaded.is_relative_to(Path(sys.prefix).resolve()) or loaded.is_relative_to(root):raise RuntimeError('Installed package outside source required')
with zipfile.ZipFile(a.wheel) as archive:
 payload={n:archive.read(n) for n in archive.namelist() if n.startswith('truss/') and not n.endswith('/')}
 for name,raw in payload.items():
  relative=Path(name).relative_to('truss')
  if (loaded/relative).read_bytes()!=raw or (root/'packages/python/src'/name).read_bytes()!=raw:raise RuntimeError('Installed/wheel/source payload drift: '+name)
modules=['test_managed_platform_grants_native.py','test_managed_grants_migration_native.py','test_preparation_runtime_recipe.py','test_installation_privileges_native.py','test_managed_installation_native.py','test_install_preflight_native.py','test_lifecycle_native.py','test_module_access_batch_native.py','test_host_execution.py','test_host_control_custody.py','test_lifecycle_wire.py','test_action_role_installation_native.py','test_action_store_native.py','test_preparation_source_inventory_native.py','test_catalog_codes_native.py','test_catalog_evolution_native.py','test_catalog_runtime_native.py']
paths=[root/'packages/python/tests'/m for m in modules]+[root/'scripts/native_fixture.py',root/'scripts/run-python-test-module.py',Path(__file__)]
basis={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
record={'scope':'Explicit selected managed/strict/host/protected-source/catalog regression; not full component coverage or legacy fullsuite pass','modules':modules,'inputBasis':basis,'wheelSha256':hashlib.sha256(a.wheel.read_bytes()).hexdigest(),'loadedPackage':str(loaded),'exactInstalledWheelSourcePayload':{n:hashlib.sha256(raw).hexdigest() for n,raw in sorted(payload.items())},'outcomes':[],'passed':False,'workerStopped':False}
receipt=out/'qualification.json'
def save():receipt.write_text(json.dumps(record,indent=2)+'\n')
save();worker=WorkerCluster()
try:
 with worker:
  env={**os.environ,**worker.environment(),'PYTHONPATH':str(root/'scripts')}
  env.pop('TRUSS_NATIVE_TEST_SOCKET',None)
  for module in modules:
   command=[sys.executable,'-W','error',str(root/'scripts/run-python-test-module.py'),'discover','-s',str(root/'packages/python/tests'),'-p',module,'-v'];start=time.monotonic()
   run=subprocess.run(command,cwd=Path(sys.prefix),env=env,capture_output=True,timeout=600);log=run.stdout+run.stderr;restored=False
   try:worker.verify_clean();restored=True
   except Exception as error:log+=('\nWorker inventory verification failed: '+str(error)).encode()
   count=re.search(rb'Ran (\d+) tests? in ',log);terminal=re.search(rb'\nOK\s*$',log)
   path=out/(Path(module).stem+'.log.gz');path.write_bytes(gzip.compress(log,mtime=0))
   row={'module':module,'command':command,'tests':int(count.group(1)) if count else None,'returncode':run.returncode,'baselineRestored':restored,'seconds':time.monotonic()-start,'log':path.name,'logSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'passed':run.returncode==0 and restored and count is not None and int(count.group(1))>0 and terminal is not None}
   record['outcomes'].append(row);save();print(json.dumps(row),flush=True)
   if not row['passed']:break
  worker.verify_clean();record['workerBaselineRestored']=True
 record['workerStopped']=True
except Exception as error:record['error']=repr(error)
record['inputsUnchanged']=all(hashlib.sha256(p.read_bytes()).hexdigest()==basis[str(p)] for p in paths)
record['tests']=sum(r['tests'] or 0 for r in record['outcomes']);record['passed']=len(record['outcomes'])==len(modules) and all(r['passed'] for r in record['outcomes']) and record['workerStopped'] and record['inputsUnchanged'] and 'error' not in record;save();sys.exit(0 if record['passed'] else 1)
