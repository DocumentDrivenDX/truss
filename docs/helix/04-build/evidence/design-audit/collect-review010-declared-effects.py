"""Source effect allocation worklist; no authored-ID reassignment/native parity."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[5]
P=R/'docs/helix/02-design/contracts/weft-review-columns-v0.10.proposal.json'
inv=json.loads(P.read_bytes());b=(R/inv['astPath']).read_bytes()
if hashlib.sha256(b).hexdigest()!=inv['astSha256']:raise ValueError('stale AST')
a=json.loads(b);effects=[];implicit=[];other=[]
def add(kind,pointer,owner,name=None):effects.append({'kind':kind,'sourcePointer':pointer,'owner':owner,'declaredName':name,'authoredPhysicalId':None,'nativeIdentity':None})
for t in inv['tables']:
 add('relation',t['createPointer'],None,t['name'])
 for c in t['columns']:add('column',c['definitionPointer'],t['name'],c['name'])
 constraints=[(c['definition'],c['pointer']) for c in t['constraints']]
 for c in t['columns']:
  constraints.extend((x['Constraint'],c['definitionPointer']+'/constraints/'+str(i)+'/Constraint') for i,x in enumerate(c['constraints']))
 for d,p in constraints:
  typ=d['contype']
  if typ in ('CONSTR_DEFAULT','CONSTR_GENERATED','CONSTR_IDENTITY'):
   add('column_expression_or_allocator',p,t['name'],d.get('conname'))
  else:
   add('constraint_source',p,t['name'],d.get('conname'))
   if typ in ('CONSTR_PRIMARY','CONSTR_UNIQUE','CONSTR_EXCLUSION'):
    implicit.append({'kind':'constraint_supporting_index','creatorPointer':p,'owner':t['name'],'authoredPhysicalId':None,'nativeIdentity':None})
   if typ=='CONSTR_FOREIGN':implicit.append({'kind':'foreign_key_internal_trigger_dependency_set','creatorPointer':p,'owner':t['name'],'cardinality':'native collection required','authoredPhysicalId':None})
for item in inv['indexes']:
 d=item['definition'];add('explicit_index',item['pointer'],d['relation']['relname'],d['idxname'])
for i,n in enumerate(a):
 s=n['stmt'];p=f'/{i}/stmt';kind=next(iter(s))
 if kind=='CreateSeqStmt':add('sequence',p+'/CreateSeqStmt',None,s[kind]['sequence']['relname'])
 elif kind=='CreateFunctionStmt':add('routine',p+'/CreateFunctionStmt',None,'.'.join(x['String']['sval'] for x in s[kind]['funcname']))
 elif kind not in ('CreateStmt','AlterTableStmt','IndexStmt'):other.append({'statementKind':kind,'sourcePointer':p,'requiresSeparateEffectReview':True})
counts=dict(collections.Counter(x['kind'] for x in effects))
receipt={'scope':'selected 0.10 explicit declaration/effect-source worklist and potential implicit dependency classes; constraints remain source nodes rather than asserted native object counts','inventorySha256':hashlib.sha256(P.read_bytes()).hexdigest(),'astPath':inv['astPath'],'astSha256':inv['astSha256'],'effects':effects,'expectedImplicitClasses':implicit,'otherStatements':other,'counts':counts,'physicalCoverageComplete':False,'nativeQualified':False,'identityAllocation':'reuse prior authored identities through original source correspondence; null IDs are unresolved, never generated from names or pointers'}
(R/'docs/helix/04-build/evidence/design-audit/review010-declared-effects.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'sourceEffects':counts,'implicitWorkItems':len(implicit),'otherStatements':len(other),'physicalCoverageComplete':False}))
