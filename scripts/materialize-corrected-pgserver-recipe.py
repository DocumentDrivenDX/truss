#!/usr/bin/env python3
"""Materialize pinned native recipe bytes from original upstream; no build/publish."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if len(sys.argv)!=3:raise SystemExit('usage: materialize-corrected-pgserver-recipe.py SOURCE_CHECKOUT NEW_OUTPUT_DIRECTORY')
source,out=(Path(v).resolve() for v in sys.argv[1:])
if out.exists():raise SystemExit('Use a new output directory')
manifest=ROOT/'docs/helix/04-build/evidence/design-audit/pgserver-corrected-build-inputs.json'
original_manifest=manifest.read_bytes();inputs=json.loads(original_manifest)
def sha(value):return hashlib.sha256(value).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=source)
if git('rev-parse','HEAD').decode().strip()!=inputs['pgserverRevision']:raise ValueError('Original source revision drift')
original=git('show','HEAD:pgbuild/Makefile')
if sha(original)!=inputs['upstreamMakefileSha256']:raise ValueError('Original recipe drift')
selected=original
for old,new in inputs['makefileReplacements']:
 if old.encode() not in selected:raise ValueError('Replacement source missing')
 selected=selected.replace(old.encode(),new.encode())
if sha(selected)!=inputs['candidateMakefileSha256']:raise ValueError('Selected recipe drift')
if manifest.read_bytes()!=original_manifest:raise ValueError('Input drift')
out.mkdir();(out/'Makefile').write_bytes(selected)
receipt={'scope':'Exact corrected native recipe materialization from original pinned git blob; no native rebuild, packaging, installation or publication','sourceRevision':inputs['pgserverRevision'],'upstreamMakefileSha256':sha(original),'candidateMakefileSha256':sha(selected),'inputManifestSha256':sha(original_manifest),'producerSha256':sha(Path(__file__).read_bytes()),'nativeBuildPerformed':False,'defaultRuntimePublished':False}
(out/'recipe.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
