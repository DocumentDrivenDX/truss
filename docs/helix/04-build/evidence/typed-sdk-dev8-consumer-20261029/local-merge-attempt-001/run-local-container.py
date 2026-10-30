import json,os,signal,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent
name='truss0052-local-qualified-20261030'
image='sha256:7e44ba6b5c483f84c0d630180ba4cd17a82f1bba950577bf1dc9200e7f26e556'
command=['docker','run','--pull=never','--name',name,'--init','--cpus=2','--memory=4g',
 '--mount',f'type=bind,src={root}/source,dst=/source,readonly',
 '--mount',f'type=bind,src={root}/generator-source,dst=/generator-original,readonly',
 '--mount',f'type=bind,src={root},dst=/control,readonly',
 '--mount',f'type=bind,src={root},dst=/out',
 image,'timeout','--signal=TERM','--kill-after=5s','570s','bash','/control/run-container.sh']
started=time.monotonic();child=None;code=125;cleanup={}
def stop(signum,frame):raise SystemExit(128+signum)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
try:
 with (root/'operation.stdout').open('wb')as stdout,(root/'operation.stderr').open('wb')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
  try:code=child.wait(timeout=580)
  except subprocess.TimeoutExpired:code=124
finally:
 if child is not None and child.poll()is None:
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=2)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 removal=subprocess.run(['docker','rm','-f',name],timeout=12,capture_output=True,text=True)
 inspection=subprocess.run(['docker','ps','-a','--filter','name=^/'+name+'$','--format','{{.ID}}'],timeout=5,capture_output=True,text=True)
 cleanup={'removeExit':removal.returncode,'containerAbsent':inspection.returncode==0 and not inspection.stdout.strip()}
 record={'command':command,'exitCode':code,'elapsedSeconds':time.monotonic()-started,'cleanup':cleanup,'source':json.loads((root/'operation-inputs.json').read_bytes())}
 (root/'operation-result.json').write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps(record),flush=True)
raise SystemExit(code if code else 0 if cleanup['containerAbsent'] else 1)
