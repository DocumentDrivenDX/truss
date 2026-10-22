"""Verify public Truss0.0.48 against its exact source and original hosted artifacts."""
import argparse,datetime,hashlib,json,subprocess,tarfile,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--source',required=True);p.add_argument('--repository',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.repository,text=True).strip()==a.source
metadata=json.loads(a.metadata.read_bytes());assert metadata['tagName']=='v0.0.48' and not metadata['isDraft'] and not metadata['isPrerelease']
checks={line.split()[1]:line.split()[0] for line in (a.assets/'SHA256SUMS').read_text().splitlines()}
assert set(checks)=={f.name for f in a.assets.iterdir() if f.is_file() and f.name!='SHA256SUMS'}
assert {f['name'] for f in metadata['assets']}==set(checks)|{'SHA256SUMS'}
for name,digest in checks.items():assert sha((a.assets/name).read_bytes())==digest,name
package_names={'truss_toolkit-0.0.48-py3-none-any.whl','truss_toolkit-0.0.48.tar.gz','truss-hf-conformance-0.0.48.zip','isolated-runtime-constraints.txt'}
original_package=a.artifacts/'python-package'
assert {f.name for f in original_package.iterdir()}==package_names,'Original package-job artifact set is incomplete or unexpected'
for name in sorted(package_names):assert (original_package/name).read_bytes()==(a.assets/name).read_bytes(),name
pins=json.loads((a.assets/'release-pins.json').read_bytes());assert pins['commit']==a.source and pins['tag']=='v0.0.48' and pins['version']=='0.0.48'
assert pins['runtimeSupport']=='latest-only' and pins['installationUpgradesSupported'] and not pins['pre010MigrationSupported']
source=a.repository/'packages/python/src/truss'
assert pins['runtimeManifestSha256']==sha((source/'_catalog_runtime/manifest.json').read_bytes())
assert pins['migrationManifestSha256']==sha((source/'_migrations/manifest.json').read_bytes())
q=json.loads((a.assets/'migration-qualification.json').read_bytes())
assert q['passed'] and q['tests']==80 and q['failures']==q['errors']==q['skipped']==0
assert q['sourceCommit']==a.source and q['platform']=='linux' and q['package']=='0.0.48'
assert q['recipeSha256']==pins['migrationManifestSha256'] and q['targetManifestSha256']==pins['runtimeManifestSha256']
assert set(q['originalWheels'])=={'source44','source46','source47'} and q['previousMigrationRelease']=='v0.0.47'
with tarfile.open(a.assets/'migration-qualification-evidence.tar.gz') as archive:
 migration={f.name:archive.extractfile(f).read() for f in archive.getmembers() if f.isfile()}
assert json.loads(migration['qualification.json'])==q
original=a.artifacts/'runtime-migration-qualification-ubuntu-24.04'
assert set(migration)=={f.name for f in original.iterdir() if f.is_file()}
for name,raw in migration.items():assert raw==(original/name).read_bytes(),name
for label in ('source44','source46','source47'):
 assert label+'-native-inventory.json' in migration and label+'-original-evidence.json' in migration
hf=json.loads((a.assets/'hf-conformance-qualification.json').read_bytes())
assert hf['passed'] and hf['tests']==62 and hf['failures']==hf['errors']==hf['skipped']==0 and hf['sourceCommit']==a.source
assert (a.assets/'hf-conformance-qualification.json').read_bytes()==(a.artifacts/'hf-conformance-qualification-ubuntu-24.04/qualification.json').read_bytes()
assert hf['compilerSourceRevision']==pins['weftSourceRevision'] and hf['compilerNativeModuleSha256']==pins['weftNativeModuleSha256']
assert hf['corpusSha256']==pins['hfConformanceCorpusSha256'] and hf['nativeManifestSha256']==pins['runtimeManifestSha256']
corpus_path='docs/helix/03-test/fixtures/hohfeld-followup-0.1.json'
assert hf['corpusSha256']==sha((a.repository/corpus_path).read_bytes())
with zipfile.ZipFile(a.assets/pins['hfConformanceArchive']) as archive:
 manifest=json.loads(archive.read('conformance-manifest.json'))
 assert hf['corpusSha256']==sha(archive.read(corpus_path))
 for name,digest in manifest['files'].items():assert sha(archive.read(name))==digest,name
expected={f.relative_to(source).as_posix():f.read_bytes() for f in source.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
with zipfile.ZipFile(next(a.assets.glob('*.whl'))) as archive:
 actual={n.removeprefix('truss/'):archive.read(n) for n in archive.namelist() if n.startswith('truss/') and not n.endswith('/')}
assert actual==expected
with tarfile.open(a.assets/'truss_toolkit-0.0.48.tar.gz') as archive:
 actual={f.name.split('/src/truss/',1)[1]:archive.extractfile(f).read() for f in archive.getmembers() if f.isfile() and '/src/truss/' in f.name}
assert actual==expected
assert (a.assets/'isolated-runtime-constraints.txt').read_bytes()==(a.repository/'packages/python/isolated-runtime-constraints.txt').read_bytes()
receipt={'passed':True,'observedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'release':metadata['url'],'sourceCommit':a.source,'assetsSha256':checks,'runtimeFiles':len(expected),'runtimeSupport':'latest-only','migrationTests':q['tests'],'independentTests':hf['tests'],'compilerSource':hf['compilerSourceRevision'],'compilerModuleSha256':hf['compilerNativeModuleSha256'],'originalHostedEvidenceMatched':True,'conformanceManifestFiles':len(manifest['files']),'scope':'Public assets, source payloads and original Linux workflow evidence; independent clean macOS native/public quickstart qualification follows'}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='assetsSha256'}))
