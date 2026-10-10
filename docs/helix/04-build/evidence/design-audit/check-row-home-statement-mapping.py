"""Authored row-home identity to original statement source bridge, no native effects proof."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[5]
load=lambda p:json.loads((root/p).read_text())
sha=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
composition_path='docs/helix/04-build/evidence/design-audit/row-home-statement-composition.json'
c=load(composition_path);statements=c['statements']
assert [x['ordinal'] for x in statements]==[str(i) for i in range(len(statements))]
for source in c['inputs']:
 assert sha(source['modelPath'])==source['modelSha256'] and sha(source['sourcePath'])==source['sourceSha256']
for x in statements:assert hashlib.sha256(x['sql'].encode()).hexdigest()==x['sha256']
assert len(c['joins'])==len(statements)+1
joined=c['joins'][0]+''.join(x['sql']+c['joins'][i+1] for i,x in enumerate(statements))
assert hashlib.sha256(joined.encode()).hexdigest()==c['joinedSqlSha256']
lookup={(x['modelPath'],x['sourceStatementIndex']):x for x in statements};assert len(lookup)==len(statements)
paths=['docs/helix/02-design/models/truss-row-home-candidate.physical-ids.proposal.json','docs/helix/02-design/models/truss-row-home-candidate.supporting-index-ids.proposal.json']
base=load(paths[0]);effects=load(paths[1]);assert effects['sourceAllocationSha256']==sha(paths[0])
creators={e['entryId']:e for e in base['entries'] if e['objectKind']=='constraint'}
models={p['modelPath']:load(p['modelPath']) for p in c['inputs']};seen=set();mapped={x['ordinal']:[] for x in statements}
for allocation in [base,effects]:
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
assert all(mapped.values()), 'statement without selected authored source identity'
receipt={'scope':'Selected76 authored source/effect identities to ten ordered original export statements; full native effect/guard/grant/dependency inventory remains incomplete','inputPins':[{'path':p,'sha256':sha(p)} for p in [composition_path,*paths]],'physicalIdentities':len(seen),'statements':len(statements),'unmappedStatements':[],'physicalCoverageComplete':False,'mapping':[{'ordinal':x['ordinal'],'modelPath':x['modelPath'],'sourceStatementIndex':x['sourceStatementIndex'],'statementSqlSha256':x['sha256'],'entries':mapped[x['ordinal']]} for x in statements]}
(root/'docs/helix/04-build/evidence/design-audit/row-home-statement-mapping.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['physicalIdentities','statements','unmappedStatements','physicalCoverageComplete']}))
