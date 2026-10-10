"""Original source/target identity only; no native initialization admission."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[5];path='docs/helix/02-design/models/truss-row-home-capacity.initialization-ids.proposal.json'
sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
d=json.loads((root/path).read_text());assert d['complete'] is False and sha(d['source'])==d['sourceSha256']
pin=d['parentAllocation'];assert sha(pin['path'])==pin['sha256'];parents=json.loads((root/pin['path']).read_text())
assert len(d['entries'])==1;e=d['entries'][0]
parent=next(x for x in parents['entries'] if x['entryId']==e['parentId']);assert parent['objectKind']=='table' and parent['nativeName']=='row_home_capacity'
loc=e['capturedModelLocator'];assert sha(loc['modelPath'])==loc['modelSha256'];n=json.loads((root/loc['modelPath']).read_text())
for part in loc['jsonPointer'].strip('/').split('/'):n=n[int(part)] if isinstance(n,list) else n[part]
assert n==e['originalNativeNode'] and n['members']['relation']['members']['relname']['value']==parent['nativeName']
assert n['members']['relation']['members']['schemaname']['value']=='truss'
assert e['nativeBinding']=={'state':'unresolved'} and e['mode']=='fresh-empty-scope-only'
assert e['parameterMeanings']==[{'position':'1','meaning':'original-admitted-layout-definition-bytes','nativeCarrier':'bytea'},{'position':'2','meaning':'original-admitted-touch-retention-resource-profile-bytes','nativeCarrier':'bytea'}]
receipt={'scope':'Authored initializer identity/original retained INSERT node/target allocation only; native parameter/default/empty-scope/privilege/counter admission unresolved','allocationSha256':sha(path),'initializationEntries':1,'exactOriginalTargetCorrespondence':True,'physicalCoverageComplete':False}
(root/'docs/helix/04-build/evidence/design-audit/row-home-capacity-initialization-id.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
