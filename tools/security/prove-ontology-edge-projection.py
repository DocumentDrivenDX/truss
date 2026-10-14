"""Conditional unbounded typed-key witness law; not extracted Python/SQL proof."""
import hashlib,json
from pathlib import Path
from z3 import DeclareSort,Function,Const,Consts,BoolSort,ForAll,Exists,And,Not,Implies,Distinct,Solver,get_version_string
S,P,R,A,O=[DeclareSort(name) for name in ('Staff','Project','Resource','Assignment','Ownership')]
KS,KP,KR=[DeclareSort(name) for name in ('StaffKey','ProjectKey','ResourceKey')]
ks,kp,kr=Function('staff_key',S,KS),Function('project_key',P,KP),Function('resource_key',R,KR)
as_staff,as_project,ow_resource,ow_project=Function('assignment_staff',A,S),Function('assignment_project',A,P),Function('ownership_resource',O,R),Function('ownership_project',O,P)
active,projected_active=Function('active',A,BoolSort()),Function('projected_active',A,BoolSort())
s,r,a,o=Const('subject',S),Const('resource',R),Const('a',A),Const('o',O)
def injective(sort,key,name):
 x,y=Consts(name+'1 '+name+'2',sort);return ForAll([x,y],Implies(key(x)==key(y),x==y))
inj=[injective(S,ks,'s'),injective(P,kp,'p'),injective(R,kr,'r')]
state=ForAll([a],projected_active(a)==active(a))
native=Exists([a,o],And(as_staff(a)==s,ow_resource(o)==r,as_project(a)==ow_project(o),active(a)))
logical=Exists([a,o],And(ks(as_staff(a))==ks(s),kr(ow_resource(o))==kr(r),kp(as_project(a))==kp(ow_project(o)),projected_active(a)))
controls=[('typed-key-projection-equivalence','unsat',inj+[state,native!=logical]),('positive-population','sat',inj+[state,native,logical]),('omit-staff-key-injectivity','sat',[inj[1],inj[2],state,logical,Not(native)]),('omit-project-key-injectivity','sat',[inj[0],inj[2],state,logical,Not(native)]),('omit-resource-key-injectivity','sat',[inj[0],inj[1],state,logical,Not(native)]),('omit-active-preservation','sat',inj+[logical,Not(native)])]
rows=[]
for name,expected,formula in controls:
 solver=Solver();solver.set(timeout=5000);solver.add(*formula);observed=str(solver.check());assert observed==expected,(name,expected,observed)
 smt=solver.sexpr();rows.append({'id':name,'expected':expected,'observed':observed,'smtSha256':hashlib.sha256(smt.encode()).hexdigest(),'smt':smt})
paths=[Path(__file__),Path('scripts/security_ontology_edge_projection.py')]
receipt={'status':'passed','z3':get_version_string(),'cases':rows,'sourceDigests':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'Unbounded uninterpreted typed entities/keys. Exactly-one native endpoint paths represented by total endpoint functions; complete enumeration and injective per-type key normalization plus preserved active state imply equal existential resource eligibility. SAT controls witness necessity. No automatic Python/SQL/compiler refinement, authenticated source/completeness, lock/snapshot/publication, disclosure or backend admission proof.'}
Path('docs/helix/04-build/evidence/security-ontology-shared-policy-20261014/formal.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':'passed','cases':len(rows),'z3':get_version_string()}))
