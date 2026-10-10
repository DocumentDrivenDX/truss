"""Exact candidate source delta, not native installation or enforcement."""
from pathlib import Path
import json,hashlib,copy
B=Path(__file__).parent;root=B.parents[4]
def load(name):return json.loads((B/name).read_text())
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=load('row-home-edge-limit-guard-statement-composition.json');b=load('row-home-unfinished-unique-guard-statement-composition.json')
am=load('row-home-edge-limit-guard-statement-mapping.json');bm=load('row-home-unfinished-unique-guard-statement-mapping.json')
def key(s):return s['modelPath'],s['sourceStatementIndex']
old={key(s):s for s in a['statements']};new={key(s):s for s in b['statements']}
require(len(old)==23 and len(new)==24,'exact original statement membership')
require(set(old)<set(new),'preserve every original source statement')
for k,s in old.items():
 t=new[k];require({p:v for p,v in s.items() if p!='ordinal'}=={p:v for p,v in t.items() if p!='ordinal'},'retained original statement changed')
added=[s for k,s in new.items() if k not in old];require(len(added)==1,'one index statement')
index=added[0];require(index['modelPath'].endswith('/row-operation-unfinished-unique-v0.1.proposal.umf.json') and index['sourceStatementIndex']=='0' and index['executionKind']=='ddl' and index['parameterPositions']==[],'exact index source identity')
old_order=[key(s) for s in a['statements']];retained_order=[key(s) for s in b['statements'] if key(s) in old];require(old_order==retained_order,'preserved original relative order')
parent=next(s for s in b['statements'] if s['modelPath'].endswith('/row-home-operation-v0.1.proposal.umf.json'))
require(int(parent['ordinal'])<int(index['ordinal']),'registry precedes added index')
require(b['statements'][-1]['executionKind']=='parameterized-initialization','fresh initializer remains last')
def validate_mapping(c,m):
 require(len(m['mapping'])==len(c['statements']),'complete mapping statement membership')
 require([r['ordinal'] for r in m['mapping']]==[str(i) for i in range(len(c['statements']))],'mapping ordinal membership/order')
 ids=[]
 for statement,row in zip(c['statements'],m['mapping']):
  for field in ['modelPath','sourceStatementIndex','executionKind','parameterPositions']:
   require(row[field]==statement[field],'mapping original statement field: '+field)
  require(row['statementSqlSha256']==statement['sha256'] and bool(row['entries']),'mapped statement hash/nonempty identities')
  for e in row['entries']:
   require(e['statementSqlSha256']==statement['sha256'],'mapped effect original statement hash')
   ids.append(e['physicalIdentity'])
 require(len(ids)==len(set(ids))==m['physicalIdentities'],'no duplicate/redefined effect membership')
 require(m['statements']==len(c['statements']) and m['unmappedStatements']==[] and not m['physicalCoverageComplete'] and not m['installable'],'exact mapping scope/limitations')
validate_mapping(a,am);validate_mapping(b,bm)
def entries(m):return {e['physicalIdentity']:(s,e) for s in m['mapping'] for e in s['entries']}
ae=entries(am);be=entries(bm);require(len(ae)==142 and len(be)==143 and set(ae)<set(be),'exact authored effect membership')
require(set(be)-set(ae)=={'truss.row-home.index.row_home_operation_unfinished_xid'},'one added index identity')
for id,(s,e) in ae.items():
 t,f=be[id];require(e==f and {k:v for k,v in s.items() if k not in ('ordinal','entries')}=={k:v for k,v in t.items() if k not in ('ordinal','entries')},'retained identity/source mapping changed')
for c in [a,b]:
 require(not c['installable'] and not c['physicalCoverageComplete'] and not c['nativeExecution'],'no widened support claim')
 for pin in c['inputs']:require(sha(root/pin['modelPath'])==pin['modelSha256'] and sha(root/pin['sourcePath'])==pin['sourceSha256'],'original input pins')
mapping_controls=[]
for name,change in [
 ('missing-statement-row',lambda m:m['mapping'].pop()),
 ('duplicate-effect-identity',lambda m:m['mapping'][0]['entries'].append(copy.deepcopy(m['mapping'][0]['entries'][0]))),
 ('wrong-original-source-index',lambda m:m['mapping'][0].update(sourceStatementIndex='999')),
 ('wrong-effect-statement-hash',lambda m:m['mapping'][0]['entries'][0].update(statementSqlSha256='0'*64)),
 ('lost-initialization-parameters',lambda m:m['mapping'][-1].update(parameterPositions=[])),
 ('promote-installation-claim',lambda m:m.update(installable=True))]:
 candidate=copy.deepcopy(bm);change(candidate)
 try:validate_mapping(b,candidate)
 except ValueError:mapping_controls.append(name)
 else:raise RuntimeError('accepted mapping corruption: '+name)
receipt={'status':'pass','scope':'exact retained 23-statement/142-identity source correspondence and relative order, one additional source-bound index after registry, initializer last; no native dependency/security/adoption/installation/enforcement','mappingCorruptionControls':mapping_controls,'retainedStatements':23,'retainedIdentities':142,'addedStatements':1,'addedIdentities':1,'candidateStatements':24,'candidateIdentities':143,'inputPins':{name:sha(B/name) for name in ['row-home-edge-limit-guard-statement-composition.json','row-home-unfinished-unique-guard-statement-composition.json','row-home-edge-limit-guard-statement-mapping.json','row-home-unfinished-unique-guard-statement-mapping.json']},'installable':False,'nativeExecution':False}
(B/'unfinished-unique-composition-delta.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='inputPins'}))
