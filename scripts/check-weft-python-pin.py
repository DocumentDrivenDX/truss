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
from truss.weft import CompilerBoundary, CompileRefusal, WEFT_SOURCE

root = Path(__file__).resolve().parents[1]
if len(sys.argv) != 3:
 raise SystemExit('usage: check-weft-python-pin.py PYTHON_BUILD_MANIFEST CLI_BUILD_MANIFEST')
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
 'pythonBoundarySourceOnly':True,
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(root / 'docs/helix/04-build/evidence/design-audit/weft-python-f05f2df-component.json').write_text(
 json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'revision':revision,'cases':len(cases),'transportRefusals':5,
 'loadedExtensionMatchesWheel':True,'qualifiedTrussPythonRuntime':False}))
