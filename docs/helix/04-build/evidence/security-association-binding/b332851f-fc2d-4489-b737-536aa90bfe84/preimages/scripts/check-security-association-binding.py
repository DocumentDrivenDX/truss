"""Retained private component test evidence; no native/backend qualification."""
import ast,hashlib,json,os,re,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if Path.cwd()!=ROOT:raise SystemExit('Exact root invocation required')
paths=[Path(__file__),ROOT/'packages/python/src/truss/_security_association_binding.py',ROOT/'packages/python/tests/test_security_association_binding.py',ROOT/'packages/python/tests/fixtures/security-association-core.json',ROOT/'packages/python/tests/fixtures/security-association-ontology.json',ROOT/'scripts/check-module-boundaries.py']
frozen={str(p.relative_to(ROOT)):p.read_bytes() for p in paths};sha=lambda b:hashlib.sha256(b).hexdigest()
out=ROOT/'docs/helix/04-build/evidence/security-association-binding'/str(uuid.uuid4());out.mkdir(parents=True)
for p,b in frozen.items():
 dest=out/'preimages'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
expected={node.name for node in ast.walk(ast.parse(frozen['packages/python/tests/test_security_association_binding.py'])) if isinstance(node,ast.FunctionDef) and node.name.startswith('test_')}
env={**os.environ,'PYTHONPATH':str(ROOT/'packages/python/src'),'PYTHONDONTWRITEBYTECODE':'1'}
command=[sys.executable,'-m','unittest','discover','-s','packages/python/tests','-p','test_security_association_binding.py','-v']
result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=30)
if len(result.stdout)+len(result.stderr)>1048576:raise ValueError('Bounded test output required')
(out/'tests.log').write_text(result.stdout+result.stderr)
observed=re.findall(r'^(test_\w+) \(.+\) \.\.\. ok$',result.stderr,re.M)
boundary=subprocess.run([sys.executable,'scripts/check-module-boundaries.py'],env=env,capture_output=True,text=True,timeout=10)
(out/'boundaries.log').write_text(boundary.stdout+boundary.stderr)
passed=result.returncode==0 and boundary.returncode==0 and len(observed)==len(set(observed)) and set(observed)==expected and all((ROOT/p).read_bytes()==b for p,b in frozen.items())
receipt={'status':'pass' if passed else 'fail','pythonVersion':sys.version.split()[0],'sourceSha256':{p:sha(b) for p,b in frozen.items()},'command':command,'tests':{'expected':sorted(expected),'passed':sorted(observed),'exitCode':result.returncode},'moduleBoundaries':{'exitCode':boundary.returncode,'output':boundary.stdout.strip()},'scope':'Private original-source association binding correspondence tests; source tree Python execution','limitations':['No genuine UMF/ontology owner semantic validation or authenticated artifact/cut authority','No database staging, installed public package qualification, predicate lowering or publication','No accepted-binding vocabulary registration or backend acceptance promotion'],'acceptancePromoted':False}
(out/'tests.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'tests':len(observed),'receipt':str(out/'tests.json')}))
if not passed:raise SystemExit(1)
