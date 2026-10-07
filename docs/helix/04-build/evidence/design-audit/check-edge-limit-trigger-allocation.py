"""Original three observer declaration identities/captured nodes only, no native qualification."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[5]
PATH=ROOT/'docs/helix/02-design/models/truss-edge-limit-triggers.physical-ids.proposal.json'
a=json.loads(PATH.read_text());assert a['complete'] is False and len(a['entries'])==3
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
for s in a['sources']:assert sha(s['source'])==s['sourceSha256'] and sha(s['model'])==s['modelSha256']
pin=a['parentAllocationPins'][0];assert sha(pin['path'])==pin['sha256'];parents={e['entryId']:e for e in json.loads((ROOT/pin['path']).read_text())['entries'] if e['objectKind']=='table'}
expected={'edge_limit_edge_observe':('edge','edge_limit_observe'),'edge_limit_marker_observe':('edge_limit','edge_limit_observe'),'edge_limit_catalog_observe':('rel_def','edge_limit_catalog_observe')}
seen=set()
for e in a['entries']:
 assert e['nativeName'] in expected and e['nativeName'] not in seen;seen.add(e['nativeName']);assert e['entryId']=='truss.edge-limit.trigger.'+e['nativeName'] and e['nativeBinding']=={'state':'unresolved'}
 loc=e['capturedModelLocator'];assert sha(loc['modelPath'])==loc['modelSha256'];node=json.loads((ROOT/loc['modelPath']).read_text())
 for part in loc['jsonPointer'].strip('/').split('/'):node=node[int(part)] if isinstance(node,list) else node[part]
 assert node==e['originalNativeNode'];m=node['members'];parent,fn=expected[e['nativeName']]
 assert parents[e['parentId']]['nativeIdentity']=={'schema':'truss','name':parent}
 assert m['relation']['members']['schemaname']['value']=='truss' and m['relation']['members']['relname']['value']==parent
 assert m['trigname']['value']==e['nativeName'] and [x['members']['String']['members']['sval']['value'] for x in m['funcname']['items']]==['truss',fn]
 assert m['row']=={'kind':'boolean','value':True} and m['events']=={'kind':'number','value':'28'}
 assert not any(k in m for k in ['whenClause','columns','args','transitionRels','isconstraint','before','deferrable','initdeferred'])
assert seen==set(expected)
result={'scope':'three fixed original observer identities/parent/function/all-row-event source nodes and pinned UMF archive only; omitted AST defaults follow selected owner source, not actual installed native event/enablement/role/body proof','status':'pass','entries':3,'allocationSha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),'nativeBinding':'unresolved'}
Path(__file__).with_name('edge-limit-trigger-allocation-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'entries':3,'status':'pass','nativeBinding':'unresolved'}))
