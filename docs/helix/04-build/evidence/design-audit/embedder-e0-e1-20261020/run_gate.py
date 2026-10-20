"""Run selected owned native/unit fixtures and preserve exact source evidence."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('--label', required=True)
p.add_argument('--package-root', type=Path, required=True)
p.add_argument('--tests-root', type=Path, required=True)
p.add_argument('selectors', nargs='+')
a = p.parse_args()
out = Path(__file__).resolve().parent
repo = out.parents[5]
target = out / (a.label+'.json')
if target.exists():
    raise SystemExit('Use a fresh gate label')
package = a.package_root.resolve()
def pins(root):
    return {str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob('*')) if path.is_file()
            and '__pycache__' not in path.parts and path.suffix != '.pyc'}
before = pins(package/'truss')
tests_before = pins(a.tests_root)
producer_before = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
probe_before = hashlib.sha256((out/'baseline_probe.py').read_bytes()).hexdigest()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TRUSS_BUN_EXECUTABLE='/no-external-runtime',
           TRUSS_EMBEDDER_MEASUREMENT_LABEL=a.label,
           PYTHONPATH=os.pathsep.join(map(str, [package,a.tests_root.resolve(),out,repo/'scripts'])))
env.pop('TRUSS_NATIVE_TEST_SOCKET', None)
env.pop('TRUSS_NATIVE_WORKER', None)
command = [sys.executable, str(repo/'scripts/run-python-test-module.py'), *a.selectors, '-v']
start = time.monotonic()
log = out/(a.label+'.log')
with log.open('wb') as captured:
    result = subprocess.run(command, cwd='/private/tmp', env=env,
                            stdout=captured, stderr=subprocess.STDOUT)
unchanged = (before==pins(package/'truss') and tests_before==pins(a.tests_root)
             and producer_before==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
             and probe_before==hashlib.sha256((out/'baseline_probe.py').read_bytes()).hexdigest())
receipt = {'label':a.label,'command':command,'packageRoot':str(package),
           'testsRoot':str(a.tests_root.resolve()),'selectors':a.selectors,
           'passed':result.returncode==0 and unchanged,'returncode':result.returncode,
           'elapsedSeconds':time.monotonic()-start,'runtimeUnchanged':before==pins(package/'truss'),
           'allInputsUnchanged':unchanged,
           'runtimeSha256':before,'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'baselineProbeSha256':probe_before,
           'testSha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in a.tests_root.glob('test_*.py')},
           'dependencies':{name:importlib.metadata.version(name) for name in
                ['weft-sql','pgserver-pg18','psycopg','mini-racer']},
           'python':sys.version,'nativeFixtures':'Original isolated LocalPostgres class fixtures; no borrowed database or shared TCP listener',
           'scope':'Focused selected E0/E1 fixtures only; no full runtime/platform qualification',
           'logSha256':hashlib.sha256(log.read_bytes()).hexdigest()}
target.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['label','passed','returncode','elapsedSeconds','runtimeUnchanged']}),flush=True)
if result.returncode:
    print(log.read_text()[-12000:],flush=True)
raise SystemExit(result.returncode)
