"""Bounded actual-qualifier fault injection. All Docker subprocess calls are mocked."""
from pathlib import Path
import importlib.util,json,subprocess,hashlib,sys,tempfile
from unittest.mock import patch
ROOT=Path('/private/tmp/network-isolation-review-20261013')
SOURCE=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('reviewed_network',SOURCE);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class FakeDocker:
 def __init__(self,mode):self.mode=mode;self.resources={};self.probes=0;self.removed=[];self.first_failure=False;self.cleanup_attempts=[]
 def __call__(self,argv,**kwargs):
  assert argv[0]=='docker';a=argv[1:]
  def result(code=0,out='',err=''):return subprocess.CompletedProcess(['synthetic-docker'],code,out,err)
  if a[0]=='version':return result(1,err='Cannot connect to the Docker daemon') if self.mode=='initial_failure' else result(out='29.4.0')
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
   host=next(v for v in a if v.startswith('host=')).split()[0][5:]
   if self.mode in ('auth_negative','primary_and_cleanup'):return result(2,err='psql: error: FATAL: password authentication failed for user "service_reader"')
   if self.mode=='exec_negative':return result(1,err='Error response from daemon: container is not running')
   if self.mode=='sql_negative':return result(2,err='psql: error: ERROR: relation "private_assignment" does not exist')
   if self.mode=='wrong_host':host='unrelated'
   cause={'refused':'Connection refused','timeout':'timeout expired','timed_out':'Connection timed out'}.get(self.mode,'Network is unreachable')
   msg=('psql: error: could not translate host name "database" to address: '+('Name or service not known' if self.mode=='dns_alternative' else 'Temporary failure in name resolution')) if host=='database' else f'psql: error: connection to server at "{host}", port 5432 failed: {cause}'
   return result(1 if self.mode=='wrong_exit' else 2,'unexpected SQL output' if self.mode=='negative_stdout' else '',msg)
  if len(a)>1 and a[1]=='inspect':
   if self.probes>=7:self.cleanup_attempts.append(a[2].split('-')[-1])
   if self.mode=='cleanup_daemon_error' and self.probes>=7:return result(1,err='Cannot connect to the Docker daemon')
   item=self.resources.get(a[2])
   if item:
    if self.mode=='wrong_cleanup_label' and self.probes>=7 and a[2].endswith('peer'):item['Config']['Labels']={}
    return result(out=json.dumps([item]))
   name=a[2];err='Error response from daemon: No such '+a[0]+': '+name
   if self.mode=='notfound_object':err='Error: No such object: '+name
   if self.mode=='notfound_kind':err='Error: No such '+a[0]+': '+name
   if self.mode=='notfound_network' and a[0]=='network':err='Error response from daemon: network '+name+' not found'
   if self.mode=='missing_wrong_name':err+='-different'
   if self.mode=='missing_wrong_error':err='permission denied'
   return result(2 if self.mode=='missing_wrong_exit' else 1,'unrelated output' if self.mode=='missing_wrong_stdout' else '[]',err)
  if a[0]=='rm' or a[:2]==['network','rm']:
   if self.mode in ('first_remove_error','primary_and_cleanup') and not self.first_failure:self.first_failure=True;return result(1,err='temporary cleanup failure')
   key=next(k for k,v in self.resources.items() if v['Id']==a[-1]);assert a[-1]=='id-'+key;self.removed.append(key.split('-')[-1]);del self.resources[key];return result()
  raise AssertionError('Unscripted Docker operation')
accepted={'baseline','dns_alternative','refused','timeout','timed_out','notfound_object','notfound_kind','notfound_network'}
modes=list(accepted)+['cleanup_daemon_error','first_remove_error','wrong_cleanup_label','auth_negative','exec_negative','sql_negative','wrong_host','wrong_exit','negative_stdout','missing_wrong_name','missing_wrong_error','missing_wrong_exit','missing_wrong_stdout','primary_and_cleanup','initial_failure']
rows=[]
for mode in sorted(modes):
 fake=FakeDocker(mode)
 with tempfile.TemporaryDirectory(prefix='network-review-') as d:
  out=Path(d);error=None
  with patch.object(module.subprocess,'run',fake):
   try:module.qualify(out)
   except BaseException as e:error=type(e).__name__+': '+str(e)
  assert (out/'results.json').exists(),mode
  receipt=json.loads((out/'results.json').read_bytes())
  assert set(receipt['cleanup'])=={'peer','service','database','front','back'},mode
  if mode in accepted:assert error is None and receipt['status']=='pass' and not fake.resources,mode
  else:assert error and receipt['status']=='failed',mode
  if mode=='cleanup_daemon_error':assert len(fake.resources)==5 and not any(receipt['cleanup'].values()) and set(fake.cleanup_attempts)=={'peer','service','database','front','back'}
  if mode in ('first_remove_error','wrong_cleanup_label','primary_and_cleanup'):assert fake.removed==['service','database','front','back'] and receipt['cleanup']['peer'] is False,mode
  if mode=='primary_and_cleanup':assert error=='RuntimeError: Original native network denial required; auth/SQL/infrastructure failures do not qualify',error
  rows.append({'control':mode,'passed':True,'qualificationStatus':receipt['status'],'cleanup':receipt['cleanup'],'exception':error,'remainingSyntheticResources':len(fake.resources),'removed':fake.removed})
result={'scope':'Actual qualifier with synthetic Docker responses; no Docker/container/native lifecycle invoked','sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'passed':len(rows),'controls':rows}
(ROOT/'results-final.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':len(rows),'sourceSha256':result['sourceSha256']}))
