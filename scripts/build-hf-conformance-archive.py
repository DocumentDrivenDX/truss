#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Archive the exact independent conformance producers; no old runtime is bundled."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
corpus=ROOT/'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json';profile=json.loads(corpus.read_bytes());paths=[ROOT/name for name in profile['producers']]+[corpus,ROOT/'scripts/run-hf-conformance.py']
paths += [p for p in (ROOT/'packages/python/tests/fixtures').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
paths += [ROOT/'packages/python'/name for name in ('LICENSE.md','LICENSE-MIT','LICENSE-APACHE')]
archive_manifest={'profile':profile['profile'],'toolkitVersion':profile['toolkitVersion'],'nativeManifestSha256':profile['nativeManifestSha256'],'compilerVersion':profile['compilerVersion'],'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))},'scope':'Independent synthetic native fixture corpus and runner, not a runtime distribution or permission to modify application databases'}
a.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
 def write(name,raw):
  info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
  z.writestr(info,raw)
 for path in sorted(set(paths)):write(str(path.relative_to(ROOT)),path.read_bytes())
 write('conformance-manifest.json',json.dumps(archive_manifest,indent=2)+'\n')
 write('README.md',f"Install the exact checksum-verified Truss{profile['toolkitVersion']} native/local/query dependency cohort. Unzip this archive in a new directory. Run `python scripts/run-hf-conformance.py --installed-package --output qualification.json`. Tests create and remove isolated local PostgreSQL clusters with synthetic data. No application database connection is accepted. Administrative fixture controls are explicit, not supported public mutation APIs. Runtime migrations are separately qualified by the release lineage gate.\n")
print(json.dumps({'archive':str(a.output),'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'files':len(archive_manifest['files']),'cases':len(profile['cases'])}))
