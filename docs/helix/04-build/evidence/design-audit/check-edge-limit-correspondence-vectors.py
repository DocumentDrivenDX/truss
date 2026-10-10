"""Independent finite design-case oracle; no native/production guard implementation."""
from pathlib import Path
from collections import Counter
import hashlib,json
PATH=Path(__file__).resolve().parents[3]/'02-design/contracts/bindings/edge-limit-correspondence-v0.1.vectors.json'
a=json.loads(PATH.read_text());assert a['profile']=='truss-edge-limit-correspondence/0.1.0' and len(a['vectors'])==11
names=set();outcomes=[]
def row(m):return tuple(m[k] for k in ('relationshipId','side','endpointId','edgeId'))
for c in a['vectors']:
 assert c['name'] not in names;names.add(c['name']);defs={d['relationshipId']:d for d in c['definitions']};assert len(defs)==len(c['definitions']);required=[];missing=False
 for e in c['edges']:
  d=defs.get(e['relationshipId'])
  if d is None:missing=True;continue
  if d['targetMax']=='1':required.append((e['relationshipId'],'s',e['sourceId'],e['id']))
  if d['sourceMax']=='1':required.append((e['relationshipId'],'t',e['targetId'],e['id']))
 assert Counter(required)==Counter(row(m) for m in c['expectedRequiredMarkers'])
 keys=Counter(m[:3] for m in required)
 outcome='definition_unavailable' if missing else 'required_key_conflict' if any(v>1 for v in keys.values()) else 'marker_mismatch' if Counter(required)!=Counter(row(m) for m in c['actualMarkers']) else 'correspondence'
 if 'separateLargerBoundExpected' in c:
  counts=Counter((e['relationshipId'],e['sourceId']) for e in c['edges'])
  violation=any(defs[rel]['targetMax'] is not None and int(defs[rel]['targetMax'])>1 and count>int(defs[rel]['targetMax']) for (rel,_),count in counts.items())
  assert violation and c['separateLargerBoundExpected']=='violation' and outcome=='correspondence'
 assert outcome==c['expectedOutcome'],c['name'];outcomes.append({'case':c['name'],'matchesIndependentlyAuthoredExpectation':True,'outcome':outcome})
result={'scope':'eleven finite independently authored maximum-one derivation/multiset cases checked by Python oracle only; no Truss/native/privilege/cut/resource/support qualification','status':'pass','outcomes':outcomes,'vectorsSha256':hashlib.sha256(PATH.read_bytes()).hexdigest()}
Path(__file__).with_name('edge-limit-correspondence-vectors-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'cases':11,'status':'pass'}))
