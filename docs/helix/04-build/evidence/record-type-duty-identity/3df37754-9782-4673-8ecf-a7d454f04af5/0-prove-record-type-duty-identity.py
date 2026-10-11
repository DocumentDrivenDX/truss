"""Conditional declaration-duty tuple/gate algebra; not a JavaScript or native proof."""
from pathlib import Path
import hashlib,json,uuid
from z3 import *
root=Path.cwd();out=root/'docs/helix/04-build/evidence/record-type-duty-identity'/str(uuid.uuid4());out.mkdir(parents=True)
fields=['profile','document','revision','digest','module','field','pointer','family']
Duty=Datatype('DeclarationDuty');Duty.declare('duty',*[(f,StringSort()) for f in fields]);Duty=Duty.create()
a=[String('a_'+f) for f in fields];b=[String('b_'+f) for f in fields]
x=Duty.duty(*a);y=Duty.duty(*b);same=And(*[v==w for v,w in zip(a,b)])
configured,observed,meaning,issued,duplicate=Bools('configured observed meaning issued duplicate')
accept=And(issued,Not(duplicate),Or(Not(configured),And(observed,meaning)))
queries=[]
def check(name,formula,want):
 s=Solver();s.add(formula);got=str(s.check());assert got==want,(name,got)
 queries.append({'name':name,'expected':want,'result':got,'smt2':s.to_smt2(),'witness':str(s.model()) if got=='sat' else None})
check('equal coordinates cannot split duty identity',And(same,x!=y),'unsat')
check('distinct qualified occurrence cannot collapse duty identity',And(Not(same),x==y),'unsat')
check('protocol difference with equal occurrence remains one duty',And(same,String('protocol_a')!=String('protocol_b'),x==y),'sat')
check('different qualified Field module remains a distinguishable duty',And(a[4]!=b[4],x!=y),'sat')
check('configured unavailable observation cannot allocate',And(accept,configured,Not(observed)),'unsat')
check('configured mismatched meaning cannot allocate',And(accept,configured,Not(meaning)),'unsat')
check('unissued receipt cannot allocate',And(accept,Not(issued)),'unsat')
check('duplicate receipt-backed occurrence cannot allocate',And(accept,duplicate),'unsat')
check('no generic owner may retain explicitly unavailable correspondence',And(accept,Not(configured),Not(observed)),'sat')
check('issued matching nonduplicate occurrence may allocate',And(accept,configured,observed,meaning,issued,Not(duplicate)),'sat')
paths=[Path(__file__),root/'packages/umf-bun/src/catalog-record-type-rule-families.ts',root/'packages/umf-bun/src/catalog-report-preparation.ts',root/'tests/catalog-type-journals.test.ts']
pins=[]
for i,p in enumerate(paths):
 data=p.read_bytes();name=str(i)+'-'+p.name;(out/name).write_bytes(data);pins.append({'path':str(p),'archive':name,'sha256':hashlib.sha256(data).hexdigest()})
proof={'status':'passed','z3Version':get_version_string(),'queries':queries,'sourcePreimages':pins,'scope':'Conditional tuple injectivity and Boolean admission-gate algebra only','premises':['Actual issued collections supply original coordinates and complete meaning; tested independently, not proved here','Strings faithfully stand for original profile/doc/revision/digest/qualified Field/pointer/family; no hash collision proof','Protocol is evidence outside duty identity','Duplicate detection and configured correspondence map to the displayed Boolean gate; no code correspondence theorem'],'excluded':['JavaScript execution','JSON parsing','issuer authentication','nested record-valued literals','native data enforcement','unbounded runtime resource analysis'],'acceptancePromoted':False}
(out/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'status':'passed','queries':len(queries),'proof':str(out/'proof.json')}))
