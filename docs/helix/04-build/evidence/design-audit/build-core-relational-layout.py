"""Author core layout from pinned owner declaration inventory; no SQL generation."""
import json, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[3]
modelpath=root/'02-design/models/truss-layout-reference-history-0.12.proposal.umf.json'
invpath=root/'02-design/contracts/weft-review-columns-v0.12.proposal.json'
model=json.loads(modelpath.read_text()); inv=json.loads(invpath.read_text())
hashbytes=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
astpath=root.parent.parent/inv['astPath']
assert hashbytes(astpath)==inv['astSha256']
module='truss-layout'; ref=lambda e:{'module':module,'element':e}
records={}; cols={}; constraints=[]; elements=[]
families={'text':'string','bpchar':'string','bytea':'binary','int2':'integer','int4':'integer','int8':'integer','bool':'boolean','numeric':'decimal','timestamptz':'timestamp'}
for t in inv['tables']:
 name=t['name']; record={'id':name,'name':name,'kind':'record','extensions':{},'members':[],'references':[]}; records[name]=record; elements.append(record)
 for c in t['columns']:
  fid=name+'.'+c['name'];typeparts=[n['String']['sval'] for n in c['declaredType']['names']]; native='.'.join(typeparts)
  field={'id':fid,'name':c['name'],'kind':'field','scalarType':families.get(typeparts[-1],'postgresql.'+typeparts[-1]),'cardinality':'one','nullability':'required' if any(z.get('Constraint',{}).get('contype') in ('CONSTR_NOTNULL','CONSTR_PRIMARY') for z in c['constraints']) else 'unspecified','extensions':{'truss.layout.native':{'sourcePointer':c['definitionPointer'],'nativeType':c['declaredType'],'collation':c['collation'],'constraints':c['constraints'],'sqlNullMeaning':'retained-native-constraints; not core absence'}}}
  elements.append(field);cols[(name,c['name'])]=fid;record['members'].append(ref(fid));record['references'].append({'role':'member',**ref(fid)})
  for z in c['constraints']:
   q=z.get('Constraint');
   if q:constraints.append((name,[c['name']],c['definitionPointer'],q))
 for z in t['constraints']:constraints.append((name,None,z['pointer'],z['definition']))
keys={}; fks=[]
strings=lambda xs:[x['String']['sval'] for x in xs]
for table,inline,pointer,q in constraints:
 kind=q['contype'];fields=inline if inline is not None else strings(q.get('keys',[]))
 if kind in ('CONSTR_PRIMARY','CONSTR_UNIQUE'):
  assert fields and all((table,c) in cols for c in fields)
  kid=q.get('conname') or ('primary' if kind=='CONSTR_PRIMARY' else 'unique')+'-'+str(len(records[table].get('keys',[])))
  key={'id':kid,'name':kid,'fields':[ref(cols[(table,c)]) for c in fields],'primary':kind=='CONSTR_PRIMARY'}
  
  if kind=='CONSTR_PRIMARY':
   for fieldname in fields:
    next(e for e in elements if e['id']==cols[(table,fieldname)])['nullability']='required'
  records[table].setdefault('keys',[]).append(key);keys.setdefault((table,tuple(fields)),[]).append(kid)
 if kind=='CONSTR_FOREIGN':fks.append((table,inline,pointer,q))
relationships=[]
for i,(table,inline,pointer,q) in enumerate(fks):
 target=q['pktable']['relname'];sf=inline if inline is not None else strings(q.get('fk_attrs',[]));tf=strings(q.get('pk_attrs',[]))
 if not tf:
  pk=[k for k in records[target].get('keys',[]) if k['primary']];assert len(pk)==1;tf=[f['element'].split('.',1)[1] for f in pk[0]['fields']]
 assert len(sf)==len(tf) and all((table,c) in cols for c in sf)
 candidates=keys.get((target,tuple(tf)),[]);assert len(candidates)==1,(table,target,tf,candidates)
 rid='fk-'+str(i+1)
 relationships.append({'id':rid,'name':q.get('conname') or rid,'source':[ref(table)],'target':[{**ref(target),'key':candidates[0]}],'sourceMultiplicity':{'min':0,'max':'*'},'targetMultiplicity':{'min':0,'max':1},'targetLifecycle':'unspecified','directed':True,'fieldCorrespondence':[{'source':ref(cols[(table,a)]),'target':ref(cols[(target,b)])} for a,b in zip(sf,tf)],'nativeCorrespondence':{'sourcePointer':pointer,'definition':q,'scope':'physical FK association; broad multiplicities are not full native enforcement equivalence'}})
model['id']='truss-layout-core-relational-0.1-review'
# New authored core document; the untouched original source remains pinned separately.
model['umf']='0.7.0'
model['modules'].append({'id':module,'namespace':'truss','elements':elements,'relationships':relationships})
model.setdefault('vocabularies',{})['truss.layout.native']={'version':'0.1.0'}
model.setdefault('extensions',{})['truss.layout.native']={'sourceModel':str(modelpath.relative_to(root)),'sourceSha256':hashbytes(modelpath),'inventorySha256':hashbytes(invpath),'scope':'Authored core structural mirror with retained native archive. No portable DDL equivalence or installed identity claim.'}
assert len(records)==46 and len(cols)==442 and len(relationships)==61
out=root/'02-design/models/truss-layout-core-relational-0.1.proposal.umf.json'
output=json.dumps(model,separators=(',',':'),ensure_ascii=False)+'\n'
if '--check' in __import__('sys').argv:assert out.read_text()==output
else:out.write_text(output)
print(json.dumps({'records':len(records),'fields':len(cols),'keys':sum(len(t.get('keys',[])) for t in records.values()),'relationships':len(relationships),'nativeArchiveRetained':True,'nativeQualified':False}))
