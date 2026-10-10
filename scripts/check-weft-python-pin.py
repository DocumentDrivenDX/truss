"""Pinned Python/CLI compiler correspondence; no database or host qualification."""
import copy
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys
import zipfile
import weft
import weft.weft as extension
import truss.weft as boundary_module
from truss.weft import CompilerBoundary, CompileRefusal, WEFT_SOURCE

root = Path(__file__).resolve().parents[1]
if len(sys.argv) not in (3,4):
 raise SystemExit('usage: check-weft-python-pin.py PYTHON_BUILD_MANIFEST CLI_BUILD_MANIFEST [TRUSS_WHEEL]')
build = json.loads(Path(sys.argv[1]).read_bytes())
cli_manifest = Path(sys.argv[2])
cli_build = json.loads(cli_manifest.read_bytes())
revision = 'f05f2df09e9c2494ac8c6d703dfe38413dbc4181'
assert build['revision'] == cli_build['revision'] == revision
assert WEFT_SOURCE == revision
assert build['features'] == [cli_build['feature']] == ['truss-postgresql-qualified']
assert build['sourceArchiveSha256'] == cli_build['archiveSha256']
wheel = Path(build['wheel']['path'])
assert hashlib.sha256(wheel.read_bytes()).hexdigest() == build['wheel']['sha256']
with zipfile.ZipFile(wheel) as archive:
 members = [n for n in archive.namelist() if n.endswith('.so')]
 assert len(members) == 1
 native = archive.read(members[0])
assert Path(extension.__file__).read_bytes() == native
cli = cli_manifest.parent / 'target/debug/weft-runtime'
assert hashlib.sha256(cli.read_bytes()).hexdigest() == cli_build['executableSha256']
fixture_path = root / 'tests/weft/fixtures/qualified-count.request.json'
fixture_bytes = fixture_path.read_bytes()
request = json.loads(fixture_bytes)
cases = [('count',request,True)]
grouped = copy.deepcopy(request)
grouped['sql'] = 'SELECT c.name, COUNT(*) AS total FROM Customer c GROUP BY c.name ORDER BY c.name LIMIT 10'
cases.append(('bounded_group_count',grouped,True))
unbounded = copy.deepcopy(grouped)
unbounded['sql'] = 'SELECT c.name, COUNT(*) AS total FROM Customer c GROUP BY c.name ORDER BY c.name'
cases.append(('unbounded_group_count',unbounded,False))
profile = copy.deepcopy(request)
profile['target']['targetProfile'] = 'truss-reference-history/0.12'
cases.append(('unsupported_profile',profile,False))
cases.append(('missing_version',{},False))
observations = []
boundary = CompilerBoundary(weft.compile_json)
for name,value,compiled in cases:
 original = json.dumps(value,ensure_ascii=False,separators=(',',':'))
 raw = weft.compile_json(original)
 response = json.loads(raw)
 cli_raw = subprocess.check_output([str(cli)],input=original,text=True,timeout=30)
 assert response == json.loads(cli_raw), name + ': Python/CLI artifact mismatch'
 assert (response['status'] == 'compiled') == compiled, name + ': independent status mismatch'
 if compiled:
  assert response['interfaceVersion'] == 'weft-compile/0.2.0'
  assert response['dialect'] == 'weft-sql/0.2.0'
  assert response['backend'] == {
   'interfaceVersion':'weft-backend/0.2.0',
   **{k:value['target'][k] for k in ['backendId','backendVersion','targetProfile']}}
  assert response['bindingSha256'] == value['target']['bindingSha256']
  assert 'count(*)::text' in response['sql']
  if name == 'bounded_group_count':
   assert all(clause in response['sql'].upper() for clause in ['GROUP BY','ORDER BY','LIMIT'])
 else:
  assert 'sql' not in response
 try:
  admitted = boundary.compile_request(original.encode('utf-8'))
 except CompileRefusal as error:
  assert not compiled
  assert error.code == ('input_version' if name == 'missing_version' else 'compiler_blocked')
 else:
  assert compiled
  assert admitted.original_response == raw.encode('utf-8')
  assert admitted.artifact['sql'] == response['sql']
 observations.append({'id':name,'expectedCompiled':compiled,
  'inputSha256':hashlib.sha256(original.encode()).hexdigest(),
  'pythonResponseSha256':hashlib.sha256(raw.encode()).hexdigest(),
  'cliResponseSha256':hashlib.sha256(cli_raw.encode()).hexdigest(),
  'fullParsedResponseEqual':True})
