"""Check a locally built wheel against original native SQL and module bytes."""
from pathlib import Path
import hashlib,json,sys,zipfile
root=Path(__file__).resolve().parents[5]
wheel=Path(sys.argv[1]);receipt=Path(sys.argv[2]);extract=Path(sys.argv[3]);extract.mkdir(exist_ok=True)
with zipfile.ZipFile(wheel) as archive:
 archive.extractall(extract)
 raw=archive.read('truss/_security_source_epoch/manifest.json');manifest=json.loads(raw);controls=[]
 for name,digest in manifest['sources'].items():
  packaged=archive.read('truss/_security_source_epoch/'+name)
  assert packaged==(root/'packages/postgresql/native'/('source-epoch-'+name)).read_bytes()
  assert hashlib.sha256(packaged).hexdigest()==digest
  controls.append({'source':name,'sha256':digest,'originalNativeBytesMatch':True})
 module=archive.read('truss/_security_source_epoch_installation.py')
 assert module==(root/'packages/python/src/truss/_security_source_epoch_installation.py').read_bytes()
receipt.write_text(json.dumps({'wheel':wheel.name,'wheelSha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'installerSha256':hashlib.sha256(module).hexdigest(),'manifestSha256':hashlib.sha256(raw).hexdigest(),'sources':controls,'status':'pass','scope':'Local built wheel bytes and repository-native SQL correspondence; not clean installed consumer qualification'},indent=2)+'\n')
