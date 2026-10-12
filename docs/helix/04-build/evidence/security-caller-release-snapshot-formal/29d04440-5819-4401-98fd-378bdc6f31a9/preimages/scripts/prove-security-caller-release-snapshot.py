"""Conditional endpoint privilege observations; uninterrupted authority lifetime remains unproved."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-caller-release-snapshot-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-caller-release-snapshot.py','scripts/security_owned_read.py','packages/python/src/truss/_psycopg_dependency_fact_cut.py','packages/python/src/truss/_psycopg_epoch_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
initial_private,final_private,intermediate_private,permit,release=z3.Bools('initial_private_privilege final_private_privilege intermediate_private_privilege permit release')
protocol=release==z3.And(permit,z3.Not(initial_private),z3.Not(final_private))
queries=[
 ('initial_private_privilege_prevents_release','unsat',[protocol,initial_private,release]),
 ('final_private_privilege_prevents_release','unsat',[protocol,final_private,release]),
 ('late_grant_remaining_at_release_prevents_release','unsat',[protocol,z3.Not(initial_private),intermediate_private,final_private,release]),
 ('admission_only_filter_misses_late_privilege','sat',[release==z3.And(permit,z3.Not(initial_private)),z3.Not(initial_private),final_private,release]),
 ('grant_revoke_between_snapshots_is_not_excluded','sat',[protocol,z3.Not(initial_private),intermediate_private,z3.Not(final_private),release])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Abstract admission and final privilege snapshots. Present final privilege prevents release; admission-only checking misses late grants. Grant/revoke between snapshots remains compatible with release.','limitations':['No native catalog/role/ACL/SQL or host refinement proof','Endpoint observation does not prove uninterrupted authority lifetime or exclude changes after the last check','No authenticated caller/issuer/mapping, full mutation/privilege closure, revocation drain or admitted protected backend']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
