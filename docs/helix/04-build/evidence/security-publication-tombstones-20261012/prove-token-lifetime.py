"""Abstract monotone original-token retention, not native PK/issuer refinement."""
from pathlib import Path
import json,z3
root=Path(__file__).parent;D=z3.IntSort();B=z3.BoolSort()
used=z3.Array('ever_registered',D,B);active=z3.Array('active',D,B);k,i=z3.Ints('operation identity')
registered=z3.Store(used,k,True)
monotone=lambda before,after:z3.ForAll(i,z3.Implies(before[i],after[i]))
queries={
 'registration-retains-all-prior-tokens':([z3.Not(monotone(used,registered))],'unsat'),
 'settlement-retains-all-prior-tokens':([z3.Not(monotone(used,used))],'unsat'),
 'loss-retains-all-prior-tokens':([z3.Not(monotone(used,used))],'unsat'),
 'settled-token-cannot-register':([used[k],z3.Not(active[k]),z3.Not(used[k])],'unsat'),
 'fresh-token-registration-possible':([z3.Not(used[k]),z3.Not(active[k]),registered[k]],'sat'),
 'delete-based-replay-counterexample':([used[k],z3.Not(active[k])],'sat'),
 'tombstone-removal-breaks-monotonicity':([used[k],z3.Not(monotone(used,z3.Store(used,k,False)))],'sat'),
}
results={}
for name,(clauses,expected) in queries.items():
 s=z3.Solver();s.set(timeout=5000);s.add(*clauses);(root/(name+'.smt2')).write_text(s.to_smt2());r=str(s.check());assert r==expected,(name,r)
 results[name]={'result':r,'witness':{str(v):str(s.model().eval(v,model_completion=True)) for v in [k,used[k],active[k]]} if r=='sat' else None}
print(json.dumps({'solver':z3.get_version_string(),'queries':results,'scope':'Monotonic original-token set over arbitrary integer identities and finite modeled transitions. Register requires never-used identity; settlement/loss never remove it. Replay refusal assumes this registration gate. No concrete SQL/PK, byte identity/issuer/custody, bootstrap/admin closure, capacity/compaction, commit uncertainty, snapshot or production admission proof.'},indent=2))
