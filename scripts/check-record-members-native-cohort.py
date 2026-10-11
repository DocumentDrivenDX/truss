"""Owned native scalar and membership report composition; no backend enforcement admission."""
from pathlib import Path
import os,json,hashlib,uuid,subprocess,time,zipfile
root=Path.cwd();out=root/'docs/helix/04-build/evidence/record-members-native-cohort'/str(uuid.uuid4());out.mkdir(parents=True)
env=os.environ.copy();sha=lambda b:hashlib.sha256(b).hexdigest()
host=root/'docs/helix/04-build/evidence/original-occurrence-inventory/ae5c7e87-96b6-4f88-af81-9240d82edde0/receipt.json'
hostReceipt=json.loads(host.read_text())
for p in hostReceipt['sourcePreimages']:
 if sha(Path(p['path']).read_bytes())!=p['sha256']:raise RuntimeError('Host source precondition changed: '+p['path'])
absent=hostReceipt['absentConfigurations']
if any(Path(p).exists() for p in absent):raise RuntimeError('Absent host configuration appeared')
pins={str(Path(p['path']).resolve()):p['sha256'] for p in hostReceipt['sourcePreimages']}
producerDirectories={}
for role in ['TRUSS_UMF_PRODUCER','TRUSS_UMF_DECLARATION_PRODUCER','TRUSS_UMF_FIELD_ASSERTION_PRODUCER','TRUSS_UMF_SCALAR_TYPE_PRODUCER','TRUSS_UMF_RECORD_MEMBERS_PRODUCER']:
 if not env.get(role):raise RuntimeError('Exact original producer directory required: '+role)
 directory=Path(env[role]).resolve();producerDirectories[role]=str(directory)
 for name in ['producer.js','producer.ts','producer-manifest.json']:
  path=directory/name
  if str(path) not in pins or sha(path.read_bytes())!=pins[str(path)]:raise RuntimeError('Executed producer is not the host-captured bundle: '+str(path))
paths={Path(p['path']) for p in hostReceipt['sourcePreimages']}
paths.update([Path(__file__).resolve(),host,root/'scripts/check-catalog-new-cohort.ts',root/'scripts/build-configuration-context-admission.py'])
paths.update(root.joinpath('packages/postgresql/native').rglob('*.sql'))
paths.update(root/'docs/helix/04-build/evidence'/p for p in ['qualified-property-layout-0.15.owner-export.sql','source-epoch-storage.owner-export.sql','operation-configuration-storage.owner-export.sql'])
preimages={str(p):p.read_bytes() for p in sorted(paths)}
container=None;inventory=None;cleanup=None;failure=None;native=None
suffix=uuid.uuid4().hex;dbname='truss_members_cohort_'+suffix;name='truss-members-cohort-'+suffix;cidfile=out/'container.cid'
try:
 created=subprocess.run(['docker','run','-d','--name',name,'--cidfile',str(cidfile),'--label','truss.members.fixture.owner='+suffix,'-e','POSTGRES_HOST_AUTH_METHOD=trust','-e','POSTGRES_DB='+dbname,'-p','127.0.0.1::5432','postgres:17.9'],capture_output=True,text=True,timeout=60)
 if created.returncode:raise RuntimeError('Owned fixture creation failed: '+created.stderr)
 container=created.stdout.strip()
 if len(container)!=64 or any(c not in '0123456789abcdef' for c in container):raise RuntimeError('Unexpected container identity')
 inspected=json.loads(subprocess.check_output(['docker','inspect',container],text=True,timeout=20))[0]
 ports=inspected['NetworkSettings']['Ports']['5432/tcp']
 if inspected['Id']!=container or inspected['Config']['Labels'].get('truss.members.fixture.owner')!=suffix or len(ports)!=1 or ports[0]['HostIp']!='127.0.0.1':raise RuntimeError('Exact loopback fixture correspondence required')
 inventory={'containerId':container,'imageId':inspected['Image'],'database':dbname,'port':ports[0]['HostPort'],'scope':'Owned disposable native candidate collector fixture'}
 ready=False
 for _ in range(60):
  probe=subprocess.run(['docker','exec',container,'pg_isready','-U','postgres','-d',dbname],capture_output=True,text=True,timeout=5)
  if probe.returncode==0:ready=True;break
  time.sleep(.25)
 if not ready:raise RuntimeError('Fixture readiness exhausted')
 env['TRUSS_OPERATION_TEST_URL']='postgres://postgres@127.0.0.1:'+ports[0]['HostPort']+'/'+dbname
 env['TRUSS_COHORT_EVIDENCE']=str(out/'native.json')
 native=subprocess.run(['bun','scripts/check-catalog-new-cohort.ts'],env=env,capture_output=True,text=True,timeout=120)
 (out/'native.log').write_text(native.stdout+native.stderr)
 if native.returncode:raise RuntimeError('Native composition failed: '+str(native.returncode))
 report=json.loads((out/'native.json').read_text())
 required=[
  'actual native report retains both original scalar family duties',
  'actual native report retains independent scalar owner revision and bundle',
  'actual native report ordered coverage includes every scalar element observation',
  'native scalar composition preserves original artifact and explicit unqualified status',
  'actual native report retains both membership declarations and member occurrences',
  'actual native report retains independent membership owner revision and bundle',
  'actual native report ordered coverage includes every membership element observation',
  'native membership composition preserves original artifact and explicit unqualified status',
  'actual empty membership stages one Record without invented properties',
  'actual empty membership retains its explicit original declaration duty']
 if any(report['checks'].count(check)!=1 for check in required):raise RuntimeError('All ten native scalar and membership observations required')
 scalarManifest=json.loads((Path(producerDirectories['TRUSS_UMF_SCALAR_TYPE_PRODUCER'])/'producer-manifest.json').read_text())
 if report['assertionProfiles']['scalar']!={'identity':'umf-scalar-type-inspection','version':scalarManifest['revision'],'sha256':scalarManifest['bundleSha256']}:raise RuntimeError('Native scalar owner pin correspondence required')
 memberManifest=json.loads((Path(producerDirectories['TRUSS_UMF_RECORD_MEMBERS_PRODUCER'])/'producer-manifest.json').read_text())
 if report['assertionProfiles']['members']!={'identity':'umf-record-members-inspection','version':memberManifest['revision'],'sha256':memberManifest['bundleSha256']}:raise RuntimeError('Native membership owner pin correspondence required')
