#!/usr/bin/env python3
"""Native owned-module interrupt cleanup and unrelated-worker survival control."""
from truss._runtime_profile import SERVER_VERSION
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,tempfile,time
root=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1]:raise SystemExit('Supply a fresh receipt basename')
receipt_name=sys.argv[1]
sys.path.insert(0,str(root/'scripts'))
from native_fixture import WorkerCluster,connect,evidence_directory
if (evidence_directory()/receipt_name).exists():raise SystemExit("Receipt exists")
with tempfile.TemporaryDirectory(prefix='truss-module-interrupt-',dir='/private/tmp') as folder:
 folder=Path(folder);ready=folder/'ready.json'
 (folder/'test_owned_interrupt.py').write_text('''import json,os,signal,unittest
from pathlib import Path
from test_psycopg_host_native import PsycopgHostNativeTests
class OwnedInterruptTests(PsycopgHostNativeTests):
 def test_interrupt(self):
  Path(os.environ['TRUSS_INTERRUPT_READY']).write_text(json.dumps({'data':str(self.data),'socket':str(self.socket)}))
  signal.pause()
def load_tests(loader,tests,pattern):return unittest.TestSuite([OwnedInterruptTests('test_interrupt')])
''')
 env={**os.environ,'PYTHONPATH':str(root/'packages/python/tests'),'TRUSS_INTERRUPT_READY':str(ready),'TRUSS_CENSUS_POSTGRES_BIN':str(Path(sys.prefix)/'lib/python3.11/site-packages/pgserver/pginstall/bin')}
 with WorkerCluster() as worker:
  child=subprocess.Popen([sys.executable,str(root/'scripts/run-python-test-module.py'),'discover','-s',str(folder),'-p','test_owned_interrupt.py','-v'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  try:
   deadline=time.monotonic()+60
   while not ready.exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.1)
   if not ready.exists():raise RuntimeError('Owned raw fixture did not reach interrupt point')
   observed=json.loads(ready.read_text());os.kill(child.pid,signal.SIGINT)
   stdout,stderr=child.communicate(timeout=45)
   worker.verify_clean();admin=connect(worker.uri)
   try:survives=admin.run('SELECT 1')==[[1]]
   finally:admin.close()
   checks={'interruptionPropagated':child.returncode!=0,'ownedRawDirectoryRemoved':not Path(observed['data']).parent.exists(),'ownedRawSocketAbsent':not (Path(observed['socket'])/'.s.PGSQL.5432').exists(),'borrowedWorkerSurvives':survives}
   assert all(checks.values()),checks
  finally:
   if child.poll() is None:child.send_signal(signal.SIGINT);child.communicate(timeout=45)
 receipt={'passed':True,'postgresql':SERVER_VERSION,'checks':checks,'childReturncode':child.returncode,'stderr':stderr.decode(),'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'wrapperSha256':hashlib.sha256((root/'scripts/run-python-test-module.py').read_bytes()).hexdigest(),'scope':'SIGINT during an owned raw native fixture; confirmed shutdown and directory removal, unrelated socket worker stays usable'}
 out=evidence_directory()/receipt_name;out.write_text(json.dumps(receipt,indent=2)+'\n');print(checks)
