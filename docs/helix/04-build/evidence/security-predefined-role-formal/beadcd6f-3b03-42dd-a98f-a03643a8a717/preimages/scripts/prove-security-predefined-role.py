"""Conditional predefined-role reachability model; native privilege and lifetime refinement remain unproved."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-predefined-role-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-predefined-role.py','scripts/security_owned_read.py','packages/python/src/truss/_psycopg_dependency_fact_cut.py','packages/python/src/truss/_psycopg_epoch_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
inherited,direct_set,bridge_set,bridge_inherited,member,callback=z3.Bools('inherited_predefined direct_set_predefined set_bridge bridge_inherited_predefined membership callback')
active=z3.Or(inherited,direct_set,z3.And(bridge_set,bridge_inherited))
protocol=callback==z3.Not(active)
queries=[
 ('inherited_predefined_excludes_callback','unsat',[protocol,inherited,callback]),
 ('set_predefined_excludes_callback','unsat',[protocol,direct_set,callback]),
 ('set_bridge_with_inherited_predefined_excludes_callback','unsat',[protocol,bridge_set,bridge_inherited,callback]),
 ('set_only_filter_misses_inherited_privilege','sat',[callback==z3.Not(direct_set),inherited,z3.Not(direct_set),callback]),
 ('inactive_membership_does_not_require_refusal','sat',[protocol,member,z3.Not(active),callback])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Abstract predefined-role inherited and SET reachability, including a SET-reachable identity with inherited predefined privileges. Three active paths exclude callback. A SET-only filter misses inherited privileges; inactive membership permits callback in this dimension.','limitations':['No native pg_has_role, SQL, role graph or host refinement proof','Role reachability observations are snapshots; concurrent authority mutation remains unqualified','Predefined-role exclusion does not qualify ordinary grants, routine closure, caller/issuer authentication or a complete protected backend']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
