"""Published fragment byte/content-hash checks; not a canonical projection implementation."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parents[3]/'02-design/contracts/bindings/bootstrap-projection-v0.1.vectors.json'
a=json.loads(p.read_text());assert a['profile']=='truss-bootstrap-inventory-basis/0.1.0' and a['encoding']=='truss-canonical/0.1.0'
assert len(a['vectors'])==9 and a['equalPairs']==[[0,1]] and a['distinctPairs']==[[0,2],[3,4],[5,6],[7,8]]
raws=[]
for v in a['vectors']:
 raw=bytes.fromhex(v['canonicalUtf8Hex']);assert raw==v['canonicalUtf8'].encode('utf-8');json.loads(raw);assert hashlib.sha256(raw).hexdigest()==v['contentSha256'];raws.append(raw)
for x,y in a['equalPairs']: assert raws[x]==raws[y]
for x,y in a['distinctPairs']: assert raws[x]!=raws[y]
result={'scope':'nine manually authored fragment UTF-8/content hashes and one equal/four distinct pair checks only; no projection, complete inventory, native semantics or canonicalizer qualification','cases':9,'pairChecks':5,'status':'pass','vectorsSha256':hashlib.sha256(p.read_bytes()).hexdigest()}
Path(__file__).with_name('bootstrap-projection-vectors-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'cases':9,'pairChecks':5,'status':'pass'}))
