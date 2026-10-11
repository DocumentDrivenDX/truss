"""Conditional reachable-definer exclusion model; no call-graph or ACL lifetime theorem."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-definer-exclusion-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-definer-exclusion.py','packages/python/src/truss/_psycopg_epoch_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
I=z3.IntSort();B=z3.BoolSort()
superuser=z3.Array('original_superuser',I,B);create=z3.Array('original_createrole',I,B);bypass=z3.Array('original_bypassrls',I,B);member=z3.Array('original_owner_membership',I,B)
later_super=z3.Array('later_superuser',I,B);definer=z3.Array('reachable_privileged_definer',I,B)
session,effective=z3.Ints('original_session_role original_effective_role')
unsafe=lambda r:z3.Or(z3.Select(superuser,r),z3.Select(create,r),z3.Select(bypass,r),z3.Select(member,r))
admitted=z3.And(z3.Not(unsafe(session)),z3.Not(unsafe(effective)))
later_unsafe=lambda r:z3.Or(z3.Select(later_super,r),z3.Select(create,r),z3.Select(bypass,r),z3.Select(member,r))
later_admitted=z3.And(z3.Not(later_unsafe(session)),z3.Not(later_unsafe(effective)))
strong=z3.And(admitted,z3.Not(z3.Select(definer,session)),z3.Not(z3.Select(definer,effective)))
later_definer=z3.Array('later_reachable_privileged_definer',I,B)
later_strong=z3.And(admitted,z3.Not(z3.Select(later_definer,session)),z3.Not(z3.Select(later_definer,effective)))
queries=[
 ('strong_snapshot_excludes_session_definer','unsat',[strong,z3.Select(definer,session)]),
 ('strong_snapshot_excludes_effective_definer','unsat',[strong,z3.Select(definer,effective)]),
 ('weak_role_snapshot_permits_definer_path','sat',[admitted,z3.Select(definer,effective)]),
 ('later_acl_change_can_invalidate_definer_exclusion','sat',[strong,z3.Not(later_strong)]),
 ('stable_reachability_preserves_selected_exclusion','unsat',[strong,later_definer==definer,z3.Not(later_strong)])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded role identities with abstract original native role and EXECUTE reachability predicates. Both session and effective identities must lack reachable definers under this selected invoker-only profile. Weaker role-only admission and later ACL reachability changes have countermodels; stable reachability preserves the selected exclusion.','limitations':['No PostgreSQL has_function_privilege or complete call-graph/catalog/SQL/Python refinement proof','ACL/role/source lifetime, invoker-to-privileged transitions and qualified-definer profiles remain unqualified','No authenticated caller/issuer, full authority admission or protected final release proof']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
