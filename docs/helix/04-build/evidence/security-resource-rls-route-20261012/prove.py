"""Conditional three-valued row-binding law; not native SQL refinement."""
import z3,json,hashlib
from pathlib import Path
root=Path(__file__).parent;source=Path('/private/tmp/truss-security-main-integration/packages/postgresql/src/security-predicate.ts');frozen={p:p.read_bytes() for p in [source,root/'sql.json',root/'rls.py',Path(__file__)]}
actual,asserted=z3.Ints('actual asserted');domain=[actual>=0,actual<=2,asserted>=0,asserted<=2];eligible=lambda x:x==1;observations=[]
for name,clauses,expected in [('actual-row-policy-excludes-denied-values',[eligible(actual),eligible(asserted),actual!=1],'unsat'),('asserted-predicate-alone-can-lie',[eligible(asserted),actual==0],'sat'),('wrong-argument-binding-can-broaden-access',[eligible(asserted),actual==2],'sat')]:
 solver=z3.Solver();solver.add(*domain,*clauses);outcome=str(solver.check());assert outcome==expected;row={'id':name,'expected':expected,'observed':outcome,'formula':solver.sexpr()}
 if outcome=='sat':row['witness']={str(d):str(solver.model()[d]) for d in solver.model().decls()}
 observations.append(row)
assert all(p.read_bytes()==b for p,b in frozen.items());(root/'formal.json').write_text(json.dumps({'z3':z3.get_version_string(),'truthDomain':'0=False,1=True,2=Unknown','observations':observations,'sourcePins':{str(p):hashlib.sha256(b).hexdigest() for p,b in frozen.items()},'scope':'Conditional row-binding implication plus concrete widening witnesses; native SQL/function/source authenticity and general Rust/TS refinement are not proved'},indent=2)+'\n')
