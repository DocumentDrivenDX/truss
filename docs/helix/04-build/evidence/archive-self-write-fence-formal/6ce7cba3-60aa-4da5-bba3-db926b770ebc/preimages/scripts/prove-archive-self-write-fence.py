"""Conditional archive fence transition laws; not SQL/Python refinement."""
from pathlib import Path
import hashlib,json,uuid
import z3
root=Path.cwd();folder=root/'docs/helix/04-build/evidence/archive-self-write-fence-formal'/str(uuid.uuid4())
folder.mkdir(parents=True)
paths=['scripts/prove-archive-self-write-fence.py','packages/postgresql/native/catalog-report/archive-self-write-fence.sql','packages/python/tests/test_archive_self_write_fence_native.py','scripts/check-python-catalog-report-release-native.py']
pins={}
for name in paths:
    raw=(root/name).read_bytes();pins[name]=hashlib.sha256(raw).hexdigest()
    target=folder/'preimages'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
alive,installed,mutate=z3.Bools('alive installed mutate')
state,desired,intermediate,final=z3.Ints('state desired intermediate final')
allowed=z3.Not(z3.And(alive,installed,mutate))
step=intermediate==z3.If(z3.And(mutate,allowed),desired,state)
# One step with persistent exclusion cannot change the abstract archive state.
# Arbitrary finite histories follow by induction ONLY while each step has these
# premises; native event/trigger/lock coverage and physical state interpretation
# are independent qualification obligations.
queries=[
 ('fenced_step_preserves_state','unsat',[alive,installed,step,intermediate!=state]),
 ('fenced_successful_mutation_unreachable','unsat',[alive,installed,mutate,allowed]),
 ('read_step_preserves_state_without_fence','unsat',[z3.Not(mutate),step,intermediate!=state]),
 ('omitted_fence_allows_change_restore','sat',[alive,z3.Not(installed),mutate,step,intermediate!=state,final==state]),
 ('rollback_crossing_cut_allows_later_change','sat',[z3.Not(alive),installed,mutate,step,intermediate!=state]),
 ('disabled_trigger_allows_change','sat',[alive,z3.Not(installed),mutate,step,intermediate!=state])]
results=[]
for name,expected,clauses in queries:
    solver=z3.Solver();solver.set(timeout=10000);solver.add(*clauses)
    original=solver.to_smt2();(folder/(name+'.smt2')).write_text(original)
    actual=str(solver.check())
    context=z3.Context();replay=z3.Solver(ctx=context);replay.set(timeout=10000)
    replay.add(z3.parse_smt2_string(original,ctx=context));replayed=str(replay.check())
    if actual!=expected or replayed!=expected:raise RuntimeError('Exact expected solver and fresh-context replay required')
    results.append({'id':name,'expected':expected,'observed':actual,'freshContextReplay':replayed,'counterexample':str(solver.model()) if actual=='sat' else None,'smt2Sha256':hashlib.sha256(original.encode()).hexdigest()})
if any(hashlib.sha256((root/p).read_bytes()).hexdigest()!=h for p,h in pins.items()):raise RuntimeError('Original source drift')
receipt={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded abstract one-step preservation and stated finite-history induction, with trigger installed, every successful mutation reaching this fence, actual original ShareLock observation and no privileged bypass as premises. State is opaque, not a digest or SQL catalog interpretation. Acquisition/reparenting/rollback, PostgreSQL pg_locks correspondence, trigger installation/effective privilege, complete source/authority cut and final disclosure are not proven by this model. Native lifetime tests provide separate scoped evidence; no implementation refinement or backend acceptance claim.'}
(folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'evidence':str(folder),'queries':len(results)}))
