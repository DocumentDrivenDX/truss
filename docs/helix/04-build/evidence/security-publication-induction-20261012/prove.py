"""Abstract inductive safety obligations for arbitrary integer claim identities.
No SQL/driver refinement, issuer authenticity, fairness or real-time theorem.
"""
from pathlib import Path
import json,z3
root=Path(__file__).parent
D=z3.IntSort();B=z3.BoolSort()
active=z3.Array('active',D,B);pending=z3.Array('pending',D,B);cg=z3.Array('claim_generation',D,D)
g,k,i,request=z3.Ints('generation operation identity requested_generation')
MAX=9223372036854775807

def invariant(a,p,c,generation):
 return z3.And(generation>0,generation<=MAX,z3.ForAll(i,z3.Implies(p[i],z3.And(a[i],c[i]==generation))))
inv=invariant(active,pending,cg,g)
zero=z3.K(D,False)
registered_a=z3.Store(active,k,True);registered_p=z3.Store(pending,k,True);registered_c=z3.Store(cg,k,g)
completed=z3.Store(pending,k,False);settled=z3.Store(active,k,False)
empty=z3.ForAll(i,z3.Not(active[i]))
queries={
 'initial-invariant':([z3.Not(invariant(zero,zero,z3.K(D,0),z3.IntVal(1)))],'unsat'),
 'registration-preserves':([inv,z3.Not(active[k]),request==g,z3.Not(invariant(registered_a,registered_p,registered_c,g))],'unsat'),
 'completion-preserves':([inv,active[k],z3.Not(invariant(active,completed,cg,g))],'unsat'),
 'settlement-preserves':([inv,z3.Not(pending[k]),z3.Not(invariant(settled,pending,cg,g))],'unsat'),
 'native-loss-preserves':([inv,z3.Not(invariant(active,pending,cg,g))],'unsat'),
 'generation-advance-preserves':([inv,empty,g<MAX,z3.Not(invariant(active,pending,cg,g+1))],'unsat'),
 'acknowledgment-excludes-pending-release':([inv,empty,z3.Exists(i,pending[i])],'unsat'),
 'stale-registration-refuses':([inv,request!=g,request==g],'unsat'),
 'pending-operation-is-reachable':([g==1,active==zero,pending==zero,request==g,z3.Not(active[k]),invariant(registered_a,registered_p,registered_c,g),registered_p[k]],'sat'),
 'unsafe-settlement-counterexample':([inv,pending[k],z3.Not(invariant(settled,pending,cg,g))],'sat'),
 'loss-auto-clear-counterexample':([inv,pending[k],z3.Not(invariant(settled,pending,cg,g))],'sat'),
 'partial-writer-check-counterexample':([inv,z3.Not(active[k]),pending[k+1],g<MAX,z3.Not(invariant(active,pending,cg,g+1))],'sat'),
}
results={}
for name,(clauses,expected) in queries.items():
 s=z3.Solver();s.set(timeout=5000);s.add(*clauses);(root/(name+'.smt2')).write_text(s.to_smt2());r=str(s.check());assert r==expected,(name,r)
 witness=None
 if r=='sat':
  m=s.model();witness={str(v):str(m.eval(v,model_completion=True)) for v in [g,k,request,active[k],pending[k],cg[k],active[k+1],pending[k+1],cg[k+1]]}
 results[name]={'result':r,'witness':witness}
print(json.dumps({'solver':z3.get_version_string(),'queries':results,'invariant':'Every pending protected release has a durable active claim in the current generation.','induction':'Initialization and each modeled transition preserve the invariant. An authority acknowledgment requires absence of all active claims, therefore no pending protected release.','scope':'Arbitrary integer-indexed claims and arbitrary finite sequences of these abstract atomic transitions, subject to the stated invariant and transition premises. Registration, completion and settlement are trusted original-owner events. Native loss leaves durable state unchanged. Writers check all claims; registration/generation transitions are serialized. Not concrete SQL/driver/native refinement, identity anti-reuse/custody, commit uncertainty, source/fact coverage, sink authenticity, clocks, fairness/liveness or deployment admission.'},indent=2))
