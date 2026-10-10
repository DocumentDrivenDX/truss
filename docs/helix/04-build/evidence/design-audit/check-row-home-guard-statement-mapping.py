"""Authored row-home identity to original statement source bridge, no native effects proof."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[5]
load=lambda p:json.loads((root/p).read_text())
sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
include_unfinished_unique='--include-unfinished-unique' in sys.argv
include_edge_limits=include_unfinished_unique or '--include-edge-limits' in sys.argv
include_guards=include_edge_limits or '--include-guards' in sys.argv
include_initialization=include_guards or '--include-initialization' in sys.argv
include_capacity=include_initialization or '--include-capacity' in sys.argv
composition_path='docs/helix/04-build/evidence/design-audit/'+('row-home-unfinished-unique-guard-statement-composition.json' if include_unfinished_unique else 'row-home-edge-limit-guard-statement-composition.json' if include_edge_limits else 'row-home-native-guard-statement-composition.json' if include_guards else 'row-home-initialized-statement-composition.json' if include_initialization else 'row-home-protected-statement-composition.json' if include_capacity else 'row-home-guard-statement-composition.json')
c=load(composition_path);statements=c['statements']
assert [x['ordinal'] for x in statements]==[str(i) for i in range(len(statements))]
for source in c['inputs']:
 assert sha(source['modelPath'])==source['modelSha256'] and sha(source['sourcePath'])==source['sourceSha256']
for x in statements:assert hashlib.sha256(x['sql'].encode()).hexdigest()==x['sha256']
assert len(c['joins'])==len(statements)+1
joined=c['joins'][0]+''.join(x['sql']+c['joins'][i+1] for i,x in enumerate(statements))
assert hashlib.sha256(joined.encode()).hexdigest()==c['joinedSqlSha256']
lookup={(x['modelPath'],x['sourceStatementIndex']):x for x in statements};assert len(lookup)==len(statements)
paths=['docs/helix/02-design/models/truss-row-home-candidate.physical-ids.proposal.json','docs/helix/02-design/models/truss-row-home-candidate.supporting-index-ids.proposal.json','docs/helix/02-design/models/truss-row-home-touch.physical-ids.proposal.json','docs/helix/02-design/models/truss-row-home-touch.supporting-index-ids.proposal.json']
if include_capacity:paths.extend(['docs/helix/02-design/models/truss-row-home-capacity.physical-ids.proposal.json','docs/helix/02-design/models/truss-row-home-capacity.supporting-index-ids.proposal.json'])
if include_guards:paths.extend(['docs/helix/02-design/models/truss-row-home-operation.physical-ids.proposal.json','docs/helix/02-design/models/truss-row-home-operation.supporting-index-ids.proposal.json','docs/helix/02-design/models/truss-row-home-triggers.physical-ids.proposal.json'])
if include_edge_limits:paths.append('docs/helix/02-design/models/truss-edge-limit-triggers.physical-ids.proposal.json')
if include_unfinished_unique:paths.append('docs/helix/02-design/models/truss-row-operation-unfinished-unique.physical-ids.proposal.json')
if include_initialization:paths.append('docs/helix/02-design/models/truss-row-home-capacity.initialization-ids.proposal.json')
allocations=[load(p) for p in paths]
for allocation in allocations:
 if 'sourceAllocationPath' in allocation:assert allocation['sourceAllocationSha256']==sha(allocation['sourceAllocationPath'])
 if 'parentAllocation' in allocation:assert allocation['parentAllocation']['sha256']==sha(allocation['parentAllocation']['path'])
 if 'referencedAllocation' in allocation:assert allocation['referencedAllocation']['sha256']==sha(allocation['referencedAllocation']['path'])
 for pin in allocation.get('parentAllocationPins',[]):assert pin['sha256']==sha(pin['path'])
creators={e['entryId']:e for allocation in allocations for e in allocation['entries'] if e['objectKind']=='constraint'}
models={p['modelPath']:load(p['modelPath']) for p in c['inputs']};seen=set();mapped={x['ordinal']:[] for x in statements}
for allocation in allocations:
 assert allocation['complete'] is False
 for e in allocation['entries']:
  assert e['entryId'] not in seen;seen.add(e['entryId']);loc=e['capturedModelLocator']
  assert loc['modelSha256']==sha(loc['modelPath'])
  pointer=loc['jsonPointer'];parts=pointer.strip('/').split('/');i=parts.index('stmts');assert parts[i+1]=='items'
  index=parts[i+2];s=lookup[(loc['modelPath'],index)];node=models[loc['modelPath']]
  for part in parts:node=node[int(part)] if isinstance(node,list) else node[part]
  if e['objectKind']=='supporting-index':
   creator=creators[e['creatingConstraintId']];assert loc==creator['capturedModelLocator'] and e['parentId']==creator['parentId']
  else:assert node==e['originalNativeNode']
  mapped[s['ordinal']].append({'physicalIdentity':e['entryId'],'objectKind':e['objectKind'],'capturedSourcePath':pointer,'statementSqlSha256':s['sha256']})
for allocation in allocations:
 if 'referencedAllocation' in allocation:
  ref=allocation['referencedAllocation'];assert {ref['tableEntryId'],*ref['columnEntryIds']}<=seen
assert all(mapped.values()), 'statement without selected authored source identity'
receipt={'scope':'Selected authored source/effect identities to complete ordered selected original export statements; full native effect/guard/grant/dependency inventory remains incomplete','inputPins':[{'path':p,'sha256':sha(p)} for p in [composition_path,*paths]],'physicalIdentities':len(seen),'statements':len(statements),'unmappedStatements':[],'physicalCoverageComplete':False,'installable':False,'blockedDependencies':c.get('blockedDependencies',[]),'mapping':[{'ordinal':x['ordinal'],'modelPath':x['modelPath'],'sourceStatementIndex':x['sourceStatementIndex'],'statementSqlSha256':x['sha256'],'executionKind':x['executionKind'],'parameterPositions':x['parameterPositions'],'entries':mapped[x['ordinal']]} for x in statements]}
(root/('docs/helix/04-build/evidence/design-audit/'+('row-home-unfinished-unique-guard-statement-mapping.json' if include_unfinished_unique else 'row-home-edge-limit-guard-statement-mapping.json' if include_edge_limits else 'row-home-native-guard-statement-mapping.json' if include_guards else 'row-home-initialized-statement-mapping.json' if include_initialization else 'row-home-protected-statement-mapping.json' if include_capacity else 'row-home-guard-statement-mapping.json'))).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['physicalIdentities','statements','unmappedStatements','physicalCoverageComplete']}))
