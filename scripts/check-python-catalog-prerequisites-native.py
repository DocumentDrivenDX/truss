# SPDX-License-Identifier: MIT OR Apache-2.0
import hashlib,json,os,subprocess,sys,uuid,zipfile,importlib.metadata,shutil,resource
from pathlib import Path
root=Path.cwd()
run_id=str(uuid.uuid4());out=root/'docs/helix/04-build/evidence/python-catalog-prerequisites'/run_id
out.mkdir(parents=True)
inputs={}
def retain(path):
 if path.is_file() and '__pycache__' not in path.parts:inputs[str(path.relative_to(root))]=path.read_bytes()
for folder in ['packages/python/src/truss','packages/python/tests','packages/postgresql/native','docs/helix/02-design/contracts']:
 for p in (root/folder).rglob('*'):
  if p.is_file() and p.suffix in ['.py','.json','.sql','.zip','.js','.ts']:retain(p)
for p in ['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql','docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql','docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql','scripts/check-module-boundaries.py','scripts/extract-feed-prerequisite-statements.ts','scripts/compose-catalog-wide-report-candidate.ts','scripts/check-python-catalog-prerequisites-native.py']:
 retain(root/p)
sha=lambda b:hashlib.sha256(b).hexdigest()
pins={p:sha(b) for p,b in inputs.items()}
external={}
for package in ['psycopg','psycopg-binary','typing-extensions','jsonschema','jsonschema-specifications','attrs','referencing','rpds-py','pg8000','scramp','asn1crypto','python-dateutil','six']:
 distribution=importlib.metadata.distribution(package)
 for item in distribution.files:
  path=Path(distribution.locate_file(item)).resolve()
  if path.is_file() and (path.suffix in ['.py','.so','.dylib'] or path.name in ['METADATA','RECORD']):external[str(path)]=path.read_bytes()
for path in [Path(sys.executable).resolve(),Path(shutil.which('bun')).resolve()]:external[str(path)]=path.read_bytes()
external_pins={p:sha(raw) for p,raw in external.items()}
with zipfile.ZipFile(out/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p,b in inputs.items():z.writestr(p,b)
 for p,b in external.items():z.writestr('external/'+p.lstrip('/'),b)
pgbin=Path(os.environ['TRUSS_CENSUS_POSTGRES_BIN'])
binaries={str(p):sha(p.read_bytes()) for p in pgbin.parent.rglob('*') if p.is_file()}
env=dict(os.environ,TRUSS_CENSUS_POSTGRES_BIN=str(pgbin),PYTHONPATH='packages/python/src:packages/python/tests',TRUSS_PREREQUISITE_EVIDENCE_DIR=str(out))
command=[sys.executable,'-m','unittest','test_catalog_prerequisites_psycopg_native.PrerequisitePsycopgNativeTests','-v']
result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,timeout=240)
(out/'native.log').write_text(result.stdout+result.stderr)
boundary=subprocess.run(['/opt/homebrew/bin/python3.14','scripts/check-module-boundaries.py'],cwd=root,capture_output=True,text=True,timeout=60)
(out/'boundaries.log').write_text(boundary.stdout+boundary.stderr)
cleanup=json.loads((out/'cleanup.json').read_text()) if (out/'cleanup.json').exists() else None
receipt={'run':run_id,'scope':'Administrative single-original fresh catalog report/revision/document/configuration pending registration through supported psycopg. No public installation, head publication, finalization, accepted catalog, commit, ordinary-person or default-timeout qualification.', 'command':command,'native_exit':result.returncode,'boundary_exit':boundary.returncode,'source_sha256':pins,'native_binary_sha256':binaries,'external_file_sha256':external_pins,'external_files_unchanged':all(sha(Path(p).read_bytes())==h for p,h in external_pins.items()),'child_process_peak_rss':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'peak_rss_units':'bytes on this macOS host; child-process observation, not whole native operation qualification','dependencies':{p:importlib.metadata.version(p) for p in ['psycopg','psycopg-binary','jsonschema','pg8000']},'source_unchanged':all(sha((root/p).read_bytes())==h for p,h in pins.items()),'cleanup':cleanup,'timeouts_ms':{'caller_statement':10000,'toolkit_statement':8000,'operation':15000},'evidence_sha256':{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'run':run_id,'native_exit':result.returncode,'boundary_exit':boundary.returncode,'source_unchanged':receipt['source_unchanged'],'cleanup':cleanup,'source_count':len(pins),'native_files':len(binaries)}))
if result.returncode or boundary.returncode or not receipt['source_unchanged'] or not receipt['external_files_unchanged'] or cleanup is None or cleanup.get('stop')!=0 or cleanup.get('status')!=3 or not cleanup.get('socket_absent'):sys.exit(1)
