# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fresh owned PostgreSQL codec/Chromium/host custody evidence, not backend admission."""
from pathlib import Path
import os, json, uuid, hashlib, zipfile, subprocess, time
ROOT=Path.cwd();out=ROOT/'docs/helix/04-build/evidence/original-byte-custody'/str(uuid.uuid4());out.mkdir(parents=True)
env=os.environ.copy();sha=lambda b:hashlib.sha256(b).hexdigest()
tests=['tests/original-byte-custody.test.ts','tests/acceptance-json.test.ts','tests/source-occurrence-index.test.ts','tests/canonical-wire-tree.test.ts','tests/acceptance-input-inspector.test.ts','tests/canonical-report-handoff.test.ts','tests/composed-report-handoff.test.ts','tests/catalog-input-preparation.test.ts','tests/catalog-core-assertion-identities.test.ts','tests/asserted-origin-map.test.ts']
paths=set(p for folder in ['packages/umf-bun/src','packages/postgresql/src','docs/helix/02-design/contracts'] for p in (ROOT/folder).rglob('*') if p.is_file() and (p.suffix in ['.ts','.json'] or p.name.endswith('.d.ts')))
paths.update(ROOT/p for p in tests+['scripts/check-original-byte-custody.py','scripts/check-original-byte-browser.ts','scripts/check-canonical-report-native.ts','docs/helix/03-test/report-wire-untrusted.fixture.json','docs/helix/03-test/acceptance-outer-json-expected.proposal.json','packages/postgresql/native/canonical-string-bytes.sql','packages/postgresql/native/canonical-tree-bytes.sql'])
for role in ['TRUSS_UMF_PRODUCER','TRUSS_UMF_DECLARATION_PRODUCER','TRUSS_UMF_FIELD_ASSERTION_PRODUCER']:
 paths.update(Path(env[role])/p for p in ['producer.js','producer.ts','producer-manifest.json'])
paths.add(Path('/Users/erik/Projects/umf/package.json'));paths=sorted(paths);preimages={str(p):p.read_bytes() for p in paths}
def execute(args,log,timeout=90):
 r=subprocess.run(args,env=env,capture_output=True,text=True,timeout=timeout);(out/log).write_text(r.stdout+r.stderr)
 if r.returncode:raise RuntimeError(log+' failed: '+str(r.returncode))
 return r
host=execute(['bun','test',*tests],'host.txt')
typecmd=['bun',env['UMF_TSC'],'--ignoreConfig','--noEmit','--strict','--skipLibCheck','--target','ES2022','--module','ESNext','--moduleResolution','bundler','--types','bun,node','--typeRoots',env['UMF_TYPE_ROOTS'],'packages/postgresql/src/original-byte-custody.ts','packages/postgresql/src/canonical-wire-tree.ts','packages/postgresql/src/asserted-origin-map.ts','packages/postgresql/src/captured-origin-context.ts','packages/umf-bun/src/acceptance-input.ts','packages/umf-bun/src/canonical-report-handoff.ts','packages/umf-bun/src/catalog-captured-origin-basis.ts','packages/umf-bun/src/catalog-epoch-context-basis.ts','packages/umf-bun/src/catalog-admission-configuration-basis.ts','packages/umf-bun/src/catalog-asserted-origin-basis.ts','tests/original-byte-custody.test.ts']
typed=execute(typecmd,'typecheck.txt')
env['TRUSS_CANONICAL_BROWSER_EVIDENCE']=str(out/'browser.json');browser=execute(['bun','scripts/check-original-byte-browser.ts'],'browser.log')
container=None;cleanup=None;native=None;inventory=None;failure=None
try:
 name='truss-byte-custody-'+uuid.uuid4().hex
 created=subprocess.run(['docker','run','-d','--name',name,'-e','POSTGRES_USER=custody_fixture','-e','POSTGRES_PASSWORD=custody_fixture_only','-e','POSTGRES_DB=byte_custody','-p','127.0.0.1::5432','postgres:17.9'],capture_output=True,text=True,timeout=60)
 if created.returncode:raise RuntimeError('Owned container creation failed: '+created.stderr)
 container=created.stdout.strip()
 if len(container)!=64 or any(c not in '0123456789abcdef' for c in container):raise RuntimeError('Unexpected created container identity')
 inspected=json.loads(subprocess.check_output(['docker','inspect',container],text=True))[0]
 if inspected['Id']!=container:raise RuntimeError('Container identity mismatch')
 ports=inspected['NetworkSettings']['Ports']['5432/tcp']
 if len(ports)!=1 or ports[0]['HostIp']!='127.0.0.1':raise RuntimeError('Original loopback-only fixture required')
 inventory={'containerId':container,'imageId':inspected['Image'],'port':ports[0]['HostPort'],'scope':'Owned disposable codec fixture; no installed application schemas/roles'}
 ready=False
 for attempt in range(60):
  probe=subprocess.run(['docker','exec',container,'pg_isready','-U','custody_fixture','-d','byte_custody'],capture_output=True,text=True,timeout=5)
  if probe.returncode==0:ready=True;break
  time.sleep(0.25)
 if not ready:raise RuntimeError('Owned fixture readiness exhausted')
 env['TRUSS_OPERATION_TEST_URL']='postgres://custody_fixture:custody_fixture_only@127.0.0.1:'+ports[0]['HostPort']+'/byte_custody'
 env['TRUSS_CANONICAL_NATIVE_EVIDENCE']=str(out/'native.json');native=execute(['bun','scripts/check-canonical-report-native.ts'],'native.log')
except Exception as e:failure=str(e)
finally:
 if container:
  removed=subprocess.run(['docker','rm','-f',container],capture_output=True,text=True,timeout=30);cleanup={'containerId':container,'exitCode':removed.returncode,'stdout':removed.stdout.strip(),'stderr':removed.stderr.strip()}
  if removed.returncode and failure is None:failure='Owned exact-container cleanup failed'
 if failure:(out/'failure.json').write_text(json.dumps({'failure':failure,'nativeFixture':inventory,'cleanup':cleanup},indent=2)+'\n')
if failure:raise RuntimeError(failure)
if any(Path(p).read_bytes()!=b for p,b in preimages.items()):raise RuntimeError('Captured source changed')
with zipfile.ZipFile(out/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for i,(path,bytes_) in enumerate(preimages.items()):z.writestr(str(i)+'/'+Path(path).name,bytes_)
receipt={'status':'passed','sourcePreimages':[{'path':p,'archive':str(i)+'/'+Path(p).name,'sha256':sha(b)} for i,(p,b) in enumerate(preimages.items())],'hostCommand':['bun','test',*tests],'typecheckCommand':typecmd,'exitCodes':{'host':host.returncode,'typecheck':typed.returncode,'browser':browser.returncode,'native':native.returncode},'nativeFixture':inventory,'cleanup':cleanup,'premises':['Pristine trusted runtime intrinsics; caller-controlled source properties/iterators/species are not invoked','Structural shared-storage copy is not an atomic concurrent snapshot; original wire/profile handoffs require actual ordinary storage','Local Bun/Ajv/compiler/Playwright/dependencies and Docker image; not hermetic'],'scope':'Bounded original byte custody and temporary native canonical codec correspondence only; no semantic owner/issuer authority, complete report or backend security admission','acceptancePromoted':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'passed','sourcePins':len(preimages),'receipt':str(out/'receipt.json'),'cleanup':cleanup['exitCode']}))
