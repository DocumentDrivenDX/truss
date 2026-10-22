"""Verify v0.0.47 public assets. Args: asset-dir release-json tag-artifact-dir output-json. Run from the released checkout."""
from pathlib import Path
import hashlib,json,tarfile,zipfile,datetime,sys
root=Path(sys.argv[1])
metadata=json.loads(Path(sys.argv[2]).read_text())
source='6c9365c8be60b55602fe4e7bd4e45b4b5040ec74'
assert metadata['tagName']=='v0.0.47' and not metadata['isDraft'] and not metadata['isPrerelease']
entries={line.split()[1]:line.split()[0] for line in (root/'SHA256SUMS').read_text().splitlines()}
assert set(entries)=={p.name for p in root.iterdir() if p.is_file() and p.name!='SHA256SUMS'}
for name,digest in entries.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
tag_artifacts=Path(sys.argv[3])
for path in (tag_artifacts/'package').iterdir():assert path.read_bytes()==(root/path.name).read_bytes(),path.name
assert {a['name'] for a in metadata['assets']}==set(entries)|{'SHA256SUMS'}
pins=json.loads((root/'release-pins.json').read_text());assert pins['commit']==source and pins['tag']=='v0.0.47' and pins['version']=='0.0.47'
assert pins['runtimeSupport']=='latest-only' and pins['installationUpgradesSupported'] and not pins['pre010MigrationSupported']
q=json.loads((root/'migration-qualification.json').read_text());assert q['sourceCommit']==source and q['platform']=='linux' and q['passed'] and q['tests']==52 and q['skipped']==q['errors']==q['failures']==0
assert q['recipeSha256']==pins['migrationManifestSha256'] and q['targetManifestSha256']==pins['runtimeManifestSha256']
with tarfile.open(root/'migration-qualification-evidence.tar.gz') as t:
 evidence={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
 assert json.loads(evidence['qualification.json'])==q
 for name,data in evidence.items():assert data==(tag_artifacts/'qualification'/name).read_bytes(),name
 assert set(evidence)=={'qualification.json','source44-native-inventory.json','source44-original-evidence.json','source46-native-inventory.json','source46-original-evidence.json'}
src=Path('packages/python/src/truss');expected={p.relative_to(src).as_posix():p.read_bytes() for p in src.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
wheel=next(root.glob('*.whl'))
with zipfile.ZipFile(wheel) as z:actual={n[6:]:z.read(n) for n in z.namelist() if n.startswith('truss/') and not n.endswith('/')}
assert actual==expected
sdist=root/'truss_toolkit-0.0.47.tar.gz'
with tarfile.open(sdist) as t:actual={m.name.split('/src/truss/',1)[1]:t.extractfile(m).read() for m in t.getmembers() if m.isfile() and '/src/truss/' in m.name}
assert actual==expected
assert (root/'isolated-runtime-constraints.txt').read_bytes()==Path('packages/python/isolated-runtime-constraints.txt').read_bytes()
receipt={'observedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'release':metadata['url'],'publishedAt':metadata['publishedAt'],'tag':'v0.0.47','sourceCommit':source,'runtimeSupport':'latest-only','publicChecksumsVerified':True,'tagPackageArtifactsMatched':True,'tagOriginalEvidenceMatched':True,'assetsSha256':entries,'checksumFileSha256':hashlib.sha256((root/'SHA256SUMS').read_bytes()).hexdigest(),'runtimePayloadMatched':True,'runtimeFiles':len(expected),'nativeManifestSha256':pins['runtimeManifestSha256'],'migrationManifestSha256':pins['migrationManifestSha256'],'linuxQualification':q,'originalNativeEvidenceSha256':{name:hashlib.sha256(data).hexdigest() for name,data in evidence.items()},'scope':'Public GitHub release assets and exact installed Linux migration qualification; separate clean installed macOS test follows'}
Path(sys.argv[4]).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'release':receipt['release'],'sourceCommit':source,'assetsVerified':len(entries),'runtimeFiles':len(expected),'linuxMigrationTests':q['tests'],'passed':True}))
