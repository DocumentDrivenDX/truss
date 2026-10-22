import argparse,hashlib,json,tarfile,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('dist',type=Path);a=p.parse_args()
root=Path('/Users/erik/Projects/truss');src=root/'packages/python/src';package=src/'truss'
expected={str(q.relative_to(src)):q.read_bytes() for q in package.rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.suffix!='.pyc'}
wheel=next(a.dist.glob('*.whl'));sdist=next(a.dist.glob('*.tar.gz'))
with zipfile.ZipFile(wheel) as z:
 actual={n:z.read(n) for n in z.namelist() if n.startswith('truss/') and not n.endswith('/')}
 assert actual==expected, {'missing':sorted(expected.keys()-actual.keys()),'extra':sorted(actual.keys()-expected.keys()),'changed':[n for n in actual.keys()&expected.keys() if actual[n]!=expected[n]]}
with tarfile.open(sdist) as t:
 actual={m.name.split('/src/',1)[1]:t.extractfile(m).read() for m in t.getmembers() if m.isfile() and '/src/truss/' in m.name}
 assert actual==expected, {'missing':sorted(expected.keys()-actual.keys()),'extra':sorted(actual.keys()-expected.keys()),'changed':[n for n in actual.keys()&expected.keys() if actual[n]!=expected[n]]}
record={'passed':True,'packageFiles':len(expected),'wheel':str(wheel),'wheelSha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'sdist':str(sdist),'sdistSha256':hashlib.sha256(sdist.read_bytes()).hexdigest(),'files':{n:hashlib.sha256(v).hexdigest() for n,v in sorted(expected.items())}}
(a.dist/'payload-verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='files'}))
