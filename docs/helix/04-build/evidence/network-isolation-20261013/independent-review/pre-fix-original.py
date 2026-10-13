"""Owned PostgreSQL18.6 network-domain controls; not protected backend admission."""
import subprocess,json,secrets,uuid,time,sys
from pathlib import Path

IMAGE='postgres@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336'

def qualify(output):
 nonce=uuid.uuid4().hex;prefix='truss-security-net-'+nonce[:12]
 names={k:prefix+'-'+k for k in ('front','back','database','service','peer')}
 password=secrets.token_hex(32);admin_password=secrets.token_hex(32)
 evidence={'scope':'Owned native TCP network isolation only; not TLS/guarded-policy composition or backend readiness','image':IMAGE,'nonce':nonce,'controls':{},'cleanup':{}}
 def docker(*args,input=None,check=True,timeout=20):
  r=subprocess.run(['docker',*args],input=input,capture_output=True,text=True,timeout=timeout)
  if check and r.returncode:raise RuntimeError('Owned Docker fixture operation refused')
  return r
 def inspect(kind,name):
  r=docker(kind,'inspect',name,check=False)
  return json.loads(r.stdout)[0] if r.returncode==0 else None
 def probe(container,host):
  r=docker('exec','--env','PGPASSWORD='+password,container,'psql','-X','-A','-t','-v','ON_ERROR_STOP=1',f'host={host} user=service_reader dbname=postgres connect_timeout=2','-c',"SELECT session_user,rolsuper,rolbypassrls,current_setting('server_version_num'),(SELECT count(*) FROM private_assignment) FROM pg_roles WHERE rolname=session_user",timeout=8,check=False)
  return {'exitCode':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}
 try:
  evidence['dockerVersion']=docker('version','--format','{{.Server.Version}}').stdout.strip()
  for k in ('front','back'):docker('network','create','--internal','--label','truss.security.fixture='+nonce,names[k])
  docker('run','-d','--name',names['database'],'--label','truss.security.fixture='+nonce,'--network',names['back'],'--network-alias','database','--env','POSTGRES_PASSWORD='+admin_password,IMAGE)
  for k in ('service','peer'):
   docker('run','-d','--name',names[k],'--label','truss.security.fixture='+nonce,'--network',names['front'],'--user','postgres','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--entrypoint','sleep',IMAGE,'240')
  docker('network','connect',names['back'],names['service'])
  deadline=time.monotonic()+25
  while docker('exec',names['database'],'pg_isready','-U','postgres',check=False).returncode:
   if time.monotonic()>deadline:raise RuntimeError('Owned database readiness deadline')
   time.sleep(0.2)
  sql="CREATE TABLE private_assignment(staff text,project text,active boolean); INSERT INTO private_assignment VALUES('s1','p1',true); CREATE ROLE service_reader LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOINHERIT NOBYPASSRLS PASSWORD '"+password+"'; GRANT SELECT ON private_assignment TO service_reader;"
  docker('exec','-i',names['database'],'psql','-X','-v','ON_ERROR_STOP=1','-U','postgres',input=sql)
  db=inspect('container',names['database']);service=inspect('container',names['service']);peer=inspect('container',names['peer'])
  db_ip=db['NetworkSettings']['Networks'][names['back']]['IPAddress']
  assert set(db['NetworkSettings']['Networks'])=={names['back']}
  assert set(peer['NetworkSettings']['Networks'])=={names['front']}
  assert set(service['NetworkSettings']['Networks'])=={names['front'],names['back']}
  for item in (db,service,peer):assert not item['HostConfig']['Privileged'] and not item['HostConfig']['PortBindings']
  for item in (service,peer):assert item['HostConfig']['ReadonlyRootfs'] and item['HostConfig']['CapDrop']==['ALL']
  assert not ({m['Source'] for m in db['Mounts']}&{m['Source'] for m in peer['Mounts']})
  assert not any(m['Destination'].endswith('docker.sock') for m in peer['Mounts'])
  assert not any(v.startswith(('PGPASSWORD=','POSTGRES_PASSWORD=')) for v in peer['Config']['Env'])
  evidence['topology']={'databaseNetworks':list(db['NetworkSettings']['Networks']),'serviceNetworks':list(service['NetworkSettings']['Networks']),'peerNetworks':list(peer['NetworkSettings']['Networks']),'noPublishedPorts':True,'peerNoPrivateDatabaseMount':True,'peerNoDockerSocket':True,'peerNoDeclaredSqlCredential':True,'peerAndServiceCapsDropped':True}
  expected='service_reader|f|f|180006|1'
  positive=probe(names['service'],'database');assert positive['exitCode']==0 and positive['stdout']==expected
  evidence['controls']['trustedServiceNativeSql']=positive
  for label,host in [('peerPrivateDns','database'),('peerKnownDatabaseIp',db_ip),('peerServiceFrontSql',service['NetworkSettings']['Networks'][names['front']]['IPAddress']),('peerServiceBackSql',service['NetworkSettings']['Networks'][names['back']]['IPAddress'])]:
   result=probe(names['peer'],host);assert result['exitCode']!=0 and not result['stdout'];evidence['controls'][label]=result
  # Excluded topology administrator can bypass: same peer and valid credential.
  docker('network','connect',names['back'],names['peer'])
  bypass=probe(names['peer'],db_ip);assert bypass['exitCode']==0 and bypass['stdout']==expected
  evidence['controls']['excludedTopologyAdminAttach']=bypass
  docker('network','disconnect',names['back'],names['peer'])
  restored=probe(names['peer'],db_ip);assert restored['exitCode']!=0 and not restored['stdout']
  evidence['controls']['peerIsolationRestored']=restored
  evidence['status']='pass'
 except BaseException as error:
  evidence['status']='failed';evidence['failureType']=type(error).__name__;raise
 finally:
  for kind,keys in [('container',('peer','service','database')),('network',('front','back'))]:
   for k in keys:
    item=inspect(kind,names[k])
    if item is not None:
     labels=item['Config']['Labels'] if kind=='container' else item['Labels']
     if labels.get('truss.security.fixture')!=nonce:raise RuntimeError('Original owned cleanup identity required')
     if kind=='container':docker('rm','-f','-v',item['Id'])
     else:docker('network','rm',item['Id'])
    absent=inspect(kind,names[k]) is None;evidence['cleanup'][k]=absent
    if not absent:raise RuntimeError('Owned fixture cleanup incomplete')
  output.mkdir(parents=True,exist_ok=True)
  (output/'results.json').write_text(json.dumps(evidence,indent=2)+'\n')
 return evidence

if __name__=='__main__':
 result=qualify(Path(sys.argv[1]));print(json.dumps({'status':result['status'],'controls':len(result['controls']),'ownedResourcesAbsent':all(result['cleanup'].values())}))
