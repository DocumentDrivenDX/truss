"""Conditional original-attempt identity laws; not SQL/source refinement.

Native premises: immutable authenticated anchor; unique full native transaction
identities; peer incarnation/full-xid reconciliation; authentic private issuance.
Program/source/Subject/action permission are deliberately separate predicates.
"""
import json
import z3

anchor_tx,current_tx,anchor_pid,current_pid,anchor_backend,current_backend=z3.Ints(
    'anchor_tx current_tx anchor_pid current_pid anchor_backend current_backend')
original_live,tuple_matches,permission=z3.Bools('original_live tuple_matches permission')
valid=z3.And(anchor_tx>0,anchor_tx<2**64,current_tx>0,current_tx<2**64,
             anchor_pid>0,current_pid>0,anchor_backend>0,current_backend>0)
identity=z3.And(original_live,anchor_tx==current_tx,anchor_pid==current_pid,anchor_backend==current_backend)
combined=z3.And(tuple_matches,identity)
queries=[
 ('bare_tuple_same_backend_replacement','sat',z3.And(tuple_matches,anchor_pid==current_pid,anchor_backend==current_backend,anchor_tx!=current_tx)),
 ('anchored_same_backend_replacement','unsat',z3.And(combined,anchor_pid==current_pid,anchor_backend==current_backend,anchor_tx!=current_tx)),
 ('ended_original_coordinator','unsat',z3.And(combined,z3.Not(original_live))),
 ('different_backend_incarnation','unsat',z3.And(combined,anchor_backend!=current_backend)),
 ('live_original_attempt','sat',combined),
 ('identity_is_not_authorization','sat',z3.And(combined,z3.Not(permission))),
]
results=[]
for name,expected,condition in queries:
    solver=z3.Solver();solver.add(valid,condition);actual=str(solver.check())
    result={'name':name,'expected':expected,'actual':actual,'passed':actual==expected}
    if actual=='sat':result['counterexampleOrWitness']=str(solver.model())
    results.append(result)
print(json.dumps({'z3':z3.get_version_string(),'results':results,'passed':all(r['passed'] for r in results),
 'scope':'Conditional abstract identity law only; native SQL/full-xid/immutability/privilege custody remain premises. No program or current permission theorem.'},indent=2))
if not all(r['passed'] for r in results):raise SystemExit(1)