except Exception as e:failure=str(e)
finally:
 # Creation may have succeeded even when docker run timed out before stdout.
 # Recover only our fresh, exact labeled/name fixture; never delete by broad name matching.
 try:
  recovered=subprocess.run(['docker','inspect',name],capture_output=True,text=True,timeout=20)
  if recovered.returncode==0:
   owned=json.loads(recovered.stdout)[0]
   if owned['Name']!='/'+name or owned['Config']['Labels'].get('truss.members.fixture.owner')!=suffix:raise RuntimeError('Owned cleanup identity recovery refused')
   recoveredId=owned['Id']
   if container is not None and container!=recoveredId:raise RuntimeError('Created/recovered fixture identity mismatch')
   container=recoveredId
   removed=subprocess.run(['docker','rm','-f',container],capture_output=True,text=True,timeout=30)
   cleanup={'containerId':container,'exitCode':removed.returncode,'stdout':removed.stdout.strip(),'stderr':removed.stderr.strip(),'recoveredByExactNameAndLabel':True}
   if removed.returncode:raise RuntimeError('Owned fixture cleanup failed')
  elif container is None and not cidfile.exists() and 'no such object:' in recovered.stderr.lower():
   cleanup={'containerId':None,'exitCode':0,'status':'not_created','recoveryStderr':recovered.stderr.strip()}
  else:raise RuntimeError('Owned fixture recovery state uncertain: '+recovered.stderr)
 except Exception as cleanupError:
  cleanup={'containerId':container,'exitCode':1,'error':str(cleanupError)}
  failure=(failure+'; ' if failure else '')+str(cleanupError)
 if failure:(out/'failure.json').write_text(json.dumps({'failure':failure,'nativeFixture':inventory,'cleanup':cleanup,'ownedName':name,'cidfile':str(cidfile)},indent=2)+'\n')
if failure:raise RuntimeError(failure)
if any(Path(p).exists() for p in absent):raise RuntimeError('Absent configuration appeared during native verification')
if any(Path(p).read_bytes()!=b for p,b in preimages.items()):raise RuntimeError('Captured native input changed')
with zipfile.ZipFile(out/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for i,(p,b) in enumerate(preimages.items()):z.writestr(str(i)+'/'+Path(p).name,b)
receipt={'status':'passed','command':['bun','scripts/check-catalog-new-cohort.ts'],'exitCode':native.returncode,'sourcePreimages':[{'path':p,'archive':str(i)+'/'+Path(p).name,'sha256':sha(b)} for i,(p,b) in enumerate(preimages.items())],'nativeFixture':inventory,'cleanup':cleanup,'nativeReceiptSha256':sha((out/'native.json').read_bytes()),'nativeLogSha256':sha((out/'native.log').read_bytes()),'producerDirectories':producerDirectories,'absentConfigurations':absent,'scope':'Actual PostgreSQL17.9 private new-cohort/report/observer correspondence with original scalar and membership owner duties; no installed scalar/member data enforcement, authenticated issuer, complete accepted-report authority/publication/finalizer or public admission','premises':['Local Bun/dependencies and Docker image/runtime, not hermetic','Hostae5c7e87 config absence and owner custody premises remain; self-declared producer manifests are not issuer authentication'],'acceptancePromoted':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'passed','sourcePins':len(preimages),'checks':len(json.loads((out/'native.json').read_text())['checks']),'receipt':str(out/'receipt.json'),'cleanup':cleanup['exitCode']}))
