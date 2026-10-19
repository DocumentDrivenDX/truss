# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional privilege-separated release model; service trust and native refinement remain premises."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-delegated-read-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-delegated-read.py','scripts/security_owned_read.py','packages/python/src/truss/_psycopg_dependency_fact_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
caller_ok,executor_ok,guard_active,decision_permit,caller_private_access,release=z3.Bools('caller_verified executor_verified guard_active decision_permit caller_private_access release')
protocol=release==z3.And(caller_ok,executor_ok,guard_active,decision_permit)
weak=release==decision_permit
queries=[
 ('missing_original_caller_prevents_release','unsat',[protocol,z3.Not(caller_ok),release]),
 ('missing_original_executor_prevents_release','unsat',[protocol,z3.Not(executor_ok),release]),
 ('retired_guard_prevents_protected_release','unsat',[protocol,z3.Not(guard_active),release]),
 ('trusted_delegation_does_not_require_caller_private_access','sat',[protocol,release,z3.Not(caller_private_access)]),
 ('omitted_release_guard_can_publish_after_retirement','sat',[weak,decision_permit,z3.Not(guard_active),release])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Abstract original caller/executor verification and live release guard. The protected release rule excludes missing custody or retired guard. Trusted delegation can evaluate without caller private-table access; omitted guard permits release after retirement.','limitations':['No native privilege/host lease/SQL/JSON/UMF/connection-authentication refinement proof','Trusted service, original verified contexts and live guard are premises; installed issuer/mapping/package custody and complete lifetime remain unqualified','No authenticated caller/issuer, original writer installation/ACL closure, full authority admission or protected final release proof']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
