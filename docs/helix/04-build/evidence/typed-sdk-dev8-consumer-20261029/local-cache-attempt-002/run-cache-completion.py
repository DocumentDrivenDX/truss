"""One proposed bounded continuation; requires coordinator admission before use."""
import json,os,signal,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent;previous=root.parent
name='truss0052-cached-qualification-20261030'
image='sha256:7e44ba6b5c483f84c0d630180ba4cd17a82f1bba950577bf1dc9200e7f26e556'
started=time.monotonic();code=125;child=None;prefetch=None;command=[]
def stop(signum,frame):raise SystemExit(128+signum)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
try:
 prefetch=subprocess.Popen(['/usr/bin/python3',str(root/'prefetch-public.py')],start_new_session=True)
 try:code=prefetch.wait(timeout=95)
 except subprocess.TimeoutExpired:code=124
 if code:raise SystemExit(code)
 code=125
 remaining=381.084566292-(time.monotonic()-started)-25
 if remaining<=0:raise SystemExit('No admitted time remains for Docker plus cleanup')
 command=['docker','run','--pull=never','--platform=linux/amd64','--name',name,'--init','--cpus=2','--memory=4g',
  '--mount',f'type=bind,src={previous}/source,dst=/source,readonly',
  '--mount',f'type=bind,src={previous}/generator-source,dst=/generator-original,readonly',
  '--mount',f'type=bind,src={root},dst=/control,readonly',
  '--mount',f'type=bind,src={root},dst=/out',
  '--mount',f'type=bind,src={root}/public-http-cache,dst=/public-cache,readonly',
  image,'timeout','--signal=TERM','--kill-after=5s',str(min(340,remaining))+'s','bash','/control/run-container.sh']
 with (root/'operation.stdout').open('wb')as stdout,(root/'operation.stderr').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
  try:code=child.wait(timeout=max(1,381.084566292-(time.monotonic()-started)-20))
  except subprocess.TimeoutExpired:code=124
finally:
 if prefetch is not None:
  if prefetch.poll()is None:
   os.killpg(prefetch.pid,signal.SIGTERM)
   try:prefetch.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(prefetch.pid,signal.SIGKILL)
  prefetch.wait()
 if child is not None and child.poll()is None:
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=2)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 removal=subprocess.run(['docker','rm','-f',name],timeout=10,capture_output=True,text=True)
 inspection=subprocess.run(['docker','ps','-a','--filter','name=^/'+name+'$','--format','{{.ID}}'],timeout=5,capture_output=True,text=True)
 cleanup={'removeExit':removal.returncode,'containerAbsent':inspection.returncode==0 and not inspection.stdout.strip()}
 (root/'operation-result.json').write_text(json.dumps({'command':command,'exitCode':code,'elapsedSeconds':time.monotonic()-started,'cleanup':cleanup,'source':json.loads((root/'operation-inputs.json').read_bytes())},indent=2)+'\n')
raise SystemExit(code if code else 0 if cleanup['containerAbsent']else 1)
