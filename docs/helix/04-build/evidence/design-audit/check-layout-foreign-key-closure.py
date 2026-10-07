"""Declared source FK target/unique-key closure only; no native type resolution."""
import copy,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[5]
version=sys.argv[1] if len(sys.argv)>1 else '0.9'
if version not in ('0.9','0.10'):raise ValueError('unsupported inventory version')
P=R/f'docs/helix/02-design/contracts/weft-review-columns-v{version}.proposal.json'
inventory=json.loads(P.read_bytes())
if hashlib.sha256((R/inventory['astPath']).read_bytes()).hexdigest()!=inventory['astSha256']:raise ValueError('stale source AST')
def names(xs):return tuple(x['String']['sval'] for x in xs)
def audit(inv):
 tables={t['name']:t for t in inv['tables']};unique={};refs=[]
 for name,t in tables.items():
  unique[name]=[]
  for c in t['constraints']:
   d=c['definition']
   if d['contype'] in ('CONSTR_PRIMARY','CONSTR_UNIQUE') and not d.get('deferrable',False):unique[name].append(names(d['keys']))
  for c in t['columns']:
   for x in c['constraints']:
    d=x['Constraint']
    if d['contype'] in ('CONSTR_PRIMARY','CONSTR_UNIQUE') and not d.get('deferrable',False):unique[name].append((c['name'],))
 for idx in inv['indexes']:
  d=idx['definition']
  if d.get('unique') and not d.get('whereClause'):
   keys=tuple(x['IndexElem'].get('name') for x in d['indexParams'])
   if all(keys):unique[d['relation']['relname']].append(keys)
 for name,t in tables.items():
  constraints=[(c['definition'],None) for c in t['constraints']]
  constraints += [(x['Constraint'],c['name']) for c in t['columns'] for x in c['constraints']]
  for d,col in constraints:
   if d['contype']!='CONSTR_FOREIGN':continue
   target=d['pktable'];tn=target['relname']
   if target.get('schemaname') not in (None,'truss') or tn not in tables:raise ValueError('missing/foreign target '+name+' -> '+tn)
   fk=names(d['fk_attrs']) if d.get('fk_attrs') else (col,)
   if d.get('pk_attrs'):pk=names(d['pk_attrs'])
   else:
    prim=[]
    for c in tables[tn]['constraints']:
     if c['definition']['contype']=='CONSTR_PRIMARY':prim.append(names(c['definition']['keys']))
    for c in tables[tn]['columns']:
     if any(x['Constraint']['contype']=='CONSTR_PRIMARY' for x in c['constraints']):prim.append((c['name'],))
    if len(prim)!=1:raise ValueError('implicit target PK unresolved')
    pk=prim[0]
   if len(fk)!=len(pk) or any(x not in {c['name'] for c in t['columns']} for x in fk) or any(x not in {c['name'] for c in tables[tn]['columns']} for x in pk):raise ValueError('FK column/arity mismatch')
   if not any(len(u)==len(pk) and set(u)==set(pk) for u in unique[tn]):raise ValueError('missing nondeferrable unique target '+tn+str(pk))
   refs.append({'from':name,'columns':fk,'to':tn,'targetColumns':pk})
 return refs
refs=audit(inventory)
damaged=copy.deepcopy(inventory)
found=False
for t in damaged['tables']:
 for c in t['constraints']:
  if c['definition']['contype']=='CONSTR_FOREIGN':c['definition']['pktable']['relname']='missing_table';found=True;break
 if found:break
if not found:raise ValueError('no test reference')
try:audit(damaged)
except ValueError:pass
else:raise ValueError('missing target accepted')
receipt={'scope':'all declared inline/table FK columns and referenced nondeferrable declared PK/unique targets; no native type/collation/operator/dependency or hidden-effect qualification','inventorySha256':hashlib.sha256(P.read_bytes()).hexdigest(),'references':refs,'missingTargetControlRejected':True,'nativeQualified':False}
(R/('docs/helix/04-build/evidence/design-audit/layout-foreign-key-closure'+('' if version=='0.9' else '-v'+version)+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'declaredReferences':len(refs),'sourceTargetClosure':True,'missingTargetControlRejected':True,'nativeQualified':False}))
