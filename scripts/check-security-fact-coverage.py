"""Retain actual owner-produced dependency fixture and exact consumer controls."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,uuid,zipfile
root=Path.cwd();owner=Path('/Users/erik/.codex/worktrees/security-main-integration/umf');out=root/'docs/helix/04-build/evidence/security-fact-coverage'/str(uuid.uuid4());out.mkdir(parents=True)
paths=[root/p for p in ('scripts/check-security-fact-coverage.py','scripts/produce-security-fact-requirements.ts','scripts/check-module-boundaries.py','packages/python/src/truss/_security_fact_coverage.py','packages/python/tests/test_security_fact_coverage.py')]
paths += [p for p in (owner/'src').rglob('*') if p.is_file() and p.suffix in ('.ts','.json')]
paths += [owner/'tests/security/fixture.ts',owner/'tests/security/dependencies.test.ts']
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with zipfile.ZipFile(out/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in paths:z.writestr(str(p).lstrip('/'),p.read_bytes())
producer=subprocess.run(['/opt/homebrew/bin/bun','scripts/produce-security-fact-requirements.ts'],capture_output=True,text=True,timeout=60)
(out/'producer.log').write_text(producer.stdout+producer.stderr)
base=root/'docs/helix/04-build/evidence/security-fact-requirements'
for p in base.iterdir():
 if p.is_file():(out/p.name).write_bytes(p.read_bytes())
env=dict(os.environ,PYTHONPATH='packages/python/src:packages/python/tests')
tests=subprocess.run([sys.executable,'-m','unittest','test_security_fact_coverage','-v'],env=env,capture_output=True,text=True,timeout=60)
(out/'consumer.log').write_text(tests.stdout+tests.stderr)
owner_tests=subprocess.run(['/opt/homebrew/bin/bun','test','tests/security/dependencies.test.ts'],cwd=owner,capture_output=True,text=True,timeout=60)
(out/'owner-tests.log').write_text(owner_tests.stdout+owner_tests.stderr)
boundary=subprocess.run([sys.executable,'scripts/check-module-boundaries.py'],capture_output=True,text=True,timeout=60)
(out/'boundaries.log').write_text(boundary.stdout+boundary.stderr)
unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in pins.items())
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('coverage_component',root/'packages/python/src/truss/_security_fact_coverage.py');module=module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
raw=(out/'requirements.json').read_bytes();digest=hashlib.sha256(raw).hexdigest();artifact=json.loads(raw)
assert hashlib.sha256((out/'policy.json').read_bytes()).hexdigest()==artifact['policySha256']
assert hashlib.sha256((out/'resolution.json').read_bytes()).hexdigest()==artifact['resolutionSha256']
entries=tuple(module._FactBindingDeclaration('association',tuple(r[k] for k in ('documentId','moduleId','elementId')),'declared-native-graph') for r in artifact['dependencies']['associations'])
coverage=module._inspect_fact_coverage(raw,digest,entries)
passed=producer.returncode==tests.returncode==owner_tests.returncode==boundary.returncode==0 and unchanged and 'Ran 6 tests' in tests.stderr and len(coverage.required)==10 and len(coverage.missing)==8 and not coverage.admitted
receipt={'status':'component-passed' if passed else 'component-failed','sourceDigests':pins,'producerExitCode':producer.returncode,'consumerExitCode':tests.returncode,'ownerTestExitCode':owner_tests.returncode,'boundaryExitCode':boundary.returncode,'sourceUnchanged':unchanged,'required':coverage.required,'associationOnlyMissing':coverage.missing,'admitted':coverage.admitted,'requirementsSha256':digest,'scope':'Actual original UMF0.1 dependency function over conformance fixture and six Python coverage controls. Eight fields/two associations, exact original input hashes and source/archive correspondence. No authenticated issuer, complete physical producers, native installed profile, original business admission or new backend acceptance binding.'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'evidence':str(out)}))
if not passed:raise SystemExit(1)
