"""Owned PostgreSQL17.9 original-response census witness, never backend acceptance."""
import hashlib,json,os,secrets,subprocess,tempfile,time,uuid,zipfile
from pathlib import Path
root=Path.cwd();run_id=str(uuid.uuid4());name='truss-source-census-'+run_id
folder=root/'docs/helix/04-build/evidence/security-source-census-transport'/run_id
folder.mkdir(parents=True,mode=0o700)
command_log=[];container=None;creation_attempted=False;result=None
def command(args,**kwargs):
 return subprocess.run(args,text=True,capture_output=True,timeout=kwargs.pop('timeout',30),**kwargs)
def require(r):
 if r.returncode:raise RuntimeError('Witness command failed: '+r.stderr[:2000])
 return r.stdout.strip()
sha=lambda b:hashlib.sha256(b).hexdigest()
with tempfile.TemporaryDirectory(prefix='truss-census-build-') as build:
 build=Path(build);meta=build/'metafile.json'
 args=['bun','build','packages/pg-runtime/tools/security-source-census-native.ts','--target=bun','--outdir='+str(build),'--metafile='+str(meta),'--sourcemap=external']
 built=command(args);(folder/'build.stdout.log').write_text(built.stdout);(folder/'build.stderr.log').write_text(built.stderr);require(built)
 graph=json.loads(meta.read_text());paths=[Path(p) for p in graph['inputs']]
 paths += [Path(__file__),Path('packages/postgresql/native/security-query-source-census.sql'),*[Path('tests')/p for p in ['security-source-census.test.ts','pg-wire.test.ts','query-journal.test.ts']],Path('docs/helix/04-build/evidence/inert-assembly/native-wire.json'),Path('bun.lock'),Path('package.json'),Path('packages/pg-runtime/package.json')]
 for p in list(paths):
  for parent in p.parents:
   manifest=parent/'package.json'
   if manifest.is_file():paths.append(manifest);break
 paths=list(dict.fromkeys(paths));frozen={str(p):p.read_bytes() for p in paths};pins={p:sha(b) for p,b in frozen.items()}
 # The first build only discovers inputs. The qualifying build happens after
 # freezing every input and must consume the identical graph/current preimages.
 (folder/'discovery.stdout.log').write_text(built.stdout);(folder/'discovery.stderr.log').write_text(built.stderr)
 if any(Path(p).read_bytes()!=b for p,b in frozen.items()):raise RuntimeError('Source changed before qualifying build')
 built=command(args);(folder/'build.stdout.log').write_text(built.stdout);(folder/'build.stderr.log').write_text(built.stderr);require(built)
 if set(json.loads(meta.read_text())['inputs'])!=set(graph['inputs']) or any(Path(p).read_bytes()!=b for p,b in frozen.items()):raise RuntimeError('Qualifying build input changed')
 bundle=build/'security-source-census-native.js'
 outputs={p.name:p.read_bytes() for p in [bundle,build/'security-source-census-native.js.map',meta]}
 with zipfile.ZipFile(folder/'sources.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for p,b in frozen.items():archive.writestr(p,b)
  for p,b in outputs.items():archive.writestr('executed-build/'+p,b)
 with zipfile.ZipFile(folder/'sources.zip') as archive:
  assert all(archive.read(p)==b for p,b in frozen.items())
 try:
  check=command(['bun','test','tests/security-source-census.test.ts','tests/pg-wire.test.ts','tests/query-journal.test.ts'],timeout=60)
  (folder/'host.stdout.log').write_text(check.stdout);(folder/'host.stderr.log').write_text(check.stderr);require(check)
  typed=command(['node_modules/.bin/tsc','--ignoreConfig','--noEmit','--strict','--target','ES2022','--module','ESNext','--moduleResolution','bundler','packages/pg-runtime/src/security-source-census.ts','packages/pg-runtime/tools/security-source-census-native.ts'])
  (folder/'typecheck.stdout.log').write_text(typed.stdout);(folder/'typecheck.stderr.log').write_text(typed.stderr);require(typed)
  if name in require(command(['docker','container','ls','-a','--format','{{.Names}}'])).splitlines():raise RuntimeError('Preexisting fixture')
  password=secrets.token_hex(32);creation_attempted=True
  container=require(command(['docker','run','-d','--name',name,'--label','truss.security.run='+run_id,'--publish','127.0.0.1::5432','-e','POSTGRES_PASSWORD','postgres:17.9'],env={**os.environ,'POSTGRES_PASSWORD':password}))
  deadline=time.monotonic()+25
  while command(['docker','exec',container,'pg_isready','-h','127.0.0.1','-U','postgres']).returncode:
   if time.monotonic()>deadline:raise TimeoutError('Readiness')
   time.sleep(.1)
  details=json.loads(require(command(['docker','inspect',container])))[0]
  if details['Config']['Labels'].get('truss.security.run')!=run_id:raise RuntimeError('Owned fixture required')
  # Environment (including credentials) is intentionally never retained.
  port=int(details['NetworkSettings']['Ports']['5432/tcp'][0]['HostPort'])
  engine=require(command(['docker','exec',container,'psql','-X','-A','-t','-U','postgres','-c',"SELECT version();"]))
  native=command(['bun',str(bundle)],input=json.dumps({'source':str(root/'packages/postgresql/native/security-query-source-census.sql'),'port':port,'password':password,'evidence':str(folder)}),timeout=180)
  (folder/'native.stdout.log').write_text(native.stdout);(folder/'native.stderr.log').write_text(native.stderr);require(native)
  if any(Path(p).read_bytes()!=b for p,b in frozen.items()):raise RuntimeError('Executed source changed')
  result={'status':'component-passed','runId':run_id,'sourceDigests':pins,'buildOutputs':{p:sha(b) for p,b in outputs.items()},'buildCommand':args,'nativeCommand':['bun','executed-build/security-source-census-native.js'],'hostCommand':['bun','test','tests/security-source-census.test.ts','tests/pg-wire.test.ts','tests/query-journal.test.ts'],'versions':{'bun':require(command(['bun','--version'])),'engine':engine,'pg':'8.16.3'},'scope':'Exact bundled source closure and original native wire census capture on excluded installer. Local custody identifiers are not authenticated native authority. No heap/CPU bound, Python16.15 port, graph profile, writer coordination or backend acceptance.'}
 except BaseException as error:
  result={'status':'failed','runId':run_id,'sourceDigests':pins,'error':str(error),'scope':'Retained failed component attempt; no acceptance or source correspondence claim.'}
 finally:
  cleanup={'attempted':False}
  if creation_attempted:
   inventory=command(['docker','container','inspect',container or name]);cleanup={'attempted':True,'inspectionExitCode':inventory.returncode}
   if inventory.returncode==0:
    found=json.loads(inventory.stdout)[0]
    if found['Config']['Labels'].get('truss.security.run')!=run_id:raise RuntimeError('Cleanup identity mismatch')
    removed=command(['docker','rm','-f',found['Id']]);cleanup.update({'container':found['Id'],'exitCode':removed.returncode,'stdout':removed.stdout,'stderr':removed.stderr})
    remaining=command(['docker','container','ls','-a','--filter','id='+found['Id'],'--format','{{.ID}}'])
    cleanup.update({'absenceExitCode':remaining.returncode,'remaining':remaining.stdout,'absenceStderr':remaining.stderr})
    if removed.returncode or remaining.returncode or remaining.stdout.strip():result['status']='failed'
   else:
    cleanup.update({'scope':'Unknown fixture state; inspection failed','stderr':inventory.stderr});result['status']='failed'
  result['cleanup']=cleanup;(folder/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'evidence':str(folder)}))
 if result['status']!='component-passed':raise SystemExit(1)
