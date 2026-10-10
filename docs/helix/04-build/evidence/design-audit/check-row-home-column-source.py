"""Complete retained row-home column source observation; native resolution unproven."""
from pathlib import Path
import json,hashlib
from collections import Counter
root=Path(__file__).resolve().parents[5]
allocation='docs/helix/02-design/models/truss-row-home-candidate.physical-ids.proposal.json'
raw=(root/allocation).read_bytes();d=json.loads(raw);models={};pins=[{'path':allocation,'sha256':hashlib.sha256(raw).hexdigest()}]
for source in d['sources']:
 for path,expected in [(source['source'],source['sourceSha256']),(source['model'],source['modelSha256'])]:
  b=(root/path).read_bytes();assert hashlib.sha256(b).hexdigest()==expected;pins.append({'path':path,'sha256':expected})
 models[source['model']]=json.loads((root/source['model']).read_text())
columns=[];counts=Counter();defaults=[]
def references(n,p):
 if isinstance(n,dict):
  for k,v in n.items():
   if k in {'FuncCall','TypeCast','CollateClause'}:yield {'sourcePath':p+'/'+k,'nativeNodeKind':k,'originalNativeNode':v,'nativeBinding':{'state':'unresolved'}}
   yield from references(v,p+'/'+k)
 elif isinstance(n,list):
  for i,v in enumerate(n):yield from references(v,p+'/'+str(i))
for e in d['entries']:
 if e['objectKind']!='column':continue
 loc=e['capturedModelLocator'];node=models[loc['modelPath']]
 for part in loc['jsonPointer'].strip('/').split('/'):node=node[int(part)] if isinstance(node,list) else node[part]
 assert node==e['originalNativeNode'];m=node['members'];constraints=[]
 for i,x in enumerate(m.get('constraints',{}).get('items',[])):
  c=x['members']['Constraint'];kind=c['members']['contype']['value'];counts[kind]+=1
  path=loc['jsonPointer']+f'/members/constraints/items/{i}/members/Constraint'
  constraints.append({'sourcePath':path,'nativeKind':kind,'originalNativeNode':c})
  if kind=='CONSTR_DEFAULT':defaults.append({'columnId':e['entryId'],'sourcePath':path,'originalDefaultNode':c,'references':list(references(c,path))})
 columns.append({'columnId':e['entryId'],'parentId':e['parentId'],'capturedModelLocator':loc,'nativeFieldNames':sorted(m),'originalNativeDefinition':node,'constraints':constraints,'nativeBinding':{'state':'unresolved'}})
assert len(columns)==36
for pin in pins:assert hashlib.sha256((root/pin['path']).read_bytes()).hexdigest()==pin['sha256']
receipt={'scope':'All retained ColumnDef fields, exact local constraint/default/type/collation source and source references only. Explicit NOT NULL source is separate from effective PK nullability; native type/collation/default/function/regclass/sequence dependencies remain unresolved.','inputPins':pins,'columns':columns,'columnConstraintCounts':dict(sorted(counts.items())),'defaults':defaults,'physicalCoverageComplete':False}
(root/'docs/helix/04-build/evidence/design-audit/row-home-column-source.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'columns':len(columns),'columnConstraintCounts':receipt['columnConstraintCounts'],'defaults':len(defaults),'physicalCoverageComplete':False}))
