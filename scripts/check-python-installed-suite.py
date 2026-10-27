#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Current installed package component suite; no complete engine qualification."""
from truss._runtime_profile import RUNTIME_DISTRIBUTION, RUNTIME_VERSION, SERVER_VERSION, SERVER_VERSION_NUM
from native_fixture import evidence_directory
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import tomllib
import zipfile
import unittest
import os
import pgserver
import truss
root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from publish_pypi_release import distribution_for_version
project=tomllib.loads((root/'packages/python/pyproject.toml').read_text())['project']
truss_distribution=distribution_for_version(project['version'])
if len(sys.argv) not in (2,3,4) or (len(sys.argv)>=3 and sys.argv[2]!='--corrected-pgserver'):
 raise SystemExit('usage: check-python-installed-suite.py TRUSS_WHEEL [--corrected-pgserver [NEW_RECEIPT_FILENAME]]')
corrected = True  # Historical flag remains a compatibility spelling.
filename = sys.argv[3] if len(sys.argv)==4 else ('python-corrected-runtime-installed-suite.json' if corrected else 'python-current-installed-suite.json')
if Path(filename).name != filename or not filename.endswith('.json'): raise RuntimeError('Receipt basename required')
receipt_path = evidence_directory()/filename
if receipt_path.exists(): raise RuntimeError('Receipt already exists; supply a new filename')
timeout_seconds = int(os.environ.get('TRUSS_INSTALLED_SUITE_TIMEOUT', '1800'))
if not 30 <= timeout_seconds <= 1800:
 raise RuntimeError('Installed suite timeout must be between30 and1800 seconds')
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
dependencies = {n:importlib.metadata.version(n) for n in [truss_distribution,RUNTIME_DISTRIBUTION,'fasteners','platformdirs','psutil','weft-sql']}
for name,version in {RUNTIME_DISTRIBUTION:RUNTIME_VERSION,'fasteners':'0.20','platformdirs':'4.12.4','psutil':'7.2.2'}.items():
 if dependencies[name] != version: raise RuntimeError('Local dependency drift: '+name)
expected_tests = unittest.defaultTestLoader.discover(str(root/'packages/python/tests')).countTestCases()
environment = os.environ.copy()
environment.setdefault('TRUSS_CENSUS_POSTGRES_BIN', str(Path(pgserver.__file__).resolve().parent/'pginstall/bin'))
command = [sys.executable, str(root/'scripts/run-python-installed-workers.py')]
fixture_paths = [
 'tests/fixtures/layout-migration-planning.json',
 'tests/fixtures/operation-ordinal-issuer.json',
 'docs/helix/03-test/acceptance-outer-json-expected.proposal.json',
 'docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json',
 'docs/helix/02-design/contracts/bindings/bootstrap-permit-arithmetic-v0.1.proposal.json',
 'docs/helix/03-test/python-exact-value-vectors.proposal.json',
 'docs/helix/04-build/evidence/receipt-position-locator-vectors.json',
 'docs/helix/02-design/contracts/row-operation-registry-observation-v0.1.proposal.sql',
]
def pin_inputs():
 paths = sorted((root/'packages/python/tests').glob('test_*.py')) + [root/p for p in fixture_paths] + [root/'scripts/native_fixture.py', root/'scripts/run-python-installed-workers.py', root/'scripts/run-python-test-module.py']
 return [{'path':str(p.relative_to(root)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
input_basis = pin_inputs()
def save_failure(status, stdout, stderr, returncode=None):
 def captured(value):
  return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
 failure = {'scope':'Installed suite failure observation; no pass or native cleanup claim',
  'status':status,'timeoutSeconds':timeout_seconds,'returncode':returncode,'command':command,
  'stdout':captured(stdout),'stderr':captured(stderr),'expectedTests':expected_tests,
  'modules':modules,'dependencies':dependencies,'loadedPackage':str(loaded),
  'originalTestAndFixtureInputs':input_basis,
  'wheelSha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),
  'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'testSources':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((root/'packages/python/tests').glob('test_*.py'))],
  'completeEngineQualified':False,'nativeCleanupConfirmed':False}
 with receipt_path.open('x') as output: output.write(json.dumps(failure,indent=2)+'\n')
try:
 result = subprocess.run(command,cwd=Path(sys.prefix),capture_output=True,text=True,timeout=timeout_seconds,env=environment)
except subprocess.TimeoutExpired as error:
 save_failure('timeout', error.stdout, error.stderr)
 raise SystemExit('Installed suite timed out; original partial output retained in '+filename)
if result.returncode or f'Ran {expected_tests} tests' not in result.stderr or not result.stderr.rstrip().endswith('OK'):
 save_failure('failed', result.stdout, result.stderr, result.returncode)
 raise SystemExit('Installed suite failed; original output retained in '+filename)
if pin_inputs() != input_basis:
 save_failure('test_or_fixture_input_drift', result.stdout, result.stderr, result.returncode)
 raise SystemExit('Test/fixture input drift; original basis and output retained in '+filename)
worker_receipt = json.loads((evidence_directory()/'python-workers/receipt.json').read_text())
if worker_receipt['tests'] != expected_tests or not worker_receipt['passed']:
 raise SystemExit('Incomplete installed module-worker coverage')
receipt = {'scope':f'Installed current wheel full existing component suite on PostgreSQL{SERVER_VERSION}; shared fresh databases/roles, isolated lifecycle fixtures and synthetic/pure controls',
 'workerReceipt':str((evidence_directory()/'python-workers/receipt.json').relative_to(root)),
 'workerResults':worker_receipt,'skippedTests':worker_receipt['skippedTests'],
 'wheelSha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'python':sys.version,
 'loadedPackage':str(loaded),'modules':modules,'dependencies':dependencies,
 'environmentReused':True,'correctedPgserverCandidate':corrected,'tests':expected_tests,'command':command,'output':result.stdout+result.stderr,
 'originalTestAndFixtureInputs':input_basis,'testAndFixtureInputsUnchanged':True,
 'inputPinScope':'Selected test files and eight explicit checked-in inputs, compared before/after execution; not hermetic or host-tamper proof',
 'testSources':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((root/'packages/python/tests').glob('test_*.py'))],
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'completeEngineQualified':False,'installationQualified':False,'migrationExecutionQualified':False,
 'platformScope':f'macOS arm64 Python3.11 {RUNTIME_DISTRIBUTION}=={RUNTIME_VERSION} PostgreSQL{SERVER_VERSION}'+'; no process-crash or cross-platform qualification'}
with receipt_path.open('x') as output:
 output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'modules':len(modules),'tests':expected_tests,'completeEngineQualified':False}))
