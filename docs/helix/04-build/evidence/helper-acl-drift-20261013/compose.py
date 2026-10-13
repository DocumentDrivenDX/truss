import subprocess,json,uuid,pathlib,select,os,time,sys
refuse=bool(sys.argv[1:])
if sys.argv[1:] not in ([],['--refuse-event-triggers'],['--refuse-helper-public-grant']):raise ValueError('Exact owner mode required')
root=pathlib.Path('/private/tmp/truss-security-linux-composition');nonce=uuid.uuid4().hex;network='truss-channel-'+nonce[:12];service=network+'-service';peer=network+'-peer';image='truss-security-linux-composition:source-6fc0a27'
def docker(*args,**kw):return subprocess.run(['docker',*args],capture_output=True,text=True,check=True,timeout=90,**kw)
bootstrap=(root/'run-native-channel.sh').read_text().split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
bootstrap=bootstrap[:bootstrap.index('os.execv')]+"os.execv(sys.executable,[sys.executable,'-u','scripts/security_channel_composition_service.py']+"+repr(sys.argv[1:])+")\n"
result={'ownerMode':sys.argv[1][2:] if refuse else 'read','scope':'Owned external peer TLS publication; database stays in service-private local runtime, not a separate network database','controls':{},'cleanup':{}}
process=None;failure=None;pending=bytearray()
def line():
 deadline=time.monotonic()+60
 while b'\n' not in pending:
  remaining=deadline-time.monotonic()
  if remaining<=0 or not select.select([process.stdout],[],[],remaining)[0]:raise TimeoutError('Original service response deadline')
  chunk=os.read(process.stdout.fileno(),4096)
  if not chunk:raise RuntimeError('Original service terminated before response')
  pending.extend(chunk)
  if len(pending)>16384:raise RuntimeError('Original service response limit')
 response,_,rest=pending.partition(b'\n');pending[:]=rest
 return response.decode('utf-8')
