"""Original source identity correspondence only; no native/generation qualification."""
import json, hashlib, sys
from pathlib import Path
root=Path(__file__).resolve().parents[5]
path=sys.argv[1] if len(sys.argv)>1 else 'docs/helix/02-design/models/truss-row-home-candidate.physical-ids.proposal.json'
d=json.loads((root/path).read_text());assert d['complete'] is False
sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
models={};expected=set()
for source in d['sources']:
 assert sha(source['source'])==source['sourceSha256']
 assert sha(source['model'])==source['modelSha256']
 model=json.loads((root/source['model']).read_text());models[source['model']]=model
 def walk(n,p=''):
  if isinstance(n,dict):
   for k,v in n.items():
    target=p+'/'+k
    if k in {'CreateStmt','CreateSeqStmt','IndexStmt','ColumnDef','CreateTrigStmt'} or (k=='Constraint' and v['members']['contype']['value'] in {'CONSTR_PRIMARY','CONSTR_UNIQUE','CONSTR_FOREIGN','CONSTR_CHECK'}):expected.add((source['model'],target))
    walk(v,target)
  elif isinstance(n,list):
   for i,v in enumerate(n):walk(v,p+'/'+str(i))
 walk(model)
seen=set();observed=set();counts={}
baseline=json.loads((root/'docs/helix/02-design/models/truss-layout-0.2.physical-ids.draft.json').read_text())
parents={e['entryId'] for e in baseline['entries'] if e['objectKind']=='table'}|{e['entryId'] for e in d['entries'] if e['objectKind']=='table'}
parent_entries={}
for pin in d.get('parentAllocationPins',[]):
 assert sha(pin['path'])==pin['sha256']
 allocation=json.loads((root/pin['path']).read_text())
 for parent in allocation['entries']:
  if parent['objectKind']=='table':parents.add(parent['entryId']);parent_entries[parent['entryId']]=parent
for e in d['entries']:
 assert e['entryId'] not in seen;seen.add(e['entryId'])
 assert e['nativeBinding']=={'state':'unresolved'}
 if 'parentId' in e:assert e['parentId'] in parents
 loc=e['capturedModelLocator'];assert sha(loc['modelPath'])==loc['modelSha256'];n=models[loc['modelPath']]
 for c in loc['jsonPointer'].strip('/').split('/'):n=n[int(c)] if isinstance(n,list) else n[c]
 assert n==e['originalNativeNode']
 if e['objectKind']=='trigger':
  assert n['members']['trigname']['value']==e['nativeName']
  assert n['members']['relation']['members']['relname']['value']==parent_entries[e['parentId']]['nativeName']
  assert n['members']['relation']['members']['schemaname']['value']=='truss'
 key=(loc['modelPath'],loc['jsonPointer']);assert key not in observed;observed.add(key)
 counts[e['objectKind']]=counts.get(e['objectKind'],0)+1
assert observed==expected, (expected-observed,observed-expected)
receipt={'scope':d['scope'],'allocationSha256':sha(path),'entries':len(seen),'counts':counts,'complete':False,'exactCapturedNodes':True,'selectedSourceCoverage':True}
(root/(sys.argv[2] if len(sys.argv)>2 else 'docs/helix/04-build/evidence/design-audit/row-home-physical-ids.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
