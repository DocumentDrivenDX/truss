"""Retain scoped original-owner inventory evidence; no backend admission claim."""
from pathlib import Path
import os, json, hashlib, zipfile, subprocess, uuid
root=Path.cwd(); out=root/'docs/helix/04-build/evidence/original-occurrence-inventory'/str(uuid.uuid4());out.mkdir(parents=True)
env=os.environ.copy()
roles=['TRUSS_UMF_PRODUCER','TRUSS_UMF_DECLARATION_PRODUCER','TRUSS_UMF_FIELD_ASSERTION_PRODUCER','TRUSS_UMF_SCALAR_TYPE_PRODUCER','TRUSS_UMF_RECORD_MEMBERS_PRODUCER','TRUSS_UMF_REFERENCE_LINKS_PRODUCER']
for role in roles:
 if role not in env:raise RuntimeError('Original producer environment required: '+role)
tests=['tests/catalog-input-preparation.test.ts','tests/catalog-core-assertion-identities.test.ts','tests/acceptance-json.test.ts','tests/source-occurrence-index.test.ts','tests/catalog-report-preparation.test.ts','tests/catalog-nullability-correspondence.test.ts','tests/catalog-field-shape-correspondence.test.ts','tests/catalog-scalar-type-correspondence.test.ts','tests/catalog-record-members-correspondence.test.ts','tests/catalog-reference-links-correspondence.test.ts']
paths=sorted(set([p for folder in ['packages/umf-bun/src','packages/postgresql/src'] for p in root.joinpath(folder).rglob('*.ts')]+[root/p for p in tests]+[Path(__file__).resolve()]))
for role in roles:
 paths += [Path(env[role])/name for name in ['producer.js','producer.ts','producer-manifest.json']]
paths += sorted(root.joinpath('docs/helix/02-design/contracts').rglob('*.json'))
paths += sorted(root.joinpath('docs/helix/02-design/contracts').rglob('*.d.ts'))
paths += sorted(root.glob('**/acceptance-outer-json-expected.proposal.json'))
paths += [root/'scripts/build-umf-runtime.ts',root/'package.json',root/'bun.lock',root/'docs/helix/03-test/report-wire-untrusted.fixture.json',Path('/Users/erik/Projects/umf/package.json')]
configCandidates=[root/'tsconfig.json',root/'bunfig.toml']
configAbsence=[str(p) for p in configCandidates if not p.exists()]
paths += [p for p in configCandidates if p.exists()]
preimages={str(p):p.read_bytes() for p in paths}
sha=lambda b:hashlib.sha256(b).hexdigest()
cmd=['bun','test',*tests]
run=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90)
(out/'host.txt').write_text(run.stdout+run.stderr)
compiler=env['UMF_TSC']; types=env['UMF_TYPE_ROOTS']
typecmd=['bun',compiler,'--ignoreConfig','--noEmit','--strict','--skipLibCheck','--target','ES2022','--module','ESNext','--moduleResolution','bundler','--types','bun,node','--typeRoots',types,'packages/umf-bun/src/catalog-original-occurrence-inventory.ts','tests/catalog-core-assertion-identities.test.ts','tests/catalog-nullability-correspondence.test.ts','tests/catalog-field-shape-correspondence.test.ts','tests/catalog-scalar-type-correspondence.test.ts','tests/catalog-record-members-correspondence.test.ts','tests/catalog-reference-links-correspondence.test.ts']
typed=subprocess.run(typecmd,env=env,capture_output=True,text=True,timeout=90)
(out/'typecheck.txt').write_text(typed.stdout+typed.stderr)
if run.returncode or typed.returncode:raise RuntimeError('Verification failed; retained output')
if any(Path(p).exists() for p in configAbsence):raise RuntimeError('Absent configuration appeared during verification')
if any(p.read_bytes()!=preimages[str(p)] for p in paths):raise RuntimeError('Source changed during verification')
with zipfile.ZipFile(out/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
 for i,(path,data) in enumerate(preimages.items()):z.writestr(str(i)+'/'+Path(path).name,data)
receipt={'status':'passed','command':cmd,'typecheckCommand':typecmd,'exitCodes':[run.returncode,typed.returncode],'sourcePreimages':[{ 'path':path,'archive':str(i)+'/'+Path(path).name,'sha256':sha(data)} for i,(path,data) in enumerate(preimages.items())],'sourceScope':'Selected full UMF Bun and PostgreSQL TypeScript directories, tests, runner and original local producer bundles/manifests, contract schemas/fixtures/declarations and selected outer JSON corpus','absentConfigurations':configAbsence,'runtimePremises':'Local Bun, compiler/ambient dependencies and package installation; not hermetic','semanticScope':'Complete original JSON values with partial core owner interpretation; unclassified values unavailable','acceptancePromoted':False,'nativeExecution':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':'passed','sourcePins':len(preimages),'receipt':str(out/'receipt.json')}))
