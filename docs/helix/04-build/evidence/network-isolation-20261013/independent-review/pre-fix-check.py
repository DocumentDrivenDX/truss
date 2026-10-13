"""Actual qualifier with synthetic Docker process responses; never invokes Docker."""
from pathlib import Path
import importlib.util,json,subprocess,hashlib,sys,tempfile
from unittest.mock import patch
ROOT=Path('/private/tmp/network-isolation-review-20261013')
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'original.py'
spec=importlib.util.spec_from_file_location('reviewed_network',SOURCE);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class FakeDocker:
 def __init__(self,mode):self.mode=mode;self.resources={};self.probes=0;self.removed=[];self.first_failure=False
 def __call__(self,argv,**kwargs):
  assert argv[0]=='docker';a=argv[1:]
  def result(code=0,out='',err=''):return subprocess.CompletedProcess(['synthetic-docker'],code,out,err)
  if a[0]=='version':return result(out='29.4.0')
  if a[:2]==['network','create']:
   name=a[-1];label=a[a.index('--label')+1].split('=',1);self.resources[name]={'Id':'id-'+name,'Labels':{label[0]:label[1]}};return result(out='id-'+name)
  if a[0]=='run':
   name=a[a.index('--name')+1];network=a[a.index('--network')+1];label=a[a.index('--label')+1].split('=',1);self.resources[name]={'Id':'id-'+name,'Config':{'Labels':{label[0]:label[1]},'Env':[]},'NetworkSettings':{'Networks':{network:{'IPAddress':'192.168.1.'+('2' if name.endswith('database') else '3')}}},'HostConfig':{'Privileged':False,'PortBindings':{},'ReadonlyRootfs':True,'CapDrop':['ALL']},'Mounts':[{'Source':'volume-'+name,'Destination':'/data'}]};return result(out='id-'+name)
  if a[:2]==['network','connect']:
   self.resources[a[3]]['NetworkSettings']['Networks'][a[2]]={'IPAddress':'192.168.2.3'};return result()
  if a[:2]==['network','disconnect']:
   del self.resources[a[3]]['NetworkSettings']['Networks'][a[2]];return result()
  if a[0]=='exec':
   if '--env' not in a:return result()
   self.probes+=1
   if self.probes in (1,6):return result(out='service_reader|f|f|180006|1\n')
   if self.mode=='auth_negative':return result(2,err='psql: error: FATAL: password authentication failed for user "service_reader"')
   if self.mode=='exec_negative':return result(1,err='Error response from daemon: container is not running')
   return result(2,err='psql: error: connection to server at "192.168.1.2", port 5432 failed: Network is unreachable')
  if len(a)>1 and a[1]=='inspect':
   if self.mode=='cleanup_daemon_error' and self.probes>=7:return result(1,err='Cannot connect to the Docker daemon')
   item=self.resources.get(a[2]);return result(out=json.dumps([item])) if item else result(1,err='Error response from daemon: No such '+a[0]+': '+a[2])
  if a[0]=='rm' or a[:2]==['network','rm']:
   if self.mode=='first_remove_error' and not self.first_failure:self.first_failure=True;return result(1,err='temporary cleanup failure')
   key=next(k for k,v in self.resources.items() if v['Id']==a[-1]);self.removed.append(key.split('-')[-1]);del self.resources[key];return result()
  raise AssertionError('Unscripted Docker operation')
rows=[]
for mode in ('baseline','cleanup_daemon_error','first_remove_error','auth_negative','exec_negative'):
 fake=FakeDocker(mode)
 with tempfile.TemporaryDirectory(prefix='network-review-') as d:
  out=Path(d);error=None;receipt=None
  with patch.object(module.subprocess,'run',fake):
   try:receipt=module.qualify(out)
   except BaseException as e:error=type(e).__name__+': '+str(e)
  rows.append({'control':mode,'status':receipt.get('status') if receipt else None,'cleanup':receipt.get('cleanup') if receipt else None,'exception':error,'receiptWritten':(out/'results.json').exists(),'remainingResources':len(fake.resources),'removed':fake.removed})
result={'scope':'Synthetic Docker response fault injection into actual qualifier; no Docker/container/network lifecycle invoked','sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'controls':rows}
(ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
