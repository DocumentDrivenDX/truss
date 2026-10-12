"""Conditional three-role SET-state/INHERIT-rights model, not SQL refinement."""
import json
from pathlib import Path
root=Path(__file__).parent
import z3
n=3
sets=[[z3.Bool(f's_{a}_{b}') for b in range(n)] for a in range(n)]
inherits=[[z3.Bool(f'i_{a}_{b}') for b in range(n)] for a in range(n)]
def closure(edges):
    c=[[z3.Or(a==b,edges[a][b]) for b in range(n)] for a in range(n)]
    for k in range(n):
        c=[[z3.Or(c[a][b],z3.And(c[a][k],c[k][b])) for b in range(n)] for a in range(n)]
    return c
def bounded_paths(edges,a,b):
    return z3.Or(a==b,edges[a][b],*[z3.And(edges[a][k],edges[k][b]) for k in range(n)])
s=closure(sets);i=closure(inherits)
exposed=z3.Or(*[z3.And(s[0][state],i[state][2]) for state in range(n)])
independent=z3.Or(*[z3.And(bounded_paths(sets,0,state),bounded_paths(inherits,state,2)) for state in range(n)])
solver=z3.Solver();solver.add(exposed!=independent)
(root/"closure.smt2").write_text(solver.to_smt2())
assert solver.check()==z3.unsat
rows=[('set_set',False,True,False,True,True),('set_inherit',False,True,True,False,True),('inherit_set',True,False,False,True,False),('dormant',False,False,True,False,False)]
results=[]
for name,i0,s0,i1,s1,expected in rows:
    q=z3.Solver()
    for a in range(n):
        for b in range(n):
            q.add(sets[a][b]==({(0,1):s0,(1,2):s1}.get((a,b),False)))
            q.add(inherits[a][b]==({(0,1):i0,(1,2):i1}.get((a,b),False)))
    q.add(exposed!=expected);(root/(name+".smt2")).write_text(q.to_smt2());assert q.check()==z3.unsat
    results.append({'native_control':name,'expected_exposed':expected,'contradiction':'unsat'})
naive=closure([[z3.Or(sets[a][b],inherits[a][b]) for b in range(n)] for a in range(n)])[0][2]
q=z3.Solver();q.add(naive,z3.Not(exposed));(root/"mixed-countermodel.smt2").write_text(q.to_smt2());assert q.check()==z3.sat
print(json.dumps({'z3':z3.get_version_string(),'closure_equivalence':'unsat','controls':results,'arbitrary_mixed_edges_countermodel':'sat','countermodel':str(q.model()),'limits':'Three-role finite logical model. Native correspondence is exercised for four concrete graphs only; no complete SQL, membership-currentness, owner, delegation, callable, diagnostic, or lifetime proof.'},indent=2))