for bad in [None,{},b'{}',1]:
 try: weft.compile_json(bad)
 except TypeError: pass
 else: raise AssertionError('Wrong Python transport type admitted')
try: weft.compile_json('\ud800')
except UnicodeError: pass
else: raise AssertionError('Unpaired surrogate admitted')
assert not hasattr(weft,'compile_json_with_conformance_configuration')
distribution = importlib.metadata.distribution('weft-sql')
assert not distribution.requires
truss_delivery = None
if len(sys.argv) == 4:
 truss_wheel = Path(sys.argv[3])
 loaded = Path(boundary_module.__file__).resolve()
 assert loaded.is_relative_to(Path(sys.prefix).resolve()), 'Truss must load from installed environment'
 assert not loaded.is_relative_to(root), 'Source checkout cannot prove wheel delivery'
 with zipfile.ZipFile(truss_wheel) as archive:
  members = sorted(n for n in archive.namelist() if n.startswith('truss/') and n.endswith('.py'))
  expected_members = sorted('truss/'+p.name for p in (root/'packages/python/src/truss').glob('*.py'))
  assert members == expected_members, 'Incomplete Python module delivery'
  delivered = []
  for name in members:
   payload = archive.read(name)
   assert payload == (loaded.parent/Path(name).name).read_bytes(), 'Installed Python source differs from wheel'
   assert payload == (root/'packages/python/src'/name).read_bytes(), 'Wheel differs from current source'
   delivered.append({'path':name,'sha256':hashlib.sha256(payload).hexdigest()})
 truss_distribution = importlib.metadata.distribution('truss-toolkit')
 assert truss_distribution.requires == [f'{p}; extra == "local"' for p in (
  'pgserver==0.1.4','fasteners==0.20','platformdirs==4.12.4','psutil==7.2.2')]
 truss_delivery = {
  'wheel':{'path':str(truss_wheel),'sha256':hashlib.sha256(truss_wheel.read_bytes()).hexdigest()},
  'loadedBoundary':str(loaded),'modules':delivered,'allModulePayloadsMatch':True,
  'version':truss_distribution.version,'requiresDist':truss_distribution.requires,
  'installedDistributions':sorted(
   [{'name':d.metadata['Name'],'version':d.version} for d in importlib.metadata.distributions()],
   key=lambda d:d['name']),
  'localExtraInstalled':all(
   any(d.metadata['Name'].lower()==name and d.version==version
       for d in importlib.metadata.distributions())
   for name,version in [('pgserver','0.1.4'),('fasteners','0.20'),
                        ('platformdirs','4.12.4'),('psutil','7.2.2')]),
  'nativeInstallationQualified':False,
 }
receipt = {
 'scope':'Embedded Rust Python extension pinned to the same source/features as the Truss CLI; focused independent compiler expectations and complete cross-binding response correspondence only',
 'python':sys.version,'revision':revision,'weftVersion':weft.__version__,
 'platform':sys.platform,'machine':platform.machine(),
 'declaredRuntimeDependencies':distribution.requires or [],
 'build':build,'loadedExtensionSha256':hashlib.sha256(native).hexdigest(),
 'loadedExtensionMatchesWheel':True,'cliExecutableSha256':cli_build['executableSha256'],
 'fixtureSha256':hashlib.sha256(fixture_bytes).hexdigest(),'cases':observations,
 'transportRefusals':5,'testOnlyExportAbsent':True,
 'nativeDatabaseExecuted':False,'qualifiedTrussPythonRuntime':False,
 'pythonBoundarySourceSha256':hashlib.sha256((root/'packages/python/src/truss/weft.py').read_bytes()).hexdigest(),
 'pythonBoundarySourceOnly':truss_delivery is None,
 'trussWheelDelivery':truss_delivery,
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
receipt_name = ('python-weft-coordinator-wheel-component.json'
 if truss_delivery and 'truss/_query_execution.py' in members else
 'python-weft-wheel-component.json' if truss_delivery else 'weft-python-f05f2df-component.json')
(root / 'docs/helix/04-build/evidence/design-audit' / receipt_name).write_text(
 json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'revision':revision,'cases':len(cases),'transportRefusals':5,
 'loadedExtensionMatchesWheel':True,'qualifiedTrussPythonRuntime':False}))
