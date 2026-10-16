"""Read-only retained-byte audit; no source execution, SQL or authority claim."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parent
meta=lambda b:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
manifest=json.loads((root/'retention.json').read_text())
assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}==set(manifest)|{'retention.json'}
for name,pin in manifest.items():
 p=(root/name).resolve();assert p.is_relative_to(root);assert meta(p.read_bytes())==pin,name
reviews=json.loads((root/'reviews.json').read_text());artifacts=0
for name,receipt in reviews.items():
 archive=root/(name+'.zip');assert meta(archive.read_bytes())==receipt['archive']
 with zipfile.ZipFile(archive) as z:
  assert meta(z.read('manifest.json'))==receipt['manifest'];assert meta(z.read('review.json'))==receipt['review']
  pins=json.loads(z.read('manifest.json'));assert len(pins)==receipt['artifacts']
  for path,pin in pins.items():assert meta(z.read(path))==pin,(name,path)
  artifacts+=len(pins)
native_pins=0
for epoch in ('r1','r3','r4'):
 p=root/('native-'+epoch);pins=json.loads((p/'source-before.json').read_text())
 with zipfile.ZipFile(p/'source-inputs.zip') as z:
  for name,pin in pins.items():assert meta(z.read(name))==pin,(epoch,name)
 native_pins+=len(pins)
p=root/'wheel';receipt=json.loads((p/'wheel-correspondence.json').read_text());wheel=next(p.glob('*.whl'));assert meta(wheel.read_bytes())['sha256']==receipt['wheelSha256']
source=json.loads((p/'source-before.json').read_text());expected={n.removeprefix('src/') for n in source if n.startswith('src/truss/')}
with zipfile.ZipFile(wheel) as z:
 assert {n for n in z.namelist() if n.startswith('truss/') and not n.endswith('/')}==expected
 for name in expected:assert meta(z.read(name))==source['src/'+name],name
print(json.dumps({'passed':True,'retainedFiles':len(manifest),'completeReviewerArtifacts':artifacts,'nativeSourcePins':native_pins,'wheelMembers':len(expected),'scope':'Stored-byte audit only; not fresh tests, native execution, authority or acceptance promotion.'}))
