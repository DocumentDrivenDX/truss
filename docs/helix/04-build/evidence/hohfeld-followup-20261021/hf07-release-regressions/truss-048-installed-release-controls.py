import os,sys,subprocess,shlex,json,time
from pathlib import Path
from pgserver._commands import POSTGRES_BIN_PATH
root=Path('/Users/erik/Projects/truss');out=Path('/private/tmp/truss-048-installed-release-controls');out.mkdir(exist_ok=True)
source=(root/'.github/workflows/release.yml').read_text().split('\n  native:\n',1)[1].split('\n  stress:\n',1)[0]
commands=[]
for line in source.splitlines():
 if 'python -m unittest ' in line:
  tests=shlex.split(line.split('python -m unittest ',1)[1]);commands.append([sys.executable,'-m','unittest',*tests])
env={**os.environ,'PYTHONPATH':str(root/'packages/python/tests'),'TRUSS_BUN_EXECUTABLE':'/opt/homebrew/bin/bun','TRUSS_CENSUS_POSTGRES_BIN':str(POSTGRES_BIN_PATH),'PYTHONDONTWRITEBYTECODE':'1'}
results=[]
for i,cmd in enumerate(commands):
 started=time.monotonic();path=out/f'{i:02}.log'
 with path.open('w') as f:done=subprocess.run(cmd,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
 results.append({'command':cmd,'returncode':done.returncode,'seconds':time.monotonic()-started,'log':path.name})
 (out/'qualification.json').write_text(json.dumps({'scope':'Installed local macOS ARM64 unit/native commands extracted from mandatory Linux release job; separate platform observation, no Linux/publication claim','commands':results,'passed':all(x['returncode']==0 for x in results),'complete':len(results)==len(commands),'expectedCommands':len(commands)},indent=2)+'\n')
 print(i,done.returncode,cmd[3:5],flush=True)
raise SystemExit(any(x['returncode'] for x in results))
