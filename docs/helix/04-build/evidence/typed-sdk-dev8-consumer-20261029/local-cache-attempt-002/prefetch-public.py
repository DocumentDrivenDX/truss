"""Prepare normal pip HTTP cache; never install from the downloaded-file folder."""
import json,os,signal,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent
python='/private/tmp/arras-pypi-extras-20261026/public-extras-macos/bin/python'
cache=root/'public-http-cache';downloads=root/'public-downloads'
cache.mkdir();downloads.mkdir()
environment={k:v for k,v in os.environ.items()if not k.startswith('PIP_')}
environment.update(PIP_CONFIG_FILE=os.devnull,PIP_NO_INPUT='1',PIP_KEYRING_PROVIDER='disabled')
command=[python,'-m','pip','download','--cache-dir',str(cache),'--only-binary=:all:',
 '--index-url','https://pypi.org/simple','--platform','manylinux_2_27_x86_64',
 '--platform','manylinux2014_x86_64','--platform','manylinux_2_17_x86_64',
 '--python-version','3.11.17','--implementation','cp','--abi','cp311','--abi','abi3',
 '--dest',str(downloads),str(root/'artifacts/umf_truss-0.0.52-py3-none-any.whl')+'[native,query,typed-sdk]',
 'pydantic==2.13.5']
started=time.monotonic();code=125;child=None
def stop(signum,frame):raise SystemExit(128+signum)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
with (root/'public-prefetch.stdout').open('wb')as stdout,(root/'public-prefetch.stderr').open('wb')as stderr:
 try:
  child=subprocess.Popen(command,env=environment,stdout=stdout,stderr=stderr,start_new_session=True)
  try:code=child.wait(timeout=90)
  except subprocess.TimeoutExpired:code=124
 finally:
  if child is not None:
   try:os.killpg(child.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   child.wait()
(root/'public-prefetch.result.json').write_text(json.dumps({'command':command,'exitCode':code,'elapsedSeconds':time.monotonic()-started,'scope':'Public transport cache acquisition only; fresh Linux consumer still installs via public index'},indent=2)+'\n')
raise SystemExit(code)
