"""Implicit index identity allocation correspondence; no native index evidence."""
from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parents[5]
path=sys.argv[1] if len(sys.argv)>1 else 'docs/helix/02-design/models/truss-row-home-candidate.supporting-index-ids.proposal.json'
d=json.loads((root/path).read_text());source=root/d['sourceAllocationPath']
assert hashlib.sha256(source.read_bytes()).hexdigest()==d['sourceAllocationSha256']
base=json.loads(source.read_text());assert d['complete'] is False
expected={e['entryId']:e for e in base['entries'] if e['objectKind']=='constraint' and e.get('nativeKind') in {'CONSTR_PRIMARY','CONSTR_UNIQUE'}}
seen=set();ids={e['entryId'] for e in base['entries']}
for e in d['entries']:
 creator=expected[e['creatingConstraintId']]
 assert e['creatingConstraintId'] not in seen;seen.add(e['creatingConstraintId'])
 assert e['entryId'] not in ids;ids.add(e['entryId'])
 assert e['parentId']==creator['parentId']
 assert e['capturedModelLocator']==creator['capturedModelLocator']
 assert e['nativeBinding']=={'state':'unresolved'} and e['nativeName'] is None
 assert e['objectKind']=='supporting-index'
assert seen==set(expected)
receipt={'scope':'One authored index effect for each original PK/UNIQUE constraint; no FK-created index or native definition/name/installation qualification','allocationSha256':hashlib.sha256((root/path).read_bytes()).hexdigest(),'supportingIndexEffects':len(seen),'complete':False,'exactCreatorCorrespondence':True}
(root/(sys.argv[2] if len(sys.argv)>2 else 'docs/helix/04-build/evidence/design-audit/row-home-supporting-index-ids.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
