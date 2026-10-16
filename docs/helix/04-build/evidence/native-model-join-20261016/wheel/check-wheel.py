from pathlib import Path
import zipfile,json,hashlib,email
root=Path(__file__).parent;source=root/'source';installed=root/'installed';wheel=next((root/'wheel').glob('*.whl'));pins=json.loads((root/'source-before.json').read_text())
def meta(raw):return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
for name,pin in pins.items():assert meta((source/name).read_bytes())==pin,name
with zipfile.ZipFile(wheel) as z:
 expected={name.removeprefix('src/') for name in pins if name.startswith('src/truss/')};actual={name for name in z.namelist() if name.startswith('truss/') and not name.endswith('/')};assert actual==expected,(actual-expected,expected-actual)
 for name in sorted(expected):
  raw=z.read(name);assert meta(raw)==pins['src/'+name] and raw==(installed/name).read_bytes(),name
 metadata=email.message_from_bytes(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))));assert metadata['Version']=='0.0.38.dev0';requirements=metadata.get_all('Requires-Dist');assert any('weft-sql==0.4.36' in r and 'query' in r for r in requirements)
result={'wheel':str(wheel),'wheelSha256':meta(wheel.read_bytes())['sha256'],'version':metadata['Version'],'sourcePackageMembers':len(expected),'allSourceWheelInstalledBytesExact':True,'packagingInputUnchanged':True,'requirements':requirements,'scope':'Fresh local pure-Python package candidate; no publication, default compiler/cohort activation or new native authority claim.'};(root/'wheel-correspondence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
