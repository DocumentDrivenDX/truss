"""Pure current-source controls; Docker, socket binds and native SQL never run."""
from pathlib import Path
from unittest.mock import patch
import subprocess,runpy,json,hashlib,unittest,sys,ssl,ast,types,os,select,time
sys.path.insert(0,'/private/tmp/truss-security-main-integration/scripts')
from security_catalog_channel import AuthenticatedReadChannel
base=Path('/private/tmp/channel-composition-review-20261013');source=Path('/private/tmp/truss-security-linux-composition/compose.py');service=Path('/private/tmp/truss-security-main-integration/scripts/security_channel_composition_service.py');rows=[]
for mode in ('unowned_network','remove_failure','daemon_failure','absent'):
 calls=[];written=[];state={};nonce=None
 def fake_run(argv,**kwargs):
  global nonce
  a=argv[1:];calls.append(a[:2])
  if a[:2]==['network','create']:
   nonce=a[a.index('--label')+1].split('=',1)[1];name=a[-1]
   if mode=='unowned_network':state[name]={'Id':'foreign-network-id','Labels':{'truss.security.fixture':'foreign'}}
   if mode=='remove_failure':
    for suffix in ('peer','service'):state[name+'-'+suffix]={'Id':'owned-'+suffix,'Config':{'Labels':{'truss.security.fixture':nonce}}}
    state[name]={'Id':'owned-network','Labels':{'truss.security.fixture':nonce}}
   raise subprocess.CalledProcessError(1,['synthetic-primary-failure'])
  if a[0]=='inspect' or a[:2]==['network','inspect']:
   kind='network' if a[0]=='network' else 'container';name=a[-1]
   if mode=='daemon_failure':return subprocess.CompletedProcess(['synthetic-docker'],1,'','Cannot connect to Docker daemon')
   if name in state:return subprocess.CompletedProcess(['synthetic-docker'],0,json.dumps([state[name]]),'')
   error='Error response from daemon: network '+name+' not found' if kind=='network' else 'error: no such object: '+name
   return subprocess.CompletedProcess(['synthetic-docker'],1,'[]',error)
  if a[0]=='rm' or a[:2]==['network','rm']:
   if a[-1]=='owned-peer':raise subprocess.CalledProcessError(1,['synthetic-cleanup-failure'])
   assert a[-1]!='foreign-network-id'
   del state[next(k for k,v in state.items() if v['Id']==a[-1])]
   return subprocess.CompletedProcess(['synthetic-docker'],0,'','')
  raise AssertionError(a[:2])
 def fake_write(path,text,*args,**kwargs):written.append(json.loads(text));return len(text)
 with patch('subprocess.run',fake_run),patch.object(Path,'write_text',fake_write):
  try:runpy.run_path(str(source))
  except subprocess.CalledProcessError as e:assert e.cmd==['synthetic-primary-failure']
  else:raise AssertionError('Original failure lost')
 assert len(written)==1 and written[0]['status']=='failed' and len(written[0]['cleanup'])==3
 if mode=='unowned_network':assert len(state)==1 and ['network','rm'] not in calls
 if mode=='remove_failure':assert len(state)==1 and ['network','rm'] in calls
 if mode=='daemon_failure':assert not any(written[0]['cleanup'].values())
 if mode=='absent':assert all(written[0]['cleanup'].values())
 rows.append({'control':'cleanup_'+mode,'passed':True,'receiptRetained':True,'primaryPreserved':True})
server=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server.minimum_version=ssl.TLSVersion.TLSv1_3
bad=[('0.0.0.0',0),('192.0.2.1',443),('localhost',0),('::1',0),('127.0.0.1',True),('127.0.0.1',-1),('127.0.0.1',65536),['127.0.0.1',0],('127.1',0),('127.000.0.1',0)]
with patch('security_catalog_channel.HTTPServer.__init__') as bind:
 for a in bad:
  try:AuthenticatedReadChannel(bytes(32),lambda p:None,bind_address=a)
  except ValueError:pass
  else:raise AssertionError(a)
  rows.append({'control':'invalid_bind_'+str(len(rows)),'passed':True})
 bind.assert_not_called()
 for a,ctx in [(('127.0.0.1',0),None),(('127.0.0.2',54321),None),(('0.0.0.0',0),server),(('192.0.2.1',443),server)]:
  AuthenticatedReadChannel(bytes(32),lambda p:None,tls_context=ctx,bind_address=a);rows.append({'control':'valid_bind_'+str(len(rows)),'passed':True})
 assert bind.call_count==4
# Execute unchanged retained function ASTs with bounded synthetic dependencies.
tree=ast.parse(source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='line')
for mode in ('two_lines','limit','deadline','eof','invalid_utf8'):
 env={'time':types.SimpleNamespace(monotonic=lambda:0),'select':types.SimpleNamespace(select=lambda *a:([1],[],[]) if mode!='deadline' else ([],[],[])),'os':types.SimpleNamespace(read=None),'process':types.SimpleNamespace(stdout=types.SimpleNamespace(fileno=lambda:99)),'pending':bytearray()}
 chunks=iter({'two_lines':[b'one\ntwo\n'],'limit':[b'x'*4096]*5,'eof':[b''],'invalid_utf8':[b'\xff\n'],'deadline':[]}[mode]);env['os'].read=lambda *a:next(chunks)
 exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),env)
 if mode=='two_lines':assert env['line']()=='one' and env['line']()=='two'
 else:
  try:env['line']()
  except (RuntimeError,TimeoutError,UnicodeDecodeError):pass
  else:raise AssertionError(mode)
 rows.append({'control':'bounded_line_'+mode,'passed':True})
tree=ast.parse(service.read_text());serve=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='serve');body=next(n for n in serve.body if isinstance(n,ast.Try)).finalbody
cleanup=ast.FunctionDef(name='cleanup',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='fixture'),ast.arg(arg='cls')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[]);mod=ast.fix_missing_locations(ast.Module(body=[cleanup],type_ignores=[]));env={};exec(compile(mod,str(service),'exec'),env)
for mode in ('ok','teardown','cleanup_false','class_failure','all'):
 called=[]
 def td():
  called.append('tearDown')
  if mode in ('teardown','all'):raise ValueError('synthetic teardown')
 def dc():called.append('doCleanups');return mode not in ('cleanup_false','all')
 def cc():
  called.append('doClassCleanups');cls.tearDown_exceptions=[(ValueError,ValueError('synthetic class'),None)] if mode in ('class_failure','all') else []
 cls=types.SimpleNamespace(doClassCleanups=cc);fixture=types.SimpleNamespace(tearDown=td,doCleanups=dc)
 try:env['cleanup'](fixture,cls)
 except RuntimeError:assert mode!='ok'
 else:assert mode=='ok'
 assert called==['tearDown','doCleanups','doClassCleanups'];rows.append({'control':'service_cleanup_'+mode,'passed':True})
r={'scope':'Actual qualifier mocked-Docker failures, actual bind constructor with mocked socket initialization, unchanged function AST controls for bounded line/cleanup; no Docker/socket/native lifecycle invoked','passed':len(rows),'controls':rows,'sourcePins':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,service,Path('/private/tmp/truss-security-main-integration/scripts/security_catalog_channel.py')]}}
(base/'results-final.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':len(rows),'sourcePins':r['sourcePins']}))
