# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional role snapshot model; no native role-lifetime theorem."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-role-snapshot-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-role-snapshot.py','packages/python/src/truss/_psycopg_epoch_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
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
queries=[
 ('both_original_role_exclusions_prevent_selected_admin_flags','unsat',[admitted,z3.Or(unsafe(session),unsafe(effective))]),
 ('lowered_effective_role_does_not_override_session_superuser','unsat',[admitted,z3.Select(superuser,session),z3.Not(unsafe(effective))]),
 ('concurrent_role_change_can_invalidate_snapshot','sat',[admitted,z3.Not(later_admitted)]),
 ('role_snapshot_does_not_exclude_privileged_definer_path','sat',[admitted,z3.Select(definer,effective)]),
 ('stable_role_sources_preserve_selected_exclusion','unsat',[admitted,later_super==superuser,z3.Not(later_admitted)])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded role identities with abstract original native attribute/membership predicates. Both session and effective identities must satisfy the selected exclusion. Stable original role sources preserve that exclusion; snapshot-only admission permits later privilege changes and says nothing about privileged definer paths.','limitations':['No PostgreSQL pg_has_role membership-closure, native catalog or SQL/Python refinement proof','Role/source lifetime and reachable routine/ACL closure remain unqualified','No authenticated caller/issuer, full authority admission or protected final release proof']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
