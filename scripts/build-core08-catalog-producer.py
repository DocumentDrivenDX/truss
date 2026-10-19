# SPDX-License-Identifier: MIT OR Apache-2.0
"""Build the separate original core0.8 catalog observer from committed UMF."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
repository=sys.argv[1];root=Path(__file__).resolve().parents[1]
target=root/'packages/python/src/truss/_umf_core08'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if repository=='--wrapper-only':
    retained=json.loads((target/'manifest.json').read_bytes())
    for name in ('producer.js','producer-manifest.json'):
        if sha(target/name)!=retained['files'][name]:raise ValueError('Retained original owner bundle required')
else:
    built=subprocess.run(['/opt/homebrew/bin/bun','scripts/build-umf-runtime.ts',repository,'core08-catalog'],cwd=root,text=True,capture_output=True,check=True,timeout=120)
    source=Path(built.stdout.strip())
    for name in ('producer.js','producer-manifest.json'):shutil.copyfile(source/name,target/name)
shutil.copytree(root/'packages/python/src/truss/_umf/licenses',target/'licenses',dirs_exist_ok=True)
subprocess.run(['/opt/homebrew/bin/bun','build','packages/umf-bun/src/python-preparation-core08.ts','--target=bun','--format=esm','--outfile='+str(target/'preparation.mjs')],cwd=root,check=True,timeout=120,stdout=sys.stderr)
(target/'acceptance-input-v0.1.schema.json').write_bytes((root/'docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json').read_bytes())
paths=[p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file() and p.name!='manifest.json']
manifest={'interfaceVersion':'truss-core08-catalog-producer/0.2.0','runtimeVersion':'1.4.2','owner':json.loads((target/'producer-manifest.json').read_text()),'files':{p:sha(target/p) for p in sorted(paths)},'scope':'Original core0.8 observation source only. No native ingress, report acceptance, migration, issuer authentication or protected execution.'}
(target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(root/'packages/python/src/truss/_core08_catalog_release.py').write_text('"""Generated original core0.8 producer pin; no native admission authority."""\nMANIFEST_SHA256 = '+repr(sha(target/'manifest.json'))+'\n')
print(json.dumps({'manifestSha256':sha(target/'manifest.json'),'ownerBundleSha256':manifest['owner']['bundleSha256'],'ownerRevision':manifest['owner']['revision']}))
