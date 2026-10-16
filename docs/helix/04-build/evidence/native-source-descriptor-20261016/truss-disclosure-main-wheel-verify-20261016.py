"""Current integration wheel correspondence; explicit local dev cohort, no SQL."""
from pathlib import Path,PurePosixPath
from hashlib import sha256
from email.parser import BytesParser
import zipfile,json,sys,argparse
p=argparse.ArgumentParser()
for name in ['source-root','wheel','weft-root','installed','fixture','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();source=a.source_root.resolve();installed=a.installed.resolve();installed.mkdir(exist_ok=False);verified={}
with zipfile.ZipFile(a.wheel) as z:
 names=z.namelist();assert len(names)==len(set(names))
 for name in names:
  pure=PurePosixPath(name);assert not pure.is_absolute() and '..' not in pure.parts
  if name.endswith('/'):continue
  data=z.read(name);target=installed.joinpath(*pure.parts);assert target.resolve().is_relative_to(installed)
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  if name.startswith('truss/'):
   assert (source/name).read_bytes()==data,name;verified[name]=sha256(data).hexdigest()
 metadata_name=next(n for n in names if n.endswith('.dist-info/METADATA'));metadata=BytesParser().parsebytes(z.read(metadata_name));requirements=metadata.get_all('Requires-Dist')
 assert any('weft-sql==0.4.36' in r and 'query' in r for r in requirements)
 for path in (source/'truss/_current_disclosure_owner').rglob('*'):
  if path.is_file():assert str(path.relative_to(source)) in names
sys.path.insert(0,str(installed));sys.path.insert(1,str(a.weft_root.resolve()))
import truss,weft.weft as native
from truss import _current_disclosure_originals as originals,_current_query_originals as legacy
assert Path(truss.__file__).resolve()==installed/'truss/__init__.py'
assert sha256(Path(native.__file__).read_bytes()).hexdigest()=='a94439b3949c6db574ded8d95d9b81b23e128b0cbb7570edff65228d3737c402'
fixture=json.loads(a.fixture.read_bytes());opaque=json.dumps(fixture['opaqueSources'],separators=(',',':')).encode();selected=truss.prepare_current_disclosure_originals(opaque)
assert originals._actual_disclosure_consumer()['umfRevision']=='206951ff20d766874b9af7d29fdf8027c3bab499'
try:legacy._actual_consumer()
except ValueError:pass
else:raise AssertionError('Old ABI2 cohort selected candidate presence module')
for name,h in verified.items():assert sha256((source/name).read_bytes()).hexdigest()==h and sha256((installed/name).read_bytes()).hexdigest()==h
result={'status':'passed','python':sys.version,'wheelSha256':sha256(a.wheel.read_bytes()).hexdigest(),'sourceMembers':verified,'members':len(verified),'newOwnerAssets':sum(n.startswith('truss/_current_disclosure_owner/') for n in verified),'consumer':originals._actual_disclosure_consumer(),'requiresDist':requirements,'scope':'Fresh isolated integration wheel exactly corresponds to current source, retains original owner notices, selects exact local ARM presence cohort and refuses it in legacy ABI2. No SQL, native binding/current authority/release or backend promotion.'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'members':result['members'],'assets':result['newOwnerAssets'],'wheelSha256':result['wheelSha256']}))
