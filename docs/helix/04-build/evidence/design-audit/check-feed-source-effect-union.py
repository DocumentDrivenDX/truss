"""Explicit source identity union; reference edges are not installed objects."""
import copy,collections,hashlib,json
from pathlib import Path
root=Path('docs/helix/02-design/models')
files=['truss-feed-native-layout.physical-ids.proposal.json','truss-feed-native-layout.derived-effects.proposal.json','truss-feed-current-union-trigger-effects.proposal.json']
expected=[{'table':4,'column':47,'constraint':17},{'expected_supporting_index':5,'source_foreign_key_reference':3},{'trigger':4,'expected_trigger_constraint':4}]
def require(ok,msg):
 if not ok:raise ValueError(msg)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs=[{'path':str(root/f),'sha256':sha(root/f),'allocation':json.loads((root/f).read_text())} for f in files]
def verify(xs):
 require([x['path'] for x in xs]==[str(root/f) for f in files],'explicit source allocation membership')
 allentries=[]
 for x,kinds in zip(xs,expected):
  r=x['allocation'];require(r['complete'] is False,'no native complete claim');require(dict(collections.Counter(e['objectKind'] for e in r['entries']))==kinds,'independent per-family identity kinds/counts');allentries.extend(r['entries'])
 ids={e['entryId']:e for e in allentries};require(len(ids)==84,'distinct original source identities');require(sum(e['objectKind']!='source_foreign_key_reference' for e in allentries)==81,'81 authored/expected physical identities plus 3 source edges')
 for e in allentries:
  require(e['nativeBinding']=={'state':'unresolved'},'unresolved original binding')
  for key in ['parentId','creatorId']:
   if key in e:require(e[key] in ids,'original parent/creator union closure')
  if e['objectKind']!='table':require(ids[e['parentId']]['objectKind']=='table','original physical parent is a table')
 return allentries
entries=verify(inputs);controls=[]
for label,mutate in [('missing allocation family',lambda x:x.pop()),('reference promoted to physical constraint',lambda x:next(e for e in x[1]['allocation']['entries'] if e['objectKind']=='source_foreign_key_reference').update(objectKind='constraint')),('reused trigger identity',lambda x:x[2]['allocation']['entries'][0].update(entryId=x[0]['allocation']['entries'][0]['entryId'])),('outside creator',lambda x:x[2]['allocation']['entries'][1].update(creatorId='unallocated')),('unqualified complete inflation',lambda x:x[0]['allocation'].update(complete=True))]:
 x=copy.deepcopy(inputs);mutate(x)
 try:verify(x)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise ValueError('accepted '+label)
r={'scope':'Explicit union of three authored source allocations, per-kind quantities and parent/creator identity closure only; not native object counts, semantic node equivalence, source regeneration, installation or enforcement','allocationPins':[{'path':x['path'],'sha256':x['sha256']} for x in inputs],'authoredOrExpectedPhysicalIdentities':81,'sourceReferenceEdges':3,'totalIdentities':84,'counts':dict(collections.Counter(e['objectKind'] for e in entries)),'controls':controls,'nativeExecution':False,'installable':False,'complete':False}
Path('docs/helix/04-build/evidence/design-audit/feed-source-effect-union.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'physicalIdentities':81,'sourceEdges':3,'refusals':len(controls),'installable':False}))
