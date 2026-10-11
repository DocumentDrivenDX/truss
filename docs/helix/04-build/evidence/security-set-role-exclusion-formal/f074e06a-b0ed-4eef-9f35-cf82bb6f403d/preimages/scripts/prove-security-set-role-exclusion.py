"""Conditional SET-reachability model; no native membership or role-lifetime theorem."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-set-role-exclusion-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-set-role-exclusion.py','packages/python/src/truss/_psycopg_epoch_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
I=z3.IntSort();B=z3.BoolSort()
reachable=z3.Array('original_set_reachable',I,B);inherited=z3.Array('original_inherited',I,B);unsafe=z3.Array('original_selected_unsafe_role',I,B);later=z3.Array('later_set_reachable',I,B)
session,role=z3.Ints('session candidate_role')
strong=z3.ForAll([role],z3.Implies(z3.Select(reachable,role),z3.Not(z3.Select(unsafe,role))))
later_strong=z3.ForAll([role],z3.Implies(z3.Select(later,role),z3.Not(z3.Select(unsafe,role))))
queries=[
 ('no_inheritance_does_not_imply_no_set_reachability','sat',[z3.Not(z3.Select(inherited,role)),z3.Select(reachable,role)]),
 ('safe_session_can_have_unsafe_assumable_role','sat',[z3.Not(z3.Select(unsafe,session)),z3.Select(reachable,role),z3.Select(unsafe,role),z3.Not(z3.Select(inherited,role))]),
 ('complete_reachable_exclusion_prevents_selected_unsafe_role','unsat',[strong,z3.Select(reachable,role),z3.Select(unsafe,role)]),
 ('later_membership_change_can_invalidate_snapshot','sat',[strong,z3.Not(later_strong)]),
 ('stable_reachability_preserves_selected_exclusion','unsat',[strong,later==reachable,z3.Not(later_strong)])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded role identities and abstract original SET/inheritance reachability predicates. Inheritance and SET are distinct; excluding selected unsafe roles over complete SET reachability prevents the modeled bypass. Later membership changes have countermodels; stable reachability preserves the exclusion.','limitations':['No PostgreSQL pg_has_role SET/transitive-closure or SQL/Python refinement proof','Role/ACL lifetime, complete privileged-role/routine inventory and qualified-definer profiles remain unqualified','No authenticated caller/issuer, full authority admission or protected final release proof']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
