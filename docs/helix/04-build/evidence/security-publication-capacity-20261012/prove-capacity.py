"""Abstract cardinality proof; fresh serial count is a premise, not SQL refinement."""
from pathlib import Path
import z3,json
root=Path(__file__).parent;n,c=z3.Ints('retained capacity');valid=z3.And(c>=1,c<=1048576,n>=0,n<=c)
queries={'fresh-serial-registration-preserves-capacity':([valid,n<c,n+1>c],'unsat'),'two-fresh-serial-registrations-preserve-capacity':([valid,n<c,n+1<c,n+2>c],'unsat'),'settlement-retains-capacity-occupancy':([valid,n>c],'unsat'),'last-slot-is-reachable':([valid,n==c-1,n<c,n+1==c],'sat'),'shared-stale-count-oversubscribes':([valid,n==c-1,n<c,n<c,n+2>c],'sat')}
out={}
for name,(clauses,expected) in queries.items():
 s=z3.Solver();s.add(*clauses);(root/(name+'.smt2')).write_text(s.to_smt2());r=str(s.check());assert r==expected
 out[name]={'result':r,'witness':{str(v):str(s.model().eval(v,model_completion=True)) for v in [n,c]} if r=='sat' else None}
print(json.dumps({'solver':z3.get_version_string(),'queries':out,'scope':'Integer cardinality invariant under serialized fresh counts and retained settlement. Capacity is fixed by original verified profile. No physical heap/CPU bound, SQL snapshot/lock refinement, byte custody, complete registrant coverage, caller/profile authentication, capacity migration or admission proof.'},indent=2))
