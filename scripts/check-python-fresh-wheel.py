#!/usr/bin/env python3
"""Build and verify a fresh installed component wheel; no engine release claim."""
import hashlib,json,os,re,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if len(sys.argv)!=3 or not sys.argv[1].isdigit() or Path(sys.argv[2]).name!=sys.argv[2] or not sys.argv[2].endswith('.json'):
 raise SystemExit('usage: check-python-fresh-wheel.py EXPECTED_TEST_COUNT NEW_RECEIPT.json')
expected=int(sys.argv[1]);out=ROOT/'docs/helix/04-build/evidence/design-audit'/sys.argv[2]
if out.exists():raise SystemExit('Receipt exists')
def digest(raw):return hashlib.sha256(raw).hexdigest()
source_paths=[ROOT/'packages/python/pyproject.toml',*sorted((ROOT/'packages/python/src/truss').glob('*.py'))]
test_paths=sorted((ROOT/'packages/python/tests').glob('test_*.py'))
source={str(p.relative_to(ROOT)):p.read_bytes() for p in source_paths}
tests={str(p.relative_to(ROOT)):p.read_bytes() for p in test_paths}
stage=Path(tempfile.mkdtemp(prefix='truss-fresh-wheel-',dir='/private/tmp'))
for name,raw in source.items():
 target=stage/'source'/Path(name).relative_to('packages/python');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
env=dict(os.environ);env.pop('PYTHONPATH',None)
commands=[]
def run(command,log,environment=env):
 commands.append(command)
 result=subprocess.run(command,cwd=stage,env=environment,capture_output=True,text=True,timeout=180)
 (stage/log).write_text(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError('Command failed; original output retained in '+str(stage/log))
 return result
run([sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--wheel-dir',str(stage/'wheel'),str(stage/'source')],'build.log')
wheels=list((stage/'wheel').glob('*.whl'))
if len(wheels)!=1:raise RuntimeError('Expected one original wheel')
wheel=wheels[0];installed=stage/'installed'
run([sys.executable,'-m','pip','install','--no-deps','--no-compile','--target',str(installed),str(wheel)],'install.log')
modules=[]
with zipfile.ZipFile(wheel) as archive:
 names=sorted(n for n in archive.namelist() if n.startswith('truss/') and n.endswith('.py'))
 if names!=sorted('truss/'+Path(p).name for p in source if p.endswith('.py')):raise RuntimeError('Wheel membership drift')
 for name in names:
  raw=archive.read(name)
  if raw!=source['packages/python/src/'+name] or raw!=(installed/name).read_bytes():raise RuntimeError('Source/wheel/installed drift')
  modules.append({'path':name,'sha256':digest(raw)})
installed_env=dict(env,PYTHONPATH=str(installed))
probe=run([sys.executable,'-c','import json,truss;print(json.dumps({"loaded":truss.__file__,"exports":truss.__all__}))'],'import.log',installed_env)
identity=json.loads(probe.stdout)
if not Path(identity['loaded']).resolve().is_relative_to(installed):raise RuntimeError('Source package imported')
result=run([sys.executable,'-W','error','-m','unittest','discover','-s',str(ROOT/'packages/python/tests'),'-v'],'tests.log',installed_env)
if re.search(r'Ran '+str(expected)+r' tests\b',result.stderr) is None or not result.stderr.rstrip().endswith('OK'):raise RuntimeError('Unexpected test count or completion')
for name,raw in {**source,**tests}.items():
 if (ROOT/name).read_bytes()!=raw:raise RuntimeError('Source/test changed during execution')
receipt={'scope':'Fresh separately installed wheel complete existing Python component suite; not protected engine release','stage':str(stage),'wheel':str(wheel),'installed':str(installed),'wheelSha256':digest(wheel.read_bytes()),'python':sys.version,'testsPassed':expected,'loadedPackage':identity['loaded'],'exports':identity['exports'],'modules':modules,'sourceTestSha256':{p:digest(raw) for p,raw in tests.items()},'sourcePackagingSha256':digest(source['packages/python/pyproject.toml']),'commands':commands,'logs':{name:digest((stage/name).read_bytes()) for name in ('build.log','install.log','import.log','tests.log')},'producerSha256':digest(Path(__file__).read_bytes()),'sourceWheelInstalledBytesExact':True,'published':False,'completeEngineQualified':False,'installationQualified':False,'migrationExecutionQualified':False,'limitations':['Local corrected pgserver environment, not published default or managed profile','Source tests use checked-in external fixture files; not hermetic dependency closure','Public exports remain local runtime lifecycle only','Private component checks do not prove protected mutation/query/journal/feed or installation APIs']}
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'tests':expected,'modules':len(modules),'stage':str(stage),'completeEngineQualified':False}))