try:
 docker('network','create','--internal','--label','truss.security.fixture='+nonce,network)
 args=['docker','run','--rm','-i','--name',service,'--label','truss.security.fixture='+nonce,'--network',network,'--cap-drop','ALL','--cap-add','SETUID','--cap-add','SETGID','--security-opt','no-new-privileges','--mount','type=bind,src=/private/tmp/truss-security-main-integration,dst=/app/truss,readonly','--mount','type=bind,src=/Users/erik/.codex/worktrees/security-main-integration/umf,dst=/Users/erik/.codex/worktrees/security-main-integration/umf,readonly','--workdir','/app/truss','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/app/weft-native:/app/truss/packages/python/src:/app/truss/packages/python/tests:/app/truss/scripts','--env','TRUSS_SECURITY_MAPPING_WEFT_MODULE_DIR=/app/weft-native',image,'python','-u','-']
 process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(root/'composition-service.log').open('w'),text=True)
 process.stdin.write(bootstrap);process.stdin.close()
 descriptor=json.loads(line())
 info=json.loads(docker('inspect',service).stdout)[0];host=info['NetworkSettings']['Networks'][network]['IPAddress'];descriptor['host']=host;descriptor['expectedRefusal']=refuse
 assert not info['HostConfig']['Privileged'] and not info['HostConfig']['PortBindings']
 peer_code='''import sys,json,ssl,socket,http.client,psycopg
v=json.load(sys.stdin);ctx=ssl.create_default_context(cadata=v['certificate']);ctx.minimum_version=ssl.TLSVersion.TLSv1_3
request=b'{"operation":"read-resource"}'
def call(token):
 raw=socket.create_connection((v['host'],v['port']),timeout=30)
 with ctx.wrap_socket(raw,server_hostname='127.0.0.1') as wire:
  assert wire.version()=='TLSv1.3'
  wire.sendall(b'POST /protected/read HTTP/1.1\\r\\nHost: original\\r\\nAuthorization: Bearer '+token.encode()+b'\\r\\nContent-Type: application/json\\r\\nContent-Length: '+str(len(request)).encode()+b'\\r\\n\\r\\n'+request)
  r=http.client.HTTPResponse(wire);r.begin();return r.status,r.read()
assert call('00'*32)==(401,b'{}')
status,packet=call(v['credential'])
if v['expectedRefusal']:
 assert (status,packet)==(503,b'{}');decision=None
else:
 assert status==200;decision=json.loads(packet);assert [r['key'] for r in decision['rows']]==[[{'string':'r1'}]];assert decision['rows'][0]['output'][0]['disposition']=='withheld'
assert call(v['credential'])==(403,b'{}')
try:psycopg.connect(host=v['host'],port=v['sqlPort'],user='consumer',dbname='postgres',connect_timeout=2)
except psycopg.OperationalError as error:
 assert 'Connection refused' in str(error) or 'timeout expired' in str(error),str(error)
else:raise AssertionError('Private SQL endpoint reached')
print(json.dumps({'unknownBearerDenied':True,'verifiedTls13':True,'decision':decision,'genericNativeRefusal':v['expectedRefusal'],'replayDenied':True,'peerServiceTcpSqlDenied':True}))
'''
 docker('run','-d','--name',peer,'--label','truss.security.fixture='+nonce,'--network',network,'--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--entrypoint','sleep',image,'240')
 peer_info=json.loads(docker('inspect',peer).stdout)[0]
 assert peer_info['Mounts']==[] and not peer_info['HostConfig']['Privileged'] and not peer_info['HostConfig']['PortBindings']
 assert peer_info['HostConfig']['ReadonlyRootfs'] and peer_info['HostConfig']['CapDrop']==['ALL']
 assert not any(v.startswith(('PGPASSWORD=','POSTGRES_PASSWORD=')) for v in peer_info['Config']['Env'])
 result['controls']['peerTopology']={'noMounts':True,'noPublishedPorts':True,'readOnlyRootfs':True,'allCapabilitiesDropped':True,'noDeclaredSqlCredential':True,'originalNativeSqlPort':descriptor['sqlPort']}
 observed=docker('exec','-i',peer,'python','-c',peer_code,input=json.dumps(descriptor))
 result['controls']['externalPeer']=json.loads(observed.stdout)
 result['controls']['originalService']=json.loads(line());process.wait(timeout=45);assert process.returncode==0
 result['status']='pass'
except BaseException as error:
 failure=error;result['status']='failed';result['failureType']=type(error).__name__
finally:
 for kind,name in [('container',peer),('container',service),('network',network)]:
  try:
   command=['inspect',name] if kind=='container' else ['network','inspect',name]
   def inspect():
    observed=subprocess.run(['docker',*command],capture_output=True,text=True,timeout=20)
    if observed.returncode==0:return json.loads(observed.stdout)[0]
    missing={f'Error: No such object: {name}',f'error: no such object: {name}'} if kind=='container' else {f'Error response from daemon: network {name} not found'}
    if observed.returncode==1 and observed.stdout.strip() in ('','[]') and observed.stderr.strip() in missing:return None
    raise RuntimeError('Owned cleanup inspection failed; absence unknown')
   item=inspect()
   if item is not None:
    labels=item['Config']['Labels'] if kind=='container' else item['Labels']
    assert labels['truss.security.fixture']==nonce
    if kind=='container':docker('rm','-f','-v',item['Id'])
    else:docker('network','rm',item['Id'])
   result['cleanup'][name]=inspect() is None
  except BaseException as error:
   result['cleanup'][name]=False;result.setdefault('cleanupFailures',{})[name]=type(error).__name__
 if process is not None:
  try:process.wait(timeout=10)
  except BaseException as error:result['status']='failed';result['processSettlementFailure']=type(error).__name__
 if not all(result['cleanup'].values()):result['status']='failed'
 (root/'composition-results.json').write_text(json.dumps(result,indent=2)+'\n')
if failure is not None:raise failure
if result['status']!='pass':raise RuntimeError('Owned composition or cleanup failed; receipt retained')
