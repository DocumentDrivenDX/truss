#!/usr/bin/env python3
"""Current installed package component suite; no complete engine qualification."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import truss
root = Path(__file__).resolve().parents[1]
if len(sys.argv) not in (2,3,4) or (len(sys.argv)>=3 and sys.argv[2]!='--corrected-pgserver'):
 raise SystemExit('usage: check-python-installed-suite.py TRUSS_WHEEL [--corrected-pgserver [NEW_RECEIPT_FILENAME]]')
corrected = len(sys.argv)>=3
filename = sys.argv[3] if len(sys.argv)==4 else ('python-corrected-runtime-installed-suite.json' if corrected else 'python-current-installed-suite.json')
if Path(filename).name != filename or not filename.endswith('.json'): raise RuntimeError('Receipt basename required')
receipt_path = root/'docs/helix/04-build/evidence/design-audit'/filename
if receipt_path.exists(): raise RuntimeError('Receipt already exists; supply a new filename')
wheel = Path(sys.argv[1])
loaded = Path(truss.__file__).resolve().parent
if not loaded.is_relative_to(Path(sys.prefix).resolve()) or loaded.is_relative_to(root):
 raise RuntimeError('Installed environment outside source checkout required')
modules = []
with zipfile.ZipFile(wheel) as archive:
 names = sorted(n for n in archive.namelist() if n.startswith('truss/') and n.endswith('.py'))
 expected = sorted('truss/'+p.name for p in (root/'packages/python/src/truss').glob('*.py'))
 if names != expected: raise RuntimeError('Incomplete wheel module membership')
 for name in names:
  original = archive.read(name)
  if original != (loaded/Path(name).name).read_bytes() or original != (root/'packages/python/src'/name).read_bytes():
   raise RuntimeError('Installed/wheel/source payload drift: '+name)
  modules.append({'path':name,'sha256':hashlib.sha256(original).hexdigest()})
dependencies = {n:importlib.metadata.version(n) for n in ['truss-toolkit','pgserver','fasteners','platformdirs','psutil','weft-sql']}
for name,version in {'pgserver':'0.1.4+truss.pg16.15' if corrected else '0.1.4','fasteners':'0.20','platformdirs':'4.12.4','psutil':'7.2.2'}.items():
 if dependencies[name] != version: raise RuntimeError('Local dependency drift: '+name)
command = [sys.executable,'-W','error','-m','unittest','discover','-s',str(root/'packages/python/tests'),'-v']
def save_failure(status, stdout, stderr, returncode=None):
 def captured(value):
  return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
 failure = {'scope':'Installed suite failure observation; no pass or native cleanup claim',
  'status':status,'timeoutSeconds':180,'returncode':returncode,'command':command,
  'stdout':captured(stdout),'stderr':captured(stderr),'expectedTests':61,
  'modules':modules,'dependencies':dependencies,'loadedPackage':str(loaded),
  'wheelSha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),
  'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'testSources':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((root/'packages/python/tests').glob('test_*.py'))],
  'completeEngineQualified':False,'nativeCleanupConfirmed':False}
 with receipt_path.open('x') as output: output.write(json.dumps(failure,indent=2)+'\n')
try:
 result = subprocess.run(command,cwd=Path(sys.prefix),capture_output=True,text=True,timeout=180)
except subprocess.TimeoutExpired as error:
 save_failure('timeout', error.stdout, error.stderr)
 raise SystemExit('Installed suite timed out; original partial output retained in '+filename)
if result.returncode or 'Ran 61 tests' not in result.stderr or not result.stderr.rstrip().endswith('OK'):
 save_failure('failed', result.stdout, result.stderr, result.returncode)
 raise SystemExit('Installed suite failed; original output retained in '+filename)
receipt = {'scope':'Installed current wheel full existing component suite; four native lifecycle tests plus synthetic/pure controls',
 'wheelSha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'python':sys.version,
 'loadedPackage':str(loaded),'modules':modules,'dependencies':dependencies,
 'environmentReused':True,'correctedPgserverCandidate':corrected,'tests':61,'command':command,'output':result.stdout+result.stderr,
 'testSources':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((root/'packages/python/tests').glob('test_*.py'))],
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'completeEngineQualified':False,'installationQualified':False,'migrationExecutionQualified':False,
 'platformScope':('macOS27 arm64 Python3.11 pgserver0.1.4+truss.pg16.15 PostgreSQL16.15' if corrected else 'macOS arm64 Python3.11 pgserver0.1.4 PostgreSQL16.2')+'; no process-crash or cross-platform qualification'}
with receipt_path.open('x') as output:
 output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'modules':len(modules),'tests':61,'completeEngineQualified':False}))
