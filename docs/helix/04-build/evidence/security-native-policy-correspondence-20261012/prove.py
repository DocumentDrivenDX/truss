"""Conditional Boolean native policy-composition model; no implementation proof."""
from pathlib import Path
import json,itertools,z3
out=Path(__file__).parent
p,e,c,r=z3.Bools('original_permissive added_permissive caller_restriction added_restriction')
original=z3.And(p,c);widened=z3.And(z3.Or(p,e),c)
cases=[('added-permissive-can-widen',z3.And(widened,z3.Not(original)),'sat'),('closed-original-policy-set-excludes-widening',z3.And(z3.Not(e),widened,z3.Not(original)),'unsat'),('added-restriction-cannot-widen',z3.And(original,r,z3.Not(original)),'unsat'),('original-policy-positive',original,'sat')]
observations=[]
for name,formula,expected in cases:
 solver=z3.Solver();solver.add(formula);(out/(name+'.smt2')).write_text(solver.to_smt2());observed=str(solver.check());assert observed==expected
 replay=z3.Solver();replay.from_file(str(out/(name+'.smt2')));assert str(replay.check())==expected
 observations.append({'id':name,'expected':expected,'observed':observed,'formula':name+'.smt2','model':str(solver.model()) if observed=='sat' else None})
counts=[0]*4
for pv,ev,cv,rv in itertools.product([False,True],repeat=4):
 old=pv and cv;new=(pv or ev) and cv
 checks=[new and not old,(not ev) and new and not old,old and rv and not old,old]
 for i,check in enumerate(checks):counts[i]+=int(check)
assert [v>0 for v in counts]==[True,False,False,True]
(out/'formal.json').write_text(json.dumps({'solver':z3.get_version_string(),'scope':'Four Boolean predicate-match flags, exactly16 assignments. Retained original predicates unchanged; closed-set premise excludes added permissive matches. Not native correspondence, source authenticity, unknown-value refinement, held authority or general policy-engine proof.','observations':observations,'replays':4,'independentBooleanOracle':{'assignments':16,'satisfyingAssignmentCounts':counts}},indent=2)+'\n')
