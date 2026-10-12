"""Finite row-eligibility composition, no disclosure/source/native refinement."""
from pathlib import Path
import json,z3
root=Path(__file__).parent
p1,p2,r,f=z3.Ints('p1 p2 require forbid') # 0=F,1=T,2=U
valid=z3.And(*[z3.And(x>=0,x<=2) for x in [p1,p2,r,f]])
semantic=z3.And(*[x!=2 for x in [p1,p2,r,f]],z3.Or(p1==1,p2==1),r==1,f==0)
native=z3.And(z3.Or(p1==1,p2==1),p1!=2,p2!=2,r==1,f==0)
unguarded=z3.And(z3.Or(p1==1,p2==1),r==1,f==0)
queries=[('row-eligibility-equivalence',z3.And(valid,semantic!=native),'unsat'),('unknown-permit-guard-required',z3.And(valid,unguarded,z3.Not(semantic)),'sat')]
results={}
for name,query,expected in queries:
 s=z3.Solver();s.add(query);p=root/(name+'.smt2');p.write_text(s.to_smt2());assert str(s.check())==expected
 replay=z3.Solver(ctx=z3.Context());replay.add(z3.parse_smt2_file(str(p),ctx=replay.ctx));assert str(replay.check())==expected
 results[name]=expected
print(json.dumps({'z3':z3.get_version_string(),'results':results,'fresh_replays':2,'limits':'Fixed four-rule finite truth model. Actual generated SQL separately exercises81 assignments, not general SQL/routine/snapshot/source/caller/mask/publication refinement.'},indent=2))
