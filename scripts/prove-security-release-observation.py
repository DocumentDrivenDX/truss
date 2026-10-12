"""Conditional release observation model; uninterrupted native guard lifetime remains unproved."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-release-observation-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-release-observation.py','scripts/security_owned_read.py','packages/python/src/truss/_psycopg_dependency_fact_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
captured,lost,reacquired,checked,permit,release,same_xid=z3.Bools('captured_guard lost_guard reacquired_guard observed_guard permit release same_native_xid')
transition=z3.And(checked==z3.Or(z3.And(captured,z3.Not(lost)),reacquired),z3.Implies(reacquired,lost))
protocol=release==z3.And(permit,checked)
continuous=z3.And(captured,z3.Not(lost))
queries=[
 ('missing_observed_guard_refuses_release','unsat',[transition,protocol,z3.Not(checked),release]),
 ('lost_guard_without_reacquisition_refuses_release','unsat',[transition,protocol,captured,lost,z3.Not(reacquired),release]),
 ('no_guard_loss_preserves_original_cut','unsat',[transition,protocol,captured,z3.Not(lost),release,z3.Not(continuous)]),
 ('same_xid_alone_does_not_preserve_guard','sat',[transition,captured,lost,z3.Not(reacquired),same_xid,z3.Not(checked)]),
 ('loss_reacquisition_can_pass_observation_without_continuity','sat',[transition,protocol,captured,lost,reacquired,same_xid,release,z3.Not(continuous)])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Abstract capture/loss/reacquisition/check transition. Existing-lock observation refuses unavailable guards, including loss without reacquisition. Same native transaction ID does not entail guard retention. Loss/reacquisition admits release with no uninterrupted original cut.','limitations':['No native PostgreSQL lock/transaction, host lease, SQL, JSON or UMF refinement proof','No-loss is a premise under the exclusive host/raw-alias contract, not proved by endpoint observations','No authenticated issuer/mapping/target/credential, complete source/role/ACL lifetime or protected final-release qualification']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
