from pathlib import Path,PurePosixPath
import zipfile,hashlib,json
root=Path('/private/tmp/truss-disclosure-main-integration-20261016/packages/python/src');wheel=next(Path('/private/tmp/truss-native-observer-wheel-20261016').glob('*.whl'));target=Path('/private/tmp/truss-native-observer-installed-20261016');target.mkdir()
with zipfile.ZipFile(wheel) as z:
 names=z.namelist();assert len(names)==len(set(names));pins={}
 for n in names:
  p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts
  if n.endswith('/'):continue
  b=z.read(n);dest=target/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
  if n.startswith('truss/'):
   assert b==(root/n).read_bytes(),n;pins[n]=hashlib.sha256(b).hexdigest()
 expected={str(p.relative_to(root)) for p in (root/'truss').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 assert set(pins)==expected,(set(pins)^expected)
report={'status':'passed','baseline':'31ce4449010051832398e50130582acd9999c7e9','members':len(pins),'wheelSha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'sourcePins':pins,'scope':'Fresh main-baseline wheel with exact observer overlay; source/package correspondence only. Native receipt retains its separate native71 overlay; no native authority or acceptance promotion.'}
Path('/private/tmp/truss-native-observer-wheel-check-20261016.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='sourcePins'}))
