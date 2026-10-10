"""Original actor-helper source capture only; no native actor or policy qualification."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[5]
path='docs/helix/02-design/models/truss-module-isolation-0.2.umf.json'
b=(R/path).read_bytes();model=json.loads(b)
base='/modules/0/elements/0/extensions/umf.postgresql/root/members/stmts/items'
nodes=model['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root']['members']['stmts']['items']
def decode(n):
 if n['kind']=='object':return {k:decode(v) for k,v in n['members'].items()}
 if n['kind']=='array':return [decode(v) for v in n['items']]
 return json.loads(n['value']) if n['kind']=='number' else n.get('value')
found=[]
for i,n in enumerate(nodes):
 f=decode(n).get('stmt',{}).get('CreateFunctionStmt')
 if f and [x['String']['sval'] for x in f['funcname']]==['truss','acting_role']:found.append((i,n,f))
if len(found)!=1:raise ValueError('original helper membership')
i,node,f=found[0]
if f.get('parameters') or [x['String']['sval'] for x in f['returnType']['names']]!=['text']:raise ValueError('original helper signature')
opts={x['DefElem']['defname']:x['DefElem']['arg'] for x in f['options']}
if opts['language']['String']['sval']!='sql' or opts['volatility']['String']['sval']!='stable':raise ValueError('original helper attributes')
body=opts['as']['List']['items'][0]['String']['sval']
if body!=" SELECT COALESCE(NULLIF(current_setting('role'), 'none'), session_user)::text ":raise ValueError('original actor capture changed')
result={'scope':__doc__,'sourceModel':{'path':path,'sha256':hashlib.sha256(b).hexdigest()},
 'originalLocator':base+'/'+str(i),'originalTaggedStatement':node,'decodedDefinition':f,
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'physicalIdentity':None,'nativeBinding':None,'otherBaselinePoliciesAdmitted':False,'nativeQualified':False}
(R/'docs/helix/04-build/evidence/design-audit/acting-role-helper-source.json').write_text(json.dumps(result,indent=2)+'\n')
print('Original zero-argument SQL STABLE text helper captured; no native/policy adoption.')
